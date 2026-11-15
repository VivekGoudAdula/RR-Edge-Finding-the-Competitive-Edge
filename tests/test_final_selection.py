"""Unit tests for final selection intelligence, decision matrices, and Top-10 dossiers.

Tests:
1. Decision matrix candidate volume (>=15 candidates per discipline).
2. Exactly 10 ordered, unique selections for batters and bowlers.
3. 10,000-iteration match-cluster bootstrap execution and validity.
4. Strict cross-format denominator additivity (IPL + T20I = Combined).
5. Elimination of unsupported cricket claims from decision notes.
"""

import os
import pytest
import numpy as np
import pandas as pd

from src.models.final_selection import (
    build_final_batter_decision_matrix,
    build_final_bowler_decision_matrix,
    compute_top_10_pairwise_bootstrap,
    run_final_selection_pipeline,
)


def test_final_decision_matrices_structure_and_counts():
    """Verify decision matrices have at least 15 candidates and complete schemas."""
    base_dir = "."
    b_mat = build_final_batter_decision_matrix(base_dir)
    w_mat = build_final_bowler_decision_matrix(base_dir)

    assert len(b_mat) >= 15
    assert len(w_mat) >= 15

    required_cols = [
        "player_id", "player_name", "discipline", "primary_role", "phase_suitability", "format_coverage",
        "ipl_pressure_volume", "t20i_pressure_volume", "combined_pressure_volume",
        "ipl_matches", "t20i_matches", "combined_matches",
        "is_recommended_top_10", "top_10_rank", "selection_status", "selection_rationale",
        "main_strengths", "main_weaknesses", "selection_risks",
    ]
    for col in required_cols:
        assert col in b_mat.columns, f"Missing {col} in batter decision matrix"
        assert col in w_mat.columns, f"Missing {col} in bowler decision matrix"


def test_top_10_lists_uniqueness_and_ranks():
    """Verify Top 10 lists have exactly 10 unique players ranked 1 through 10."""
    out_dir = os.path.join("data", "processed", "final_selections")
    top_b = pd.read_parquet(os.path.join(out_dir, "top_10_batters.parquet"))
    top_w = pd.read_parquet(os.path.join(out_dir, "top_10_bowlers.parquet"))

    assert len(top_b) == 10
    assert len(top_w) == 10

    # Assert ranks 1 to 10
    expected_ranks = list(range(1, 11))
    assert sorted(top_b["top_10_rank"].astype(int).tolist()) == expected_ranks
    assert sorted(top_w["top_10_rank"].astype(int).tolist()) == expected_ranks

    # Assert no duplicate IDs
    assert top_b["player_id"].nunique() == 10
    assert top_w["player_id"].nunique() == 10


def test_top_10_pairwise_bootstrap_iterations_and_intervals():
    """Verify match-cluster bootstrap results with 10,000 iterations for adjacent pairs."""
    out_dir = os.path.join("data", "processed", "final_selections")
    boot = pd.read_csv(os.path.join(out_dir, "top_10_pairwise_bootstrap.csv"))

    assert len(boot) == 18  # 9 adjacent batter pairs + 9 adjacent bowler pairs

    assert "bootstrap_se_10k" in boot.columns
    assert "bootstrap_ci_95_lower" in boot.columns
    assert "bootstrap_ci_95_upper" in boot.columns
    assert "statistical_distinction" in boot.columns

    # Standard errors must be positive and non-zero
    assert (boot["bootstrap_se_10k"] > 0.0).all()
    # CI lower must be strictly less than upper
    assert (boot["bootstrap_ci_95_lower"] < boot["bootstrap_ci_95_upper"]).all()


def test_denominator_additivity_in_final_matrices():
    """Verify cross-format exposure denominator additivity in decision matrices."""
    out_dir = os.path.join("data", "processed", "final_selections")
    b_mat = pd.read_parquet(os.path.join(out_dir, "batter_final_decision_matrix.parquet"))
    w_mat = pd.read_parquet(os.path.join(out_dir, "bowler_final_decision_matrix.parquet"))

    for df in [b_mat, w_mat]:
        np.testing.assert_array_equal(
            df["combined_pressure_volume"],
            df["ipl_pressure_volume"] + df["t20i_pressure_volume"],
        )
        np.testing.assert_array_equal(
            df["combined_matches"],
            df["ipl_matches"] + df["t20i_matches"],
        )


def test_unsupported_claims_prevention_in_final_intel():
    """Verify absence of uncalculated technical claims in final decision matrices."""
    out_dir = os.path.join("data", "processed", "final_selections")
    b_mat = pd.read_parquet(os.path.join(out_dir, "batter_final_decision_matrix.parquet"))
    w_mat = pd.read_parquet(os.path.join(out_dir, "bowler_final_decision_matrix.parquet"))

    forbidden_terms = ["yorker", "150kph", "bowl_speed", "robotic", "masterclass", "spin demolition"]

    for df in [b_mat, w_mat]:
        for text_col in ["main_strengths", "main_weaknesses", "selection_risks"]:
            for text in df[text_col].dropna():
                for term in forbidden_terms:
                    assert term not in text.lower(), f"Found forbidden term '{term}' in {text_col}: {text}"

