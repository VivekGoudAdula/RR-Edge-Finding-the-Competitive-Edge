"""
Unit tests for pressure research module, rolling momentum, resource modeling,
asymmetric pressure classification, and Empirical Bayes shrinkage.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from src.cricket.pressure_research import (
    compute_previous_legal_runs,
    compute_advanced_momentum,
    FirstInningsResourceModel,
    classify_batter_pressure_multidimensional,
    classify_bowler_pressure_multidimensional,
    classify_delivery_pressure_multidimensional,
    empirical_bayes_shrinkage,
    evaluate_sample_size_confidence,
)


def test_compute_previous_legal_runs():
    """Verify rolling previous legal runs aggregates only legal deliveries and resets across groups."""
    df = pd.DataFrame([
        # Innings 1: 4 legal balls, 1 wide
        {"match_id": 1, "innings": 1, "is_legal_ball": True, "total_delivery_runs": 1},
        {"match_id": 1, "innings": 1, "is_legal_ball": True, "total_delivery_runs": 4},
        {"match_id": 1, "innings": 1, "is_legal_ball": False, "total_delivery_runs": 1},  # wide
        {"match_id": 1, "innings": 1, "is_legal_ball": True, "total_delivery_runs": 0},
        {"match_id": 1, "innings": 1, "is_legal_ball": True, "total_delivery_runs": 6},
        # Innings 2: must reset
        {"match_id": 1, "innings": 2, "is_legal_ball": True, "total_delivery_runs": 2},
    ])

    prev_runs = compute_previous_legal_runs(df, window=6)

    # Ball 1 of Innings 1: NaN (no prior balls)
    assert np.isnan(prev_runs[0])

    # Ball 2: 1 prior legal ball (1 run) normalized to 6 balls = 6.0
    assert prev_runs[1] == 6.0

    # Ball 3 (wide): 2 prior legal balls (1 + 4 = 5 runs) -> 5 * (6/2) = 15.0
    assert prev_runs[2] == 15.0

    # Ball 4: wide does not add to legal history, so prior legal balls still [1, 4] -> 15.0
    assert prev_runs[3] == 15.0

    # Ball 1 of Innings 2: must reset to NaN
    assert np.isnan(prev_runs[5])


def test_compute_advanced_momentum():
    """Verify 4 rolling momentum features: pre-delivery, inside-group, no boundary leaks."""
    # Construct 1 innings with 7 legal balls and 1 wide
    rows = []
    # Ball 0..5 (Over 0: 6 legal balls: 0, 1, 0, 4, 0, 6 = 11 runs, 3 dots, 0 wkts)
    runs_seq = [0, 1, 0, 4, 0, 6]
    for b in range(6):
        rows.append({
            "match_id": 10,
            "innings": 1,
            "is_legal_ball": True,
            "total_delivery_runs": runs_seq[b],
            "is_wicket": False,
        })
    # Ball 6: Over 1, ball 0 (legal ball 6, 1 wkt)
    rows.append({
        "match_id": 10,
        "innings": 1,
        "is_legal_ball": True,
        "total_delivery_runs": 0,
        "is_wicket": True,
    })
    # Innings 2 delivery (must reset completely)
    rows.append({
        "match_id": 10,
        "innings": 2,
        "is_legal_ball": True,
        "total_delivery_runs": 4,
        "is_wicket": False,
    })

    df = pd.DataFrame(rows)
    mom = compute_advanced_momentum(df, window=6)

    # Ball 0: all NaN
    assert np.isnan(mom.loc[0, "prev_6_runs"])
    assert np.isnan(mom.loc[0, "prev_6_dots"])
    assert np.isnan(mom.loc[0, "prev_6_wkts"])
    assert np.isnan(mom.loc[0, "prev_over_runs"])

    # Ball 6 (first ball of Over 1):
    # Exactly 6 prior legal balls: runs = 11, dots = 3 (balls 0, 2, 4), wkts = 0
    assert mom.loc[6, "prev_6_runs"] == 11.0
    assert mom.loc[6, "prev_6_dots"] == 3.0
    assert mom.loc[6, "prev_6_wkts"] == 0.0
    # Over 0 is completed, so prev_over_runs == 11.0
    assert mom.loc[6, "prev_over_runs"] == 11.0

    # Innings 2 Ball 0: all NaN (reset isolation)
    assert np.isnan(mom.loc[7, "prev_6_runs"])
    assert np.isnan(mom.loc[7, "prev_over_runs"])


def test_first_innings_resource_model_competition_support():
    """Verify first-innings resource model with competition benchmarks and par deficit."""
    train_data = []
    for mid in range(1, 11):
        c_type = "IPL" if mid <= 5 else "T20I"
        base_rate = 1.6 if c_type == "IPL" else 1.3
        for b in range(120):
            w = min(9, b // 20)
            train_data.append({
                "match_id": mid,
                "innings": 1,
                "competition_type": c_type,
                "legal_balls_bowled_before": b,
                "wickets_lost_before": w,
                "current_score_before": b * base_rate,
                "total_delivery_runs": base_rate,
            })
    train_df = pd.DataFrame(train_data)

    model = FirstInningsResourceModel(by_competition=True)
    model.fit(train_df)

    # IPL remaining should be higher than T20I given higher scoring
    rem_ipl = model.predict_remaining_runs(0, 0, competition_type="IPL")
    rem_t20i = model.predict_remaining_runs(0, 0, competition_type="T20I")
    assert rem_ipl > rem_t20i

    # Par deficit calculation
    # Team at over 10 (60 balls), 2 wickets down, score 60 (tracking slow for IPL)
    deficit = model.predict_par_deficit(
        current_score_before=60,
        legal_balls_bowled=60,
        wickets_lost=2,
        competition_type="IPL",
    )
    # Deficit must be positive (underperforming benchmark)
    assert deficit > 0.0


def test_asymmetric_pressure_classifiers():
    """Verify separate batter vs bowler pressure logic and asymmetry."""
    # Situation: RRR = 16.5, chasing team is 8 wickets down (wickets_remaining = 2)
    # Batter is under EXTREME pressure
    batter_res = classify_batter_pressure_multidimensional(
        innings=2,
        balls_remaining=18,
        wickets_remaining=2,
        rrr=16.5,
    )
    assert batter_res["composite_tier"] == "HIGH"
    assert batter_res["rate_tier"] == "EXTREME_RATE"

    # Bowler is CLOSING OUT TAIL -> Low/Medium bowler pressure (bowler in control)
    bowler_res = classify_bowler_pressure_multidimensional(
        innings=2,
        balls_remaining=18,
        wickets_remaining=2,
        rrr=16.5,
        runs_required=50,
    )
    assert bowler_res["bowler_context_tier"] == "CLOSING_OUT_TAIL"
    assert bowler_res["is_high_pressure"] is False

    # Situation: Acute margin pressure (bowler defending 12 runs off last over, 6 balls remaining)
    bowler_margin = classify_bowler_pressure_multidimensional(
        innings=2,
        balls_remaining=6,
        wickets_remaining=6,
        rrr=12.0,
        runs_required=12,
    )
    assert bowler_margin["is_margin_critical"] is True
    assert bowler_margin["is_high_pressure"] is True


def test_empirical_bayes_shrinkage():
    """Verify Empirical Bayes shrinkage math and sample-size confidence tiers."""
    # A batter with 10 balls and 200 strike rate regresses toward prior mean (130)
    shrunk_small = empirical_bayes_shrinkage(
        observed_metric=200.0,
        sample_size=10,
        prior_mean=130.0,
        prior_weight=30.0,
    )
    # 10 / (10 + 30) * 200 + 30 / 40 * 130 = 0.25 * 200 + 0.75 * 130 = 50 + 97.5 = 147.5
    assert round(shrunk_small, 1) == 147.5

    # A batter with 120 balls retains mostly their observed strike rate
    shrunk_large = empirical_bayes_shrinkage(
        observed_metric=200.0,
        sample_size=120,
        prior_mean=130.0,
        prior_weight=30.0,
    )
    # 120 / 150 * 200 + 30 / 150 * 130 = 0.8 * 200 + 0.2 * 130 = 160 + 26 = 186.0
    assert round(shrunk_large, 1) == 186.0

    # Confidence tiers
    conf_small = evaluate_sample_size_confidence(15)
    assert conf_small["status"] == "INSUFFICIENT"
    assert not conf_small["is_qualified"]

    conf_prov = evaluate_sample_size_confidence(35)
    assert conf_prov["status"] == "PROVISIONAL"
    assert conf_prov["is_qualified"]

    conf_conf = evaluate_sample_size_confidence(85)
    assert conf_conf["status"] == "CONFIDENT"
    assert conf_conf["is_qualified"]


if __name__ == "__main__":
    test_compute_previous_legal_runs()
    test_compute_advanced_momentum()
    test_first_innings_resource_model_competition_support()
    test_asymmetric_pressure_classifiers()
    test_empirical_bayes_shrinkage()
    print("All Phase 2.1.1 unit tests passed successfully!")
