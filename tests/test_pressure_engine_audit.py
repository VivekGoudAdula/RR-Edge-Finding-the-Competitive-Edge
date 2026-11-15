"""
Regression test suite for Phase 2.2.1 Pressure Engine Independent Audit.

Verifies:
1. Parquet dataset integrity (rows, columns, deduplication, zero infinite values).
2. Traceability of all output rows to raw ball_by_ball deliveries.
3. DLS cohort isolation contract (is_primary_pressure_cohort).
4. Non-striker dismissal attribution (RunOut, Retire Out).
5. Asymmetric discipline distribution (tail closure dominance).
6. Independent recomputation consistency on a reproducible sample.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from src.data.load_data import load_all
from src.cricket.semantics import is_legal_delivery
from src.cricket.pressure_engine import (
    PressureEngineConfig,
    classify_batter_delivery_pressure,
    classify_bowler_delivery_pressure,
)


@pytest.fixture(scope="module")
def parquet_data():
    project_root = Path(__file__).resolve().parents[1]
    parquet_path = project_root / "data" / "processed" / "pressure_deliveries.parquet"
    assert parquet_path.exists(), f"Missing Parquet dataset at {parquet_path}"
    return pd.read_parquet(parquet_path)


def test_parquet_dataset_integrity(parquet_data):
    """Verify total row count, expected columns, and absence of infinite values."""
    assert len(parquet_data) == 194014
    assert len(parquet_data.columns) >= 60

    # Primary key deduplication
    dup_keys = parquet_data.duplicated(subset=["match_id", "innings", "innings_ball_num"])
    assert dup_keys.sum() == 0, "Duplicate delivery keys found in Parquet dataset!"

    # No infinite values in numeric columns
    numeric_cols = parquet_data.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        assert not np.isinf(parquet_data[col]).any(), f"Infinite values detected in {col}!"


def test_dls_cohort_filtering_contract(parquet_data):
    """Verify that all uncertain DLS deliveries are isolated by is_primary_pressure_cohort."""
    dls_mask = parquet_data["target_certainty"] == "UNCERTAIN_DLS_TIMING"
    assert dls_mask.sum() == 1641

    # Filtering contract check
    assert (parquet_data.loc[dls_mask, "is_primary_pressure_cohort"] == False).all()
    primary_df = parquet_data[parquet_data["is_primary_pressure_cohort"]]
    assert len(primary_df) == 192373
    assert (primary_df["target_certainty"] != "UNCERTAIN_DLS_TIMING").all()


def test_player_attribution_and_non_striker_outs(parquet_data):
    """Verify dismissed player attribution distinguishes strikers from non-strikers."""
    dismissals = parquet_data[parquet_data["is_wicket"] == 1]
    assert len(dismissals) > 10000

    # Non-striker dismissals
    non_striker_outs = dismissals[dismissals["dismissed_player_id"] != dismissals["striker_id"]]
    assert len(non_striker_outs) == 263

    # All non-striker dismissals must be RunOut or Retire Out
    valid_types = {"RunOut", "Retire Out", "run out", "retired out"}
    actual_types = set(non_striker_outs["dismissal_type"].unique())
    assert actual_types.issubset(valid_types)


def test_bowler_tail_closure_asymmetry(parquet_data):
    """Verify that bowlers facing tailenders under high RRR are classified as LOW pressure,
    except when acute margin pressure (<= 18 runs in <= 12 balls) takes precedence."""
    tail_deliveries = parquet_data[
        (parquet_data["innings"].isin([2, 4]))
        & (parquet_data["batter_wickets_remaining"] <= 2)
        & (parquet_data["batter_required_run_rate"] >= 14.0)
    ]
    assert len(tail_deliveries) == 3326

    # Batter is 100% EXTREME
    assert (tail_deliveries["batter_pressure_tier"] == "EXTREME").all()

    # For non-acute margin, bowler is strictly 100% LOW pressure (closing out tail)
    non_acute_tail = tail_deliveries[
        ~(
            (tail_deliveries["bowler_legal_balls_remaining"] <= 12)
            & (tail_deliveries["bowler_runs_to_defend"] <= 18)
        )
    ]
    assert len(non_acute_tail) == 3128
    assert (non_acute_tail["bowler_pressure_tier"] == "LOW").all()

    # Acute margin tail deliveries correctly trigger EXTREME margin defense
    acute_tail = tail_deliveries[
        (tail_deliveries["bowler_legal_balls_remaining"] <= 12)
        & (tail_deliveries["bowler_runs_to_defend"] <= 18)
    ]
    assert len(acute_tail) == 198
    assert (acute_tail["bowler_pressure_tier"] == "EXTREME").all()


def test_independent_recomputation_sample(parquet_data):
    """Independently recompute pre-delivery metrics for a deterministic sample."""
    sample_df = parquet_data.sample(n=50, random_state=42)
    raw_bbb = load_all()["ball_by_ball"]
    cfg = PressureEngineConfig()

    for row in sample_df.itertuples():
        prior_balls = raw_bbb[
            (raw_bbb["match_id"] == row.match_id)
            & (raw_bbb["innings"] == row.innings)
            & (raw_bbb["innings_ball_num"] < row.innings_ball_num)
        ]

        if len(prior_balls) == 0:
            indep_score = 0
            indep_wkts = 0
            indep_leg = 0
        else:
            indep_score = int((prior_balls["runs"] + prior_balls["extras1_runs"] + prior_balls["extras_2_runs"]).sum())
            indep_wkts = int(prior_balls["is_wicket"].astype(int).sum())
            indep_leg = int(prior_balls["extras_type"].apply(is_legal_delivery).astype(int).sum())

        assert indep_score == row.current_score_before
        assert indep_wkts == row.wickets_lost_before
        assert indep_leg == row.legal_balls_bowled_before

        # Recomputed tiers must match
        recomputed_b_tier, _ = classify_batter_delivery_pressure(
            row.innings, row.batter_required_run_rate, row.batter_delta_rrr,
            row.batter_wickets_remaining, row.batter_legal_balls_remaining,
            row.batter_first_innings_par_deficit, row.batter_prev_6_runs,
            row.batter_prev_6_dots, cfg
        )
        assert recomputed_b_tier == row.batter_pressure_tier

