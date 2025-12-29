"""
Unit tests for the Irrigation calculator module.

Author: Mounia Tonazzini
Date: December 2025
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

from agriwater.irrigation_calculator import IrrigationCalculator
from agriwater.exceptions import ValidationError, WeatherAPIError



# Test 1: Successful initialization with valid parameters to ensure that 
# the calculator initializes correctly
def test_irrigation_calculator_initialization():
    calc = IrrigationCalculator(
        latitude=43.6,
        longitude=3.9,
        crop_name="wheat",
        crop_stage="mid_season",
        surface_ha=2.0
    )

    assert calc.latitude == 43.6
    assert calc.longitude == 3.9
    assert calc.surface_ha == 2.0
    assert calc.crop_name == "wheat"
    assert calc.crop_stage == "mid_season"
    assert calc.weather_data is None


# Test 2: Validate strict control of allowed strategies 
# (Invalid missing data strategy should raise ValidationError)
def test_invalid_missing_data_strategy():
    with pytest.raises(ValidationError):
        IrrigationCalculator(
            latitude=43.6,
            longitude=3.9,
            crop_name="wheat",
            missing_data_strategy="unknown_strategy"
        )


# Test 3: Ensure weather data is fetched and stored
@patch("agriwater.irrigation_calculator.MeteoAPI.fetch_weather_data")
def test_fetch_weather_data(mock_fetch):
    fake_weather = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=7),
        "eto": [4.0] * 7,
        "precipitation": [1.0] * 7
    })

    mock_fetch.return_value = fake_weather

    calc = IrrigationCalculator(
        latitude=43.6,
        longitude=3.9,
        crop_name="wheat"
    )

    data = calc.fetch_weather_data(nb_days=7)

    assert isinstance(data, pd.DataFrame)
    assert len(data) == 7
    assert calc.weather_data is not None


# Test 4: Weather API failure is properly re-raised
@patch("agriwater.irrigation_calculator.MeteoAPI.fetch_weather_data")
def test_fetch_weather_data_api_failure(mock_fetch):
    mock_fetch.side_effect = WeatherAPIError("API failure")

    calc = IrrigationCalculator(
        latitude=43.6,
        longitude=3.9,
        crop_name="wheat"
    )

    with pytest.raises(WeatherAPIError):
        calc.fetch_weather_data()


# Test 5: Validate orchestration logic
@patch("agriwater.irrigation_calculator.EvapotranspirationCalculator")
@patch("agriwater.irrigation_calculator.MeteoAPI.fetch_weather_data")
def test_calculate_irrigation_needs(mock_fetch, mock_et):
    fake_weather = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=7),
        "eto": [4.0] * 7,
        "precipitation": [1.0] * 7
    })

    mock_fetch.return_value = fake_weather

    mock_et_instance = MagicMock()
    mock_et_instance.calculate_irrigation_volume.return_value = {
        "total_precipitation_mm": 7.0,
        "avg_etc_mm_day": 5.0,
        "net_irrigation_mm": 28.0,
        "gross_irrigation_mm": 33.0
    }
    mock_et.return_value = mock_et_instance

    calc = IrrigationCalculator(
        latitude=43.6,
        longitude=3.9,
        crop_name="wheat"
    )

    results = calc.calculate_irrigation_needs(period_days=7)

    assert isinstance(results, dict)
    assert "avg_etc_mm_day" in results
    assert results["avg_etc_mm_day"] > 0


# Test 6: Validate ETc enrichment of weather data
@patch("agriwater.irrigation_calculator.EvapotranspirationCalculator")
@patch("agriwater.irrigation_calculator.MeteoAPI.fetch_weather_data")
def test_get_weather_summary(mock_fetch, mock_et):
    fake_weather = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=3),
        "eto": [4.0, 4.2, 4.1],
        "precipitation": [0.0, 1.0, 0.5]
    })

    mock_fetch.return_value = fake_weather

    enriched_weather = fake_weather.copy()
    enriched_weather["ETc"] = [5.0, 5.2, 5.1]

    mock_et_instance = MagicMock()
    mock_et_instance.calculate_etc.return_value = enriched_weather
    mock_et.return_value = mock_et_instance

    calc = IrrigationCalculator(
        latitude=43.6,
        longitude=3.9,
        crop_name="wheat"
    )

    summary = calc.get_weather_summary()

    assert isinstance(summary, pd.DataFrame)
    assert "ETc" in summary.columns


# Test 7: Ensure irrigation decision logic is correct
@patch.object(IrrigationCalculator, "calculate_irrigation_needs")
def test_generate_agronomic_summary(mock_calc):
    mock_calc.return_value = {
        "total_precipitation_mm": 10.0,
        "avg_etc_mm_day": 4.0
    }

    calc = IrrigationCalculator(
        latitude=43.6,
        longitude=3.9,
        crop_name="wheat",
        surface_ha=2.0
    )

    summary = calc.generate_agronomic_summary(period_days=5, efficiency=0.85)

    assert summary["irrigation_required"] is True
    assert summary["recommended_mm"] > 0
    assert summary["recommended_total_m3"] > 0


# Test 8: CSV export creates file and DataFrame
@patch.object(IrrigationCalculator, "calculate_irrigation_needs")
def test_export_results_to_csv(mock_calc, tmp_path):
    mock_calc.return_value = {
        "total_precipitation_mm": 10.0,
        "avg_etc_mm_day": 4.0,
        "net_irrigation_mm": 10.0,
        "gross_irrigation_mm": 12.0
    }

    calc = IrrigationCalculator(
        latitude=43.6,
        longitude=3.9,
        crop_name="wheat"
    )

    file_path, df = calc.export_results_to_csv(
        filename="test_results.csv",
        period_days=5
    )

    assert isinstance(file_path, Path)
    assert file_path.exists()
    assert isinstance(df, pd.DataFrame)
