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

def format_number(value: float, decimals: int = 2) -> str:
    """
    Formats a number with a specified number of decimal and returns it as a string.
    
    Args:
        - value (float): Value to format.
        - decimals (int): Number of decimal places.
        
    Returns: str: Formatted string.
    """
    return f"{value:.{decimals}f}"


def validate_area(area_ha: float) -> bool:
    """
    Validates that a surface area in hectares is positive.
    
    Args: area_ha (float): Surface area in hectares.
        
    Returns: bool: True if valid, False otherwise.
    """
    if area_ha <= 0:
        print(f"Error: Surface area must be positive (provided: {area_ha} ha)")
        return False
    return True



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
    """

    return m3 / (10 * surface_ha)  # m³ / (10 * ha) = mm


def coordinates_validation(latitude:int|float,longitude:int|float) -> None:
    """
    Checks if GPS coordinates are valid.
    
    Args : 
        - latitude (float) : latitude in degrees, must be between -90 and 90
        - longitude (float) : longitude in degrees, must be between -180 and 180

    Raises : 
        - TypeError if the coordinates are not float numbers
        - ValueError if the coordinates are not in a valid range
    """
    errors = []

    # Type checks
    if not isinstance(latitude, (int, float)):
        errors.append(f"Latitude must be a number, got {type(latitude).__name__}")
    if not isinstance(longitude, (int, float)):
        errors.append(f"Longitude must be a number, got {type(longitude).__name__}")

    # Value checks (only if types are correct)
    if isinstance(latitude, (int, float)) and not (-90 <= latitude <= 90):
        errors.append(f"Latitude {latitude} out of range [-90, 90]")
    if isinstance(longitude, (int, float)) and not (-180 <= longitude <= 180):
        errors.append(f"Longitude {longitude} out of range [-180, 180]")

    if errors:
        # Combine all errors into one exception
        raise ValueError("; ".join(errors))



# __________ Example usage for testing __________ 

if __name__ == "__main__":
    
    print("\n--- Testing utility functions ---")
    
    # Test number formatting
    print("\n- Number formatting tests:")
    print(f"Pi (2 decimals): {format_number(3.14159, 2)}")
    print(f"Pi (4 decimals): {format_number(3.14159, 4)}")
    
    # Test surface validation
    print("\n- Surface validation tests:")
    print(f"10 ha is valid: {validate_area(10)}")
    print(f"-5 ha is valid: {validate_area(-5)}")

    # Test conversions
    print("\n- Conversion tests:")
    print(f"10 mm = {convert_mm_to_m3_per_ha(10)} m³/ha")
    print(f"100 m³ on 5 ha = {convert_m3_to_mm(100, 5)} mm")

    # Test coordinate validation
    print("\n- Coordinates validation tests:")
    test_coords = [
        (43.6109, 3.8772), # Montpellier
        (48.8566, 2.3522), # Paris
        (95.0, 3.8772), # Invalid latitude
        (43.6109, 200.0), # Invalid longitude
        ("45", "10"), # Invalid  coordinates
        (45, "ab") # Invalid longitude type
    ]
    
    for lat, lon in test_coords:
        try:
            coordinates_validation(lat, lon)
            print("Coordinates are valid")
        except (ValueError, TypeError) as e:
            print(f"Coordinates are invalid: {e}")
    
    

    
