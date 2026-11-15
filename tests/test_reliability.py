"""
Unit tests for reliability, match consistency, Empirical Bayes shrinkage, and Bayesian credible intervals.

Phase 2.3: Tests match-level consistency aggregation, Bayesian posterior credible intervals,
shrinkage sensitivity across candidate M values, and evidence strength tier classification.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from src.models.reliability import (
    compute_batter_match_consistency,
    compute_bowler_match_consistency,
    empirical_bayes_shrink,
    compute_beta_binomial_credible_interval,
    compute_rate_uncertainty_interval,
    classify_evidence_tier,
    evaluate_shrinkage_sensitivity,
)


def test_match_level_aggregation_before_consistency():
    """Verify that match-level consistency groups by match before computing standard deviation."""
    # Batter facing balls across 3 matches:
    # Match 1: 10 balls, 20 runs (SR = 200.0)
    # Match 2: 10 balls, 15 runs (SR = 150.0)
    # Match 3: 10 balls, 10 runs (SR = 100.0)
    # Match SRs: [200, 150, 100] -> Sample std dev = 50.0, Median = 150.0
    rows = []
    runs_by_match = {1: [2] * 10, 2: [1, 2] * 5, 3: [1] * 10}
    for m_id, runs_list in runs_by_match.items():
        for r in runs_list:
            rows.append({
                "striker_id": 99,
                "striker_name": "Consistent Batter",
                "match_id": m_id,
                "is_ball_faced": True,
                "batter_runs": r,
            })
    df = pd.DataFrame(rows)

    consistency = compute_batter_match_consistency(df, min_balls_per_match=3)
    assert len(consistency) == 1
    row = consistency.iloc[0]
    assert row["pressure_matches_count"] == 3
    assert row["pressure_matches_evaluated"] == 3
    assert round(row["pressure_match_sr_std"], 1) == 50.0
    assert row["pressure_match_sr_median"] == 150.0
    # Match 1 (200.0) passes (>= 130), Match 2 (150.0) passes, Match 3 (100.0) fails -> Pass rate = 66.67%
    assert round(row["pressure_match_pass_rate"], 2) == 66.67


def test_bowler_match_consistency_aggregation():
    """Verify bowler match economy aggregation and benchmark pass rate."""
    # Bowler in 2 matches:
    # Match 1: 6 legal balls, 6 runs conceded (Econ = 6.0) -> Pass (<= 9.0)
    # Match 2: 6 legal balls, 12 runs conceded (Econ = 12.0) -> Fail
    rows = []
    for _ in range(6):
        rows.append({"bowler_id": 88, "bowler_name": "Bowler X", "match_id": 1, "is_legal_bowler_ball": True, "bowler_runs_conceded": 1, "bowler_wicket_credit": 0})
    for _ in range(6):
        rows.append({"bowler_id": 88, "bowler_name": "Bowler X", "match_id": 2, "is_legal_bowler_ball": True, "bowler_runs_conceded": 2, "bowler_wicket_credit": 0})
    df = pd.DataFrame(rows)

    consistency = compute_bowler_match_consistency(df, min_balls_per_match=3)
    assert len(consistency) == 1
    row = consistency.iloc[0]
    assert row["pressure_matches_count"] == 2
    assert row["pressure_match_pass_rate"] == 50.0
    assert row["pressure_match_econ_median"] == 9.0


def test_empirical_bayes_shrink_properties():
    """Verify mathematical properties of Empirical Bayes shrinkage estimator."""
    prior_sr = 130.0

    # Case 1: n = 0 -> returns prior
    assert empirical_bayes_shrink(200.0, 0, prior_sr, prior_weight=30.0) == 130.0

    # Case 2: small sample (n=10, obs=200) -> heavy regression toward 130
    # (10/40)*200 + (30/40)*130 = 50 + 97.5 = 147.5
    assert empirical_bayes_shrink(200.0, 10, prior_sr, prior_weight=30.0) == 147.5

    # Case 3: large sample (n=120, obs=200) -> observed dominates
    # (120/150)*200 + (30/150)*130 = 160 + 26 = 186.0
    assert empirical_bayes_shrink(200.0, 120, prior_sr, prior_weight=30.0) == 186.0

    # Case 4: M=60 shrinks more aggressively than M=15
    shrunk_m15 = empirical_bayes_shrink(200.0, 30, prior_sr, prior_weight=15.0)
    shrunk_m60 = empirical_bayes_shrink(200.0, 30, prior_sr, prior_weight=60.0)
    assert abs(shrunk_m15 - 200.0) < abs(shrunk_m60 - 200.0)


def test_beta_binomial_credible_interval():
    """Verify statistical properties of Beta-Binomial posterior credible interval."""
    # 20 dots out of 50 balls faced (40% observed)
    mean_pct, lower, upper = compute_beta_binomial_credible_interval(
        successes=20, trials=50, prior_alpha=3.8, prior_beta=6.2, confidence_level=0.95
    )
    # Validity bounds
    assert 0.0 < lower < mean_pct < upper < 100.0
    # Interval width must be strictly positive and sensible (< 30% width for n=50)
    width = upper - lower
    assert 10.0 < width < 30.0


def test_evidence_tier_classification():
    """Verify multidimensional evidence tier classification."""
    # Confident: 70 balls, 10 matches, 3 tournaments
    c_tier = classify_evidence_tier(sample_size=70, distinct_matches=10, distinct_competitions=3)
    assert c_tier["evidence_tier"] == "CONFIDENT_EVIDENCE"
    assert c_tier["is_reliable"] is True
    assert c_tier["recommended_m"] == 15.0

    # Moderate: 35 balls, 5 matches, 1 tournament
    m_tier = classify_evidence_tier(sample_size=35, distinct_matches=5, distinct_competitions=1)
    assert m_tier["evidence_tier"] == "MODERATE_EVIDENCE"
    assert m_tier["is_reliable"] is True
    assert m_tier["recommended_m"] == 30.0

    # Provisional: 15 balls, 2 matches
    p_tier = classify_evidence_tier(sample_size=15, distinct_matches=2, distinct_competitions=1)
    assert p_tier["evidence_tier"] == "PROVISIONAL_EVIDENCE"
    assert p_tier["is_reliable"] is False

    # Insufficient: 8 balls
    i_tier = classify_evidence_tier(sample_size=8, distinct_matches=1, distinct_competitions=1)
    assert i_tier["evidence_tier"] == "INSUFFICIENT_EVIDENCE"
    assert i_tier["is_reliable"] is False

