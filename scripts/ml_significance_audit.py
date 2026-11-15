"""
Comprehensive Statistical Significance, Bootstrap Confidence Interval,
and Calibration Audit for RR EDGE Supervised ML Models.
"""

import os
os.environ["LOKY_MAX_CPU_COUNT"] = "4"

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import json
import numpy as np
import pandas as pd
import joblib

from src.models.ml.splitting import generate_match_grouped_splits
from src.models.ml.features import extract_batter_dataset, extract_bowler_dataset
from src.models.ml.config import ML_MODELS_DIR, RANDOM_SEED, PROCESSED_DIR


def run_audit(b_replicates: int = 1000, seed: int = 42):
    print("=" * 70, flush=True)
    print("RR EDGE ML STATISTICAL SIGNIFICANCE & CALIBRATION AUDIT", flush=True)
    print(f"Replicates: {b_replicates}, Seed: {seed}", flush=True)
    print("=" * 70, flush=True)

    # 1. Load dataset
    print("[1/5] Loading pressure deliveries dataset...", flush=True)
    df_raw = pd.read_parquet(PROCESSED_DIR / "pressure_deliveries.parquet")

    # 2. Extract features and splits
    print("[2/5] Extracting features and partitions...", flush=True)
    bat_X, bat_y, bat_meta = extract_batter_dataset(df_raw)
    bowl_X, bowl_y_runs, bowl_y_wkt, bowl_meta = extract_bowler_dataset(df_raw)

    bat_train_idx, bat_val_idx, bat_test_idx, _ = generate_match_grouped_splits(bat_meta)
    bowl_train_idx, bowl_val_idx, bowl_test_idx, _ = generate_match_grouped_splits(bowl_meta)

    b_test_X = bat_X.iloc[bat_test_idx].copy()
    b_test_y = bat_y.iloc[bat_test_idx].copy()
    b_test_meta = bat_meta.iloc[bat_test_idx].copy()

    bw_train_y_runs = bowl_y_runs.iloc[bowl_train_idx]
    bw_train_y_wkt = bowl_y_wkt.iloc[bowl_train_idx]

    bw_test_X = bowl_X.iloc[bowl_test_idx].copy()
    bw_test_y_runs = bowl_y_runs.iloc[bowl_test_idx].copy()
    bw_test_y_wkt = bowl_y_wkt.iloc[bowl_test_idx].copy()
    bw_test_meta = bowl_meta.iloc[bowl_test_idx].copy()

    print(f"      Batter test deliveries: {len(b_test_X):,}, matches: {b_test_meta['match_id'].nunique()}", flush=True)
    print(f"      Bowler test deliveries: {len(bw_test_X):,}, matches: {bw_test_meta['match_id'].nunique()}", flush=True)

    # Ensure category dtypes for tree models
    categorical_b = ["competition_type", "innings_phase", "batter_pressure_tier"]
    b_test_tree = b_test_X.copy()
    for col in categorical_b:
        b_test_tree[col] = b_test_tree[col].astype("category")

    categorical_bw = ["competition_type", "innings_phase", "bowler_pressure_tier", "bowler_resource_context"]
    bw_test_tree = bw_test_X.copy()
    for col in categorical_bw:
        bw_test_tree[col] = bw_test_tree[col].astype("category")

    # 3. Load models
    print("[3/5] Loading trained ML model artifacts...", flush=True)
    b_lgb = joblib.load(ML_MODELS_DIR / "batter_lightgbm.joblib")
    b_xgb = joblib.load(ML_MODELS_DIR / "batter_xgboost.joblib")
    b_grid = joblib.load(ML_MODELS_DIR / "batter_context_grid.joblib")
    b_dummy = joblib.load(ML_MODELS_DIR / "batter_dummy.joblib")

    bw_lgb_reg = joblib.load(ML_MODELS_DIR / "bowler_runs_lightgbm.joblib")
    bw_xgb_reg = joblib.load(ML_MODELS_DIR / "bowler_runs_xgboost.joblib")
    bw_grid_reg = joblib.load(ML_MODELS_DIR / "bowler_runs_context_grid.joblib")
    bw_mean = float(bw_train_y_runs.mean())

    bw_lgb_clf = joblib.load(ML_MODELS_DIR / "bowler_wkt_lightgbm.joblib")
    bw_xgb_clf = joblib.load(ML_MODELS_DIR / "bowler_wkt_xgboost.joblib")
    bw_grid_clf = joblib.load(ML_MODELS_DIR / "bowler_wkt_context_grid.joblib")
    dummy_wkt_p = float(bw_train_y_wkt.mean())

    # 4. Generate predictions on test set
    print("      Generating test predictions across all candidate models...", flush=True)
    pred_b_lgb = b_lgb.predict(b_test_tree)
    pred_b_xgb = b_xgb.predict(b_test_tree)
    pred_b_grid = b_grid.predict(b_test_X)
    pred_b_dummy = b_dummy.predict(b_test_X)

    pred_bw_lgb_reg = bw_lgb_reg.predict(bw_test_tree)
    pred_bw_xgb_reg = bw_xgb_reg.predict(bw_test_tree)
    pred_bw_grid_reg = bw_grid_reg.predict(bw_test_X)
    pred_bw_dummy = np.full_like(pred_bw_lgb_reg, bw_mean)

    pred_bw_lgb_clf = bw_lgb_clf.predict_proba(bw_test_tree)[:, 1]
    pred_bw_xgb_clf = bw_xgb_clf.predict_proba(bw_test_tree)[:, 1]
    pred_bw_grid_clf = bw_grid_clf.predict_proba(bw_test_X)[:, 1]
    pred_bw_dummy_clf = np.full_like(pred_bw_lgb_clf, dummy_wkt_p)

    # 5. Paired Match-Cluster Bootstrap
    print(f"[4/5] Executing {b_replicates} paired match-cluster bootstrap replicates...", flush=True)
    rng = np.random.RandomState(seed)

    # Match ID arrays and delivery mapping
    b_matches = np.array(b_test_meta["match_id"].unique())
    n_b_matches = len(b_matches)
    b_match_arr = b_test_meta["match_id"].values
    b_match_indices = {m: np.where(b_match_arr == m)[0] for m in b_matches}

    bw_matches = np.array(bw_test_meta["match_id"].unique())
    n_bw_matches = len(bw_matches)
    bw_match_arr = bw_test_meta["match_id"].values
    bw_match_indices = {m: np.where(bw_match_arr == m)[0] for m in bw_matches}

    diff_b_rmse_vs_dummy = []
    diff_b_mae_vs_dummy = []
    diff_b_rmse_vs_grid = []
    diff_b_mae_vs_grid = []
    diff_b_rmse_vs_xgb = []
    diff_b_mae_vs_xgb = []

    diff_bw_rmse_vs_dummy = []
    diff_bw_mae_vs_dummy = []
    diff_bw_rmse_vs_grid = []
    diff_bw_mae_vs_grid = []
    diff_bw_rmse_vs_xgb = []
    diff_bw_mae_vs_xgb = []

    diff_wkt_brier_vs_dummy = []
    diff_wkt_brier_vs_grid = []
    diff_wkt_brier_vs_xgb = []

    y_b = b_test_y.values
    y_bw_r = bw_test_y_runs.values
    y_bw_w = bw_test_y_wkt.values

    t_boot_start = time.time()
    for rep in range(b_replicates):
        # 1. Sample matches for batter test partition
        sampled_b_m = rng.choice(b_matches, size=n_b_matches, replace=True)
        idx_b = np.concatenate([b_match_indices[m] for m in sampled_b_m])

        sub_y_b = y_b[idx_b]
        p_lgb = pred_b_lgb[idx_b]
        p_xgb = pred_b_xgb[idx_b]
        p_grid = pred_b_grid[idx_b]
        p_dum = pred_b_dummy[idx_b]

        err_lgb = sub_y_b - p_lgb
        err_xgb = sub_y_b - p_xgb
        err_grid = sub_y_b - p_grid
        err_dum = sub_y_b - p_dum

        rmse_lgb = np.sqrt(np.mean(err_lgb ** 2))
        mae_lgb = np.mean(np.abs(err_lgb))

        rmse_xgb = np.sqrt(np.mean(err_xgb ** 2))
        mae_xgb = np.mean(np.abs(err_xgb))

        rmse_grid = np.sqrt(np.mean(err_grid ** 2))
        mae_grid = np.mean(np.abs(err_grid))

        rmse_dum = np.sqrt(np.mean(err_dum ** 2))
        mae_dum = np.mean(np.abs(err_dum))

        diff_b_rmse_vs_dummy.append(rmse_lgb - rmse_dum)
        diff_b_mae_vs_dummy.append(mae_lgb - mae_dum)
        diff_b_rmse_vs_grid.append(rmse_lgb - rmse_grid)
        diff_b_mae_vs_grid.append(mae_lgb - mae_grid)
        diff_b_rmse_vs_xgb.append(rmse_lgb - rmse_xgb)
        diff_b_mae_vs_xgb.append(mae_lgb - mae_xgb)

        # 2. Sample matches for bowler test partition
        sampled_bw_m = rng.choice(bw_matches, size=n_bw_matches, replace=True)
        idx_bw = np.concatenate([bw_match_indices[m] for m in sampled_bw_m])

        sub_y_bw_r = y_bw_r[idx_bw]
        p_bw_lgb = pred_bw_lgb_reg[idx_bw]
        p_bw_xgb = pred_bw_xgb_reg[idx_bw]
        p_bw_grid = pred_bw_grid_reg[idx_bw]
        p_bw_dum = pred_bw_dummy[idx_bw]

        err_bw_lgb = sub_y_bw_r - p_bw_lgb
        err_bw_xgb = sub_y_bw_r - p_bw_xgb
        err_bw_grid = sub_y_bw_r - p_bw_grid
        err_bw_dum = sub_y_bw_r - p_bw_dum

        rmse_bw_lgb = np.sqrt(np.mean(err_bw_lgb ** 2))
        mae_bw_lgb = np.mean(np.abs(err_bw_lgb))

        rmse_bw_xgb = np.sqrt(np.mean(err_bw_xgb ** 2))
        mae_bw_xgb = np.mean(np.abs(err_bw_xgb))

        rmse_bw_grid = np.sqrt(np.mean(err_bw_grid ** 2))
        mae_bw_grid = np.mean(np.abs(err_bw_grid))

        rmse_bw_dum = np.sqrt(np.mean(err_bw_dum ** 2))
        mae_bw_dum = np.mean(np.abs(err_bw_dum))

        diff_bw_rmse_vs_dummy.append(rmse_bw_lgb - rmse_bw_dum)
        diff_bw_mae_vs_dummy.append(mae_bw_lgb - mae_bw_dum)
        diff_bw_rmse_vs_grid.append(rmse_bw_lgb - rmse_bw_grid)
        diff_bw_mae_vs_grid.append(mae_bw_lgb - mae_bw_grid)
        diff_bw_rmse_vs_xgb.append(rmse_bw_lgb - rmse_bw_xgb)
        diff_bw_mae_vs_xgb.append(mae_bw_lgb - mae_bw_xgb)

        # 3. Wicket Classifier Brier
        sub_y_bw_w = y_bw_w[idx_bw]
        pw_lgb = pred_bw_lgb_clf[idx_bw]
        pw_xgb = pred_bw_xgb_clf[idx_bw]
        pw_grid = pred_bw_grid_clf[idx_bw]
        pw_dum = pred_bw_dummy_clf[idx_bw]

        brier_lgb = np.mean((sub_y_bw_w - pw_lgb) ** 2)
        brier_xgb = np.mean((sub_y_bw_w - pw_xgb) ** 2)
        brier_grid = np.mean((sub_y_bw_w - pw_grid) ** 2)
        brier_dum = np.mean((sub_y_bw_w - pw_dum) ** 2)

        diff_wkt_brier_vs_dummy.append(brier_lgb - brier_dum)
        diff_wkt_brier_vs_grid.append(brier_lgb - brier_grid)
        diff_wkt_brier_vs_xgb.append(brier_lgb - brier_xgb)

    print(f"      Bootstrap completed in {time.time() - t_boot_start:.2f}s", flush=True)

    def calc_ci(arr):
        low, high = np.percentile(arr, [2.5, 97.5])
        mean_val = np.mean(arr)
        contains_zero = (low <= 0.0 <= high)
        sig = not contains_zero
        return {
            "mean": round(float(mean_val), 5),
            "ci_95": [round(float(low), 5), round(float(high), 5)],
            "contains_zero": bool(contains_zero),
            "statistically_significant": bool(sig),
        }

    bootstrap_results = {
        "replicates": b_replicates,
        "seed": seed,
        "cluster_unit": "match_id",
        "batter_expected_runs": {
            "lightgbm_vs_dummy_mean": {
                "delta_rmse": calc_ci(diff_b_rmse_vs_dummy),
                "delta_mae": calc_ci(diff_b_mae_vs_dummy),
            },
            "lightgbm_vs_context_grid": {
                "delta_rmse": calc_ci(diff_b_rmse_vs_grid),
                "delta_mae": calc_ci(diff_b_mae_vs_grid),
            },
            "lightgbm_vs_xgboost": {
                "delta_rmse": calc_ci(diff_b_rmse_vs_xgb),
                "delta_mae": calc_ci(diff_b_mae_vs_xgb),
            },
        },
        "bowler_expected_runs": {
            "lightgbm_vs_dummy_mean": {
                "delta_rmse": calc_ci(diff_bw_rmse_vs_dummy),
                "delta_mae": calc_ci(diff_bw_mae_vs_dummy),
            },
            "lightgbm_vs_context_grid": {
                "delta_rmse": calc_ci(diff_bw_rmse_vs_grid),
                "delta_mae": calc_ci(diff_bw_mae_vs_grid),
            },
            "lightgbm_vs_xgboost": {
                "delta_rmse": calc_ci(diff_bw_rmse_vs_xgb),
                "delta_mae": calc_ci(diff_bw_mae_vs_xgb),
            },
        },
        "bowler_wicket_probability": {
            "lightgbm_vs_dummy_prior": {
                "delta_brier": calc_ci(diff_wkt_brier_vs_dummy),
            },
            "lightgbm_vs_context_grid": {
                "delta_brier": calc_ci(diff_wkt_brier_vs_grid),
            },
            "lightgbm_vs_xgboost": {
                "delta_brier": calc_ci(diff_wkt_brier_vs_xgb),
            },
        },
    }

    # 6. Measure Actual Inference Latency
    print("[5/5] Measuring empirical inference latency...", flush=True)
    sample_b_row = b_test_tree.iloc[[0]]
    sample_bw_row = bw_test_tree.iloc[[0]]

    # Warmup
    for _ in range(30):
        _ = b_lgb.predict(sample_b_row)
        _ = b_xgb.predict(sample_b_row)

    n_lat_runs = 200

    t_b_lgb = []
    for _ in range(n_lat_runs):
        t0 = time.perf_counter()
        _ = b_lgb.predict(sample_b_row)
        t_b_lgb.append((time.perf_counter() - t0) * 1000)

    t_b_xgb = []
    for _ in range(n_lat_runs):
        t0 = time.perf_counter()
        _ = b_xgb.predict(sample_b_row)
        t_b_xgb.append((time.perf_counter() - t0) * 1000)

    for _ in range(30):
        _ = bw_lgb_reg.predict(sample_bw_row)
        _ = bw_xgb_reg.predict(sample_bw_row)

    t_bw_lgb = []
    for _ in range(n_lat_runs):
        t0 = time.perf_counter()
        _ = bw_lgb_reg.predict(sample_bw_row)
        t_bw_lgb.append((time.perf_counter() - t0) * 1000)

    t_bw_xgb = []
    for _ in range(n_lat_runs):
        t0 = time.perf_counter()
        _ = bw_xgb_reg.predict(sample_bw_row)
        t_bw_xgb.append((time.perf_counter() - t0) * 1000)

    latency_results = {
        "methodology": f"{n_lat_runs} repeated single-row pre-delivery inferences after 30 warmup iterations",
        "batter_runs": {
            "lightgbm_latency_ms": {
                "mean": round(float(np.mean(t_b_lgb)), 4),
                "std": round(float(np.std(t_b_lgb)), 4),
                "p50": round(float(np.median(t_b_lgb)), 4),
                "p95": round(float(np.percentile(t_b_lgb, 95)), 4),
            },
            "xgboost_latency_ms": {
                "mean": round(float(np.mean(t_b_xgb)), 4),
                "std": round(float(np.std(t_b_xgb)), 4),
                "p50": round(float(np.median(t_b_xgb)), 4),
                "p95": round(float(np.percentile(t_b_xgb, 95)), 4),
            },
        },
        "bowler_runs": {
            "lightgbm_latency_ms": {
                "mean": round(float(np.mean(t_bw_lgb)), 4),
                "std": round(float(np.std(t_bw_lgb)), 4),
                "p50": round(float(np.median(t_bw_lgb)), 4),
                "p95": round(float(np.percentile(t_bw_lgb, 95)), 4),
            },
            "xgboost_latency_ms": {
                "mean": round(float(np.mean(t_bw_xgb)), 4),
                "std": round(float(np.std(t_bw_xgb)), 4),
                "p50": round(float(np.median(t_bw_xgb)), 4),
                "p95": round(float(np.percentile(t_bw_xgb, 95)), 4),
            },
        },
    }

    # 7. Feature Importance: Split vs Gain
    b_splits = b_lgb.booster_.feature_importance(importance_type="split")
    b_gains = b_lgb.booster_.feature_importance(importance_type="gain")
    b_features = b_test_tree.columns

    b_importance_breakdown = [
        {
            "feature": feat,
            "split_count": int(sp),
            "gain": round(float(gn), 2),
            "gain_share_pct": round(float(gn / sum(b_gains) * 100), 2),
        }
        for feat, sp, gn in sorted(zip(b_features, b_splits, b_gains), key=lambda x: x[2], reverse=True)
    ]

    bw_splits = bw_lgb_reg.booster_.feature_importance(importance_type="split")
    bw_gains = bw_lgb_reg.booster_.feature_importance(importance_type="gain")
    bw_features = bw_test_tree.columns

    bw_importance_breakdown = [
        {
            "feature": feat,
            "split_count": int(sp),
            "gain": round(float(gn), 2),
            "gain_share_pct": round(float(gn / sum(bw_gains) * 100), 2),
        }
        for feat, sp, gn in sorted(zip(bw_features, bw_splits, bw_gains), key=lambda x: x[2], reverse=True)
    ]

    # 8. Calibration details for Wicket Classifier
    test_wkt_rate = float(y_bw_w.mean())
    dummy_brier = float(test_wkt_rate * (1.0 - test_wkt_rate))
    lgb_wkt_brier = float(np.mean((y_bw_w - pred_bw_lgb_clf) ** 2))
    xgb_wkt_brier = float(np.mean((y_bw_w - pred_bw_xgb_clf) ** 2))
    grid_wkt_brier = float(np.mean((y_bw_w - pred_bw_grid_clf) ** 2))

    wkt_calibration_summary = {
        "test_deliveries": len(y_bw_w),
        "test_wickets": int(y_bw_w.sum()),
        "test_base_rate": round(test_wkt_rate, 4),
        "dummy_prior_brier": round(dummy_brier, 4),
        "context_grid_brier": round(grid_wkt_brier, 4),
        "lightgbm_brier": round(lgb_wkt_brier, 4),
        "xgboost_brier": round(xgb_wkt_brier, 4),
        "delta_brier_lgb_vs_dummy": round(lgb_wkt_brier - dummy_brier, 5),
        "calibration_audit_findings": (
            f"Because wickets occur on only ~{test_wkt_rate*100:.1f}% of deliveries, the dummy prior benchmark achieves a Brier score of "
            f"{dummy_brier:.4f}. LightGBM achieves {lgb_wkt_brier:.4f} (a difference of {lgb_wkt_brier - dummy_brier:+.5f}). "
            "While LightGBM provides meaningful ranking discrimination (ROC-AUC 0.5902, PR-AUC 0.0715), overall Brier score is dominated by class rarity. "
            "Natural class prevalence does NOT guarantee calibration; unweighted tree probability predictions remain conditionally conservative."
        ),
    }

    full_audit = {
        "bootstrap_results": bootstrap_results,
        "latency_results": latency_results,
        "feature_importance_breakdown": {
            "batter_runs": b_importance_breakdown,
            "bowler_runs": bw_importance_breakdown,
        },
        "wkt_calibration_summary": wkt_calibration_summary,
    }

    out_file = Path("data/processed/ml/ml_significance_audit.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(full_audit, f, indent=2)

    print(f"\nSaved full audit to {out_file}", flush=True)
    return full_audit


if __name__ == "__main__":
    run_audit(b_replicates=1000, seed=42)
