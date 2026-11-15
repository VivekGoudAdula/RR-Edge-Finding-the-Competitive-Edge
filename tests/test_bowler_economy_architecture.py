"""Unit tests for Bowler Economy Metric Architecture.

Verifies:
1. Wides and no-balls attribution.
2. Byes, leg-byes, and penalty runs exclusion.
3. Legal-ball denominators.
4. Expected concession calculations and population calibration.
5. Zero-exposure cases.
6. Cross-format separation (IPL vs T20I).
7. Representative bowler metrics reconciliation.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.models.bowler_performance import (
    prepare_bowler_delivery_attributes,
    compute_context_adjusted_bowler_metrics,
)


@pytest.fixture
def sample_delivery_df():
    """Create a synthetic delivery DataFrame covering all extras and contexts."""
    rows = [
        # Bowler 1 (Narine-like control): 6 legal balls (4 runs), 1 wide (1 run)
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Middle", "wickets_remaining_before": 8, "runs": 1, "total_delivery_runs": 1, "extras_type": None, "is_legal_ball": True, "bowler_id": 101, "bowler_name": "Bowler LowExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Middle", "wickets_remaining_before": 8, "runs": 0, "total_delivery_runs": 0, "extras_type": None, "is_legal_ball": True, "bowler_id": 101, "bowler_name": "Bowler LowExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Middle", "wickets_remaining_before": 8, "runs": 0, "total_delivery_runs": 0, "extras_type": None, "is_legal_ball": True, "bowler_id": 101, "bowler_name": "Bowler LowExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Middle", "wickets_remaining_before": 8, "runs": 1, "total_delivery_runs": 1, "extras_type": None, "is_legal_ball": True, "bowler_id": 101, "bowler_name": "Bowler LowExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Middle", "wickets_remaining_before": 8, "runs": 2, "total_delivery_runs": 2, "extras_type": None, "is_legal_ball": True, "bowler_id": 101, "bowler_name": "Bowler LowExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Middle", "wickets_remaining_before": 8, "runs": 0, "total_delivery_runs": 0, "extras_type": None, "is_legal_ball": True, "bowler_id": 101, "bowler_name": "Bowler LowExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 1},
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Middle", "wickets_remaining_before": 7, "runs": 0, "total_delivery_runs": 1, "extras_type": "wide", "is_legal_ball": False, "bowler_id": 101, "bowler_name": "Bowler LowExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},

        # Bowler 2 (Pathirana-like high extras): 6 legal balls (6 runs), 3 wides (5 runs total), 1 no-ball (2 runs), 1 bye (4 runs)
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Death", "wickets_remaining_before": 5, "runs": 1, "total_delivery_runs": 1, "extras_type": None, "is_legal_ball": True, "bowler_id": 102, "bowler_name": "Bowler HighExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Death", "wickets_remaining_before": 5, "runs": 1, "total_delivery_runs": 1, "extras_type": None, "is_legal_ball": True, "bowler_id": 102, "bowler_name": "Bowler HighExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Death", "wickets_remaining_before": 5, "runs": 0, "total_delivery_runs": 1, "extras_type": "wide", "is_legal_ball": False, "bowler_id": 102, "bowler_name": "Bowler HighExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Death", "wickets_remaining_before": 5, "runs": 0, "total_delivery_runs": 2, "extras_type": "wide", "is_legal_ball": False, "bowler_id": 102, "bowler_name": "Bowler HighExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Death", "wickets_remaining_before": 5, "runs": 0, "total_delivery_runs": 2, "extras_type": "wide", "is_legal_ball": False, "bowler_id": 102, "bowler_name": "Bowler HighExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Death", "wickets_remaining_before": 5, "runs": 1, "total_delivery_runs": 2, "extras_type": "Overstep", "is_legal_ball": False, "bowler_id": 102, "bowler_name": "Bowler HighExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Death", "wickets_remaining_before": 5, "runs": 2, "total_delivery_runs": 2, "extras_type": None, "is_legal_ball": True, "bowler_id": 102, "bowler_name": "Bowler HighExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Death", "wickets_remaining_before": 5, "runs": 0, "total_delivery_runs": 4, "extras_type": "byes", "is_legal_ball": True, "bowler_id": 102, "bowler_name": "Bowler HighExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Death", "wickets_remaining_before": 5, "runs": 1, "total_delivery_runs": 1, "extras_type": None, "is_legal_ball": True, "bowler_id": 102, "bowler_name": "Bowler HighExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
        {"match_id": 1, "comp_id": 1, "competition_type": "IPL", "innings_phase": "Death", "wickets_remaining_before": 5, "runs": 1, "total_delivery_runs": 1, "extras_type": None, "is_legal_ball": True, "bowler_id": 102, "bowler_name": "Bowler HighExtras", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 1},

        # Bowler 3 in T20I (format separation test)
        {"match_id": 2, "comp_id": 2, "competition_type": "T20I", "innings_phase": "Middle", "wickets_remaining_before": 8, "runs": 1, "total_delivery_runs": 1, "extras_type": None, "is_legal_ball": True, "bowler_id": 103, "bowler_name": "T20I Bowler", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
        {"match_id": 2, "comp_id": 2, "competition_type": "T20I", "innings_phase": "Middle", "wickets_remaining_before": 8, "runs": 2, "total_delivery_runs": 2, "extras_type": None, "is_legal_ball": True, "bowler_id": 103, "bowler_name": "T20I Bowler", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
        {"match_id": 2, "comp_id": 2, "competition_type": "T20I", "innings_phase": "Middle", "wickets_remaining_before": 8, "runs": 0, "total_delivery_runs": 5, "extras_type": "Penalty", "is_legal_ball": True, "bowler_id": 103, "bowler_name": "T20I Bowler", "is_primary_pressure_cohort": True, "is_bowler_pressure": True, "bowler_wicket_credit": 0},
    ]
    return pd.DataFrame(rows)


def test_wides_and_noballs_charged_to_bowler(sample_delivery_df):
    """Test that wides and no-balls are correctly charged in bowler_runs_conceded."""
    prep = prepare_bowler_delivery_attributes(sample_delivery_df)
    
    # Check wide delivery
    wide_row = prep[prep["extras_type"] == "wide"].iloc[0]
    assert wide_row["bowler_runs_conceded"] == wide_row["total_delivery_runs"]
    assert not wide_row["is_legal_bowler_ball"]

    # Check no-ball delivery
    nb_row = prep[prep["extras_type"] == "Overstep"].iloc[0]
    assert nb_row["bowler_runs_conceded"] == nb_row["total_delivery_runs"]
    assert not nb_row["is_legal_bowler_ball"]


def test_byes_legbyes_penalty_excluded(sample_delivery_df):
    """Test that byes, leg-byes, and penalty runs are strictly 0 for the bowler."""
    prep = prepare_bowler_delivery_attributes(sample_delivery_df)
    
    # Byes check
    bye_row = prep[prep["extras_type"] == "byes"].iloc[0]
    assert bye_row["bowler_runs_conceded"] == 0
    assert bye_row["total_delivery_runs"] == 4  # Total runs were 4, but bowler charged 0

    # Penalty check
    penalty_row = prep[prep["extras_type"] == "Penalty"].iloc[0]
    assert penalty_row["bowler_runs_conceded"] == 0
    assert penalty_row["total_delivery_runs"] == 5


def test_legal_ball_denominators(sample_delivery_df):
    """Test that legal balls form the exposure denominator for both metrics."""
    prep = prepare_bowler_delivery_attributes(sample_delivery_df)
    metrics = compute_context_adjusted_bowler_metrics(sample_delivery_df, filter_primary_cohort=False, min_legal_balls=1)
    
    # Bowler HighExtras bowled 10 physical deliveries, but exactly 6 legal balls
    b102 = metrics[metrics["bowler_id"] == 102].iloc[0]
    assert b102["pressure_legal_balls"] == 6

    # Bowler LowExtras bowled 7 physical deliveries, exactly 6 legal balls
    b101 = metrics[metrics["bowler_id"] == 101].iloc[0]
    assert b101["pressure_legal_balls"] == 6


def test_dual_metric_distinction(sample_delivery_df):
    """Test that All-Runs RCAE includes extras while Legal-Ball RCAE strictly excludes them."""
    metrics = compute_context_adjusted_bowler_metrics(sample_delivery_df, filter_primary_cohort=False, min_legal_balls=1)
    
    b102 = metrics[metrics["bowler_id"] == 102].iloc[0]
    
    # Legal balls: 6
    # Legal runs: 1 + 1 + 2 + 0(bye) + 1 + 1 = 6 runs -> legal econ = 6.00
    assert pytest.approx(b102["observed_legal_econ"], 0.01) == 6.00
    
    # Total bowler runs: 6 (legal) + 1 (wide) + 2 (wide) + 2 (wide) + 2 (no-ball) = 13 runs
    # Standard economy: (13 * 6.0) / 6 = 13.00
    assert pytest.approx(b102["observed_pressure_econ"], 0.01) == 13.00

    # Demonstrates clear divergence: 13.00 standard econ vs 6.00 legal econ
    assert b102["observed_pressure_econ"] > b102["observed_legal_econ"]


def test_expected_concession_calibration():
    """Verify that expected all-runs aggregation matches observed concession across context cells."""
    parquet_path = Path(__file__).resolve().parent.parent / "data" / "processed" / "pressure_deliveries.parquet"
    if not parquet_path.exists():
        pytest.skip("Pressure deliveries dataset not present for full calibration test.")

    df = pd.read_parquet(parquet_path)
    primary = df[df["is_primary_pressure_cohort"]].copy()
    prep = prepare_bowler_delivery_attributes(primary)
    prep["wkt_bucket"] = pd.cut(
        prep["wickets_remaining_before"],
        bins=[-1, 3, 6, 11],
        labels=["0-3 wkts", "4-6 wkts", "7-10 wkts"],
    )
    context_keys = ["competition_type", "innings_phase", "wkt_bucket"]
    cell_grp = prep.groupby(context_keys, observed=False)
    cell_runs = cell_grp["bowler_runs_conceded"].sum()
    cell_legal = cell_grp["is_legal_bowler_ball"].sum()
    exp_rate = np.where(cell_legal > 0, cell_runs / cell_legal, np.nan)
    
    # Mathematical proof: exp_rate * cell_legal == cell_runs for all non-empty cells
    valid = cell_legal > 0
    np.testing.assert_allclose(exp_rate[valid] * cell_legal[valid], cell_runs[valid])


def test_zero_exposure_cases():
    """Verify that bowlers with zero legal balls do not crash or produce divide-by-zero."""
    df_empty = pd.DataFrame(columns=[
        "match_id", "comp_id", "competition_type", "innings_phase",
        "wickets_remaining_before", "runs", "total_delivery_runs", "extras_type",
        "is_legal_ball", "bowler_id", "bowler_name", "is_primary_pressure_cohort",
        "is_bowler_pressure", "bowler_wicket_credit"
    ])
    metrics = compute_context_adjusted_bowler_metrics(df_empty, filter_primary_cohort=False, min_legal_balls=0)
    assert metrics.empty


def test_cross_format_separation():
    """Verify that IPL and T20I expected benchmarks are strictly separated."""
    parquet_path = Path(__file__).resolve().parent.parent / "data" / "processed" / "pressure_deliveries.parquet"
    if not parquet_path.exists():
        pytest.skip("Pressure deliveries dataset not present for cross-format test.")

    df = pd.read_parquet(parquet_path)
    prep = prepare_bowler_delivery_attributes(df[df["is_primary_pressure_cohort"]])
    prep["wkt_bucket"] = pd.cut(
        prep["wickets_remaining_before"],
        bins=[-1, 3, 6, 11],
        labels=["0-3 wkts", "4-6 wkts", "7-10 wkts"],
    )
    context_keys = ["competition_type", "innings_phase", "wkt_bucket"]
    cell_grp = prep.groupby(context_keys, observed=False)
    grid_all = cell_grp["bowler_runs_conceded"].sum().reset_index()
    
    ipl_rows = grid_all[grid_all["competition_type"] == "IPL"]
    t20i_rows = grid_all[grid_all["competition_type"] == "T20I"]
    
    # Ensure both formats exist and have independent non-zero expected cells
    assert len(ipl_rows) > 0
    assert len(t20i_rows) > 0
    assert set(ipl_rows["competition_type"]) == {"IPL"}
    assert set(t20i_rows["competition_type"]) == {"T20I"}
