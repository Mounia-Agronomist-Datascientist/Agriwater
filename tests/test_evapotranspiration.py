"""
Unit tests for the evapotranspiration module.

These tests validate critical calculations for irrigation needs.

Author: Mounia Tonazzini
Date: December 2025
"""

import pytest
import pandas as pd
from src.agriwater.evapotranspiration import EvapotranspirationCalculator
from src.agriwater.utils import convert_mm_to_m3_per_ha, convert_m3_to_mm


class TestEvapotranspirationCalculator:
    """Test suite for EvapotranspirationCalculator class."""
    
    @pytest.fixture
    def sample_weather_data(self):
        """Create sample weather data for testing."""
        return pd.DataFrame({
            'date': pd.date_range(start='2024-12-01', periods=7, freq='D'),
            'et0_fao': [2.0, 2.5, 3.0, 2.8, 2.2, 2.0, 2.5],
            'precipitation': [0, 5.0, 0, 0, 10.0, 0, 0]
        })
    
    @pytest.fixture
    def calculator(self, sample_weather_data):
        """Create a calculator instance with sample data."""
        return EvapotranspirationCalculator(
            weather_data=sample_weather_data,
            crop_kc=1.2,
            crop_name="Test Crop"
        )
    
    
    def test_calculate_etc(self, calculator):
        """Test that ETc is correctly calculated as ET0 x Kc."""
        result = calculator.calculate_etc()
        
        # ETc should be ET0 * 1.2
        expected_etc = [2.4, 3.0, 3.6, 3.36, 2.64, 2.4, 3.0]
        
        assert 'etc' in result.columns, "ETc column should be created"
        assert len(result['etc']) == 7, "Should have 7 days of ETc data"
        
        # Check values with tolerance
        for i, expected in enumerate(expected_etc):
            assert abs(result['etc'].iloc[i] - expected) < 0.01, \
                f"ETc day {i+1} should be {expected}, got {result['etc'].iloc[i]}"
    
    
    def test_calculate_cumulative_precipitation(self, calculator):
        """Test cumulative precipitation calculation."""
        total_precip = calculator.calculate_cumulative_precipitation(period_days=7)
        
        # Sum of sample data: 0 + 5 + 0 + 0 + 10 + 0 + 0 = 15 mm
        assert total_precip == 15.0, f"Total precipitation should be 15 mm, got {total_precip}"
    
    
    def test_calculate_average_etc(self, calculator):
        """Test average ETc calculation."""
        calculator.calculate_etc()
        avg_etc = calculator.calculate_average_etc(period_days=7)
        
        # Average of [2.4, 3.0, 3.6, 3.36, 2.64, 2.4, 3.0] = 2.914...
        expected_avg = 2.914
        
        assert abs(avg_etc - expected_avg) < 0.01, \
            f"Average ETc should be ~{expected_avg} mm/day, got {avg_etc}"
    
    
    def test_calculate_irrigation_need(self, calculator):
        """Test irrigation need calculation (net and gross)."""
        results = calculator.calculate_irrigation_need(period_days=7, efficiency=0.85)
        
        # Expected values
        expected_total_etc = 2.914 * 7  # ~20.4 mm
        expected_total_precip = 15.0  # mm
        expected_net_need = expected_total_etc - expected_total_precip  # ~5.4 mm
        expected_gross_need = expected_net_need / 0.85  # ~6.35 mm
        
        assert abs(results['total_etc_mm'] - expected_total_etc) < 0.1
        assert results['total_precipitation_mm'] == 15.0
        assert abs(results['net_irrigation_need_mm'] - expected_net_need) < 0.1
        assert abs(results['gross_irrigation_need_mm'] - expected_gross_need) < 0.1
    
    
    def test_calculate_irrigation_volume(self, calculator):
        """Test volume calculation in m³."""
        surface_ha = 10.0
        results = calculator.calculate_irrigation_volume(
            surface_ha=surface_ha,
            period_days=7,
            efficiency=0.85
        )
        
        assert 'net_volume_m3' in results
        assert 'gross_volume_m3' in results
        assert results['surface_ha'] == surface_ha
        
        # Volume should be positive
        assert results['net_volume_m3'] >= 0
        assert results['gross_volume_m3'] >= 0
        
        # Gross volume should be >= net volume
        assert results['gross_volume_m3'] >= results['net_volume_m3']
    
    
    def test_no_irrigation_needed(self):
        """Test case where precipitation exceeds ETc (no irrigation needed)."""
        # Create data with high precipitation
        weather_data = pd.DataFrame({
            'date': pd.date_range(start='2024-12-01', periods=7, freq='D'),
            'et0_fao': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            'precipitation': [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0]  # 35 mm total
        })
        
        calc = EvapotranspirationCalculator(
            weather_data=weather_data,
            crop_kc=1.0,
            crop_name="Test"
        )
        
        results = calc.calculate_irrigation_need(period_days=7, efficiency=0.85)
        
        # ETc = 1.0 * 1.0 * 7 = 7 mm
        # Precipitation = 35 mm
        # Net need = 0 (precipitation exceeds need)
        assert results['net_irrigation_need_mm'] == 0, "Should need no irrigation"
        assert results['gross_irrigation_need_mm'] == 0, "Should need no irrigation"
    
    
    def test_invalid_surface_area(self, calculator):
        """Test that negative surface area raises an error."""
        with pytest.raises(ValueError, match="Surface area must be positive"):
            calculator.calculate_irrigation_volume(
                surface_ha=-5.0,
                period_days=7,
                efficiency=0.85
            )
    
    
    def test_kc_validation(self, sample_weather_data):
        """Test that invalid Kc values raise an error."""
        with pytest.raises(ValueError, match="Kc must be between 0 and 2"):
            EvapotranspirationCalculator(
                weather_data=sample_weather_data,
                crop_kc=3.0,  # Invalid Kc
                crop_name="Test"
            )


class TestUtilityFunctions:
    """Test suite for utility conversion functions."""
    
    def test_convert_mm_to_m3_per_ha(self):
        """Test mm to m³/ha conversion."""
        # 1 mm = 10 m³/ha
        assert convert_mm_to_m3_per_ha(1) == 10
        assert convert_mm_to_m3_per_ha(10) == 100
        assert convert_mm_to_m3_per_ha(0) == 0
        assert convert_mm_to_m3_per_ha(5.5) == 55
    
    
    def test_convert_m3_to_mm(self):
        """Test m³ to mm conversion."""
        # 100 m³ on 5 ha = 2 mm
        assert convert_m3_to_mm(100, 5) == 2.0
        
        # 50 m³ on 1 ha = 5 mm
        assert convert_m3_to_mm(50, 1) == 5.0
        
        # 0 m³ = 0 mm
        assert convert_m3_to_mm(0, 10) == 0
    
    
    def test_convert_m3_to_mm_invalid_surface(self):
        """Test that negative surface raises an error."""
        with pytest.raises(ValueError, match="Surface area must be positive"):
            convert_m3_to_mm(100, -5)
        
        with pytest.raises(ValueError, match="Surface area must be positive"):
            convert_m3_to_mm(100, 0)
    
    
    def test_conversion_round_trip(self):
        """Test that converting back and forth returns the original value."""
        original_mm = 15.5
        surface_ha = 8.0
        
        # Convert mm → m³ → mm
        m3_total = convert_mm_to_m3_per_ha(original_mm) * surface_ha
        back_to_mm = convert_m3_to_mm(m3_total, surface_ha)
        
        assert abs(back_to_mm - original_mm) < 0.0001, \
            "Round-trip conversion should return original value"


# Run tests with: pytest tests/test_evapotranspiration.py -v