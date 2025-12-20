"""
Utility module for loading crop parameters and other helper functions.

Author: Mounia Tonazzini
Date: December 2025
"""

import json
import os
from typing import Dict, List, Optional

class CropDatabase:
    """
    Class to load and manage crop agronomic parameters.
    """
    
    def __init__(self, json_path: str = "../data/crops_parameters.json"):
        """
        Initializes the crop database.
        
        Args: json_path (str): Path to the parameters JSON file.
        """
        self.json_path = json_path
        self.data = self._load_json()



    def _load_json(self) -> dict:
        """
        Loads the crop parameters JSON file.
        
        Returns: dict: Data from the JSON file.
            
        Raises:
            FileNotFoundError: If the JSON file does not exist.
            json.JSONDecodeError: If the JSON is poorly formatted.
        """
        if not os.path.exists(self.json_path):
            raise FileNotFoundError(
                f"The file {self.json_path} was not found. "
                "Ensure that crops_parameters.json is in the 'data/' folder."
            )
            
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Crop parameters successfully loaded from {self.json_path}")
            return data
            
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"JSON formatting error in {self.json_path}: {e}",
                e.doc, e.pos
            )
        


    def get_available_crops(self) -> List[str]:
        """
        Returns the list of available crops.
        
        Returns: List[str]: List of crop names 
        """

        return list(self.data["crops"].keys())
    


    def get_crop_info(self, crop_name: str):
        """
        Returns all information for a specific crop.
        
        Args: crop_name (str): Name of the crop (e.g., 'maize')
            
        Returns:
            - Dict: Dictionary containing all crop parameters.
            - None: If the crop is not found.
        """
        crop_name_lower = crop_name.lower()
        
        if crop_name_lower not in self.data["crops"]:
            print(f"Crop '{crop_name}' not found.")
            print(f"Available crops: {', '.join(self.get_available_crops())}")
            return None
            
        return self.data["crops"][crop_name_lower]
    


    def get_kc_for_stage(self, crop_name: str, stage: str):
        """
        Returns the Kc coefficient for a given phenological stage.
        
        Args:
            - crop_name (str): Name of the crop (e.g., 'maize')
            - stage (str): Phenological stage ('initial', 'development', 'mid_season', 'late_season')
            
        Returns:
            - float: Kc value.
            - None: If the crop or stage does not exist.
        """
        crop_info = self.get_crop_info(crop_name)
        
        if crop_info is None:
            return None
            
        if stage not in crop_info["phenological_stages"]:
            print(f"Stage '{stage}' not found for crop '{crop_name}'.")
            print(f"Available stages: {', '.join(crop_info['phenological_stages'].keys())}")
            return None
            
        return crop_info["phenological_stages"][stage]["kc"]
    


    def get_irrigation_interval(self, crop_name: str) -> Optional[List[int]]:
        """
        Returns the recommended irrigation interval for a crop.
        
        Args: crop_name (str): Name of the crop.
            
        Returns:
           - List[int]: Recommended intervals in days (e.g., [5, 7]).
            - None: If the crop is not found.
        """
        crop_info = self.get_crop_info(crop_name)
        
        if crop_info is None:
            return None
            
        return crop_info["irrigation_interval"]
    


    def display_crop_summary(self, crop_name: str) -> None:
        """
        Displays a summary of a crop's parameters.
        
        Args: crop_name (str): Name of the crop.
        """
        crop_info = self.get_crop_info(crop_name)
        
        if crop_info is None:
            return
            
        print(f"\n{'-'*60}")
        print(f"{' '*15}{crop_info['full_name']}({crop_info['scientific_name']})\n")
        print(f"Type: {crop_info['type']}")
        print(f"Description: {crop_info['description']}")
        print(f"Total Cycle: {crop_info['total_cycle_days']} days")
        print(f"Water Stress Sensitivity: {crop_info['water_stress_sensitivity']}")
        print(f"\n Kc Coefficients by Stage:")
        
        for stage, params in crop_info["phenological_stages"].items():
            readable_stage = stage.replace('_', ' ').title()
            print(f"   • {readable_stage}: Kc = {params['kc']:.2f} ({params['duration_days']} days)")
        
        print(f"\nRecommended Irrigation Interval: {crop_info['irrigation_interval']} days")
        print(f"{'-'*60}\n")



def format_number(value: float, decimals: int = 2) -> str:
    """
    Formats a number with a specified number of decimal places.
    
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
    Convert mm of water to m³ per hectare.
    
    Args: mm (float): Water depth in millimeters
    
    Returns:float: Water volume in m³/ha
    """

    return mm * 10  # 1 mm = 10 m³/ha



def convert_m3_to_mm(m3: float, surface_ha: float) -> float:
    """
    Convert m³ of water to mm for a given surface area.
    
    Args:
        - m3 (float): Water volume in m³
        - surface_ha (float): Surface area in hectares
    
    Returns:float: Water depth in mm
    """

    return m3 / (10 * surface_ha)  # m³ / (10 * ha) = mm



# __________ Example usage for testing __________ 

if __name__ == "__main__":
    
    try:
        # Initialization
        db = CropDatabase()
        
        # Display available crops
        print(f"Available crops: {db.get_available_crops()}\n")
        
        # Display summary for each crop
        for crop in db.get_available_crops():
            db.display_crop_summary(crop)
            
        # Specific Kc retrieval test
        print("\nTest: Fetching Kc for maize in development stage")
        maize_kc = db.get_kc_for_stage("maize", "development")
        print(f"Maize Kc (development) = {maize_kc}")
        
        # Non-existent crop test
        print("\nTest: Non-existent crop")
        db.get_crop_info("banana")
        
    except Exception as e:
        print(f"Error: {e}")