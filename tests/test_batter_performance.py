"""
Unit tests for batter performance engine and attribution mechanics.

Phase 2.3: Tests exact balls faced attribution (wides excluded, no-balls included),
non-striker dismissals, delta metric formulas, and zero-exposure edge cases.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from src.models.batter_performance import (
    prepare_batter_delivery_attributes,
    compute_player_dismissals,
    aggregate_batter_segment,
    build_batter_profile,
)


def test_batter_balls_faced_and_runs_attribution():
    """Verify that wides do not count as balls faced, while no-balls and byes do."""
    # Synthetic deliveries for a single batter
    records = [
        # Ball 1: Legal delivery, 1 run
        {"striker_id": 10, "striker_name": "Test Batter", "non_striker_id": 20, "runs": 1, "extras_type": None, "total_delivery_runs": 1, "is_wicket": 0, "dismissed_player_id": np.nan, "batter_pressure_tier": "HIGH"},
        # Ball 2: Wide delivery (extras1=1, runs=0). Must NOT count as ball faced.
        {"striker_id": 10, "striker_name": "Test Batter", "non_striker_id": 20, "runs": 0, "extras_type": "wide", "total_delivery_runs": 1, "is_wicket": 0, "dismissed_player_id": np.nan, "batter_pressure_tier": "HIGH"},
        # Ball 3: No-ball (Overstep) with 4 runs off bat. MUST count as ball faced.
        {"striker_id": 10, "striker_name": "Test Batter", "non_striker_id": 20, "runs": 4, "extras_type": "Overstep", "total_delivery_runs": 5, "is_wicket": 0, "dismissed_player_id": np.nan, "batter_pressure_tier": "HIGH"},
        # Ball 4: Legbye (extras1=1, runs=0). MUST count as ball faced (0 batter runs).
        {"striker_id": 10, "striker_name": "Test Batter", "non_striker_id": 20, "runs": 0, "extras_type": "legbyes", "total_delivery_runs": 1, "is_wicket": 0, "dismissed_player_id": np.nan, "batter_pressure_tier": "HIGH"},
        # Ball 5: Six off legal delivery
        {"striker_id": 10, "striker_name": "Test Batter", "non_striker_id": 20, "runs": 6, "extras_type": None, "total_delivery_runs": 6, "is_wicket": 0, "dismissed_player_id": np.nan, "batter_pressure_tier": "HIGH"},
    ]
    df = pd.DataFrame(records)
    df["match_id"] = 1
    df["comp_id"] = 100

    prep_df = prepare_batter_delivery_attributes(df)

    # Balls faced: 4 (Balls 1, 3, 4, 5). Wide (Ball 2) is excluded.
    assert prep_df["is_ball_faced"].sum() == 4
    # Batter runs: 1 + 0 + 4 + 0 + 6 = 11 runs. (Wide and legbye extras are excluded).
    assert prep_df["batter_runs"].sum() == 11
    # Boundaries: 2 (one 4, one 6)
    assert prep_df["is_boundary"].sum() == 2
    assert prep_df["boundary_runs"].sum() == 10

    # Test aggregation
    summary = aggregate_batter_segment(prep_df, prefix="pressure_")
    assert len(summary) == 1
    row = summary.iloc[0]
    assert row["pressure_balls_faced"] == 4
    assert row["pressure_runs"] == 11
    assert row["pressure_strike_rate"] == (11.0 / 4.0) * 100.0  # 275.0
    assert row["pressure_boundary_ball_pct"] == 50.0  # 2 boundaries out of 4 balls faced


def test_non_striker_dismissal_attribution():
    """Verify that run outs of the non-striker are attributed to the non-striker, not the striker."""
    # Striker = 10, Non-Striker = 20. Run out of non-striker (20).
    records = [
        {"striker_id": 10, "non_striker_id": 20, "is_wicket": 1, "dismissed_player_id": 20.0},
        # Striker = 10, Non-Striker = 30. Bowled dismissal of striker (10).
        {"striker_id": 10, "non_striker_id": 30, "is_wicket": 1, "dismissed_player_id": 10.0},
    ]
    df = pd.DataFrame(records)

    dismissals = compute_player_dismissals(df)
    assert dismissals[10] == 1  # Player 10 dismissed once
    assert dismissals[20] == 1  # Player 20 dismissed once as non-striker


def test_batter_delta_metrics_and_zero_pressure_exposure():
    """Verify delta metric calculation and clean handling of players with zero pressure exposure."""
    records = [
        # Player A: Has both normal and pressure deliveries
        {"striker_id": 1, "striker_name": "Player A", "non_striker_id": 2, "match_id": 1, "comp_id": 1, "runs": 10, "extras_type": None, "total_delivery_runs": 10, "is_wicket": 0, "dismissed_player_id": np.nan, "batter_pressure_tier": "LOW", "is_primary_pressure_cohort": True},
        {"striker_id": 1, "striker_name": "Player A", "non_striker_id": 2, "match_id": 1, "comp_id": 1, "runs": 20, "extras_type": None, "total_delivery_runs": 20, "is_wicket": 0, "dismissed_player_id": np.nan, "batter_pressure_tier": "HIGH", "is_primary_pressure_cohort": True},
        # Player B: Has ONLY normal deliveries (0 pressure deliveries)
        {"striker_id": 2, "striker_name": "Player B", "non_striker_id": 1, "match_id": 1, "comp_id": 1, "runs": 15, "extras_type": None, "total_delivery_runs": 15, "is_wicket": 0, "dismissed_player_id": np.nan, "batter_pressure_tier": "MODERATE", "is_primary_pressure_cohort": True},
    ]
    df = pd.DataFrame(records)

    profile = build_batter_profile(df, filter_primary_cohort=True)
    assert len(profile) == 2

    # Player B should have 0 pressure balls faced and NaN pressure strike rate without crashing
    player_b = profile[profile["striker_id"] == 2].iloc[0]
    assert player_b["pressure_balls_faced"] == 0
    assert player_b["pressure_runs"] == 0
    assert np.isnan(player_b["pressure_strike_rate"])
    assert np.isnan(player_b["delta_strike_rate"])

    # Player A should have valid pressure SR and delta SR
    player_a = profile[profile["striker_id"] == 1].iloc[0]
    assert player_a["pressure_balls_faced"] == 1
    assert player_a["normal_balls_faced"] == 1
    assert player_a["pressure_strike_rate"] == 2000.0
    assert player_a["normal_strike_rate"] == 1000.0
    assert player_a["delta_strike_rate"] == 1000.0

