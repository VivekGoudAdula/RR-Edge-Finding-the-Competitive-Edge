"""
Unit and Integration Tests for RR EDGE Supervised Machine Learning Pipeline.

Tests:
1. Target construction & cricket extras attribution.
2. Feature leakage controls & prohibited columns detection.
3. Chronological match-grouped split disjointness & zero leakage.
4. Model artifact existence and format validity.
5. Live inference and API response contracts.
"""

import json
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from src.models.ml.config import (
    ML_DIR,
    ML_MODELS_DIR,
    PROHIBITED_FEATURE_COLS,
    BATTER_FEATURE_COLS,
    BOWLER_FEATURE_COLS,
)
from src.models.ml.features import (
    compute_bowler_runs_conceded,
    assert_zero_leakage,
    extract_batter_dataset,
    extract_bowler_dataset,
)
from src.models.ml.splitting import generate_match_grouped_splits
from src.models.ml.service import ml_service
from src.api.main import app


@pytest.fixture
def sample_delivery_df():
    """Create a realistic sample deliveries dataframe."""
    return pd.DataFrame({
        "match_id": [101, 101, 102, 103, 104],
        "season": ["2022", "2022", "2024", "2025", "2026"],
        "match_date": ["2022-03-26", "2022-03-26", "2024-04-10", "2025-05-01", "2026-04-15"],
        "competition_type": ["IPL", "IPL", "T20I", "IPL", "T20I"],
        "is_knockout": [False, False, True, False, False],
        "innings": [1, 1, 2, 2, 1],
        "overid": [1, 2, 18, 19, 10],
        "batting_order_raw": [3, 3, 6, 7, 4],
        "legal_balls_bowled_before": [6, 12, 108, 114, 60],
        "balls_remaining_before": [114, 108, 12, 6, 60],
        "current_score_before": [8, 14, 160, 172, 85],
        "wickets_lost_before": [0, 1, 5, 6, 3],
        "wickets_remaining_before": [10, 9, 5, 4, 7],
        "current_run_rate_before": [8.0, 7.0, 8.89, 9.05, 8.5],
        "innings_target": [np.nan, np.nan, 180.0, 185.0, np.nan],
        "batter_required_run_rate": [np.nan, np.nan, 10.0, 13.0, np.nan],
        "batter_delta_rrr": [np.nan, np.nan, 1.11, 3.95, np.nan],
        "batter_first_innings_par_deficit": [0.0, 2.5, np.nan, np.nan, -5.0],
        "batter_pressure_tier": ["LOW", "MODERATE", "HIGH", "EXTREME", "MODERATE"],
        "batter_prev_6_runs": [6.0, 8.0, 12.0, 9.0, 7.0],
        "batter_prev_6_dots": [2.0, 3.0, 1.0, 0.0, 2.0],
        "batter_prev_6_wickets": [0.0, 1.0, 0.0, 1.0, 0.0],
        "bowler_runs_to_defend": [np.nan, np.nan, 20.0, 13.0, np.nan],
        "bowler_required_run_rate": [np.nan, np.nan, 10.0, 13.0, np.nan],
        "bowler_expected_scoring_rate": [8.0, 8.0, 10.5, 12.0, 8.5],
        "par_deficit": [0.0, 2.5, 0.0, 0.0, -5.0],
        "bowler_pressure_tier": ["LOW", "MODERATE", "HIGH", "EXTREME", "MODERATE"],
        "bowler_batting_resource_context": ["TOP_ORDER_INTACT", "TOP_ORDER_INTACT", "MIDDLE_ORDER", "MIDDLE_ORDER", "MIDDLE_ORDER"],
        "bowler_prev_6_runs": [6.0, 8.0, 12.0, 9.0, 7.0],
        "bowler_prev_6_dots": [2.0, 3.0, 1.0, 0.0, 2.0],
        "bowler_prev_6_wickets": [0.0, 1.0, 0.0, 1.0, 0.0],
        "is_primary_pressure_cohort": [True, True, True, True, True],
        "runs": [1, 4, 6, 0, 2],
        "total_delivery_runs": [1, 4, 7, 0, 2],
        "extras_type": [np.nan, np.nan, "wide", "legbyes", np.nan],
        "is_wicket": [False, False, False, False, False],
        "is_bowler_wkt": [False, False, False, False, False],
        "striker_id": [1, 1, 2, 3, 4],
        "striker_name": ["Batter A", "Batter A", "Batter B", "Batter C", "Batter D"],
        "bowler_id": [10, 10, 20, 30, 40],
        "bowler_name": ["Bowler X", "Bowler X", "Bowler Y", "Bowler Z", "Bowler W"],
        "innings_phase": ["Powerplay", "Powerplay", "Death", "Death", "Middle"],
    })


def test_compute_bowler_runs_conceded():
    """Verify cricket extras attribution rules for bowler conceded runs."""
    df_test = pd.DataFrame({
        "extras_type": ["legbyes", "byes", "Penalty", "wide", "Overstep", "other", np.nan, None],
        "total_delivery_runs": [4, 2, 5, 5, 2, 1, 6, 1],
        "runs": [0, 0, 0, 0, 1, 1, 6, 1],
    })
    conceded = compute_bowler_runs_conceded(df_test)

    # Byes, leg-byes, penalty must be 0
    assert conceded[0] == 0  # legbyes
    assert conceded[1] == 0  # byes
    assert conceded[2] == 0  # Penalty

    # Wides and no-balls must equal total delivery runs
    assert conceded[3] == 5  # wide
    assert conceded[4] == 2  # Overstep (no ball)
    assert conceded[5] == 1  # other bowler extra

    # Standard deliveries must equal bat runs
    assert conceded[6] == 6  # six off the bat
    assert conceded[7] == 1  # single


def test_assert_zero_leakage():
    """Verify that feature matrices reject prohibited columns."""
    clean_df = pd.DataFrame({"competition_type": ["IPL"], "over_num": [5]})
    assert_zero_leakage(clean_df)  # Should not raise

    leaked_df = pd.DataFrame({"competition_type": ["IPL"], "runs": [4]})
    with pytest.raises(ValueError, match="CRITICAL LEAKAGE DETECTED"):
        assert_zero_leakage(leaked_df)

    player_leak_df = pd.DataFrame({"competition_type": ["IPL"], "striker_id": [1234]})
    with pytest.raises(ValueError, match="CRITICAL LEAKAGE DETECTED"):
        assert_zero_leakage(player_leak_df)


def test_match_grouped_split_disjointness(sample_delivery_df):
    """Verify chronological match-grouped splits have zero match overlap."""
    train_idx, val_idx, test_idx, manifest = generate_match_grouped_splits(sample_delivery_df)

    train_matches = set(sample_delivery_df.iloc[train_idx]["match_id"])
    val_matches = set(sample_delivery_df.iloc[val_idx]["match_id"])
    test_matches = set(sample_delivery_df.iloc[test_idx]["match_id"])

    # Assert pairwise empty intersection
    assert len(train_matches.intersection(val_matches)) == 0
    assert len(train_matches.intersection(test_matches)) == 0
    assert len(val_matches.intersection(test_matches)) == 0

    assert manifest["train"]["matches"] == 2  # 101, 102
    assert manifest["validation"]["matches"] == 1  # 103
    assert manifest["test"]["matches"] == 1  # 104


def test_ml_artifacts_exist():
    """Verify that all required ML artifacts were successfully generated."""
    assert (ML_DIR / "ml_evaluation_summary.json").exists()
    assert (ML_DIR / "split_manifest.json").exists()
    assert (ML_DIR / "batter_test_predictions.parquet").exists()

    # Model binaries
    assert (ML_MODELS_DIR / "batter_lightgbm.joblib").exists()
    assert (ML_MODELS_DIR / "batter_xgboost.joblib").exists()
    assert (ML_MODELS_DIR / "bowler_runs_lightgbm.joblib").exists()
    assert (ML_MODELS_DIR / "bowler_wkt_lightgbm.joblib").exists()


def test_api_ml_endpoints():
    """Verify FastAPI ML intelligence endpoints return valid schemas."""
    client = TestClient(app)

    # 1. Overview
    r_ov = client.get("/api/ml/overview")
    assert r_ov.status_code == 200
    data_ov = r_ov.json()
    assert "models" in data_ov
    assert "batter_expected_runs" in data_ov["models"]
    assert "bowler_expected_runs" in data_ov["models"]
    assert "bowler_wicket_probability" in data_ov["models"]

    # 2. Predictions
    r_pred = client.get("/api/ml/predictions?limit=10")
    assert r_pred.status_code == 200
    preds = r_pred.json()
    assert len(preds) <= 10
    if len(preds) > 0:
        assert "actual_runs" in preds[0]
        assert "pred_lightgbm" in preds[0]

    # 3. Live Batter Inference
    sample_feat = {
        "competition_type": "IPL",
        "innings": 2,
        "innings_phase": "Death",
        "is_knockout": 1,
        "over_num": 18,
        "batting_order": 5,
        "legal_balls_bowled": 110,
        "balls_remaining": 10,
        "current_score": 170,
        "wickets_lost": 4,
        "wickets_remaining": 6,
        "current_run_rate": 9.2,
        "target_runs": 190.0,
        "required_run_rate": 12.0,
        "delta_rrr": 2.8,
        "par_deficit": 0.0,
        "batter_pressure_tier": "HIGH",
        "prev_6_runs": 11.0,
        "prev_6_dots": 1.0,
        "prev_6_wickets": 0.0,
    }
    r_bat = client.post("/api/ml/predict/batter", json=sample_feat)
    assert r_bat.status_code == 200
    res_bat = r_bat.json()
    assert "expected_runs" in res_bat
    assert "implied_strike_rate" in res_bat
    assert res_bat["expected_runs"] > 0

