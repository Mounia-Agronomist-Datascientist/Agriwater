"""
Unit tests for the Meteo API module.

Author: Mounia Tonazzini
Date: December 2025
"""


import pytest
import pandas as pd
import requests

from agriwater.meteo_api import MeteoAPI
from agriwater.exceptions import ValidationError, WeatherAPIError


# Fixtures: fake API responses
@pytest.fixture
def valid_api_response():
    return {
        "daily": {
            "time": ["2024-01-01", "2024-01-02"],
            "temperature_2m_min": [5.0, 6.0],
            "temperature_2m_mean": [10.0, 11.0],
            "temperature_2m_max": [15.0, 16.0],
            "et0_fao_evapotranspiration": [3.5, 3.6],
            "precipitation_sum": [1.0, 0.5],
        }
    }


@pytest.fixture
def api_response_with_nan():
    return {
        "daily": {
            "time": ["2024-01-01", "2024-01-02"],
            "temperature_2m_min": [5.0, None],
            "temperature_2m_mean": [10.0, 11.0],
            "temperature_2m_max": [15.0, 16.0],
            "et0_fao_evapotranspiration": [3.5, 3.6],
            "precipitation_sum": [1.0, None],
        }
    }



# Test 1: Validate coordinates handling
def test_meteo_api_initialization():
    api = MeteoAPI(latitude=43.6, longitude=3.9)
    assert api.latitude == 43.6
    assert api.longitude == 3.9



# Test 2: Ensure correct ISO date formatting
def test_calculate_date_range():
    api = MeteoAPI(43.6, 3.9)
    start, end = api._calculate_date_range(5)

    assert isinstance(start, str)
    assert isinstance(end, str)
    assert start < end



# Test 3: Convert API JSON to a clean DataFrame
def test_parse_response_success(valid_api_response):
    api = MeteoAPI(43.6, 3.9)

    df = api._parse_response_to_dataframe(
        valid_api_response,
        missing_data_strategy="raise"
    )

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "et0_fao" in df.columns
    assert "precipitation" in df.columns



# Test 4: Invalid missing data strategy
def test_invalid_missing_data_strategy(valid_api_response):
    api = MeteoAPI(43.6, 3.9)

    with pytest.raises(ValidationError):
        api._parse_response_to_dataframe(
            valid_api_response,
            missing_data_strategy="unknown"
        )


# Test 5: Missing data with 'raise' strategy
def test_missing_data_raise_strategy(api_response_with_nan):
    api = MeteoAPI(43.6, 3.9)

    with pytest.raises(WeatherAPIError):
        api._parse_response_to_dataframe(
            api_response_with_nan,
            missing_data_strategy="raise"
        )



# Test 6: Missing data with 'zero' strategy
def test_missing_data_zero_strategy(api_response_with_nan):
    api = MeteoAPI(43.6, 3.9)

    df = api._parse_response_to_dataframe(
        api_response_with_nan,
        missing_data_strategy="zero"
    )

    assert df.isna().sum().sum() == 0


# Test 7: Missing data with 'drop' strategy
def test_missing_data_drop_strategy(api_response_with_nan):
    api = MeteoAPI(43.6, 3.9)

    df = api._parse_response_to_dataframe(
        api_response_with_nan,
        missing_data_strategy="drop"
    )

    assert len(df) == 1



# Test 8: Missing data with 'interpolate' strategy
def test_missing_data_interpolate_strategy(api_response_with_nan):
    api = MeteoAPI(43.6, 3.9)

    df = api._parse_response_to_dataframe(
        api_response_with_nan,
        missing_data_strategy="interpolate"
    )

    assert df.isna().sum().sum() == 0



# Test 9: Validate full API workflow (mocked request)
def test_fetch_weather_data_success(monkeypatch, valid_api_response):
    api = MeteoAPI(43.6, 3.9)

    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return valid_api_response

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponse())

    df = api.fetch_weather_data(days_count=2)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2



# Test 10: API timeout handling
def test_fetch_weather_timeout(monkeypatch):
    api = MeteoAPI(43.6, 3.9)

    def mock_timeout(*args, **kwargs):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(requests, "get", mock_timeout)

    with pytest.raises(WeatherAPIError):
        api.fetch_weather_data()


# Test 11: Invalid days_count
def test_invalid_days_count():
    api = MeteoAPI(43.6, 3.9)

    with pytest.raises(ValidationError):
        api.fetch_weather_data(days_count=0)



# Test 12: Location info
def test_get_location_info():
    api = MeteoAPI(43.6, 3.9)

    info = api.get_location_info()

    assert info["latitude"] == 43.6
    assert info["longitude"] == 3.9
