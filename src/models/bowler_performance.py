"""
Bowler performance modeling and pressure-decomposition engine for RR EDGE.

Phase 2.3: Computes player-level bowling metrics across overall, pressure,
and normal match states, stratified by formats, phases, and bowling styles, with
exact cricket extras concession rules and bowler-credited wicket attribution.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd


def prepare_bowler_delivery_attributes(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare delivery-level helper attributes for bowler metrics aggregation.

    Attribution Rules:
    - Legal balls bowled = `is_legal_ball == True`.
    - Bowler runs conceded:
      - Byes, leg-byes, and penalty runs are NOT charged to the bowler.
      - Wides and no-balls (extras1 + extras_2) are charged to the bowler.
      - Batter runs scored off the bat are charged to the bowler.
    - Bowler wickets:
      - Includes ONLY bowler-credited dismissals: bowled, caught, lbw, stumped, hit wicket (`is_bowler_wkt == True`).
      - Excludes run outs, retired outs, and obstructing the field.
    - Dot balls = legal deliveries where the bowler concedes 0 runs.
    - Boundary balls = deliveries where a 4 or 6 is scored off the bowler.

    Parameters
    ----------
    df : pd.DataFrame
        Delivery DataFrame containing bowler_id, bowler_name, runs, total_delivery_runs,
        extras_type, is_legal_ball, is_bowler_wkt, bowler_pressure_tier.

    Returns
    -------
    pd.DataFrame
        DataFrame with bowler helper columns appended.
    """
    df_out = df.copy()

    # 1. Bowler runs conceded calculation
    # Byes, legbyes, and penalty awards are excluded from bowler analysis
    extras_series = df_out["extras_type"]
    tot_runs = df_out["total_delivery_runs"].values
    bat_runs = df_out["runs"].values

    bowler_runs = np.zeros(len(df_out), dtype=np.int64)
    for i, et in enumerate(extras_series):
        if et in ("byes", "legbyes", "Penalty"):
            bowler_runs[i] = 0
        elif et in ("wide", "Overstep", "other"):
            bowler_runs[i] = int(tot_runs[i])
        else:
            bowler_runs[i] = int(bat_runs[i])

    df_out["bowler_runs_conceded"] = bowler_runs

    # 2. Legal delivery flag
    df_out["is_legal_bowler_ball"] = df_out["is_legal_ball"].astype(bool)

    # 3. Bowler dot ball: legal ball with 0 runs conceded
    df_out["is_bowler_dot"] = df_out["is_legal_bowler_ball"] & (df_out["bowler_runs_conceded"] == 0)

    # 4. Boundary conceded: 4 or 6 off the bat or 4+ runs conceded on legal ball
    df_out["is_four_conceded"] = df_out["runs"] == 4
    df_out["is_six_conceded"] = df_out["runs"] == 6
    df_out["is_boundary_conceded"] = df_out["is_four_conceded"] | df_out["is_six_conceded"]

    # 5. Bowler wicket (bowled, caught, lbw, stumped, hit wicket)
    if "is_bowler_wkt" in df_out.columns:
        df_out["bowler_wicket_credit"] = df_out["is_bowler_wkt"].astype(int)
    elif "bowler_wicket_credit" in df_out.columns:
        df_out["bowler_wicket_credit"] = df_out["bowler_wicket_credit"].astype(int)
    else:
        df_out["bowler_wicket_credit"] = 0

    # 6. Pressure tier partitioning
    if "bowler_pressure_tier" in df_out.columns:
        df_out["is_bowler_pressure"] = df_out["bowler_pressure_tier"].isin(["HIGH", "EXTREME"])
        df_out["is_bowler_normal"] = df_out["bowler_pressure_tier"].isin(["LOW", "MODERATE"])
    else:
        if "is_bowler_pressure" not in df_out.columns:
            df_out["is_bowler_pressure"] = True
        if "is_bowler_normal" not in df_out.columns:
            df_out["is_bowler_normal"] = False

    return df_out


def aggregate_bowler_segment(
    df_segment: pd.DataFrame,
    prefix: str = "",
) -> pd.DataFrame:
    """Aggregate core bowling performance metrics for a specific delivery segment.

    Parameters
    ----------
    df_segment : pd.DataFrame
        Delivery records for this segment (e.g. pressure, normal, Death phase).
    prefix : str, optional
        Column name prefix (e.g. 'pressure_', 'normal_').

    Returns
    -------
    pd.DataFrame
        Aggregated metrics indexed by bowler_id.
    """
    if len(df_segment) == 0:
        return pd.DataFrame()

    grp = df_segment.groupby(["bowler_id", "bowler_name"])

    # Aggregations
    legal_balls = grp["is_legal_bowler_ball"].sum()
    total_deliveries = grp.size()
    runs_conceded = grp["bowler_runs_conceded"].sum()
    wickets = grp["bowler_wicket_credit"].sum()
    dot_balls = grp["is_bowler_dot"].sum()
    fours_conceded = grp["is_four_conceded"].sum()
    sixes_conceded = grp["is_six_conceded"].sum()
    boundary_balls = grp["is_boundary_conceded"].sum()
    matches = grp["match_id"].nunique()
    competitions = grp["comp_id"].nunique()

    # Derived Rate Metrics
    overs = legal_balls / 6.0
    economy_rate = np.where(legal_balls > 0, (runs_conceded * 6.0) / legal_balls, np.nan)
    bowling_average = np.where(wickets > 0, runs_conceded / wickets, np.nan)
    strike_rate = np.where(wickets > 0, legal_balls / wickets, np.nan)
    dot_ball_pct = np.where(legal_balls > 0, (dot_balls * 100.0) / legal_balls, 0.0)
    boundary_concession_pct = np.where(legal_balls > 0, (boundary_balls * 100.0) / legal_balls, 0.0)

    summary = pd.DataFrame(
        {
            f"{prefix}legal_balls": legal_balls,
            f"{prefix}total_deliveries": total_deliveries,
            f"{prefix}overs": overs.round(2),
            f"{prefix}runs_conceded": runs_conceded,
            f"{prefix}wickets": wickets,
            f"{prefix}economy_rate": economy_rate,
            f"{prefix}bowling_average": bowling_average,
            f"{prefix}strike_rate": strike_rate,
            f"{prefix}dot_balls": dot_balls,
            f"{prefix}dot_ball_pct": dot_ball_pct,
            f"{prefix}fours_conceded": fours_conceded,
            f"{prefix}sixes_conceded": sixes_conceded,
            f"{prefix}boundary_balls_conceded": boundary_balls,
            f"{prefix}boundary_concession_pct": boundary_concession_pct,
            f"{prefix}matches": matches,
            f"{prefix}competitions": competitions,
        }
    ).reset_index()

    return summary


def build_bowler_profile(
    df: pd.DataFrame,
    filter_primary_cohort: bool = True,
    min_legal_balls: int = 0,
) -> pd.DataFrame:
    """Build complete bowler profile comparing pressure vs normal performance.

    Includes:
    - Overall performance metrics
    - Pressure performance metrics (HIGH + EXTREME tiers)
    - Normal performance metrics (LOW + MODERATE tiers)
    - Pressure vs Normal comparison delta metrics
    - Visible denominators for every metric

    Parameters
    ----------
    df : pd.DataFrame
        Pressure deliveries dataset.
    filter_primary_cohort : bool, optional
        Filter `is_primary_pressure_cohort == True` (default: True).
    min_legal_balls : int, optional
        Minimum overall legal balls bowled threshold for inclusion (default: 0).

    Returns
    -------
    pd.DataFrame
        Comprehensive bowler profile table.
    """
    cohort_df = df[df["is_primary_pressure_cohort"]].copy() if filter_primary_cohort else df.copy()
    cohort_df = prepare_bowler_delivery_attributes(cohort_df)

    # 1. Overall metrics
    overall_df = aggregate_bowler_segment(cohort_df, prefix="")

    # 2. Pressure metrics (HIGH + EXTREME tiers)
    pressure_deliveries = cohort_df[cohort_df["is_bowler_pressure"]]
    pressure_df = aggregate_bowler_segment(pressure_deliveries, prefix="pressure_")

    # 3. Normal metrics (LOW + MODERATE tiers)
    normal_deliveries = cohort_df[cohort_df["is_bowler_normal"]]
    normal_df = aggregate_bowler_segment(normal_deliveries, prefix="normal_")

    # Merge overall, pressure, and normal
    profile = overall_df.merge(
        pressure_df.drop(columns=["bowler_name"], errors="ignore"),
        on="bowler_id",
        how="left",
    ).merge(
        normal_df.drop(columns=["bowler_name"], errors="ignore"),
        on="bowler_id",
        how="left",
    )

    # Fill count columns with 0 for bowlers with 0 exposure in a segment
    count_cols = [
        "pressure_legal_balls", "pressure_total_deliveries", "pressure_runs_conceded",
        "pressure_wickets", "pressure_dot_balls", "pressure_fours_conceded",
        "pressure_sixes_conceded", "pressure_boundary_balls_conceded",
        "pressure_matches", "pressure_competitions",
        "normal_legal_balls", "normal_total_deliveries", "normal_runs_conceded",
        "normal_wickets", "normal_dot_balls", "normal_fours_conceded",
        "normal_sixes_conceded", "normal_boundary_balls_conceded",
        "normal_matches", "normal_competitions",
    ]
    for c in count_cols:
        if c in profile.columns:
            profile[c] = profile[c].fillna(0).astype(int)

    # 4. Comparative Delta Metrics (Pressure vs Normal)
    # Economy delta: negative is FAVOURABLE (bowler concedes fewer runs per over under pressure)
    profile["delta_economy"] = profile["pressure_economy_rate"] - profile["normal_economy_rate"]

    # Dot ball percentage delta: positive is FAVOURABLE (bowler bowls higher % of dots under pressure)
    profile["delta_dot_ball_pct"] = (
        profile["pressure_dot_ball_pct"] - profile["normal_dot_ball_pct"]
    )

    # Boundary concession rate delta: negative is FAVOURABLE (fewer boundaries conceded)
    profile["delta_boundary_concession_pct"] = (
        profile["pressure_boundary_concession_pct"] - profile["normal_boundary_concession_pct"]
    )

    # Bowling strike rate delta: negative is FAVOURABLE (takes wickets in fewer balls)
    profile["delta_strike_rate"] = profile["pressure_strike_rate"] - profile["normal_strike_rate"]

    # Filter minimum legal balls
    if min_legal_balls > 0:
        profile = profile[profile["legal_balls"] >= min_legal_balls].copy()

    # Reorder columns
    id_cols = ["bowler_id", "bowler_name", "matches", "competitions", "legal_balls", "overs", "wickets", "economy_rate"]
    other_cols = [c for c in profile.columns if c not in id_cols]
    profile = profile[id_cols + other_cols].sort_values("legal_balls", ascending=False).reset_index(drop=True)

    return profile


def compute_context_adjusted_bowler_metrics(
    df: pd.DataFrame,
    filter_primary_cohort: bool = True,
    min_legal_balls: int = 20,
) -> pd.DataFrame:
    """Compute context-adjusted Runs Conceded Above Expected (RCAE) and Context Delta Economy.

    Computes two complementary metrics:
    1. Primary Metric: All-Runs RCAE (Δ Economy)
       Includes all bowler-conceded runs (wides, no-balls off the bat, extras charged to bowler),
       excluding byes, leg-byes, and penalty runs according to cricket rules.
       Normalized by legal-ball exposure against a context expectation trained on all bowler runs per legal ball.
    2. Secondary Diagnostic Metric: Legal-Ball RCAE (Δ Legal Economy)
       Evaluates delivery execution strictly on valid deliveries, excluding all illegal deliveries
       (wides, no-balls) from both observed concession and contextual expectation.

    Controls for competition format, innings phase, and wickets in hand:
    E[runs_conceded | format, phase, wickets_bucket].

    Parameters
    ----------
    df : pd.DataFrame
        Deliveries dataset containing competition_type, innings_phase,
        wickets_remaining_before, runs, is_primary_pressure_cohort, extras_type.
    filter_primary_cohort : bool, optional
        Filter is_primary_pressure_cohort == True (default: True).
    min_legal_balls : int, optional
        Minimum pressure legal balls bowled threshold (default: 20).

    Returns
    -------
    pd.DataFrame
        Table containing observed Economy, expected Economy, All-Runs RCAE,
        Legal Economy, and Legal-Ball RCAE.
    """
    cohort_df = df[df["is_primary_pressure_cohort"]].copy() if filter_primary_cohort else df.copy()
    prep = prepare_bowler_delivery_attributes(cohort_df)

    # Context partitioning: format x phase x wickets bucket
    prep["wkt_bucket"] = pd.cut(
        prep["wickets_remaining_before"],
        bins=[-1, 3, 6, 11],
        labels=["0-3 wkts", "4-6 wkts", "7-10 wkts"],
    )
    context_keys = ["competition_type", "innings_phase", "wkt_bucket"]

    # 1. Legal-ball only grid (for secondary diagnostic: Legal-Ball RCAE)
    legal_prep = prep[prep["is_legal_bowler_ball"]].copy()
    grid_legal = legal_prep.groupby(context_keys, observed=False)["bowler_runs_conceded"].mean().reset_index()
    grid_legal = grid_legal.rename(columns={"bowler_runs_conceded": "exp_legal_runs_per_ball"})

    # 2. All-runs grid (for primary metric: All-Runs RCAE / Standard Economy context delta)
    # Expected bowler-conceded runs (including wides/no-balls, excluding byes/leg-byes/penalty) per legal ball
    cell_grp = prep.groupby(context_keys, observed=False)
    cell_runs = cell_grp["bowler_runs_conceded"].sum().reset_index()
    cell_legal = cell_grp["is_legal_bowler_ball"].sum().reset_index()
    grid_all = cell_runs.merge(cell_legal, on=context_keys)
    grid_all["exp_all_runs_per_legal_ball"] = np.where(
        grid_all["is_legal_bowler_ball"] > 0,
        grid_all["bowler_runs_conceded"] / grid_all["is_legal_bowler_ball"],
        np.nan,
    )

    # Filter to pressure deliveries
    p_df = prep[prep["is_bowler_pressure"]].copy()
    if len(p_df) == 0:
        return pd.DataFrame()

    # Total bowler runs (including wides/no-balls) under pressure
    all_grp = p_df.groupby(["bowler_id", "bowler_name"])
    tot_conceded = all_grp["bowler_runs_conceded"].sum()

    # Legal deliveries under pressure
    p_legal = p_df[p_df["is_legal_bowler_ball"]].copy()
    p_legal = p_legal.merge(grid_legal, on=context_keys, how="left")
    p_legal = p_legal.merge(grid_all[context_keys + ["exp_all_runs_per_legal_ball"]], on=context_keys, how="left")

    legal_grp = p_legal.groupby(["bowler_id", "bowler_name"])
    legal_balls = legal_grp["is_legal_bowler_ball"].sum()
    legal_runs = legal_grp["bowler_runs_conceded"].sum()
    exp_legal_runs = legal_grp["exp_legal_runs_per_ball"].sum()
    exp_all_runs = legal_grp["exp_all_runs_per_legal_ball"].sum()

    res = pd.DataFrame(
        {
            "pressure_legal_balls": legal_balls,
            "pressure_total_runs_conceded": tot_conceded,
            "pressure_legal_runs_conceded": legal_runs,
            "expected_all_runs_conceded": exp_all_runs,
            "expected_legal_runs_conceded": exp_legal_runs,
        }
    ).reset_index()

    res["pressure_legal_balls"] = res["pressure_legal_balls"].fillna(0).astype(int)
    res = res[res["pressure_legal_balls"] > 0].copy()

    # 1. Primary Metric: All-Runs RCAE (Δ Economy)
    res["observed_pressure_econ"] = (res["pressure_total_runs_conceded"] * 6.0) / res["pressure_legal_balls"]
    res["expected_pressure_econ"] = (res["expected_all_runs_conceded"] * 6.0) / res["pressure_legal_balls"]
    res["all_runs_rcae_delta_econ"] = res["observed_pressure_econ"] - res["expected_pressure_econ"]
    # Maintain context_adjusted_delta_econ as primary All-Runs RCAE for backwards compatibility
    res["context_adjusted_delta_econ"] = res["all_runs_rcae_delta_econ"]

    # 2. Secondary Diagnostic Metric: Legal-Ball RCAE (Δ Legal Economy)
    res["observed_legal_econ"] = (res["pressure_legal_runs_conceded"] * 6.0) / res["pressure_legal_balls"]
    res["expected_legal_econ"] = (res["expected_legal_runs_conceded"] * 6.0) / res["pressure_legal_balls"]
    res["legal_context_delta_econ"] = res["observed_legal_econ"] - res["expected_legal_econ"]
    res["legal_rcae_delta_econ"] = res["legal_context_delta_econ"]

    # Backward-compatible column aliases
    res["pressure_runs_conceded"] = res["pressure_total_runs_conceded"]
    res["expected_runs_conceded"] = res["expected_all_runs_conceded"]
    res["runs_conceded_above_expected"] = res["pressure_total_runs_conceded"] - res["expected_all_runs_conceded"]

    if min_legal_balls > 0:
        res = res[res["pressure_legal_balls"] >= min_legal_balls].copy()

    return res.sort_values("context_adjusted_delta_econ", ascending=True).reset_index(drop=True)


def build_bowler_stratified_metrics(
    df: pd.DataFrame,
    stratify_by: str = "competition_type",
    filter_primary_cohort: bool = True,
    min_balls: int = 12,
) -> pd.DataFrame:
    """Build bowler metrics stratified by competition format, phase, or bowling type.

    Parameters
    ----------
    df : pd.DataFrame
        Pressure deliveries dataset.
    stratify_by : str, optional
        'competition_type' or 'innings_phase'.
    filter_primary_cohort : bool, optional
        Filter primary cohort (default: True).
    min_balls : int, optional
        Minimum legal balls in segment (default: 12).

    Returns
    -------
    pd.DataFrame
        Stratified summary table.
    """
    cohort_df = df[df["is_primary_pressure_cohort"]].copy() if filter_primary_cohort else df.copy()
    cohort_df = prepare_bowler_delivery_attributes(cohort_df)

    records: List[pd.DataFrame] = []
    for stratum, grp in cohort_df.groupby(stratify_by):
        seg_summary = aggregate_bowler_segment(grp, prefix=f"{stratum}_")
        p_grp = grp[grp["is_bowler_pressure"]]
        if len(p_grp) > 0:
            p_summary = aggregate_bowler_segment(p_grp, prefix=f"{stratum}_pressure_")
            seg_summary = seg_summary.merge(
                p_summary.drop(columns=["bowler_name"], errors="ignore"),
                on="bowler_id",
                how="left",
            )
        n_grp = grp[grp["is_bowler_normal"]]
        if len(n_grp) > 0:
            n_summary = aggregate_bowler_segment(n_grp, prefix=f"{stratum}_normal_")
            seg_summary = seg_summary.merge(
                n_summary.drop(columns=["bowler_name"], errors="ignore"),
                on="bowler_id",
                how="left",
            )
        # Compute within-stratum context-controlled delta economy
        p_econ_col = f"{stratum}_pressure_economy_rate"
        n_econ_col = f"{stratum}_normal_economy_rate"
        if p_econ_col in seg_summary.columns and n_econ_col in seg_summary.columns:
            seg_summary[f"{stratum}_delta_economy"] = (
                seg_summary[p_econ_col] - seg_summary[n_econ_col]
            )
        records.append(seg_summary)

    if len(records) == 0:
        return pd.DataFrame()

    out_df = records[0]
    for r in records[1:]:
        out_df = out_df.merge(r, on=["bowler_id", "bowler_name"], how="outer")

    return out_df

