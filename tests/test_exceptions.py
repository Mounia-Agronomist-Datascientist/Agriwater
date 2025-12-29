"""
Unit tests for the custom exceptions.

Author: Mounia Tonazzini
Date: December 2025
"""

import pytest
from agriwater.irrigation_calculator import IrrigationCalculator
from agriwater.exceptions import  (AgriWaterError, 
                                   WeatherAPIError,
                                   CropDataError,
                                   CalculationError,
                                   ValidationError)

# Test 1 : Inheritance
def test_all_exceptions_inherit_from_agriwater_error():
    assert issubclass(WeatherAPIError, AgriWaterError)
    assert issubclass(CropDataError, AgriWaterError)
    assert issubclass(CalculationError, AgriWaterError)
    assert issubclass(ValidationError, AgriWaterError)


# Test 2: Each exception can be raised
@pytest.mark.parametrize(
    "exception_class",
    [
        WeatherAPIError,
        CropDataError,
        CalculationError,
        ValidationError,
    ],
)
def test_exceptions_can_be_raised(exception_class):
    with pytest.raises(exception_class):
        raise exception_class("Test error")


# Test 3: The parent class catches all the exceptions
def test_agriwater_error_catches_all_custom_errors():
    try:
        raise WeatherAPIError("API down")
    except AgriWaterError as e:
        assert isinstance(e, WeatherAPIError)

#  Test 4: No silent specific exception
def test_specific_exception_is_not_caught_by_wrong_type():
    with pytest.raises(WeatherAPIError):
        raise WeatherAPIError("Weather issue")
