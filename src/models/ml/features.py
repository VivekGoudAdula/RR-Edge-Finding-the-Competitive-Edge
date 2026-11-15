"""
Feature Extraction and Leakage Prevention Pipeline for RR EDGE ML.

Guarantees:
- Strict Pre-Delivery Temporal Boundary: Only match state preceding the delivery is extracted.
- Zero Target Leakage: Target columns and post-delivery indicators are explicitly barred.
- Zero Player Shortcut Cheat: Player IDs and names are never provided to feature matrices.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import (
    BATTER_FEATURE_COLS,
    BOWLER_FEATURE_COLS,
    CATEGORICAL_COLS,
    NUMERICAL_IMPUTATION_VALUES,
    PROHIBITED_FEATURE_COLS,
)


def compute_bowler_runs_conceded(df: pd.DataFrame) -> np.ndarray:
    """Compute bowler-conceded runs per delivery following exact cricket semantics.

    - Wides, No-Balls (Overstep), and other bowler extras: charged to bowler.
    - Batsman runs: charged to bowler.
    - Byes, Leg-byes, and Penalty runs: EXCLUDED from bowler runs.
    """
    extras_series = df["extras_type"].values
    tot_runs = df["total_delivery_runs"].values
    bat_runs = df["runs"].values

    bowler_runs = np.zeros(len(df), dtype=np.int64)
    for i, et in enumerate(extras_series):
        if et in ("byes", "legbyes", "Penalty"):
            bowler_runs[i] = 0
        elif et in ("wide", "Overstep", "other"):
            bowler_runs[i] = int(tot_runs[i])
        else:
            bowler_runs[i] = int(bat_runs[i])
    return bowler_runs


def assert_zero_leakage(feature_df: pd.DataFrame, prohibited_cols: Optional[List[str]] = None) -> None:
    """Validate that feature DataFrame contains zero leaked or prohibited columns."""
    if prohibited_cols is None:
        prohibited_cols = PROHIBITED_FEATURE_COLS

    leaked = [col for col in prohibited_cols if col in feature_df.columns]
    if leaked:
        raise ValueError(f"CRITICAL LEAKAGE DETECTED: Features contain prohibited columns: {leaked}")


def extract_batter_dataset(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Extract clean batter feature matrix, target (runs off bat), and metadata.

    Population: Deliveries faced by batter (exclude wides, include no-balls and legal balls).
    Filters to primary pressure cohort.
    """
    # Exclude wides because batter does not face a wide in cricket laws
    is_wide = df_raw["extras_type"].fillna("").astype(str).str.lower() == "wide"
    cohort_mask = df_raw["is_primary_pressure_cohort"] & (~is_wide)

    df = df_raw[cohort_mask].copy()

    # Pre-delivery feature preparation
    features = pd.DataFrame(index=df.index)
    features["competition_type"] = df["competition_type"].astype(str)
    features["innings"] = df["innings"].astype(int)
    features["innings_phase"] = df["innings_phase"].astype(str)
    features["is_knockout"] = df["is_knockout"].fillna(False).astype(int)
    features["over_num"] = df["overid"].astype(int)
    features["batting_order"] = df["batting_order_raw"].fillna(5).astype(int)

    # Resource State Before Delivery
    features["legal_balls_bowled"] = df["legal_balls_bowled_before"].fillna(0).astype(int)
    features["balls_remaining"] = df["balls_remaining_before"].fillna(120).astype(int)
    features["current_score"] = df["current_score_before"].fillna(0).astype(int)
    features["wickets_lost"] = df["wickets_lost_before"].fillna(0).astype(int)
    features["wickets_remaining"] = df["wickets_remaining_before"].fillna(10).astype(int)
    features["current_run_rate"] = df["current_run_rate_before"].fillna(7.5).astype(float)

    # Dynamics & Pressure
    features["target_runs"] = df["innings_target"].fillna(NUMERICAL_IMPUTATION_VALUES["target_runs"]).astype(float)
    features["required_run_rate"] = df["batter_required_run_rate"].fillna(NUMERICAL_IMPUTATION_VALUES["required_run_rate"]).astype(float)
    features["delta_rrr"] = df["batter_delta_rrr"].fillna(NUMERICAL_IMPUTATION_VALUES["delta_rrr"]).astype(float)
    features["par_deficit"] = df["batter_first_innings_par_deficit"].fillna(NUMERICAL_IMPUTATION_VALUES["par_deficit"]).astype(float)
    features["batter_pressure_tier"] = df["batter_pressure_tier"].fillna("MODERATE").astype(str)

    # Recent Momentum (Previous 6 balls)
    features["prev_6_runs"] = df["batter_prev_6_runs"].fillna(NUMERICAL_IMPUTATION_VALUES["prev_6_runs"]).astype(float)
    features["prev_6_dots"] = df["batter_prev_6_dots"].fillna(NUMERICAL_IMPUTATION_VALUES["prev_6_dots"]).astype(float)
    features["prev_6_wickets"] = df["batter_prev_6_wickets"].fillna(NUMERICAL_IMPUTATION_VALUES["prev_6_wickets"]).astype(float)

    # Target: Off-bat runs scored on this delivery
    target = df["runs"].astype(float)

    # Metadata (for grouping, evaluation, audit tracing)
    metadata = df[[
        "match_id", "season", "match_date", "competition_type",
        "striker_id", "striker_name", "bowler_id", "bowler_name",
        "innings_phase", "batter_pressure_tier"
    ]].copy()

    # Ensure zero leakage
    assert_zero_leakage(features)

    return features, target, metadata


def extract_bowler_dataset(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series, pd.DataFrame]:
    """Extract clean bowler feature matrix, regression target (runs conceded),
    classification target (is_bowler_wkt), and metadata.

    Population: All deliveries in primary pressure cohort.
    """
    cohort_mask = df_raw["is_primary_pressure_cohort"].copy()
    df = df_raw[cohort_mask].copy()

    # Compute exact bowler runs conceded
    df["bowler_runs_conceded"] = compute_bowler_runs_conceded(df)

    # Pre-delivery feature preparation
    features = pd.DataFrame(index=df.index)
    features["competition_type"] = df["competition_type"].astype(str)
    features["innings"] = df["innings"].astype(int)
    features["innings_phase"] = df["innings_phase"].astype(str)
    features["is_knockout"] = df["is_knockout"].fillna(False).astype(int)
    features["over_num"] = df["overid"].astype(int)

    # Resource State Before Delivery
    features["legal_balls_bowled"] = df["legal_balls_bowled_before"].fillna(0).astype(int)
    features["balls_remaining"] = df["balls_remaining_before"].fillna(120).astype(int)
    features["current_score"] = df["current_score_before"].fillna(0).astype(int)
    features["wickets_lost"] = df["wickets_lost_before"].fillna(0).astype(int)
    features["wickets_remaining"] = df["wickets_remaining_before"].fillna(10).astype(int)
    features["current_run_rate"] = df["current_run_rate_before"].fillna(7.5).astype(float)

    # Dynamics & Pressure
    features["runs_to_defend"] = df["bowler_runs_to_defend"].fillna(NUMERICAL_IMPUTATION_VALUES["runs_to_defend"]).astype(float)
    features["required_run_rate"] = df["bowler_required_run_rate"].fillna(NUMERICAL_IMPUTATION_VALUES["required_run_rate"]).astype(float)
    features["expected_scoring_rate"] = df["bowler_expected_scoring_rate"].fillna(NUMERICAL_IMPUTATION_VALUES["expected_scoring_rate"]).astype(float)
    features["par_deficit"] = df["par_deficit"].fillna(NUMERICAL_IMPUTATION_VALUES["par_deficit"]).astype(float)
    features["bowler_pressure_tier"] = df["bowler_pressure_tier"].fillna("MODERATE").astype(str)
    features["bowler_resource_context"] = df["bowler_batting_resource_context"].fillna("MIDDLE_ORDER").astype(str)

    # Recent Momentum (Previous 6 balls)
    features["prev_6_runs"] = df["bowler_prev_6_runs"].fillna(NUMERICAL_IMPUTATION_VALUES["prev_6_runs"]).astype(float)
    features["prev_6_dots"] = df["bowler_prev_6_dots"].fillna(NUMERICAL_IMPUTATION_VALUES["prev_6_dots"]).astype(float)
    features["prev_6_wickets"] = df["bowler_prev_6_wickets"].fillna(NUMERICAL_IMPUTATION_VALUES["prev_6_wickets"]).astype(float)

    # Targets
    target_runs = df["bowler_runs_conceded"].astype(float)
    target_wicket = df["is_bowler_wkt"].astype(int)

    # Metadata
    metadata = df[[
        "match_id", "season", "match_date", "competition_type",
        "striker_id", "striker_name", "bowler_id", "bowler_name",
        "innings_phase", "bowler_pressure_tier", "is_legal_ball"
    ]].copy()

    # Ensure zero leakage
    assert_zero_leakage(features)

    return features, target_runs, target_wicket, metadata

