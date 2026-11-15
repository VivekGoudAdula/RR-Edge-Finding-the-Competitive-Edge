"""
Training and Validation Pipeline for Batter Expected Performance Regressors.

Models:
1. Baseline Regressor (Dummy Mean)
2. Context-Grid Baseline (Contingency Stratum Mean)
3. Regularized Linear Model (Ridge)
4. LightGBM Regressor (Gradient Boosted Trees)
5. XGBoost Regressor (Extreme Gradient Boosting)

Evaluation:
- MAE, RMSE, R²
- Stratified evaluation across Format (IPL vs T20I) and Phase
- Feature Importance extraction
- Out-of-Time Holdout Generalization Verification
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import lightgbm as lgb
import xgboost as xgb

from .config import RANDOM_SEED, ML_MODELS_DIR, ML_DIR


class ContextGridBaseline(BaseEstimator, RegressorMixin):
    """Cricket context-grid baseline predicting empirical training mean by
    [competition_type, innings_phase, wickets_bucket]."""

    def __init__(self):
        self.grid_: Dict[Tuple[str, str, int], float] = {}
        self.global_mean_: float = 1.30

    def _get_wickets_bucket(self, wickets_lost: int) -> int:
        if wickets_lost <= 2:
            return 0  # 0-2 wickets
        elif wickets_lost <= 5:
            return 1  # 3-5 wickets
        return 2      # 6+ wickets

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.global_mean_ = float(y.mean())
        df = X[["competition_type", "innings_phase", "wickets_lost"]].copy()
        df["target"] = y.values
        df["w_bucket"] = df["wickets_lost"].apply(self._get_wickets_bucket)

        grp = df.groupby(["competition_type", "innings_phase", "w_bucket"])["target"].mean()
        self.grid_ = grp.to_dict()
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        df = X[["competition_type", "innings_phase", "wickets_lost"]].copy()
        preds = []
        for _, row in df.iterrows():
            w_b = self._get_wickets_bucket(int(row["wickets_lost"]))
            key = (str(row["competition_type"]), str(row["innings_phase"]), w_b)
            preds.append(self.grid_.get(key, self.global_mean_))
        return np.array(preds, dtype=np.float64)


def evaluate_regression(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metadata_subset: pd.DataFrame,
) -> Dict[str, Any]:
    """Calculate comprehensive regression metrics overall and stratified by competition."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))

    metrics = {
        "overall": {"mae": round(mae, 4), "rmse": round(rmse, 4), "r2": round(r2, 4), "samples": len(y_true)}
    }

    # Stratified by format
    for comp in ["IPL", "T20I"]:
        mask = (metadata_subset["competition_type"] == comp).values
        if mask.sum() > 0:
            comp_y_true = y_true[mask]
            comp_y_pred = y_pred[mask]
            metrics[comp.lower()] = {
                "mae": round(float(mean_absolute_error(comp_y_true, comp_y_pred)), 4),
                "rmse": round(float(np.sqrt(mean_squared_error(comp_y_true, comp_y_pred))), 4),
                "r2": round(float(r2_score(comp_y_true, comp_y_pred)), 4),
                "samples": int(mask.sum()),
            }

    return metrics


def train_batter_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    meta_train: pd.DataFrame,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    meta_val: pd.DataFrame,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    meta_test: pd.DataFrame,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, np.ndarray]]:
    """Train candidate batter expected runs regressors, evaluate out-of-time,
    and save artifacts.
    """
    ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    categorical_features = ["competition_type", "innings_phase", "batter_pressure_tier"]
    numerical_features = [col for col in X_train.columns if col not in categorical_features]

    # Preprocessing for linear / distance-based models
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numerical_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
        ]
    )

    models: Dict[str, Any] = {}

    # 1. Baseline: Dummy Mean
    print("  Training Batter Baseline 1 (Dummy Mean)...")
    dummy = DummyRegressor(strategy="mean")
    dummy.fit(X_train, y_train)
    models["dummy_mean"] = dummy

    # 2. Baseline: Cricket Context Grid
    print("  Training Batter Baseline 2 (Context-Grid Mean)...")
    grid_model = ContextGridBaseline()
    grid_model.fit(X_train, y_train)
    models["context_grid"] = grid_model

    # 3. Regularized Linear Model: Ridge
    print("  Training Batter Model 1 (Ridge Regressor)...")
    ridge_pipe = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", Ridge(alpha=10.0, random_state=RANDOM_SEED)),
    ])
    ridge_pipe.fit(X_train, y_train)
    models["ridge"] = ridge_pipe

    # 4. Tree Models Preprocessing: Category Dtype for LightGBM/XGBoost
    X_train_tree = X_train.copy()
    X_val_tree = X_val.copy()
    X_test_tree = X_test.copy()
    for col in categorical_features:
        X_train_tree[col] = X_train_tree[col].astype("category")
        X_val_tree[col] = X_val_tree[col].astype("category")
        X_test_tree[col] = X_test_tree[col].astype("category")

    # 4. LightGBM Regressor
    print("  Training Batter Model 2 (LightGBM Regressor)...")
    lgb_reg = lgb.LGBMRegressor(
        n_estimators=300,
        learning_rate=0.03,
        num_leaves=31,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_SEED,
        verbose=-1,
    )
    lgb_reg.fit(
        X_train_tree,
        y_train,
        eval_set=[(X_val_tree, y_val)],
        callbacks=[lgb.early_stopping(stopping_rounds=25, verbose=False)],
    )
    models["lightgbm"] = lgb_reg

    # 5. XGBoost Regressor
    print("  Training Batter Model 3 (XGBoost Regressor)...")
    xgb_reg = xgb.XGBRegressor(
        n_estimators=300,
        learning_rate=0.03,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        enable_categorical=True,
        random_state=RANDOM_SEED,
        tree_method="hist",
        early_stopping_rounds=25,
    )
    xgb_reg.fit(
        X_train_tree,
        y_train,
        eval_set=[(X_val_tree, y_val)],
        verbose=False,
    )
    models["xgboost"] = xgb_reg

    # Evaluate all models
    results: Dict[str, Any] = {}
    test_preds: Dict[str, np.ndarray] = {}

    for name, model in models.items():
        if name in ("lightgbm", "xgboost"):
            val_p = model.predict(X_val_tree)
            test_p = model.predict(X_test_tree)
        else:
            val_p = model.predict(X_val)
            test_p = model.predict(X_test)

        test_preds[name] = test_p

        val_metrics = evaluate_regression(y_val.values, val_p, meta_val)
        test_metrics = evaluate_regression(y_test.values, test_p, meta_test)

        results[name] = {
            "validation": val_metrics,
            "test": test_metrics,
        }

    # Extract feature importance for Champion Model (LightGBM)
    importance_df = pd.DataFrame({
        "feature": X_train_tree.columns,
        "importance": lgb_reg.feature_importances_,
    }).sort_values("importance", ascending=False)
    importance_dict = dict(zip(importance_df["feature"], importance_df["importance"].astype(int)))

    # Save artifacts
    joblib.dump(lgb_reg, ML_MODELS_DIR / "batter_lightgbm.joblib")
    joblib.dump(xgb_reg, ML_MODELS_DIR / "batter_xgboost.joblib")
    joblib.dump(grid_model, ML_MODELS_DIR / "batter_context_grid.joblib")
    joblib.dump(dummy, ML_MODELS_DIR / "batter_dummy.joblib")

    return results, importance_dict, test_preds

