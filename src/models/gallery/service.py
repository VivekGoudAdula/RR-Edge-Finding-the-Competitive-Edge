"""Player Intelligence Gallery Service for RR EDGE.

Provides a unified, searchable gallery of all 888 unique eligible players
(819 batters, 595 bowlers) with comprehensive 12-section player intelligence profiles.
Strictly relies on verified historical data without biographical speculation.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from ..scenarios.service import scenario_service

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
FINAL_DIR = PROCESSED_DIR / "final_selections"
EVAL_DIR = PROCESSED_DIR / "player_evaluations"
METRICS_DIR = PROCESSED_DIR / "player_metrics"
BEH_DIR = PROCESSED_DIR / "behavioral"
ML_DIR = PROCESSED_DIR / "ml"


def _safe_int(val: Any, default: int = 0) -> int:
    """Convert value safely to int, handling None, NaN, and strings."""
    if val is None or pd.isna(val):
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def _safe_float(val: Any, default: Optional[float] = None, round_digits: int = 1) -> Optional[float]:
    """Convert value safely to rounded float, returning default if None or NaN."""
    if val is None or pd.isna(val):
        return default
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return default
        return round(f, round_digits)
    except (ValueError, TypeError):
        return default


class GalleryService:
    """Service for searching, filtering, and compiling player intelligence profiles."""

    def __init__(self):
        self._bat_metrics: Optional[pd.DataFrame] = None
        self._bowl_metrics: Optional[pd.DataFrame] = None
        self._bat_formats: Optional[pd.DataFrame] = None
        self._bowl_formats: Optional[pd.DataFrame] = None
        self._bat_phase: Optional[pd.DataFrame] = None
        self._bowl_phase: Optional[pd.DataFrame] = None
        self._top_10_bat: Optional[pd.DataFrame] = None
        self._top_10_bowl: Optional[pd.DataFrame] = None
        self._team_mapping: Optional[pd.DataFrame] = None
        self._playing_eleven: Optional[pd.DataFrame] = None
        self._deliv_df: Optional[pd.DataFrame] = None
        self._matches_df: Optional[pd.DataFrame] = None
        self._bat_behavioral: Optional[pd.DataFrame] = None
        self._bowl_behavioral: Optional[pd.DataFrame] = None
        self._bat_ml_preds: Optional[pd.DataFrame] = None
        self._bowl_ml_preds: Optional[pd.DataFrame] = None
        self._player_index: Optional[Dict[int, Dict[str, Any]]] = None
        self._all_players_list: Optional[List[Dict[str, Any]]] = None
        self._initialized = False

    def initialize(self) -> None:
        """Load datasets and compile the unified player index."""
        if self._initialized:
            return

        # Load metrics tables
        self._bat_metrics = pd.read_parquet(METRICS_DIR / "batter_metrics_overall.parquet")
        self._bowl_metrics = pd.read_parquet(METRICS_DIR / "bowler_metrics_overall.parquet")
        self._bat_formats = pd.read_parquet(METRICS_DIR / "batter_metrics_formats.parquet")
        self._bowl_formats = pd.read_parquet(METRICS_DIR / "bowler_metrics_formats.parquet")
        self._bat_phase = pd.read_parquet(EVAL_DIR / "batter_phase_metrics.parquet")
        self._bowl_phase = pd.read_parquet(EVAL_DIR / "bowler_phase_metrics.parquet")
        self._bat_eval = pd.read_parquet(EVAL_DIR / "batter_evaluation.parquet")
        self._bowl_eval = pd.read_parquet(EVAL_DIR / "bowler_evaluation.parquet")

        # Selections
        self._top_10_bat = pd.read_parquet(FINAL_DIR / "top_10_batters.parquet")
        self._top_10_bowl = pd.read_parquet(FINAL_DIR / "top_10_bowlers.parquet")

        # Behavioral & ML
        self._bat_behavioral = pd.read_parquet(BEH_DIR / "batter_behavioral.parquet")
        self._bowl_behavioral = pd.read_parquet(BEH_DIR / "bowler_behavioral.parquet")
        self._bat_ml_preds = pd.read_parquet(ML_DIR / "batter_test_predictions.parquet")
        self._bowl_ml_preds = pd.read_parquet(ML_DIR / "bowler_test_predictions.parquet")

        # Raw metadata
        self._team_mapping = pd.read_csv(RAW_DIR / "competition_team_player_mapping.csv")
        self._playing_eleven = pd.read_csv(RAW_DIR / "playing_eleven.csv")
        self._matches_df = pd.read_csv(RAW_DIR / "matches.csv")
        self._deliv_df = pd.read_parquet(PROCESSED_DIR / "pressure_deliveries.parquet")

        # Build player index
        self._compile_player_index()
        self._initialized = True

    def _compile_player_index(self) -> None:
        """Build consolidated dictionary of all 888 players with verified metadata."""
        # Top 10 maps
        top_bat_map = self._top_10_bat.set_index("player_id")["top_10_rank"].to_dict()
        top_bowl_map = self._top_10_bowl.set_index("player_id")["top_10_rank"].to_dict()

        # Wicketkeeper identification
        wk_ids = set(self._playing_eleven[self._playing_eleven["is_wk"] == True]["player_id"])

        # Evaluation role maps
        bat_role_map = self._bat_eval.set_index("striker_id")["primary_batting_role"].to_dict()
        bowl_role_map = self._bowl_eval.set_index("bowler_id")["primary_bowling_role"].to_dict()

        # Teams mapping: player_id -> list of unique team names
        team_map = self._team_mapping.groupby("player_id")["team_name"].unique().to_dict()

        # Format mapping from delivery dataset
        deliv_formats = self._deliv_df.groupby("striker_id")["competition_type"].unique().to_dict()
        bowl_deliv_formats = self._deliv_df.groupby("bowler_id")["competition_type"].unique().to_dict()

        bat_dict = self._bat_metrics.set_index("striker_id").to_dict(orient="index")
        bowl_dict = self._bowl_metrics.set_index("bowler_id").to_dict(orient="index")

        all_pids = set(bat_dict.keys()).union(set(bowl_dict.keys()))

        index: Dict[int, Dict[str, Any]] = {}
        players_list: List[Dict[str, Any]] = []

        for pid in sorted(all_pids):
            has_bat = pid in bat_dict
            has_bowl = pid in bowl_dict
            b_info = bat_dict.get(pid, {})
            bw_info = bowl_dict.get(pid, {})

            p_name = b_info.get("striker_name") or bw_info.get("bowler_name") or f"Player {pid}"

            # Determine role & discipline strictly supported by metadata
            is_wk = pid in wk_ids
            has_both_records = has_bat and has_bowl
            bat_b = b_info.get("balls_faced", 0)
            bowl_b = bw_info.get("legal_balls", 0)

            bat_pos_role = bat_role_map.get(pid)
            bowl_pos_role = bowl_role_map.get(pid)

            if is_wk:
                role = "Wicketkeeper Batter"
                discipline = "BATTER"
            elif has_both_records and bat_b >= 100 and bowl_b >= 100:
                # Genuine dual-discipline contributor with substantial exposure in both facets
                role = "Dual-Discipline Contributor (Bat & Bowl)"
                discipline = "ALL_ROUNDER"
            elif has_bat and (not has_bowl or bat_b >= bowl_b):
                pos_str = f"{bat_pos_role} " if bat_pos_role else ""
                role = f"{pos_str}Batter"
                discipline = "BATTER"
            else:
                bowl_str = f"{bowl_pos_role} " if bowl_pos_role else "Specialist "
                role = f"{bowl_str}Bowler"
                discipline = "BOWLER"

            # Formats
            formats_set = set()
            if pid in deliv_formats:
                formats_set.update(deliv_formats[pid])
            if pid in bowl_deliv_formats:
                formats_set.update(bowl_deliv_formats[pid])
            formats_list = sorted(list(formats_set)) if formats_set else ["IPL"]

            # Matches and deliveries
            matches = max(b_info.get("matches", 0), bw_info.get("matches", 0))
            deliveries = b_info.get("balls_faced", 0) + bw_info.get("total_deliveries", 0)

            # Top 10 status
            is_top_10 = (pid in top_bat_map) or (pid in top_bowl_map)
            top_10_rank = top_bat_map.get(pid) or top_bowl_map.get(pid)

            # Primary performance rate
            if discipline in ["BATTER", "ALL_ROUNDER"] and has_bat:
                primary_rate = round(float(b_info.get("strike_rate", 0.0)), 1)
                rate_label = "Strike Rate"
            elif has_bowl:
                primary_rate = round(float(bw_info.get("economy_rate", 0.0)), 2)
                rate_label = "Economy Rate"
            else:
                primary_rate = round(float(b_info.get("strike_rate", 0.0)), 1)
                rate_label = "Strike Rate"

            # Pressure performance indicator (RAE or RCAE)
            pressure_indicator = None
            if pid in self._top_10_bat.set_index("player_id").index:
                t_row = self._top_10_bat.loc[self._top_10_bat["player_id"] == pid].iloc[0]
                val = t_row.get("ipl_context_delta_sr")
                pressure_indicator = f"RAE {round(float(val), 1):+0.1f}" if pd.notna(val) else None
            elif pid in self._top_10_bowl.set_index("player_id").index:
                t_row = self._top_10_bowl.loc[self._top_10_bowl["player_id"] == pid].iloc[0]
                val = t_row.get("ipl_context_delta_econ")
                pressure_indicator = f"RCAE {round(float(val), 2):+0.2f}" if pd.notna(val) else None

            # Evidence tier
            if deliveries >= 100 or matches >= 15:
                evidence_tier = "CONFIDENT"
            elif deliveries >= 30:
                evidence_tier = "PROVISIONAL"
            else:
                evidence_tier = "INSUFFICIENT"

            # Verified teams
            teams = [str(t) for t in team_map.get(pid, []) if pd.notna(t)]

            card = {
                "player_id": int(pid),
                "player_name": str(p_name),
                "role": role,
                "discipline": discipline,
                "formats": formats_list,
                "matches": int(matches),
                "deliveries": int(deliveries),
                "is_top_10": bool(is_top_10),
                "top_10_rank": int(top_10_rank) if top_10_rank is not None else None,
                "primary_rate": primary_rate,
                "rate_label": rate_label,
                "pressure_indicator": pressure_indicator,
                "evidence_tier": evidence_tier,
                "verified_teams": teams,
                "has_dual_records": bool(has_both_records),
                "dual_records_detail": f"Batting ({bat_b}b) & Bowling ({bowl_b}b)" if has_both_records else None,
            }
            index[pid] = card
            players_list.append(card)

        self._player_index = index
        self._all_players_list = players_list

    def get_players(
        self,
        discipline: str = "ALL",  # 'ALL' | 'BATTER' | 'BOWLER' | 'ALL_ROUNDER'
        format_filter: str = "ALL",  # 'ALL' | 'IPL' | 'T20I'
        season: str = "ALL",  # 'ALL' | '2022' | '2023' | '2024' | '2025' | '2026'
        evidence_tier: str = "ALL",  # 'ALL' | 'CONFIDENT' | 'PROVISIONAL'
        search: Optional[str] = None,
        is_top_10_only: bool = False,
        sort_by: str = "deliveries",
        ascending: bool = False,
        page: int = 1,
        page_size: int = 24,
    ) -> Dict[str, Any]:
        """Search and filter players with pagination."""
        self.initialize()
        filtered = self._all_players_list

        # Discipline filter
        if discipline != "ALL":
            filtered = [p for p in filtered if p["discipline"] == discipline]

        # Format filter
        if format_filter != "ALL":
            filtered = [p for p in filtered if format_filter in p["formats"]]

        # Evidence tier
        if evidence_tier != "ALL":
            filtered = [p for p in filtered if p["evidence_tier"] == evidence_tier]

        # Top 10 filter
        if is_top_10_only:
            filtered = [p for p in filtered if p["is_top_10"]]

        # Search by player name
        if search:
            q = search.lower().strip()
            filtered = [p for p in filtered if q in p["player_name"].lower()]

        # Sort
        sort_key = sort_by if sort_by in ["deliveries", "matches", "primary_rate", "player_name"] else "deliveries"
        if sort_key == "player_name":
            filtered = sorted(filtered, key=lambda x: x["player_name"].lower(), reverse=ascending)
        else:
            filtered = sorted(
                filtered,
                key=lambda x: (
                    0 if x["is_top_10"] else 1,
                    x.get(sort_key, 0) if ascending else -(x.get(sort_key, 0) or 0),
                ),
            )

        total_players = len(filtered)
        start_idx = (page - 1) * page_size
        paginated = filtered[start_idx : start_idx + page_size]

        return {
            "total_players": total_players,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, int(np.ceil(total_players / page_size))),
            "players": paginated,
        }

    def get_player_profile(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Construct the complete 12-section Player Intelligence Profile."""
        self.initialize()
        card = self._player_index.get(player_id)
        if not card:
            return None

        # 1. Career Overview (Strictly Verified Metadata)
        overview = {
            "player_id": player_id,
            "player_name": card["player_name"],
            "role": card["role"],
            "discipline": card["discipline"],
            "formats": card["formats"],
            "verified_teams": card["verified_teams"],
            "career_matches": card["matches"],
            "career_deliveries": card["deliveries"],
            "is_top_10": card["is_top_10"],
            "top_10_rank": card["top_10_rank"],
            "birth_date": "Not available",
            "age": "Not available",
            "nationality": "Not available (Verified via Team Rosters)",
            "batting_style": "Not available",
            "bowling_style": "Not available",
            "biography": "Not available (Speculative biographies strictly excluded under RR EDGE rules)",
        }

        # 2. IPL Performance
        ipl_perf = self._get_format_performance(player_id, "IPL")

        # 3. T20I Performance
        t20i_perf = self._get_format_performance(player_id, "T20I")

        # 4. Season-by-Season History
        season_history = self._get_season_history(player_id)

        # 5. Match-by-Match History
        match_history = self._get_match_history(player_id)

        # 6. Innings Phase Splits
        phase_stats = self._get_phase_splits(player_id)

        # 7. Pressure Intelligence
        pressure_intel = self._get_pressure_intel(player_id)

        # 8. Scenario Lab Results
        scenario_results = scenario_service.get_player_scenarios(
            player_id=player_id,
            discipline=card["discipline"] if card["discipline"] != "ALL_ROUNDER" else "BATTER",
            format_filter="Combined",
        )

        # 9. Behavioral Intelligence
        behavioral_intel = self._get_behavioral_intel(player_id, card["discipline"])

        # 10. ML Context
        ml_context = self._get_ml_context(player_id, card["discipline"])

        # 11. Reliability & Statistical Evidence
        reliability_stats = self._get_reliability_stats(player_id, card["discipline"])

        # 12. Player Comparison Peers
        comparison_peers = self._get_comparison_peers(player_id, card["discipline"])

        return {
            "player_id": player_id,
            "card": card,
            "sections": {
                "career_overview": overview,
                "ipl_performance": ipl_perf,
                "t20i_performance": t20i_perf,
                "season_history": season_history,
                "match_history": match_history,
                "phase_statistics": phase_stats,
                "pressure_intelligence": pressure_intel,
                "scenario_lab_results": scenario_results,
                "behavioral_intelligence": behavioral_intel,
                "ml_context": ml_context,
                "reliability_evidence": reliability_stats,
                "comparison_peers": comparison_peers,
            },
        }

    def _get_format_performance(self, player_id: int, format_name: str) -> Dict[str, Any]:
        """Extract format-specific batting and bowling performance."""
        # Batting format metrics
        bat_row = None
        if self._bat_formats is not None and player_id in self._bat_formats["striker_id"].values:
            b_sub = self._bat_formats[self._bat_formats["striker_id"] == player_id]
            if not b_sub.empty:
                bat_row = b_sub.iloc[0]

        # Bowling format metrics
        bowl_row = None
        if self._bowl_formats is not None and player_id in self._bowl_formats["bowler_id"].values:
            bw_sub = self._bowl_formats[self._bowl_formats["bowler_id"] == player_id]
            if not bw_sub.empty:
                bowl_row = bw_sub.iloc[0]

        prefix = f"{format_name}_"
        batting_stats = None
        if bat_row is not None and f"{prefix}balls_faced" in bat_row and pd.notna(bat_row[f"{prefix}balls_faced"]):
            bf = _safe_int(bat_row.get(f"{prefix}balls_faced"))
            if bf > 0:
                batting_stats = {
                    "matches": _safe_int(bat_row.get(f"{prefix}matches")),
                    "balls_faced": bf,
                    "runs": _safe_int(bat_row.get(f"{prefix}runs")),
                    "strike_rate": _safe_float(bat_row.get(f"{prefix}strike_rate"), 0.0, 1),
                    "fours": _safe_int(bat_row.get(f"{prefix}fours")),
                    "sixes": _safe_int(bat_row.get(f"{prefix}sixes")),
                    "dot_ball_pct": _safe_float(bat_row.get(f"{prefix}dot_ball_pct"), 0.0, 1),
                    "boundary_runs_pct": _safe_float(bat_row.get(f"{prefix}boundary_runs_pct"), 0.0, 1),
                    "pressure_balls": _safe_int(bat_row.get(f"{prefix}pressure_balls_faced")),
                    "pressure_strike_rate": _safe_float(bat_row.get(f"{prefix}pressure_strike_rate"), None, 1),
                }

        bowling_stats = None
        if bowl_row is not None and f"{prefix}legal_balls" in bowl_row and pd.notna(bowl_row[f"{prefix}legal_balls"]):
            lb = _safe_int(bowl_row.get(f"{prefix}legal_balls"))
            if lb > 0:
                bowling_stats = {
                    "matches": _safe_int(bowl_row.get(f"{prefix}matches")),
                    "legal_balls": lb,
                    "overs": _safe_float(bowl_row.get(f"{prefix}overs", lb / 6.0), round(lb / 6.0, 1), 1),
                    "runs_conceded": _safe_int(bowl_row.get(f"{prefix}runs_conceded")),
                    "wickets": _safe_int(bowl_row.get(f"{prefix}wickets")),
                    "economy_rate": _safe_float(bowl_row.get(f"{prefix}economy_rate"), 0.0, 2),
                    "dot_ball_pct": _safe_float(bowl_row.get(f"{prefix}dot_ball_pct"), 0.0, 1),
                    "bowling_average": _safe_float(bowl_row.get(f"{prefix}bowling_average"), None, 2),
                    "pressure_balls": _safe_int(bowl_row.get(f"{prefix}pressure_legal_balls")),
                    "pressure_economy": _safe_float(bowl_row.get(f"{prefix}pressure_economy_rate"), None, 2),
                }

        return {
            "format": format_name,
            "has_data": (batting_stats is not None) or (bowling_stats is not None),
            "batting": batting_stats,
            "bowling": bowling_stats,
        }

    def _get_season_history(self, player_id: int) -> List[Dict[str, Any]]:
        """Extract season-by-season progression across 2022-2026."""
        df = self._deliv_df
        b_sub = df[df["striker_id"] == player_id]
        bw_sub = df[df["bowler_id"] == player_id]

        seasons_set = set(b_sub["season"].unique()).union(set(bw_sub["season"].unique()))
        history: List[Dict[str, Any]] = []

        for s in sorted(list(seasons_set)):
            s_b = b_sub[b_sub["season"] == s]
            s_bw = bw_sub[bw_sub["season"] == s]

            b_legal = s_b[s_b["is_legal_ball"] == True]
            bw_legal = s_bw[s_bw["is_legal_ball"] == True]

            bat_balls = len(b_legal)
            bat_runs = int(s_b["runs"].sum())
            bat_sr = round(bat_runs / bat_balls * 100.0, 1) if bat_balls > 0 else None

            bowl_balls = len(bw_legal)
            bowl_runs = int(s_bw["total_delivery_runs"].sum())
            bowl_wkts = int(s_bw["is_bowler_wkt"].sum())
            bowl_econ = round(bowl_runs / bowl_balls * 6.0, 2) if bowl_balls > 0 else None

            matches = int(max(s_b["match_id"].nunique(), s_bw["match_id"].nunique()))

            history.append({
                "season": str(s),
                "matches": matches,
                "batting_balls": bat_balls,
                "batting_runs": bat_runs,
                "batting_strike_rate": bat_sr,
                "bowling_balls": bowl_balls,
                "bowling_runs": bowl_runs,
                "bowling_wickets": bowl_wkts,
                "bowling_economy": bowl_econ,
            })

        return history

    def _get_match_history(self, player_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Extract recent match-by-match performances."""
        df = self._deliv_df
        matches = self._matches_df.set_index("match_id").to_dict(orient="index")

        p_deliv = df[(df["striker_id"] == player_id) | (df["bowler_id"] == player_id)]
        m_groups = p_deliv.groupby("match_id", sort=False)

        match_logs: List[Dict[str, Any]] = []
        for m_id, m_df in list(m_groups)[-limit:]:
            m_info = matches.get(m_id, {})
            m_date = m_info.get("match_date", "Unknown")
            comp = m_df["comp_name"].iloc[0]
            
            # Batting in match
            b_df = m_df[m_df["striker_id"] == player_id]
            b_legal = b_df[b_df["is_legal_ball"] == True]
            b_runs = int(b_df["runs"].sum()) if not b_df.empty else None
            b_balls = len(b_legal) if not b_df.empty else None
            b_sr = round(b_runs / b_balls * 100.0, 1) if (b_balls and b_balls > 0) else None

            # Bowling in match
            bw_df = m_df[m_df["bowler_id"] == player_id]
            bw_legal = bw_df[bw_df["is_legal_ball"] == True]
            bw_runs = int(bw_df["total_delivery_runs"].sum()) if not bw_df.empty else None
            bw_balls = len(bw_legal) if not bw_df.empty else None
            bw_wkts = int(bw_df["is_bowler_wkt"].sum()) if not bw_df.empty else None
            bw_econ = round(bw_runs / bw_balls * 6.0, 2) if (bw_balls and bw_balls > 0) else None

            match_logs.append({
                "match_id": int(m_id),
                "match_date": str(m_date),
                "competition": str(comp),
                "home_team": str(m_info.get("home_team", "")),
                "away_team": str(m_info.get("away_team", "")),
                "venue_country": str(m_info.get("venue_country", "India")),
                "batting_runs": b_runs,
                "batting_balls": b_balls,
                "batting_strike_rate": b_sr,
                "bowling_balls": bw_balls,
                "bowling_runs": bw_runs,
                "bowling_wickets": bw_wkts,
                "bowling_economy": bw_econ,
                "match_result": str(m_info.get("result", "Completed")),
            })

        # Reverse to show newest first
        return list(reversed(match_logs))

    def _get_phase_splits(self, player_id: int) -> Dict[str, Any]:
        """Extract phase splits (Powerplay, Middle, Death)."""
        bat_phases = {}
        if self._bat_phase is not None and player_id in self._bat_phase["striker_id"].values:
            sub = self._bat_phase[self._bat_phase["striker_id"] == player_id]
            for _, r in sub.iterrows():
                ph = r["innings_phase"]
                bat_phases[ph] = {
                    "balls": int(r.get("phase_pressure_balls", 0)),
                    "runs": int(r.get("phase_pressure_runs", 0)),
                    "strike_rate": round(float(r.get("phase_pressure_sr", 0.0)), 1) if pd.notna(r.get("phase_pressure_sr")) else 0.0,
                    "dot_ball_pct": round(float(r.get("phase_pressure_dot_pct", 0.0)), 1) if pd.notna(r.get("phase_pressure_dot_pct")) else 0.0,
                    "boundary_runs_pct": round(float(r.get("phase_pressure_boundary_pct", 0.0)), 1) if pd.notna(r.get("phase_pressure_boundary_pct")) else 0.0,
                }

        bowl_phases = {}
        if self._bowl_phase is not None and player_id in self._bowl_phase["bowler_id"].values:
            sub = self._bowl_phase[self._bowl_phase["bowler_id"] == player_id]
            for _, r in sub.iterrows():
                ph = r["bowler_innings_phase"]
                bowl_phases[ph] = {
                    "legal_balls": int(r.get("phase_pressure_balls", 0)),
                    "runs_conceded": int(r.get("phase_pressure_runs", 0)),
                    "wickets": int(r.get("phase_pressure_wickets", 0)),
                    "economy": round(float(r.get("phase_pressure_economy", 0.0)), 2) if pd.notna(r.get("phase_pressure_economy")) else 0.0,
                    "dot_ball_pct": round(float(r.get("phase_pressure_dot_pct", 0.0)), 1) if pd.notna(r.get("phase_pressure_dot_pct")) else 0.0,
                }

        return {
            "batting_phases": bat_phases,
            "bowling_phases": bowl_phases,
        }

    def _get_pressure_intel(self, player_id: int) -> Dict[str, Any]:
        """Extract pressure exposure and par deficit statistics."""
        df = self._deliv_df
        b_deliv = df[(df["striker_id"] == player_id) & (df["is_primary_pressure_cohort"] == True)]
        bw_deliv = df[(df["bowler_id"] == player_id) & (df["is_primary_pressure_cohort"] == True)]

        bat_tiers = b_deliv["batter_pressure_tier"].value_counts().to_dict() if not b_deliv.empty else {}
        bowl_tiers = bw_deliv["bowler_pressure_tier"].value_counts().to_dict() if not bw_deliv.empty else {}

        return {
            "batting_pressure_balls": len(b_deliv),
            "batting_tier_distribution": bat_tiers,
            "bowling_pressure_balls": len(bw_deliv),
            "bowling_tier_distribution": bowl_tiers,
        }

    def _get_behavioral_intel(self, player_id: int, discipline: str) -> Optional[Dict[str, Any]]:
        """Extract behavioral response metrics."""
        if discipline in ["BATTER", "ALL_ROUNDER"] and self._bat_behavioral is not None:
            sub = self._bat_behavioral[self._bat_behavioral["striker_id"] == player_id]
            if not sub.empty:
                r = sub.iloc[0]
                return {
                    "type": "BATTER",
                    "scoring_resilience_index": round(float(r.get("scoring_resilience_index", 0.0)), 1),
                    "drought_recovery_sr": round(float(r.get("post_dot_strike_rate", 0.0)), 1),
                    "drought_balls": int(r.get("post_dot_balls", 0)),
                    "latency_to_score_median": round(float(r.get("latency_to_score_median", 0.0)), 1),
                    "confidence_tier": str(r.get("confidence_tier", "INSUFFICIENT")),
                }
        if self._bowl_behavioral is not None:
            sub = self._bowl_behavioral[self._bowl_behavioral["bowler_id"] == player_id]
            if not sub.empty:
                r = sub.iloc[0]
                return {
                    "type": "BOWLER",
                    "bounceback_index": round(float(r.get("bounceback_index", 0.0)), 1),
                    "post_boundary_economy": round(float(r.get("post_boundary_economy", 0.0)), 2),
                    "post_boundary_balls": int(r.get("post_boundary_balls", 0)),
                    "post_boundary_dot_pct": round(float(r.get("post_boundary_dot_pct", 0.0)), 1),
                    "confidence_tier": str(r.get("confidence_tier", "INSUFFICIENT")),
                }
        return None

    def _get_ml_context(self, player_id: int, discipline: str) -> Optional[Dict[str, Any]]:
        """Extract supervised ML test partition residuals."""
        if discipline in ["BATTER", "ALL_ROUNDER"] and self._bat_ml_preds is not None:
            sub = self._bat_ml_preds[self._bat_ml_preds["striker_id"] == player_id]
            if not sub.empty:
                actual = float(sub["actual_runs"].sum())
                expected = float(sub["pred_lightgbm"].sum())
                residual = actual - expected
                return {
                    "evaluated_deliveries": len(sub),
                    "actual_runs": round(actual, 1),
                    "contextual_expected_runs": round(expected, 1),
                    "net_residual": round(residual, 1),
                    "residual_per_ball": round(residual / len(sub), 2),
                    "model": "LightGBM Regressor (2026 Out-of-Time Test)",
                }
        if self._bowl_ml_preds is not None:
            sub = self._bowl_ml_preds[self._bowl_ml_preds["bowler_id"] == player_id]
            if not sub.empty:
                actual = float(sub["actual_runs_conceded"].sum())
                expected = float(sub["pred_lightgbm_runs"].sum())
                residual = actual - expected  # negative is good for bowling
                return {
                    "evaluated_deliveries": len(sub),
                    "actual_runs_conceded": round(actual, 1),
                    "contextual_expected_runs": round(expected, 1),
                    "net_residual": round(residual, 1),
                    "suppression_per_over": round(residual / len(sub) * 6.0, 2),
                    "model": "LightGBM Regressor (2026 Out-of-Time Test)",
                }
        return None

    def _get_reliability_stats(self, player_id: int, discipline: str) -> Dict[str, Any]:
        """Extract Bayesian shrinkage parameters, operational evidence tiers, and sample disclosures."""
        card = self._player_index.get(player_id, {})
        deliv = card.get("deliveries", 0)
        matches = card.get("matches", 0)

        # Operational sample tier based on both delivery volume and match exposure
        if deliv >= 100 and matches >= 15:
            adequacy = "Substantial (N >= 100 balls, M >= 15 matches)"
            uncertainty = "Operational Tier: High sample volume across multiple distinct matches"
        elif deliv >= 30 and matches >= 5:
            adequacy = "Moderate (N >= 30 balls, M >= 5 matches)"
            uncertainty = "Operational Tier: Moderate sample; estimates subject to match-level clustering variance"
        else:
            adequacy = "Limited (N < 30 balls or M < 5 matches)"
            uncertainty = "Operational Tier: Low sample limitation; treat with caution due to high sampling noise"

        return {
            "sample_deliveries": deliv,
            "sample_matches": matches,
            "shrinkage_m_factor": 45,
            "shrinkage_scope": "Validated strictly for overall competition pressure Strike Rate and Economy rate via empirical Bayes ANOVA. Scenario evaluations are presented as un-shrunk observed sample means with match-cluster bootstrap intervals.",
            "sample_adequacy": adequacy,
            "uncertainty_status": uncertainty,
        }

    def _get_comparison_peers(self, player_id: int, discipline: str) -> List[Dict[str, Any]]:
        """Retrieve 3-4 peers in the same discipline for quick head-to-head comparison."""
        all_same = [p for p in self._all_players_list if p["discipline"] == discipline and p["player_id"] != player_id]
        # Return Top 10 members or high volume candidates
        top_peers = [p for p in all_same if p["is_top_10"]][:4]
        if len(top_peers) < 4:
            top_peers.extend([p for p in all_same if not p["is_top_10"]][: 4 - len(top_peers)])
        return [
            {
                "player_id": p["player_id"],
                "player_name": p["player_name"],
                "role": p["role"],
                "deliveries": p["deliveries"],
                "primary_rate": p["primary_rate"],
                "rate_label": p["rate_label"],
                "is_top_10": p["is_top_10"],
            }
            for p in top_peers
        ]


# Singleton instance
gallery_service = GalleryService()
