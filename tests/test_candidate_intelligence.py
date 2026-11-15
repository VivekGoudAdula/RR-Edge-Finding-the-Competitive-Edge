"""Unit tests for candidate intelligence, statistical integrity corrections, and comparative profiles.

Tests:
1. Match-cluster-aware bootstrap resampling uncertainty and small-sample detection.
2. Cross-format exposure denominator reconciliation (IPL + T20I = Combined).
3. Auditing and prevention of unsupported cricket interpretation claims.
4. Candidate pool structure, qualification tiers, and stability archetypes.
"""

import os
import pytest
import numpy as np
import pandas as pd

from src.models.candidate_intelligence import (
    assign_qualification_tier,
    compute_match_cluster_bootstrap,
    compute_player_reconciliation_denominators,
    build_batter_candidate_pool,
    build_bowler_candidate_pool,
    compute_head_to_head_comparisons,
    compute_candidate_stability,
    compute_candidate_risk_flags,
    run_candidate_intelligence_pipeline,
)


def test_assign_qualification_tier():
    """Verify correct qualification tier assignment according to sample rules."""
    assert assign_qualification_tier(120, 10) == "Strict"
    assert assign_qualification_tier(100, 8) == "Strict"
    assert assign_qualification_tier(99, 12) == "Balanced"
    assert assign_qualification_tier(60, 6) == "Balanced"
    assert assign_qualification_tier(75, 5) == "Discovery"
    assert assign_qualification_tier(45, 6) == "Discovery"
    assert assign_qualification_tier(30, 4) == "Discovery"


def test_match_cluster_bootstrap_statistical_integrity():
    """Verify match-cluster bootstrap uncertainty estimation and sample assessment."""
    p_df = pd.read_parquet(os.path.join("data", "processed", "pressure_deliveries.parquet"))
    b_ipl = pd.read_parquet(os.path.join("data", "processed", "candidate_intelligence", "batter_candidates_ipl.parquet"))

    j_row = b_ipl[b_ipl["striker_name"].str.contains("Jaiswal")].iloc[0]
    k_row = b_ipl[b_ipl["striker_name"].str.contains("Kohli")].iloc[0]

    res = compute_match_cluster_bootstrap(
        deliveries_df=p_df,
        player_a_id=int(j_row["striker_id"]),
        player_b_id=int(k_row["striker_id"]),
        discipline="Batter",
        comp_type="IPL",
        n_boot=500,
        seed=42,
    )

    assert res["bootstrap_se"] > 0.0
    assert res["bootstrap_ci_95_lower"] < res["bootstrap_ci_95_upper"]
    assert res["effective_sample_assessment"] == "ROBUST_SAMPLE"
    # CI should cross 0 for Jaiswal vs Kohli
    assert res["bootstrap_ci_95_lower"] <= 0.0 <= res["bootstrap_ci_95_upper"]
    assert res["statistical_distinction"] == "NO_STATISTICAL_DISTINCTION_CONFIRMED"


def test_small_sample_inconclusive_flagging():
    """Verify that comparisons with small samples are flagged as inconclusive."""
    out_dir = os.path.join("data", "processed", "candidate_intelligence")
    h2h_bat = pd.read_csv(os.path.join(out_dir, "batter_head_to_head.csv"))
    h2h_bowl = pd.read_csv(os.path.join(out_dir, "bowler_head_to_head.csv"))

    # Check that McGurk vs Sooryavanshi comparison is marked inconclusive due to McGurk's 6 matches
    mcgurk_comp = h2h_bat[h2h_bat["profile_id"] == "IPL_BAT_PROF_02"].iloc[0]
    assert mcgurk_comp["effective_sample_assessment"] == "INSUFFICIENT_SAMPLE_LIMITATION"
    assert mcgurk_comp["statistical_distinction"] == "INCONCLUSIVE_INSUFFICIENT_SAMPLE"

    # Check that Mayank Yadav comparison is marked inconclusive due to 5 matches
    mayank_comp = h2h_bowl[h2h_bowl["profile_id"] == "IPL_BOWL_PROF_05"].iloc[0]
    assert mayank_comp["effective_sample_assessment"] == "INSUFFICIENT_SAMPLE_LIMITATION"
    assert mayank_comp["statistical_distinction"] == "INCONCLUSIVE_INSUFFICIENT_SAMPLE"


def test_exposure_denominator_reconciliation():
    """Verify exact cross-format exposure denominator reconciliation for key players."""
    out_dir = os.path.join("data", "processed", "candidate_intelligence")
    recon = pd.read_csv(os.path.join(out_dir, "candidate_denominator_reconciliation.csv"))

    # Assert additivity: Combined == IPL + T20I across all candidates
    np.testing.assert_array_equal(
        recon["combined_pressure_volume"],
        recon["ipl_pressure_volume"] + recon["t20i_pressure_volume"],
    )
    np.testing.assert_array_equal(
        recon["combined_distinct_matches"],
        recon["ipl_distinct_matches"] + recon["t20i_distinct_matches"],
    )

    # 1. Vaibhav Sooryavanshi: 76 IPL + 10 T20I = 86 Combined balls, 12 + 4 = 16 matches
    soorya = recon[recon["player_name"].str.contains("Sooryavanshi")].iloc[0]
    assert soorya["ipl_pressure_volume"] == 76
    assert soorya["t20i_pressure_volume"] == 10
    assert soorya["combined_pressure_volume"] == 86
    assert soorya["ipl_distinct_matches"] == 12
    assert soorya["t20i_distinct_matches"] == 4
    assert soorya["combined_distinct_matches"] == 16

    # 2. Tim David: 334 IPL + 176 T20I = 510 Combined balls, 32 + 15 = 47 matches
    david = recon[recon["player_name"].str.contains("Tim David")].iloc[0]
    assert david["ipl_pressure_volume"] == 334
    assert david["t20i_pressure_volume"] == 176
    assert david["combined_pressure_volume"] == 510
    assert david["ipl_distinct_matches"] == 32
    assert david["t20i_distinct_matches"] == 15
    assert david["combined_distinct_matches"] == 47

    # 3. Suryakumar Yadav: 579 IPL + 253 T20I = 832 Combined balls, 34 + 26 = 60 matches
    sky = recon[recon["player_name"].str.contains("Suryakumar")].iloc[0]
    assert sky["ipl_pressure_volume"] == 579
    assert sky["t20i_pressure_volume"] == 253
    assert sky["combined_pressure_volume"] == 832
    assert sky["ipl_distinct_matches"] == 34
    assert sky["t20i_distinct_matches"] == 26
    assert sky["combined_distinct_matches"] == 60


def test_prevention_of_unsupported_claims():
    """Verify that narrative text fields do not contain unverified technical speculation."""
    out_dir = os.path.join("data", "processed", "candidate_intelligence")
    h2h_bat = pd.read_csv(os.path.join(out_dir, "batter_head_to_head.csv"))
    h2h_bowl = pd.read_csv(os.path.join(out_dir, "bowler_head_to_head.csv"))
    risk = pd.read_csv(os.path.join(out_dir, "candidate_risk_flags.csv"))

    prohibited_terms = ["yorker", "150kph", "bowl_speed", "robotic", "masterclass", "spin demolition"]

    for df in [h2h_bat, h2h_bowl]:
        for text in df["tactical_tradeoff_evidence"].dropna():
            for term in prohibited_terms:
                assert term not in text.lower(), f"Found unsupported term '{term}' in comparison evidence text: {text}"

    for note in risk["risk_notes"].dropna():
        for term in prohibited_terms:
            assert term not in note.lower(), f"Found unsupported term '{term}' in risk notes: {note}"


def test_candidate_pools_structure_and_sizes():
    """Verify that generated candidate pool files exist and conform to schema."""
    out_dir = os.path.join("data", "processed", "candidate_intelligence")
    
    b_ipl = pd.read_parquet(os.path.join(out_dir, "batter_candidates_ipl.parquet"))
    b_t20i = pd.read_parquet(os.path.join(out_dir, "batter_candidates_t20i.parquet"))
    w_ipl = pd.read_parquet(os.path.join(out_dir, "bowler_candidates_ipl.parquet"))
    w_t20i = pd.read_parquet(os.path.join(out_dir, "bowler_candidates_t20i.parquet"))

    assert 20 <= len(b_ipl) <= 35
    assert 20 <= len(b_t20i) <= 35
    assert 20 <= len(w_ipl) <= 35
    assert 20 <= len(w_t20i) <= 35

    # Denominator columns must be present in candidate files
    for df in [b_ipl, b_t20i]:
        assert "ipl_pressure_balls" in df.columns
        assert "t20i_pressure_balls" in df.columns
        assert "combined_pressure_balls" in df.columns

    for df in [w_ipl, w_t20i]:
        assert "ipl_pressure_legal_balls" in df.columns
        assert "t20i_pressure_legal_balls" in df.columns
        assert "combined_pressure_legal_balls" in df.columns


def test_candidate_stability_archetypes():
    """Verify stability analysis calculations and archetype assignments."""
    out_dir = os.path.join("data", "processed", "candidate_intelligence")
    stab = pd.read_csv(os.path.join(out_dir, "candidate_stability.csv"))

    assert len(stab) > 100
    expected_archetypes = {"ROBUST_ANCHOR", "SHRINKAGE_SENSITIVE", "CONTEXT_DEPENDENT", "DISCOVERY_UPSIDE"}
    found_archetypes = set(stab["stability_archetype"].unique())
    assert found_archetypes.issubset(expected_archetypes)
    assert len(found_archetypes) >= 3
    assert (stab["shrinkage_rank_max_shift"] >= 0).all()
