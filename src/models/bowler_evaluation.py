"""
Bowler Evaluation Engine for RR EDGE — Phase 3.

Builds an explainable, role-aware, evidence-weighted bowler evaluation that
produces a full component profile and sensitivity-tested ranking for every
qualified bowler in the primary pressure cohort.

Design principles:
- Uses only is_primary_pressure_cohort == True deliveries.
- Separates IPL and T20I format contexts.
- Distinguishes Powerplay, Middle-Over, and Death-Over specialist roles.
- Derives component metrics independently; never buries them inside a composite.
- Applies Empirical Bayes shrinkage across the M=[25,45,60,90] sensitivity grid.
- Attaches evidence tier, uncertainty intervals, and rank-stability metadata.
- Rewards wickets only when conceded runs and exposure are both considered.
- Never silently replaces NaN with zero for rate metrics.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from src.models.bowler_performance import (
    aggregate_bowler_segment,
    compute_context_adjusted_bowler_metrics,
    prepare_bowler_delivery_attributes,
)
from src.models.reliability import (
    classify_evidence_tier,
    compute_bowler_match_consistency,
    compute_beta_binomial_credible_interval,
    compute_rate_uncertainty_interval,
    empirical_bayes_shrink,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Qualification thresholds for primary bowler ranking eligibility
MIN_PRESSURE_BALLS_QUALIFIED: int = 30
MIN_PRESSURE_MATCHES_QUALIFIED: int = 4

# Shrinkage sensitivity grid (delivery-level pseudo-observations)
SHRINKAGE_M_GRID: List[int] = [25, 45, 60, 90]

# Format-specific population pressure economy priors (Phase 2.3.2 calibration)
FORMAT_PRIOR_ECON: Dict[str, float] = {
    "IPL": 11.4,
    "T20I": 10.2,
    "MIXED": 10.8,
}

# Bowling phase role threshold fractions
PHASE_SPECIALIST_THRESHOLD: float = 0.55  # fraction of pressure balls in a single phase


# ---------------------------------------------------------------------------
# 1. Bowling Role Classification (Phase Specialist)
# ---------------------------------------------------------------------------

def classify_bowling_role(df: pd.DataFrame) -> pd.DataFrame:
    """Assign a bowling role based on where the bowler bowls under pressure.

    Uses bowler_innings_phase (which mirrors innings_phase) to determine
    the phase where the bowler has greatest pressure-ball exposure.

    Roles:
    - Powerplay Specialist : >= PHASE_SPECIALIST_THRESHOLD of pressure balls in Powerplay.
    - Death Specialist     : >= PHASE_SPECIALIST_THRESHOLD of pressure balls in Death.
    - Middle Specialist    : >= PHASE_SPECIALIST_THRESHOLD in Middle.
    - All-Phases           : No single phase dominates.

    Parameters
    ----------
    df : pd.DataFrame
        Delivery-level primary-cohort DataFrame with bowler_id and
        bowler_innings_phase.

    Returns
    -------
    pd.DataFrame
        One row per bowler_id with columns:
        [bowler_id, primary_bowling_role, role_phase_pct,
         powerplay_pct, middle_pct, death_pct].
    """
    legal = df[df["is_legal_bowler_ball"]].copy()
    if legal.empty:
        return pd.DataFrame()

    phase_counts = (
        legal.groupby(["bowler_id", "bowler_innings_phase"])
        .size()
        .rename("count")
        .reset_index()
    )
    total = phase_counts.groupby("bowler_id")["count"].sum().rename("total")
    phase_counts = phase_counts.join(total, on="bowler_id")
    phase_counts["pct"] = phase_counts["count"] / phase_counts["total"]

    records = []
    for bid, grp in phase_counts.groupby("bowler_id"):
        pct_map = grp.set_index("bowler_innings_phase")["pct"].to_dict()
        pp_pct = pct_map.get("Powerplay", 0.0)
        md_pct = pct_map.get("Middle", 0.0)
        dt_pct = pct_map.get("Death", 0.0)

        if dt_pct >= PHASE_SPECIALIST_THRESHOLD:
            role = "Death Specialist"
            role_pct = dt_pct
        elif pp_pct >= PHASE_SPECIALIST_THRESHOLD:
            role = "Powerplay Specialist"
            role_pct = pp_pct
        elif md_pct >= PHASE_SPECIALIST_THRESHOLD:
            role = "Middle Specialist"
            role_pct = md_pct
        else:
            role = "All-Phases"
            role_pct = max(pp_pct, md_pct, dt_pct)

        records.append(
            {
                "bowler_id": bid,
                "primary_bowling_role": role,
                "role_phase_pct": round(role_pct * 100, 1),
                "powerplay_pct": round(pp_pct * 100, 1),
                "middle_pct": round(md_pct * 100, 1),
                "death_pct": round(dt_pct * 100, 1),
            }
        )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 2. Per-Phase Pressure Metrics
# ---------------------------------------------------------------------------

def compute_phase_pressure_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute pressure-only bowling metrics per innings phase.

    Returns one row per (bowler_id, bowler_innings_phase) with aggregated
    pressure legal balls, runs conceded, economy, wickets, and dot-ball%.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared delivery DataFrame (after prepare_bowler_delivery_attributes).

    Returns
    -------
    pd.DataFrame
        Multi-row table indexed by (bowler_id, bowler_innings_phase).
    """
    pressure_df = df[df["is_bowler_pressure"]].copy()
    if pressure_df.empty:
        return pd.DataFrame()

    legal_pressure = pressure_df[pressure_df["is_legal_bowler_ball"]]
    grp = legal_pressure.groupby(["bowler_id", "bowler_innings_phase"])

    agg = pd.DataFrame(
        {
            "phase_pressure_balls": grp["is_legal_bowler_ball"].sum(),
            "phase_pressure_runs": grp["bowler_runs_conceded"].sum(),
            "phase_pressure_wickets": grp["bowler_wicket_credit"].sum(),
            "phase_pressure_dots": grp["is_bowler_dot"].sum(),
            "phase_pressure_boundaries": grp["is_boundary_conceded"].sum(),
        }
    ).reset_index()

    agg["phase_pressure_economy"] = np.where(
        agg["phase_pressure_balls"] > 0,
        agg["phase_pressure_runs"] * 6.0 / agg["phase_pressure_balls"],
        np.nan,
    )
    agg["phase_pressure_dot_pct"] = np.where(
        agg["phase_pressure_balls"] > 0,
        agg["phase_pressure_dots"] * 100.0 / agg["phase_pressure_balls"],
        np.nan,
    )
    agg["phase_pressure_boundary_pct"] = np.where(
        agg["phase_pressure_balls"] > 0,
        agg["phase_pressure_boundaries"] * 100.0 / agg["phase_pressure_balls"],
        np.nan,
    )
    return agg


# ---------------------------------------------------------------------------
# 3. Pressure-Tier Breakdown (HIGH vs EXTREME)
# ---------------------------------------------------------------------------

def compute_pressure_tier_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Compute separate metrics for HIGH and EXTREME bowler pressure tiers.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared delivery DataFrame.

    Returns
    -------
    pd.DataFrame
        One row per (bowler_id, bowler_pressure_tier) for HIGH and EXTREME.
    """
    tier_df = df[
        df["bowler_pressure_tier"].isin(["HIGH", "EXTREME"])
        & df["is_legal_bowler_ball"]
    ].copy()
    if tier_df.empty:
        return pd.DataFrame()

    grp = tier_df.groupby(["bowler_id", "bowler_pressure_tier"])
    agg = pd.DataFrame(
        {
            "tier_legal_balls": grp["is_legal_bowler_ball"].sum(),
            "tier_runs": grp["bowler_runs_conceded"].sum(),
            "tier_wickets": grp["bowler_wicket_credit"].sum(),
        }
    ).reset_index()

    agg["tier_economy"] = np.where(
        agg["tier_legal_balls"] > 0,
        agg["tier_runs"] * 6.0 / agg["tier_legal_balls"],
        np.nan,
    )
    return agg


# ---------------------------------------------------------------------------
# 4. Batting-Resource Situation Metrics
# ---------------------------------------------------------------------------

def compute_resource_situation_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute pressure economy when batting resources are abundant vs scarce.

    Segments (all within is_bowler_pressure deliveries on legal balls):
    - Against top-order  : bowler_wickets_remaining >= 7 (batting team comfortable)
    - Against tail        : bowler_wickets_remaining <= 3 (batting team scrambling)
    - Chase crunch        : bowler_legal_balls_remaining <= 12 AND high scoring rate needed

    Parameters
    ----------
    df : pd.DataFrame
        Prepared delivery DataFrame.

    Returns
    -------
    pd.DataFrame
        One row per bowler_id with resource-situation economy metrics.
    """
    pressure_legal = df[df["is_bowler_pressure"] & df["is_legal_bowler_ball"]].copy()
    if pressure_legal.empty:
        return pd.DataFrame()

    def _agg_segment(segment: pd.DataFrame, prefix: str) -> pd.DataFrame:
        """Aggregate a segment of legal deliveries into economy summary."""
        if segment.empty:
            return pd.DataFrame(
                columns=["bowler_id", f"{prefix}balls", f"{prefix}runs", f"{prefix}economy"]
            )
        g = segment.groupby("bowler_id")
        out = pd.DataFrame(
            {
                f"{prefix}balls": g["is_legal_bowler_ball"].sum(),
                f"{prefix}runs": g["bowler_runs_conceded"].sum(),
                f"{prefix}wickets": g["bowler_wicket_credit"].sum(),
            }
        ).reset_index()
        out[f"{prefix}economy"] = np.where(
            out[f"{prefix}balls"] > 0,
            out[f"{prefix}runs"] * 6.0 / out[f"{prefix}balls"],
            np.nan,
        )
        return out

    top_order = pressure_legal[pressure_legal["bowler_wickets_remaining"] >= 7]
    tail = pressure_legal[pressure_legal["bowler_wickets_remaining"] <= 3]
    crunch = pressure_legal[pressure_legal["bowler_legal_balls_remaining"] <= 12]

    top_df = _agg_segment(top_order, "vs_top_order_")
    tail_df = _agg_segment(tail, "vs_tail_")
    crunch_df = _agg_segment(crunch, "chase_crunch_")

    merged = top_df.merge(tail_df, on="bowler_id", how="outer")
    merged = merged.merge(crunch_df, on="bowler_id", how="outer")
    return merged


# ---------------------------------------------------------------------------
# 5. Wicket Impact Metric
# ---------------------------------------------------------------------------

def compute_wicket_impact(df: pd.DataFrame) -> pd.DataFrame:
    """Compute wicket impact combining wicket rate with run-cost efficiency.

    Wicket Impact Score = (pressure_wickets / pressure_overs) - (pressure_economy / 10)
    This rewards taking wickets frequently but penalises high run concession.

    The formula is intentionally simple and transparent; it is one input
    component, not a final score.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared delivery DataFrame.

    Returns
    -------
    pd.DataFrame
        One row per bowler_id with wickets_per_over, wicket_impact_score.
    """
    pressure_legal = df[df["is_bowler_pressure"] & df["is_legal_bowler_ball"]].copy()
    if pressure_legal.empty:
        return pd.DataFrame()

    grp = pressure_legal.groupby("bowler_id")
    out = pd.DataFrame(
        {
            "pressure_legal_balls": grp["is_legal_bowler_ball"].sum(),
            "pressure_runs": grp["bowler_runs_conceded"].sum(),
            "pressure_wickets": grp["bowler_wicket_credit"].sum(),
        }
    ).reset_index()

    out["pressure_overs"] = out["pressure_legal_balls"] / 6.0
    out["wickets_per_over"] = np.where(
        out["pressure_overs"] > 0,
        out["pressure_wickets"] / out["pressure_overs"],
        np.nan,
    )
    out["pressure_economy"] = np.where(
        out["pressure_legal_balls"] > 0,
        out["pressure_runs"] * 6.0 / out["pressure_legal_balls"],
        np.nan,
    )
    out["wicket_impact_score"] = (
        out["wickets_per_over"] - out["pressure_economy"] / 10.0
    )
    return out[["bowler_id", "wickets_per_over", "wicket_impact_score"]]


# ---------------------------------------------------------------------------
# 6. Format Detection
# ---------------------------------------------------------------------------

def detect_primary_format(df: pd.DataFrame) -> pd.DataFrame:
    """Identify each bowler's primary format by pressure ball volume.

    Returns 'IPL', 'T20I', or 'MIXED' (when neither exceeds 60%).

    Parameters
    ----------
    df : pd.DataFrame
        Delivery-level DataFrame with bowler_id, competition_type,
        is_legal_bowler_ball, is_bowler_pressure.

    Returns
    -------
    pd.DataFrame
        One row per bowler_id with primary_format and format coverage pcts.
    """
    pressure_legal = df[df["is_bowler_pressure"] & df["is_legal_bowler_ball"]].copy()
    if pressure_legal.empty:
        return pd.DataFrame(columns=["bowler_id", "primary_format"])

    fmt_counts = (
        pressure_legal.groupby(["bowler_id", "competition_type"])
        .size()
        .rename("fmt_balls")
        .reset_index()
    )
    total = fmt_counts.groupby("bowler_id")["fmt_balls"].sum().rename("total_balls")
    fmt_counts = fmt_counts.join(total, on="bowler_id")
    fmt_counts["fmt_pct"] = fmt_counts["fmt_balls"] / fmt_counts["total_balls"]

    records = []
    for bid, grp in fmt_counts.groupby("bowler_id"):
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
                "bowler_id": bid,
                "primary_format": primary_format,
                "ipl_pressure_pct": round(ipl_pct * 100, 1),
                "t20i_pressure_pct": round(t20i_pct * 100, 1),
            }
        )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 7. Shrinkage Sensitivity Grid
# ---------------------------------------------------------------------------

def apply_bowler_shrinkage_grid(
    profile_df: pd.DataFrame,
    format_col: str = "primary_format",
) -> pd.DataFrame:
    """Apply Empirical Bayes shrinkage across M=[25,45,60,90] for pressure economy.

    Uses format-specific prior means where the player has a dominant format.
    Economy shrinkage pulls outliers toward their cohort average;
    lower shrunk economy = better performance.

    Parameters
    ----------
    profile_df : pd.DataFrame
        Bowler profile table with pressure_legal_balls and pressure_economy_rate.
    format_col : str
        Column indicating primary format ('IPL', 'T20I', 'MIXED').

    Returns
    -------
    pd.DataFrame
        Input DataFrame with shrunk_pressure_econ_m{M} columns appended.
    """
    df_out = profile_df.copy()

    for m in SHRINKAGE_M_GRID:
        col_name = f"shrunk_pressure_econ_m{m}"

        def _shrink_row(row: pd.Series, _m: int = m) -> float:
            prior = FORMAT_PRIOR_ECON.get(str(row.get(format_col, "MIXED")), FORMAT_PRIOR_ECON["MIXED"])
            return empirical_bayes_shrink(
                observed_metric=row["pressure_economy_rate"],
                sample_size=int(row["pressure_legal_balls"]),
                prior_mean=prior,
                prior_weight=float(_m),
            )

        df_out[col_name] = df_out.apply(_shrink_row, axis=1)

    return df_out


# ---------------------------------------------------------------------------
# 8. Rank Stability Analysis
# ---------------------------------------------------------------------------

def compute_bowler_rank_stability(profile_df: pd.DataFrame) -> pd.DataFrame:
    """Compute ranking under each M value and measure position volatility.

    For economy-based ranking: lower economy = better = rank 1.

    Parameters
    ----------
    profile_df : pd.DataFrame
        Bowler profile including shrunk_pressure_econ_m{M} columns.

    Returns
    -------
    pd.DataFrame
        One row per bowler_id with rank stability metrics.
    """
    if profile_df is None or profile_df.empty:
        return pd.DataFrame()

    id_col = "bowler_id"
    name_col = "bowler_name"

    rank_cols = []
    for m in SHRINKAGE_M_GRID:
        rc = f"rank_m{m}"
        shrunk_col = f"shrunk_pressure_econ_m{m}"
        if shrunk_col in profile_df.columns:
            # Lower economy = better rank
            profile_df[rc] = profile_df[shrunk_col].rank(ascending=True, method="min", na_option="bottom")
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
# 9. Main Evaluation Builder
# ---------------------------------------------------------------------------

def build_bowler_evaluation(
    df: pd.DataFrame,
    min_pressure_balls: int = MIN_PRESSURE_BALLS_QUALIFIED,
    min_pressure_matches: int = MIN_PRESSURE_MATCHES_QUALIFIED,
    competition_type: Optional[str] = None,
) -> Dict[str, pd.DataFrame]:
    """Build the complete bowler evaluation dataset.

    Steps:
    1.  Filter to primary cohort (and optionally format: 'IPL' or 'T20I').
    2.  Prepare delivery attributes.
    3.  Build overall pressure + normal profile.
    4.  Assign bowling role.
    5.  Detect primary format.
    6.  Compute RCAE context-adjusted delta economy.
    7.  Compute phase-level pressure metrics.
    8.  Compute pressure-tier breakdown (HIGH/EXTREME).
    9.  Compute batting-resource situation metrics.
    10. Compute wicket impact metric.
    11. Compute match consistency.
    12. Attach evidence tier.
    13. Attach uncertainty intervals.
    14. Apply shrinkage sensitivity grid (M=25,45,60,90).
    15. Flag qualified candidates.
    16. Compute rank stability.

    Parameters
    ----------
    df : pd.DataFrame
        Full pressure deliveries dataset.
    min_pressure_balls : int
        Minimum pressure legal balls for ranking eligibility.
    min_pressure_matches : int
        Minimum distinct pressure matches for ranking eligibility.
    competition_type : str, optional
        Filter to specific format ('IPL' or 'T20I'), or None for all formats.

    Returns
    -------
    Dict[str, pd.DataFrame]
        'evaluation'    : Full bowler evaluation table (all bowlers).
        'qualified'     : Subset meeting minimum qualification thresholds.
        'phase_metrics' : Per-bowler per-phase pressure summary.
        'tier_metrics'  : Per-bowler HIGH/EXTREME tier breakdown.
        'resource_metrics': Per-bowler batting-resource-situation metrics.
        'wicket_impact' : Wicket impact scores.
        'rank_stability': Rank stability table across M grid.
        'rcae_metrics'  : Context-adjusted RCAE from Phase 2.3.
    """
    # --- Step 1: Primary cohort ---
    primary = df[df["is_primary_pressure_cohort"]].copy()
    if competition_type is not None:
        primary = primary[primary["competition_type"] == competition_type].copy()

    # --- Step 2: Prepare attributes ---
    prepared = prepare_bowler_delivery_attributes(primary)

    # --- Step 3: Overall profile ---
    pressure_del = prepared[prepared["is_bowler_pressure"]]
    normal_del = prepared[prepared["is_bowler_normal"]]

    overall = aggregate_bowler_segment(prepared, prefix="")
    pressure_agg = aggregate_bowler_segment(pressure_del, prefix="pressure_")
    normal_agg = aggregate_bowler_segment(normal_del, prefix="normal_")

    # Guard: only merge non-empty segments (empty DF has no columns including 'bowler_id')
    pressure_agg_safe = pressure_agg.drop(columns=["bowler_name"], errors="ignore")
    normal_agg_safe = normal_agg.drop(columns=["bowler_name"], errors="ignore")

    profile = overall
    if not pressure_agg_safe.empty and "bowler_id" in pressure_agg_safe.columns:
        profile = profile.merge(pressure_agg_safe, on="bowler_id", how="left")
    if not normal_agg_safe.empty and "bowler_id" in normal_agg_safe.columns:
        profile = profile.merge(normal_agg_safe, on="bowler_id", how="left")

    # Fill count columns with 0
    _count_cols = [
        "pressure_legal_balls", "pressure_total_deliveries", "pressure_runs_conceded",
        "pressure_wickets", "pressure_dot_balls", "pressure_fours_conceded",
        "pressure_sixes_conceded", "pressure_boundary_balls_conceded",
        "pressure_matches", "pressure_competitions",
        "normal_legal_balls", "normal_total_deliveries", "normal_runs_conceded",
        "normal_wickets", "normal_dot_balls", "normal_fours_conceded",
        "normal_sixes_conceded", "normal_boundary_balls_conceded",
        "normal_matches", "normal_competitions",
    ]
    for c in _count_cols:
        if c not in profile.columns:
            profile[c] = 0
        else:
            profile[c] = profile[c].fillna(0).astype(int)

    # Ensure rate columns exist (initialize to NaN if player cohort has zero exposure in that segment)
    _rate_cols = [
        "pressure_economy_rate", "pressure_bowling_average", "pressure_strike_rate",
        "pressure_dot_ball_pct", "pressure_boundary_concession_pct",
        "normal_economy_rate", "normal_bowling_average", "normal_strike_rate",
        "normal_dot_ball_pct", "normal_boundary_concession_pct",
    ]
    for c in _rate_cols:
        if c not in profile.columns:
            profile[c] = np.nan

    # Delta metrics
    profile["delta_economy"] = profile["pressure_economy_rate"] - profile["normal_economy_rate"]
    profile["delta_dot_ball_pct"] = profile["pressure_dot_ball_pct"] - profile["normal_dot_ball_pct"]
    profile["delta_boundary_concession_pct"] = (
        profile["pressure_boundary_concession_pct"] - profile["normal_boundary_concession_pct"]
    )

    # --- Step 4: Bowling role ---
    roles = classify_bowling_role(prepared)
    profile = profile.merge(roles, on="bowler_id", how="left")

    # --- Step 5: Primary format ---
    fmt = detect_primary_format(prepared)
    profile = profile.merge(fmt, on="bowler_id", how="left")

    # --- Step 6: Context-adjusted RCAE ---
    rcae_df = compute_context_adjusted_bowler_metrics(primary, filter_primary_cohort=False, min_legal_balls=20)

    # --- Step 7: Phase metrics ---
    phase_metrics = compute_phase_pressure_metrics(prepared)

    # --- Step 8: Pressure tier breakdown ---
    tier_metrics = compute_pressure_tier_breakdown(prepared)

    # --- Step 9: Resource situation metrics ---
    resource_metrics = compute_resource_situation_metrics(prepared)
    if not resource_metrics.empty and "bowler_id" in resource_metrics.columns:
        profile = profile.merge(resource_metrics, on="bowler_id", how="left")

    # --- Step 10: Wicket impact ---
    wicket_impact = compute_wicket_impact(prepared)
    if not wicket_impact.empty and "bowler_id" in wicket_impact.columns:
        profile = profile.merge(wicket_impact, on="bowler_id", how="left")

    # --- Step 11: Match consistency ---
    pressure_legal_for_consistency = pressure_del[pressure_del["is_legal_bowler_ball"]].copy()
    consistency = compute_bowler_match_consistency(pressure_legal_for_consistency)
    if not consistency.empty and "bowler_id" in consistency.columns:
        profile = profile.merge(
            consistency.drop(columns=["bowler_name"], errors="ignore"),
            on="bowler_id",
            how="left",
        )

    # --- Step 12: Evidence tier ---
    def _evidence(row: pd.Series) -> pd.Series:
        tier_info = classify_evidence_tier(
            sample_size=int(row.get("pressure_legal_balls", 0)),
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

    # --- Step 13: Uncertainty intervals ---
    def _ci_row(row: pd.Series) -> pd.Series:
        n = int(row.get("pressure_legal_balls", 0))
        econ = row.get("pressure_economy_rate", np.nan)
        fmt_str = str(row.get("primary_format", "MIXED"))
        prior_mean = FORMAT_PRIOR_ECON.get(fmt_str, FORMAT_PRIOR_ECON["MIXED"])

        shrunk, ci_lo, ci_hi = compute_rate_uncertainty_interval(
            observed_rate=float(econ) if not pd.isna(econ) else np.nan,
            sample_size=n,
            prior_mean=prior_mean,
            prior_weight=30.0,
            population_std=2.5,
        )
        # Beta-binomial for dot ball %
        dots = int(row.get("pressure_dot_balls", 0))
        dot_post, dot_lo, dot_hi = compute_beta_binomial_credible_interval(
            successes=dots,
            trials=n,
            prior_alpha=3.0,
            prior_beta=5.0,
        )
        return pd.Series(
            {
                "pressure_econ_ci_lower_95": round(ci_lo, 2),
                "pressure_econ_ci_upper_95": round(ci_hi, 2),
                "pressure_dot_pct_posterior": round(dot_post, 1),
                "pressure_dot_pct_ci_lower_95": round(dot_lo, 1),
                "pressure_dot_pct_ci_upper_95": round(dot_hi, 1),
            }
        )

    ci_cols = profile.apply(_ci_row, axis=1)
    profile = pd.concat([profile, ci_cols], axis=1)

    # --- Step 14: Shrinkage grid ---
    profile = apply_bowler_shrinkage_grid(profile, format_col="primary_format")

    # Merge RCAE onto main profile
    if not rcae_df.empty:
        rcae_cols = [
            "bowler_id",
            "context_adjusted_delta_econ",
            "all_runs_rcae_delta_econ",
            "observed_pressure_econ",
            "expected_pressure_econ",
            "legal_context_delta_econ",
            "legal_rcae_delta_econ",
            "observed_legal_econ",
            "expected_legal_econ",
        ]
        rcae_subset = rcae_df[[c for c in rcae_cols if c in rcae_df.columns]]
        profile = profile.merge(rcae_subset, on="bowler_id", how="left")

    # --- Step 15: Qualification flag ---
    profile["meets_minimum_qualification"] = (
        (profile["pressure_legal_balls"] >= min_pressure_balls)
        & (profile["pressure_matches"] >= min_pressure_matches)
    )

    # --- Step 16: Ordering ---
    profile = profile.sort_values("pressure_legal_balls", ascending=False).reset_index(drop=True)

    # Rank stability (qualified players only)
    qualified = profile[profile["meets_minimum_qualification"]].copy()
    if qualified.empty:
        rank_stability = pd.DataFrame()
    else:
        rank_stability = compute_bowler_rank_stability(qualified)

    return {
        "evaluation": profile,
        "qualified": qualified,
        "phase_metrics": phase_metrics,
        "tier_metrics": tier_metrics,
        "resource_metrics": resource_metrics,
        "wicket_impact": wicket_impact,
        "rank_stability": rank_stability,
        "rcae_metrics": rcae_df,
    }


# ---------------------------------------------------------------------------
# 10. Role-Specific Summaries
# ---------------------------------------------------------------------------

def build_bowler_role_summaries(evaluation_df: pd.DataFrame) -> pd.DataFrame:
    """Compute aggregated pressure performance summary by bowling role.

    Parameters
    ----------
    evaluation_df : pd.DataFrame
        Qualified bowler evaluation table with primary_bowling_role.

    Returns
    -------
    pd.DataFrame
        One row per bowling role with median and IQR for key pressure metrics.
    """
    key_metrics = [
        "pressure_legal_balls",
        "pressure_economy_rate",
        "context_adjusted_delta_econ",
        "pressure_dot_ball_pct",
        "pressure_boundary_concession_pct",
        "pressure_match_pass_rate",
        "shrunk_pressure_econ_m45",
        "wickets_per_over",
    ]
    available = [c for c in key_metrics if c in evaluation_df.columns]
    records = []
    for role, grp in evaluation_df.groupby("primary_bowling_role", observed=True):
        row = {"primary_bowling_role": role, "player_count": len(grp)}
        for col in available:
            vals = grp[col].dropna()
            row[f"{col}_median"] = round(float(vals.median()), 2) if len(vals) > 0 else np.nan
            row[f"{col}_p25"] = round(float(vals.quantile(0.25)), 2) if len(vals) > 0 else np.nan
            row[f"{col}_p75"] = round(float(vals.quantile(0.75)), 2) if len(vals) > 0 else np.nan
        records.append(row)
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 11. Qualification Sensitivity Analysis
# ---------------------------------------------------------------------------

def build_bowler_qualification_sensitivity(eval_df: pd.DataFrame) -> pd.DataFrame:
    """Evaluate bowler candidate qualification under three sensitivity configurations.

    Threshold configurations:
    1. Broad / Discovery : >= 30 pressure legal balls AND >= 4 distinct matches
    2. Balanced          : >= 60 pressure legal balls AND >= 6 distinct matches
    3. Strict / High     : >= 100 pressure legal balls AND >= 8 distinct matches

    Parameters
    ----------
    eval_df : pd.DataFrame
        Bowler evaluation table.

    Returns
    -------
    pd.DataFrame
        Qualified candidates tagged with qualification cohorts and rank sensitivity.
    """
    df = eval_df.copy()
    df["qual_broad_30b_4m"] = (df["pressure_legal_balls"] >= 30) & (df["pressure_matches"] >= 4)
    df["qual_balanced_60b_6m"] = (df["pressure_legal_balls"] >= 60) & (df["pressure_matches"] >= 6)
    df["qual_strict_100b_8m"] = (df["pressure_legal_balls"] >= 100) & (df["pressure_matches"] >= 8)

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
        "bowler_id", "bowler_name", "primary_bowling_role", "primary_format",
        "pressure_legal_balls", "pressure_matches", "pressure_competitions",
        "evidence_tier", "qualification_cohort", "qual_broad_30b_4m",
        "qual_balanced_60b_6m", "qual_strict_100b_8m",
        "pressure_economy_rate", "shrunk_pressure_econ_m25", "shrunk_pressure_econ_m45",
        "shrunk_pressure_econ_m60", "shrunk_pressure_econ_m90",
        "context_adjusted_delta_econ", "pressure_match_pass_rate", "wickets_per_over"
    ]
    available = [c for c in cols if c in qual.columns]
    return qual[available].sort_values("shrunk_pressure_econ_m25", ascending=True).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 12. Persistence Helper
# ---------------------------------------------------------------------------

def save_bowler_evaluation(
    result: Dict[str, pd.DataFrame],
    output_dir: Path,
) -> None:
    """Persist all bowler evaluation tables to Parquet and CSV.

    Parameters
    ----------
    result : Dict[str, pd.DataFrame]
        Output of build_bowler_evaluation().
    output_dir : Path
        Directory where files are written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    file_map = {
        "bowler_evaluation": result["evaluation"],
        "bowler_qualified": result["qualified"],
        "bowler_phase_metrics": result["phase_metrics"],
        "bowler_tier_metrics": result["tier_metrics"],
        "bowler_resource_metrics": result["resource_metrics"],
        "bowler_wicket_impact": result["wicket_impact"],
        "bowler_rank_stability": result["rank_stability"],
        "bowler_rcae_metrics": result["rcae_metrics"],
    }

    # Role summaries and qualification sensitivity derived from evaluation
    if not result["qualified"].empty:
        role_summary = build_bowler_role_summaries(result["qualified"])
        file_map["bowler_role_summaries"] = role_summary
        qual_sens = build_bowler_qualification_sensitivity(result["evaluation"])
        file_map["bowler_qualification_sensitivity"] = qual_sens

    for name, table in file_map.items():
        if table is None or table.empty:
            continue
        parquet_path = output_dir / f"{name}.parquet"
        csv_path = output_dir / f"{name}.csv"
        table.to_parquet(parquet_path, index=False)
        table.to_csv(csv_path, index=False)
