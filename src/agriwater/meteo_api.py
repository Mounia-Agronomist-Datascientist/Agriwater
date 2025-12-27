"""
Weather data retrieval module via the Open-Meteo API

This module retrieves:
- Temperatures (min, mean, max)
- Reference Evapotranspiration (ET0) calculated via the FAO Penman-Monteith method
- Precipitation

"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from agriwater.utils import coordinates_validation
from agriwater.exceptions import ValidationError, WeatherAPIError

class MeteoAPI:
    """
    Class to interact with the Open-Meteo API and retrieve meteorological data.
    
    Attributes:
        - base_url (str): Base URL for the Open-Meteo Archive API
        - latitude (float): Location latitude (-90 to 90)
        - longitude (float): Location longitude (-180 to 180)
    """

    def __init__(self, latitude: float, longitude: float):
        # We use the Archive API for historical data
        self.base_url = "https://archive-api.open-meteo.com/v1/archive"
        
        # Coordinate validation
        coordinates_validation(latitude,longitude)
        self.latitude = latitude
        self.longitude = longitude
            

    def _calculate_date_range(self, days_count: int) -> tuple[str, str]:
        """
        Calculates the date range for the API request.
        
        - Args: days_count (int): Number of days to retrieve (counting back from today)
        - Returns: tuple[str, str]: (start_date, end_date) in ISO format (YYYY-MM-DD)
        """
        
        today = datetime.today()
        start_date = (today.date() - timedelta(days=days_count)).isoformat()
        end_date = today.date().isoformat()

        return start_date, end_date



    def _parse_response_to_dataframe(self, data: dict, missing_data_strategy:str = "raise") -> pd.DataFrame:
        """
        Converts the API JSON response into a pandas DataFrame. 
        Offers different strategys to deal with missing values
        
        - Args: 
                - data (dict): API JSON response
                - missing_data_strategy (str) : to try different options in case of missing data ("raise","zero","interpolate","drop")
        - Returns: pd.DataFrame: Structured DataFrame with weather data
        - Raises : 
                - WeatherAPIError : If there are missing weather data
                - ValidationError: If the chosen strategy (for missing data) is not correct
        """
        try:
            # Extract daily data
            daily_data = data["daily"]
            
            # Create DataFrame
            df_weather = pd.DataFrame({
                "date": pd.to_datetime(daily_data["time"]),
                "temp_min": daily_data["temperature_2m_min"],
                "temp_mean": daily_data["temperature_2m_mean"],
                "temp_max": daily_data["temperature_2m_max"],
                "et0_fao": daily_data["et0_fao_evapotranspiration"],
                "precipitation": daily_data["precipitation_sum"]
            })
            
            ALLOWED_STRATEGIES = {"raise", "zero", "interpolate", "drop"}
            
            if df_weather.isna().any().any():

                if missing_data_strategy not in ALLOWED_STRATEGIES:
                    raise ValidationError(f"Unknown missing_data_strategy: {missing_data_strategy}")

                if missing_data_strategy == "raise":
                    raise WeatherAPIError(
                        "Missing meteorological data returned by the API."
                    )

                elif missing_data_strategy == "zero":
                    df_weather = df_weather.fillna(0)

                elif missing_data_strategy == "interpolate":
                    df_weather = df_weather.interpolate(method="linear") 
                    # Interpolate strategy is better for temperatures than for precipitations

                elif missing_data_strategy == "drop":
                    df_weather = df_weather.dropna()
            
            return df_weather
        
        except KeyError as e:
            raise WeatherAPIError(f"Unexpected API response format. Missing key: {e}")

    
    def fetch_weather_data(self, days_count: int = 10, missing_data_strategy:str = "raise") -> pd.DataFrame:
        """
        Fetches weather data from the Open-Meteo API.
        
        Args: 
            - days_count (int): Number of days to retrieve (default 10)
            - missing_data_strategy (str) : to try different options in case of missing data ("raise","zero","interpolate","drop")
            
        Returns:
            pd.DataFrame: DataFrame with the following columns:
                - date: Measurement date
                - temp_min: Minimum temperature (°C)
                - temp_mean: Mean temperature (°C)
                - temp_max: Maximum temperature (°C)
                - et0_fao: FAO Reference Evapotranspiration (mm/day)
                - precipitation: Precipitation (mm)
            
        Raises:
            - Validation error: If the day_counts is not correct
            - WeatherAPIError: If the API request fails   

        """
        
        if not isinstance(days_count, int) or days_count <= 0:
            raise ValidationError("days_count must be a positive integer")

        # Calculate dates
        start_date, end_date = self._calculate_date_range(days_count)
        
        # API request parameters
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "daily": "temperature_2m_min,temperature_2m_mean,temperature_2m_max,precipitation_sum,et0_fao_evapotranspiration",
            "start_date": start_date,
            "end_date": end_date,
            "timezone": "auto"  # Automatic timezone based on location
        }
        
        try:
            # API Request
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()  # Raises an exception for HTTP errors
            
            # Extract JSON data
            data = response.json()
            
            # Create DataFrame
            df_weather_data = self._parse_response_to_dataframe(data, missing_data_strategy=missing_data_strategy)
            
            return df_weather_data
            
        except requests.exceptions.Timeout as e:
            raise WeatherAPIError("The weather service timed out. Please check your internet connection.")
        
        except requests.exceptions.HTTPError as e:
            raise WeatherAPIError(f"Weather service returned an error ({response.status_code}): {e}")
        
        except requests.exceptions.RequestException as e:
            raise WeatherAPIError(f"Failed to retrieve weather data for ({self.latitude}, {self.longitude}): {e}")
        
        except KeyError as e:
            raise WeatherAPIError(f"Network error while fetching weather data: {e}")


    def get_location_info(self) -> dict[str,float]:
        """
        Returns location information.
        
        Returns: - dict: Dictionary containing latitude and longitude
        """

        return {
            "latitude": self.latitude,
            "longitude": self.longitude
        }
