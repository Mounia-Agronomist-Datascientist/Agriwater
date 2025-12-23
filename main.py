"""
AgriWater - Irrigation Needs Calculator
Main script with interactive CLI interface

This script provides an interactive command-line interface to calculate
irrigation needs based on FAO-56 methodology.

Author: Mounia Tonazzini
Date: December 2025
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import created classes and functions
from src.irrigation_calculator import IrrigationCalculator
from src.crop_database import CropDatabase
from src.visualizations import IrrigationVisualizer
from src.utils import coordinates_validation

# Tools for CLI visualisation
from rich.console import Console
from rich.prompt import Prompt, FloatPrompt, IntPrompt

class AgriWaterCLI:
    """
    Command-line interface for AgriWater irrigation calculator.
    """
    
    def __init__(self):
        """Initialize the CLI interface."""
        self.console = Console()
        self.crop_db = CropDatabase()
        self.calculator = None
    
    
    def print_header(self) -> None:
        """Print application  and the way it works."""
     
        header = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║                AGRIWATER - IRRIGATION CALCULATOR              ║
    ║                                                               ║
    ║           Calculate irrigation needs based on FAO-56          ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
            """
        self.console.print(header, style="bright_green")
        print("Welcome to Agriwater, a water need calculation tool to help you evaluate your need of watering your culture.")
        print("You will have to select several parameters in the following order") 
        print("- 'Location Configuration' section : Your location (among a predefined list or your personalized coordinates),")
        print("- 'Crop Parameters' section : Your crop, its stage of growth, and the surface,")
        print("- 'Analysis Parameters' section : The number of last days for the weather data to collect and your irrigation efficiency,")
        print("For each selection you will have to do, a default value is suggested into parenthesis.")
        print("The application will then run will these information and provides you with the irrigation volume (if needed) and a full report.")
        
    
    

    def get_location(self) -> tuple[float, float]:
        """
        Get location coordinates from user.
        
        Returns: Tuple[float, float]: (latitude, longitude)
        """
        
        self.console.print("\n--- [bold]Location Configuration ---[/bold]", style="bright_green")
        
        # Predefined locations
        locations = {
            "1": ("Montpellier, France", 43.6109, 3.8772),
            "2": ("Paris, France", 48.8566, 2.3522),
            "3": ("Lyon, France", 45.7640, 4.8357),
            "4": ("Toulouse, France", 43.6047, 1.4442),
            "5": ("Custom", None, None)
        }
        
        print("\nLocations:\n")
        for key, (name, _, _) in locations.items():
            print(f"{key}. {name}")
        
        while True:
            choice = Prompt.ask("\nSelect a location", choices=list(locations.keys()), default="1")
          
            if choice in locations:
                name, lat, lon = locations[choice]
                
                if choice == "5":
                    # Custom location
                    try:
                        lat = FloatPrompt.ask("Enter latitude (-90 to 90)")
                        lon = FloatPrompt.ask("Enter longitude (-180 to 180)")

                        if coordinates_validation(lat,lon) is not None:
                            print("Invalid coordinates. Please try again.")
                            continue
                    except ValueError:
                        print("Invalid input. Please enter valid numbers.")
                        continue
                
                print(f"Selected: {name if name != 'Custom' else 'Custom location'}")
                print(f"Coordinates: ({lat:.4f}, {lon:.4f})")
                return lat, lon
            else:
                print("Invalid choice. Please try again.")
    
    

    def get_crop_selection(self) -> tuple[str, str]:
        """
        Get crop and growth stage selection from user.
        
        Returns:Tuple[str, str]: (crop_name, crop_stage)
        """

        self.console.print("\n[bold]--- Crop Parameters ---[/bold]", style="bright_green")
        
        # Get available crops
        available_crops = self.crop_db.get_available_crops()
        
        # Display crops
        print("\nAvailable crops:\n")
        for idx, crop in enumerate(available_crops, 1):
            crop_info = self.crop_db.get_crop_info(crop)
            print(f"   {idx}. {crop_info['full_name']} ({crop})")
        
        # Get crop selection
        while True:
            try:
                crop_idx = IntPrompt.ask("\nSelect crop number", default=1)

                if 1 <= crop_idx <= len(available_crops):
                    crop_name = available_crops[crop_idx - 1]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(available_crops)}")
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        # Get crop info
        crop_info = self.crop_db.get_crop_info(crop_name)
        print(f"\nSelected crop: {crop_info['full_name']}")
        
        # Display growth stages
        stages = list(crop_info["phenological_stages"].keys())
        print(f"\nGrowth stages for {crop_info['full_name']}:\n")
        for idx, stage in enumerate(stages, 1):
            stage_info = crop_info["phenological_stages"][stage]
            print(f"   {idx}. {stage.replace('_', ' ').title()} (Kc = {stage_info['kc']:.2f})")
        
        # Get stage selection
        while True:
            try:
                stage_idx = IntPrompt.ask("\nSelect growth stage", default=3)

                if 1 <= stage_idx <= len(stages):
                    crop_stage = stages[stage_idx - 1]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(stages)}")
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        stage_info = crop_info["phenological_stages"][crop_stage]
        print(f"Selected stage: {crop_stage.replace('_', ' ').title()} (Kc = {stage_info['kc']:.2f})")
        
        return crop_name, crop_stage
    
    

    def get_surface_area(self) -> float:
        """
        Get surface area from user.
        
        Returns: float: Surface area in hectares
        """
        while True:
            try:
                surface = FloatPrompt.ask("\nEnter surface area in hectares", default=10.0)

                if surface > 0:
                    print(f"Surface area: {surface:.2f} ha")
                    return surface
                else:
                    print("Surface area must be positive.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")
    
    

    def get_analysis_parameters(self) -> tuple[int, float]:
        """
        Gets analysis parameters (period and efficiency).
        
        Returns:Tuple[int, float]: (period_days, efficiency)
        """

        self.console.print("\n[bold]--- Analysis Parameters ---[/bold]", style="bright_green")
        
        # Period
        while True:
            try:
                period = IntPrompt.ask("\nAnalysis period (days)", default=7)
                
                if period > 0:
                    break
                else:
                    print("Period must be positive.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")
        
        # Efficiency
        while True:
            try:
                efficiency = FloatPrompt.ask("\nIrrigation efficiency (0-1)", default=0.85)

                if 0 < efficiency <= 1:
                    break
                else:
                    print("Efficiency must be between 0 and 1.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")
        
        print(f"Period: {period} days, Efficiency: {efficiency*100:.0f}%")
        return period, efficiency
    


    
    def run(self) -> None:
        """Runs the interactive CLI application."""
        
        self.print_header()
        
        try:
            # Step 1: Get location
            latitude, longitude = self.get_location()
            
            # Step 2: Get crop selection
            crop_name, crop_stage = self.get_crop_selection()
            
            # Step 3: Get surface area
            surface_ha = self.get_surface_area()
            
            # Step 4: Get analysis parameters
            period_days, efficiency = self.get_analysis_parameters()
            
            # Step 5: Initialize calculator
            self.console.print("\n[bold]Initializing calculator...[/bold]", style="cyan")
            
            self.calculator = IrrigationCalculator(
                latitude=latitude,
                longitude=longitude,
                crop_name=crop_name,
                crop_stage=crop_stage,
                surface_ha=surface_ha
            )
            
            # Step 6: Display results
            self.console.print("\n[bold]Calculating irrigation needs...[/bold]", style="cyan")
            
            self.calculator.display_full_report(
                period_days=period_days,
                efficiency=efficiency
            )
            
            # Step 7: Ask for additional actions
            self.post_calculation_menu(period_days, efficiency)
            
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    

    def post_calculation_menu(self, period_days: int, efficiency: float) -> None:
        """
        Displays a menu for additional actions after calculation.
        
        Args:
            - period_days (int): Analysis period
            - efficiency (float): Irrigation efficiency
        """
        while True:
            self.console.print("\n[bold]====== Additional Actions ======\n[/bold]", style="bright_green")
            print("   1. Export results to CSV")
            print("   2. Create visualizations")
            print("   3. Display crop information")
            print("   4. Run a new calculation")
            print("   5. Exit")
            
            choice = Prompt.ask("\nSelect an action", choices=["1", "2", "3", "4", "5"], default="5")
       
            if choice == "1":

                # Export CSV
                filename = input("Enter filename [default: irrigation_results.csv]: ").strip() or "irrigation_results.csv"
                self.calculator.export_results_to_csv(
                    filename=filename,
                    period_days=period_days,
                    efficiency=efficiency
                )
            
            elif choice == "2":
                result_df = self.calculator.calculate_irrigation_needs(period_days=period_days, efficiency=efficiency)
                if result_df is None:
                    print("No results available. Please run a calculation first.")
                    return
                
                output_dir = input("Enter output directory [default: output]: ").strip() or "output"
                print(f"\nCreating visualizations in '{output_dir}/'...")
                
                # Create visualizations
                visualizer = IrrigationVisualizer(
                    weather_data = self.calculator.weather_data,
                    crop_name = self.calculator.crop_name,
                    crop_kc = self.calculator.crop_kc
                )
                visualizer.create_all_plots(surface_ha=self.calculator.surface_ha,irrigation_results=result_df)
            
            elif choice == "3":
                # Display crop info
                self.calculator.get_crop_summary()
            
            elif choice == "4":
                # New calculation
                print("\nStarting new calculation...\n")
                self.run()
                break
            
            elif choice == "5":
                # Exit
                print("\nThank you for using AgriWater! Goodbye!")
                break
            
            else:
                print("Invalid choice. Please try again.")



# _________________MAIN ENTRY POINT _________________

def main():
    """Main entry point for the application."""
    cli = AgriWaterCLI()
    cli.run()


if __name__ == "__main__":
    main()