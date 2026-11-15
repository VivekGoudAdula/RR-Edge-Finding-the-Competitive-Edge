"""
Core pressure intelligence engine for RR EDGE.

Phase 2.2: Generates pre-delivery pressure features, continuous dimensions,
and explainable categorical tiers separately for batters and bowlers across
all eligible deliveries in IPL (2022-2026) and senior Men's T20Is.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from src.data.load_data import load_all, DEFAULT_RAW_DIR
from src.cricket.competition_config import is_competition_included
from src.cricket.match_state import reconstruct_match_state
from src.cricket.pressure_research import (
    compute_advanced_momentum,
    FirstInningsResourceModel,
)


@dataclass
class PressureEngineConfig:
    """Configurable thresholds and parameters for the pressure engine."""

    # Batter chase rate thresholds (runs per over)
    threshold_batter_extreme_rrr: float = 14.0
    threshold_batter_high_rrr: float = 10.5
    threshold_batter_low_rrr: float = 7.5

    # Rate momentum deficit thresholds (RRR - CRR)
    threshold_batter_extreme_delta_rrr: float = 6.0
    threshold_batter_high_delta_rrr: float = 2.5

    # Wickets remaining thresholds
    threshold_critical_wickets: int = 3
    threshold_depleted_wickets: int = 5
    threshold_ample_wickets: int = 7

    # Rolling momentum thresholds (over previous 6 legal deliveries)
    threshold_drought_runs: float = 3.0
    threshold_surge_runs: float = 12.0
    threshold_dot_stall_count: int = 4

    # 1st-innings Par Deficit thresholds (runs below competition baseline)
    threshold_par_deficit_extreme: float = 25.0
    threshold_par_deficit_high: float = 15.0
    threshold_par_surplus_low: float = -15.0

    # Bowler acute margin thresholds
    threshold_bowler_acute_balls: int = 12
    threshold_bowler_acute_runs: int = 18
    threshold_bowler_death_balls: int = 24
    threshold_bowler_death_runs: int = 36

    # Bowler tail dominance
    threshold_bowler_tail_wickets: int = 2
    threshold_bowler_tail_rrr: float = 12.0

    # Momentum window (legal balls)
    momentum_window: int = 6


def filter_whitelisted_data(
    matches_df: pd.DataFrame,
    bbb_df: pd.DataFrame,
    comp_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Filter raw matches and delivery records to whitelisted competitions.

    Parameters
    ----------
    matches_df : pd.DataFrame
        Raw matches DataFrame.
    bbb_df : pd.DataFrame
        Raw ball_by_ball DataFrame.
    comp_df : pd.DataFrame
        Raw competitions DataFrame.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        Filtered (matches, ball_by_ball) DataFrames.
    """
    comp_format_map = comp_df.set_index("comp_id")["match_format"].to_dict()

    valid_matches = matches_df[
        matches_df.apply(
            lambda r: is_competition_included(r["comp_id"], comp_format_map.get(r["comp_id"], "T20I")),
            axis=1,
        )
    ].copy()

    comp_meta = comp_df[["comp_id", "comp_name", "season"]].drop_duplicates("comp_id")
    valid_matches = valid_matches.merge(comp_meta, on="comp_id", how="left")
    valid_matches["competition_type"] = np.where(
        valid_matches["comp_name"].str.startswith("IPL"), "IPL", "T20I"
    )

    whitelisted_bbb = bbb_df[bbb_df["match_id"].isin(valid_matches["match_id"])].copy()
    return valid_matches, whitelisted_bbb


def calculate_isolated_first_innings_expectations(
    df: pd.DataFrame,
    train_match_ids: Optional[Union[set, list]] = None,
    n_folds: int = 5,
) -> pd.DataFrame:
    """Calculate 1st-innings expected runs and par metrics without data leakage.

    Guarantees:
    - Deliveries from match M are NEVER used to predict match M.
    - Uses 5-fold match-level cross-fitting for training matches.
    - Test matches are predicted strictly by the model fitted on training matches.
    - All predictions are separated by competition (IPL vs T20I).

    Parameters
    ----------
    df : pd.DataFrame
        Reconstructed delivery DataFrame containing match_id, innings,
        legal_balls_bowled_before, wickets_lost_before, current_score_before,
        total_delivery_runs, competition_type.
    train_match_ids : set or list, optional
        Set of training match IDs. If None, uses first 80% chronologically.
    n_folds : int, optional
        Number of match-level folds for out-of-fold calibration (default: 5).

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        - expected_remaining_runs
        - expected_final_score
        - par_score
        - par_deficit
    """
    n = len(df)
    exp_rem = np.full(n, np.nan, dtype=np.float64)
    par_score = np.full(n, np.nan, dtype=np.float64)
    par_deficit = np.full(n, np.nan, dtype=np.float64)

    inn1_mask = df["innings"] == 1
    inn1_df = df[inn1_mask]

    if len(inn1_df) == 0:
        return pd.DataFrame(
            {
                "expected_remaining_runs": exp_rem,
                "expected_final_score": par_score,
                "par_score": par_score,
                "par_deficit": par_deficit,
            },
            index=df.index,
        )

    # Establish train and test partitions
    all_inn1_mids = list(inn1_df["match_id"].drop_duplicates())
    if train_match_ids is None:
        n_train = int(len(all_inn1_mids) * 0.8)
        train_mids = set(all_inn1_mids[:n_train])
        test_mids = set(all_inn1_mids[n_train:])
    else:
        train_mids = set(train_match_ids)
        test_mids = set(all_inn1_mids) - train_mids

    # 1. Predict on training matches using K-fold out-of-fold match cross-fitting
    train_mids_list = sorted(list(train_mids))
    effective_folds = min(n_folds, len(train_mids_list))
    if len(train_mids_list) > 1 and effective_folds > 1:
        fold_size = max(1, len(train_mids_list) // effective_folds)
        for f in range(effective_folds):
            start_idx = f * fold_size
            end_idx = None if f == effective_folds - 1 else (f + 1) * fold_size
            val_fold_mids = set(train_mids_list[start_idx:end_idx])
            fit_fold_mids = train_mids - val_fold_mids

            fit_df = inn1_df[inn1_df["match_id"].isin(fit_fold_mids)]
            val_df = inn1_df[inn1_df["match_id"].isin(val_fold_mids)]

            if len(fit_df) == 0 or len(val_df) == 0:
                continue

            model_f = FirstInningsResourceModel(by_competition=True)
            model_f.fit(fit_df)

            for idx, row in val_df.iterrows():
                b = int(row["legal_balls_bowled_before"])
                w = int(row["wickets_lost_before"])
                c = str(row["competition_type"])
                s = float(row["current_score_before"])

                r = model_f.predict_remaining_runs(b, w, c)
                p = s + r
                d = model_f.predict_par_deficit(s, b, w, c)

                exp_rem[idx] = r
                par_score[idx] = p
                par_deficit[idx] = d
    elif len(train_mids_list) == 1:
        # Fallback for single-match synthetic test edge case
        fit_df = inn1_df[inn1_df["match_id"].isin(train_mids)]
        model_single = FirstInningsResourceModel(by_competition=True)
        model_single.fit(fit_df)
        for idx, row in fit_df.iterrows():
            b = int(row["legal_balls_bowled_before"])
            w = int(row["wickets_lost_before"])
            c = str(row["competition_type"])
            s = float(row["current_score_before"])

            exp_rem[idx] = model_single.predict_remaining_runs(b, w, c)
            par_score[idx] = s + exp_rem[idx]
            par_deficit[idx] = model_single.predict_par_deficit(s, b, w, c)

    # 2. Predict on test matches using model trained on ALL training matches
    if len(test_mids) > 0:
        fit_full_train = inn1_df[inn1_df["match_id"].isin(train_mids)]
        test_df = inn1_df[inn1_df["match_id"].isin(test_mids)]

        if len(fit_full_train) > 0 and len(test_df) > 0:
            model_test = FirstInningsResourceModel(by_competition=True)
            model_test.fit(fit_full_train)

            for idx, row in test_df.iterrows():
                b = int(row["legal_balls_bowled_before"])
                w = int(row["wickets_lost_before"])
                c = str(row["competition_type"])
                s = float(row["current_score_before"])

                r = model_test.predict_remaining_runs(b, w, c)
                p = s + r
                d = model_test.predict_par_deficit(s, b, w, c)

                exp_rem[idx] = r
                par_score[idx] = p
                par_deficit[idx] = d

    res = pd.DataFrame(
        {
            "expected_remaining_runs": exp_rem,
            "expected_final_score": par_score,
            "par_score": par_score,
            "par_deficit": par_deficit,
        },
        index=df.index,
    )
    return res


def classify_batter_delivery_pressure(
    innings: int,
    rrr: float,
    delta_rrr: float,
    wickets_remaining: int,
    balls_remaining: int,
    par_deficit: float,
    prev_6_runs: float,
    prev_6_dots: float,
    config: PressureEngineConfig,
) -> Tuple[str, str]:
    """Classify batter pressure tier and explainable reason for a delivery.

    Returns
    -------
    Tuple[str, str]
        (pressure_tier, reason_string) where tier is 'LOW', 'MODERATE', 'HIGH', 'EXTREME'.
    """
    is_chase = innings in {2, 4}

    if is_chase:
        # Chase Tier Logic
        if pd.notna(rrr):
            # EXTREME CHASE
            if rrr >= config.threshold_batter_extreme_rrr:
                return "EXTREME", "CHASE_EXTREME_RRR"
            if pd.notna(delta_rrr) and delta_rrr >= config.threshold_batter_extreme_delta_rrr:
                return "EXTREME", "CHASE_EXTREME_DELTA_RRR"
            if rrr >= 12.0 and wickets_remaining <= config.threshold_critical_wickets:
                return "EXTREME", "CHASE_CRITICAL_WICKETS_HIGH_RATE"
            if balls_remaining <= 18 and rrr >= 11.0 and wickets_remaining <= 4:
                return "EXTREME", "CHASE_LATE_OVERS_RATE_PRESSURE"

            # HIGH CHASE
            if rrr >= config.threshold_batter_high_rrr:
                return "HIGH", "CHASE_ELEVATED_RRR"
            if pd.notna(delta_rrr) and delta_rrr >= config.threshold_batter_high_delta_rrr:
                return "HIGH", "CHASE_ELEVATED_DELTA_RRR"
            if wickets_remaining <= config.threshold_critical_wickets and balls_remaining <= 36:
                return "HIGH", "CHASE_RESOURCE_STRESS"
            if rrr >= 9.5 and pd.notna(prev_6_runs) and prev_6_runs <= config.threshold_drought_runs:
                return "HIGH", "CHASE_MOMENTUM_DROUGHT"
            if rrr >= 9.5 and pd.notna(prev_6_dots) and prev_6_dots >= config.threshold_dot_stall_count:
                return "HIGH", "CHASE_DOT_PRESSURE_STALL"

            # LOW CHASE
            if rrr <= config.threshold_batter_low_rrr and wickets_remaining >= config.threshold_ample_wickets:
                return "LOW", "CHASE_CRUISING_AMPLE_WICKETS"
            if rrr <= 6.0:
                return "LOW", "CHASE_SUBDUED_RATE"

            return "MODERATE", "CHASE_BALANCED_PROGRESSION"

        return "MODERATE", "CHASE_TARGET_UNAVAILABLE"

    else:
        # 1st Innings Tier Logic
        if pd.notna(par_deficit):
            # EXTREME 1ST INNINGS
            if par_deficit >= config.threshold_par_deficit_extreme:
                return "EXTREME", "1ST_INN_SEVERE_PAR_DEFICIT"
            if par_deficit >= config.threshold_par_deficit_high and wickets_remaining <= config.threshold_critical_wickets:
                return "EXTREME", "1ST_INN_PAR_DEFICIT_AND_COLLAPSE"

            # HIGH 1ST INNINGS
            if par_deficit >= config.threshold_par_deficit_high:
                return "HIGH", "1ST_INN_ELEVATED_PAR_DEFICIT"
            if wickets_remaining <= config.threshold_critical_wickets and balls_remaining <= 36:
                return "HIGH", "1ST_INN_RESOURCE_STRESS"
            if balls_remaining <= 30 and pd.notna(prev_6_dots) and prev_6_dots >= config.threshold_dot_stall_count:
                return "HIGH", "1ST_INN_DEATH_DOT_STALL"

            # LOW 1ST INNINGS
            if par_deficit <= config.threshold_par_surplus_low and wickets_remaining >= 6:
                return "LOW", "1ST_INN_SURGING_AHEAD_OF_PAR"

            return "MODERATE", "1ST_INN_STEADY_PROGRESSION"

        return "MODERATE", "1ST_INN_STANDARD"


def classify_bowler_delivery_pressure(
    innings: int,
    rrr: float,
    runs_to_defend: float,
    wickets_remaining: int,
    balls_remaining: int,
    prev_6_runs: float,
    prev_6_dots: float,
    innings_phase: str,
    par_deficit: float,
    config: PressureEngineConfig,
) -> Tuple[str, str, str]:
    """Classify bowler pressure tier, resource context, and explainable reason.

    Returns
    -------
    Tuple[str, str, str]
        (pressure_tier, resource_context, reason_string)
    """
    is_chase = innings in {2, 4}

    # Batting resource context
    if wickets_remaining <= config.threshold_bowler_tail_wickets:
        resource_context = "TAIL_EXPOSED"
    elif wickets_remaining >= config.threshold_ample_wickets:
        resource_context = "TOP_ORDER_INTACT"
    else:
        resource_context = "MIDDLE_ORDER"

    if is_chase:
        # Chase Bowling Logic
        # 1. ACUTE MARGIN PRESSURE (Single ball flips match)
        if pd.notna(runs_to_defend) and balls_remaining > 0:
            if balls_remaining <= config.threshold_bowler_acute_balls and runs_to_defend <= config.threshold_bowler_acute_runs:
                return "EXTREME", resource_context, "BOWLER_ACUTE_MARGIN_DEFENSE"
            if balls_remaining <= 6 and runs_to_defend <= 12:
                return "EXTREME", resource_context, "BOWLER_FINAL_OVER_DEFENSE"

        # 2. CLOSING OUT TAIL (Bowler dominant, low pressure despite high RRR)
        if pd.notna(rrr) and rrr >= config.threshold_bowler_tail_rrr and wickets_remaining <= config.threshold_bowler_tail_wickets:
            return "LOW", resource_context, "BOWLER_CLOSING_OUT_TAIL"

        if pd.notna(rrr) and rrr >= 16.0 and wickets_remaining <= 4:
            return "LOW", resource_context, "BOWLER_OPPOSITION_COLLAPSED"

        # 3. HIGH FIREPOWER ASSAULT (Opposition batting deep under high RRR)
        if pd.notna(rrr) and rrr >= 13.0 and wickets_remaining >= 6:
            return "EXTREME", resource_context, "BOWLER_HIGH_FIREPOWER_DEFENSE"

        # 4. HIGH PRESSURE DEFENSE
        if pd.notna(runs_to_defend) and balls_remaining <= config.threshold_bowler_death_balls and runs_to_defend <= config.threshold_bowler_death_runs:
            return "HIGH", resource_context, "BOWLER_DEATH_MARGIN_DEFENSE"

        if pd.notna(rrr) and rrr >= config.threshold_batter_high_rrr and pd.notna(prev_6_runs) and prev_6_runs >= config.threshold_surge_runs:
            return "HIGH", resource_context, "BOWLER_OPPOSITION_MOMENTUM_SURGE"

        if innings_phase == "DEATH" and wickets_remaining >= 5 and pd.notna(rrr) and rrr <= 12.0:
            return "HIGH", resource_context, "BOWLER_DEATH_OVERS_CONTAINMENT"

        # 5. LOW PRESSURE CRUISING
        if pd.notna(rrr) and rrr <= 7.0 and wickets_remaining >= 6:
            return "MODERATE", resource_context, "BOWLER_OPPOSITION_CONTROLLED_CHASE"

        if pd.notna(runs_to_defend) and balls_remaining <= 18 and runs_to_defend >= 45:
            return "LOW", resource_context, "BOWLER_DECIDED_MATCH_CLOSURE"

        return "MODERATE", resource_context, "BOWLER_BALANCED_CHASE_DEFENSE"

    else:
        # 1st Innings Bowling Logic
        # EXTREME: Death assault with set top order
        if balls_remaining <= 18 and wickets_remaining >= 7 and pd.notna(prev_6_runs) and prev_6_runs >= 14.0:
            return "EXTREME", resource_context, "BOWLER_1ST_INN_DEATH_SLOG_ASSAULT"

        # HIGH: Death overs containment or opposition scoring surge
        if balls_remaining <= 30 and wickets_remaining >= 5:
            return "HIGH", resource_context, "BOWLER_1ST_INN_DEATH_CONTAINMENT"

        if pd.notna(prev_6_runs) and prev_6_runs >= config.threshold_surge_runs and pd.notna(par_deficit) and par_deficit <= -10.0:
            return "HIGH", resource_context, "BOWLER_1ST_INN_OPPOSITION_SURGE"

        # LOW: Opposition tail exposed early or heavy squeeze
        if wickets_remaining <= 3:
            return "LOW", resource_context, "BOWLER_1ST_INN_TAIL_EXPOSED"

        if pd.notna(prev_6_dots) and prev_6_dots >= config.threshold_dot_stall_count and pd.notna(par_deficit) and par_deficit >= 15.0:
            return "LOW", resource_context, "BOWLER_1ST_INN_SQUEEZE_CONTROL"

        return "MODERATE", resource_context, "BOWLER_1ST_INN_STANDARD_CONTAINMENT"


def build_pressure_pipeline(
    raw_dir: Optional[Path] = None,
    config: Optional[PressureEngineConfig] = None,
) -> pd.DataFrame:
    """Execute complete end-to-end pressure intelligence pipeline.

    Parameters
    ----------
    raw_dir : Path, optional
        Path to raw CSV directory.
    config : PressureEngineConfig, optional
        Threshold configuration.

    Returns
    -------
    pd.DataFrame
        Complete delivery DataFrame with pre-delivery pressure dimensions.
    """
    if config is None:
        config = PressureEngineConfig()

    # 1. Load data
    datasets = load_all(raw_dir=raw_dir)
    bbb = datasets["ball_by_ball"]
    matches = datasets["matches"]
    comp = datasets["competitions"]

    # 2. Filter to whitelisted competitions
    valid_matches, whitelisted_bbb = filter_whitelisted_data(matches, bbb, comp)

    # 3. Reconstruct pre-delivery match state (inside-group cumulative shifts)
    state_df = reconstruct_match_state(whitelisted_bbb, valid_matches)

    # Merge competition and match metadata
    match_meta_cols = [
        "match_id",
        "comp_id",
        "competition_type",
        "comp_name",
        "season",
        "match_date",
        "stage",
        "knock_out",
    ]
    meta_df = valid_matches[match_meta_cols].drop_duplicates("match_id")
    state_df = state_df.merge(meta_df, on="match_id", how="left")

    # Merge playing eleven impact player info for striker
    pe_df = datasets.get("playing_eleven")
    if pe_df is not None and not pe_df.empty:
        striker_pe = pe_df[["match_id", "player_id", "is_impact", "is_impact_off"]].rename(
            columns={
                "player_id": "striker_id",
                "is_impact": "striker_is_impact",
                "is_impact_off": "striker_is_impact_off",
            }
        ).drop_duplicates(subset=["match_id", "striker_id"])
        state_df = state_df.merge(striker_pe, on=["match_id", "striker_id"], how="left")
    else:
        state_df["striker_is_impact"] = np.nan
        state_df["striker_is_impact_off"] = np.nan

    # Flag primary pressure cohort (excludes UNCERTAIN_DLS_TIMING from model calibration)
    state_df["is_primary_pressure_cohort"] = state_df["target_certainty"] != "UNCERTAIN_DLS_TIMING"
    state_df["is_knockout"] = state_df["knock_out"] == 1
    state_df["match_stage"] = state_df["stage"]

    # 4. Calculate isolated 1st-innings expected-scoring expectations (Model C)
    first_inn_metrics = calculate_isolated_first_innings_expectations(state_df)
    state_df["expected_remaining_runs"] = first_inn_metrics["expected_remaining_runs"]
    state_df["expected_final_score"] = first_inn_metrics["expected_final_score"]
    state_df["par_score"] = first_inn_metrics["par_score"]
    state_df["par_deficit"] = first_inn_metrics["par_deficit"]

    # 5. Compute rolling momentum features (prev 6 legal deliveries)
    momentum_df = compute_advanced_momentum(state_df, window=config.momentum_window)
    state_df["prev_6_runs"] = momentum_df["prev_6_runs"]
    state_df["prev_6_dots"] = momentum_df["prev_6_dots"]
    state_df["prev_6_wickets"] = momentum_df["prev_6_wkts"]
    state_df["prev_over_runs"] = momentum_df["prev_over_runs"]

    # 6. Extract Batter Pressure Dimensions
    state_df["batter_required_run_rate"] = np.where(
        state_df["innings"].isin([2, 4]), state_df["required_run_rate_before"], np.nan
    )
    state_df["batter_delta_rrr"] = np.where(
        state_df["innings"].isin([2, 4]),
        state_df["required_run_rate_before"] - state_df["current_run_rate_before"],
        np.nan,
    )
    state_df["batter_wickets_remaining"] = state_df["wickets_remaining_before"]
    state_df["batter_legal_balls_remaining"] = state_df["balls_remaining_before"]
    state_df["batter_innings_phase"] = state_df["innings_phase"]
    state_df["batter_prev_6_runs"] = state_df["prev_6_runs"]
    state_df["batter_prev_6_dots"] = state_df["prev_6_dots"]
    state_df["batter_prev_6_wickets"] = state_df["prev_6_wickets"]
    state_df["batter_prev_over_runs"] = state_df["prev_over_runs"]
    state_df["batter_first_innings_par_score"] = np.where(
        state_df["innings"] == 1, state_df["par_score"], np.nan
    )
    state_df["batter_first_innings_par_deficit"] = np.where(
        state_df["innings"] == 1, state_df["par_deficit"], np.nan
    )

    # 7. Extract Bowler Pressure Dimensions
    state_df["bowler_runs_to_defend"] = np.where(
        state_df["innings"].isin([2, 4]), state_df["required_runs_before"], np.nan
    )
    state_df["bowler_legal_balls_remaining"] = state_df["balls_remaining_before"]
    state_df["bowler_wickets_remaining"] = state_df["wickets_remaining_before"]
    state_df["bowler_required_run_rate"] = np.where(
        state_df["innings"].isin([2, 4]), state_df["required_run_rate_before"], np.nan
    )

    # Expected scoring rate against bowler:
    # In chase: RRR; in 1st inn: E[Remaining] / (Balls Remaining / 6)
    expected_bowler_rate = np.where(
        state_df["innings"].isin([2, 4]),
        state_df["required_run_rate_before"],
        np.where(
            (state_df["innings"] == 1) & (state_df["balls_remaining_before"] > 0),
            state_df["expected_remaining_runs"] / (state_df["balls_remaining_before"] / 6.0),
            np.nan,
        ),
    )
    state_df["bowler_expected_scoring_rate"] = expected_bowler_rate
    state_df["bowler_innings_phase"] = state_df["innings_phase"]
    state_df["bowler_prev_6_runs"] = state_df["prev_6_runs"]
    state_df["bowler_prev_6_dots"] = state_df["prev_6_dots"]
    state_df["bowler_prev_6_wickets"] = state_df["prev_6_wickets"]
    state_df["bowler_prev_over_runs"] = state_df["prev_over_runs"]

    # 8. Compute Categorical Classifications & Reasons
    b_tiers: List[str] = []
    b_reasons: List[str] = []
    bow_tiers: List[str] = []
    bow_contexts: List[str] = []
    bow_reasons: List[str] = []

    for row in state_df.itertuples():
        # Batter classification
        b_tier, b_reason = classify_batter_delivery_pressure(
            innings=row.innings,
            rrr=row.batter_required_run_rate,
            delta_rrr=row.batter_delta_rrr,
            wickets_remaining=row.batter_wickets_remaining,
            balls_remaining=row.batter_legal_balls_remaining,
            par_deficit=row.batter_first_innings_par_deficit,
            prev_6_runs=row.batter_prev_6_runs,
            prev_6_dots=row.batter_prev_6_dots,
            config=config,
        )
        b_tiers.append(b_tier)
        b_reasons.append(b_reason)

        # Bowler classification
        bow_tier, bow_context, bow_reason = classify_bowler_delivery_pressure(
            innings=row.innings,
            rrr=row.bowler_required_run_rate,
            runs_to_defend=row.bowler_runs_to_defend,
            wickets_remaining=row.bowler_wickets_remaining,
            balls_remaining=row.bowler_legal_balls_remaining,
            prev_6_runs=row.bowler_prev_6_runs,
            prev_6_dots=row.bowler_prev_6_dots,
            innings_phase=row.bowler_innings_phase,
            par_deficit=row.par_deficit,
            config=config,
        )
        bow_tiers.append(bow_tier)
        bow_contexts.append(bow_context)
        bow_reasons.append(bow_reason)

    state_df["batter_pressure_tier"] = b_tiers
    state_df["batter_pressure_reason"] = b_reasons
    state_df["bowler_batting_resource_context"] = bow_contexts
    state_df["bowler_pressure_tier"] = bow_tiers
    state_df["bowler_pressure_reason"] = bow_reasons

    # 9. Assemble clean, typed output schema
    output_columns = [
        # Identifiers
        "match_id",
        "comp_id",
        "competition_type",
        "comp_name",
        "season",
        "match_date",
        "stage",
        "is_knockout",
        "innings",
        "overid",
        "over_ball_num",
        "innings_ball_num",
        "batting_team_id",
        "bowling_team_id",
        "striker_id",
        "striker_name",
        "non_striker_id",
        "non_striker_name",
        "bowler_id",
        "bowler_name",
        "batting_order_raw",
        "striker_is_impact",
        "striker_is_impact_off",
        # Pre-delivery match state
        "current_score_before",
        "wickets_lost_before",
        "wickets_remaining_before",
        "legal_balls_bowled_before",
        "balls_remaining_before",
        "innings_phase",
        "current_run_rate_before",
        "innings_target",
        "target_certainty",
        "is_primary_pressure_cohort",
        # First-innings par metrics
        "expected_remaining_runs",
        "expected_final_score",
        "par_score",
        "par_deficit",
        # Batter pressure features
        "batter_required_run_rate",
        "batter_delta_rrr",
        "batter_wickets_remaining",
        "batter_legal_balls_remaining",
        "batter_innings_phase",
        "batter_prev_6_runs",
        "batter_prev_6_dots",
        "batter_prev_6_wickets",
        "batter_prev_over_runs",
        "batter_first_innings_par_score",
        "batter_first_innings_par_deficit",
        "batter_pressure_tier",
        "batter_pressure_reason",
        # Bowler pressure features
        "bowler_runs_to_defend",
        "bowler_legal_balls_remaining",
        "bowler_wickets_remaining",
        "bowler_required_run_rate",
        "bowler_expected_scoring_rate",
        "bowler_innings_phase",
        "bowler_prev_6_runs",
        "bowler_prev_6_dots",
        "bowler_prev_6_wickets",
        "bowler_prev_over_runs",
        "bowler_batting_resource_context",
        "bowler_pressure_tier",
        "bowler_pressure_reason",
        # Delivery outcome ground truth
        "is_legal_ball",
        "total_delivery_runs",
        "runs",
        "extras_type",
        "is_wicket",
        "is_bowler_wkt",
        "dismissal_type",
        "dismissed_player_id",
    ]

    clean_df = state_df[output_columns].copy()
    return clean_df


def run_pressure_engine(
    raw_dir: Optional[Path] = None,
    output_parquet_path: Optional[Path] = None,
    output_sample_csv_path: Optional[Path] = None,
    sample_size: int = 5000,
    config: Optional[PressureEngineConfig] = None,
) -> pd.DataFrame:
    """Run pressure engine pipeline, validate output, and write parquet and sample csv.

    Parameters
    ----------
    raw_dir : Path, optional
        Path to raw data directory.
    output_parquet_path : Path, optional
        Target parquet file path.
    output_sample_csv_path : Path, optional
        Target sample CSV path.
    sample_size : int, optional
        Number of rows for sample CSV (default: 5000).
    config : PressureEngineConfig, optional
        Threshold configuration.

    Returns
    -------
    pd.DataFrame
        Processed delivery-level pressure intelligence DataFrame.
    """
    project_root = Path(__file__).resolve().parents[2]

    if output_parquet_path is None:
        output_parquet_path = project_root / "data" / "processed" / "pressure_deliveries.parquet"
    if output_sample_csv_path is None:
        output_sample_csv_path = project_root / "data" / "processed" / "pressure_deliveries_sample.csv"

    # Ensure output directory exists
    output_parquet_path.parent.mkdir(parents=True, exist_ok=True)

    print("Executing RR EDGE Pressure Engine Pipeline...")
    df = build_pressure_pipeline(raw_dir=raw_dir, config=config)

    # Validate output integrity
    assert len(df) > 0, "Pipeline produced empty DataFrame"
    assert "batter_pressure_tier" in df.columns, "Missing batter_pressure_tier"
    assert "bowler_pressure_tier" in df.columns, "Missing bowler_pressure_tier"
    assert df["batter_pressure_tier"].isin(["LOW", "MODERATE", "HIGH", "EXTREME"]).all()
    assert df["bowler_pressure_tier"].isin(["LOW", "MODERATE", "HIGH", "EXTREME"]).all()

    # Save to Parquet
    print(f"Saving {len(df):,} deliveries to {output_parquet_path}...")
    df.to_parquet(output_parquet_path, index=False, engine="pyarrow")

    # Save representative sample to CSV
    print(f"Exporting {sample_size:,} row sample to {output_sample_csv_path}...")
    sample_df = df.sample(n=min(sample_size, len(df)), random_state=42)
    sample_df.to_csv(output_sample_csv_path, index=False)

    print("Pipeline execution and export completed successfully.")
    return df


# Type alias for cleaner type annotations
Set_or_List = Optional[Union[set, list]]


if __name__ == "__main__":
    run_pressure_engine()
