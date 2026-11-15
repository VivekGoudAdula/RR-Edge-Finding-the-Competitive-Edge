"""
Unit tests for bowler performance engine and attribution mechanics.

Phase 2.3: Tests exact bowler runs conceded (byes/legbyes excluded, wides/no-balls included),
bowler-credited wicket attribution, delta economy formulas, and zero-exposure edge cases.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from src.models.bowler_performance import (
    prepare_bowler_delivery_attributes,
    aggregate_bowler_segment,
    build_bowler_profile,
)


def test_bowler_runs_conceded_and_extras_rules():
    """Verify that byes and legbyes are not conceded by bowler, while wides and no-balls are."""
    records = [
        # Ball 1: Legal delivery, 1 run off bat -> Bowler concedes 1
        {"bowler_id": 50, "bowler_name": "Test Bowler", "runs": 1, "total_delivery_runs": 1, "extras_type": None, "is_legal_ball": True, "is_bowler_wkt": False, "bowler_pressure_tier": "HIGH"},
        # Ball 2: Wide delivery (1 wide run). Bowler concedes 1, 0 legal balls.
        {"bowler_id": 50, "bowler_name": "Test Bowler", "runs": 0, "total_delivery_runs": 1, "extras_type": "wide", "is_legal_ball": False, "is_bowler_wkt": False, "bowler_pressure_tier": "HIGH"},
        # Ball 3: Byes (4 bye runs, 0 off bat). Bowler concedes 0!
        {"bowler_id": 50, "bowler_name": "Test Bowler", "runs": 0, "total_delivery_runs": 4, "extras_type": "byes", "is_legal_ball": True, "is_bowler_wkt": False, "bowler_pressure_tier": "HIGH"},
        # Ball 4: Legbyes (2 legbye runs, 0 off bat). Bowler concedes 0!
        {"bowler_id": 50, "bowler_name": "Test Bowler", "runs": 0, "total_delivery_runs": 2, "extras_type": "legbyes", "is_legal_ball": True, "is_bowler_wkt": False, "bowler_pressure_tier": "HIGH"},
        # Ball 5: Overstep no-ball (1 penalty + 2 bat runs = 3 runs). Bowler concedes 3, 0 legal balls.
        {"bowler_id": 50, "bowler_name": "Test Bowler", "runs": 2, "total_delivery_runs": 3, "extras_type": "Overstep", "is_legal_ball": False, "is_bowler_wkt": False, "bowler_pressure_tier": "HIGH"},
        # Ball 6: Penalty award (5 penalty runs). Bowler concedes 0!
        {"bowler_id": 50, "bowler_name": "Test Bowler", "runs": 0, "total_delivery_runs": 5, "extras_type": "Penalty", "is_legal_ball": True, "is_bowler_wkt": False, "bowler_pressure_tier": "HIGH"},
        # Ball 7: Dot ball (legal ball, 0 runs) -> Bowler dot ball!
        {"bowler_id": 50, "bowler_name": "Test Bowler", "runs": 0, "total_delivery_runs": 0, "extras_type": None, "is_legal_ball": True, "is_bowler_wkt": False, "bowler_pressure_tier": "HIGH"},
    ]
    df = pd.DataFrame(records)
    df["match_id"] = 1
    df["comp_id"] = 100

    prep_df = prepare_bowler_delivery_attributes(df)

    # Bowler runs conceded:
    # Ball 1: 1
    # Ball 2 (wide): 1
    # Ball 3 (byes): 0
    # Ball 4 (legbyes): 0
    # Ball 5 (Overstep): 3
    # Ball 6 (Penalty): 0
    # Ball 7 (dot): 0
    # Total conceded: 1 + 1 + 0 + 0 + 3 + 0 + 0 = 5 runs!
    assert prep_df["bowler_runs_conceded"].sum() == 5

    # Legal balls: 5 (Balls 1, 3, 4, 6, 7). Balls 2 & 5 are illegal.
    assert prep_df["is_legal_bowler_ball"].sum() == 5

    # Dot balls: Ball 7 is a legal ball with 0 runs conceded. Balls 3, 4, 6 had byes/legbyes/penalties so 0 bowler runs, but Ball 7 is a true dot.
    assert bool(prep_df.loc[6, "is_bowler_dot"]) is True


def test_bowler_wicket_credit_attribution():
    """Verify that bowler wickets only include bowler-credited dismissals, excluding run outs."""
    records = [
        # Dismissal 1: Caught -> Bowler wicket
        {"bowler_id": 1, "bowler_name": "Bowler A", "runs": 0, "total_delivery_runs": 0, "extras_type": None, "is_legal_ball": True, "is_bowler_wkt": True, "bowler_pressure_tier": "HIGH"},
        # Dismissal 2: Bowled -> Bowler wicket
        {"bowler_id": 1, "bowler_name": "Bowler A", "runs": 0, "total_delivery_runs": 0, "extras_type": None, "is_legal_ball": True, "is_bowler_wkt": True, "bowler_pressure_tier": "HIGH"},
        # Dismissal 3: Run out -> NOT a bowler wicket!
        {"bowler_id": 1, "bowler_name": "Bowler A", "runs": 1, "total_delivery_runs": 1, "extras_type": None, "is_legal_ball": True, "is_bowler_wkt": False, "bowler_pressure_tier": "HIGH"},
    ]
    df = pd.DataFrame(records)
    df["match_id"] = 1
    df["comp_id"] = 100

    prep_df = prepare_bowler_delivery_attributes(df)
    summary = aggregate_bowler_segment(prep_df, prefix="pressure_")

    assert summary.loc[0, "pressure_wickets"] == 2  # Only the caught & bowled dismissals


def test_bowler_delta_metrics_and_zero_exposure():
    """Verify delta economy rate calculation and zero exposure handling."""
    records = [
        # Bowler A: Concedes 6 runs in 6 normal balls (Econ 6.0), 12 runs in 6 pressure balls (Econ 12.0)
        {"bowler_id": 10, "bowler_name": "Bowler A", "match_id": 1, "comp_id": 1, "runs": 1, "total_delivery_runs": 1, "extras_type": None, "is_legal_ball": True, "is_bowler_wkt": False, "bowler_pressure_tier": "LOW", "is_primary_pressure_cohort": True},
        {"bowler_id": 10, "bowler_name": "Bowler A", "match_id": 1, "comp_id": 1, "runs": 2, "total_delivery_runs": 2, "extras_type": None, "is_legal_ball": True, "is_bowler_wkt": False, "bowler_pressure_tier": "HIGH", "is_primary_pressure_cohort": True},
        # Bowler B: Concedes 0 pressure balls (only normal)
        {"bowler_id": 20, "bowler_name": "Bowler B", "match_id": 1, "comp_id": 1, "runs": 1, "total_delivery_runs": 1, "extras_type": None, "is_legal_ball": True, "is_bowler_wkt": False, "bowler_pressure_tier": "MODERATE", "is_primary_pressure_cohort": True},
    ]
    df = pd.DataFrame(records)

    profile = build_bowler_profile(df, filter_primary_cohort=True)
    assert len(profile) == 2

    # Bowler B has 0 pressure balls without crashing
    bowler_b = profile[profile["bowler_id"] == 20].iloc[0]
    assert bowler_b["pressure_legal_balls"] == 0
    assert np.isnan(bowler_b["pressure_economy_rate"])
    assert np.isnan(bowler_b["delta_economy"])

    # Bowler A delta economy
    bowler_a = profile[profile["bowler_id"] == 10].iloc[0]
    assert bowler_a["pressure_legal_balls"] == 1
    assert bowler_a["normal_legal_balls"] == 1
    assert bowler_a["delta_economy"] == bowler_a["pressure_economy_rate"] - bowler_a["normal_economy_rate"]

