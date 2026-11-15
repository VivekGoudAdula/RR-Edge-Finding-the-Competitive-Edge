"""
Service Layer for RR EDGE Supervised Machine Learning Models.

Provides fast, in-memory caching and inference endpoints for FastAPI backend:
- Model overview metadata and validation metrics
- Test partition sample predictions
- Live single-delivery inference for Batter Expected Runs and Bowler Wicket Probability
"""

from typing import Dict, Any, Optional, List
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from .config import ML_DIR, ML_MODELS_DIR, BATTER_FEATURE_COLS, BOWLER_FEATURE_COLS


class MLModelService:
    """Singleton service for loading ML models and serving predictions."""

    def __init__(self):
        self._summary: Optional[Dict[str, Any]] = None
        self._sample_preds: Optional[pd.DataFrame] = None
        self._batter_lgb = None
        self._bowler_runs_lgb = None
        self._bowler_wkt_lgb = None
        self._loaded = False

    def load_artifacts(self) -> None:
        """Load evaluation summary and trained model binaries into memory."""
        if self._loaded:
            return

        summary_file = ML_DIR / "ml_evaluation_summary.json"
        if summary_file.exists():
            with open(summary_file, "r", encoding="utf-8") as f:
                self._summary = json.load(f)

        preds_file = ML_DIR / "batter_test_predictions.parquet"
        if preds_file.exists():
            self._sample_preds = pd.read_parquet(preds_file)

        # Load LightGBM Champion Models
        bat_model_path = ML_MODELS_DIR / "batter_lightgbm.joblib"
        if bat_model_path.exists():
            self._batter_lgb = joblib.load(bat_model_path)

        bowl_runs_path = ML_MODELS_DIR / "bowler_runs_lightgbm.joblib"
        if bowl_runs_path.exists():
            self._bowler_runs_lgb = joblib.load(bowl_runs_path)

        bowl_wkt_path = ML_MODELS_DIR / "bowler_wkt_lightgbm.joblib"
        if bowl_wkt_path.exists():
            self._bowler_wkt_lgb = joblib.load(bowl_wkt_path)

        self._loaded = True

    def get_overview(self) -> Dict[str, Any]:
        """Return complete validated ML training and evaluation metadata."""
        self.load_artifacts()
        if not self._summary:
            raise FileNotFoundError("ML evaluation summary not found. Run pipeline first.")
        return self._summary

    def get_predictions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return sample actual vs predicted records from holdout test partition."""
        self.load_artifacts()
        if self._sample_preds is None:
            return []
        df_slice = self._sample_preds.head(limit)
        return df_slice.to_dict(orient="records")

    def predict_batter_delivery(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Perform live inference for expected batter runs on a single delivery."""
        self.load_artifacts()
        if self._batter_lgb is None:
            raise RuntimeError("Batter LightGBM model not loaded.")

        row = {col: features.get(col, 0) for col in BATTER_FEATURE_COLS}
        df_row = pd.DataFrame([row])
        for col in ["competition_type", "innings_phase", "batter_pressure_tier"]:
            df_row[col] = df_row[col].astype("category")

        pred_runs = float(self._batter_lgb.predict(df_row)[0])
        implied_sr = round(pred_runs * 100.0, 1)

        return {
            "expected_runs": round(pred_runs, 3),
            "implied_strike_rate": implied_sr,
            "model": "LightGBM Regressor v1.0",
        }

    def predict_bowler_delivery(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Perform live inference for expected bowler runs conceded and wicket probability."""
        self.load_artifacts()
        if self._bowler_runs_lgb is None or self._bowler_wkt_lgb is None:
            raise RuntimeError("Bowler models not loaded.")

        row = {col: features.get(col, 0) for col in BOWLER_FEATURE_COLS}
        df_row = pd.DataFrame([row])
        for col in ["competition_type", "innings_phase", "bowler_pressure_tier", "bowler_resource_context"]:
            df_row[col] = df_row[col].astype("category")

        pred_runs = float(self._bowler_runs_lgb.predict(df_row)[0])
        pred_wkt_prob = float(self._bowler_wkt_lgb.predict_proba(df_row)[0, 1])
        implied_econ = round(pred_runs * 6.0, 2)

        return {
            "expected_runs_conceded": round(pred_runs, 3),
            "implied_economy": implied_econ,
            "wicket_probability": round(pred_wkt_prob, 4),
            "wicket_percentage": round(pred_wkt_prob * 100.0, 2),
            "model": "LightGBM Regressor + Classifier v1.0",
        }


# Singleton service instance
ml_service = MLModelService()

