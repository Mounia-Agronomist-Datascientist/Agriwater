"""
Unit tests for the Crop Database module.

Author: Mounia Tonazzini
Date: December 2025
"""

import pytest
from agriwater.crop_database import CropDatabase
from agriwater.exceptions import ValidationError, CropDataError


# Test 1: Check if the database is loaded and contains a "crop" section
def test_crop_database_loads_data():
    db = CropDatabase()
    
    assert isinstance(db.data, dict)
    assert "crops" in db.data


#  Test 2: Check if the list of crops is not nul
def test_get_available_crops_returns_list():
    db = CropDatabase()
    crops = db.get_available_crops()

    assert isinstance(crops, list)
    assert len(crops) > 0



#  Test 3: Check if a crop exists
def test_known_crop_exists():
    db = CropDatabase()

    assert db.crop_exists("wheat") is True



#  Test 4: Check a non existing crop
def test_unknown_crop_does_not_exist():
    db = CropDatabase()

    assert db.crop_exists("potatoes") is False



# Test 5: Check the validation of crop and stage (should not raise exception)
def test_validate_crop_and_stage_valid():
    db = CropDatabase()
    db.validate_crop_and_stage("wheat", "mid_season")



# Test 6: Check the ValidationError with an invalid crop
def test_validate_invalid_crop_raises_error():
    db = CropDatabase()

    with pytest.raises(ValidationError):
        db.validate_crop_and_stage("invalid_crop", "mid_season")



# Test 7: Check the ValidationError with an invalid stage
def test_validate_invalid_stage_raises_error():
    db = CropDatabase()

    with pytest.raises(ValidationError):
        db.validate_crop_and_stage("wheat", "unknown_stage")


# Test 8: Check the Kc
def test_get_kc_for_stage_returns_float():
    db = CropDatabase()
    
    kc = db.get_kc_for_stage("wheat", "mid_season")

    assert isinstance(kc, float)
    assert kc > 0


# Test 9: Check CropDataError
def test_get_kc_invalid_stage_raises_error():
    db = CropDatabase()

    with pytest.raises(CropDataError):
        db.get_kc_for_stage("wheat", "invalid_stage")


# Test 10: Check interval irrigation
def test_get_irrigation_interval():
    db = CropDatabase()

    interval = db.get_irrigation_interval("wheat")

    assert isinstance(interval, list)
    assert len(interval) == 2
    assert interval[0] < interval[1]


#  Test 11: Check the summary
def test_get_crop_summary_returns_string():
    db = CropDatabase()

    summary = db.get_crop_summary("wheat")

    assert isinstance(summary, str)
    assert "wheat" in summary.lower()
