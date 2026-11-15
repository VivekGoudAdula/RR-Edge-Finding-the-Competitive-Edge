"""
Batter performance modeling and pressure-decomposition engine for RR EDGE.

Phase 2.3: Computes player-level batting metrics across overall, pressure,
and normal match states, stratified by formats, phases, and roles, with
exact cricket dismissal and balls-faced attribution.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd


def prepare_batter_delivery_attributes(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare delivery-level helper attributes for batter metrics aggregation.

    Attribution Rules:
    - Batter runs = `runs` (from bat only; extras are NOT batter runs).
    - Balls faced = deliveries where `extras_type != 'wide'`.
      (Wides do not count as balls faced; no-balls, byes, leg-byes count as balls faced).
    - Boundaries = 4s and 6s scored by the batter (`runs == 4` or `runs == 6`).
    - Dot balls = legal deliveries or no-balls faced with 0 batter runs (`runs == 0` and `extras_type != 'wide'`).
    - Dismissals = attributed using `dismissed_player_id`.

    Parameters
    ----------
    df : pd.DataFrame
        Delivery DataFrame containing match_id, innings, striker_id, non_striker_id,
        runs, extras_type, is_wicket, dismissed_player_id, batter_pressure_tier.

    Returns
    -------
    pd.DataFrame
        DataFrame with helper columns appended.
    """
    df_out = df.copy()

    # 1. Balls faced: any delivery that is NOT a wide
    df_out["is_ball_faced"] = df_out["extras_type"] != "wide"

    # 2. Batter runs
    df_out["batter_runs"] = df_out["runs"].astype(int)

    # 3. Boundaries and boundary runs
    df_out["is_four"] = df_out["batter_runs"] == 4
    df_out["is_six"] = df_out["batter_runs"] == 6
    df_out["is_boundary"] = df_out["is_four"] | df_out["is_six"]
    df_out["boundary_runs"] = np.where(df_out["is_boundary"], df_out["batter_runs"], 0)

    # 4. Dot balls (faced balls yielding 0 runs)
    df_out["is_dot_ball"] = df_out["is_ball_faced"] & (df_out["batter_runs"] == 0)

    # 5. Pressure tier partitioning
    df_out["is_pressure"] = df_out["batter_pressure_tier"].isin(["HIGH", "EXTREME"])
    df_out["is_normal"] = df_out["batter_pressure_tier"].isin(["LOW", "MODERATE"])

    return df_out


def compute_player_dismissals(
    df: pd.DataFrame,
    player_id: Optional[int] = None,
) -> pd.Series:
    """Compute total dismissals for players, correctly accounting for non-striker outs.

    Accounts for:
    - Striker dismissals (bowled, caught, lbw, stumped, striker run-out, hit wicket).
    - Non-striker dismissals (non-striker run-out, non-striker retire out).

    Parameters
    ----------
    df : pd.DataFrame
        Delivery DataFrame with is_wicket, dismissed_player_id, striker_id, non_striker_id.
    player_id : int, optional
        Filter to a specific player ID, or None for all players.

    Returns
    -------
    pd.Series
        Total dismissals indexed by player ID.
    """
    wickets = df[df["is_wicket"] == 1]
    if len(wickets) == 0:
        return pd.Series(dtype=int)

    # Handle explicit dismissed_player_id
    valid_dismissals = wickets[wickets["dismissed_player_id"].notna()].copy()
    valid_dismissals["dismissed_player_id"] = valid_dismissals["dismissed_player_id"].astype(int)

    if player_id is not None:
        valid_dismissals = valid_dismissals[valid_dismissals["dismissed_player_id"] == player_id]

    dismissal_counts = valid_dismissals.groupby("dismissed_player_id").size()

    # Fallback for rare rows with NaN dismissed_player_id (e.g. non-striker retire out)
    nan_dismissals = wickets[wickets["dismissed_player_id"].isna()]
    if len(nan_dismissals) > 0:
        for _, row in nan_dismissals.iterrows():
            # If striker was set, credit striker, else non-striker
            p = row["striker_id"] if pd.notna(row["striker_id"]) else row["non_striker_id"]
            if pd.notna(p):
                pid = int(p)
                if player_id is None or pid == player_id:
                    dismissal_counts[pid] = dismissal_counts.get(pid, 0) + 1

    return dismissal_counts


def aggregate_batter_segment(
    df_segment: pd.DataFrame,
    df_all_wickets: Optional[pd.DataFrame] = None,
    prefix: str = "",
) -> pd.DataFrame:
    """Aggregate core batting performance metrics for a specific delivery segment.

    Parameters
    ----------
    df_segment : pd.DataFrame
        Delivery records for this segment (e.g. pressure, normal, IPL, or Death phase).
    df_all_wickets : pd.DataFrame, optional
        Wickets DataFrame for dismissal attribution within this condition.
        If None, uses `df_segment[df_segment['is_wicket'] == 1]`.
    prefix : str, optional
        Column name prefix (e.g. 'pressure_', 'normal_').

    Returns
    -------
    pd.DataFrame
        Aggregated metrics indexed by striker_id.
    """
    if len(df_segment) == 0:
        return pd.DataFrame()

    grp = df_segment.groupby(["striker_id", "striker_name"])

    # Aggregations
    balls_faced = grp["is_ball_faced"].sum()
    batter_runs = grp["batter_runs"].sum()
    fours = grp["is_four"].sum()
    sixes = grp["is_six"].sum()
    boundary_balls = grp["is_boundary"].sum()
    boundary_runs = grp["boundary_runs"].sum()
    dot_balls = grp["is_dot_ball"].sum()
    match_count = grp["match_id"].nunique()
    comp_count = grp["comp_id"].nunique()

    # Calculate dismissals within this segment
    wkt_source = df_segment if df_all_wickets is None else df_all_wickets
    seg_dismissals = compute_player_dismissals(wkt_source)

    # Assemble summary DataFrame
    summary = pd.DataFrame(
        {
            f"{prefix}balls_faced": balls_faced,
            f"{prefix}runs": batter_runs,
            f"{prefix}fours": fours,
            f"{prefix}sixes": sixes,
            f"{prefix}boundary_balls": boundary_balls,
            f"{prefix}boundary_runs": boundary_runs,
            f"{prefix}dot_balls": dot_balls,
            f"{prefix}matches": match_count,
            f"{prefix}competitions": comp_count,
        }
    ).reset_index()

    # Map dismissals
    summary[f"{prefix}dismissals"] = summary["striker_id"].map(seg_dismissals).fillna(0).astype(int)

    # Derived Rate Metrics
    # Strike rate
    summary[f"{prefix}strike_rate"] = np.where(
        summary[f"{prefix}balls_faced"] > 0,
        (summary[f"{prefix}runs"] * 100.0) / summary[f"{prefix}balls_faced"],
        np.nan,
    )

    # Boundary percentage (runs from boundaries / total runs)
    summary[f"{prefix}boundary_runs_pct"] = np.where(
        summary[f"{prefix}runs"] > 0,
        (summary[f"{prefix}boundary_runs"] * 100.0) / summary[f"{prefix}runs"],
        0.0,
    )

    # Boundary ball frequency (percentage of balls faced hit for boundary)
    summary[f"{prefix}boundary_ball_pct"] = np.where(
        summary[f"{prefix}balls_faced"] > 0,
        (summary[f"{prefix}boundary_balls"] * 100.0) / summary[f"{prefix}balls_faced"],
        0.0,
    )

    # Dot ball percentage
    summary[f"{prefix}dot_ball_pct"] = np.where(
        summary[f"{prefix}balls_faced"] > 0,
        (summary[f"{prefix}dot_balls"] * 100.0) / summary[f"{prefix}balls_faced"],
        0.0,
    )

    # Dismissal rate (dismissals / balls faced)
    summary[f"{prefix}dismissal_rate"] = np.where(
        summary[f"{prefix}balls_faced"] > 0,
        summary[f"{prefix}dismissals"] / summary[f"{prefix}balls_faced"],
        0.0,
    )

    # Runs per dismissal (Batting Average)
    # If 0 dismissals, record total runs (undefeated) but flag in analysis
    summary[f"{prefix}runs_per_dismissal"] = np.where(
        summary[f"{prefix}dismissals"] > 0,
        summary[f"{prefix}runs"] / summary[f"{prefix}dismissals"],
        np.where(summary[f"{prefix}runs"] > 0, summary[f"{prefix}runs"], np.nan),
    )

    return summary


def build_batter_profile(
    df: pd.DataFrame,
    filter_primary_cohort: bool = True,
    min_balls_faced: int = 0,
) -> pd.DataFrame:
    """Build complete batter profile comparing pressure vs normal performance.

    Includes:
    - Overall performance metrics
    - Pressure performance metrics (HIGH + EXTREME)
    - Normal performance metrics (LOW + MODERATE)
    - Pressure vs Normal comparison delta metrics
    - Visible denominators for every metric

    Parameters
    ----------
    df : pd.DataFrame
        Pressure deliveries dataset.
    filter_primary_cohort : bool, optional
        Filter `is_primary_pressure_cohort == True` (default: True).
    min_balls_faced : int, optional
        Minimum overall balls faced threshold for inclusion (default: 0).

    Returns
    -------
    pd.DataFrame
        Comprehensive batter profile table.
    """
    cohort_df = df[df["is_primary_pressure_cohort"]].copy() if filter_primary_cohort else df.copy()
    cohort_df = prepare_batter_delivery_attributes(cohort_df)

    # 1. Overall metrics
    overall_df = aggregate_batter_segment(cohort_df, prefix="")

    # 2. Pressure metrics (HIGH + EXTREME tiers)
    pressure_deliveries = cohort_df[cohort_df["is_pressure"]]
    pressure_df = aggregate_batter_segment(pressure_deliveries, prefix="pressure_")

    # 3. Normal metrics (LOW + MODERATE tiers)
    normal_deliveries = cohort_df[cohort_df["is_normal"]]
    normal_df = aggregate_batter_segment(normal_deliveries, prefix="normal_")

    # Merge overall, pressure, and normal
    profile = overall_df.merge(
        pressure_df.drop(columns=["striker_name"], errors="ignore"),
        on="striker_id",
        how="left",
    ).merge(
        normal_df.drop(columns=["striker_name"], errors="ignore"),
        on="striker_id",
        how="left",
    )

    # Fill missing pressure/normal counts with 0 for players with no exposure in a segment
    count_cols = [
        "pressure_balls_faced", "pressure_runs", "pressure_fours", "pressure_sixes",
        "pressure_boundary_balls", "pressure_boundary_runs", "pressure_dot_balls",
        "pressure_matches", "pressure_competitions", "pressure_dismissals",
        "normal_balls_faced", "normal_runs", "normal_fours", "normal_sixes",
        "normal_boundary_balls", "normal_boundary_runs", "normal_dot_balls",
        "normal_matches", "normal_competitions", "normal_dismissals",
    ]
    for c in count_cols:
        if c in profile.columns:
            profile[c] = profile[c].fillna(0).astype(int)

    # 4. Comparative Delta Metrics (Pressure vs Normal)
    # Strike rate delta: positive means player scores FASTER under pressure (favourable)
    profile["delta_strike_rate"] = profile["pressure_strike_rate"] - profile["normal_strike_rate"]

    # Runs per dismissal delta: positive means player averages MORE runs before out under pressure
    profile["delta_runs_per_dismissal"] = (
        profile["pressure_runs_per_dismissal"] - profile["normal_runs_per_dismissal"]
    )

    # Boundary ball frequency delta: positive means player hits boundaries MORE frequently
    profile["delta_boundary_ball_pct"] = (
        profile["pressure_boundary_ball_pct"] - profile["normal_boundary_ball_pct"]
    )

    # Dot ball percentage delta: negative means player plays FEWER dots under pressure (favourable)
    profile["delta_dot_ball_pct"] = (
        profile["pressure_dot_ball_pct"] - profile["normal_dot_ball_pct"]
    )

    # Filter minimum balls faced
    if min_balls_faced > 0:
        profile = profile[profile["balls_faced"] >= min_balls_faced].copy()

    # Reorder columns logically
    id_cols = ["striker_id", "striker_name", "matches", "competitions", "balls_faced", "runs", "strike_rate"]
    other_cols = [c for c in profile.columns if c not in id_cols]
    profile = profile[id_cols + other_cols].sort_values("balls_faced", ascending=False).reset_index(drop=True)

    return profile


def compute_context_adjusted_batter_metrics(
    df: pd.DataFrame,
    filter_primary_cohort: bool = True,
    min_balls: int = 20,
) -> pd.DataFrame:
    """Compute context-adjusted Runs Above Expected (RAE) and Context Delta SR.

    Controls for competition format, innings phase, and wickets in hand by matching
    each delivery to its contextual expectation: E[runs | format, phase, wickets_bucket].

    Parameters
    ----------
    df : pd.DataFrame
        Deliveries dataset containing competition_type, innings_phase,
        wickets_remaining_before, runs, is_primary_pressure_cohort, extras_type.
    filter_primary_cohort : bool, optional
        Filter is_primary_pressure_cohort == True (default: True).
    min_balls : int, optional
        Minimum pressure balls faced threshold (default: 20).

    Returns
    -------
    pd.DataFrame
        Table containing observed SR, expected SR, RAE, and context-adjusted delta SR.
    """
    cohort_df = df[df["is_primary_pressure_cohort"]].copy() if filter_primary_cohort else df.copy()
    prep = prepare_batter_delivery_attributes(cohort_df)
    faced = prep[prep["is_ball_faced"]].copy()

    # Context partitioning: format x phase x wickets bucket
    faced["wkt_bucket"] = pd.cut(
        faced["wickets_remaining_before"],
        bins=[-1, 3, 6, 11],
        labels=["0-3 wkts", "4-6 wkts", "7-10 wkts"],
    )

    context_keys = ["competition_type", "innings_phase", "wkt_bucket"]
    grid = faced.groupby(context_keys, observed=False)["batter_runs"].mean().reset_index()
    grid = grid.rename(columns={"batter_runs": "exp_runs_per_ball"})

    faced = faced.merge(grid, on=context_keys, how="left")
    faced["runs_above_expected"] = faced["batter_runs"] - faced["exp_runs_per_ball"]

    # Filter to pressure deliveries
    p_faced = faced[faced["is_pressure"]]
    if len(p_faced) == 0:
        return pd.DataFrame()

    grp = p_faced.groupby(["striker_id", "striker_name"])
    res = pd.DataFrame(
        {
            "pressure_balls_faced": grp["batter_runs"].count(),
            "pressure_runs": grp["batter_runs"].sum(),
            "expected_runs": grp["exp_runs_per_ball"].sum(),
            "runs_above_expected": grp["runs_above_expected"].sum(),
        }
    ).reset_index()

    res["observed_pressure_sr"] = (res["pressure_runs"] * 100.0) / res["pressure_balls_faced"]
    res["expected_pressure_sr"] = (res["expected_runs"] * 100.0) / res["pressure_balls_faced"]
    res["context_adjusted_delta_sr"] = (res["runs_above_expected"] * 100.0) / res["pressure_balls_faced"]

    if min_balls > 0:
        res = res[res["pressure_balls_faced"] >= min_balls].copy()

    return res.sort_values("context_adjusted_delta_sr", ascending=False).reset_index(drop=True)


def build_batter_stratified_metrics(
    df: pd.DataFrame,
    stratify_by: str = "competition_type",
    filter_primary_cohort: bool = True,
    min_balls: int = 10,
) -> pd.DataFrame:
    """Build batter metrics stratified by competition format, phase, or role.

    Parameters
    ----------
    df : pd.DataFrame
        Pressure deliveries dataset.
    stratify_by : str, optional
        Column to partition by: 'competition_type', 'innings_phase', or 'batting_order_group'.
    filter_primary_cohort : bool, optional
        Filter primary cohort (default: True).
    min_balls : int, optional
        Minimum balls faced in segment (default: 10).

    Returns
    -------
    pd.DataFrame
        Stratified summary table.
    """
    cohort_df = df[df["is_primary_pressure_cohort"]].copy() if filter_primary_cohort else df.copy()
    cohort_df = prepare_batter_delivery_attributes(cohort_df)

    if stratify_by == "batting_order_group":
        cohort_df["batting_order_group"] = pd.cut(
            cohort_df["batting_order_raw"],
            bins=[0, 3, 6, 20],
            labels=["Top-Order (1-3)", "Middle-Order (4-6)", "Lower-Order (7-11)"],
        )

    records: List[pd.DataFrame] = []
    for stratum, grp in cohort_df.groupby(stratify_by):
        seg_summary = aggregate_batter_segment(grp, prefix=f"{stratum}_")
        p_grp = grp[grp["is_pressure"]]
        if len(p_grp) > 0:
            p_summary = aggregate_batter_segment(p_grp, prefix=f"{stratum}_pressure_")
            seg_summary = seg_summary.merge(
                p_summary.drop(columns=["striker_name"], errors="ignore"),
                on="striker_id",
                how="left",
            )
        n_grp = grp[grp["is_normal"]]
        if len(n_grp) > 0:
            n_summary = aggregate_batter_segment(n_grp, prefix=f"{stratum}_normal_")
            seg_summary = seg_summary.merge(
                n_summary.drop(columns=["striker_name"], errors="ignore"),
                on="striker_id",
                how="left",
            )
        # Compute within-stratum context-controlled delta strike rate
        p_sr_col = f"{stratum}_pressure_strike_rate"
        n_sr_col = f"{stratum}_normal_strike_rate"
        if p_sr_col in seg_summary.columns and n_sr_col in seg_summary.columns:
            seg_summary[f"{stratum}_delta_strike_rate"] = (
                seg_summary[p_sr_col] - seg_summary[n_sr_col]
            )
        records.append(seg_summary)

    if len(records) == 0:
        return pd.DataFrame()

    out_df = records[0]
    for r in records[1:]:
        out_df = out_df.merge(r, on=["striker_id", "striker_name"], how="outer")

    return out_df

