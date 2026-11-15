"""Scenario Lab Service for RR EDGE API.

Provides scenario catalog, execution, custom scenario modeling, player comparisons,
and player-level scenario profiles for the Player Intelligence Gallery.
"""

from typing import Any, Dict, List, Optional, Tuple
from .definitions import ALL_SCENARIOS, BOWLING_SCENARIOS, BATTING_SCENARIOS
from .engine import scenario_engine


class ScenarioService:
    """Service layer for Scenario Lab operations with caching."""

    def __init__(self):
        self._cache: Dict[Tuple[str, str, bool], Dict[str, Any]] = {}

    def _get_base_scenario(self, scenario_id: str, format_filter: str, use_relaxed: bool) -> Dict[str, Any]:
        """Fetch or compute the full unpaginated scenario result."""
        cache_key = (scenario_id, format_filter, use_relaxed)
        if cache_key in self._cache:
            return self._cache[cache_key]

        res = scenario_engine.execute_scenario(
            scenario_id=scenario_id,
            format_filter=format_filter,
            min_evidence="ALL",
            use_relaxed=use_relaxed,
            search=None,
            sort_by=None,
            limit=2000,
            offset=0,
        )
        self._cache[cache_key] = res
        return res

    def execute_scenario(
        self,
        scenario_id: str,
        format_filter: str = "IPL",
        min_evidence: str = "ALL",
        use_relaxed: bool = False,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        ascending: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Execute a standard scenario using cached base result with fast in-memory filtering."""
        base = self._get_base_scenario(scenario_id, format_filter, use_relaxed)
        players = list(base["players"])

        # Filter by min_evidence
        if min_evidence == "CONFIDENT":
            players = [p for p in players if p["evidence_tier"] == "CONFIDENT"]
        elif min_evidence == "PROVISIONAL":
            players = [p for p in players if p["evidence_tier"] in ["CONFIDENT", "PROVISIONAL"]]

        # Search filter
        if search:
            q = search.lower().strip()
            players = [p for p in players if q in p["player_name"].lower()]

        # Sort
        if sort_by:
            players.sort(key=lambda x: (x.get(sort_by, 0) or 0) if ascending else -(x.get(sort_by, 0) or 0))

        total_players = len(players)
        paginated = players[offset : offset + limit]

        return {
            "scenario": base["scenario"],
            "format": format_filter,
            "cohort_benchmarks": base["cohort_benchmarks"],
            "total_players": total_players,
            "players": paginated,
            "sample_episodes": base["sample_episodes"],
        }

    def get_catalog(self) -> Dict[str, Any]:
        """Return full catalog of standard bowling and batting scenarios."""
        bowling = [
            {
                "id": s.id,
                "name": s.name,
                "discipline": s.discipline,
                "category": s.category,
                "description": s.description,
                "tactical_intent": s.tactical_intent,
                "metric_focus": s.metric_focus,
                "exact_rules": s.exact_rules,
                "relaxed_rules": s.relaxed_rules,
                "relaxation_explanation": s.relaxation_explanation,
            }
            for s in BOWLING_SCENARIOS
        ]
        batting = [
            {
                "id": s.id,
                "name": s.name,
                "discipline": s.discipline,
                "category": s.category,
                "description": s.description,
                "tactical_intent": s.tactical_intent,
                "metric_focus": s.metric_focus,
                "exact_rules": s.exact_rules,
                "relaxed_rules": s.relaxed_rules,
                "relaxation_explanation": s.relaxation_explanation,
            }
            for s in BATTING_SCENARIOS
        ]
        return {
            "total_scenarios": len(bowling) + len(batting),
            "bowling_scenarios": bowling,
            "batting_scenarios": batting,
        }

    def execute_custom_scenario(
        self,
        config: Dict[str, Any],
        format_filter: str = "Combined",
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Execute a custom user-defined scenario."""
        return scenario_engine.execute_custom_scenario(
            config=config,
            format_filter=format_filter,
            search=search,
            limit=limit,
            offset=offset,
        )

    def compare_players(
        self,
        scenario_id: str,
        player_ids: List[int],
        format_filter: str = "Combined",
        use_relaxed: bool = False,
    ) -> Dict[str, Any]:
        """Compare multiple players on a specific scenario."""
        return scenario_engine.compare_players_on_scenario(
            scenario_id=scenario_id,
            player_ids=player_ids,
            format_filter=format_filter,
            use_relaxed=use_relaxed,
        )

    def get_player_scenarios(
        self,
        player_id: int,
        discipline: str = "BATTER",
        format_filter: str = "Combined",
    ) -> List[Dict[str, Any]]:
        """Extract a single player's performance across all standard scenarios."""
        standard_list = BOWLING_SCENARIOS if discipline == "BOWLER" else BATTING_SCENARIOS
        results: List[Dict[str, Any]] = []

        for scen in standard_list:
            res = self.execute_scenario(
                scenario_id=scen.id,
                format_filter=format_filter,
                min_evidence="ALL",
                limit=2000,
            )
            player_match = next((p for p in res["players"] if p["player_id"] == player_id), None)
            if player_match:
                results.append({
                    "scenario_id": scen.id,
                    "scenario_name": scen.name,
                    "category": scen.category,
                    "deliveries": player_match["deliveries"],
                    "primary_rate": player_match["primary_rate"],
                    "dot_pct": player_match["dot_pct"],
                    "boundary_pct": player_match["boundary_pct"],
                    "success_rate": player_match["success_rate"],
                    "context_diff": player_match["context_diff"],
                    "cohort_benchmark_rate": res["cohort_benchmarks"]["cohort_rate"],
                    "evidence_tier": player_match["evidence_tier"],
                    "confidence_interval": player_match["confidence_interval"],
                })
            else:
                results.append({
                    "scenario_id": scen.id,
                    "scenario_name": scen.name,
                    "category": scen.category,
                    "deliveries": 0,
                    "primary_rate": None,
                    "dot_pct": None,
                    "boundary_pct": None,
                    "success_rate": None,
                    "context_diff": 0.0,
                    "cohort_benchmark_rate": res["cohort_benchmarks"]["cohort_rate"],
                    "evidence_tier": "INSUFFICIENT",
                    "confidence_interval": [0.0, 0.0],
                })

        return results


# Singleton instance
scenario_service = ScenarioService()
