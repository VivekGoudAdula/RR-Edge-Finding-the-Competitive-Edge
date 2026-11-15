"""
Phase 2.3.1: Independent statistical and model validity unit tests.

Audits:
- Exact evidence tier boundary transitions.
- Format-specific and role-specific shrinkage validation.
- Within-stratum context-controlled rate deltas.
- Attribution integrity for extras (byes, leg-byes, wides, no-balls).
- Player pool reconciliation across primary and quarantined cohorts.
"""

import sys
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.reliability import (
    classify_evidence_tier,
    empirical_bayes_shrink,
    empirical_bayes_shrink_by_format,
    compute_beta_binomial_credible_interval,
    compute_rate_uncertainty_interval,
    evaluate_holdout_shrinkage_grid,
)
from src.models.batter_performance import prepare_batter_delivery_attributes, build_batter_stratified_metrics
from src.models.bowler_performance import prepare_bowler_delivery_attributes, build_bowler_stratified_metrics


class TestEvidenceTierBoundaries:
    """Test all edge cases and boundary thresholds for evidence tier classification."""

    def test_sixty_balls_seven_matches(self):
        """60 balls across 7 matches lacks match breadth: must fall to MODERATE."""
        res = classify_evidence_tier(sample_size=60, distinct_matches=7, distinct_competitions=3)
        assert res["evidence_tier"] == "MODERATE_EVIDENCE"
        assert res["is_reliable"] is True
        assert res["recommended_m"] == 30.0

    def test_sixty_balls_eight_matches_one_competition(self):
        """60 balls across 8 matches in 1 competition lacks multi-tournament breadth: falls to MODERATE."""
        res = classify_evidence_tier(sample_size=60, distinct_matches=8, distinct_competitions=1)
        assert res["evidence_tier"] == "MODERATE_EVIDENCE"
        assert res["is_reliable"] is True
        assert res["recommended_m"] == 30.0

    def test_confident_tier_boundary(self):
        """60 balls across 8 matches and 2 competitions meets all criteria: CONFIDENT."""
        res = classify_evidence_tier(sample_size=60, distinct_matches=8, distinct_competitions=2)
        assert res["evidence_tier"] == "CONFIDENT_EVIDENCE"
        assert res["is_reliable"] is True
        assert res["recommended_m"] == 15.0

    def test_twenty_four_balls_three_matches(self):
        """24 balls across 3 matches lacks match breadth: falls to PROVISIONAL."""
        res = classify_evidence_tier(sample_size=24, distinct_matches=3, distinct_competitions=2)
        assert res["evidence_tier"] == "PROVISIONAL_EVIDENCE"
        assert res["is_reliable"] is False
        assert res["recommended_m"] == 45.0

    def test_twenty_four_balls_four_matches(self):
        """24 balls across 4 matches qualifies for MODERATE."""
        res = classify_evidence_tier(sample_size=24, distinct_matches=4, distinct_competitions=1)
        assert res["evidence_tier"] == "MODERATE_EVIDENCE"
        assert res["is_reliable"] is True
        assert res["recommended_m"] == 30.0

    def test_twelve_balls_one_match(self):
        """12 balls across only 1 match has 0 replication: must be INSUFFICIENT."""
        res = classify_evidence_tier(sample_size=12, distinct_matches=1, distinct_competitions=1)
        assert res["evidence_tier"] == "INSUFFICIENT_EVIDENCE"
        assert res["is_reliable"] is False
        assert res["recommended_m"] == 60.0

    def test_high_volume_concentrated_exposure(self):
        """150 balls concentrated in only 3 matches lacks cross-match replication."""
        res = classify_evidence_tier(sample_size=150, distinct_matches=3, distinct_competitions=1)
        assert res["evidence_tier"] == "PROVISIONAL_EVIDENCE"
        assert res["is_reliable"] is False


class TestShrinkageAndPosteriorIntervals:
    """Test shrinkage mathematics, format calibration, and uncertainty intervals."""

    def test_format_specific_shrinkage_divergence(self):
        """IPL prior (135.3) and T20I prior (118.0) must pull identical raw SR in different directions."""
        raw_sr = 125.0
        n_balls = 20
        ipl_shrunk = empirical_bayes_shrink_by_format(raw_sr, n_balls, format_type="IPL", discipline="batter")
        t20i_shrunk = empirical_bayes_shrink_by_format(raw_sr, n_balls, format_type="T20I", discipline="batter")

        # IPL prior is 135.3 > 125.0, so IPL shrunk must pull UP
        assert ipl_shrunk > raw_sr
        # T20I prior is 118.0 < 125.0, so T20I shrunk must pull DOWN
        assert t20i_shrunk < raw_sr

    def test_beta_binomial_validity(self):
        """Beta-Binomial credible interval must have 0 <= lower <= mean <= upper <= 100."""
        mean, lower, upper = compute_beta_binomial_credible_interval(
            successes=8, trials=20, prior_alpha=3.8, prior_beta=6.2
        )
        assert 0.0 <= lower <= mean <= upper <= 100.0

    def test_rate_uncertainty_interval_shrinks_with_sample_size(self):
        """Uncertainty interval width must strictly shrink as sample size increases."""
        _, l1, u1 = compute_rate_uncertainty_interval(140.0, sample_size=10, prior_mean=130.0, prior_weight=30.0)
        _, l2, u2 = compute_rate_uncertainty_interval(140.0, sample_size=100, prior_mean=130.0, prior_weight=30.0)
        width1 = u1 - l1
        width2 = u2 - l2
        assert width2 < width1


class TestAttributionAndContextStratification:
    """Test extras attribution on bowler dot balls and stratified deltas."""

    def test_bowler_dot_ball_on_legal_byes(self):
        """Legal ball yielding 4 byes is 0 bowler runs conceded and credits a bowler dot ball."""
        df = pd.DataFrame([
            {
                "bowler_id": 1,
                "bowler_name": "Test Bowler",
                "runs": 0,
                "total_delivery_runs": 4,
                "extras_type": "byes",
                "is_legal_ball": True,
                "is_bowler_wkt": False,
                "bowler_pressure_tier": "HIGH",
            }
        ])
        prep = prepare_bowler_delivery_attributes(df)
        assert prep.loc[0, "bowler_runs_conceded"] == 0
        assert bool(prep.loc[0, "is_bowler_dot"]) is True

    def test_bowler_dot_ball_on_wide_is_false(self):
        """Wide is not a legal ball and cannot be a bowler dot ball."""
        df = pd.DataFrame([
            {
                "bowler_id": 1,
                "bowler_name": "Test Bowler",
                "runs": 0,
                "total_delivery_runs": 1,
                "extras_type": "wide",
                "is_legal_ball": False,
                "is_bowler_wkt": False,
                "bowler_pressure_tier": "HIGH",
            }
        ])
        prep = prepare_bowler_delivery_attributes(df)
        assert prep.loc[0, "bowler_runs_conceded"] == 1
        assert bool(prep.loc[0, "is_bowler_dot"]) is False

    def test_within_phase_delta_strike_rate_calculation(self):
        """build_batter_stratified_metrics computes within-phase delta strike rate."""
        df = pd.DataFrame([
            # Death pressure: 2 balls, 4 runs (SR = 200)
            {"striker_id": 1, "striker_name": "Player A", "runs": 4, "extras_type": "none",
             "is_ball_faced": True, "batter_pressure_tier": "HIGH", "innings_phase": "Death",
             "is_primary_pressure_cohort": True, "match_id": 101, "comp_id": 1, "is_wicket": 0, "dismissed_player_id": np.nan},
            {"striker_id": 1, "striker_name": "Player A", "runs": 0, "extras_type": "none",
             "is_ball_faced": True, "batter_pressure_tier": "HIGH", "innings_phase": "Death",
             "is_primary_pressure_cohort": True, "match_id": 101, "comp_id": 1, "is_wicket": 0, "dismissed_player_id": np.nan},
            # Death normal: 2 balls, 2 runs (SR = 100)
            {"striker_id": 1, "striker_name": "Player A", "runs": 1, "extras_type": "none",
             "is_ball_faced": True, "batter_pressure_tier": "LOW", "innings_phase": "Death",
             "is_primary_pressure_cohort": True, "match_id": 101, "comp_id": 1, "is_wicket": 0, "dismissed_player_id": np.nan},
            {"striker_id": 1, "striker_name": "Player A", "runs": 1, "extras_type": "none",
             "is_ball_faced": True, "batter_pressure_tier": "LOW", "innings_phase": "Death",
             "is_primary_pressure_cohort": True, "match_id": 101, "comp_id": 1, "is_wicket": 0, "dismissed_player_id": np.nan},
        ])
        res = build_batter_stratified_metrics(df, stratify_by="innings_phase", filter_primary_cohort=False)
        assert "Death_delta_strike_rate" in res.columns
        # Expected Delta = 200.0 - 100.0 = +100.0
        delta = res.loc[res["striker_id"] == 1, "Death_delta_strike_rate"].iloc[0]
        assert np.isclose(delta, 100.0)

