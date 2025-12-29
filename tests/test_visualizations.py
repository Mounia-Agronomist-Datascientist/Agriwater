"""
Unit tests for the Visualizations module.

Author: Mounia Tonazzini
Date: December 2025
"""

import pytest
import pandas as pd
import os
import tempfile
from agriwater.visualizations import IrrigationVisualizer
from agriwater.evapotranspiration import EvapotranspirationCalculator


# Setup dummy weather data
@pytest.fixture
def dummy_weather_data():
    # Create a 7-day dummy DataFrame
    data = {
        "date": pd.date_range(start="2025-12-22", periods=7, freq="D"),
        "et0_fao": [4.5, 4.7, 4.2, 4.3, 4.6, 4.8, 4.4],
        "precipitation": [0.0, 5.0, 0.0, 0.0, 2.0, 0.0, 0.0],
        "temp_mean": [12, 13, 12.5, 12.8, 13.2, 12.7, 12.9]
    }
    df = pd.DataFrame(data)
    # Add ETc column
    df['etc'] = df['et0_fao'] * 1.2
    return df


# Test 1: initialization
def test_visualizer_init(dummy_weather_data):
    viz = IrrigationVisualizer(dummy_weather_data, crop_name="Corn", crop_kc=1.2)
    # Check attributes
    assert viz.crop_name == "Corn"
    assert viz.crop_kc == 1.2
    assert 'etc' in viz.weather_data.columns
    assert pd.api.types.is_datetime64_any_dtype(viz.weather_data['date'])


# Test 2: plot_weather_overview
def test_plot_weather_overview(dummy_weather_data):
    viz = IrrigationVisualizer(dummy_weather_data)
    # Test plotting does not raise errors (show plots disabled)
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = os.path.join(tmpdir, "weather_overview.png")
        viz.plot_weather_overview(save_path=save_path)
        # Check that file was created
        assert os.path.exists(save_path)


# Test 3: plot_etc_comparison
def test_plot_etc_comparison(dummy_weather_data):
    viz = IrrigationVisualizer(dummy_weather_data, crop_kc=1.2)
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = os.path.join(tmpdir, "etc_comparison.png")
        viz.plot_etc_comparison(save_path=save_path)
        assert os.path.exists(save_path)


# Test 4: plot_water_balance
def test_plot_water_balance(dummy_weather_data):
    viz = IrrigationVisualizer(dummy_weather_data)
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = os.path.join(tmpdir, "water_balance.png")
        viz.plot_water_balance(period_days=7, save_path=save_path)
        assert os.path.exists(save_path)


# Test 5: plot_irrigation_recommendation
def test_plot_irrigation_recommendation(dummy_weather_data):
    viz = IrrigationVisualizer(dummy_weather_data)
    irrigation_results = {
        'total_etc_mm': 32.0,
        'total_precipitation_mm': 7.0,
        'net_irrigation_need_mm': 25.0,
        'gross_irrigation_need_mm': 29.41,
        'net_volume_m3': 250.0,
        'gross_volume_m3': 294.1
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = os.path.join(tmpdir, "irrigation_recommendation.png")
        viz.plot_irrigation_recommendation(surface_ha=10.0, irrigation_results=irrigation_results, save_path=save_path)
        assert os.path.exists(save_path)


# Test 6: create_all_plots
def test_create_all_plots(dummy_weather_data):
    viz = IrrigationVisualizer(dummy_weather_data)
    irrigation_results = {
        'total_etc_mm': 32.0,
        'total_precipitation_mm': 7.0,
        'net_irrigation_need_mm': 25.0,
        'gross_irrigation_need_mm': 29.41,
        'net_volume_m3': 250.0,
        'gross_volume_m3': 294.1
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        viz.create_all_plots(surface_ha=10.0, irrigation_results=irrigation_results, output_dir=tmpdir)
        # Check that all files exist
        expected_files = [
            "weather_overview.png",
            "etc_comparison.png",
            "water_balance.png",
            "irrigation_recommendation.png"
        ]
        for fname in expected_files:
            assert os.path.exists(os.path.join(tmpdir, fname))
