"""
This file centralizes all the "errors" specific to Agriwater

Author: Mounia Tonazzini
Date: December 2025
"""


class AgriWaterError(Exception):
    """Base class for all AgriWater project exceptions."""
    pass

class WeatherAPIError(AgriWaterError):
    """Raised when there is an issue with the Open-Meteo API (network, timeout, data format)."""
    pass

class CropDataError(AgriWaterError):
    """Raised if a crop or growth stage is missing or incorrectly defined in the database."""
    pass

class CalculationError(AgriWaterError):
    """Raised in case of mathematical or physical logic errors (e.g., negative ET0)."""
    pass

class ValidationError(AgriWaterError):
    """Raised when user input (coordinates, dates, etc.) is invalid."""
    pass