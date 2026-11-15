"""
Tests for match-state reconstruction integrity, group-wise cumulative isolation,
scheduled balls resolution, and target reconstruction.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from src.data.load_data import load_all
from src.cricket.competition_config import (
    is_competition_included,
    get_competition_status,
    EXCLUDED_COMPETITION_IDS,
    IPL_COMPETITION_IDS,
)
from src.cricket.match_state import (
    resolve_scheduled_balls,
    reconstruct_match_state,
)


def test_competition_whitelist():
    """Verify explicit competition whitelist rules and exclusion rationales."""
    # Excluded developmental / A-team comps
    assert is_competition_included(2670) is False
    assert is_competition_included(3289) is False

    # Included IPL editions
    assert is_competition_included(1358) is True
    assert is_competition_included(1715) is True
    assert is_competition_included(2193) is True
    assert is_competition_included(2725) is True
    assert is_competition_included(3298) is True

    # Included T20Is
    assert is_competition_included(1331, match_format="T20I") is True

    # Check status and reason
    is_inc, reason = get_competition_status(2670, "Mens T20 Emerging Teams Asia Cup 2024", "T20")
    assert is_inc is False
    assert "A-teams" in reason


def test_scheduled_balls_resolution():
    """Verify innings-specific scheduled ball resolution for standard, shortened, and super overs."""
    # Standard 20 overs
    assert resolve_scheduled_balls(1) == 120
    assert resolve_scheduled_balls(2) == 120

    # Shortened innings (where units are legal balls)
    assert resolve_scheduled_balls(1, first_inn_revised_overs=60.0) == 60
    assert resolve_scheduled_balls(2, second_inn_revised_overs=90.0) == 90
    assert resolve_scheduled_balls(2, second_inn_revised_overs=48.0) == 48

    # Independent innings (Inn 1 scheduled 54, Inn 2 scheduled 30)
    assert resolve_scheduled_balls(1, first_inn_revised_overs=54.0, second_inn_revised_overs=30.0) == 54
    assert resolve_scheduled_balls(2, first_inn_revised_overs=54.0, second_inn_revised_overs=30.0) == 30

    # Super overs
    assert resolve_scheduled_balls(3) == 6
    assert resolve_scheduled_balls(4) == 6


def test_group_wise_cumulative_isolation_synthetic():
    """Verify with synthetic multi-match, multi-innings data that NO state leaks across boundaries."""
    synthetic_bbb = pd.DataFrame([
        # Match 1, Innings 1 (3 balls, total runs = 5, 1 wicket)
        {"match_id": 101, "innings": 1, "innings_ball_num": 1, "runs": 4, "extras1_runs": 0, "extras_2_runs": 0,
         "extras_type": np.nan, "is_wicket": False, "dismissal_type": np.nan, "batting_order": 1, "overid": 1},
        {"match_id": 101, "innings": 1, "innings_ball_num": 2, "runs": 1, "extras1_runs": 0, "extras_2_runs": 0,
         "extras_type": np.nan, "is_wicket": False, "dismissal_type": np.nan, "batting_order": 1, "overid": 1},
        {"match_id": 101, "innings": 1, "innings_ball_num": 3, "runs": 0, "extras1_runs": 0, "extras_2_runs": 0,
         "extras_type": np.nan, "is_wicket": True, "dismissal_type": "Bowled", "batting_order": 2, "overid": 1},

        # Match 1, Innings 2 (2 balls, total runs = 6)
        {"match_id": 101, "innings": 2, "innings_ball_num": 1, "runs": 6, "extras1_runs": 0, "extras_2_runs": 0,
         "extras_type": np.nan, "is_wicket": False, "dismissal_type": np.nan, "batting_order": 1, "overid": 1},
        {"match_id": 101, "innings": 2, "innings_ball_num": 2, "runs": 0, "extras1_runs": 0, "extras_2_runs": 0,
         "extras_type": np.nan, "is_wicket": False, "dismissal_type": np.nan, "batting_order": 1, "overid": 1},

        # Match 102, Innings 1 (first ball must have ZERO state from Match 101)
        {"match_id": 102, "innings": 1, "innings_ball_num": 1, "runs": 2, "extras1_runs": 0, "extras_2_runs": 0,
         "extras_type": np.nan, "is_wicket": False, "dismissal_type": np.nan, "batting_order": 1, "overid": 1},
        {"match_id": 102, "innings": 1, "innings_ball_num": 2, "runs": 0, "extras1_runs": 1, "extras_2_runs": 0,
         "extras_type": "wide", "is_wicket": False, "dismissal_type": np.nan, "batting_order": 1, "overid": 1},
    ])

    synthetic_matches = pd.DataFrame([
        {"match_id": 101, "revised_target": np.nan, "first_inn_revised_overs": np.nan, "second_inn_revised_overs": np.nan, "result": "Team B won"},
        {"match_id": 102, "revised_target": np.nan, "first_inn_revised_overs": np.nan, "second_inn_revised_overs": np.nan, "result": "Team A won"},
    ])

    reconstructed = reconstruct_match_state(synthetic_bbb, synthetic_matches)

    # 1. First ball of Match 101, Innings 1: all pre-delivery metrics must be 0
    m101_inn1_b1 = reconstructed.iloc[0]
    assert m101_inn1_b1["current_score_before"] == 0
    assert m101_inn1_b1["wickets_lost_before"] == 0
    assert m101_inn1_b1["legal_balls_bowled_before"] == 0
    assert m101_inn1_b1["wickets_remaining_before"] == 10
    assert m101_inn1_b1["balls_remaining_before"] == 120

    # 2. Third ball of Match 101, Innings 1: score_before = 4 + 1 = 5, legal_balls = 2
    m101_inn1_b3 = reconstructed.iloc[2]
    assert m101_inn1_b3["current_score_before"] == 5
    assert m101_inn1_b3["wickets_lost_before"] == 0
    assert m101_inn1_b3["legal_balls_bowled_before"] == 2

    # 3. First ball of Match 101, Innings 2: MUST RESET TO ZERO (no carry-over from Inn 1)
    m101_inn2_b1 = reconstructed.iloc[3]
    assert m101_inn2_b1["current_score_before"] == 0, "Score leaked across innings!"
    assert m101_inn2_b1["wickets_lost_before"] == 0, "Wickets leaked across innings!"
    assert m101_inn2_b1["legal_balls_bowled_before"] == 0, "Balls leaked across innings!"
    assert m101_inn2_b1["innings_target"] == 6.0  # Inn 1 score (5) + 1
    assert m101_inn2_b1["target_certainty"] == "CERTAIN"
    assert m101_inn2_b1["required_runs_before"] == 6.0

    # 4. First ball of Match 102, Innings 1: MUST RESET TO ZERO (no carry-over from Match 101)
    m102_inn1_b1 = reconstructed.iloc[5]
    assert m102_inn1_b1["current_score_before"] == 0, "Score leaked across matches!"
    assert m102_inn1_b1["wickets_lost_before"] == 0, "Wickets leaked across matches!"
    assert m102_inn1_b1["legal_balls_bowled_before"] == 0, "Balls leaked across matches!"

    # 5. Wide handling on ball 2 of Match 102:
    # Ball 2 is a wide, so legal_balls_bowled_before is 1 (from ball 1).
    m102_inn1_b2 = reconstructed.iloc[6]
    assert m102_inn1_b2["current_score_before"] == 2
    assert m102_inn1_b2["legal_balls_bowled_before"] == 1
    assert not m102_inn1_b2["is_legal_ball"]


def test_actual_dataset_group_wise_integrity():
    """Run regression test on actual dataset sample proving zero carry-over at all innings starts."""
    datasets = load_all()
    bbb = datasets["ball_by_ball"]
    matches = datasets["matches"]

    # Test on a diverse subset of 10 matches (including standard, DLS, and super over)
    test_match_ids = [13511, 13612, 16754, 17765, 21586, 34429, 40725, 40727, 48029, 50359]
    sample_bbb = bbb[bbb["match_id"].isin(test_match_ids)].copy()
    sample_matches = matches[matches["match_id"].isin(test_match_ids)].copy()

    reconstructed = reconstruct_match_state(sample_bbb, sample_matches)

    # For EVERY (match_id, innings) group:
    for (mid, inn), grp in reconstructed.groupby(["match_id", "innings"]):
        first_delivery = grp.iloc[0]
        assert first_delivery["current_score_before"] == 0, (
            f"Leakage detected: Match {mid}, Innings {inn} first ball has score_before={first_delivery['current_score_before']}"
        )
        assert first_delivery["wickets_lost_before"] == 0, (
            f"Leakage detected: Match {mid}, Innings {inn} first ball has wickets_before={first_delivery['wickets_lost_before']}"
        )
        assert first_delivery["legal_balls_bowled_before"] == 0, (
            f"Leakage detected: Match {mid}, Innings {inn} first ball has balls_before={first_delivery['legal_balls_bowled_before']}"
        )
        assert first_delivery["wickets_remaining_before"] == 10

        # Verify final reconstructed total matches sum of total_delivery_runs
        final_delivery = grp.iloc[-1]
        reconstructed_final_score = final_delivery["current_score_before"] + final_delivery["total_delivery_runs"]
        actual_total = grp["total_delivery_runs"].sum()
        assert reconstructed_final_score == actual_total, (
            f"Total mismatch: Match {mid}, Innings {inn}: reconstructed {reconstructed_final_score} != actual {actual_total}"
        )


def test_dls_target_certainty_flagging():
    """Verify that DLS matches are explicitly tagged with UNCERTAIN_DLS_TIMING."""
    datasets = load_all()
    bbb = datasets["ball_by_ball"]
    matches = datasets["matches"]

    # Match 21586 is IPL 2023 Final (revised target 171)
    dls_mid = 21586
    m_bbb = bbb[bbb["match_id"] == dls_mid]
    m_mat = matches[matches["match_id"] == dls_mid]

    reconstructed = reconstruct_match_state(m_bbb, m_mat)
    inn2 = reconstructed[reconstructed["innings"] == 2]

    # Target should be 171 and certainty should be UNCERTAIN_DLS_TIMING
    assert (inn2["innings_target"] == 171.0).all()
    assert (inn2["target_certainty"] == "UNCERTAIN_DLS_TIMING").all()
    assert (inn2["scheduled_innings_balls"] == 90).all()


def test_batting_order_raw_preserved():
    """Verify that batting_order_raw preserves all values without clamping (including 12 and 13)."""
    datasets = load_all()
    bbb = datasets["ball_by_ball"]
    matches = datasets["matches"]

    # Match 48029 contains batting order 12 and 13
    mid = 48029
    m_bbb = bbb[bbb["match_id"] == mid]
    m_mat = matches[matches["match_id"] == mid]

    reconstructed = reconstruct_match_state(m_bbb, m_mat)

    # Check that 12 and 13 are present in batting_order_raw
    assert 12 in reconstructed["batting_order_raw"].values
    assert 13 in reconstructed["batting_order_raw"].values


if __name__ == "__main__":
    test_competition_whitelist()
    print("✓ test_competition_whitelist")
    test_scheduled_balls_resolution()
    print("✓ test_scheduled_balls_resolution")
    test_group_wise_cumulative_isolation_synthetic()
    print("✓ test_group_wise_cumulative_isolation_synthetic")
    test_actual_dataset_group_wise_integrity()
    print("✓ test_actual_dataset_group_wise_integrity")
    test_dls_target_certainty_flagging()
    print("✓ test_dls_target_certainty_flagging")
    test_batting_order_raw_preserved()
    print("✓ test_batting_order_raw_preserved")
    print("\nAll match-state integrity tests passed successfully.")
