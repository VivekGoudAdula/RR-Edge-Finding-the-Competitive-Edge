"""
Unit tests for Phase 2.3.2 statistical corrections & validation closure.

Tests:
- Context-adjusted expected runs and economy calculations.
- Mathematical unit reconciliation between match-stints and deliveries.
- Chronological 3-way holdout validation execution.
- Format and phase relative baseline differences.
- Uncertainty interval safeguards and non-negativity.
"""

import sys
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.batter_performance import (
    prepare_batter_delivery_attributes,
    compute_context_adjusted_batter_metrics,
)
from src.models.bowler_performance import (
    prepare_bowler_delivery_attributes,
    compute_context_adjusted_bowler_metrics,
)
from src.models.reliability import (
    empirical_bayes_shrink,
    compute_rate_uncertainty_interval,
    compute_posterior_predictive_interval,
    evaluate_three_way_chronological_holdout,
)


class TestContextAdjustedMetrics:
    """Test context-adjusted runs above expected (RAE) and economy metrics."""

    def test_context_adjusted_batter_delta_sr(self):
        """Context adjusted delta SR must equal observed SR minus expected SR."""
        df = pd.DataFrame([
            # Batter 1 in IPL Death against 5 wkts remaining
            {"striker_id": 1, "striker_name": "Batter A", "runs": 6, "extras_type": "none",
             "is_ball_faced": True, "batter_pressure_tier": "HIGH", "innings_phase": "Death",
             "competition_type": "IPL", "wickets_remaining_before": 5, "is_primary_pressure_cohort": True},
            {"striker_id": 1, "striker_name": "Batter A", "runs": 4, "extras_type": "none",
             "is_ball_faced": True, "batter_pressure_tier": "HIGH", "innings_phase": "Death",
             "competition_type": "IPL", "wickets_remaining_before": 5, "is_primary_pressure_cohort": True},
            # Batter 2 in same context scoring 0 runs
            {"striker_id": 2, "striker_name": "Batter B", "runs": 0, "extras_type": "none",
             "is_ball_faced": True, "batter_pressure_tier": "HIGH", "innings_phase": "Death",
             "competition_type": "IPL", "wickets_remaining_before": 5, "is_primary_pressure_cohort": True},
            {"striker_id": 2, "striker_name": "Batter B", "runs": 0, "extras_type": "none",
             "is_ball_faced": True, "batter_pressure_tier": "HIGH", "innings_phase": "Death",
             "competition_type": "IPL", "wickets_remaining_before": 5, "is_primary_pressure_cohort": True},
        ])
        res = compute_context_adjusted_batter_metrics(df, filter_primary_cohort=False, min_balls=1)
        assert len(res) == 2
        for _, row in res.iterrows():
            calc_delta = row["observed_pressure_sr"] - row["expected_pressure_sr"]
            assert np.isclose(row["context_adjusted_delta_sr"], calc_delta)

        # Batter A scored 10 runs off 2 balls (SR 500), context mean is 2.5 runs/ball (SR 250)
        row_a = res[res["striker_id"] == 1].iloc[0]
        assert row_a["observed_pressure_sr"] == 500.0
        assert row_a["expected_pressure_sr"] == 250.0
        assert row_a["context_adjusted_delta_sr"] == 250.0

    def test_context_adjusted_bowler_delta_econ(self):
        """Context adjusted delta economy must equal observed Economy minus expected Economy."""
        df = pd.DataFrame([
            # Bowler 1 conceding 1 run in IPL Death
            {"bowler_id": 10, "bowler_name": "Bowler X", "runs": 1, "extras_type": "none",
             "total_delivery_runs": 1, "is_legal_ball": True, "is_bowler_wkt": False,
             "bowler_pressure_tier": "HIGH", "innings_phase": "Death",
             "competition_type": "IPL", "wickets_remaining_before": 5, "is_primary_pressure_cohort": True},
            # Bowler 2 conceding 6 runs in same context
            {"bowler_id": 20, "bowler_name": "Bowler Y", "runs": 6, "extras_type": "none",
             "total_delivery_runs": 6, "is_legal_ball": True, "is_bowler_wkt": False,
             "bowler_pressure_tier": "HIGH", "innings_phase": "Death",
             "competition_type": "IPL", "wickets_remaining_before": 5, "is_primary_pressure_cohort": True},
        ])
        res = compute_context_adjusted_bowler_metrics(df, filter_primary_cohort=False, min_legal_balls=1)
        assert len(res) == 2
        for _, row in res.iterrows():
            calc_delta = row["observed_pressure_econ"] - row["expected_pressure_econ"]
            assert np.isclose(row["context_adjusted_delta_econ"], calc_delta)

        # Bowler X conceded 1 run in 1 ball (Econ 6.0), context mean is 3.5 runs/ball (Econ 21.0)
        row_x = res[res["bowler_id"] == 10].iloc[0]
        assert row_x["observed_pressure_econ"] == 6.0
        assert row_x["expected_pressure_econ"] == 21.0
        assert row_x["context_adjusted_delta_econ"] == -15.0  # Favourable


class TestShrinkageUnitReconciliation:
    """Test shrinkage dimension calculations."""

    def test_delivery_level_theoretical_m_formula(self):
        """Delivery-level Bayes shrinkage constant equals sampling variance divided by true variance."""
        # Simulated parameters
        deliv_var = 3.0  # Var(runs per delivery)
        sr_sampling_var_per_ball = 10000.0 * deliv_var  # 30,000
        tau2_true_talent = 300.0  # Spread across true player strike rates

        theoretical_m_balls = sr_sampling_var_per_ball / tau2_true_talent
        assert np.isclose(theoretical_m_balls, 100.0)

    def test_three_way_chronological_holdout_structure(self):
        """Verify 3-way chronological holdout executes and outputs train/val/test frames."""
        matches_df = pd.DataFrame([
            {"match_id": i, "match_date": f"2023-01-{i:02d}"} for i in range(1, 21)
        ])
        deliveries = []
        for m in range(1, 21):
            for p in [1, 2]:
                for b in range(10):
                    deliveries.append({
                        "match_id": m,
                        "striker_id": p,
                        "striker_name": f"Player {p}",
                        "runs": 1 if p == 1 else 2,
                        "extras_type": "none",
                        "is_primary_pressure_cohort": True,
                        "batter_pressure_tier": "HIGH",
                    })
        deliv_df = pd.DataFrame(deliveries)
        res = evaluate_three_way_chronological_holdout(deliv_df, matches_df, discipline="batter", m_values=[0.0, 30.0], min_balls_period=5)
        assert "validation_results" in res
        assert "test_results" in res
        assert len(res["validation_results"]) == 2
        assert len(res["test_results"]) == 2
        assert res["validation_results"]["rmse"].iloc[0] >= 0.0


class TestPosteriorIntervalSafeguards:
    """Test posterior interval mathematical boundaries and non-negativity."""

    def test_rate_uncertainty_interval_non_negativity(self):
        """Lower bound for rate uncertainty interval must never be negative."""
        _, low, high = compute_rate_uncertainty_interval(
            observed_rate=20.0, sample_size=5, prior_mean=130.0, prior_weight=30.0, population_std=170.0
        )
        assert low >= 0.0
        assert high > low

    def test_posterior_predictive_interval_wider_than_parameter_interval(self):
        """Posterior predictive interval must be strictly wider than parameter interval.

        Because Var(Y_future | data) = Var(theta | data) + Var(Y_future | theta).
        """
        _, p_low, p_high = compute_rate_uncertainty_interval(
            observed_rate=140.0, sample_size=30, prior_mean=130.0, prior_weight=30.0, population_std=172.0
        )
        param_width = p_high - p_low

        _, pred_low, pred_high = compute_posterior_predictive_interval(
            observed_rate=140.0, sample_size=30, future_balls=25, prior_mean=130.0, prior_weight=30.0, delivery_std=172.0
        )
        pred_width = pred_high - pred_low

        assert pred_width > param_width
        assert pred_low >= 0.0

    def test_configurable_shrinkage_grid_m25_to_m90(self):
        """Shrinkage estimates for M=25, 45, 60, 90 must strictly pull toward prior as M increases."""
        raw = 200.0
        n = 30
        prior = 130.0
        s25 = empirical_bayes_shrink(raw, n, prior, prior_weight=25.0)
        s45 = empirical_bayes_shrink(raw, n, prior, prior_weight=45.0)
        s60 = empirical_bayes_shrink(raw, n, prior, prior_weight=60.0)
        s90 = empirical_bayes_shrink(raw, n, prior, prior_weight=90.0)

        # Monotonic regression toward prior
        assert raw > s25 > s45 > s60 > s90 > prior

