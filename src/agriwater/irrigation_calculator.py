"""
Main irrigation calculator module that orchestrates all components.

This module combines:
- Weather data retrieval (MeteoAPI)
- Crop parameters loading (CropDatabase)
- Evapotranspiration calculations (EvapotranspirationCalculator)

Author: Mounia Tonazzini
Date: December 2025
"""
import sys
import os
import pandas as pd

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agriwater.meteo_api import MeteoAPI
from src.agriwater.utils import coordinates_validation, validate_area
from src.agriwater.evapotranspiration import EvapotranspirationCalculator
from src.agriwater.crop_database import CropDatabase


class IrrigationCalculator:
    """
    Main class that orchestrates irrigation needs calculation.
    
    This class combines weather data, crop parameters, and evapotranspiration
    calculations to provide irrigation recommendations.
    
    Attributes:
        - latitude (float): Latitude of the location
        - longitude (float): Longitude of the location
        - crop_name (str): Name of the crop
        - crop_stage (str): Phenological stage of the crop
        - surface_ha (float): Surface area in hectares
        - crop_db (CropDatabase): Crop parameters database
        - crop_info (dict): Crop information and parameters
        - crop_kc (float): Crop coefficient for the selected stage
        - meteo_api (MeteoAPI): Weather data API instance
        - weather_data (pd.DataFrame): Retrieved weather data
    
    """
    
    def __init__(
        self,
        latitude: float,
        longitude: float,
        crop_name: str,
        crop_stage: str = "mid_season",
        surface_ha: float = 1.0
    ):
        """
        Initialize the irrigation calculator.
        
        Args:
            - latitude (float): Latitude of the location
            - longitude (float): Longitude of the location
            - crop_name (str): Name of the crop ('WHEAT', 'MAIZE', 'TOMATO', 'GRAPEVINE')
            - crop_stage (str): Phenological stage ('initial', 'development', 'mid_season', 'late_season')
            - surface_ha (float): Surface area in hectares (default: 1.0)
         
            
        Raises:ValueError: If crop or stage is invalid
        """

        # Validate coordinates
        coordinates_validation(latitude,longitude)
        self.latitude = latitude
        self.longitude = longitude
        
        # Initialize crop database and validate crop and stage
        self.crop_db = CropDatabase()
        self.crop_db.validate_crop_and_stage(crop_name,crop_stage)
        self.crop_name = crop_name.lower()
        self.crop_stage = crop_stage.lower()

        # Validate area
        validate_area(surface_ha)
        self.surface_ha = surface_ha
        
        # Load crop information
        self.crop_info = self.crop_db.get_crop_info(self.crop_name)
        self.crop_kc = self.crop_db.get_kc_for_stage(self.crop_name, self.crop_stage)
        
        # Initialize weather API
        self.meteo_api = MeteoAPI(latitude=latitude, longitude=longitude)

        # Weather data (fetched when needed)
        self.weather_data = None
        
        print(f"\nIrrigation calculator initialized")
        print(f"- Location: ({latitude:.4f}, {longitude:.4f})")
        print(f"- Crop: {self.crop_info["full_name"]} ({self.crop_name})")
        print(f"- Stage: {self.crop_stage.replace('_', ' ').title()}")
        print(f"- Kc: {self.crop_kc:.2f}")
        print(f"- Surface: {self.surface_ha:.2f} ha\n")
    
    
    def fetch_weather_data(self, nb_days: int = 7) -> pd.DataFrame:
        """
        Fetch weather data from the API.
        
        Args:nb_days (int): Number of days of historical data to fetch (default: 7)
            
        Returns:pd.DataFrame: Weather data
        """

        print(f"Fetching weather data for the last {nb_days} days")
        self.weather_data = self.meteo_api.fetch_weather_data(days_count=nb_days)
        
        if self.weather_data is None:
            raise RuntimeError("Failed to fetch weather data. Check your internet connection.")
        
        return self.weather_data
    
    
    def calculate_irrigation_needs(self,period_days: int|None = None, efficiency: float = 0.85) -> dict[str, float]:
        """
        Calculate irrigation needs based on weather data and crop parameters.
        
        Args:
            - period_days (int, optional): Number of days to consider for calculations.
            If None, uses recommended period for the crop.
            - efficiency (float): Irrigation efficiency (default: 0.85 = 85%)
            
        Returns: dict[str, float]: Dictionary with irrigation needs and water balance
        """

        # Fetch weather data if not already done
        if self.weather_data is None:
            nb_days = period_days if period_days else max(self.crop_info["irrigation_interval"])
            self.fetch_weather_data(nb_days=nb_days)
        
        # Use recommended period if not specified
        if period_days is None:
            # Use the maximum recommended period for the crop
            period_days = max(self.crop_info["irrigation_interval"])
            print(f"Using recommended irrigation period: {period_days} days")
        
        # Create evapotranspiration calculator
        et_calculator = EvapotranspirationCalculator(
            weather_data=self.weather_data,
            crop_kc=self.crop_kc,
            crop_name=self.crop_info["full_name"]
        )
        
        # Calculate irrigation volume
        results = et_calculator.calculate_irrigation_volume(
            surface_ha=self.surface_ha,
            period_days=period_days,
            efficiency=efficiency
        )
        
        return results
    
    
    def display_full_report(
        self,
        period_days: int|None = None,
        efficiency: float = 0.85
    ) -> None:
        """
        Display a complete irrigation report with recommendations.
        
        Args:
            - period_days (int, optional): Number of days to consider for calculations
            - efficiency (float): Irrigation efficiency (default: 0.85)
        """
        
        # Fetch weather data if not already done
        if self.weather_data is None:
            nb_days = period_days if period_days else max(self.crop_info["irrigation_interval"])
            self.fetch_weather_data(nb_days=nb_days)
        
        # Use recommended period if not specified
        if period_days is None:
            period_days = max(self.crop_info["irrigation_interval"])
        
        # Create evapotranspiration calculator
        et_calculator = EvapotranspirationCalculator(
            weather_data=self.weather_data,
            crop_kc=self.crop_kc,
            crop_name=self.crop_info["full_name"]
        )
        
        # Display summary
        et_calculator.display_irrigation_summary(
            surface_ha=self.surface_ha,
            period_days=period_days,
            efficiency=efficiency
        )
    
    
    def get_crop_summary(self) -> None:
        """
        Display a summary of the selected crop parameters.
        """
        self.crop_db.display_crop_summary(self.crop_name)
    

    def get_weather_summary(self) -> pd.DataFrame:
        """
        Get a summary of the weather data with ETc calculated.
        
        Returns:pd.DataFrame: Weather data with ETc column
        """

        if self.weather_data is None:
            self.fetch_weather_data()
        
        # Create evapotranspiration calculator
        et_calculator = EvapotranspirationCalculator(
            weather_data=self.weather_data,
            crop_kc=self.crop_kc,
            crop_name=self.crop_info["full_name"]
        )
        
        # Calculate ETc
        weather_with_etc = et_calculator.calculate_etc()
        
        return weather_with_etc
    
    
    def export_results_to_csv(
        self,
        filename: str = "irrigation_results.csv",
        period_days: int|None = None,
        efficiency: float = 0.85
    ) -> None:
        """
        s calculation results to a CSV file.
        
        Args:
            - filename (str): Output filename (default: 'irrigation_results.csv')
            - period_days (int, optional): Number of days to consider
            - efficiency (float): Irrigation efficiency
        """
        # Calculate results
        results = self.calculate_irrigation_needs(period_days, efficiency)
        
        # Create DataFrame
        results_df = pd.DataFrame([results])
        
        # Add metadata
        results_df['crop'] = self.crop_info['full_name']
        results_df['crop_stage'] = self.crop_stage
        results_df['kc'] = self.crop_kc
        results_df['latitude'] = self.latitude
        results_df['longitude'] = self.longitude
        results_df['date'] = pd.Timestamp.now()
        
        # Reorder columns
        cols = ['date', 'crop', 'crop_stage', 'kc', 'latitude', 'longitude'] + \
               [col for col in results_df.columns if col not in 
                ['date', 'crop', 'crop_stage', 'kc', 'latitude', 'longitude']]
        results_df = results_df[cols]
        
        # Export to CSV
        results_df.to_csv(filename, index=False)
        print(f"\nResults exported to {filename}")

        return results_df
    
    





# __________ Example usage for testing __________ 

if __name__ == "__main__":

    try:
        # Example 1: Grapevine in Montpellier
        print("\n" + "="*70)
        print("EXAMPLE 1: Grapevine field in Montpellier (mid-season)")
        print("="*70)
        
        calc_grapevine = IrrigationCalculator(
            latitude=43.6109,
            longitude=3.8772,
            crop_name="GRAPEVINE",
            crop_stage="mid_season",
            surface_ha=15.0
        )
        
        # Display crop summary
        calc_grapevine.get_crop_summary()
        
        # Display full irrigation report
        calc_grapevine.display_full_report(period_days=7, efficiency=0.85)
        
        # Export results
        calc_grapevine.export_results_to_csv("example_grapevine_results.csv")
        
        # Display weather data with ETc
        print("\nWeather data with ETc:")
        weather_summary = calc_grapevine.get_weather_summary()
        print(weather_summary[['date', 'temp_mean', 'et0_fao', 'precipitation', 'etc']].to_string(index=False))


        # Example 2: Test with invalid crop (error handling)
        print("\n\n" + "="*70)
        
        try:
            calc_invalid = IrrigationCalculator(
                latitude=43.6109,
                longitude=3.8772,
                crop_name="banane",  # Invalid crop
                crop_stage="mid_season"
            )
        except ValueError as e:
            print(f"Error correctly caught: {e}")
        
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()