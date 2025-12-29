"""
Test for display_complete_agronomic_summary function in agronomic_report.py

Author: Mounia Tonazzini
Date: December 2025
"""

import pytest
from rich.console import Console
from agriwater.cli.agronomic_report import display_complete_agronomic_summary
from io import StringIO


def mock_summary(irrigation_required=True):
    return {
        "crop_name": "corn",
        "crop_stage": "mid_season",
        "surface_ha": 10,
        "period_days": 7,
        "efficiency": 0.85,
        "total_etc_mm": 18.5,
        "total_precip_mm": 5.0,
        "recommended_mm": 13.5,
        "recommended_m3_per_ha": 135,
        "recommended_total_m3": 1350,
        "water_balance_mm": -13.5,
        "irrigation_required": irrigation_required
    }


def test_report_irrigation_required(capsys):
    """
    Test that the report displays the irrigation required message
    """
    console = Console(file=StringIO(), width=80)
    summary = mock_summary(irrigation_required=True)
    
    display_complete_agronomic_summary(console, summary)
    
    output = console.file.getvalue()
    
    # Check for key phrases
    assert "IRRIGATION REQUIRED" in output
    assert "Corn (Mid Season)" in output
    assert "Water Need" in output
    assert "Recommended application rate" in output


def test_report_no_irrigation(capsys):
    """
    Test that the report displays the no irrigation needed message
    """
    console = Console(file=StringIO(), width=80)
    summary = mock_summary(irrigation_required=False)
    
    display_complete_agronomic_summary(console, summary)
    
    output = console.file.getvalue()
    
    # Check for key phrases
    assert "NO IRRIGATION NEEDED" in output
    assert "Corn (Mid Season)" in output
    assert "Water Need" in output
    assert "Total volume required" not in output

if __name__ == "__main__":
    test_report_irrigation_required()
    test_report_no_irrigation()
    print("Agronomic report tests passed successfully!")