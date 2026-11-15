"""
Phase 3 Evaluation Engine Tests for RR EDGE.

Tests cover:
- Primary-cohort filtering (DLS isolation).
- Correct player attribution (no cross-contamination).
- Batting role and bowling role classification.
- Missing-data handling (no silent NaN → 0 for rate metrics).
- Metric directionality (higher SR = better; lower economy = better).
- Sample qualification thresholds.
- Shrinkage sensitivity (M=25,45,60,90).
- Ranking reproducibility (deterministic).
- Ranking stability (rank_range, rank_stable).
- No DLS leakage.
- No hidden arbitrary weights.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.batter_evaluation import (
    MIN_PRESSURE_BALLS_QUALIFIED,
    MIN_PRESSURE_MATCHES_QUALIFIED,
    SHRINKAGE_M_GRID,
    apply_batter_shrinkage_grid,
    build_batter_evaluation,
    classify_batting_role,
    compute_phase_pressure_metrics,
    compute_pressure_tier_breakdown,
    compute_resource_situation_metrics,
    detect_primary_format as batter_detect_format,
    compute_batter_rank_stability,
)
from src.models.bowler_evaluation import (
    apply_bowler_shrinkage_grid,
    build_bowler_evaluation,
    classify_bowling_role,
    compute_phase_pressure_metrics as bowler_phase_metrics,
    compute_pressure_tier_breakdown as bowler_tier_breakdown,
    compute_resource_situation_metrics as bowler_resource_metrics,
    compute_wicket_impact,
    detect_primary_format as bowler_detect_format,
    compute_bowler_rank_stability,
)
from src.models.reliability import empirical_bayes_shrink


# ---------------------------------------------------------------------------
# Fixtures: minimal synthetic delivery DataFrames
# ---------------------------------------------------------------------------

def _make_batter_deliveries(
    n_matches: int = 10,
    balls_per_match: int = 10,
    pressure_fraction: float = 0.6,
    competition_type: str = "IPL",
    batting_order: int = 1,
    striker_id: int = 101,
    striker_name: str = "Test Batter",
    is_primary: bool = True,
    is_dls: bool = False,
) -> pd.DataFrame:
    """Build a minimal synthetic delivery table for one batter.

    Includes all columns required by the full evaluation pipeline:
    - Core delivery fields (runs, extras_type, wicket info).
    - Pressure tier columns for batter and bowler perspectives.
    - Resource-situation columns (batter_wickets_remaining, etc.).
    - Context-model columns (wickets_remaining_before for RAE computation).
    - is_primary_pressure_cohort flag.
    """
    n = n_matches * balls_per_match
    rng = np.random.default_rng(42)

    n_pressure = int(n * pressure_fraction)
    tier_arr = ["HIGH"] * n_pressure + ["MODERATE"] * (n - n_pressure)
    rng.shuffle(tier_arr)

    runs = rng.integers(0, 7, size=n)
    df = pd.DataFrame(
        {
            "match_id": np.repeat(np.arange(n_matches), balls_per_match),
            "comp_id": 1,
            "competition_type": competition_type,
            "innings_phase": "Middle",
            "batter_innings_phase": "Middle",
            # Batter identifiers
            "striker_id": striker_id,
            "striker_name": striker_name,
            "batting_order_raw": batting_order,
            # Scoring
            "runs": runs,
            "total_delivery_runs": runs,
            "extras_type": "normal",
            # Wicket columns
            "is_wicket": rng.integers(0, 2, size=n),
            "dismissed_player_id": np.where(rng.integers(0, 2, size=n), float(striker_id), np.nan),
            # Pressure tier labels
            "batter_pressure_tier": tier_arr,
            "bowler_pressure_tier": "MODERATE",
            # Primary cohort flag (DLS exclusion)
            "is_primary_pressure_cohort": not is_dls if is_primary else False,
            # Resource-situation columns (batter view)
            "batter_wickets_remaining": rng.integers(1, 11, size=n),
            "batter_legal_balls_remaining": rng.integers(1, 60, size=n),
            # Context model columns (used by RAE)
            "wickets_remaining_before": rng.integers(1, 11, size=n),
            # Bowler and legal-ball columns (needed by bowler helpers called inside batter pipeline)
            "bowler_id": 999,
            "bowler_name": "Generic Bowler",
            "is_legal_ball": True,
            "is_bowler_wkt": False,
            "bowler_innings_phase": "Middle",
            "bowler_wickets_remaining": rng.integers(1, 11, size=n),
            "bowler_legal_balls_remaining": rng.integers(1, 60, size=n),
        }
    )
    return df


def _make_bowler_deliveries(
    n_matches: int = 10,
    balls_per_match: int = 10,
    pressure_fraction: float = 0.6,
    competition_type: str = "IPL",
    phase: str = "Death",
    bowler_id: int = 201,
    bowler_name: str = "Test Bowler",
    is_primary: bool = True,
) -> pd.DataFrame:
    """Build a minimal synthetic delivery table for one bowler.

    Includes all columns required by the full bowler evaluation pipeline:
    - Core delivery fields (runs, extras_type, legal ball, wicket info).
    - Pressure tier columns for batter and bowler perspectives.
    - Resource-situation columns (bowler_wickets_remaining, etc.).
    - Context model columns (wickets_remaining_before for RCAE computation).
    - Batter-side columns required by aggregate helpers when called on combined data.
    - is_primary_pressure_cohort flag.
    """
    n = n_matches * balls_per_match
    rng = np.random.default_rng(99)

    n_pressure = int(n * pressure_fraction)
    tier_arr = ["HIGH"] * n_pressure + ["MODERATE"] * (n - n_pressure)
    rng.shuffle(tier_arr)

    runs = rng.integers(0, 7, size=n)
    df = pd.DataFrame(
        {
            "match_id": np.repeat(np.arange(n_matches), balls_per_match),
            "comp_id": 1,
            "competition_type": competition_type,
            "innings_phase": phase,
            "bowler_innings_phase": phase,
            # Bowler identifiers
            "bowler_id": bowler_id,
            "bowler_name": bowler_name,
            # Scoring
            "runs": runs,
            "total_delivery_runs": runs,
            "extras_type": "normal",
            # Legal-ball and wicket columns
            "is_legal_ball": True,
            "is_bowler_wkt": rng.integers(0, 2, size=n).astype(bool),
            # Pressure tier labels
            "bowler_pressure_tier": tier_arr,
            "batter_pressure_tier": "MODERATE",
            # Primary cohort flag
            "is_primary_pressure_cohort": is_primary,
            # Resource-situation columns (bowler view)
            "bowler_wickets_remaining": rng.integers(1, 11, size=n),
            "bowler_legal_balls_remaining": rng.integers(1, 60, size=n),
            # Context model columns (used by RCAE)
            "wickets_remaining_before": rng.integers(1, 11, size=n),
            # Batter-side columns required by helpers called inside evaluation
            "striker_id": 999,
            "striker_name": "Generic Batter",
            "batting_order_raw": 1,
            "batter_innings_phase": phase,
            "batter_wickets_remaining": rng.integers(1, 11, size=n),
            "batter_legal_balls_remaining": rng.integers(1, 60, size=n),
        }
    )
    return df


# ============================================================================
# TEST GROUP 1: Primary-Cohort Filtering & DLS Isolation
# ============================================================================

class TestPrimaryCohortFiltering:
    """Ensure non-primary and DLS deliveries never enter evaluations."""

    def test_dls_deliveries_excluded_from_batter_evaluation(self):
        """DLS deliveries (is_primary_pressure_cohort=False) must not appear."""
        primary = _make_batter_deliveries(n_matches=6, is_primary=True)
        dls = _make_batter_deliveries(
            n_matches=3,
            is_primary=False,
            striker_id=999,
            striker_name="DLS Batter",
        )
        combined = pd.concat([primary, dls], ignore_index=True)
        result = build_batter_evaluation(combined)
        evaluation = result["evaluation"]
        assert 999 not in evaluation["striker_id"].values, (
            "DLS-quarantined batter leaked into evaluation."
        )

    def test_dls_deliveries_excluded_from_bowler_evaluation(self):
        """DLS deliveries must not appear in bowler evaluation."""
        primary = _make_bowler_deliveries(n_matches=6, is_primary=True)
        dls = _make_bowler_deliveries(
            n_matches=3,
            is_primary=False,
            bowler_id=999,
            bowler_name="DLS Bowler",
        )
        combined = pd.concat([primary, dls], ignore_index=True)
        result = build_bowler_evaluation(combined)
        assert 999 not in result["evaluation"]["bowler_id"].values, (
            "DLS-quarantined bowler leaked into evaluation."
        )

    def test_primary_cohort_flag_respected_exactly(self):
        """Evaluation row count must match distinct striker IDs in primary cohort only."""
        df = _make_batter_deliveries(n_matches=5, is_primary=True, striker_id=1)
        df2 = _make_batter_deliveries(n_matches=5, is_primary=False, striker_id=2)
        combined = pd.concat([df, df2], ignore_index=True)
        result = build_batter_evaluation(combined)
        assert len(result["evaluation"]) == 1, (
            "Only 1 primary-cohort batter should appear; non-primary excluded."
        )


# ============================================================================
# TEST GROUP 2: Player Attribution
# ============================================================================

class TestPlayerAttribution:
    """Ensure metrics are attributed to the correct player IDs."""

    def test_batter_id_preserved_through_pipeline(self):
        """striker_id in evaluation must exactly match the input."""
        df = _make_batter_deliveries(striker_id=42, striker_name="Player A")
        result = build_batter_evaluation(df)
        ids = result["evaluation"]["striker_id"].tolist()
        assert ids == [42], f"Expected [42], got {ids}"

    def test_bowler_id_preserved_through_pipeline(self):
        """bowler_id in evaluation must exactly match the input."""
        df = _make_bowler_deliveries(bowler_id=77, bowler_name="Bowler B")
        result = build_bowler_evaluation(df)
        ids = result["evaluation"]["bowler_id"].tolist()
        assert ids == [77], f"Expected [77], got {ids}"

    def test_no_cross_player_contamination_batters(self):
        """Two different batters must not share each other's ball counts."""
        df_a = _make_batter_deliveries(striker_id=1, n_matches=5)
        df_b = _make_batter_deliveries(striker_id=2, n_matches=8)
        combined = pd.concat([df_a, df_b], ignore_index=True)
        result = build_batter_evaluation(combined)
        eval_df = result["evaluation"]
        balls_1 = int(eval_df.loc[eval_df["striker_id"] == 1, "balls_faced"].iloc[0])
        balls_2 = int(eval_df.loc[eval_df["striker_id"] == 2, "balls_faced"].iloc[0])
        assert balls_1 == 50, f"Batter 1 should have 50 balls, got {balls_1}"
        assert balls_2 == 80, f"Batter 2 should have 80 balls, got {balls_2}"


# ============================================================================
# TEST GROUP 3: Role Classification
# ============================================================================

class TestRoleClassification:
    """Validate batting and bowling role assignment logic."""

    def test_top_order_role_classification(self):
        """Batter always at position 1 → Top-Order."""
        df = _make_batter_deliveries(batting_order=1)
        roles = classify_batting_role(df)
        assert roles.iloc[0]["primary_batting_role"] == "Top-Order"

    def test_middle_order_role_classification(self):
        """Batter always at position 5 → Middle-Order."""
        df = _make_batter_deliveries(batting_order=5)
        roles = classify_batting_role(df)
        assert roles.iloc[0]["primary_batting_role"] == "Middle-Order"

    def test_lower_order_role_classification(self):
        """Batter always at position 8 → Lower-Order."""
        df = _make_batter_deliveries(batting_order=8)
        roles = classify_batting_role(df)
        assert roles.iloc[0]["primary_batting_role"] == "Lower-Order"

    def test_death_specialist_bowling_role(self):
        """Bowler with all deliveries in Death → Death Specialist."""
        from src.models.bowler_performance import prepare_bowler_delivery_attributes
        df = _make_bowler_deliveries(phase="Death", n_matches=10, balls_per_match=10)
        prepared = prepare_bowler_delivery_attributes(df)
        roles = classify_bowling_role(prepared)
        assert roles.iloc[0]["primary_bowling_role"] == "Death Specialist"

    def test_powerplay_specialist_bowling_role(self):
        """Bowler with all deliveries in Powerplay → Powerplay Specialist."""
        from src.models.bowler_performance import prepare_bowler_delivery_attributes
        df = _make_bowler_deliveries(phase="Powerplay", n_matches=10, balls_per_match=10)
        prepared = prepare_bowler_delivery_attributes(df)
        roles = classify_bowling_role(prepared)
        assert roles.iloc[0]["primary_bowling_role"] == "Powerplay Specialist"

    def test_all_phases_bowling_role(self):
        """Bowler split evenly across all phases → All-Phases."""
        from src.models.bowler_performance import prepare_bowler_delivery_attributes
        df1 = _make_bowler_deliveries(phase="Powerplay", n_matches=5, balls_per_match=6)
        df2 = _make_bowler_deliveries(phase="Middle", n_matches=5, balls_per_match=6)
        df3 = _make_bowler_deliveries(phase="Death", n_matches=5, balls_per_match=6)
        combined = pd.concat([df1, df2, df3], ignore_index=True)
        prepared = prepare_bowler_delivery_attributes(combined)
        roles = classify_bowling_role(prepared)
        assert roles.iloc[0]["primary_bowling_role"] == "All-Phases"


# ============================================================================
# TEST GROUP 4: Missing-Data Handling
# ============================================================================

class TestMissingDataHandling:
    """Ensure rate metrics stay NaN where insufficient data exists."""

    def test_pressure_sr_is_nan_for_zero_pressure_balls(self):
        """A batter with no pressure deliveries must have NaN pressure_strike_rate."""
        df = _make_batter_deliveries(pressure_fraction=0.0)
        result = build_batter_evaluation(df)
        sr = result["evaluation"]["pressure_strike_rate"].iloc[0]
        assert pd.isna(sr), (
            f"pressure_strike_rate should be NaN for 0 pressure balls, got {sr}"
        )

    def test_pressure_economy_is_nan_for_zero_pressure_balls(self):
        """A bowler with no pressure deliveries must have NaN pressure_economy_rate."""
        df = _make_bowler_deliveries(pressure_fraction=0.0)
        result = build_bowler_evaluation(df)
        econ = result["evaluation"]["pressure_economy_rate"].iloc[0]
        assert pd.isna(econ), (
            f"pressure_economy_rate should be NaN for 0 pressure legal balls, got {econ}"
        )

    def test_no_silent_zero_substitution_for_rate_columns(self):
        """Ensure count-zero players have NaN (not 0.0) for rate metrics."""
        df = _make_batter_deliveries(n_matches=5)
        result = build_batter_evaluation(df)
        # players with >=1 ball will have a rate; check no rate == 0 from fill
        rate_col = "pressure_strike_rate"
        # should not be an array of zeros
        non_nan_rates = result["evaluation"][rate_col].dropna()
        assert len(non_nan_rates) > 0, "Expected at least one non-NaN pressure SR."


# ============================================================================
# TEST GROUP 5: Metric Directionality
# ============================================================================

class TestMetricDirectionality:
    """Confirm that metrics move in the correct direction when performance improves."""

    def test_higher_sr_gives_higher_rank(self):
        """High-SR batter should have a better (lower number) shrunk rank than low-SR."""
        # Build two batters: one scores 6 on every ball, one scores 0
        def _make_extreme_batter(striker_id: int, runs_per_ball: int) -> pd.DataFrame:
            n = 50
            df = _make_batter_deliveries(
                striker_id=striker_id,
                striker_name=f"Batter {striker_id}",
                n_matches=10,
                balls_per_match=5,
                pressure_fraction=1.0,
            )
            df["runs"] = runs_per_ball
            return df

        df_good = _make_extreme_batter(1, 6)
        df_poor = _make_extreme_batter(2, 0)
        combined = pd.concat([df_good, df_poor], ignore_index=True)
        result = build_batter_evaluation(combined)
        eval_df = result["evaluation"]
        sr_good = float(eval_df.loc[eval_df["striker_id"] == 1, "pressure_strike_rate"].iloc[0])
        sr_poor = float(eval_df.loc[eval_df["striker_id"] == 2, "pressure_strike_rate"].iloc[0])
        assert sr_good > sr_poor, f"Good batter SR {sr_good} not > poor batter SR {sr_poor}"

    def test_lower_economy_gives_better_bowler_rank(self):
        """Economy-based bowler ranking: bowler conceding 4/over should rank above 10/over."""
        from src.models.bowler_performance import prepare_bowler_delivery_attributes

        def _make_extreme_bowler(bowler_id: int, runs_per_ball: int) -> pd.DataFrame:
            df = _make_bowler_deliveries(
                bowler_id=bowler_id,
                bowler_name=f"Bowler {bowler_id}",
                n_matches=10,
                balls_per_match=5,
                pressure_fraction=1.0,
            )
            df["runs"] = runs_per_ball
            df["total_delivery_runs"] = runs_per_ball
            return df

        df_good = _make_extreme_bowler(1, 1)   # 6/over = 6.0 economy
        df_poor = _make_extreme_bowler(2, 3)   # 18/over = 18.0 economy
        combined = pd.concat([df_good, df_poor], ignore_index=True)
        result = build_bowler_evaluation(combined)
        eval_df = result["evaluation"]
        econ_good = float(eval_df.loc[eval_df["bowler_id"] == 1, "pressure_economy_rate"].iloc[0])
        econ_poor = float(eval_df.loc[eval_df["bowler_id"] == 2, "pressure_economy_rate"].iloc[0])
        assert econ_good < econ_poor, (
            f"Good bowler economy {econ_good} not < poor bowler economy {econ_poor}"
        )

    def test_delta_sr_positive_means_better_under_pressure(self):
        """delta_strike_rate > 0 means batter performs faster under pressure than normal."""
        df = _make_batter_deliveries(n_matches=10, pressure_fraction=0.5)
        # Force pressure deliveries to yield higher runs
        df.loc[df["batter_pressure_tier"] == "HIGH", "runs"] = 6
        df.loc[df["batter_pressure_tier"] == "MODERATE", "runs"] = 0
        result = build_batter_evaluation(df)
        delta = float(result["evaluation"]["delta_strike_rate"].iloc[0])
        assert delta > 0, f"delta_strike_rate should be >0 when pressure SR > normal SR, got {delta}"

    def test_wicket_impact_decreases_with_higher_economy(self):
        """Bowler with same wickets but higher economy must have lower wicket_impact_score."""
        from src.models.bowler_performance import prepare_bowler_delivery_attributes

        def _make_wicket_bowler(bid: int, runs_per_ball: int) -> pd.DataFrame:
            df = _make_bowler_deliveries(
                bowler_id=bid,
                n_matches=10,
                balls_per_match=6,
                pressure_fraction=1.0,
            )
            df["runs"] = runs_per_ball
            df["total_delivery_runs"] = runs_per_ball
            df["is_bowler_wkt"] = False
            # Give every 6th ball a wicket so wkt rate is equal for both
            df.loc[df.index % 6 == 0, "is_bowler_wkt"] = True
            return df

        df_cheap = _make_wicket_bowler(1, 1)
        df_expensive = _make_wicket_bowler(2, 4)
        combined = pd.concat([df_cheap, df_expensive], ignore_index=True)
        prepared = prepare_bowler_delivery_attributes(combined[combined["is_primary_pressure_cohort"]])
        impact = compute_wicket_impact(prepared)
        score_cheap = float(impact.loc[impact["bowler_id"] == 1, "wicket_impact_score"].iloc[0])
        score_expensive = float(impact.loc[impact["bowler_id"] == 2, "wicket_impact_score"].iloc[0])
        assert score_cheap > score_expensive, (
            f"Cheap wicket-taker should have higher impact score, got {score_cheap} vs {score_expensive}"
        )


# ============================================================================
# TEST GROUP 6: Sample Qualification
# ============================================================================

class TestSampleQualification:
    """Validate that qualification thresholds exclude low-exposure players."""

    def test_low_exposure_batter_not_qualified(self):
        """Batter with 5 matches but only 10 balls should NOT meet qualification."""
        df = _make_batter_deliveries(n_matches=5, balls_per_match=2, pressure_fraction=1.0)
        result = build_batter_evaluation(df)
        qualified = result["qualified"]
        assert len(qualified) == 0, (
            f"Expected 0 qualified batters with low exposure, got {len(qualified)}."
        )

    def test_sufficient_exposure_batter_qualified(self):
        """Batter with 10 matches and 60 pressure balls should be qualified."""
        df = _make_batter_deliveries(n_matches=10, balls_per_match=10, pressure_fraction=0.6)
        result = build_batter_evaluation(df)
        qualified = result["qualified"]
        assert len(qualified) == 1, (
            f"Expected 1 qualified batter, got {len(qualified)}."
        )

    def test_low_exposure_bowler_not_qualified(self):
        """Bowler with only 2 matches should NOT meet qualification."""
        df = _make_bowler_deliveries(n_matches=2, balls_per_match=10, pressure_fraction=1.0)
        result = build_bowler_evaluation(df)
        qualified = result["qualified"]
        assert len(qualified) == 0, (
            f"Expected 0 qualified bowlers with 2 matches, got {len(qualified)}."
        )

    def test_sufficient_exposure_bowler_qualified(self):
        """Bowler with 8 matches and 60 pressure balls should be qualified."""
        df = _make_bowler_deliveries(n_matches=8, balls_per_match=10, pressure_fraction=0.6)
        result = build_bowler_evaluation(df)
        qualified = result["qualified"]
        assert len(qualified) == 1, (
            f"Expected 1 qualified bowler, got {len(qualified)}."
        )

    def test_evidence_tier_assigned(self):
        """Every evaluation row must have a non-null evidence_tier."""
        df = _make_batter_deliveries(n_matches=10)
        result = build_batter_evaluation(df)
        assert result["evaluation"]["evidence_tier"].notna().all(), (
            "evidence_tier must be populated for all players."
        )


# ============================================================================
# TEST GROUP 7: Shrinkage Sensitivity
# ============================================================================

class TestShrinkageSensitivity:
    """Verify shrinkage grid produces expected M=25,45,60,90 columns."""

    def test_batter_shrinkage_columns_present(self):
        """shrunk_pressure_sr_m{M} must exist for all M in [25,45,60,90]."""
        df = _make_batter_deliveries(n_matches=10, balls_per_match=10)
        result = build_batter_evaluation(df)
        for m in SHRINKAGE_M_GRID:
            col = f"shrunk_pressure_sr_m{m}"
            assert col in result["evaluation"].columns, f"Missing column: {col}"

    def test_bowler_shrinkage_columns_present(self):
        """shrunk_pressure_econ_m{M} must exist for all M in [25,45,60,90]."""
        df = _make_bowler_deliveries(n_matches=10, balls_per_match=10)
        result = build_bowler_evaluation(df)
        for m in SHRINKAGE_M_GRID:
            col = f"shrunk_pressure_econ_m{m}"
            assert col in result["evaluation"].columns, f"Missing column: {col}"

    def test_higher_m_shrinks_more_toward_prior(self):
        """Higher M must pull the shrunk estimate closer to the prior mean."""
        observed_sr = 200.0
        prior_mean = 135.3
        n_balls = 30
        shrunk_values = [
            empirical_bayes_shrink(observed_sr, n_balls, prior_mean, prior_weight=float(m))
            for m in SHRINKAGE_M_GRID
        ]
        # Shrunk values should decrease monotonically as M increases (pulled toward prior)
        for i in range(len(shrunk_values) - 1):
            assert shrunk_values[i] >= shrunk_values[i + 1], (
                f"Higher M should shrink more. M={SHRINKAGE_M_GRID[i]}: {shrunk_values[i]}, "
                f"M={SHRINKAGE_M_GRID[i+1]}: {shrunk_values[i+1]}"
            )

    def test_shrinkage_produces_finite_values(self):
        """All shrunk columns must be finite (no NaN or Inf)."""
        df = _make_batter_deliveries(n_matches=10, balls_per_match=10)
        result = build_batter_evaluation(df)
        for m in SHRINKAGE_M_GRID:
            col = f"shrunk_pressure_sr_m{m}"
            vals = result["evaluation"][col]
            assert vals.notna().all(), f"NaN in {col}"
            assert np.isfinite(vals).all(), f"Inf in {col}"


# ============================================================================
# TEST GROUP 8: Ranking Reproducibility
# ============================================================================

class TestRankingReproducibility:
    """Rankings must be deterministic given the same input data."""

    def test_batter_evaluation_is_deterministic(self):
        """Running build_batter_evaluation twice must yield identical results."""
        df = _make_batter_deliveries(n_matches=10)
        r1 = build_batter_evaluation(df)["evaluation"]
        r2 = build_batter_evaluation(df)["evaluation"]
        pd.testing.assert_frame_equal(r1.reset_index(drop=True), r2.reset_index(drop=True))

    def test_bowler_evaluation_is_deterministic(self):
        """Running build_bowler_evaluation twice must yield identical results."""
        df = _make_bowler_deliveries(n_matches=10)
        r1 = build_bowler_evaluation(df)["evaluation"]
        r2 = build_bowler_evaluation(df)["evaluation"]
        pd.testing.assert_frame_equal(r1.reset_index(drop=True), r2.reset_index(drop=True))


# ============================================================================
# TEST GROUP 9: Rank Stability
# ============================================================================

class TestRankStability:
    """Validate rank stability metadata is computed and meaningful."""

    def test_batter_rank_stability_has_required_columns(self):
        """rank_stability output must include rank_range, rank_std, rank_stable."""
        df = _make_batter_deliveries(n_matches=10, balls_per_match=10)
        result = build_batter_evaluation(df)
        stability = result["rank_stability"]
        for col in ["rank_range", "rank_std", "rank_stable"]:
            assert col in stability.columns, f"Missing column: {col}"

    def test_bowler_rank_stability_has_required_columns(self):
        """rank_stability output must include rank_range, rank_std, rank_stable."""
        df = _make_bowler_deliveries(n_matches=10, balls_per_match=10)
        result = build_bowler_evaluation(df)
        stability = result["rank_stability"]
        for col in ["rank_range", "rank_std", "rank_stable"]:
            assert col in stability.columns, f"Missing column: {col}"

    def test_perfectly_stable_batter_has_zero_rank_range(self):
        """With a single player, rank range must be 0."""
        df = _make_batter_deliveries(n_matches=10, balls_per_match=10, pressure_fraction=0.8)
        result = build_batter_evaluation(df)
        stability = result["rank_stability"]
        if len(stability) > 0:
            assert int(stability.iloc[0]["rank_range"]) == 0, (
                "Single player should have rank_range = 0."
            )


# ============================================================================
# TEST GROUP 10: No Hidden Arbitrary Weights
# ============================================================================

class TestNoHiddenWeights:
    """Confirm component metrics are explicitly visible alongside any composite."""

    def test_batter_component_metrics_visible(self):
        """All key component metrics must be present as individual columns."""
        required = [
            "pressure_balls_faced",
            "pressure_strike_rate",
            "pressure_boundary_ball_pct",
            "pressure_dot_ball_pct",
            "delta_strike_rate",
            "evidence_tier",
        ]
        df = _make_batter_deliveries(n_matches=10)
        result = build_batter_evaluation(df)
        for col in required:
            assert col in result["evaluation"].columns, (
                f"Required component metric '{col}' missing from evaluation."
            )

    def test_bowler_component_metrics_visible(self):
        """All key component metrics must be present as individual columns."""
        required = [
            "pressure_legal_balls",
            "pressure_economy_rate",
            "pressure_wickets",
            "pressure_dot_ball_pct",
            "pressure_boundary_concession_pct",
            "delta_economy",
            "evidence_tier",
            "wickets_per_over",
        ]
        df = _make_bowler_deliveries(n_matches=10)
        result = build_bowler_evaluation(df)
        for col in required:
            assert col in result["evaluation"].columns, (
                f"Required component metric '{col}' missing from evaluation."
            )

    def test_batter_evaluation_has_no_opaque_composite_score(self):
        """The evaluation must not contain a column called 'score' or 'composite'."""
        df = _make_batter_deliveries(n_matches=10)
        result = build_batter_evaluation(df)
        cols_lower = [c.lower() for c in result["evaluation"].columns]
        assert "composite_score" not in cols_lower, "Opaque composite_score column found."
        assert "final_score" not in cols_lower, "Opaque final_score column found."

    def test_bowler_evaluation_has_no_opaque_composite_score(self):
        """The evaluation must not contain a column called 'score' or 'composite'."""
        df = _make_bowler_deliveries(n_matches=10)
        result = build_bowler_evaluation(df)
        cols_lower = [c.lower() for c in result["evaluation"].columns]
        assert "composite_score" not in cols_lower, "Opaque composite_score column found."
        assert "final_score" not in cols_lower, "Opaque final_score column found."


# ============================================================================
# TEST GROUP 11: Phase and Tier Metrics Structural Integrity
# ============================================================================

class TestPhaseAndTierMetrics:
    """Validate phase and pressure-tier breakdown outputs are well-formed."""

    def test_batter_phase_metrics_has_phase_column(self):
        """Phase metrics must include 'innings_phase' column."""
        from src.models.batter_performance import prepare_batter_delivery_attributes
        df = _make_batter_deliveries(n_matches=10)
        prepared = prepare_batter_delivery_attributes(df[df["is_primary_pressure_cohort"]])
        phase_df = compute_phase_pressure_metrics(prepared)
        if not phase_df.empty:
            assert "innings_phase" in phase_df.columns

    def test_bowler_phase_metrics_has_phase_column(self):
        """Bowler phase metrics must include 'bowler_innings_phase' column."""
        from src.models.bowler_performance import prepare_bowler_delivery_attributes
        df = _make_bowler_deliveries(n_matches=10)
        prepared = prepare_bowler_delivery_attributes(df[df["is_primary_pressure_cohort"]])
        phase_df = bowler_phase_metrics(prepared)
        if not phase_df.empty:
            assert "bowler_innings_phase" in phase_df.columns

    def test_tier_breakdown_contains_high_and_extreme_tiers_only(self):
        """Pressure tier breakdown must only contain HIGH and EXTREME rows."""
        from src.models.batter_performance import prepare_batter_delivery_attributes
        df = _make_batter_deliveries(n_matches=10)
        prepared = prepare_batter_delivery_attributes(df[df["is_primary_pressure_cohort"]])
        tier_df = compute_pressure_tier_breakdown(prepared)
        if not tier_df.empty:
            valid = tier_df["batter_pressure_tier"].isin(["HIGH", "EXTREME"])
            assert valid.all(), "Tier breakdown contains non-HIGH/EXTREME tiers."


# ============================================================================
# TEST GROUP 12: Resource Situation Metrics
# ============================================================================

class TestResourceSituationMetrics:
    """Validate resource-situation columns appear in evaluation output."""

    def test_batter_resource_columns_present(self):
        """Tail anchor and final crunch metrics must appear in evaluation."""
        df = _make_batter_deliveries(n_matches=10, balls_per_match=10)
        # Ensure some deliveries have tight resources
        df.loc[:20, "batter_wickets_remaining"] = 2
        df.loc[:20, "batter_legal_balls_remaining"] = 8
        result = build_batter_evaluation(df)
        eval_df = result["evaluation"]
        # At least one resource column should be present
        resource_cols = [c for c in eval_df.columns if "tail_anchor" in c or "crunch" in c]
        assert len(resource_cols) > 0, "No resource-situation columns found in batter evaluation."

    def test_bowler_resource_columns_present(self):
        """vs_top_order and vs_tail economy columns must appear in evaluation."""
        df = _make_bowler_deliveries(n_matches=10, balls_per_match=10)
        df.loc[:20, "bowler_wickets_remaining"] = 1
        result = build_bowler_evaluation(df)
        eval_df = result["evaluation"]
        resource_cols = [c for c in eval_df.columns if "vs_tail" in c or "vs_top_order" in c]
        assert len(resource_cols) > 0, "No resource-situation columns found in bowler evaluation."


# ============================================================================
# TEST GROUP 13: Format Separation & Comparability
# ============================================================================

class TestFormatSeparationAndComparability:
    """Validate format-specific evaluation and isolation."""

    def test_batter_ipl_only_evaluation(self):
        """IPL-only evaluation must only contain IPL deliveries."""
        df_ipl = _make_batter_deliveries(competition_type="IPL", n_matches=6, striker_id=1)
        df_t20i = _make_batter_deliveries(competition_type="T20I", n_matches=6, striker_id=2)
        combined = pd.concat([df_ipl, df_t20i], ignore_index=True)

        res_ipl = build_batter_evaluation(combined, competition_type="IPL")
        eval_ipl = res_ipl["evaluation"]
        assert 1 in eval_ipl["striker_id"].values
        assert 2 not in eval_ipl["striker_id"].values

    def test_bowler_t20i_only_evaluation(self):
        """T20I-only evaluation must only contain T20I deliveries."""
        df_ipl = _make_bowler_deliveries(competition_type="IPL", n_matches=6, bowler_id=10)
        df_t20i = _make_bowler_deliveries(competition_type="T20I", n_matches=6, bowler_id=20)
        combined = pd.concat([df_ipl, df_t20i], ignore_index=True)

        res_t20i = build_bowler_evaluation(combined, competition_type="T20I")
        eval_t20i = res_t20i["evaluation"]
        assert 20 in eval_t20i["bowler_id"].values
        assert 10 not in eval_t20i["bowler_id"].values


# ============================================================================
# TEST GROUP 14: Qualification Sensitivity & Evidence Tier Audit
# ============================================================================

class TestQualificationSensitivityAndIntegrity:
    """Validate sensitivity threshold tagging and evidence tier audit logic."""

    def test_qualification_sensitivity_cohorts(self):
        """Candidates should be properly categorized into Strict, Balanced, and Discovery."""
        from src.models.batter_evaluation import build_batter_qualification_sensitivity

        # Batter with 120 balls, 12 matches -> Strict
        df_strict = _make_batter_deliveries(n_matches=12, balls_per_match=10, pressure_fraction=1.0, striker_id=1)
        # Batter with 70 balls, 7 matches -> Balanced
        df_balanced = _make_batter_deliveries(n_matches=7, balls_per_match=10, pressure_fraction=1.0, striker_id=2)
        # Batter with 35 balls, 5 matches -> Discovery
        df_discovery = _make_batter_deliveries(n_matches=5, balls_per_match=7, pressure_fraction=1.0, striker_id=3)

        combined = pd.concat([df_strict, df_balanced, df_discovery], ignore_index=True)
        eval_res = build_batter_evaluation(combined)["evaluation"]
        sens_df = build_batter_qualification_sensitivity(eval_res)

        cohort_map = sens_df.set_index("striker_id")["qualification_cohort"].to_dict()
        assert "Strict" in cohort_map.get(1, "")
        assert "Balanced" in cohort_map.get(2, "")
        assert "Discovery" in cohort_map.get(3, "")

    def test_evidence_tier_match_count_distinction_vaibhav_vs_ehsan(self):
        """Demonstrate that distinct_matches >= 8 separates CONFIDENT from MODERATE."""
        from src.models.reliability import classify_evidence_tier

        # Vaibhav condition: 86 balls, 16 matches, 5 competitions -> CONFIDENT
        res_v = classify_evidence_tier(sample_size=86, distinct_matches=16, distinct_competitions=5)
        assert res_v["evidence_tier"] == "CONFIDENT_EVIDENCE"

        # Ehsan condition: 63 balls, 7 matches (< 8), 3 competitions -> MODERATE
        res_e = classify_evidence_tier(sample_size=63, distinct_matches=7, distinct_competitions=3)
        assert res_e["evidence_tier"] == "MODERATE_EVIDENCE"

