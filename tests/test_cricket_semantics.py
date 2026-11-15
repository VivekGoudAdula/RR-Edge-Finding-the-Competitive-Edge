"""
Unit tests for cricket semantics, rules verification, and attribution logic.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from src.cricket.semantics import (
    classify_competition,
    is_senior_ipl_or_t20i,
    is_legal_delivery,
    is_wide,
    is_no_ball,
    get_scheduled_balls,
    get_match_phase,
    determine_chase_target,
    is_bowler_wicket,
    is_batter_dismissal,
    get_dismissed_player_id,
)


def test_competition_classification():
    """Verify competitions are categorized correctly."""
    assert classify_competition("IPL 2024", "T20") == "IPL"
    assert classify_competition("IPL 2022", "T20") == "IPL"
    assert classify_competition("India in England T20I Series 2022", "T20I") == "T20I_SENIOR"
    assert classify_competition("Mens T20 Emerging Teams Asia Cup 2024", "T20") == "EMERGING_A_TEAMS"
    assert classify_competition("Asia Cup Rising Stars 2025", "T20") == "EMERGING_A_TEAMS"

    # Primary analysis filter check
    assert is_senior_ipl_or_t20i("IPL 2024", "T20") is True
    assert is_senior_ipl_or_t20i("India in England T20I Series 2022", "T20I") is True
    assert is_senior_ipl_or_t20i("Mens T20 Emerging Teams Asia Cup 2024", "T20") is False
    assert is_senior_ipl_or_t20i("Asia Cup Rising Stars 2025", "T20") is False


def test_extras_and_legal_deliveries():
    """Verify extras classification and legal ball determination."""
    # Legal deliveries
    assert is_legal_delivery(np.nan) is True
    assert is_legal_delivery(None) is True
    assert is_legal_delivery("byes") is True
    assert is_legal_delivery("legbyes") is True
    assert is_legal_delivery("Penalty") is True

    # Illegal deliveries
    assert is_legal_delivery("wide") is False
    assert is_legal_delivery("Overstep") is False
    assert is_legal_delivery("other") is False

    # Specific predicates
    assert is_wide("wide") is True
    assert is_wide("Overstep") is False
    assert is_no_ball("Overstep") is True
    assert is_no_ball("other") is True
    assert is_no_ball("wide") is False
    assert is_no_ball(np.nan) is False


def test_scheduled_balls_and_overs():
    """Verify scheduled legal balls calculations."""
    # Standard 20-over match
    assert get_scheduled_balls(1) == 120
    assert get_scheduled_balls(2) == 120

    # Shortened/DLS matches (where values in CSV are legal balls)
    assert get_scheduled_balls(2, second_inn_revised_overs=90.0) == 90
    assert get_scheduled_balls(2, second_inn_revised_overs=48.0) == 48
    assert get_scheduled_balls(1, first_inn_revised_overs=60.0) == 60

    # Super overs
    assert get_scheduled_balls(3) == 6
    assert get_scheduled_balls(4) == 6


def test_match_phase():
    """Verify phase classification from 1-indexed overid."""
    assert get_match_phase(1) == "Powerplay"
    assert get_match_phase(6) == "Powerplay"
    assert get_match_phase(7) == "Middle"
    assert get_match_phase(15) == "Middle"
    assert get_match_phase(16) == "Death"
    assert get_match_phase(20) == "Death"


def test_chase_target_hierarchy():
    """Verify target calculation hierarchy and absence of target leakage."""
    # Innings 1 and 3 setting target -> None
    assert determine_chase_target(innings=1, first_innings_total_runs=180) is None
    assert determine_chase_target(innings=3, first_innings_total_runs=None) is None

    # Standard chase (innings 2, uninterrupted)
    assert determine_chase_target(innings=2, first_innings_total_runs=165) == 166

    # DLS chase (revised_target takes priority)
    assert determine_chase_target(
        innings=2,
        first_innings_total_runs=200,
        revised_target=145.0,
    ) == 145

    # Super over chase (innings 4)
    assert determine_chase_target(innings=4, first_innings_total_runs=None, super_over_inn3_total=14) == 15


def test_dismissal_attribution():
    """Verify bowler-credited wickets vs non-bowler wickets."""
    # Bowler credited wickets
    assert is_bowler_wicket(True, "Bowled") is True
    assert is_bowler_wicket(True, "Caught") is True
    assert is_bowler_wicket(True, "LBW") is True
    assert is_bowler_wicket(True, "Stump") is True
    assert is_bowler_wicket(True, "Hit Wicket") is True

    # Non-bowler credited wickets
    assert is_bowler_wicket(True, "RunOut") is False
    assert is_bowler_wicket(True, "Retire Out") is False
    assert is_bowler_wicket(True, "Obstructing the field") is False
    assert is_bowler_wicket(True, "Obstracting the field") is False

    # No wicket
    assert is_bowler_wicket(False, np.nan) is False

    # Batter dismissals (all wickets end a batter's innings)
    assert is_batter_dismissal(True, "Caught") is True
    assert is_batter_dismissal(True, "RunOut") is True
    assert is_batter_dismissal(True, "Retire Out") is True
    assert is_batter_dismissal(False, np.nan) is False

    # Dismissed player identification
    assert get_dismissed_player_id(True, 1001.0, 1001, 1002, "Caught") == 1001
    assert get_dismissed_player_id(True, 1002.0, 1001, 1002, "RunOut") == 1002
    assert get_dismissed_player_id(False, np.nan, 1001, 1002, np.nan) is None


if __name__ == "__main__":
    test_competition_classification()
    print("✓ test_competition_classification")
    test_extras_and_legal_deliveries()
    print("✓ test_extras_and_legal_deliveries")
    test_scheduled_balls_and_overs()
    print("✓ test_scheduled_balls_and_overs")
    test_match_phase()
    print("✓ test_match_phase")
    test_chase_target_hierarchy()
    print("✓ test_chase_target_hierarchy")
    test_dismissal_attribution()
    print("✓ test_dismissal_attribution")
    print("\nAll cricket semantics tests passed.")

