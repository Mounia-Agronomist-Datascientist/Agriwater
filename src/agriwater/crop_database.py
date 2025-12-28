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
from agriwater.exceptions import ValidationError, CropDataError

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
        base_dir = Path(__file__).resolve().parent # agriwater folder
        data_path = base_dir / "data" / json_file_name

        if not data_path.exists():
            raise FileNotFoundError(
                f"The file {json_file_name} was not found."
                "Ensure that crops_parameters.json is in the 'data/' folder."
            )
            
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                crop_dict = json.load(f)
            return crop_dict
            
        except json.JSONDecodeError as e:
            raise CropDataError(f"Invalid JSON format in {data_path}: {e}")
        

    def get_available_crops(self) -> list[str]:
        """
        Returns the list of available crops.
        
        Returns: List[str]: List of crop names 
        """

        return list(self.data["crops"].keys())
    

    
    def validate_crop_and_stage(self,crop_name: str, crop_stage: str) -> None:
        """
        Validates that the crop and stage exist in the database.
        
        Args:
            - crop_name (str): Crop name to validate
            - crop_stage (str): Growth stage to validate

        Raises: ValidationError: If crop or stage is invalid
        """
        
        # Validate if crop exists
        available_crops = self.get_available_crops()
        crop_name_lower = crop_name.lower()
        
        if crop_name_lower not in available_crops:
            raise ValidationError(
                f"Invalid crop: '{crop_name}'. "
                f"Available crops: {', '.join(available_crops)}"
            )
        
        # Validate if the crop and its stage exist
        crop_info = self.get_crop_info(crop_name_lower)
        available_stages = list(crop_info["phenological_stages"].keys())
        stage_lower=crop_stage.lower()
        
        if stage_lower not in available_stages:
            raise ValidationError(
                f"Invalid stage: '{crop_stage}'. "
                f"Available stages for {crop_name}: {', '.join(available_stages)}"
            )
        
    def crop_exists(self, crop_name: str) -> bool:
        """
        Checks if a crop exists in the database.
        
        Args: crop_name (str): Crop name to check
            
        Returns: bool: True if crop exists, False otherwise
        """
        
        return crop_name.lower() in self.get_available_crops()
    
    
    def stage_exists(self, crop_name: str, crop_stage: str) -> bool:
        """
        Checks if a growth stage exists for a given crop.
        
        Args:
            - crop_name (str): Crop name
            - crop_stage (str): Growth stage to check
            
        Returns:
            - bool: True if stage exists for this crop, False otherwise

        Raises: CropDataError: if the crop is missing
        """
        crop_info = self.get_crop_info(crop_name)
        
        return crop_stage.lower() in crop_info["phenological_stages"]



    def get_crop_info(self, crop_name: str)-> dict[str, Any]:
        """
        Returns all information for a specific crop.
        
        Args: crop_name (str): Name of the crop (e.g., 'maize')
            
        Returns: dict: Dictionary containing all crop parameters.

        Raises : CropDataError: if the crop is missing
        """
        
        crop_name_lower = crop_name.lower()
        
        if crop_name_lower not in self.data["crops"]:
            raise CropDataError(f"Crop '{crop_name}' not found in the database.")
            
        return self.data["crops"][crop_name_lower]
    


    def get_kc_for_stage(self, crop_name: str, crop_stage: str) -> float :
        """
        Returns the Kc coefficient for a given phenological stage.
        
        Args:
            - crop_name (str): Name of the crop (e.g., 'maize')
            - crop_stage (str): Phenological stage ('initial', 'development', 'mid_season', 'late_season')
            
        Returns: float: Kc value.

        Raises: CropDataError: if the stage is missing
        """
        
        crop_info = self.get_crop_info(crop_name)
            
        if crop_stage not in crop_info["phenological_stages"]:
            raise CropDataError(f"Stage '{crop_stage}' not found for crop '{crop_name}'.")
            
        return crop_info["phenological_stages"][crop_stage]["kc"]
    


    def get_irrigation_interval(self, crop_name: str) -> list[int]:
        """
        Returns the recommended irrigation interval for a crop.
        
        Args: crop_name (str): Name of the crop.
            
        Returns:
            - List[int]: Recommended intervals in days (e.g., [5, 7] means that the minimum 
            number of days between two waterings is 5 and the maximum is 7).
        
        Raises: CropDataError: if the crop is missing
            
        """
        
        return self.get_crop_info(crop_name)["irrigation_interval"]



    def get_crop_summary(self, crop_name: str) -> dict[str, Any]:
        """
        Returns a structured summary of a crop's parameters.
        
        Args: crop_name (str): Name of the crop.

        Raises: CropDataError: if the crop is missing
        """
        crop_info = self.get_crop_info(crop_name)

        return {
            "full_name": crop_info["full_name"],
            "scientific_name": crop_info["scientific_name"],
            "type": crop_info["type"],
            "description": crop_info["description"],
            "total_cycle_days": crop_info["total_cycle_days"],
            "water_stress_sensitivity": crop_info["water_stress_sensitivity"],
            "phenological_stages": {
                stage: {
                    "kc": params["kc"],
                    "duration_days": params["duration_days"]
                }
                for stage, params in crop_info["phenological_stages"].items()
            },
            "irrigation_interval": crop_info["irrigation_interval"]
        }

