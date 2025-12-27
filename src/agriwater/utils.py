"""
Utility functions for AgriWater project.

This module contains helper functions for:
- Number formatting
- Surface validation
- Unit conversions (mm ↔ m³)
- Coordinates validation

Author: Mounia Tonazzini
Date: December 2025
"""

from agriwater.exceptions import ValidationError

def format_number(value: float, decimals: int = 2) -> str:
    """
    Formats a number with a specified number of decimal and returns it as a string.
    
    Args:
        - value (float): Value to format.
        - decimals (int): Number of decimal places.
        
    Returns: str: Formatted string.
    """
    return f"{value:.{decimals}f}"


def validate_area(area_ha: float) -> None:
    """
    Validates that a surface area in hectares is positive.
    
    Args: area_ha (float): Surface area in hectares.
        
    Returns: ValidationError if area is not positive.
    """
    
    if not isinstance(area_ha, (int, float)):
        raise ValidationError(f"Area must be a number, got {type(area_ha).__name__}")
    
    if area_ha <= 0:
        raise ValidationError(f"Surface area must be positive (provided: {area_ha} ha)")



def convert_mm_to_m3_per_ha(mm: float) -> float:
    """
    Converts mm of water to m³ per hectare.
    
    Args: mm (float): Water depth in millimeters
    
    Returns:float: Water volume in m³/ha
    """

    return mm * 10  # 1 mm = 10 m³/ha



def convert_m3_to_mm(m3: float, surface_ha: float) -> float:
    """
    Converts m³ of water to mm for a given surface area.
    
    Args:
        - m3 (float): Water volume in m³
        - surface_ha (float): Surface area in hectares
    
    Returns:float: Water depth in mm
    Raises: ValidationError if surface_ha is not positive
    """
    if surface_ha <= 0:
        raise ValidationError(f"Surface area must be positive to calculate depth (provided: {surface_ha})")
    
    return m3 / (10 * surface_ha)  # m³ / (10 * ha) = mm


def coordinates_validation(latitude:int|float,longitude:int|float) -> None:
    """
    Validates if GPS coordinates are valid.
    
    Args : 
        - latitude (float) : latitude in degrees, must be between -90 and 90
        - longitude (float) : longitude in degrees, must be between -180 and 180

    Raises : 
        ValidationError: if the coordinates are not numbers or are out of range
    """
    errors = []

    # Type validation
    if not isinstance(latitude, (int, float)):
        errors.append(f"Latitude must be a number, got {type(latitude).__name__}")
    if not isinstance(longitude, (int, float)):
        errors.append(f"Longitude must be a number, got {type(longitude).__name__}")

    # Value validation (only if types are correct)
    if not errors:
        if not (-90 <= latitude <= 90):
            errors.append(f"Latitude {latitude} is out of range [-90, 90]")
        if not (-180 <= longitude <= 180):
            errors.append(f"Longitude {longitude} is out of range [-180, 180]")
    
    if errors:
        # Combine all errors into one custom exception
        raise ValidationError(" | ".join(errors))



# __________ Example usage for testing __________ 

# if __name__ == "__main__":
#     print("\n--- Testing utility functions ---")
    
#     # Test surface validation
#     print("\n- Surface validation tests:")
#     try:
#         validate_area(10)
#         print("10 ha: Valid")
#         validate_area(-5)
#     except ValidationError as e:
#         print(f"-5 ha: Invalid -> {e}")

#     # Test coordinate validation
#     print("\n- Coordinates validation tests:")
#     test_coords = [
#         (43.6109, 3.8772), 
#         (95.0, 3.8772),   
#         ("45", "10"),     
#     ]
    
#     for lat, lon in test_coords:
#         try:
#             coordinates_validation(lat, lon)
#             print(f"({lat}, {lon}): Valid")
#         except ValidationError as e:
#             print(f"({lat}, {lon}): Invalid -> {e}")