"""
Main irrigation calculator module that orchestrates all components.

This module combines:
- Weather data retrieval (MeteoAPI)
- Crop parameters loading (CropDatabase)
- Evapotranspiration calculations (EvapotranspirationCalculator)

Author: Mounia Tonazzini
Date: December 2025
"""

import pandas as pd
from pathlib import Path
import logging

from agriwater.meteo_api import MeteoAPI
from agriwater.utils import coordinates_validation, validate_area
from agriwater.evapotranspiration import EvapotranspirationCalculator
from agriwater.crop_database import CropDatabase
from agriwater.exceptions import WeatherAPIError, ValidationError

logger=logging.getLogger(__name__)
ALLOWED_STRATEGIES = {"raise", "zero", "interpolate", "drop"}

class IrrigationCalculator:
    """
    Main class that orchestrates irrigation needs calculation.
    
    This class combines weather data, crop parameters, and evapotranspiration
    calculations to provide irrigation recommendations. 
    (We assume a homogeneous crop surface and uniform irrigation efficiency.)
    
    Attributes:
        - latitude (float): Latitude of the location
        - longitude (float): Longitude of the location
        - crop_name (str): Name of the crop
        - crop_stage (str): Phenological stage of the crop
        - surface_ha (float): Surface area in hectares
        - missing_data_strategy (str): Strategy to deal with NaN
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
        surface_ha: float = 1.0,
        missing_data_strategy: str = "raise"
    ):
        """
        Initializes the irrigation calculator.
        
        Args:
            - latitude (float): Latitude of the location
            - longitude (float): Longitude of the location
            - crop_name (str): Name of the crop ('WHEAT', 'MAIZE', 'TOMATO', 'GRAPEVINE')
            - crop_stage (str): Phenological stage ('initial', 'development', 'mid_season', 'late_season')
            - surface_ha (float): Surface area in hectares (default: 1.0)
         
            
        Raises:
            - ValidationError: If crop, stage, coordinates or area are invalid
            - CropDataError: If crop data is missing
        """

        # Validations
        coordinates_validation(latitude,longitude)
        self.latitude = latitude
        self.longitude = longitude
        
        validate_area(surface_ha)
        self.surface_ha = surface_ha
        
        if missing_data_strategy not in ALLOWED_STRATEGIES:
            raise ValidationError(
                f"Unknown missing_data_strategy: '{missing_data_strategy}'."
                f"Allowed values: {sorted(ALLOWED_STRATEGIES)}")
        self.missing_data_strategy = missing_data_strategy
        
        # Initialize crop database and validate crop and stage
        self.crop_db = CropDatabase()
        self.crop_db.validate_crop_and_stage(crop_name,crop_stage)
        self.crop_name = crop_name.lower()
        self.crop_stage = crop_stage.lower()
        
        # Load crop information
        self.crop_info = self.crop_db.get_crop_info(self.crop_name)
        self.crop_kc = self.crop_db.get_kc_for_stage(self.crop_name, self.crop_stage)
        
        # Initialize weather API
        self.meteo_api = MeteoAPI(latitude=latitude, longitude=longitude)
        self.weather_data = None  # Fetched when needed
        
        logger.info(f"\nIrrigation calculator initialized")
        logger.info(f"- Location: ({latitude:.4f}, {longitude:.4f})")
        logger.info(f"- Crop: {self.crop_info['full_name']} ({self.crop_name})")
        logger.info(f"- Stage: {self.crop_stage.replace('_', ' ').title()}")
        logger.info(f"- Kc: {self.crop_kc:.2f}")
        logger.info(f"- Surface: {self.surface_ha:.2f} ha\n")
        logger.info(f"Missing data strategy : {missing_data_strategy}")
    

    
    def fetch_weather_data(self, nb_days: int = 7) -> pd.DataFrame:
        """
        Fetches weather data from the API using the strategy defined at initialization.
        
        Args: 
            nb_days (int): Number of days of historical data to fetch (default: 7)
            
        Returns: 
            pd.DataFrame: Weather data
        """
    
        logger.info(f"Fetching weather data for the last {nb_days} days")
        try:
            self.weather_data = self.meteo_api.fetch_weather_data(
                days_count = nb_days,
                missing_data_strategy = self.missing_data_strategy
                )
            return self.weather_data
        except WeatherAPIError as e:
            raise WeatherAPIError(
                f"IrrigationCalculator failed to fetch weather data "
                f"(strategy={self.missing_data_strategy})"
            ) from e
    

    def calculate_irrigation_needs(self,period_days: int|None = None, efficiency: float = 0.85) -> dict[str, float]:
        """
        Calculates irrigation needs based on weather data and crop parameters.
        
        Args:
            - period_days (int, optional): Number of days to consider for calculations.
            If None, uses recommended period for the crop.
            - efficiency (float): Irrigation efficiency (default: 0.85 = 85%)
            
        Returns: 
            dict[str, float]: Dictionary with irrigation needs and water balance
        """
        
        # Use the maximum recommended period for the crop if not specified
        if period_days is None:
            period_days = max(self.crop_info["irrigation_interval"])
            logger.info(f"Using recommended irrigation period: {period_days} days")
        else : 
            period_days = int(period_days)
        
        # Fetch weather data if not already done
        if self.weather_data is None or len(self.weather_data) < period_days:
            self.fetch_weather_data(nb_days=period_days)
        
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
    
    
    def get_weather_summary(self) -> pd.DataFrame:
        """
        Get a summary of the weather data with ETc calculated.
        
        Returns: 
            pd.DataFrame: Weather data with an added ETc column
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


    def generate_agronomic_summary(self,period_days: int, efficiency: float) -> dict:
        """
        Generates a clear agronomic irrigation decision summary.

        Returns:
            dict: Agronomic indicators and irrigation recommendation.
        """

        results = self.calculate_irrigation_needs(period_days, efficiency)

        total_precip_mm = results["total_precipitation_mm"]
        total_etc_mm = results["avg_etc_mm_day"] * period_days
        water_balance_mm = total_precip_mm - total_etc_mm

        irrigation_required = water_balance_mm < 0

        recommended_mm = abs(water_balance_mm) if irrigation_required else 0.0
        recommended_m3_per_ha = recommended_mm * 10  # 1 mm = 10 m³/ha
        recommended_total_m3 = recommended_m3_per_ha * self.surface_ha

        return {
            "period_days": period_days,
            "total_precip_mm": total_precip_mm,
            "total_etc_mm": total_etc_mm,
            "water_balance_mm": water_balance_mm,
            "irrigation_required": irrigation_required,
            "recommended_mm": recommended_mm,
            "recommended_m3_per_ha": recommended_m3_per_ha,
            "recommended_total_m3": recommended_total_m3,
            "surface_ha": self.surface_ha,
            "crop_name": self.crop_name,
            "crop_stage": self.crop_stage
        }

    
    def export_results_to_csv(
        self,
        filename: str = "irrigation_results.csv",
        period_days: int|None = None,
        efficiency: float = 0.85
    )-> tuple[Path, pd.DataFrame]:
        
        """
        Exports calculation results to a CSV file into the output folder using Pathlib.
        
        Args:
            - filename (str): Output filename (default: 'irrigation_results.csv')
            - period_days (int, optional): Number of days to consider
            - efficiency (float): Irrigation efficiency
        
        Returns: 
            Tuple with the path of the saved csv file and the results as a DataFrame.
        """
        
        # Project root relative to this file
        root_dir = Path(__file__).resolve().parent.parent.parent
        output_dir = root_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True) # Create the output folder if it doesn't exist
        file_path = output_dir / filename # Full file path

        # Calculate results
        results = self.calculate_irrigation_needs(period_days, efficiency)
        
        # Create DataFrame
        results_df = pd.DataFrame([results])
        
        # Add metadata for the record
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
        results_df.to_csv(file_path, index=False)

        return file_path,results_df
    
    