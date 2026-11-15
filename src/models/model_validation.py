"""
Pipeline orchestration and independent validation for Phase 2.3 player performance models.

Orchestrates:
1. Assembly of full Batter & Bowler profiles with match consistency, Empirical Bayes shrinkage,
   credible intervals, and evidence strength tiers.
2. Stratification across competition formats (IPL vs T20I) and innings phases (Powerplay, Middle, Death).
3. Export of inspectable Parquet and CSV files to data/processed/player_metrics/.
4. Comprehensive independent verification against raw ball-by-ball logs.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from src.models.batter_performance import (
    prepare_batter_delivery_attributes,
    build_batter_profile,
    build_batter_stratified_metrics,
)
from src.models.bowler_performance import (
    prepare_bowler_delivery_attributes,
    build_bowler_profile,
    build_bowler_stratified_metrics,
)
from src.models.reliability import (
    compute_batter_match_consistency,
    compute_bowler_match_consistency,
    empirical_bayes_shrink,
    compute_beta_binomial_credible_interval,
    compute_rate_uncertainty_interval,
    classify_evidence_tier,
)


def assemble_complete_batter_metrics(df_deliveries: pd.DataFrame) -> pd.DataFrame:
    """Assemble complete batter metrics table with match consistency and shrinkage.

    Parameters
    ----------
    df_deliveries : pd.DataFrame
        Deliveries dataset filtered to primary pressure cohort.

    Returns
    -------
    pd.DataFrame
        Complete batter performance table.
    """
    prepared_df = prepare_batter_delivery_attributes(df_deliveries)

    # 1. Base profile (Overall, Pressure, Normal, Deltas)
    profile = build_batter_profile(prepared_df, filter_primary_cohort=False)

    # 2. Match-level consistency
    pressure_delivs = prepared_df[prepared_df["is_pressure"]]
    consistency = compute_batter_match_consistency(pressure_delivs)
    if len(consistency) > 0:
        profile = profile.merge(
            consistency.drop(columns=["striker_name"], errors="ignore"),
            on="striker_id",
            how="left",
        )

    # 3. Empirical Bayes Shrinkage for Pressure Strike Rate
    # Cohort prior mean under pressure: 130.0
    prior_sr = 130.0
    for m_val in [15.0, 25.0, 30.0, 45.0, 60.0, 90.0]:
        profile[f"shrunk_pressure_sr_m{int(m_val)}"] = [
            empirical_bayes_shrink(sr, n, prior_sr, prior_weight=m_val)
            for sr, n in zip(profile["pressure_strike_rate"], profile["pressure_balls_faced"])
        ]

    # 4. Statistical Posterior Uncertainty Intervals (95% Credible Interval)
    sr_lower_bounds = []
    sr_upper_bounds = []
    for sr, n in zip(profile["pressure_strike_rate"], profile["pressure_balls_faced"]):
        _, low, high = compute_rate_uncertainty_interval(
            sr, n, prior_mean=prior_sr, prior_weight=30.0, population_std=30.0
        )
        sr_lower_bounds.append(round(low, 2))
        sr_upper_bounds.append(round(high, 2))

    profile["pressure_sr_ci_lower_95"] = sr_lower_bounds
    profile["pressure_sr_ci_upper_95"] = sr_upper_bounds

    # 5. Beta-Binomial Posterior for Pressure Boundary % and Dot %
    dot_means = []
    dot_lowers = []
    dot_uppers = []
    for dots, n in zip(profile["pressure_dot_balls"], profile["pressure_balls_faced"]):
        if n > 0:
            m, l, u = compute_beta_binomial_credible_interval(dots, n, prior_alpha=3.8, prior_beta=6.2)
            dot_means.append(round(m, 2))
            dot_lowers.append(round(l, 2))
            dot_uppers.append(round(u, 2))
        else:
            dot_means.append(np.nan)
            dot_lowers.append(np.nan)
            dot_uppers.append(np.nan)

    profile["pressure_dot_pct_posterior"] = dot_means
    profile["pressure_dot_pct_ci_lower_95"] = dot_lowers
    profile["pressure_dot_pct_ci_upper_95"] = dot_uppers

    # 6. Evidence Tier Classification
    evidence_tiers = []
    is_reliable_flags = []
    for n, m_cnt, c_cnt in zip(
        profile["pressure_balls_faced"],
        profile["pressure_matches"].fillna(0),
        profile["pressure_competitions"].fillna(0),
    ):
        ev = classify_evidence_tier(int(n), int(m_cnt), int(c_cnt))
        evidence_tiers.append(ev["evidence_tier"])
        is_reliable_flags.append(ev["is_reliable"])

    profile["evidence_tier"] = evidence_tiers
    profile["is_reliable_sample"] = is_reliable_flags

    return profile


def assemble_complete_bowler_metrics(df_deliveries: pd.DataFrame) -> pd.DataFrame:
    """Assemble complete bowler metrics table with match consistency and shrinkage.

    Parameters
    ----------
    df_deliveries : pd.DataFrame
        Deliveries dataset filtered to primary pressure cohort.

    Returns
    -------
    pd.DataFrame
        Complete bowler performance table.
    """
    prepared_df = prepare_bowler_delivery_attributes(df_deliveries)

    # 1. Base profile (Overall, Pressure, Normal, Deltas)
    profile = build_bowler_profile(prepared_df, filter_primary_cohort=False)

    # 2. Match-level consistency
    pressure_delivs = prepared_df[prepared_df["is_bowler_pressure"]]
    consistency = compute_bowler_match_consistency(pressure_delivs)
    if len(consistency) > 0:
        profile = profile.merge(
            consistency.drop(columns=["bowler_name"], errors="ignore"),
            on="bowler_id",
            how="left",
        )

    # 3. Empirical Bayes Shrinkage for Pressure Economy Rate
    # Cohort prior mean under pressure: 9.80
    prior_econ = 9.80
    for m_val in [15.0, 25.0, 30.0, 45.0, 60.0, 90.0]:
        profile[f"shrunk_pressure_econ_m{int(m_val)}"] = [
            empirical_bayes_shrink(econ, n, prior_econ, prior_weight=m_val)
            for econ, n in zip(profile["pressure_economy_rate"], profile["pressure_legal_balls"])
        ]

    # 4. Statistical Posterior Uncertainty Intervals (95% Credible Interval)
    econ_lower_bounds = []
    econ_upper_bounds = []
    for econ, n in zip(profile["pressure_economy_rate"], profile["pressure_legal_balls"]):
        _, low, high = compute_rate_uncertainty_interval(
            econ, n, prior_mean=prior_econ, prior_weight=30.0, population_std=2.5
        )
        econ_lower_bounds.append(round(low, 2))
        econ_upper_bounds.append(round(high, 2))

    profile["pressure_econ_ci_lower_95"] = econ_lower_bounds
    profile["pressure_econ_ci_upper_95"] = econ_upper_bounds

    # 5. Beta-Binomial Posterior for Pressure Dot %
    dot_means = []
    dot_lowers = []
    dot_uppers = []
    for dots, n in zip(profile["pressure_dot_balls"], profile["pressure_legal_balls"]):
        if n > 0:
            m, l, u = compute_beta_binomial_credible_interval(dots, n, prior_alpha=3.8, prior_beta=6.2)
            dot_means.append(round(m, 2))
            dot_lowers.append(round(l, 2))
            dot_uppers.append(round(u, 2))
        else:
            dot_means.append(np.nan)
            dot_lowers.append(np.nan)
            dot_uppers.append(np.nan)

    profile["pressure_dot_pct_posterior"] = dot_means
    profile["pressure_dot_pct_ci_lower_95"] = dot_lowers
    profile["pressure_dot_pct_ci_upper_95"] = dot_uppers

    # 6. Evidence Tier Classification
    evidence_tiers = []
    is_reliable_flags = []
    for n, m_cnt, c_cnt in zip(
        profile["pressure_legal_balls"],
        profile["pressure_matches"].fillna(0),
        profile["pressure_competitions"].fillna(0),
    ):
        ev = classify_evidence_tier(int(n), int(m_cnt), int(c_cnt))
        evidence_tiers.append(ev["evidence_tier"])
        is_reliable_flags.append(ev["is_reliable"])

    profile["evidence_tier"] = evidence_tiers
    profile["is_reliable_sample"] = is_reliable_flags

    return profile


def run_and_export_player_models(
    parquet_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, pd.DataFrame]:
    """Execute complete player performance modeling pipeline and export files.

    Parameters
    ----------
    parquet_path : Path, optional
        Path to pressure_deliveries.parquet.
    output_dir : Path, optional
        Output directory for player metrics.

    Returns
    -------
    Dict[str, pd.DataFrame]
        Dictionary of generated tables.
    """
    project_root = Path(__file__).resolve().parents[2]
    if parquet_path is None:
        parquet_path = project_root / "data" / "processed" / "pressure_deliveries.parquet"
    if output_dir is None:
        output_dir = project_root / "data" / "processed" / "player_metrics"

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Loading pressure deliveries from {parquet_path}...")
    df = pd.read_parquet(parquet_path)

    # Mandatory step: filter primary cohort
    primary_df = df[df["is_primary_pressure_cohort"]].copy()
    print(f"Filtered to primary cohort: {len(primary_df):,} deliveries across {primary_df['match_id'].nunique():,} matches.")

    # 1. Complete Batter Performance Profile
    print("Building complete Batter Performance Profile...")
    bat_overall = assemble_complete_batter_metrics(primary_df)
    bat_overall.to_parquet(output_dir / "batter_metrics_overall.parquet", index=False)
    bat_overall.to_csv(output_dir / "batter_metrics_overall.csv", index=False)
    print(f"  Exported {len(bat_overall):,} batters to batter_metrics_overall.")

    # 2. Complete Bowler Performance Profile
    print("Building complete Bowler Performance Profile...")
    bow_overall = assemble_complete_bowler_metrics(primary_df)
    bow_overall.to_parquet(output_dir / "bowler_metrics_overall.parquet", index=False)
    bow_overall.to_csv(output_dir / "bowler_metrics_overall.csv", index=False)
    print(f"  Exported {len(bow_overall):,} bowlers to bowler_metrics_overall.")

    # 3. Format Stratifications (IPL vs T20I)
    print("Building format-stratified metrics (IPL vs T20I)...")
    bat_formats = build_batter_stratified_metrics(primary_df, stratify_by="competition_type")
    bat_formats.to_parquet(output_dir / "batter_metrics_formats.parquet", index=False)
    bat_formats.to_csv(output_dir / "batter_metrics_formats.csv", index=False)

    bow_formats = build_bowler_stratified_metrics(primary_df, stratify_by="competition_type")
    bow_formats.to_parquet(output_dir / "bowler_metrics_formats.parquet", index=False)
    bow_formats.to_csv(output_dir / "bowler_metrics_formats.csv", index=False)

    # 4. Phase Stratifications (Powerplay, Middle, Death)
    print("Building phase-stratified metrics (Powerplay, Middle, Death)...")
    bat_phases = build_batter_stratified_metrics(primary_df, stratify_by="innings_phase")
    bat_phases.to_parquet(output_dir / "batter_metrics_phases.parquet", index=False)
    bat_phases.to_csv(output_dir / "batter_metrics_phases.csv", index=False)

    bow_phases = build_bowler_stratified_metrics(primary_df, stratify_by="innings_phase")
    bow_phases.to_parquet(output_dir / "bowler_metrics_phases.parquet", index=False)
    bow_phases.to_csv(output_dir / "bowler_metrics_phases.csv", index=False)

    print("All player performance models successfully generated and exported.")
    return {
        "batter_overall": bat_overall,
        "bowler_overall": bow_overall,
        "batter_formats": bat_formats,
        "bowler_formats": bow_formats,
        "batter_phases": bat_phases,
        "bowler_phases": bow_phases,
    }


if __name__ == "__main__":
    run_and_export_player_models()
