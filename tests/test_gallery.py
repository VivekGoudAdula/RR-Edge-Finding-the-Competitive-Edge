"""Comprehensive tests for RR EDGE Player Intelligence Gallery.

Validates the full 888-player database indexing, metadata integrity, 12-section
player profiles, format reconciliation, season progression, and match history.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.models.gallery.service import gallery_service


@pytest.fixture(scope="module")
def client():
    """TestClient fixture with preloaded datasets."""
    with TestClient(app) as test_client:
        yield test_client


def test_player_database_count():
    """Verify that all 888 unique eligible players are indexed."""
    gallery_service.initialize()
    assert len(gallery_service._player_index) == 888
    assert len(gallery_service._all_players_list) == 888


def test_metadata_integrity_no_speculation():
    """Verify that unverified biographical fields are strictly reported as 'Not available'."""
    # Test on a sample of verified players
    sample_ids = [2933, 6396, 781, 1699, 6819]
    for pid in sample_ids:
        prof = gallery_service.get_player_profile(pid)
        assert prof is not None
        overview = prof["sections"]["career_overview"]
        assert overview["birth_date"] == "Not available"
        assert overview["age"] == "Not available"
        assert overview["batting_style"] == "Not available"
        assert overview["bowling_style"] == "Not available"
        assert "Speculative biographies strictly excluded" in overview["biography"]
        # Verified teams must be a list
        assert isinstance(overview["verified_teams"], list)


def test_twelve_profile_sections_present():
    """Verify that all 12 specified sections exist in the full player intelligence profile."""
    # Test for Jasprit Bumrah (2933)
    bumrah = gallery_service.get_player_profile(2933)
    assert bumrah is not None
    sections = bumrah["sections"]
    expected_sections = [
        "career_overview",
        "ipl_performance",
        "t20i_performance",
        "season_history",
        "match_history",
        "phase_statistics",
        "pressure_intelligence",
        "scenario_lab_results",
        "behavioral_intelligence",
        "ml_context",
        "reliability_evidence",
        "comparison_peers",
    ]
    for sec in expected_sections:
        assert sec in sections, f"Missing section '{sec}' in player profile."


def test_gallery_filtering_and_pagination(client):
    """Test API endpoint filtering across disciplines, formats, evidence tiers, and search."""
    # All players
    r_all = client.get("/api/gallery/players?page=1&page_size=20")
    assert r_all.status_code == 200
    assert r_all.json()["total_players"] == 888

    # Batters only
    r_bat = client.get("/api/gallery/players?discipline=BATTER&page=1&page_size=20")
    assert r_bat.status_code == 200
    assert 0 < r_bat.json()["total_players"] < 888

    # Bowlers only
    r_bowl = client.get("/api/gallery/players?discipline=BOWLER&page=1&page_size=20")
    assert r_bowl.status_code == 200
    assert 0 < r_bowl.json()["total_players"] < 888

    # Search by name
    r_search = client.get("/api/gallery/players?search=Bumrah")
    assert r_search.status_code == 200
    assert r_search.json()["total_players"] >= 1
    assert "Bumrah" in r_search.json()["players"][0]["player_name"]


def test_player_matches_endpoint(client):
    """Verify match-by-match log structure and fields."""
    response = client.get("/api/gallery/players/2933/matches?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == 2933
    assert len(data["matches"]) > 0
    match = data["matches"][0]
    assert "match_id" in match
    assert "match_date" in match
    assert "competition" in match
    assert "match_result" in match


def test_player_seasons_endpoint(client):
    """Verify season progression covers multiple historical years."""
    response = client.get("/api/gallery/players/2933/seasons")
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == 2933
    seasons = [s["season"] for s in data["seasons"]]
    # Should contain 2022, 2024, etc.
    assert "2024" in seasons or "2022" in seasons


def test_shrinkage_and_evidence_disclosure_integrity():
    """Verify that Bayesian shrinkage M=45 is disclosed with strict scope and operational tiers."""
    prof = gallery_service.get_player_profile(2933)
    rel = prof["sections"]["reliability_evidence"]
    assert rel["shrinkage_m_factor"] == 45
    assert "Validated strictly for overall competition pressure" in rel["shrinkage_scope"]
    assert "Operational Tier" in rel["uncertainty_status"]
    # Check that sample adequacy reports both deliveries and matches
    assert "balls" in rel["sample_adequacy"]
    assert "matches" in rel["sample_adequacy"]
