"""
Crop database module for loading and managing crop parameters from JSON 
configuration files and providing easy access to : 
- crop coefficients (Kc),
- growth stages,
- irrigation recommendations.

Author: Mounia Tonazzini
Date: December 2025
"""

import json
from pathlib import Path
from typing import Any

class CropDatabase:
    """
    Class to load and manage crop agronomic parameters.
    """
    
    def __init__(self):
        """
        Initializes the crop database.
        """
        
        self.data = self._load_json()



    def _load_json(self) -> dict[str, Any]:
        """
        Loads the crop parameters JSON file.
        
        Returns: dict: Data from the JSON file.
            
        Raises:
            - FileNotFoundError: If the JSON file does not exist.
            - json.JSONDecodeError: If the JSON is poorly formatted.
        """
       
        # Path of the json file
        json_file_name="crops_parameters.json"
        base_dir = Path(__file__).resolve().parent.parent # Project root 
        data_path = base_dir / "data" / json_file_name

        if not data_path.exists():
            raise FileNotFoundError(
                f"The file {json_file_name} was not found."
                "Ensure that crops_parameters.json is in the 'data/' folder."
            )
            
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                crop_dict = json.load(f)
            print(f"\nCrop parameters successfully loaded from '{json_file_name}'")
            return crop_dict
            
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"JSON formatting error in {data_path}: {e}",
                e.doc, e.pos
            )
        


    def get_available_crops(self) -> list[str]:
        """
        Returns the list of available crops.
        
        Returns: List[str]: List of crop names 
        """

        return list(self.data["crops"].keys())
    

    
    def validate_crop_and_stage(self,crop_name: str, crop_stage: str) -> None:
        """
        Validate that the crop and stage exist in the database.
        
        Args:
            - crop_name (str): Crop name to validate
            - crop_stage (str): Growth stage to validate

        Raises:ValueError: If crop or stage is invalid
        """
        # Validate if crop exists
        available_crops = self.get_available_crops()
        crop_name_lower = crop_name.lower()
        
        if crop_name_lower not in available_crops:
            raise ValueError(
                f"Invalid crop: '{crop_name}'. "
                f"Available crops: {', '.join(available_crops)}"
            )
        
        # Validate if stage exists for this crop
        crop_info = self.get_crop_info(crop_name_lower)
        available_stages = list(crop_info["phenological_stages"].keys())
        stage_lower=crop_stage.lower()
        
        if stage_lower not in available_stages:
            raise ValueError(
                f"Invalid stage: '{crop_stage}'. "
                f"Available stages for {crop_name}: {', '.join(available_stages)}"
            )
        
    def crop_exists(self, crop_name: str) -> bool:
        """
        Check if a crop exists in the database.
        
        Args: crop_name (str): Crop name to check
            
        Returns:bool: True if crop exists, False otherwise
        """
        return crop_name.lower() in self.get_available_crops()
    
    
    def stage_exists(self, crop_name: str, crop_stage: str) -> bool:
        """
        Check if a growth stage exists for a given crop.
        
        Args:
            - crop_name (str): Crop name
            - crop_stage (str): Growth stage to check
            
        Returns:
            - bool: True if stage exists for this crop, False otherwise
        """
        crop_info = self.get_crop_info(crop_name)
        if crop_info is None:
            return False
        
        return crop_stage.lower() in crop_info["phenological_stages"]



    def get_crop_info(self, crop_name: str)-> dict[str, Any]| None:
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
            print(f"\nAvailable crops: {', '.join(self.get_available_crops())}")
            return None
            
        return self.data["crops"][crop_name_lower]
    


    def get_kc_for_stage(self, crop_name: str, crop_stage: str) -> float | None:
        """
        Returns the Kc coefficient for a given phenological stage.
        
        Args:
            - crop_name (str): Name of the crop (e.g., 'maize')
            - crop_stage (str): Phenological stage ('initial', 'development', 'mid_season', 'late_season')
            
        Returns:
            - float: Kc value.
            - None: If the crop or stage does not exist.
        """
        
        crop_info = self.get_crop_info(crop_name)
        
        if crop_info is None:
            return None
            
        if crop_stage not in crop_info["phenological_stages"]:
            print(f"Stage '{crop_stage}' not found for crop '{crop_name}'.")
            print(f"Available stages: {', '.join(crop_info['phenological_stages'].keys())}")
            return None
            
        return crop_info["phenological_stages"][crop_stage]["kc"]
    


    def get_irrigation_interval(self, crop_name: str) -> list[int]| None:
        """
        Returns the recommended irrigation interval for a crop.
        
        Args: crop_name (str): Name of the crop.
            
        Returns:
            - List[int]: Recommended intervals in days (e.g., [5, 7] means that the minimum 
            number of days between two waterings is 5 and the maximum is 7).
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
            print(f"Crop '{crop_name}' not found.")
            return
            
        print(f"\n{'-'*60}")
        print(f"{' '*15}{crop_info['full_name']} ({crop_info['scientific_name']})\n")
        print(f"Type: {crop_info['type']}")
        print(f"Description: {crop_info['description']}")
        print(f"Total Cycle: {crop_info['total_cycle_days']} days")
        print(f"Water Stress Sensitivity: {crop_info['water_stress_sensitivity']}")
        print(f"\nKc Coefficients by stage:")
        
        for stage, params in crop_info["phenological_stages"].items():
            readable_stage = stage.replace('_', ' ').title()
            print(f"   • {readable_stage}: Kc = {params['kc']:.2f} ({params['duration_days']} days)")
        
        print(f"\nRecommended Irrigation Interval: {crop_info['irrigation_interval']} days")
        print(f"{'-'*60}\n")


# __________ Example usage for testing __________ 


if __name__ == "__main__":
    
    try:
        # Initialization
        db = CropDatabase()
        
        # Display available crops
        print(f"\nAvailable crops: {db.get_available_crops()}\n")
        
        # Display summary for each crop
        for crop in db.get_available_crops():
            db.display_crop_summary(crop)
            
        # Specific Kc retrieval test
        print("\nTest: Fetching Kc for maize in development stage")
        maize_kc = db.get_kc_for_stage("maize", "development")
        print(f"Maize Kc (development) = {maize_kc}")
        
        # Test validation
        print("\nTest: Validate crop and stage")
        try:
            db.validate_crop_and_stage("maize", "mid_season")
            print("Corn + mid-season is valid")
        except ValueError as e:
            print(f"Error: {e}")
        
        try:
            db.validate_crop_and_stage("banana", "mid_season")
            print("Banana + mid-season is valid")
        except ValueError as e:
            print(f"Expected error caught: {e}")
        
        # Test existence checks
        print("\nTest: Check existence")
        print(f"Maize exists: {db.crop_exists('maize')}")
        print(f"Banana exists: {db.crop_exists('banana')}")
        print(f"Corn has 'mid_season' stage: {db.stage_exists('maize', 'mid_season')}")
        print(f"Wheat has 'invalid_stage': {db.stage_exists('wheat', 'invalid_stage')}")
    
    except Exception as e:
        print(f"Error: {e}")