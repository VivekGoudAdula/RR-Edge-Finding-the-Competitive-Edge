"""Smoke and validation tests for RR EDGE data loading, audit, and utility modules."""

import sys
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.load_data import load_all, get_dataset_info, FILE_REGISTRY
from src.validation.data_audit import profile_dataframe, missing_value_report
from src.validation.relationship_checks import validate_all_relationships
from src.utils.helpers import safe_divide, format_overs, get_innings_phase


def test_load_all_returns_expected_keys():
    """load_all should return a dict with all registry keys."""
    datasets = load_all()
    for key in FILE_REGISTRY:
        assert key in datasets, f"Missing key: {key}"
        assert len(datasets[key]) > 0, f"Empty DataFrame for key: {key}"


def test_ball_by_ball_shape():
    """ball_by_ball should have 200,999 rows and 33 columns."""
    datasets = load_all()
    bbb = datasets["ball_by_ball"]
    assert bbb.shape == (200999, 33), f"Unexpected shape: {bbb.shape}"


def test_no_duplicate_deliveries():
    """No duplicate deliveries by (match_id, innings, innings_ball_num)."""
    datasets = load_all()
    bbb = datasets["ball_by_ball"]
    dups = bbb.duplicated(subset=["match_id", "innings", "innings_ball_num"])
    assert dups.sum() == 0, f"Found {dups.sum()} duplicate deliveries"


def test_all_bbb_matches_in_matches():
    """Every match_id in ball_by_ball should exist in matches."""
    datasets = load_all()
    bbb_ids = set(datasets["ball_by_ball"]["match_id"].unique())
    match_ids = set(datasets["matches"]["match_id"].unique())
    orphans = bbb_ids - match_ids
    assert len(orphans) == 0, f"BBB match_ids not in matches: {orphans}"


def test_relationship_checks_run():
    """validate_all_relationships should return a non-empty list."""
    datasets = load_all()
    results = validate_all_relationships(datasets)
    assert len(results) > 0, "No relationship check results returned"


def test_utils_helpers():
    """Verify utility functions execute correctly."""
    assert safe_divide(10, 2) == 5.0
    assert safe_divide(10, 0, default=-1.0) == -1.0
    assert format_overs(13) == "2.1"
    assert get_innings_phase(5) == "Powerplay"
    assert get_innings_phase(10) == "Middle"
    assert get_innings_phase(18) == "Death"


if __name__ == "__main__":
    test_load_all_returns_expected_keys()
    print("✓ test_load_all_returns_expected_keys")
    test_ball_by_ball_shape()
    print("✓ test_ball_by_ball_shape")
    test_no_duplicate_deliveries()
    print("✓ test_no_duplicate_deliveries")
    test_all_bbb_matches_in_matches()
    print("✓ test_all_bbb_matches_in_matches")
    test_relationship_checks_run()
    print("✓ test_relationship_checks_run")
    test_utils_helpers()
    print("✓ test_utils_helpers")
    print("\nAll tests passed successfully.")
