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
from src.utils import coordinates_validation

class MeteoAPI:
    """
    Class to interact with the Open-Meteo API and retrieve meteorological data.
    
    Attributes:
        - base_url (str): Base URL for the Open-Meteo Archive API
        - latitude (float): Location latitude (-90 to 90)
        - longitude (float): Location longitude (-180 to 180)
    """

    def __init__(self, latitude: float, longitude: float):
      
        self.base_url = "https://archive-api.open-meteo.com/v1/archive"
        
        # Coordinate validation
        coordinates_validation(latitude,longitude)
        self.latitude = latitude
        self.longitude = longitude
            

    def _calculate_date_range(self, days_count: int) -> tuple[str, str]:
        """
        Calculates the date range for the API request.
        
        - Args: days_count (int): Number of days to retrieve (counting back from today)
        - Returns: Tuple[str, str]: (start_date, end_date) in ISO format (YYYY-MM-DD)
        """
        
        today = datetime.today()
        start_date = (today.date() - timedelta(days=days_count)).isoformat()
        end_date = today.date().isoformat()

        return start_date, end_date



    def _parse_response_to_dataframe(self, data: dict) -> pd.DataFrame:
        """
        Converts the API JSON response into a pandas DataFrame.
        
        - Args: data (dict): API JSON response
        - Returns: pd.DataFrame: Structured DataFrame with weather data
        """

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
        
        # Replace None values with 0 (assuming no rain/ET0 if data is missing)
        df_weather = df_weather.fillna(0)
        
        return df_weather

    
    def fetch_weather_data(self, days_count: int = 10) -> pd.DataFrame|None:
        """
        Fetches weather data from the Open-Meteo API.
        
        Args: - days_count (int): Number of days to retrieve (default 10)
            
        Returns:
            pd.DataFrame: DataFrame with the following columns:
                - date: Measurement date
                - temp_min: Minimum temperature (°C)
                - temp_mean: Mean temperature (°C)
                - temp_max: Maximum temperature (°C)
                - et0_fao: FAO Reference Evapotranspiration (mm/day)
                - precipitation: Precipitation (mm)
                - None: If an error occurs
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
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
            df_weather_data = self._parse_response_to_dataframe(data)
            
            print(f"\nWeather data successfully retrieved for {days_count} days")
            print(f"Period: \n- Beginning : {start_date},\n- End : {end_date}")
            
            return df_weather_data
            
        except requests.exceptions.Timeout:
            print("Error: API request timeout. Please check your internet connection.")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Status Code: {response.status_code}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error during weather data retrieval: {e}")
            return None
        except KeyError as e:
            print(f"Error: Missing data in API response: {e}")
            return None


    def get_location_info(self) -> dict[str,int|float]:
        """
        Returns location information.
        
        Returns: - dict: Dictionary containing latitude and longitude
        """

        return {
            "latitude": self.latitude,
            "longitude": self.longitude
        }



# __________ Example usage for testing (Location : Montpellier) __________ 

if __name__ == "__main__":
    # Test with Montpellier
    
    print("\n----- Testing MeteoAPI module with Montpellier coordinates -----\n")
    
    try:
        # Initialization
        meteo = MeteoAPI(latitude=43.6109, longitude=3.8772)
        
        # Display location info
        print(f"Location: {meteo.get_location_info()}\n")
        
        # Fetch 7-day weather data
        df_meteo = meteo.fetch_weather_data(days_count=7)
        
        if df_meteo is not None:
            print("\nData Overview:")
            print(df_meteo.to_string(index=False))
            
            print("\nStatistics:")
            print(f"   - Average ET0: {df_meteo['et0_fao'].mean():.2f} mm/day")
            print(f"   - Total Precipitation: {df_meteo['precipitation'].sum():.2f} mm")
            print(f"   - Mean Temperature: {df_meteo['temp_mean'].mean():.2f} °C")
            
    except ValueError as e:
        print(f"Validation Error: {e}")