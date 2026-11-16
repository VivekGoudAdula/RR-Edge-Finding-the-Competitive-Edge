"""FastAPI Application for RR EDGE Cricket Intelligence Platform."""

from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from .data_service import data_service
from ..models.gallery.service import gallery_service
from ..models.scenarios.service import scenario_service
from ..models.simulator.service import simulator_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preload and cache datasets on API startup."""
    data_service.load_data()
    gallery_service.initialize()
    simulator_service.initialize()
    yield


app = FastAPI(
    title="RR EDGE Cricket Intelligence API",
    description="Explainable Multi-Model Cricket Intelligence System for Pressure Performance & Player Reliability.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for cross-domain requests (e.g. local dev, Vercel preview & production domains)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
@app.get("/health")
def root_health():
    """Root health check endpoint."""
    return {"status": "healthy", "service": "RR EDGE API", "version": "1.0.0"}


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "RR EDGE API"}


@app.get("/api/overview")
def get_overview():
    """Executive overview with dataset coverage, top 10 batters, top 10 bowlers, and discoveries."""
    return data_service.get_overview()


@app.get("/api/batters")
def get_batters(
    format_filter: str = Query("IPL", alias="format"),
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
):
    """Retrieve filtered batter candidates and evaluation matrix."""
    return data_service.get_batters(format_filter=format_filter, role=role, search=search, tier=tier)


@app.get("/api/batters/{player_id}")
def get_batter_detail(player_id: int):
    """Retrieve detailed scout dossier for an individual batter."""
    res = data_service.get_batter_detail(player_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Batter with ID {player_id} not found.")
    return res


@app.get("/api/bowlers")
def get_bowlers(
    format_filter: str = Query("IPL", alias="format"),
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
):
    """Retrieve filtered bowler candidates and evaluation matrix."""
    return data_service.get_bowlers(format_filter=format_filter, role=role, search=search, tier=tier)


@app.get("/api/bowlers/{player_id}")
def get_bowler_detail(player_id: int):
    """Retrieve detailed scout dossier for an individual bowler."""
    res = data_service.get_bowler_detail(player_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Bowler with ID {player_id} not found.")
    return res


@app.get("/api/comparisons")
def get_comparison(
    player_a_id: int = Query(...),
    player_b_id: int = Query(...),
    discipline: str = Query("BATTER"),
):
    """Head-to-head comparison with match-cluster bootstrap uncertainty intervals."""
    return data_service.get_comparison(player_a_id, player_b_id, discipline)


@app.get("/api/pressure/distributions")
def get_pressure_distributions():
    """Retrieve pressure vs normal performance, phase splits, and asymmetry framework."""
    return data_service.get_pressure_distributions()


@app.get("/api/methodology")
def get_methodology():
    """Retrieve model formulas, shrinkage sensitivity tables, and evidence tier rubrics."""
    return data_service.get_methodology()


@app.get("/api/explorer")
def get_explorer_data(
    discipline: str = Query("BATTER"),
    format_filter: str = Query("IPL", alias="format"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=5, le=100),
):
    """Search and paginate through underlying evaluation datasets."""
    return data_service.get_explorer_data(
        discipline=discipline,
        format_filter=format_filter,
        search=search,
        page=page,
        page_size=page_size,
    )


# -------------------------------------------------------------
# Supervised Machine Learning Intelligence Endpoints
# -------------------------------------------------------------
from ..models.ml.service import ml_service
from ..models.behavioral.service import (
    get_behavioral_overview,
    query_batters_behavioral,
    get_batter_behavioral_profile,
    query_bowlers_behavioral,
    get_bowler_behavioral_profile,
)


@app.get("/api/ml/overview")
def get_ml_overview():
    """Retrieve full supervised ML model performance, split manifests, and feature importance."""
    return ml_service.get_overview()


@app.get("/api/ml/predictions")
def get_ml_predictions(limit: int = Query(50, ge=1, le=200)):
    """Retrieve holdout test partition actual vs predicted records."""
    return ml_service.get_predictions(limit=limit)


@app.post("/api/ml/predict/batter")
def predict_batter(features: dict):
    """Run live inference for contextual delivery outcome expectation (off-bat runs) on a pre-delivery match state. Note: Evaluates match situation expectation, NOT individual player talent."""
    return ml_service.predict_batter_delivery(features)


@app.post("/api/ml/predict/bowler")
def predict_bowler(features: dict):
    """Run live inference for contextual conceded runs and bowler-credited wicket probability on a pre-delivery match state. Evaluates match context baseline, NOT individual player skill."""
    return ml_service.predict_bowler_delivery(features)


# -------------------------------------------------------------
# Behavioral Pressure Intelligence Endpoints
# -------------------------------------------------------------
@app.get("/api/behavioral/overview")
def get_behavioral_summary():
    """Retrieve observable behavioral response summary, benchmark distributions, and leaders."""
    return get_behavioral_overview()


@app.get("/api/behavioral/batters")
def list_batters_behavioral(
    query: Optional[str] = Query(None),
    confidence: Optional[str] = Query(None),
    sort_by: str = Query("scoring_resilience_index"),
    ascending: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Query and filter batter behavioral profiles with pagination."""
    return query_batters_behavioral(
        query=query,
        confidence=confidence,
        sort_by=sort_by,
        ascending=ascending,
        limit=limit,
        offset=offset,
    )


@app.get("/api/behavioral/batters/{player_id}")
def get_batter_behavioral(player_id: int):
    """Retrieve detailed behavioral response dossier for a single batter."""
    res = get_batter_behavioral_profile(player_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Batter with ID {player_id} not found in behavioral dataset.")
    return res


@app.get("/api/behavioral/bowlers")
def list_bowlers_behavioral(
    query: Optional[str] = Query(None),
    confidence: Optional[str] = Query(None),
    sort_by: str = Query("bounceback_index"),
    ascending: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Query and filter bowler behavioral profiles with pagination."""
    return query_bowlers_behavioral(
        query=query,
        confidence=confidence,
        sort_by=sort_by,
        ascending=ascending,
        limit=limit,
        offset=offset,
    )


@app.get("/api/behavioral/bowlers/{player_id}")
def get_bowler_behavioral(player_id: int):
    """Retrieve detailed behavioral bounce-back dossier for a single bowler."""
    res = get_bowler_behavioral_profile(player_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Bowler with ID {player_id} not found in behavioral dataset.")
    return res



# -------------------------------------------------------------
# Scenario Lab Endpoints
# -------------------------------------------------------------
from ..models.scenarios.service import scenario_service
from ..models.gallery.service import gallery_service


@app.get("/api/scenarios/catalog")
def get_scenario_catalog():
    """Retrieve full catalog of standardized bowling and batting scenarios."""
    return scenario_service.get_catalog()


@app.get("/api/scenarios/execute")
def execute_scenario(
    scenario_id: str = Query(...),
    format_filter: str = Query("IPL", alias="format"),
    min_evidence: str = Query("ALL"),
    use_relaxed: bool = Query(False),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    ascending: bool = Query(False),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Execute a standardized scenario against historical match states."""
    try:
        return scenario_service.execute_scenario(
            scenario_id=scenario_id,
            format_filter=format_filter,
            min_evidence=min_evidence,
            use_relaxed=use_relaxed,
            search=search,
            sort_by=sort_by,
            ascending=ascending,
            limit=limit,
            offset=offset,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/scenarios/custom")
def execute_custom_scenario(
    config: dict,
    format_filter: str = Query("Combined", alias="format"),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Execute a custom user-configured scenario."""
    return scenario_service.execute_custom_scenario(
        config=config,
        format_filter=format_filter,
        search=search,
        limit=limit,
        offset=offset,
    )


@app.get("/api/scenarios/compare")
def compare_scenario_players(
    scenario_id: str = Query(...),
    player_ids: str = Query(..., description="Comma-separated player IDs"),
    format_filter: str = Query("Combined", alias="format"),
    use_relaxed: bool = Query(False),
):
    """Compare multiple players on a specific scenario."""
    try:
        p_ids = [int(p.strip()) for p in player_ids.split(",") if p.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid player_ids format. Expected comma-separated integers.")
    return scenario_service.compare_players(
        scenario_id=scenario_id,
        player_ids=p_ids,
        format_filter=format_filter,
        use_relaxed=use_relaxed,
    )


# -------------------------------------------------------------
# Player Intelligence Gallery Endpoints
# -------------------------------------------------------------
@app.get("/api/gallery/players")
def list_gallery_players(
    discipline: str = Query("ALL"),
    format_filter: str = Query("ALL", alias="format"),
    season: str = Query("ALL"),
    evidence_tier: str = Query("ALL"),
    search: Optional[str] = Query(None),
    is_top_10_only: bool = Query(False),
    sort_by: str = Query("deliveries"),
    ascending: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
):
    """Search and filter the complete player intelligence database (888 players)."""
    return gallery_service.get_players(
        discipline=discipline,
        format_filter=format_filter,
        season=season,
        evidence_tier=evidence_tier,
        search=search,
        is_top_10_only=is_top_10_only,
        sort_by=sort_by,
        ascending=ascending,
        page=page,
        page_size=page_size,
    )


@app.get("/api/gallery/players/{player_id}")
def get_gallery_player_profile(player_id: int):
    """Retrieve complete 12-section player intelligence profile."""
    profile = gallery_service.get_player_profile(player_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Player with ID {player_id} not found in database.")
    return profile


@app.get("/api/gallery/players/{player_id}/matches")
def get_gallery_player_matches(player_id: int, limit: int = Query(25, ge=1, le=100)):
    """Retrieve recent match-by-match history for an individual player."""
    profile = gallery_service.get_player_profile(player_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Player with ID {player_id} not found.")
    return {
        "player_id": player_id,
        "player_name": profile["card"]["player_name"],
        "matches": profile["sections"]["match_history"][:limit],
    }


@app.get("/api/gallery/players/{player_id}/seasons")
def get_gallery_player_seasons(player_id: int):
    """Retrieve season-by-season progression for an individual player."""
    profile = gallery_service.get_player_profile(player_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Player with ID {player_id} not found.")
    return {
        "player_id": player_id,
        "player_name": profile["card"]["player_name"],
        "seasons": profile["sections"]["season_history"],
    }


# -------------------------------------------------------------
# Interactive 2D Cricket Simulator Endpoints
# -------------------------------------------------------------
@app.get("/api/simulator/players")
def get_simulator_players(
    discipline: str = Query("ALL"),
    format_filter: str = Query("ALL", alias="format"),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """Retrieve indexed players for the simulator setup with evidence counts."""
    return simulator_service.get_available_players(
        discipline=discipline,
        format_filter=format_filter,
        search=search,
        limit=limit,
    )


@app.get("/api/simulator/scenarios")
def get_simulator_scenarios():
    """Retrieve standard simulator preset scenarios."""
    return simulator_service.get_preset_scenarios()


@app.get("/api/simulator/historical/sequences")
def get_simulator_historical_sequences(
    format_filter: str = Query("ALL", alias="format"),
    scenario_type: str = Query("ALL"),
    limit: int = Query(50, ge=1, le=200),
):
    """Retrieve indexed real historical death chase and defense match sequences."""
    scen_id = None if scenario_type == "ALL" else scenario_type
    return simulator_service.get_historical_sequences(
        format_filter=format_filter,
        scenario_id=scen_id,
        limit=limit,
    )


@app.get("/api/simulator/historical/match/{match_id}/sequence")
def get_simulator_sequence_deliveries(
    match_id: int,
    innings: int = Query(2, ge=1, le=2),
    over_start: int = Query(19, ge=1, le=20),
    over_end: int = Query(20, ge=1, le=20),
):
    """Retrieve delivery sequence with ground coordinates and recorded telemetry."""
    seq = simulator_service.get_historical_sequence_deliveries(
        match_id=match_id,
        innings=innings,
        over_start=over_start,
        over_end=over_end,
    )
    if not seq or not seq.get("deliveries"):
        raise HTTPException(status_code=404, detail="Historical sequence not found or contains no deliveries.")
    return seq


@app.post("/api/simulator/simulate/delivery")
def simulate_delivery_outcome(payload: Dict[str, Any] = Body(...)):
    """Simulate a single illustrative delivery outcome using empirical and contextual ML hierarchy."""
    return simulator_service.simulate_what_if_delivery(payload)


@app.get("/api/simulator/analytics/head-to-head")
def get_simulator_head_to_head(
    batter_id: int = Query(...),
    bowler_id: int = Query(...),
    format_filter: str = Query("ALL", alias="format"),
):
    """Retrieve dual player analytics and head-to-head encounter records."""
    return simulator_service.get_head_to_head_analytics(
        batter_id=batter_id,
        bowler_id=bowler_id,
        format_filter=format_filter,
    )


@app.get("/api/simulator/fielding/presets")
def get_simulator_fielding_presets():
    """Retrieve standard fielding configurations with coordinates."""
    return simulator_service.get_fielding_presets()



# Mount built production frontend and static assets
from pathlib import Path
from fastapi.staticfiles import StaticFiles

frontend_players = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "players"
if frontend_players.exists():
    app.mount("/players", StaticFiles(directory=str(frontend_players)), name="players")

frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

