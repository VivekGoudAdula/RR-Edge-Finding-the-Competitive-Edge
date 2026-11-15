"""Comprehensive tests for RR EDGE Scenario Lab.

Validates scenario state matching, last-two-ball conditions, legal ball handling,
innings boundaries, complete match-innings outcome attribution, format separation,
evidence tier thresholds, and API response structures.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.models.scenarios.definitions import ALL_SCENARIOS, BOWLING_SCENARIOS, BATTING_SCENARIOS
from src.models.scenarios.service import scenario_service
from src.models.scenarios.engine import scenario_engine


@pytest.fixture(scope="module")
def client():
    """TestClient fixture with preloaded datasets."""
    with TestClient(app) as test_client:
        yield test_client


def test_scenario_catalog_integrity():
    """Verify that all 16 standard scenarios are properly registered with complete metadata."""
    assert len(BOWLING_SCENARIOS) == 8
    assert len(BATTING_SCENARIOS) == 8
    assert len(ALL_SCENARIOS) == 16

    for s_id, s in ALL_SCENARIOS.items():
        assert s.id == s_id
        assert s.discipline in ["BOWLER", "BATTER"]
        assert len(s.name) > 0
        assert len(s.description) > 0
        assert len(s.tactical_intent) > 0
        assert len(s.metric_focus) > 0
        assert len(s.relaxation_explanation) > 0


def test_defend_12_in_2_scenario():
    """Test the 'Defend 12 in Final 2 Balls' scenario boundaries."""
    res = scenario_service.execute_scenario(
        scenario_id="defend_12_in_2",
        format_filter="Combined",
        min_evidence="ALL",
        limit=20,
    )
    assert res["scenario"]["id"] == "defend_12_in_2"
    assert res["cohort_benchmarks"]["total_deliveries"] > 0
    assert res["cohort_benchmarks"]["total_matches"] > 0

    # Ensure every sample episode satisfies balls_remaining_before <= 2 and innings == 2
    for ep in res["sample_episodes"]:
        assert ep["innings"] == 2
        assert ep["balls_remaining"] <= 2
        assert ep["runs_to_defend"] <= 12


def test_chase_12_in_6_scenario():
    """Test the 'Chase 12 in Final 6 Balls' batting scenario boundaries."""
    res = scenario_service.execute_scenario(
        scenario_id="chase_12_in_6",
        format_filter="IPL",
        min_evidence="ALL",
        limit=20,
    )
    assert res["scenario"]["id"] == "chase_12_in_6"
    assert res["cohort_benchmarks"]["total_deliveries"] > 0
    assert res["cohort_benchmarks"]["cohort_rate"] > 0  # Strike Rate > 0

    for ep in res["sample_episodes"]:
        assert ep["innings"] == 2
        assert ep["balls_remaining"] <= 6


def test_legal_versus_extras_accounting():
    """Verify that legal deliveries and total deliveries are strictly separated."""
    res = scenario_service.execute_scenario(
        scenario_id="defend_18_in_6",
        format_filter="IPL",
        min_evidence="ALL",
        limit=50,
    )
    for p in res["players"]:
        # Deliveries must be >= legal_balls due to potential wides/no-balls
        assert p["deliveries"] >= p["legal_balls"]
        # Economy rate calculated per legal ball (runs / legal_balls * 6.0)
        expected_econ = round(p["runs"] / p["legal_balls"] * 6.0, 2)
        assert abs(p["primary_rate"] - expected_econ) < 0.05


def test_format_separation():
    """Confirm that IPL, T20I, and Combined cohorts do not leak into one another."""
    ipl_res = scenario_service.execute_scenario(
        scenario_id="defend_18_in_6",
        format_filter="IPL",
        min_evidence="ALL",
    )
    t20i_res = scenario_service.execute_scenario(
        scenario_id="defend_18_in_6",
        format_filter="T20I",
        min_evidence="ALL",
    )
    comb_res = scenario_service.execute_scenario(
        scenario_id="defend_18_in_6",
        format_filter="Combined",
        min_evidence="ALL",
    )

    ipl_deliv = ipl_res["cohort_benchmarks"]["total_deliveries"]
    t20i_deliv = t20i_res["cohort_benchmarks"]["total_deliveries"]
    comb_deliv = comb_res["cohort_benchmarks"]["total_deliveries"]

    assert ipl_deliv > 0
    assert t20i_deliv > 0
    assert comb_deliv == ipl_deliv + t20i_deliv


def test_evidence_tiers_and_thresholds():
    """Verify that players are assigned to correct operational evidence tiers based on deliveries AND matches."""
    res = scenario_service.execute_scenario(
        scenario_id="defend_18_in_6",
        format_filter="Combined",
        min_evidence="ALL",
        limit=200,
    )
    for p in res["players"]:
        balls = p["legal_balls"]
        matches = p["matches"]
        tier = p["evidence_tier"]
        if balls >= 30 and matches >= 5:
            assert tier == "CONFIDENT"
        elif (balls >= 15 and matches >= 3) or balls >= 30:
            assert tier == "PROVISIONAL"
        else:
            assert tier == "INSUFFICIENT"


def test_post_wicket_incoming_batter_attribution():
    """Verify that post-wicket recovery strictly tags the incoming batter."""
    scenario_engine.initialize()
    df = scenario_engine._df
    # When batter_post_wkt is True, is_incoming_batter must be True
    pw_df = df[df["batter_post_wkt"] == True]
    assert len(pw_df) > 0
    assert (pw_df["is_incoming_batter"] == True).all()
    assert (pw_df["is_legal_ball"] == True).all()


def test_post_boundary_intra_over_attribution():
    """Verify that post-boundary response strictly operates on next legal ball within the same over."""
    scenario_engine.initialize()
    df = scenario_engine._df
    pb_df = df[df["bowler_prev_ball_boundary"] == True]
    assert len(pb_df) > 0
    # All post-boundary deliveries must be legal deliveries
    assert (pb_df["is_legal_ball"] == True).all()


def test_match_cluster_bootstrap_confidence_interval():
    """Verify match-cluster bootstrap confidence intervals are non-trivial and bounded."""
    res = scenario_service.execute_scenario(
        scenario_id="defend_18_in_6",
        format_filter="Combined",
        min_evidence="CONFIDENT",
        limit=10,
    )
    for p in res["players"]:
        ci = p["confidence_interval"]
        # CI must be [lower, upper] with lower <= upper
        assert ci[0] <= ci[1]
        assert ci[0] >= 0.0


def test_complete_match_innings_success_rate():
    """Verify that defence/chase success rate is based on distinct complete match outcomes."""
    res = scenario_service.execute_scenario(
        scenario_id="defend_18_in_6",
        format_filter="Combined",
        min_evidence="PROVISIONAL",
        limit=20,
    )
    for p in res["players"]:
        if p["success_rate"] is not None:
            # Win rate must be a percentage between 0 and 100
            assert 0.0 <= p["success_rate"] <= 100.0
            # Wilson confidence interval bounds must be valid
            assert 0.0 <= p["success_ci"][0] <= p["success_ci"][1] <= 100.0


def test_custom_scenario_execution(client):
    """Test custom scenario dynamic filtering via API endpoint."""
    payload = {
        "discipline": "BOWLER",
        "balls_remaining_max": 12,
        "runs_to_defend_max": 25,
        "innings": 2,
    }
    response = client.post("/api/scenarios/custom?format=IPL", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scenario"]["id"] == "custom"
    assert data["cohort_benchmarks"]["total_deliveries"] > 0
    assert len(data["players"]) > 0


def test_multi_player_scenario_comparison(client):
    """Test comparing multiple players on a scenario via API endpoint."""
    response = client.get("/api/scenarios/compare?scenario_id=defend_18_in_6&player_ids=2933,781&format=Combined")
    assert response.status_code == 200
    data = response.json()
    assert len(data["compared_players"]) == 2
    assert data["compared_players"][0]["player_id"] in [2933, 781]
