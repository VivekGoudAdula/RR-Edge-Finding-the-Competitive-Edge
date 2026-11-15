"""
Batter Evaluation Engine for RR EDGE — Phase 3.

Builds an explainable, role-aware, evidence-weighted batter evaluation that
produces a full component profile and sensitivity-tested ranking for every
qualified batter in the primary pressure cohort.

Design principles:
- Uses only is_primary_pressure_cohort == True deliveries.
- Separates IPL and T20I format contexts.
- Distinguishes Top-Order (1-3), Middle-Order (4-6), and Lower-Order (7+) roles.
- Derives component metrics independently; never buries them inside a composite.
- Applies Empirical Bayes shrinkage across the M=[25,45,60,90] sensitivity grid.
- Attaches evidence tier, uncertainty intervals, and rank-stability metadata.
- Never silently replaces NaN with zero for rate metrics.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from src.models.batter_performance import (
    aggregate_batter_segment,
    compute_context_adjusted_batter_metrics,
    compute_player_dismissals,
    prepare_batter_delivery_attributes,
)
from src.models.reliability import (
    classify_evidence_tier,
    compute_batter_match_consistency,
    compute_beta_binomial_credible_interval,
    compute_rate_uncertainty_interval,
    empirical_bayes_shrink,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Qualification thresholds for primary batter ranking eligibility
MIN_PRESSURE_BALLS_QUALIFIED: int = 30
MIN_PRESSURE_MATCHES_QUALIFIED: int = 4

# Shrinkage sensitivity grid (delivery-level pseudo-observations)
SHRINKAGE_M_GRID: List[int] = [25, 45, 60, 90]

# Format-specific population pressure SR priors (calibrated in Phase 2.3.2)
FORMAT_PRIOR_SR: Dict[str, float] = {
    "IPL": 135.3,
    "T20I": 118.0,
    "MIXED": 128.0,
}

# Batting role boundary definitions
BATTING_ROLE_BINS = [0, 3, 6, 20]
BATTING_ROLE_LABELS = ["Top-Order", "Middle-Order", "Lower-Order"]


# ---------------------------------------------------------------------------
# 1. Role Classification
# ---------------------------------------------------------------------------

def classify_batting_role(df: pd.DataFrame) -> pd.DataFrame:
    """Assign a batting role label based on each delivery's batting_order_raw.

    Role boundaries:
    - Top-Order   : positions 1–3
    - Middle-Order: positions 4–6
    - Lower-Order : positions 7+

    The player's most frequent role across all primary-cohort deliveries is
    recorded as the primary role; secondary roles are captured as a set.

    Parameters
    ----------
    df : pd.DataFrame
        Delivery-level primary-cohort DataFrame with striker_id and
        batting_order_raw columns.

    Returns
    -------
    pd.DataFrame
        One row per striker_id with columns:
        [striker_id, primary_batting_role, role_delivery_pct].
    """
    work = df[["striker_id", "batting_order_raw"]].dropna(subset=["batting_order_raw"]).copy()
    work["batting_order_raw"] = work["batting_order_raw"].clip(1, 20)
    work["role"] = pd.cut(
        work["batting_order_raw"],
        bins=BATTING_ROLE_BINS,
        labels=BATTING_ROLE_LABELS,
        right=True,
    ).astype(str)

    role_counts = work.groupby(["striker_id", "role"]).size().rename("count").reset_index()
    total_per_player = role_counts.groupby("striker_id")["count"].sum().rename("total")
    role_counts = role_counts.join(total_per_player, on="striker_id")
    role_counts["pct"] = role_counts["count"] / role_counts["total"]

    # Pick the role with the highest delivery count (modal role)
    idx = role_counts.groupby("striker_id")["count"].idxmax()
    primary_roles = role_counts.loc[idx, ["striker_id", "role", "pct"]].rename(
        columns={"role": "primary_batting_role", "pct": "role_delivery_pct"}
    )
    return primary_roles.reset_index(drop=True)


# ---------------------------------------------------------------------------
# 2. Per-Phase Pressure Metrics
# ---------------------------------------------------------------------------

def compute_phase_pressure_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute pressure-only batting metrics for each innings phase.

    Returns one row per (striker_id, innings_phase) with aggregated
    pressure balls, runs, SR, boundary%, and dot-ball%.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared delivery DataFrame (after prepare_batter_delivery_attributes).

    Returns
    -------
    pd.DataFrame
        Multi-row table indexed by (striker_id, innings_phase).
    """
    pressure_df = df[df["is_pressure"]].copy()
    if pressure_df.empty:
        return pd.DataFrame()

    grp = pressure_df.groupby(["striker_id", "innings_phase"])
    agg = pd.DataFrame(
        {
            "phase_pressure_balls": grp["is_ball_faced"].sum(),
            "phase_pressure_runs": grp["batter_runs"].sum(),
            "phase_pressure_boundaries": grp["is_boundary"].sum(),
            "phase_pressure_dots": grp["is_dot_ball"].sum(),
        }
    ).reset_index()

    agg["phase_pressure_sr"] = np.where(
        agg["phase_pressure_balls"] > 0,
        agg["phase_pressure_runs"] * 100.0 / agg["phase_pressure_balls"],
        np.nan,
    )
    agg["phase_pressure_boundary_pct"] = np.where(
        agg["phase_pressure_balls"] > 0,
        agg["phase_pressure_boundaries"] * 100.0 / agg["phase_pressure_balls"],
        np.nan,
    )
    agg["phase_pressure_dot_pct"] = np.where(
        agg["phase_pressure_balls"] > 0,
        agg["phase_pressure_dots"] * 100.0 / agg["phase_pressure_balls"],
        np.nan,
    )
    return agg


# ---------------------------------------------------------------------------
# 3. Pressure-Tier Breakdown (HIGH vs EXTREME)
# ---------------------------------------------------------------------------

def compute_pressure_tier_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Compute separate metrics for HIGH and EXTREME batter pressure tiers.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared delivery DataFrame.

    Returns
    -------
    pd.DataFrame
        One row per (striker_id, batter_pressure_tier) for HIGH and EXTREME.
    """
    tier_df = df[df["batter_pressure_tier"].isin(["HIGH", "EXTREME"])].copy()
    if tier_df.empty:
        return pd.DataFrame()

    grp = tier_df.groupby(["striker_id", "batter_pressure_tier"])
    agg = pd.DataFrame(
        {
            "tier_balls": grp["is_ball_faced"].sum(),
            "tier_runs": grp["batter_runs"].sum(),
        }
    ).reset_index()

    agg["tier_sr"] = np.where(
        agg["tier_balls"] > 0,
        agg["tier_runs"] * 100.0 / agg["tier_balls"],
        np.nan,
    )
    return agg


# ---------------------------------------------------------------------------
# 4. Resource-Situation Pressure Metrics (wickets & balls remaining)
# ---------------------------------------------------------------------------

def compute_resource_situation_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute pressure SR when batting resources are critically constrained.

    Segments:
    - Tail anchor   : wickets_remaining_before <= 3 AND is_pressure
    - Final crunch  : balls_remaining_before <= 12 AND is_pressure
    - Combined panic: both simultaneously

    Parameters
    ----------
    df : pd.DataFrame
        Prepared delivery DataFrame.

    Returns
    -------
    pd.DataFrame
        One row per striker_id with tail_anchor, final_crunch, and
        combined_panic pressure metrics.
    """
    pressure = df[df["is_pressure"]].copy()
    if pressure.empty:
        return pd.DataFrame()

    def _agg_segment(segment: pd.DataFrame, prefix: str) -> pd.DataFrame:
        """Aggregate a pressure sub-segment into summary columns."""
        if segment.empty:
            return pd.DataFrame(columns=["striker_id", f"{prefix}balls", f"{prefix}runs", f"{prefix}sr"])
        g = segment.groupby("striker_id")
        out = pd.DataFrame(
            {
                f"{prefix}balls": g["is_ball_faced"].sum(),
                f"{prefix}runs": g["batter_runs"].sum(),
            }
        ).reset_index()
        out[f"{prefix}sr"] = np.where(
            out[f"{prefix}balls"] > 0,
            out[f"{prefix}runs"] * 100.0 / out[f"{prefix}balls"],
            np.nan,
        )
        return out

    tail = pressure[pressure["batter_wickets_remaining"] <= 3]
    crunch = pressure[pressure["batter_legal_balls_remaining"] <= 12]
    panic = tail[tail["batter_legal_balls_remaining"] <= 12]

    tail_df = _agg_segment(tail, "tail_anchor_")
    crunch_df = _agg_segment(crunch, "final_crunch_")
    panic_df = _agg_segment(panic, "combined_panic_")

    # Merge all three segments
    merged = tail_df.merge(crunch_df, on="striker_id", how="outer")
    merged = merged.merge(panic_df, on="striker_id", how="outer")
    return merged


# ---------------------------------------------------------------------------
# 5. Shrinkage Sensitivity Grid
# ---------------------------------------------------------------------------

def apply_batter_shrinkage_grid(
    profile_df: pd.DataFrame,
    format_col: str = "primary_format",
) -> pd.DataFrame:
    """Apply Empirical Bayes shrinkage across M=[25,45,60,90] for pressure SR.

    Uses format-specific prior means where the player has a dominant format.
    Falls back to MIXED prior when both IPL and T20I are present.

    Parameters
    ----------
    profile_df : pd.DataFrame
        Batter profile table containing pressure_balls_faced and
        pressure_strike_rate columns.
    format_col : str
        Column indicating the player's primary format ('IPL', 'T20I', 'MIXED').

    Returns
    -------
    pd.DataFrame
        Input DataFrame with shrunk_pressure_sr_m{M} columns appended.
    """
    df_out = profile_df.copy()

    for m in SHRINKAGE_M_GRID:
        col_name = f"shrunk_pressure_sr_m{m}"

        def _shrink_row(row: pd.Series) -> float:
            prior = FORMAT_PRIOR_SR.get(str(row.get(format_col, "MIXED")), FORMAT_PRIOR_SR["MIXED"])
            return empirical_bayes_shrink(
                observed_metric=row["pressure_strike_rate"],
                sample_size=int(row["pressure_balls_faced"]),
                prior_mean=prior,
                prior_weight=float(m),
            )

        df_out[col_name] = df_out.apply(_shrink_row, axis=1)

    return df_out


# ---------------------------------------------------------------------------
# 6. Rank Stability Analysis
# ---------------------------------------------------------------------------

def compute_batter_rank_stability(
    profile_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute ranking under each M value and measure position volatility.

    For each batter, records rank under M=25, 45, 60, 90, and reports:
    - rank_min, rank_max: best and worst position across the grid.
    - rank_range: max - min (smaller = more stable).
    - rank_std: standard deviation of positions across M values.
    - rank_m25 (the talent-preserving anchor).

    Parameters
    ----------
    profile_df : pd.DataFrame
        Batter profile including shrunk_pressure_sr_m{M} columns.

    Returns
    -------
    pd.DataFrame
        One row per striker_id with rank stability metrics.
    """
    if profile_df is None or profile_df.empty:
        return pd.DataFrame()
    id_col = "striker_id"
    name_col = "striker_name"

    stability_cols = {}
    rank_cols = []
    for m in SHRINKAGE_M_GRID:
        rc = f"rank_m{m}"
        shrunk_col = f"shrunk_pressure_sr_m{m}"
        if shrunk_col in profile_df.columns:
            profile_df[rc] = profile_df[shrunk_col].rank(ascending=False, method="min", na_option="bottom")
            stability_cols[rc] = profile_df[rc]
            rank_cols.append(rc)

    if not rank_cols:
        return pd.DataFrame()

    rank_matrix = profile_df[rank_cols]
    out = profile_df[[id_col, name_col]].copy()
    out["rank_m25"] = profile_df.get("rank_m25", np.nan)
    out["rank_min"] = rank_matrix.min(axis=1)
    out["rank_max"] = rank_matrix.max(axis=1)
    out["rank_range"] = out["rank_max"] - out["rank_min"]
    out["rank_std"] = rank_matrix.std(axis=1, ddof=1).round(2)
    out["rank_stable"] = out["rank_range"] <= 5

    for rc in rank_cols:
        out[rc] = profile_df[rc]

    return out.sort_values("rank_m25", ascending=True).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 7. Format Detection
# ---------------------------------------------------------------------------

def detect_primary_format(df: pd.DataFrame) -> pd.DataFrame:
    """Identify each batter's primary format by pressure ball volume.

    Returns 'IPL', 'T20I', or 'MIXED' (when neither exceeds 60% of total).

    Parameters
    ----------
    df : pd.DataFrame
        Delivery-level DataFrame with striker_id, competition_type,
        is_ball_faced, and is_pressure columns.

    Returns
    -------
    pd.DataFrame
        One row per striker_id with primary_format and format coverage pcts.
    """
    pressure = df[df["is_pressure"] & df["is_ball_faced"]].copy()
    if pressure.empty:
        return pd.DataFrame(columns=["striker_id", "primary_format"])

    fmt_counts = (
        pressure.groupby(["striker_id", "competition_type"])
        .size()
        .rename("fmt_balls")
        .reset_index()
    )
    total = fmt_counts.groupby("striker_id")["fmt_balls"].sum().rename("total_balls")
    fmt_counts = fmt_counts.join(total, on="striker_id")
    fmt_counts["fmt_pct"] = fmt_counts["fmt_balls"] / fmt_counts["total_balls"]

    records = []
    for sid, grp in fmt_counts.groupby("striker_id"):
        ipl_pct = float(grp.loc[grp["competition_type"] == "IPL", "fmt_pct"].sum())
        t20i_pct = float(grp.loc[grp["competition_type"] == "T20I", "fmt_pct"].sum())
        if ipl_pct >= 0.60:
            primary_format = "IPL"
        elif t20i_pct >= 0.60:
            primary_format = "T20I"
        else:
            primary_format = "MIXED"
        records.append(
            {
                "striker_id": sid,
                "primary_format": primary_format,
                "ipl_pressure_pct": round(ipl_pct * 100, 1),
                "t20i_pressure_pct": round(t20i_pct * 100, 1),
            }
        )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 8. Main Evaluation Builder
# ---------------------------------------------------------------------------

def build_batter_evaluation(
    df: pd.DataFrame,
    min_pressure_balls: int = MIN_PRESSURE_BALLS_QUALIFIED,
    min_pressure_matches: int = MIN_PRESSURE_MATCHES_QUALIFIED,
    competition_type: Optional[str] = None,
) -> Dict[str, pd.DataFrame]:
    """Build the complete batter evaluation dataset.

    Steps:
    1.  Filter to primary cohort (and optionally format: 'IPL' or 'T20I').
    2.  Prepare delivery attributes.
    3.  Build overall pressure + normal profile.
    4.  Assign batting role.
    5.  Detect primary format.
    6.  Compute RAE context-adjusted delta SR.
    7.  Compute phase-level pressure metrics.
    8.  Compute pressure-tier breakdown (HIGH/EXTREME).
    9.  Compute resource-situation metrics.
    10. Compute match consistency.
    11. Attach evidence tier.
    12. Attach uncertainty intervals.
    13. Apply shrinkage sensitivity grid (M=25,45,60,90).
    14. Flag qualified candidates.
    15. Compute rank stability.

    Parameters
    ----------
    df : pd.DataFrame
        Full pressure deliveries dataset (may contain is_primary_pressure_cohort).
    min_pressure_balls : int
        Minimum pressure balls faced for ranking eligibility.
    min_pressure_matches : int
        Minimum distinct pressure matches for ranking eligibility.
    competition_type : str, optional
        Filter to specific format ('IPL' or 'T20I'), or None for all formats.

    Returns
    -------
    Dict[str, pd.DataFrame]
        'evaluation'    : Full batter evaluation table (all players).
        'qualified'     : Subset meeting minimum qualification thresholds.
        'phase_metrics' : Per-player per-phase pressure summary.
        'tier_metrics'  : Per-player HIGH/EXTREME tier breakdown.
        'resource_metrics': Per-player resource-situation pressure metrics.
        'rank_stability': Rank stability table across M grid.
        'rae_metrics'   : Context-adjusted RAE output from Phase 2.3.
    """
    # --- Step 1: Primary cohort ---
    primary = df[df["is_primary_pressure_cohort"]].copy()
    if competition_type is not None:
        primary = primary[primary["competition_type"] == competition_type].copy()

    # --- Step 2: Prepare attributes ---
    prepared = prepare_batter_delivery_attributes(primary)

    # --- Step 3: Overall profile ---
    pressure_del = prepared[prepared["is_pressure"]]
    normal_del = prepared[prepared["is_normal"]]

    overall = aggregate_batter_segment(prepared, prefix="")
    pressure_agg = aggregate_batter_segment(pressure_del, prefix="pressure_")
    normal_agg = aggregate_batter_segment(normal_del, prefix="normal_")

    # Guard: only merge non-empty segments (empty DF has no columns including 'striker_id')
    pressure_agg_safe = pressure_agg.drop(columns=["striker_name"], errors="ignore")
    normal_agg_safe = normal_agg.drop(columns=["striker_name"], errors="ignore")

    profile = overall
    if not pressure_agg_safe.empty and "striker_id" in pressure_agg_safe.columns:
        profile = profile.merge(pressure_agg_safe, on="striker_id", how="left")
    if not normal_agg_safe.empty and "striker_id" in normal_agg_safe.columns:
        profile = profile.merge(normal_agg_safe, on="striker_id", how="left")

    # Fill count columns with 0 (never rate columns)
    _count_cols = [
        "pressure_balls_faced", "pressure_runs", "pressure_fours", "pressure_sixes",
        "pressure_boundary_balls", "pressure_boundary_runs", "pressure_dot_balls",
        "pressure_matches", "pressure_competitions", "pressure_dismissals",
        "normal_balls_faced", "normal_runs", "normal_fours", "normal_sixes",
        "normal_boundary_balls", "normal_boundary_runs", "normal_dot_balls",
        "normal_matches", "normal_competitions", "normal_dismissals",
    ]
    for c in _count_cols:
        if c not in profile.columns:
            profile[c] = 0
        else:
            profile[c] = profile[c].fillna(0).astype(int)

    # Ensure rate columns exist (initialize to NaN if player cohort has zero exposure in that segment)
    _rate_cols = [
        "pressure_strike_rate", "pressure_boundary_runs_pct", "pressure_boundary_ball_pct",
        "pressure_dot_ball_pct", "pressure_dismissal_rate", "pressure_runs_per_dismissal",
        "normal_strike_rate", "normal_boundary_runs_pct", "normal_boundary_ball_pct",
        "normal_dot_ball_pct", "normal_dismissal_rate", "normal_runs_per_dismissal",
    ]
    for c in _rate_cols:
        if c not in profile.columns:
            profile[c] = np.nan

    # Delta metrics
    profile["delta_strike_rate"] = profile["pressure_strike_rate"] - profile["normal_strike_rate"]
    profile["delta_boundary_ball_pct"] = (
        profile["pressure_boundary_ball_pct"] - profile["normal_boundary_ball_pct"]
    )
    profile["delta_dot_ball_pct"] = (
        profile["pressure_dot_ball_pct"] - profile["normal_dot_ball_pct"]
    )

    # --- Step 4: Batting role ---
    roles = classify_batting_role(primary)
    profile = profile.merge(roles, on="striker_id", how="left")

    # --- Step 5: Primary format ---
    fmt = detect_primary_format(prepared)
    profile = profile.merge(fmt, on="striker_id", how="left")

    # --- Step 6: Context-adjusted RAE (reuse Phase 2.3 function) ---
    rae_df = compute_context_adjusted_batter_metrics(primary, filter_primary_cohort=False, min_balls=20)

    # --- Step 7: Phase metrics ---
    phase_metrics = compute_phase_pressure_metrics(prepared)

    # --- Step 8: Pressure tier breakdown ---
    tier_metrics = compute_pressure_tier_breakdown(prepared)

    # --- Step 9: Resource-situation metrics ---
    resource_metrics = compute_resource_situation_metrics(prepared)
    if not resource_metrics.empty and "striker_id" in resource_metrics.columns:
        profile = profile.merge(resource_metrics, on="striker_id", how="left")

    # --- Step 10: Match consistency ---
    pressure_deliveries_for_consistency = pressure_del.copy()
    pressure_deliveries_for_consistency["is_ball_faced"] = (
        pressure_deliveries_for_consistency["extras_type"] != "wide"
    )
    pressure_deliveries_for_consistency["batter_runs"] = (
        pressure_deliveries_for_consistency["runs"].astype(int)
    )
    consistency = compute_batter_match_consistency(pressure_deliveries_for_consistency)
    if not consistency.empty and "striker_id" in consistency.columns:
        profile = profile.merge(
            consistency.drop(columns=["striker_name"], errors="ignore"),
            on="striker_id",
            how="left",
        )

    # --- Step 11: Evidence tier ---
    def _evidence(row: pd.Series) -> pd.Series:
        tier_info = classify_evidence_tier(
            sample_size=int(row.get("pressure_balls_faced", 0)),
            distinct_matches=int(row.get("pressure_matches", 0)),
            distinct_competitions=int(row.get("pressure_competitions", 0)),
        )
        return pd.Series(
            {
                "evidence_tier": tier_info["evidence_tier"],
                "is_reliable_sample": tier_info["is_reliable"],
            }
        )

    evidence_cols = profile.apply(_evidence, axis=1)
    profile = pd.concat([profile, evidence_cols], axis=1)

    # --- Step 12: Uncertainty intervals ---
    def _ci_row(row: pd.Series) -> pd.Series:
        n = int(row.get("pressure_balls_faced", 0))
        sr = row.get("pressure_strike_rate", np.nan)
        fmt = str(row.get("primary_format", "MIXED"))
        prior_mean = FORMAT_PRIOR_SR.get(fmt, FORMAT_PRIOR_SR["MIXED"])

        shrunk, ci_lo, ci_hi = compute_rate_uncertainty_interval(
            observed_rate=float(sr) if not pd.isna(sr) else np.nan,
            sample_size=n,
            prior_mean=prior_mean,
            prior_weight=30.0,
            population_std=25.0,
        )
        # Beta-binomial for dot ball %
        dots = int(row.get("pressure_dot_balls", 0))
        dot_post, dot_lo, dot_hi = compute_beta_binomial_credible_interval(
            successes=dots,
            trials=n,
            prior_alpha=2.0,
            prior_beta=5.0,
        )
        return pd.Series(
            {
                "pressure_sr_ci_lower_95": round(ci_lo, 1),
                "pressure_sr_ci_upper_95": round(ci_hi, 1),
                "pressure_dot_pct_posterior": round(dot_post, 1),
                "pressure_dot_pct_ci_lower_95": round(dot_lo, 1),
                "pressure_dot_pct_ci_upper_95": round(dot_hi, 1),
            }
        )

    ci_cols = profile.apply(_ci_row, axis=1)
    profile = pd.concat([profile, ci_cols], axis=1)

    # --- Step 13: Shrinkage grid ---
    profile = apply_batter_shrinkage_grid(profile, format_col="primary_format")

    # Merge RAE onto main profile
    if not rae_df.empty:
        rae_subset = rae_df[
            ["striker_id", "context_adjusted_delta_sr", "observed_pressure_sr", "expected_pressure_sr"]
        ]
        profile = profile.merge(rae_subset, on="striker_id", how="left")

    # --- Step 14: Qualification flag ---
    profile["meets_minimum_qualification"] = (
        (profile["pressure_balls_faced"] >= min_pressure_balls)
        & (profile["pressure_matches"] >= min_pressure_matches)
    )

    # --- Step 15: Ordering (by pressure exposure for readability) ---
    profile = profile.sort_values("pressure_balls_faced", ascending=False).reset_index(drop=True)

    # --- Rank stability (qualified players only) ---
    qualified = profile[profile["meets_minimum_qualification"]].copy()
    if qualified.empty:
        rank_stability = pd.DataFrame()
    else:
        rank_stability = compute_batter_rank_stability(qualified)

    return {
        "evaluation": profile,
        "qualified": qualified,
        "phase_metrics": phase_metrics,
        "tier_metrics": tier_metrics,
        "resource_metrics": resource_metrics,
        "rank_stability": rank_stability,
        "rae_metrics": rae_df,
    }


# ---------------------------------------------------------------------------
# 9. Role-Specific Summaries
# ---------------------------------------------------------------------------

def build_batter_role_summaries(evaluation_df: pd.DataFrame) -> pd.DataFrame:
    """Compute aggregated pressure performance summary by batting role.

    Parameters
    ----------
    evaluation_df : pd.DataFrame
        Qualified batter evaluation table with primary_batting_role.

    Returns
    -------
    pd.DataFrame
        One row per batting role with median and IQR for key pressure metrics.
    """
    key_metrics = [
        "pressure_balls_faced",
        "pressure_strike_rate",
        "context_adjusted_delta_sr",
        "pressure_boundary_ball_pct",
        "pressure_dot_ball_pct",
        "pressure_match_pass_rate",
        "shrunk_pressure_sr_m45",
    ]

    available = [c for c in key_metrics if c in evaluation_df.columns]
    records = []
    for role, grp in evaluation_df.groupby("primary_batting_role", observed=True):
        row = {"primary_batting_role": role, "player_count": len(grp)}
        for col in available:
            vals = grp[col].dropna()
            row[f"{col}_median"] = round(float(vals.median()), 2) if len(vals) > 0 else np.nan
            row[f"{col}_p25"] = round(float(vals.quantile(0.25)), 2) if len(vals) > 0 else np.nan
            row[f"{col}_p75"] = round(float(vals.quantile(0.75)), 2) if len(vals) > 0 else np.nan
        records.append(row)
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 10. Qualification Sensitivity Analysis
# ---------------------------------------------------------------------------

def build_batter_qualification_sensitivity(eval_df: pd.DataFrame) -> pd.DataFrame:
    """Evaluate batter candidate qualification under three sensitivity configurations.

    Threshold configurations:
    1. Broad / Discovery : >= 30 pressure balls AND >= 4 distinct matches
    2. Balanced          : >= 60 pressure balls AND >= 6 distinct matches
    3. Strict / High     : >= 100 pressure balls AND >= 8 distinct matches

    Parameters
    ----------
    eval_df : pd.DataFrame
        Batter evaluation table.

    Returns
    -------
    pd.DataFrame
        Qualified candidates tagged with qualification cohorts and rank sensitivity.
    """
    df = eval_df.copy()
    df["qual_broad_30b_4m"] = (df["pressure_balls_faced"] >= 30) & (df["pressure_matches"] >= 4)
    df["qual_balanced_60b_6m"] = (df["pressure_balls_faced"] >= 60) & (df["pressure_matches"] >= 6)
    df["qual_strict_100b_8m"] = (df["pressure_balls_faced"] >= 100) & (df["pressure_matches"] >= 8)

    def _tier(row: pd.Series) -> str:
        if row["qual_strict_100b_8m"]:
            return "Strict (>=100b, >=8m)"
        elif row["qual_balanced_60b_6m"]:
            return "Balanced (>=60b, >=6m)"
        elif row["qual_broad_30b_4m"]:
            return "Discovery (>=30b, >=4m)"
        else:
            return "Unqualified (<30b or <4m)"

    df["qualification_cohort"] = df.apply(_tier, axis=1)

    qual = df[df["qual_broad_30b_4m"]].copy()
    cols = [
        "striker_id", "striker_name", "primary_batting_role", "primary_format",
        "pressure_balls_faced", "pressure_matches", "pressure_competitions",
        "evidence_tier", "qualification_cohort", "qual_broad_30b_4m",
        "qual_balanced_60b_6m", "qual_strict_100b_8m",
        "pressure_strike_rate", "shrunk_pressure_sr_m25", "shrunk_pressure_sr_m45",
        "shrunk_pressure_sr_m60", "shrunk_pressure_sr_m90",
        "context_adjusted_delta_sr", "pressure_match_pass_rate"
    ]
    available = [c for c in cols if c in qual.columns]
    return qual[available].sort_values("shrunk_pressure_sr_m25", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 11. Persistence Helper
# ---------------------------------------------------------------------------

def save_batter_evaluation(
    result: Dict[str, pd.DataFrame],
    output_dir: Path,
) -> None:
    """Persist all batter evaluation tables to Parquet and CSV.

    Parameters
    ----------
    result : Dict[str, pd.DataFrame]
        Output of build_batter_evaluation().
    output_dir : Path
        Directory where files are written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    file_map = {
        "batter_evaluation": result["evaluation"],
        "batter_qualified": result["qualified"],
        "batter_phase_metrics": result["phase_metrics"],
        "batter_tier_metrics": result["tier_metrics"],
        "batter_resource_metrics": result["resource_metrics"],
        "batter_rank_stability": result["rank_stability"],
        "batter_rae_metrics": result["rae_metrics"],
    }

    # Role summaries and sensitivity derived from evaluation
    if not result["qualified"].empty:
        role_summary = build_batter_role_summaries(result["qualified"])
        file_map["batter_role_summaries"] = role_summary
        qual_sens = build_batter_qualification_sensitivity(result["evaluation"])
        file_map["batter_qualification_sensitivity"] = qual_sens

    for name, table in file_map.items():
        if table is None or table.empty:
            continue
        parquet_path = output_dir / f"{name}.parquet"
        csv_path = output_dir / f"{name}.csv"
        table.to_parquet(parquet_path, index=False)
        table.to_csv(csv_path, index=False)
