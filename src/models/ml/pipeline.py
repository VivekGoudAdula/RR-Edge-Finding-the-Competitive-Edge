"""
End-to-End Orchestrator for RR EDGE Supervised Machine Learning Pipeline.

Orchestrates:
1. Data loading and feature extraction with leakage assertions.
2. Chronological match-grouped split partitioning.
3. Training and validation of Batter Expected Runs Regressors.
4. Training and validation of Bowler Conceded Runs Regressors.
5. Training and validation of Bowler Wicket Probability Classifiers.
6. Generation and export of metrics, manifest, feature importance, and test sample predictions.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any
import numpy as np
import pandas as pd
import lightgbm as lgb
import xgboost as xgb

from .config import (
    PROJECT_ROOT,
    PROCESSED_DIR,
    ML_DIR,
    ML_MODELS_DIR,
    RANDOM_SEED,
    TRAIN_SEASONS,
    VAL_SEASONS,
    TEST_SEASONS,
    BATTER_FEATURE_COLS,
    BOWLER_FEATURE_COLS,
)
from .features import (
    extract_batter_dataset,
    extract_bowler_dataset,
    assert_zero_leakage,
)
from .splitting import generate_match_grouped_splits
from .train_batter import train_batter_models
from .train_bowler import train_bowler_models


def run_ml_pipeline() -> Dict[str, Any]:
    """Execute complete reproducible ML training and validation pipeline."""
    start_time = time.time()
    print("=" * 70)
    print("  RR EDGE SUPERVISED MACHINE LEARNING TRAINING PIPELINE")
    print("=" * 70)

    ML_DIR.mkdir(parents=True, exist_ok=True)
    ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Processed Deliveries
    data_path = PROCESSED_DIR / "pressure_deliveries.parquet"
    if not data_path.exists():
        raise FileNotFoundError(f"Missing required dataset: {data_path}")

    print(f"\n[1/6] Loading delivery dataset: {data_path} ...")
    df_raw = pd.read_parquet(data_path)
    print(f"      Total deliveries loaded: {len(df_raw):,}")

    # 2. Extract Batter Features & Target
    print("\n[2/6] Extracting Batter Features and Target (Off-Bat Runs) ...")
    bat_X, bat_y, bat_meta = extract_batter_dataset(df_raw)
    print(f"      Batter population: {len(bat_X):,} balls faced in primary cohort.")
    assert_zero_leakage(bat_X)

    # 3. Extract Bowler Features & Targets
    print("\n[3/6] Extracting Bowler Features and Targets (Conceded Runs & Wickets) ...")
    bowl_X, bowl_y_runs, bowl_y_wkt, bowl_meta = extract_bowler_dataset(df_raw)
    print(f"      Bowler population: {len(bowl_X):,} deliveries in primary cohort.")
    assert_zero_leakage(bowl_X)

    # 4. Generate Chronological Match-Grouped Splits
    print("\n[4/6] Generating Match-Grouped Chronological Partitions ...")
    bat_train_idx, bat_val_idx, bat_test_idx, bat_manifest = generate_match_grouped_splits(bat_meta)
    bowl_train_idx, bowl_val_idx, bowl_test_idx, bowl_manifest = generate_match_grouped_splits(bowl_meta)

    print(f"      Train Set: {bat_manifest['train']['matches']} matches ({bat_manifest['train']['deliveries']:,} balls) [2022-2024]")
    print(f"      Val Set:   {bat_manifest['validation']['matches']} matches ({bat_manifest['validation']['deliveries']:,} balls) [2025]")
    print(f"      Test Set:  {bat_manifest['test']['matches']} matches ({bat_manifest['test']['deliveries']:,} balls) [2026]")

    # Save Split Manifest
    with open(ML_DIR / "split_manifest.json", "w", encoding="utf-8") as f:
        json.dump(bat_manifest, f, indent=2)

    # 5. Train Batter Models
    print("\n[5/6] Training Batter Expected Runs Regressors ...")
    bat_results, bat_importance, bat_test_preds = train_batter_models(
        X_train=bat_X.iloc[bat_train_idx],
        y_train=bat_y.iloc[bat_train_idx],
        meta_train=bat_meta.iloc[bat_train_idx],
        X_val=bat_X.iloc[bat_val_idx],
        y_val=bat_y.iloc[bat_val_idx],
        meta_val=bat_meta.iloc[bat_val_idx],
        X_test=bat_X.iloc[bat_test_idx],
        y_test=bat_y.iloc[bat_test_idx],
        meta_test=bat_meta.iloc[bat_test_idx],
    )

    # 6. Train Bowler Models
    print("\n[6/6] Training Bowler Performance Models (Runs & Wicket Probability) ...")
    bowl_runs_results, bowl_wkt_results, bowl_runs_importance, bowl_wkt_extra = train_bowler_models(
        X_train=bowl_X.iloc[bowl_train_idx],
        y_train_runs=bowl_y_runs.iloc[bowl_train_idx],
        y_train_wkt=bowl_y_wkt.iloc[bowl_train_idx],
        meta_train=bowl_meta.iloc[bowl_train_idx],
        X_val=bowl_X.iloc[bowl_val_idx],
        y_val_runs=bowl_y_runs.iloc[bowl_val_idx],
        y_val_wkt=bowl_y_wkt.iloc[bowl_val_idx],
        meta_val=bowl_meta.iloc[bowl_val_idx],
        X_test=bowl_X.iloc[bowl_test_idx],
        y_test_runs=bowl_y_runs.iloc[bowl_test_idx],
        y_test_wkt=bowl_y_wkt.iloc[bowl_test_idx],
        meta_test=bowl_meta.iloc[bowl_test_idx],
    )

    # Generate Sample Test Predictions for Inspection & Frontend
    test_meta = bat_meta.iloc[bat_test_idx].copy().reset_index(drop=True)
    test_meta["actual_runs"] = bat_y.iloc[bat_test_idx].values
    test_meta["pred_dummy"] = np.round(bat_test_preds["dummy_mean"], 3)
    test_meta["pred_context_grid"] = np.round(bat_test_preds["context_grid"], 3)
    test_meta["pred_ridge"] = np.round(bat_test_preds["ridge"], 3)
    test_meta["pred_lightgbm"] = np.round(bat_test_preds["lightgbm"], 3)
    test_meta["pred_xgboost"] = np.round(bat_test_preds["xgboost"], 3)
    test_meta["residual_lightgbm"] = np.round(test_meta["actual_runs"] - test_meta["pred_lightgbm"], 3)

    sample_preds = test_meta.head(50).to_dict(orient="records")
    test_meta.to_parquet(ML_DIR / "batter_test_predictions.parquet", index=False)

    elapsed_time = round(time.time() - start_time, 2)
    print(f"\nTraining pipeline completed successfully in {elapsed_time}s.")

    # Assemble Complete Validation Report Data
    summary_report = {
        "metadata": {
            "pipeline_name": "RR EDGE Supervised Machine Learning Intelligence Pipeline",
            "version": "1.0.0",
            "random_seed": RANDOM_SEED,
            "trained_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "training_duration_seconds": elapsed_time,
            "libraries": {
                "lightgbm": lgb.__version__,
                "xgboost": xgb.__version__,
                "scikit-learn": "1.6.1",
            },
            "split_architecture": "Chronological Match-Grouped (Train: 2022-2024, Val: 2025, Test: 2026)",
            "split_manifest": bat_manifest,
        },
        "models": {
            "batter_expected_runs": {
                "target": "runs (off-bat runs per faced delivery)",
                "features": BATTER_FEATURE_COLS,
                "results": bat_results,
                "feature_importance": bat_importance,
                "champion_model": "lightgbm",
            },
            "bowler_expected_runs": {
                "target": "bowler_runs_conceded (runs conceded per delivery)",
                "features": BOWLER_FEATURE_COLS,
                "results": bowl_runs_results,
                "feature_importance": bowl_runs_importance,
                "champion_model": "lightgbm",
            },
            "bowler_wicket_probability": {
                "target": "is_bowler_wkt (binary bowler-credited wicket)",
                "features": BOWLER_FEATURE_COLS,
                "results": bowl_wkt_results,
                "feature_importance": bowl_wkt_extra["wkt_importance"],
                "calibration": bowl_wkt_extra["calibration"],
                "champion_model": "lightgbm",
            },
        },
        "sample_predictions": sample_preds,
    }

    with open(ML_DIR / "ml_evaluation_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)

    return summary_report


if __name__ == "__main__":
    run_ml_pipeline()
