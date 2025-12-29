"""
Full test for AgriWaterCLI using mocked inputs and weather data.
This test verifies that the CLI can run end-to-end without real user 
input, real weather data, or real database access.

Author: Mounia Tonazzini
Date: December 2025
"""

# test_interface.py
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
from rich.console import Console

# Import your CLI class
from agriwater.cli.interface import AgriWaterCLI

# Mock summary that the calculator would return
mock_summary = {
    "irrigation_required": True,
    "crop_name": "maize",
    "crop_stage": "mid_season",
    "surface_ha": 10.0,
    "period_days": 7,
    "total_etc_mm": 50.0,
    "total_precip_mm": 20.0,
    "recommended_mm": 30.0,
    "recommended_m3_per_ha": 3000.0,
    "recommended_total_m3": 30000.0,
    "water_balance_mm": -10.0,
    "efficiency": 0.85
}

def test_cli_workflow():
    """
    Full workflow test for AgriWaterCLI with mocked user input and calculator.
    This test covers:
      - Location selection
      - Crop selection and growth stage
      - Surface area input
      - Analysis parameters
      - Missing data strategy
      - Post-calculation menu (exit)
    """
    
    # Initialize the CLI object
    cli = AgriWaterCLI()

    # Mock the calculator to return our pre-defined summary
    cli.calculator = MagicMock()
    cli.calculator.generate_agronomic_summary.return_value = mock_summary
    cli.calculator.weather_data = MagicMock()
    cli.calculator.surface_ha = mock_summary["surface_ha"]
    cli.calculator.crop_name = mock_summary["crop_name"]
    cli.calculator.crop_kc = 1.0
    cli.calculator.export_results_to_csv = MagicMock(return_value=(MagicMock(), MagicMock()))

    # Mock CropDatabase to avoid real database access
    cli.crop_db.get_available_crops = MagicMock(return_value=["maize", "wheat", "soybean"])
    cli.crop_db.get_crop_info = MagicMock(return_value={
        "full_name": "maize",
        "phenological_stages": {
            "mid_season": {"kc": 1.2},
            "early": {"kc": 0.8},
            "late": {"kc": 0.9}
        }
    })
    cli.crop_db.get_crop_summary = MagicMock(return_value="maize info summary")

    # Mock inputs for the entire workflow:
    # - Location, crop, stage, surface, period, efficiency, missing data
    # - Post-calculation menu: select "5" to exit
    prompt_side_effect = [
        "1",        # Location: Montpellier
        "raise",    # Missing data handling
        "2",         # Post-calculation menu: Exit
        "5"         # Post-calculation menu: NOW select Exit to break the loop
    ]
    float_side_effect = [10.0, 0.85]  # Surface area, efficiency
    int_side_effect = [
    1,          # get_crop_selection: Select crop number
    1,          # get_crop_selection: Select growth stage
    7           # get_analysis_parameters: Analysis period (days)
    ]

    with patch("agriwater.cli.interface.Prompt.ask", side_effect=prompt_side_effect), \
         patch("agriwater.cli.interface.FloatPrompt.ask", side_effect=float_side_effect), \
         patch("agriwater.cli.interface.IntPrompt.ask", side_effect=int_side_effect), \
         patch("builtins.input", return_value="output"), \
         patch("agriwater.cli.interface.IrrigationVisualizer.create_all_plots") as mock_viz:

        # Redirect console output to a StringIO buffer
        # cli.console = Console(file=StringIO(), width=120)

        # Run the full CLI workflow
        keep_running = cli.run_calculation_flow()

        # Assert that workflow exits after selecting "5" in the post-calculation menu
        assert keep_running is False

        # Optionally, check that visualizations were called
        mock_viz.assert_called()

