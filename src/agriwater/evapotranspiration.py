"""
Module for calculating evapotranspiration and irrigation needs based on the FAO-56 methodology.

This module provides functions to:
- Calculate crop evapotranspiration (ETc) from reference evapotranspiration (ET0) and crop coefficient (Kc)
- Calculate cumulative precipitation over a period
- Determine net irrigation needs

Author: Mounia Tonazzini
Date: December 2025
"""

import pandas as pd
from agriwater.exceptions import ValidationError, CalculationError


class EvapotranspirationCalculator:
    """
    Class for calculating evapotranspiration and irrigation needs based on FAO-56.
    
    Attributes:
        - weather_data (pd.DataFrame): DataFrame containing weather data (ET0, precipitation, etc.)
        - crop_kc (float): Crop coefficient for the selected growth stage
        - crop_name (str): Name of the crop
    """
    

    def __init__(self, weather_data: pd.DataFrame, crop_kc: float, crop_name: str = "unknown"):
        """
        Initializes the evapotranspiration calculator.
        
        Args:
            - weather_data (pd.DataFrame): DataFrame with columns ['date', 'et0_fao', 'precipitation']
            - crop_kc (float): Crop coefficient (Kc)
            - crop_name (str): Name of the crop (for display purposes)
            
        Raises:
            - CalculationError: If required columns are missing 
            - ValidationError: If Kc is invalid
        """
        
        # Validate required columns
        required_cols = ['date', 'et0_fao', 'precipitation']
        missing_cols = [col for col in required_cols if col not in weather_data.columns]
        
        if missing_cols:
            raise CalculationError(f"Missing required columns in weather_data: {missing_cols}")
        
        # Validate Kc
        if not (0 <= crop_kc <= 2):
            raise ValidationError(f"Kc must be between 0 and 2. Received: {crop_kc}")
        
        self.weather_data = weather_data.copy()
        self.crop_kc = crop_kc
        self.crop_name = crop_name
        
        # Raise an error if NaN values are present
        if self.weather_data[['et0_fao', 'precipitation']].isna().any().any():
            raise ValidationError(
                "weather_data contains missing values. "
                "Handle missing data upstream (e.g. in meteo_api)."
            )
        
    
    def calculate_etc(self) -> pd.DataFrame:
        """
        Calculates crop evapotranspiration (ETc) for each day.
        
        Formula: ETc = ET0 x Kc
        
        Returns: 
            pd.DataFrame: DataFrame with added 'etc' column (mm/day)
        """

        self.weather_data['etc'] = self.weather_data['et0_fao'] * self.crop_kc
        return self.weather_data

    
    
    def calculate_cumulative_precipitation(self, period_days: int = 7) -> float:
        """
        Calculates cumulative precipitation over the last "period_days" days.
        
        Args: 
            period_days (int): Number of days to consider (default: 7)
            
        Returns: 
            float: Total precipitation in mm over the period
        """
        if period_days <= 0:
            raise ValidationError("period_days must be a positive integer.")

        if period_days > len(self.weather_data):
            raise ValidationError(f"Requested period ({period_days} days) exceeds available weather data.")
        
        total_precipitation = self.weather_data['precipitation'].tail(period_days).sum() # Sum of precipitation of the last "period_days" days
        
        return total_precipitation
    

    
    def calculate_average_etc(self, period_days: int|None = None) -> float:
        """
        Calculates average daily ETc over a period.
        
        Args: 
            period_days (int, optional): Number of days to consider. 
            If None, uses all available data.
        
        Returns: 
            float: Average daily ETc in mm/day
        """
        
        if period_days is not None and period_days <= 0:
            raise ValidationError("period_days must be a positive integer.")

        if 'etc' not in self.weather_data.columns:
            self.calculate_etc()
        
        if period_days is not None:
            etc_values = self.weather_data['etc'].tail(period_days)
        else:
            etc_values = self.weather_data['etc']
        
        avg_etc = etc_values.mean()
        return avg_etc
    
    
    
    def calculate_irrigation_need(self, period_days: int = 7, efficiency: float = 0.85) -> dict[str, float]:
        """
        Calculates net irrigation needs based on ETc and precipitation.
        
        Args:
            - period_days (int): Number of days to consider for precipitation (default: 7)
            - efficiency (float): Irrigation efficiency (default: 0.85 = 85%)
        
        Returns:
            dict[str, float]: Dictionary containing:
                - 'avg_etc_mm_day': Average daily ETc (mm/day)
                - 'total_etc_mm': Total ETc over period (mm)
                - 'total_precipitation_mm': Total precipitation over period (mm)
                - 'net_irrigation_need_mm': Net irrigation need (mm)
                - 'gross_irrigation_need_mm': Gross irrigation need accounting for efficiency (mm)
        
        Raises: 
            ValidationError: If the irrigation efficiency is not between 0 and 1.
        """

        if period_days <= 0:
            raise ValidationError("period_days must be a positive integer.")

        if not (0 < efficiency <= 1):
            raise ValidationError(f"Irrigation efficiency must be between 0 and 1 (Received: {efficiency})")

        # Calculate ETc if not already done
        if 'etc' not in self.weather_data.columns:
            self.calculate_etc()
        
        # Calculate average daily ETc
        avg_etc = self.calculate_average_etc(period_days)
        
        # Calculate total ETc over the period
        total_etc = avg_etc * period_days
        
        # Calculate cumulative precipitation
        total_precipitation = self.calculate_cumulative_precipitation(period_days)
        
        # Calculate net irrigation need (net need cannot be negative)
        net_irrigation_need = max(0, total_etc - total_precipitation)
        
        # Calculate gross irrigation need (accounting for efficiency)
        gross_irrigation_need = net_irrigation_need / efficiency if net_irrigation_need > 0 else 0
        
        results = {
            'avg_etc_mm_day': avg_etc,
            'total_etc_mm': total_etc,
            'total_precipitation_mm': total_precipitation,
            'net_irrigation_need_mm': net_irrigation_need,
            'gross_irrigation_need_mm': gross_irrigation_need
        }
        return results
    

    
    def calculate_irrigation_volume(self, surface_ha: float, period_days: int = 7, 
                                   efficiency: float = 0.85) -> dict[str, float]:
        """
        Calculates irrigation volume needed for a given surface area.
        
        Args:
            - surface_ha (float): Surface area in hectares,
            - period_days (int): Number of days to consider (default: 7),
            - efficiency (float): Irrigation efficiency (default: 0.85).
        
        Returns:
            dict[str, float]: Dictionary containing:
                - All values from calculate_irrigation_need(),
                - 'surface_ha': Surface area (ha),
                - 'net_volume_m3': Net irrigation volume (m³),
                - 'gross_volume_m3': Gross irrigation volume (m³).
        
        Raises : 
            - ValidationError: If the surface is not positive.
        """
        
        if surface_ha <= 0:
            raise ValidationError(f"Surface area must be positive. Received: {surface_ha} ha")
        
        # Get irrigation needs in mm
        irrigation_needs = self.calculate_irrigation_need(period_days, efficiency)
        
        # Convert mm to m³/ha (1 mm = 10 m³/ha)
        net_volume_m3 = irrigation_needs['net_irrigation_need_mm'] * 10 * surface_ha
        gross_volume_m3 = irrigation_needs['gross_irrigation_need_mm'] * 10 * surface_ha
        
        # Add volume results
        results = {
            **irrigation_needs,
            'surface_ha': surface_ha,
            'net_volume_m3': net_volume_m3,
            'gross_volume_m3': gross_volume_m3
        }
        return results
    
    
    