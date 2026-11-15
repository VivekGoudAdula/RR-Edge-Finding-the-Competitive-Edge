"""
Configuration and schemas for RR EDGE Supervised Machine Learning Pipeline.

Defines:
- Chronological match split thresholds
- Target definitions and population filters
- Feature schemas with strict leakage controls
- Algorithm hyperparameters and random seeds
- File path conventions
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any

# Root directories
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
ML_DIR = PROCESSED_DIR / "ml"
ML_MODELS_DIR = ML_DIR / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"

RANDOM_SEED = 42

# Chronological split definitions (Strict Match-Grouped Out-of-Time Splits)
# Train: 2022 to 2024 (Seasons 2022, 2022/23, 2023, 2023/24, 2024, 2024/25) -> ~60% matches
# Validation: 2025 -> ~23% matches
# Holdout Test: 2026 -> ~17% matches
TRAIN_SEASONS = ["2022", "2022/23", "2023", "2023/24", "2024", "2024/25"]
VAL_SEASONS = ["2025"]
TEST_SEASONS = ["2026"]

# Feature Definitions
BATTER_FEATURE_COLS = [
    # Match & Format Context
    "competition_type",
    "innings",
    "innings_phase",
    "is_knockout",
    "over_num",
    "batting_order",
    # Resource State Before Delivery
    "legal_balls_bowled",
    "balls_remaining",
    "current_score",
    "wickets_lost",
    "wickets_remaining",
    "current_run_rate",
    # Match Dynamics / Pressure Context
    "target_runs",
    "required_run_rate",
    "delta_rrr",
    "par_deficit",
    "batter_pressure_tier",
    # Recent Momentum (Trailing 6 legal balls)
    "prev_6_runs",
    "prev_6_dots",
    "prev_6_wickets",
]

BOWLER_FEATURE_COLS = [
    # Match & Format Context
    "competition_type",
    "innings",
    "innings_phase",
    "is_knockout",
    "over_num",
    # Resource State Before Delivery
    "legal_balls_bowled",
    "balls_remaining",
    "current_score",
    "wickets_lost",
    "wickets_remaining",
    "current_run_rate",
    # Match Dynamics / Pressure Context
    "runs_to_defend",
    "required_run_rate",
    "expected_scoring_rate",
    "par_deficit",
    "bowler_pressure_tier",
    "bowler_resource_context",
    # Recent Momentum (Trailing 6 legal balls)
    "prev_6_runs",
    "prev_6_dots",
    "prev_6_wickets",
]

CATEGORICAL_COLS = [
    "competition_type",
    "innings_phase",
    "batter_pressure_tier",
    "bowler_pressure_tier",
    "bowler_resource_context",
]

NUMERICAL_IMPUTATION_VALUES = {
    "target_runs": 0.0,
    "required_run_rate": 0.0,
    "delta_rrr": 0.0,
    "par_deficit": 0.0,
    "runs_to_defend": 0.0,
    "expected_scoring_rate": 8.0,
    "prev_6_runs": 7.5,
    "prev_6_dots": 2.0,
    "prev_6_wickets": 0.0,
}

# Strict Anti-Leakage Prohibited Columns
PROHIBITED_FEATURE_COLS = [
    # Post-delivery target variables
    "runs",
    "batsman_runs",
    "total_delivery_runs",
    "bowler_runs_conceded",
    "is_wicket",
    "is_bowler_wkt",
    "dismissal_type",
    "dismissed_player_id",
    # Post-delivery delivery attributes
    "is_legal_ball",
    "extras_type",
    # Individual player identifiers (prevent memorization / shortcut cheating)
    "striker_id",
    "striker_name",
    "non_striker_id",
    "non_striker_name",
    "bowler_id",
    "bowler_name",
    # Post-match / final outcome information
    "final_score",
    "winner",
    "margin",
]

