"""
Module for calculating evapotranspiration and irrigation needs based on FAO-56 methodology.

This module provides functions to:
- Calculate crop evapotranspiration (ETc) from reference evapotranspiration (ET0) and crop coefficient (Kc)
- Calculate cumulative precipitation over a period
- Determine net irrigation needs

Author: Mounia Tonazzini
Date: December 2025
"""

import pandas as pd

# Import conversion functions from utils module
from src.utils import convert_mm_to_m3_per_ha, convert_m3_to_mm



class EvapotranspirationCalculator:
    """
    Class for calculating evapotranspiration and irrigation needs.
    
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
            ValueError: If required columns are missing or Kc is invalid
        """
        
        # Validate required columns
        required_cols = ['date', 'et0_fao', 'precipitation']
        missing_cols = [col for col in required_cols if col not in weather_data.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns in weather_data: {missing_cols}")
        
        # Validate Kc
        if not (0 <= crop_kc <= 2):
            raise ValueError(f"Kc must be between 0 and 2. Received: {crop_kc}")
        
        self.weather_data = weather_data.copy()
        self.crop_kc = crop_kc
        self.crop_name = crop_name
        
        # Replace NaN with 0 for calculations
        self.weather_data['et0_fao'] = self.weather_data['et0_fao'].fillna(0)
        self.weather_data['precipitation'] = self.weather_data['precipitation'].fillna(0)
    


    
    def calculate_etc(self) -> pd.DataFrame:
        """
        Calculates crop evapotranspiration (ETc) for each day.
        
        Formula: ETc = ET0 x Kc
        
        Returns: pd.DataFrame: DataFrame with added 'etc' column (mm/day)
        """

        self.weather_data['etc'] = self.weather_data['et0_fao'] * self.crop_kc
        print(f"ETc calculated for {self.crop_name} (Kc = {self.crop_kc})")
        return self.weather_data
    
    
    def calculate_cumulative_precipitation(self, period_days: int = 7) -> float:
        """
        Calculates cumulative precipitation over a specified period.
        
        Args: period_days (int): Number of days to consider (default: 7)
            
        Returns: float: Total precipitation in mm over the period
        """
        
        total_precipitation = self.weather_data['precipitation'].tail(period_days).sum() # Sum of the precipitations of the last "period_days" days
        print(f"Cumulative precipitation over last {period_days} days: {total_precipitation:.2f} mm")
        
        return total_precipitation
    
    
    def calculate_average_etc(self, period_days: int|None = None) -> float:
        """
        Calculates average daily ETc over a period.
        
        Args: period_days (int, optional): Number of days to consider. 
        If None, uses all available data.
        
        Returns: float: Average daily ETc in mm/day
        """

        if 'etc' not in self.weather_data.columns:
            self.calculate_etc()
        
        if period_days is not None:
            etc_values = self.weather_data['etc'].tail(period_days)
        else:
            etc_values = self.weather_data['etc']
        
        avg_etc = etc_values.mean()
        print(f"Average daily ETc for {self.crop_name}: {avg_etc:.2f} mm/day")
        return avg_etc
    
    
    
    def calculate_irrigation_need(self, period_days: int = 7, efficiency: float = 0.85) -> dict[str, float]:
        """
        Calculates net irrigation needs based on ETc and precipitation.
        
        Args:
            - period_days (int): Number of days to consider for precipitation (default: 7)
            - efficiency (float): Irrigation efficiency (default: 0.85 = 85%)
        
        Returns:
            Dict[str, float]: Dictionary containing:
                - 'avg_etc_mm_day': Average daily ETc (mm/day)
                - 'total_etc_mm': Total ETc over period (mm)
                - 'total_precipitation_mm': Total precipitation over period (mm)
                - 'net_irrigation_need_mm': Net irrigation need (mm)
                - 'gross_irrigation_need_mm': Gross irrigation need accounting for efficiency (mm)
        """

        # Calculate ETc if not already done
        if 'etc' not in self.weather_data.columns:
            self.calculate_etc()
        
        # Calculate average daily ETc
        avg_etc = self.calculate_average_etc(period_days)
        
        # Calculate total ETc over the period
        total_etc = avg_etc * period_days
        
        # Calculate cumulative precipitation
        total_precipitation = self.calculate_cumulative_precipitation(period_days)
        
        # Calculate net irrigation need
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
            - surface_ha (float): Surface area in hectares
            - period_days (int): Number of days to consider (default: 7)
            - efficiency (float): Irrigation efficiency (default: 0.85)
        
        Returns:
            Dict[str, float]: Dictionary containing:
                - All values from calculate_irrigation_need()
                - 'surface_ha': Surface area (ha)
                - 'net_volume_m3': Net irrigation volume (m³)
                - 'gross_volume_m3': Gross irrigation volume (m³)
        """
        if surface_ha <= 0:
            raise ValueError(f"Surface area must be positive. Received: {surface_ha} ha")
        
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
    
    
    def display_irrigation_summary(self, surface_ha: float, period_days: int = 7, 
                                  efficiency: float = 0.85) -> None:
        """
        Display a formatted summary of irrigation needs.
        
        Args:
            - surface_ha (float): Surface area in hectares
            - period_days (int): Number of days to consider (default: 7)
            - efficiency (float): Irrigation efficiency (default: 0.85)
        """
        results = self.calculate_irrigation_volume(surface_ha, period_days, efficiency)
        
        print(f"{'-'*60}")
        print(f"{' '*15} IRRIGATION SUMMARY - {self.crop_name.upper()}\n")
        print(f"- Analysis period: Last {period_days} days")
        print(f"- Surface area: {results['surface_ha']:.2f} ha")
        print(f"- Crop coefficient (Kc): {self.crop_kc:.2f}")
        print(f"- Irrigation efficiency: {efficiency*100:.0f}%")
        print(f"\n{'─'*60}")
        print(f"{' '*15} WATER BALANCE:\n")
        print(f"- Average daily ETc: {results['avg_etc_mm_day']:.2f} mm/day")
        print(f"- Total ETc ({period_days} days): {results['total_etc_mm']:.2f} mm")
        print(f"- Total precipitation ({period_days} days): {results['total_precipitation_mm']:.2f} mm")
        print(f"\n{'─'*60}")
        print(f"{' '*15} IRRIGATION NEEDS:\n")
        print(f"- Net irrigation need: {results['net_irrigation_need_mm']:.2f} mm")
        print(f"- Gross irrigation need: {results['gross_irrigation_need_mm']:.2f} mm")
        print(f"\n{'─'*60}")
        print(f"{' '*15} WATER VOLUME REQUIRED:\n")
        print(f"- Net volume: {results['net_volume_m3']:.1f} m³")
        print(f"- Gross volume (with losses): {results['gross_volume_m3']:.1f} m³")
        print(f"\n{'─'*60}")
        
        # Recommendations
        if results['net_irrigation_need_mm'] == 0:
            print("-> RECOMMENDATION: No irrigation needed. Recent precipitation is sufficient.")
        elif results['net_irrigation_need_mm'] < 10:
            print("-> RECOMMENDATION: Low irrigation need. Monitor soil moisture.")
        else:
            print(f"-> RECOMMENDATION: Irrigation required. Apply approximately {results['gross_volume_m3']:.0f} m³.")


# __________ Example usage for testing  __________ 

if __name__ == "__main__":
    print("Testing evapotranspiration module\n")
    
    # Create sample weather data
    dates = pd.date_range(start='2025-12-14', end='2025-12-20', freq='D')
    sample_data = pd.DataFrame({
        'date': dates,
        'et0_fao': [1.2, 1.5, 1.8, 2.0, 1.6, 1.4, 1.3],
        'precipitation': [0, 5.0, 2.0, 0, 0, 3.0, 0]
    })
    
    print("Sample weather data:")
    print(sample_data.to_string(index=False))
    print()
    
    # Test with corn (Kc = 1.2 for mid-season)
    try:
        print("Testing with CORN (Kc = 1.2)")
        print("-" * 50)
        
        calc = EvapotranspirationCalculator(
            weather_data=sample_data,
            crop_kc=1.2,
            crop_name="Corn"
        )
        
        # Calculate and display irrigation summary
        calc.display_irrigation_summary(
            surface_ha=10.0,
            period_days=7,
            efficiency=0.85
        )
        
        # Test conversion functions
        print("\nTesting conversion functions:")
        print(f"- 10 mm = {convert_mm_to_m3_per_ha(10):.0f} m³/ha")
        print(f"- 100 m³ on 5 ha = {convert_m3_to_mm(100, 5):.1f} mm")
        
    except Exception as e:
        print(f"Error during testing: {e}")