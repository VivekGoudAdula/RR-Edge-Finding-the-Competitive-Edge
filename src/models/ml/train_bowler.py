"""
Training and Validation Pipeline for Bowler Expected Performance Models.

Models:
1. Bowler Runs Conceded Regressor (Dummy, ContextGrid, Ridge, LightGBM, XGBoost)
2. Bowler Wicket Probability Classifier (Dummy, ContextGrid, LogisticRegression, LightGBM, XGBoost)

Evaluation:
- Regression: MAE, RMSE, R²
- Classification: ROC-AUC, PR-AUC (Average Precision), Log-Loss, Brier Score, Calibration
- Formats: Overall, IPL, T20I
- Feature Importance
- Out-of-Time Generalization Verification
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, ClassifierMixin
from sklearn.dummy import DummyRegressor, DummyClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
    average_precision_score,
    log_loss,
    brier_score_loss,
)
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.calibration import calibration_curve
import lightgbm as lgb
import xgboost as xgb

from .config import RANDOM_SEED, ML_MODELS_DIR, ML_DIR


class BowlerContextGridBaseline(BaseEstimator, RegressorMixin):
    """Cricket context-grid baseline predicting empirical mean bowler runs conceded
    by [competition_type, innings_phase, wickets_bucket]."""

    def __init__(self):
        self.grid_: Dict[Tuple[str, str, int], float] = {}
        self.global_mean_: float = 1.35

    def _get_wickets_bucket(self, wickets_lost: int) -> int:
        if wickets_lost <= 2:
            return 0
        elif wickets_lost <= 5:
            return 1
        return 2

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


class BowlerWicketGridBaseline(BaseEstimator, ClassifierMixin):
    """Cricket context-grid baseline predicting empirical wicket rate
    by [competition_type, innings_phase, wickets_bucket]."""

    def __init__(self):
        self.grid_: Dict[Tuple[str, str, int], float] = {}
        self.global_rate_: float = 0.05
        self.classes_ = np.array([0, 1])

    def _get_wickets_bucket(self, wickets_lost: int) -> int:
        if wickets_lost <= 2:
            return 0
        elif wickets_lost <= 5:
            return 1
        return 2

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.global_rate_ = float(y.mean())
        df = X[["competition_type", "innings_phase", "wickets_lost"]].copy()
        df["target"] = y.values
        df["w_bucket"] = df["wickets_lost"].apply(self._get_wickets_bucket)
        grp = df.groupby(["competition_type", "innings_phase", "w_bucket"])["target"].mean()
        self.grid_ = grp.to_dict()
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        df = X[["competition_type", "innings_phase", "wickets_lost"]].copy()
        probs_1 = []
        for _, row in df.iterrows():
            w_b = self._get_wickets_bucket(int(row["wickets_lost"]))
            key = (str(row["competition_type"]), str(row["innings_phase"]), w_b)
            p = self.grid_.get(key, self.global_rate_)
            probs_1.append(p)
        p1 = np.array(probs_1, dtype=np.float64)
        p0 = 1.0 - p1
        return np.column_stack([p0, p1])

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


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


def evaluate_classification(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    metadata_subset: pd.DataFrame,
) -> Dict[str, Any]:
    """Calculate classification metrics: ROC-AUC, PR-AUC, Log-Loss, Brier Score."""
    roc_auc = float(roc_auc_score(y_true, y_prob))
    pr_auc = float(average_precision_score(y_true, y_prob))
    ll = float(log_loss(y_true, y_prob))
    brier = float(brier_score_loss(y_true, y_prob))

    metrics = {
        "overall": {
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "log_loss": round(ll, 4),
            "brier_score": round(brier, 4),
            "positive_rate": round(float(y_true.mean()), 4),
            "samples": len(y_true),
        }
    }

    for comp in ["IPL", "T20I"]:
        mask = (metadata_subset["competition_type"] == comp).values
        if mask.sum() > 0 and y_true[mask].sum() > 0:
            comp_y_true = y_true[mask]
            comp_y_prob = y_prob[mask]
            metrics[comp.lower()] = {
                "roc_auc": round(float(roc_auc_score(comp_y_true, comp_y_prob)), 4),
                "pr_auc": round(float(average_precision_score(comp_y_true, comp_y_prob)), 4),
                "log_loss": round(float(log_loss(comp_y_true, comp_y_prob)), 4),
                "brier_score": round(float(brier_score_loss(comp_y_true, comp_y_prob)), 4),
                "positive_rate": round(float(comp_y_true.mean()), 4),
                "samples": int(mask.sum()),
            }

    return metrics


def train_bowler_models(
    X_train: pd.DataFrame,
    y_train_runs: pd.Series,
    y_train_wkt: pd.Series,
    meta_train: pd.DataFrame,
    X_val: pd.DataFrame,
    y_val_runs: pd.Series,
    y_val_wkt: pd.Series,
    meta_val: pd.DataFrame,
    X_test: pd.DataFrame,
    y_test_runs: pd.Series,
    y_test_wkt: pd.Series,
    meta_test: pd.DataFrame,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Train candidate bowler runs regressors and wicket classifiers, evaluate out-of-time."""
    ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    categorical_features = ["competition_type", "innings_phase", "bowler_pressure_tier", "bowler_resource_context"]
    numerical_features = [col for col in X_train.columns if col not in categorical_features]

    # Preprocessor for linear models
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numerical_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
        ]
    )

    # Tree data
    X_train_tree = X_train.copy()
    X_val_tree = X_val.copy()
    X_test_tree = X_test.copy()
    for col in categorical_features:
        X_train_tree[col] = X_train_tree[col].astype("category")
        X_val_tree[col] = X_val_tree[col].astype("category")
        X_test_tree[col] = X_test_tree[col].astype("category")

    # ==========================================
    # 1. BOWLER RUNS CONCEDED REGRESSORS
    # ==========================================
    print("  Training Bowler Runs Models...")
    runs_models: Dict[str, Any] = {}

    dummy_reg = DummyRegressor(strategy="mean")
    dummy_reg.fit(X_train, y_train_runs)
    runs_models["dummy_mean"] = dummy_reg

    grid_reg = BowlerContextGridBaseline()
    grid_reg.fit(X_train, y_train_runs)
    runs_models["context_grid"] = grid_reg

    ridge_reg = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", Ridge(alpha=10.0, random_state=RANDOM_SEED)),
    ])
    ridge_reg.fit(X_train, y_train_runs)
    runs_models["ridge"] = ridge_reg

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
        y_train_runs,
        eval_set=[(X_val_tree, y_val_runs)],
        callbacks=[lgb.early_stopping(stopping_rounds=25, verbose=False)],
    )
    runs_models["lightgbm"] = lgb_reg

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
        y_train_runs,
        eval_set=[(X_val_tree, y_val_runs)],
        verbose=False,
    )
    runs_models["xgboost"] = xgb_reg

    # Evaluate Runs Models
    runs_results: Dict[str, Any] = {}
    for name, model in runs_models.items():
        if name in ("lightgbm", "xgboost"):
            vp = model.predict(X_val_tree)
            tp = model.predict(X_test_tree)
        else:
            vp = model.predict(X_val)
            tp = model.predict(X_test)

        runs_results[name] = {
            "validation": evaluate_regression(y_val_runs.values, vp, meta_val),
            "test": evaluate_regression(y_test_runs.values, tp, meta_test),
        }

    # ==========================================
    # 2. BOWLER WICKET PROBABILITY CLASSIFIERS
    # ==========================================
    print("  Training Bowler Wicket Models...")
    wkt_models: Dict[str, Any] = {}

    dummy_clf = DummyClassifier(strategy="prior")
    dummy_clf.fit(X_train, y_train_wkt)
    wkt_models["dummy_prior"] = dummy_clf

    grid_clf = BowlerWicketGridBaseline()
    grid_clf.fit(X_train, y_train_wkt)
    wkt_models["context_grid"] = grid_clf

    lr_clf = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(max_iter=1000, random_state=RANDOM_SEED, class_weight="balanced")),
    ])
    lr_clf.fit(X_train, y_train_wkt)
    wkt_models["logistic_regression"] = lr_clf

    scale_pos_weight = float((len(y_train_wkt) - y_train_wkt.sum()) / max(1, y_train_wkt.sum()))

    lgb_clf = lgb.LGBMClassifier(
        n_estimators=300,
        learning_rate=0.03,
        num_leaves=31,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=1.0,  # Unweighted for well-calibrated probabilities
        random_state=RANDOM_SEED,
        verbose=-1,
    )
    lgb_clf.fit(
        X_train_tree,
        y_train_wkt,
        eval_set=[(X_val_tree, y_val_wkt)],
        callbacks=[lgb.early_stopping(stopping_rounds=25, verbose=False)],
    )
    wkt_models["lightgbm"] = lgb_clf

    xgb_clf = xgb.XGBClassifier(
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
    xgb_clf.fit(
        X_train_tree,
        y_train_wkt,
        eval_set=[(X_val_tree, y_val_wkt)],
        verbose=False,
    )
    wkt_models["xgboost"] = xgb_clf

    # Evaluate Wicket Models
    wkt_results: Dict[str, Any] = {}
    for name, model in wkt_models.items():
        if name in ("lightgbm", "xgboost"):
            vp = model.predict_proba(X_val_tree)[:, 1]
            tp = model.predict_proba(X_test_tree)[:, 1]
        else:
            vp = model.predict_proba(X_val)[:, 1]
            tp = model.predict_proba(X_test)[:, 1]

        wkt_results[name] = {
            "validation": evaluate_classification(y_val_wkt.values, vp, meta_val),
            "test": evaluate_classification(y_test_wkt.values, tp, meta_test),
        }

    # Extract Calibration Curve for LightGBM
    lgb_tp = lgb_clf.predict_proba(X_test_tree)[:, 1]
    prob_true, prob_pred = calibration_curve(y_test_wkt.values, lgb_tp, n_bins=5)
    calibration_data = {
        "prob_true": [round(float(x), 4) for x in prob_true],
        "prob_pred": [round(float(x), 4) for x in prob_pred],
    }

    # Feature Importance for Bowler Models
    runs_importance = dict(zip(X_train_tree.columns, [int(x) for x in lgb_reg.feature_importances_]))
    wkt_importance = dict(zip(X_train_tree.columns, [int(x) for x in lgb_clf.feature_importances_]))

    # Save artifacts
    joblib.dump(lgb_reg, ML_MODELS_DIR / "bowler_runs_lightgbm.joblib")
    joblib.dump(xgb_reg, ML_MODELS_DIR / "bowler_runs_xgboost.joblib")
    joblib.dump(grid_reg, ML_MODELS_DIR / "bowler_runs_context_grid.joblib")

    joblib.dump(lgb_clf, ML_MODELS_DIR / "bowler_wkt_lightgbm.joblib")
    joblib.dump(xgb_clf, ML_MODELS_DIR / "bowler_wkt_xgboost.joblib")
    joblib.dump(grid_clf, ML_MODELS_DIR / "bowler_wkt_context_grid.joblib")

    return runs_results, wkt_results, runs_importance, {"wkt_importance": wkt_importance, "calibration": calibration_data}
