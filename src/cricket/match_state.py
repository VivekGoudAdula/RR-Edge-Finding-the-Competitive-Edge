"""
Match-state reconstruction engine for RR EDGE.

Phase 1.2: Guarantees strict group-wise pre-delivery state reconstruction:
1. All shifts occur strictly inside (match_id, innings) groups.
2. Zero leakage across innings or matches.
3. Preserves raw batting order (no clamping).
4. Innings-specific scheduled ball resolution (distinguishing 120 balls vs DLS revised balls vs Super Overs).
5. Explicit target reconstruction with DLS timing certainty flags.
"""

from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

from src.cricket.semantics import (
    is_legal_delivery,
    is_bowler_wicket,
    is_batter_dismissal,
    get_match_phase,
)


def resolve_scheduled_balls(
    innings: int,
    first_inn_revised_overs: Optional[float] = None,
    second_inn_revised_overs: Optional[float] = None,
    result_text: Optional[str] = None,
) -> int:
    """Resolve scheduled legal balls for a specific innings.

    Units Note:
    In matches.csv, `first_inn_revised_overs` and `second_inn_revised_overs`
    are recorded in legal balls (e.g. 90.0 = 15 overs, 48.0 = 8 overs).
    Innings 1 and Innings 2 can have DIFFERENT scheduled lengths (e.g. match 36208
    scheduled 54 balls for Inn 1 and 30 balls for Inn 2).

    Parameters
    ----------
    innings : int
        Innings index (1, 2, 3, 4).
    first_inn_revised_overs : float, optional
        Scheduled legal balls for innings 1 from matches.csv.
    second_inn_revised_overs : float, optional
        Scheduled legal balls for innings 2 from matches.csv.
    result_text : str, optional
        Match result string for context.

    Returns
    -------
    int
        Scheduled legal deliveries (120 for standard T20, 6 for Super Over,
        or DLS scheduled balls).
    """
    # Super overs are strictly 1 over = 6 legal balls
    if innings in {3, 4}:
        return 6

    # Innings 1: check first_inn_revised_overs
    if innings == 1:
        if pd.notna(first_inn_revised_overs) and first_inn_revised_overs > 0:
            return int(first_inn_revised_overs)
        return 120

    # Innings 2: check second_inn_revised_overs
    if innings == 2:
        if pd.notna(second_inn_revised_overs) and second_inn_revised_overs > 0:
            return int(second_inn_revised_overs)
        return 120

    return 120


def reconstruct_match_state(
    bbb_df: pd.DataFrame,
    matches_df: pd.DataFrame,
) -> pd.DataFrame:
    """Reconstruct delivery-level match state strictly before each delivery.

    Calculates:
    - total_delivery_runs = runs + extras1_runs + extras_2_runs
    - current_score_before (inside-group shift)
    - wickets_lost_before (inside-group shift)
    - wickets_remaining_before (10 - wickets_lost_before)
    - legal_balls_bowled_before (inside-group shift)
    - balls_remaining_before
    - innings_target (target to chase)
    - target_certainty ('CERTAIN' vs 'UNCERTAIN_DLS_TIMING')
    - required_runs_before
    - required_run_rate_before
    - current_run_rate_before

    Parameters
    ----------
    bbb_df : pd.DataFrame
        Raw or filtered ball_by_ball DataFrame.
    matches_df : pd.DataFrame
        Raw matches DataFrame containing match_id, revised_target, revised overs.

    Returns
    -------
    pd.DataFrame
        DataFrame with pre-delivery match state features appended.
    """
    df = bbb_df.copy()

    # Ensure deterministic sort order
    df = df.sort_values(["match_id", "innings", "innings_ball_num"]).reset_index(drop=True)

    # 1. Base delivery attributes
    df["total_delivery_runs"] = df["runs"] + df["extras1_runs"] + df["extras_2_runs"]
    df["is_legal_ball"] = df["extras_type"].apply(is_legal_delivery)
    df["is_bowler_wkt"] = [
        is_bowler_wicket(w, dt) for w, dt in zip(df["is_wicket"], df["dismissal_type"])
    ]
    df["is_batter_out"] = df["is_wicket"].astype(bool)

    # 2. Preserve raw batting order and player identifiers (NEVER clamped)
    df["batting_order_raw"] = df["batting_order"]

    # 3. Inside-group shift for cumulative features (GUARANTEES zero cross-group leakage)
    # Using groupby.transform with lambda ensures s.cumsum().shift(1) is computed
    # independently within each (match_id, innings) Series.
    group_key = ["match_id", "innings"]

    df["current_score_before"] = df.groupby(group_key)["total_delivery_runs"].transform(
        lambda s: s.cumsum().shift(1, fill_value=0)
    ).astype(int)

    df["wickets_lost_before"] = df.groupby(group_key)["is_wicket"].transform(
        lambda s: s.astype(int).cumsum().shift(1, fill_value=0)
    ).astype(int)

    df["wickets_remaining_before"] = 10 - df["wickets_lost_before"]

    df["legal_balls_bowled_before"] = df.groupby(group_key)["is_legal_ball"].transform(
        lambda s: s.astype(int).cumsum().shift(1, fill_value=0)
    ).astype(int)

    # 4. Merge match-level context for target and scheduled balls
    match_cols = [
        "match_id",
        "revised_target",
        "first_inn_revised_overs",
        "second_inn_revised_overs",
        "result",
    ]
    avail_cols = [c for c in match_cols if c in matches_df.columns]
    match_subset = matches_df[avail_cols].drop_duplicates("match_id")
    df = df.merge(match_subset, on="match_id", how="left")

    # 5. Resolve scheduled balls per delivery
    df["scheduled_innings_balls"] = [
        resolve_scheduled_balls(inn, rev1, rev2, res)
        for inn, rev1, rev2, res in zip(
            df["innings"],
            df["first_inn_revised_overs"],
            df["second_inn_revised_overs"],
            df["result"],
        )
    ]

    df["balls_remaining_before"] = np.maximum(
        0, df["scheduled_innings_balls"] - df["legal_balls_bowled_before"]
    )

    # 6. Calculate completed 1st innings total runs per match
    inn1_totals = (
        df[df["innings"] == 1]
        .groupby("match_id")["total_delivery_runs"]
        .sum()
        .rename("inn1_total_runs")
    )
    df = df.merge(inn1_totals, on="match_id", how="left")

    # Super over inn 3 total for inn 4 chase
    inn3_totals = (
        df[df["innings"] == 3]
        .groupby("match_id")["total_delivery_runs"]
        .sum()
        .rename("inn3_total_runs")
    )
    df = df.merge(inn3_totals, on="match_id", how="left")

    # 7. Target reconstruction hierarchy & certainty classification
    targets = []
    certainties = []
    for inn, rev_t, inn1_tot, inn3_tot in zip(
        df["innings"],
        df["revised_target"],
        df["inn1_total_runs"],
        df["inn3_total_runs"],
    ):
        if inn in {1, 3}:
            targets.append(np.nan)
            certainties.append("NOT_APPLICABLE")
        elif inn == 4:
            targets.append(float(inn3_tot + 1) if pd.notna(inn3_tot) else np.nan)
            certainties.append("CERTAIN")
        elif inn == 2:
            if pd.notna(rev_t) and rev_t > 0:
                targets.append(float(rev_t))
                # Explicitly documented limitation: delivery-level revision timing unknown
                certainties.append("UNCERTAIN_DLS_TIMING")
            elif pd.notna(inn1_tot):
                targets.append(float(inn1_tot + 1))
                certainties.append("CERTAIN")
            else:
                targets.append(np.nan)
                certainties.append("UNKNOWN")
        else:
            targets.append(np.nan)
            certainties.append("UNKNOWN")

    df["innings_target"] = targets
    df["target_certainty"] = certainties

    # 8. Required runs and rates
    df["required_runs_before"] = np.where(
        df["innings_target"].notna(),
        np.maximum(0, df["innings_target"] - df["current_score_before"]),
        np.nan,
    )
    # Backward compatibility alias
    df["runs_required_before"] = df["required_runs_before"]

    # Required run rate = required_runs / (balls_remaining / 6)
    overs_remaining = df["balls_remaining_before"] / 6.0
    df["required_run_rate_before"] = np.where(
        (df["innings_target"].notna()) & (overs_remaining > 0),
        df["required_runs_before"] / overs_remaining,
        np.where((df["innings_target"].notna()) & (overs_remaining == 0), np.nan, np.nan),
    )

    # Current run rate = current_score / (balls_bowled / 6)
    overs_bowled = df["legal_balls_bowled_before"] / 6.0
    df["current_run_rate_before"] = np.where(
        overs_bowled > 0,
        df["current_score_before"] / overs_bowled,
        0.0,
    )

    # Innings phase
    df["innings_phase"] = df["overid"].apply(get_match_phase)

    return df

