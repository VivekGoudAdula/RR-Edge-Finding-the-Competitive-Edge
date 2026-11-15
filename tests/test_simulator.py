"""Tests for Interactive 2D Cricket Simulator Service and Endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.models.simulator.service import simulator_service

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_simulator():
    """Ensure simulator service is initialized."""
    simulator_service.initialize()


def test_simulator_players_retrieval():
    """Test retrieving available players for simulator configuration."""
    players = simulator_service.get_available_players(discipline="ALL", limit=50)
    assert len(players) > 0
    first = players[0]
    assert "player_id" in first
    assert "player_name" in first
    assert "discipline" in first
    assert "matches" in first
    assert first["matches"] > 0


def test_simulator_preset_scenarios():
    """Test standard preset scenario definitions."""
    scenarios = simulator_service.get_preset_scenarios()
    assert len(scenarios) >= 8
    scenario_ids = [s["id"] for s in scenarios]
    assert "defend_12_in_2" in scenario_ids
    assert "defend_18_in_6" in scenario_ids
    assert "chase_18_in_12" in scenario_ids
    assert "chase_30_in_18" in scenario_ids


def test_simulator_historical_sequences():
    """Test indexing of real historical death match sequences."""
    sequences = simulator_service.get_historical_sequences(format_filter="ALL", limit=20)
    assert len(sequences) > 0
    seq = sequences[0]
    assert "match_id" in seq
    assert "situation_title" in seq
    assert "innings" in seq
    assert "runs_needed_start" in seq


def test_simulator_historical_sequence_deliveries_and_coordinates():
    """Test retrieving actual delivery sequence with 2D ground coordinates."""
    sequences = simulator_service.get_historical_sequences(format_filter="ALL", limit=5)
    assert len(sequences) > 0
    seq_meta = sequences[0]
    match_id = seq_meta["match_id"]
    innings = seq_meta["innings"]
    over_start = seq_meta.get("over_start", 19)
    over_end = seq_meta.get("over_end", 20)

    seq_data = simulator_service.get_historical_sequence_deliveries(
        match_id=match_id, innings=innings, over_start=over_start, over_end=over_end
    )
    assert "deliveries" in seq_data
    deliveries = seq_data["deliveries"]
    assert len(deliveries) > 0

    # Verify telemetry and geometric bounds
    for d in deliveries:
        assert "striker" in d
        assert "name" in d["striker"]
        assert "bowler" in d
        assert "name" in d["bowler"]
        assert "runs" in d
        assert "total_delivery_runs" in d
        assert "pitch_landing" in d
        assert "shot_trajectory" in d

        # Pitch landing
        assert 250.0 <= d["pitch_landing"]["x"] <= 350.0
        assert 250.0 <= d["pitch_landing"]["y"] <= 350.0
        # Shot path
        assert 0.0 <= d["shot_trajectory"]["target_x"] <= 600.0
        assert 0.0 <= d["shot_trajectory"]["target_y"] <= 600.0


def test_what_if_simulation_empirical_and_ml_hierarchy():
    """Test What-if illustrative simulation follows statistical hierarchy."""
    # Scenario: Jasprit Bumrah (2933) bowling to Tim David (6396), 12 off 2 balls
    payload = {
        "format": "IPL",
        "innings": 2,
        "batter_id": 6396,
        "bowler_id": 2933,
        "balls_remaining": 2,
        "runs_to_defend": 12,
        "wickets_remaining": 4,
        "current_score": 175,
        "target_runs": 187,
        "previous_context": "dot",
    }
    result = simulator_service.simulate_what_if_delivery(payload)

    assert result["illustrative_label"] == "Illustrative Simulation"
    assert "delivery_result" in result
    outcome = result["delivery_result"]
    assert "runs" in outcome
    assert "is_wicket" in outcome
    assert "pitch_landing" in outcome
    assert "shot_trajectory" in outcome
    assert "methodology_tier" in result
    assert "contextual_ml_baseline" in result

    # Check contextual ML baseline disclosure
    ml_base = result["contextual_ml_baseline"]
    assert "expected_runs_off_bat" in ml_base
    assert "wicket_probability" in ml_base
    assert "scope_disclosure" in ml_base


def test_fielding_presets():
    """Test retrieving fielding configurations."""
    presets = simulator_service.get_fielding_presets()
    assert "death_protection" in presets
    assert "powerplay" in presets
    assert "attacking" in presets

    dp = presets["death_protection"]
    assert len(dp) == 9
    for f in dp:
        assert "id" in f
        assert "name" in f
        assert 0.0 <= f["x"] <= 600.0
        assert 0.0 <= f["y"] <= 600.0


def test_head_to_head_analytics():
    """Test dual player analytics and head-to-head records."""
    res = simulator_service.get_head_to_head_analytics(
        batter_id=6396, bowler_id=2933, format_filter="ALL"
    )
    assert "batter" in res
    assert "bowler" in res
    assert "direct_head_to_head" in res
    assert res["batter"]["player_id"] == 6396
    assert res["bowler"]["player_id"] == 2933
    assert "dot_pct" in res["batter"]
    assert "dot_pct" in res["bowler"]


def test_simulator_api_endpoints():
    """Test that all FastAPI simulator routes return HTTP 200."""
    res_players = client.get("/api/simulator/players?limit=10")
    assert res_players.status_code == 200
    assert len(res_players.json()) > 0

    res_scenarios = client.get("/api/simulator/scenarios")
    assert res_scenarios.status_code == 200
    assert len(res_scenarios.json()) >= 8

    res_sequences = client.get("/api/simulator/historical/sequences?limit=10")
    assert res_sequences.status_code == 200
    assert len(res_sequences.json()) > 0

    first_seq = res_sequences.json()[0]
    match_id = first_seq["match_id"]
    res_seq = client.get(
        f"/api/simulator/historical/match/{match_id}/sequence?innings={first_seq['innings']}&over_start={first_seq['over_start']}&over_end={first_seq['over_end']}"
    )
    assert res_seq.status_code == 200
    assert "deliveries" in res_seq.json()

    res_fielding = client.get("/api/simulator/fielding/presets")
    assert res_fielding.status_code == 200

    res_h2h = client.get("/api/simulator/analytics/head-to-head?batter_id=6396&bowler_id=2933")
    assert res_h2h.status_code == 200

    sim_payload = {
        "format": "IPL",
        "innings": 2,
        "batter_id": 6396,
        "bowler_id": 2933,
        "balls_remaining": 6,
        "runs_to_defend": 18,
        "wickets_remaining": 5,
        "current_score": 160,
        "target_runs": 178,
    }
    res_sim = client.post("/api/simulator/simulate/delivery", json=sim_payload)
    assert res_sim.status_code == 200
    data = res_sim.json()
    assert data["illustrative_label"] == "Illustrative Simulation"


def test_what_if_match_state_and_strike_rotation():
    """Test detailed match-state updates: legal balls, strike rotation, and distinct matches."""
    payload = {
        "format": "IPL",
        "innings": 2,
        "batter_id": 6396,
        "bowler_id": 2933,
        "balls_remaining": 6,
        "runs_to_defend": 10,
        "wickets_remaining": 4,
        "current_score": 160,
    }
    res = simulator_service.simulate_what_if_delivery(payload)
    u_state = res["updated_state"]
    d_res = res["delivery_result"]
    samples = res["empirical_sample_sizes"]

    # Verify sample sizes report both deliveries and distinct matches
    assert "batter_phase_deliveries" in samples
    assert "batter_distinct_matches" in samples
    assert "bowler_phase_deliveries" in samples
    assert "bowler_distinct_matches" in samples

    # Verify strike rotation logic
    if d_res["runs"] % 2 == 1:
        # Odd runs rotate strike unless it is over completion which reverses ends
        if not u_state["over_completed"]:
            assert u_state["strike_rotated"] is True
    elif d_res["runs"] % 2 == 0 and not u_state["over_completed"]:
        assert u_state["strike_rotated"] is False

    # Legal balls accounting
    if d_res["is_legal_ball"]:
        assert u_state["balls_remaining"] == 5
    else:
        assert u_state["balls_remaining"] == 6

    # Score progression
    assert u_state["current_score"] == 160 + d_res["total_runs"]
    assert u_state["runs_to_defend"] == max(0, 10 - d_res["total_runs"])


def test_all_80_historical_sequences_consistency():
    """Verify all 80 historical sequences against underlying ball records."""
    seqs = simulator_service.get_historical_sequences(format_filter="ALL", limit=100)
    assert len(seqs) == 80

    for s in seqs:
        m_id = s["match_id"]
        res = simulator_service.get_historical_sequence_deliveries(
            match_id=m_id,
            innings=s["innings"],
            over_start=s["over_start"],
            over_end=s["over_end"],
        )
        assert "error" not in res
        deliveries = res["deliveries"]
        assert len(deliveries) == s["deliveries_count"]
        assert sum(d["total_delivery_runs"] for d in deliveries) == s["total_runs_scored"]
        assert sum(1 for d in deliveries if d["is_wicket"]) == s["total_wickets_fallen"]

