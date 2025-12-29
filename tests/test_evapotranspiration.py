"""
Unit tests for the evapotranspiration module.

These tests validate critical calculations for irrigation needs.

Author: Mounia Tonazzini
Date: December 2025
"""

import pytest
import pandas as pd

from agriwater.evapotranspiration import EvapotranspirationCalculator
from agriwater.exceptions import ValidationError, CalculationError


# Helper fixture: valid weather dataset
@pytest.fixture
def valid_weather_data():
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=7),
        "et0_fao": [4.0] * 7,           # Reference ET0 (mm/day)
        "precipitation": [1.0] * 7      # Daily precipitation (mm)
    })



# Test 1: Ensure valid inputs create a calculator instance
def test_initialization_success(valid_weather_data):
    calc = EvapotranspirationCalculator(
        weather_data=valid_weather_data,
        crop_kc=1.2,
        crop_name="Wheat"
    )

    assert calc.crop_kc == 1.2
    assert calc.crop_name == "Wheat"
    assert isinstance(calc.weather_data, pd.DataFrame)


# Test 2: Enforce strict weather data structure
def test_missing_required_columns(valid_weather_data):
    bad_data = valid_weather_data.drop(columns=["et0_fao"])

    with pytest.raises(CalculationError):
        EvapotranspirationCalculator(
            weather_data=bad_data,
            crop_kc=1.0
        )


# Test 3: Invalid Kc value
def test_invalid_kc(valid_weather_data):
    with pytest.raises(ValidationError):
        EvapotranspirationCalculator(
            weather_data=valid_weather_data,
            crop_kc=2.5
        )


# Test 4: NaN values in weather data
def test_nan_values_in_weather_data(valid_weather_data):
    valid_weather_data.loc[0, "et0_fao"] = None

    with pytest.raises(ValidationError):
        EvapotranspirationCalculator(
            weather_data=valid_weather_data,
            crop_kc=1.0
        )


# Test 5: ETc calculation
def test_calculate_etc(valid_weather_data):
    calc = EvapotranspirationCalculator(
        weather_data=valid_weather_data,
        crop_kc=1.2
    )

    result = calc.calculate_etc()

    assert "etc" in result.columns
    assert pytest.approx(result["etc"].iloc[0], 0.01) == 4.8



# Test 6: Validate correct precipitation aggregation
def test_cumulative_precipitation(valid_weather_data):
    calc = EvapotranspirationCalculator(
        weather_data=valid_weather_data,
        crop_kc=1.0
    )

    total_precip = calc.calculate_cumulative_precipitation(period_days=5)

    assert total_precip == 5.0



# Test 7: Prevent invalid agronomic periods
def test_invalid_precipitation_period(valid_weather_data):
    calc = EvapotranspirationCalculator(
        weather_data=valid_weather_data,
        crop_kc=1.0
    )

    with pytest.raises(ValidationError):
        calc.calculate_cumulative_precipitation(period_days=0)



# Test 8: Validate average daily ETc over a period
def test_average_etc(valid_weather_data):
    calc = EvapotranspirationCalculator(
        weather_data=valid_weather_data,
        crop_kc=1.2
    )

    avg_etc = calc.calculate_average_etc(period_days=7)

    assert pytest.approx(avg_etc, 0.01) == 4.8



# Test 9: Validate full irrigation balance logic
def test_calculate_irrigation_need(valid_weather_data):
    calc = EvapotranspirationCalculator(
        weather_data=valid_weather_data,
        crop_kc=1.2
    )

    results = calc.calculate_irrigation_need(period_days=7, efficiency=0.8)

    assert results["total_etc_mm"] > results["total_precipitation_mm"]
    assert results["net_irrigation_need_mm"] > 0
    assert results["gross_irrigation_need_mm"] > results["net_irrigation_need_mm"]


# Test 10: Ensure no negative irrigation
def test_no_irrigation_needed(valid_weather_data):
    valid_weather_data["precipitation"] = [10.0] * 7

    calc = EvapotranspirationCalculator(
        weather_data=valid_weather_data,
        crop_kc=1.0
    )

    results = calc.calculate_irrigation_need(period_days=7)

    assert results["net_irrigation_need_mm"] == 0
    assert results["gross_irrigation_need_mm"] == 0



# Test 11: Validate mm → m³ conversion
def test_irrigation_volume(valid_weather_data):
    calc = EvapotranspirationCalculator(
        weather_data=valid_weather_data,
        crop_kc=1.2
    )

    results = calc.calculate_irrigation_volume(
        surface_ha=2.0,
        period_days=7,
        efficiency=0.85
    )

    assert results["surface_ha"] == 2.0
    assert results["net_volume_m3"] > 0
    assert results["gross_volume_m3"] > results["net_volume_m3"]



# Test 12: Invalid surface area
def test_invalid_surface_area(valid_weather_data):
    calc = EvapotranspirationCalculator(
        weather_data=valid_weather_data,
        crop_kc=1.0
    )

    with pytest.raises(ValidationError):
        calc.calculate_irrigation_volume(surface_ha=0)
