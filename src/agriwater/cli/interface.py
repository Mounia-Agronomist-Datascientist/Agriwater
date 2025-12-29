"""
This script provides an interactive command-line interface to calculate
irrigation needs based on FAO-56 methodology.

Author: Mounia Tonazzini
Date: December 2025
"""

import logging

# Import created classes and functions
from agriwater.crop_database import CropDatabase
from agriwater.irrigation_calculator import IrrigationCalculator
from agriwater.visualizations import IrrigationVisualizer
from agriwater.utils import coordinates_validation
from agriwater.exceptions import ValidationError, WeatherAPIError, CropDataError
from agriwater.cli.agronomic_report import display_complete_agronomic_summary


# Tools for CLI visualisation
from rich.console import Console
from rich.prompt import Prompt, FloatPrompt, IntPrompt


class AgriWaterCLI:
    """
    Command-line interface for AgriWater irrigation calculator.
    """
    
    def __init__(self):
        """Initializes the CLI interface."""
        self.console = Console()
        self.crop_db = CropDatabase()
        self.calculator = None
        self.results: dict | None = None

    

    def print_header(self) -> None:
        """Prints application title and how it works."""
     
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
        self.console.print("\nWelcome to Agriwater, a water requirement calculator designed to help you evaluate your irrigation needs.")
        self.console.print("\nYou will be asked to configure the following parameters in order:\n") 
        self.console.print("- 'Location Configuration' section : Select a location from the list below or enter custom coordinates,")
        self.console.print("- 'Crop Parameters' section : Select your crop, its growth stage, and the total area in hectares,")
        self.console.print("- 'Analysis Parameters' section : Set the number of previous days for weather data collection and your irrigation efficiency,")
        self.console.print("- 'Missing data handling strategy' section : Choose how to handle missing weather records,")
        self.console.print("\nFor each selection, a default value is shown in parentheses.")
        self.console.print("The application will process this information to provide the required irrigation volume and a detailed report.")
        

    def get_location(self) -> tuple[float, float]:
        """
        Gets location coordinates from user.
        
        Returns: 
            tuple[float, float]: (latitude, longitude)
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
        
        self.console.print("\nLocations:\n")
        for key, (name, _, _) in locations.items():
            self.console.print(f"{key}. {name}")
        
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
                            self.console.print("[red]Invalid coordinates. Please try again.[/red]")
                            continue
                    
                    except ValueError:
                        self.console.print("[red]Invalid input. Please enter valid numbers.[/red]")
                        continue
                
                self.console.print(f"Selected: {name if name != 'Custom' else 'Custom location'}")
                self.console.print(f"Coordinates: ({lat:.4f}, {lon:.4f})")
                return lat, lon
            else:
                self.console.print("Invalid choice. Please try again.")
    
    

    def get_crop_selection(self) -> tuple[str, str]:
        """
        Gets crop and growth stage selection from user.
        
        Returns:
            tuple[str, str]: (crop_name, crop_stage)
        """

        self.console.print("\n[bold]--- Crop Parameters ---[/bold]", style="bright_green")
        
        # Get available crops
        available_crops = self.crop_db.get_available_crops()
        
        # Display crops
        self.console.print("\nAvailable crops:\n")
        for idx, crop in enumerate(available_crops, 1):
            crop_info = self.crop_db.get_crop_info(crop)
            self.console.print(f"   {idx}. {crop_info['full_name']} ({crop})")
        
        # Get crop selection
        while True:
            try:
                crop_idx = IntPrompt.ask("\nSelect crop number", default=4)

                if 1 <= crop_idx <= len(available_crops):
                    crop_name = available_crops[crop_idx - 1]
                    break
                else:
                    self.console.print(f"[red]Please enter a number between 1 and {len(available_crops)}.[/red]")
            except ValueError:
                self.console.print("[red]Invalid input. Please enter a number.[/red]")
        
        # Get crop info
        crop_info = self.crop_db.get_crop_info(crop_name)
        self.console.print(f"\nSelected crop: {crop_info['full_name']}")
        
        # Display growth stages
        stages = list(crop_info["phenological_stages"].keys())
        self.console.print(f"\nGrowth stages for {crop_info['full_name']}:\n")
        for idx, stage in enumerate(stages, 1):
            stage_info = crop_info["phenological_stages"][stage]
            self.console.print(f"   {idx}. {stage.replace('_', ' ').title()} (Kc = {stage_info['kc']:.2f})")
        
        # Get stage selection
        while True:
            try:
                stage_idx = IntPrompt.ask("\nSelect growth stage", default=3)

                if 1 <= stage_idx <= len(stages):
                    crop_stage = stages[stage_idx - 1]
                    break
                else:
                    self.console.print(f"[red]Please enter a number between 1 and {len(stages)}.[/red]")
            except ValueError:
                self.console.print("[red]Invalid input. Please enter a number.[/red]")
        
        stage_info = crop_info["phenological_stages"][crop_stage]
        self.console.print(f"Selected stage: {crop_stage.replace('_', ' ').title()} (Kc = {stage_info['kc']:.2f})")
        
        return crop_name, crop_stage
    
    

    def get_surface_area(self) -> float:
        """
        Gets surface area from user in hectares.
        """
        
        while True:
            try:
                area = FloatPrompt.ask("\nEnter field area in hectares", default=10.0)

                if area > 0:
                    self.console.print(f"Area set to: {area:.2f} ha")
                    return area
                else:
                    self.console.print("[red]Area must be a positive number.[/red]")
            except ValueError:
                self.console.print("[red]Invalid input. Please enter a number.[/red]")
    
    

    def get_analysis_parameters(self) -> tuple[int, float]:
        """
        Gets analysis parameters (period and efficiency).
        
        Returns:
            tuple[int, float]: (period_days, efficiency).
        """

        self.console.print("\n[bold]--- Analysis Parameters ---[/bold]", style="bright_green")
        
        # Period
        while True:
            try:
                period = IntPrompt.ask("\nAnalysis period (days)", default=7)
                
                if period > 0:
                    break
                else:
                    self.console.print("[red]Period must be positive.[/red]")
            except ValueError:
                self.console.print("[red]Invalid input. Please enter a valid number.[/red]")
        
        # Efficiency
        while True:
            try:
                efficiency = FloatPrompt.ask("\nIrrigation efficiency (0-1)", default=0.85)

                if 0 < efficiency <= 1:
                    break
                else:
                    self.console.print("[red]Efficiency must be between 0 and 1.[/red]")
            except ValueError:
                self.console.print("[red]Invalid input. Please enter a valid number.[/red]")
        
        self.console.print(f"Period: {period} days, Efficiency: {efficiency*100:.0f}%")
        return period, efficiency
    
    

    def run_calculation_flow(self) -> bool:
        """
        Runs the interactive CLI application with error handling.

        Returns:
            True if the user wants to run a new analysis, False otherwise.
        """
        
        try:
            # Step 1: Get location
            latitude, longitude = self.get_location()
            
            # Step 2: Get crop selection
            crop_name, crop_stage = self.get_crop_selection()
            
            # Step 3: Get surface area
            surface_ha = self.get_surface_area()
            
            # Step 4: Get analysis parameters
            period_days, efficiency = self.get_analysis_parameters()
            
            # Step 5 : Missing data strategy choice
            self.console.print("\n--- [bold]Missing data handling strategy ---[/bold]", style="bright_green")
            strategy = Prompt.ask(
                "\nSelect a missing data handling strategy", 
                choices=["raise", "zero", "interpolate", "drop"], 
                default="raise"
            )
            
            # Step 6: Initialize calculator
            self.console.print("\n[bold]Initializing calculator...[/bold]", style="cyan")
            self.calculator = IrrigationCalculator(
                latitude=latitude,
                longitude=longitude,
                crop_name=crop_name,
                crop_stage=crop_stage,
                surface_ha=surface_ha,
                missing_data_strategy=strategy
            )
            
            # Step 8: Display results after calculation
            self.console.print("\n[bold]Processing weather data and calculating irrigation needs...[/bold]", style="cyan")
            summary = self.calculator.generate_agronomic_summary(period_days=period_days,efficiency=efficiency)
            self.results = summary
            display_complete_agronomic_summary(self.console,summary)

            # Step 9: Ask for additional actions
            return self.post_calculation_menu(period_days, efficiency)
        
        except (ValidationError, CropDataError) as e:
            self.console.print(f"\n[red]Input Error:[/red] {e}")
            return True # Allow retry
        except WeatherAPIError as e:
            self.console.print(f"\n[red]Weather Service Error:[/red] {e}")
            return False
        except KeyboardInterrupt:
            self.console.print("\n\n[orange1]Operation cancelled by user. Goodbye![/orange1]")
            return False
        

    def post_calculation_menu(self, period_days: int, efficiency: float) -> bool:
        """
        Displays a menu for additional actions after calculation.
        
        Args:
            - period_days (int): Analysis period
            - efficiency (float): Irrigation efficiency

        Returns :  True if the user wants to run a new analysis, False otherwise
        """

        while True:
            self.console.print("\n[bold]====== Additional Actions ======\n[/bold]", style="bright_green")
            self.console.print("   1. Export results to CSV")
            self.console.print("   2. Create visualizations")
            self.console.print("   3. Display crop information")
            self.console.print("   4. Run a new calculation")
            self.console.print("   5. Exit")
            
            choice = Prompt.ask("\nSelect an action", choices=["1", "2", "3", "4", "5"], default="5")
       
            if choice == "1":
                # Export CSV
                filename = Prompt.ask("Enter filename", default= 'irrigation_results.csv')
                path,df = self.calculator.export_results_to_csv(
                    filename=filename,
                    period_days=period_days,
                    efficiency=efficiency
                )
                self.console.print(f"[green]File saved successfully at:[/green] {path.absolute()}")
            
            elif choice == "2":
                result = self.results
                if result is None:
                    self.console.print("[red]No results available. Please run a calculation first.[/red]")
                
                self.console.print("\n[bold green]Irrigation Results[/bold green]")
                for key, value in result.items():
                    self.console.print(f"- {key.replace('_', ' ').title()}: {value:.2f}")
                
                output_dir = input("Enter output directory [default: output]: ").strip() or "output"
                self.console.print(f"\nCreating visualizations in '{output_dir}/'...")
                
                # Create visualizations
                visualizer = IrrigationVisualizer(
                    weather_data = self.calculator.weather_data,
                    crop_name = self.calculator.crop_name,
                    crop_kc = self.calculator.crop_kc
                )
                visualizer.create_all_plots(surface_ha=self.calculator.surface_ha,irrigation_results=result)
            
            elif choice == "3":
                # Display crop info
                crop_summary = self.crop_db.get_crop_summary(crop_name=self.calculator.crop_name)
                self.console.print("\n[bold]Crop summary[/bold]\n")
                self.console.print(crop_summary)
                
            
            elif choice == "4":
                # New calculation
                return True
            
            elif choice == "5":
                # Exit
                self.console.print("\nThank you for using AgriWater! Goodbye!")
                return False
            
            else:
                self.console.print("[red]Invalid choice. Please try again.[/red]")

    
    
    def start(self):
        """Main loop to avoid recursion"""
       
        self.print_header()
        keep_running = True
        while keep_running:
            keep_running = self.run_calculation_flow()
    