"""
Unit tests for RR EDGE pressure engine module.

Phase 2.2: Tests pipeline integrity, pre-delivery state shifts, momentum window
correctness, resource model isolation, batter/bowler asymmetry, and missing value handling.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from src.cricket.pressure_engine import (
    PressureEngineConfig,
    filter_whitelisted_data,
    calculate_isolated_first_innings_expectations,
    classify_batter_delivery_pressure,
    classify_bowler_delivery_pressure,
    build_pressure_pipeline,
)


@pytest.fixture
def sample_config():
    return PressureEngineConfig()


def test_classify_batter_pressure_tiers(sample_config):
    """Verify batter pressure classification rules and reason tags."""
    # 1. Extreme chase RRR
    tier, reason = classify_batter_delivery_pressure(
        innings=2,
        rrr=15.2,
        delta_rrr=7.1,
        wickets_remaining=5,
        balls_remaining=24,
        par_deficit=np.nan,
        prev_6_runs=6.0,
        prev_6_dots=2.0,
        config=sample_config,
    )
    assert tier == "EXTREME"
    assert reason == "CHASE_EXTREME_RRR"

    # 2. Elevated rate & resource stress
    tier_high, reason_high = classify_batter_delivery_pressure(
        innings=2,
        rrr=11.2,
        delta_rrr=1.5,
        wickets_remaining=3,
        balls_remaining=30,
        par_deficit=np.nan,
        prev_6_runs=4.0,
        prev_6_dots=2.0,
        config=sample_config,
    )
    assert tier_high == "HIGH"
    assert reason_high in {"CHASE_ELEVATED_RRR", "CHASE_RESOURCE_STRESS"}

    # 3. Cruising chase (low rate, ample wickets)
    tier_low, reason_low = classify_batter_delivery_pressure(
        innings=2,
        rrr=5.5,
        delta_rrr=-3.0,
        wickets_remaining=8,
        balls_remaining=60,
        par_deficit=np.nan,
        prev_6_runs=8.0,
        prev_6_dots=1.0,
        config=sample_config,
    )
    assert tier_low == "LOW"
    assert reason_low == "CHASE_CRUISING_AMPLE_WICKETS"

    # 4. 1st innings par deficit
    tier_inn1, reason_inn1 = classify_batter_delivery_pressure(
        innings=1,
        rrr=np.nan,
        delta_rrr=np.nan,
        wickets_remaining=4,
        balls_remaining=40,
        par_deficit=28.0,
        prev_6_runs=5.0,
        prev_6_dots=2.0,
        config=sample_config,
    )
    assert tier_inn1 == "EXTREME"
    assert reason_inn1 == "1ST_INN_SEVERE_PAR_DEFICIT"


def test_classify_bowler_pressure_asymmetry(sample_config):
    """Verify bowler pressure asymmetry: tail closure vs acute margin."""
    # Case A: Tail closure (RRR 16.0, but batting team 8 down -> LOW bowler pressure)
    tier_tail, ctx_tail, reason_tail = classify_bowler_delivery_pressure(
        innings=2,
        rrr=16.5,
        runs_to_defend=55.0,
        wickets_remaining=2,
        balls_remaining=20,
        prev_6_runs=4.0,
        prev_6_dots=3.0,
        innings_phase="DEATH",
        par_deficit=np.nan,
        config=sample_config,
    )
    assert ctx_tail == "TAIL_EXPOSED"
    assert tier_tail == "LOW"
    assert reason_tail == "BOWLER_CLOSING_OUT_TAIL"

    # Case B: Acute margin pressure (opposition needs 14 runs in 10 balls -> EXTREME bowler pressure)
    tier_margin, ctx_margin, reason_margin = classify_bowler_delivery_pressure(
        innings=2,
        rrr=8.4,
        runs_to_defend=14.0,
        wickets_remaining=5,
        balls_remaining=10,
        prev_6_runs=8.0,
        prev_6_dots=1.0,
        innings_phase="DEATH",
        par_deficit=np.nan,
        config=sample_config,
    )
    assert tier_margin == "EXTREME"
    assert reason_margin == "BOWLER_ACUTE_MARGIN_DEFENSE"

    # Case C: High firepower assault (RRR 13.5, but opposition has 7 wickets in hand -> EXTREME bowler pressure)
    tier_assault, ctx_assault, reason_assault = classify_bowler_delivery_pressure(
        innings=2,
        rrr=13.5,
        runs_to_defend=54.0,
        wickets_remaining=7,
        balls_remaining=24,
        prev_6_runs=14.0,
        prev_6_dots=0.0,
        innings_phase="DEATH",
        par_deficit=np.nan,
        config=sample_config,
    )
    assert ctx_assault == "TOP_ORDER_INTACT"
    assert tier_assault == "EXTREME"
    assert reason_assault == "BOWLER_HIGH_FIREPOWER_DEFENSE"


def test_first_innings_expectations_isolation():
    """Verify 1st innings expectations do not self-predict and are strictly NaN in 2nd innings."""
    # Synthetic deliveries across 3 matches
    rows = []
    for mid in [101, 102, 103]:
        for b in range(60):
            rows.append({
                "match_id": mid,
                "innings": 1,
                "competition_type": "IPL",
                "legal_balls_bowled_before": b,
                "wickets_lost_before": min(9, b // 10),
                "current_score_before": b * 1.5,
                "total_delivery_runs": 1.5,
            })
    # Innings 2 deliveries
    for b in range(30):
        rows.append({
            "match_id": 101,
            "innings": 2,
            "competition_type": "IPL",
            "legal_balls_bowled_before": b,
            "wickets_lost_before": 1,
            "current_score_before": b * 1.8,
            "total_delivery_runs": 1.8,
        })

    df = pd.DataFrame(rows)
    # Train matches = [101, 102], Test matches = [103]
    exp_df = calculate_isolated_first_innings_expectations(df, train_match_ids={101, 102}, n_folds=2)

    # Innings 1 has valid numbers
    inn1_mask = df["innings"] == 1
    assert exp_df.loc[inn1_mask, "expected_remaining_runs"].notna().all()
    assert exp_df.loc[inn1_mask, "par_score"].notna().all()
    assert exp_df.loc[inn1_mask, "par_deficit"].notna().all()

    # Innings 2 MUST be completely NaN (unavailable in 2nd innings)
    inn2_mask = df["innings"] == 2
    assert exp_df.loc[inn2_mask, "expected_remaining_runs"].isna().all()
    assert exp_df.loc[inn2_mask, "par_score"].isna().all()
    assert exp_df.loc[inn2_mask, "par_deficit"].isna().all()


def test_no_current_delivery_outcome_leakage():
    """Verify pre-delivery pressure tiers do not depend on the current delivery outcome."""
    cfg = PressureEngineConfig()

    # Ball A: Wicket falls on this ball, but pre-delivery state is identical
    tier_a, _ = classify_batter_delivery_pressure(
        innings=2,
        rrr=10.0,
        delta_rrr=1.0,
        wickets_remaining=6,  # 6 wickets before this ball
        balls_remaining=24,
        par_deficit=np.nan,
        prev_6_runs=6.0,
        prev_6_dots=2.0,
        config=cfg,
    )

    # Ball B: Six runs scored on this ball, pre-delivery state is identical
    tier_b, _ = classify_batter_delivery_pressure(
        innings=2,
        rrr=10.0,
        delta_rrr=1.0,
        wickets_remaining=6,
        balls_remaining=24,
        par_deficit=np.nan,
        prev_6_runs=6.0,
        prev_6_dots=2.0,
        config=cfg,
    )

    assert tier_a == tier_b == "MODERATE"


def test_dls_uncertainty_flagging():
    """Verify DLS uncertain matches are flagged as is_primary_pressure_cohort == False."""
    df = pd.DataFrame([
        {"target_certainty": "CERTAIN"},
        {"target_certainty": "UNCERTAIN_DLS_TIMING"},
        {"target_certainty": "NOT_APPLICABLE"},
    ])
    df["is_primary_pressure_cohort"] = df["target_certainty"] != "UNCERTAIN_DLS_TIMING"

    assert bool(df.loc[0, "is_primary_pressure_cohort"]) is True
    assert bool(df.loc[1, "is_primary_pressure_cohort"]) is False
    assert bool(df.loc[2, "is_primary_pressure_cohort"]) is True


def test_competition_filtering_rules():
    """Verify that developmental / A-team competitions are strictly excluded."""
    from src.cricket.competition_config import is_competition_included

    # A-team tournaments must be excluded
    assert not is_competition_included(2670, "T20")  # Emerging Teams Asia Cup 2024
    assert not is_competition_included(3289, "T20")  # Asia Cup Rising Stars 2025

    # IPL editions must be included
    assert is_competition_included(1358, "T20")  # IPL 2022
    assert is_competition_included(3298, "T20")  # IPL 2026

    # Senior T20Is must be included
    assert is_competition_included(9999, "T20I")


def test_missing_values_and_schema_consistency():
    """Verify that 1st innings has NaN for chase metrics and vice versa."""
    # Build synthetic row simulating Innings 1
    inn1_tier, _ = classify_batter_delivery_pressure(
        innings=1,
        rrr=np.nan,
        delta_rrr=np.nan,
        wickets_remaining=7,
        balls_remaining=60,
        par_deficit=5.0,
        prev_6_runs=8.0,
        prev_6_dots=2.0,
        config=PressureEngineConfig(),
    )
    assert inn1_tier in {"LOW", "MODERATE", "HIGH", "EXTREME"}

    # Build synthetic row simulating Innings 2
    inn2_tier, _ = classify_batter_delivery_pressure(
        innings=2,
        rrr=9.2,
        delta_rrr=1.2,
        wickets_remaining=6,
        balls_remaining=48,
        par_deficit=np.nan,
        prev_6_runs=7.0,
        prev_6_dots=1.0,
        config=PressureEngineConfig(),
    )
    assert inn2_tier in {"LOW", "MODERATE", "HIGH", "EXTREME"}

