"""
Unit tests for the utils module.

Author: Mounia Tonazzini
Date: December 2025
"""

import pytest
from agriwater.utils import (
    format_number,
    validate_area,
    convert_mm_to_m3_per_ha,
    convert_m3_to_mm,
    coordinates_validation,
)
from agriwater.exceptions import ValidationError


# ----- Test format_number -----

# Test default decimal formatting
def test_format_number_default_decimals():
    # Should round to 2 decimal places by default
    assert format_number(12.3456) == "12.35"

# Test custom decimal formatting
def test_format_number_custom_decimals():
    # Should round to 1 decimal place
    assert format_number(12.3456, decimals=1) == "12.3"


# ----- Test validate_area -----

# Test valid area (should not raise)
def test_validate_area_valid():
    validate_area(1.5)  # valid, nothing should happen

# Test negative or zero areas (should raise ValidationError)
@pytest.mark.parametrize("invalid_value", [-1, 0])
def test_validate_area_negative_or_zero(invalid_value):
    with pytest.raises(ValidationError):
        validate_area(invalid_value)

# Test wrong type (string input)
def test_validate_area_wrong_type():
    with pytest.raises(ValidationError):
        validate_area("ten")


# ----- Test convert_mm_to_m3_per_ha -----

def test_convert_mm_to_m3_per_ha():
    # 1 mm = 10 m³/ha
    assert convert_mm_to_m3_per_ha(10) == 100


# ----- Test convert_m3_to_mm -----

# Test conversion with valid surface
def test_convert_m3_to_mm_valid():
    assert convert_m3_to_mm(100, 1) == 10

# Test conversion with invalid surface (0 ha)
def test_convert_m3_to_mm_invalid_surface():
    with pytest.raises(ValidationError):
        convert_m3_to_mm(100, 0)


# ----- Test coordinates_validation -----

# Test valid coordinates
def test_coordinates_validation_valid():
    coordinates_validation(43.6, 3.9)  # Should not raise

# Test coordinates out of range
def test_coordinates_validation_out_of_range():
    with pytest.raises(ValidationError):
        coordinates_validation(100, 200)  # latitude and longitude invalid

# Test coordinates with wrong type
def test_coordinates_validation_wrong_type():
    with pytest.raises(ValidationError):
        coordinates_validation("north", None)


# ----- Test consistency test for mm ↔ m³ conversion -----

def test_mm_m3_conversion_consistency():
    mm = 25
    surface = 2
    # Convert mm to m³ and back
    m3 = convert_mm_to_m3_per_ha(mm) * surface
    mm_back = convert_m3_to_mm(m3, surface)
    # The result should be identical
    assert mm_back == mm
