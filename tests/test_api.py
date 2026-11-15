"""Unit tests for RR EDGE FastAPI backend endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health_check():
    """Verify health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_overview_endpoint():
    """Verify executive overview response structure."""
    response = client.get("/api/overview")
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert "top_10_batters" in data
    assert "top_10_bowlers" in data
    assert len(data["top_10_batters"]) == 10
    assert len(data["top_10_bowlers"]) == 10
    assert data["top_10_batters"][0]["player_name"] == "Tim David"
    assert data["top_10_bowlers"][0]["player_name"] == "Sunil Narine"


def test_batters_list_and_filter():
    """Verify batter list and search filtering."""
    response = client.get("/api/batters?search=Jaiswal")
    assert response.status_code == 200
    batters = response.json()
    assert len(batters) >= 1
    assert any("Jaiswal" in b["player_name"] for b in batters)


def test_batter_detail():
    """Verify detailed individual batter profile."""
    # Tim David ID = 6396
    response = client.get("/api/batters/6396")
    assert response.status_code == 200
    detail = response.json()
    assert detail["player"]["player_name"] == "Tim David"
    assert "phases" in detail
    assert "shrinkage_curve" in detail


def test_bowlers_list_and_detail():
    """Verify bowler list and individual profile."""
    # Narine ID = 781
    response = client.get("/api/bowlers/781")
    assert response.status_code == 200
    detail = response.json()
    assert detail["player"]["player_name"] == "Sunil Narine"
    assert detail["player"]["ipl_raw_econ"] == 6.7


def test_comparison_endpoint():
    """Verify head-to-head comparison endpoint."""
    # Compare David (6396) vs SKY (1699)
    response = client.get("/api/comparisons?player_a_id=6396&player_b_id=1699&discipline=BATTER")
    assert response.status_code == 200
    comp = response.json()
    assert comp["player_a"]["player"]["player_name"] == "Tim David"
    assert comp["player_b"]["player"]["player_name"] == "Suryakumar Yadav"
    assert comp["pairwise_bootstrap"] is not None
    assert comp["pairwise_bootstrap"]["pair_id"] == "BAT_RANK_1_VS_2"


def test_pressure_and_methodology():
    """Verify pressure distributions and methodology endpoints."""
    p_resp = client.get("/api/pressure/distributions")
    assert p_resp.status_code == 200
    assert "tiers" in p_resp.json()

    m_resp = client.get("/api/methodology")
    assert m_resp.status_code == 200
    assert "framework_steps" in m_resp.json()


def test_explorer_endpoint():
    """Verify pagination and search in explorer endpoint."""
    response = client.get("/api/explorer?discipline=BATTER&page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert len(data["rows"]) == 10
    assert data["total"] > 10


def test_behavioral_endpoints():
    """Verify behavioral intelligence API endpoints."""
    # 1. Overview
    resp_overview = client.get("/api/behavioral/overview")
    assert resp_overview.status_code == 200
    ov_data = resp_overview.json()
    assert "batters" in ov_data
    assert "bowlers" in ov_data
    assert ov_data["dataset_version"] == "v1.0-production"

    # 2. Batters list & search
    resp_batters = client.get("/api/behavioral/batters?query=David")
    assert resp_batters.status_code == 200
    b_data = resp_batters.json()
    assert b_data["total"] >= 1
    assert any("David" in b["striker_name"] for b in b_data["results"])

    # 3. Individual batter detail (Tim David ID = 6396)
    resp_b_detail = client.get("/api/behavioral/batters/6396")
    assert resp_b_detail.status_code == 200
    b_profile = resp_b_detail.json()
    assert b_profile["striker_name"] == "Tim David"
    assert b_profile["post_dot_strike_rate"] > 180.0
    assert b_profile["sample_confidence"] == "CONFIDENT"

    # 4. Bowlers list & search
    resp_bowlers = client.get("/api/behavioral/bowlers?query=Bumrah")
    assert resp_bowlers.status_code == 200
    bw_data = resp_bowlers.json()
    assert bw_data["total"] >= 1
    assert any("Bumrah" in b["bowler_name"] for b in bw_data["results"])

    # 5. Individual bowler detail (Jasprit Bumrah ID = 2933)
    resp_bw_detail = client.get("/api/behavioral/bowlers/2933")
    assert resp_bw_detail.status_code == 200
    bw_profile = resp_bw_detail.json()
    assert bw_profile["bowler_name"] == "Jasprit Bumrah"
    assert bw_profile["post_boundary_dot_pct"] > 35.0
    assert bw_profile["sample_confidence"] == "CONFIDENT"


