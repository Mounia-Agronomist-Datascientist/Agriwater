"""
Integration test for the full AgriWater workflow

Tests:
- ETc calculation
- Irrigation calculation
- Visualization generation

Uses mocked weather data to avoid API dependency.

Author: Mounia Tonazzini
Date: December 2025
"""

import os
import pandas as pd
import pytest

from agriwater.evapotranspiration import EvapotranspirationCalculator
from agriwater.visualizations import IrrigationVisualizer
from agriwater.exceptions import ValidationError

# Mocked weather data
def mock_weather_data():
    dates = pd.date_range(start="2025-12-20", periods=7)
    data = pd.DataFrame({
        "date": dates,
        "temp_min": [5, 6, 4, 3, 5, 6, 7],
        "temp_mean": [10, 12, 11, 9, 10, 11, 12],
        "temp_max": [15, 18, 16, 14, 15, 16, 17],
        "et0_fao": [2.5, 2.7, 2.6, 2.4, 2.5, 2.6, 2.7],
        "precipitation": [0, 5, 0, 0, 2, 0, 0]
    })
    return data

# Test full workflow
def test_full_workflow(tmp_path):
    # 1. Prepare weather data
    weather_data = mock_weather_data()
    
    # 2. Initialize ETc calculator
    crop_kc = 1.2
    crop_name = "Corn (Mid-season)"
    etc_calc = EvapotranspirationCalculator(
        weather_data=weather_data,
        crop_kc=crop_kc,
        crop_name=crop_name
    )
    
    # 3. Calculate ETc and irrigation
    etc_df = etc_calc.calculate_etc()
    assert "etc" in etc_df.columns, "ETc column not created"
    assert etc_df["etc"].iloc[0] == pytest.approx(weather_data["et0_fao"].iloc[0] * crop_kc), "ETc value mismatch"
    
    irrigation_results = etc_calc.calculate_irrigation_volume(surface_ha=10, period_days=7)
    
    # Check irrigation results
    for key in ["avg_etc_mm_day", "total_etc_mm", "total_precipitation_mm", 
                "net_irrigation_need_mm", "gross_irrigation_need_mm", 
                "net_volume_m3", "gross_volume_m3"]:
        assert key in irrigation_results, f"{key} missing from irrigation results"
        assert irrigation_results[key] >= 0, f"{key} should be non-negative"
    
    # 4. Initialize visualizer
    viz = IrrigationVisualizer(weather_data=weather_data, crop_name=crop_name, crop_kc=crop_kc)
    
    # 5. Generate all plots in temporary directory
    output_dir = tmp_path
    viz.create_all_plots(surface_ha=10, irrigation_results=irrigation_results, output_dir=output_dir)
    
    # Check that files were created
    expected_files = ["weather_overview.png", "etc_comparison.png", "water_balance.png", "irrigation_recommendation.png"]
    for f in expected_files:
        assert (output_dir / f).exists(), f"{f} was not created"

    print("Full workflow test passed successfully!")

# Run the test if executed directly
if __name__ == "__main__":
    test_full_workflow(tmp_path="./tmp_test_output")
