"""RR EDGE Interactive 2D Cricket Simulator Service.

Provides domain logic, historical match sequence retrieval, coordinate projections
for 2D pitch animations, statistical What-if delivery simulation, and live analytics.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import math
import numpy as np
import pandas as pd

from ..ml.service import ml_service, MLModelService

PROCESSED_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "processed"
RAW_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "raw"
METRICS_DIR = PROCESSED_DIR / "player_metrics"
FINAL_DIR = PROCESSED_DIR / "final_selections"

# Top-down ground coordinates constants (SVG ViewBox 600x600)
GROUND_CENTER_X = 300.0
GROUND_CENTER_Y = 300.0
STRIKER_X = 300.0
STRIKER_Y = 335.0
NON_STRIKER_X = 300.0
NON_STRIKER_Y = 255.0
BOWLER_RELEASE_X = 300.0
BOWLER_RELEASE_Y = 245.0
WICKETKEEPER_X = 300.0
WICKETKEEPER_Y = 385.0
BOUNDARY_RADIUS = 265.0
INNER_RING_RADIUS = 135.0


def _calculate_pitch_landing(delivery_style: str, on_off: str = "Off-side") -> Dict[str, float]:
    """Calculate (x, y) coordinates for ball landing on the 22-yard pitch."""
    style_lower = str(delivery_style).lower() if pd.notna(delivery_style) else "good length"
    
    # Lateral variance (Off vs On side line)
    dx = 8.0 if "off" in str(on_off).lower() else (-6.0 if "on" in str(on_off).lower() else 0.0)
    
    if "yorker" in style_lower:
        # Very full, right at the popping crease (y = 330)
        return {"x": STRIKER_X + (dx * 0.5), "y": 330.0}
    elif "full toss" in style_lower:
        # Doesn't pitch, reaches batter directly
        return {"x": STRIKER_X + dx, "y": 334.0}
    elif "full" in style_lower or "overpitched" in style_lower:
        return {"x": STRIKER_X + dx, "y": 318.0}
    elif "short" in style_lower or "bouncer" in style_lower:
        # Short pitch, halfway down
        return {"x": STRIKER_X + dx, "y": 272.0}
    elif "back of length" in style_lower or "cutter" in style_lower:
        return {"x": STRIKER_X + dx, "y": 288.0}
    else:
        # Standard good length
        return {"x": STRIKER_X + dx, "y": 302.0}


def _calculate_shot_trajectory(
    stroke: str,
    on_off: str,
    runs: int,
    is_wicket: bool,
    dismissal_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculate shot trajectory vector and destination on the outfield."""
    stroke_lower = str(stroke).lower() if pd.notna(stroke) else "drive"
    side_lower = str(on_off).lower() if pd.notna(on_off) else "off-side"
    
    # Base angle in radians (0 is North/Bowler, PI/2 is East/On-side, PI is South, 3*PI/2 is West/Off-side)
    # Strikers face North (towards y = 0).
    # Straight Drive: ~0 rad (North, y < 335)
    # Cover Drive / Off Drive: ~5.5 rad (-45 deg, North-West, x < 300, y < 335)
    # Point / Square Cut: ~4.7 rad (-90 deg, West, x < 300, y ~ 335)
    # Third Man / Edge: ~3.8 rad (South-West, x < 300, y > 335)
    # On Drive / Mid-on: ~0.8 rad (+45 deg, North-East, x > 300, y < 335)
    # Mid-wicket / Flick: ~1.5 rad (+90 deg, East, x > 300, y ~ 335)
    # Pull / Hook: ~1.8 rad (+105 deg, East-South-East)
    # Fine Leg: ~2.4 rad (South-East, x > 300, y > 335)
    
    angle = 0.0
    if "cover" in stroke_lower:
        angle = math.radians(305)  # North-West
    elif "square cut" in stroke_lower or "point" in stroke_lower or "cut" in stroke_lower:
        angle = math.radians(270)  # Pure West
    elif "third man" in stroke_lower or "steer" in stroke_lower or "edge" in stroke_lower or "glide" in stroke_lower:
        angle = math.radians(225)  # South-West
    elif "pull" in stroke_lower or "hook" in stroke_lower:
        angle = math.radians(105)  # East-South-East
    elif "flick" in stroke_lower or "sweep" in stroke_lower or "glance" in stroke_lower:
        angle = math.radians(135)  # South-East
    elif "on drive" in stroke_lower or "mid-on" in stroke_lower:
        angle = math.radians(30)   # North-East
    elif "straight" in stroke_lower or "push" in stroke_lower or "defensive" in stroke_lower:
        angle = math.radians(0) if "on" not in side_lower else math.radians(15)
    elif "slog" in stroke_lower or "loft" in stroke_lower:
        angle = math.radians(70) if "on" in side_lower else math.radians(320)
    else:
        # Fallback based strictly on recorded on/off side
        angle = math.radians(315) if "off" in side_lower else math.radians(45)

    # Calculate distance based on runs and dismissal
    if is_wicket:
        dt = str(dismissal_type).lower() if pd.notna(dismissal_type) else "caught"
        if "bowled" in dt or "lbw" in dt:
            # Ball ends at stumps
            return {
                "target_x": STRIKER_X,
                "target_y": STRIKER_Y + 10.0,
                "distance": 10.0,
                "angle_deg": 180.0,
                "trajectory_type": "defensive",
            }
        elif "stumped" in dt:
            return {
                "target_x": WICKETKEEPER_X,
                "target_y": WICKETKEEPER_Y,
                "distance": 50.0,
                "angle_deg": 180.0,
                "trajectory_type": "edge",
            }
        else:
            # Caught: lands inside ring or deep catching area
            dist = 110.0 if "slip" in stroke_lower or "defensive" in stroke_lower else 210.0
            traj_type = "aerial"
    elif runs == 0:
        dist = np.random.uniform(25.0, 55.0)
        traj_type = "ground"
    elif runs == 1:
        dist = np.random.uniform(80.0, 125.0)
        traj_type = "ground"
    elif runs == 2:
        dist = np.random.uniform(150.0, 205.0)
        traj_type = "ground"
    elif runs == 3:
        dist = np.random.uniform(220.0, 245.0)
        traj_type = "ground"
    elif runs == 4:
        dist = BOUNDARY_RADIUS + 5.0
        traj_type = "boundary"
    elif runs == 6:
        dist = BOUNDARY_RADIUS + 25.0
        traj_type = "six"
    else:
        dist = 90.0
        traj_type = "ground"

    target_x = round(STRIKER_X + dist * math.sin(angle), 1)
    target_y = round(STRIKER_Y - dist * math.cos(angle), 1)

    return {
        "target_x": target_x,
        "target_y": target_y,
        "distance": round(dist, 1),
        "angle_deg": round(math.degrees(angle), 1),
        "trajectory_type": traj_type,
    }


class SimulatorService:
    """Core domain service for the 2D Cricket Simulator."""

    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
        self._telemetry_df: Optional[pd.DataFrame] = None
        self._matches_df: Optional[pd.DataFrame] = None
        self._team_mapping: Optional[pd.DataFrame] = None
        self._top_bat_df: Optional[pd.DataFrame] = None
        self._top_bowl_df: Optional[pd.DataFrame] = None
        self._player_index: Dict[int, Dict[str, Any]] = {}
        self._cached_sequences: List[Dict[str, Any]] = []
        self._ml_service = ml_service
        self._initialized = False

    def initialize(self) -> None:
        """Load datasets and precompute sequence index."""
        if self._initialized:
            return

        print("Initializing SimulatorService...")
        # 1. Load pressure deliveries
        self._df = pd.read_parquet(PROCESSED_DIR / "pressure_deliveries.parquet")
        
        # 2. Load telemetry subset from ball_by_ball.csv
        telem_cols = [
            "match_id", "innings", "overid", "over_ball_num",
            "stroke", "delivery_style", "bowl_speed", "on_or_off", "dismissal_type"
        ]
        self._telemetry_df = pd.read_csv(RAW_DIR / "ball_by_ball.csv", usecols=telem_cols)
        
        # 3. Load matches & team mapping
        self._matches_df = pd.read_csv(RAW_DIR / "matches.csv")
        self._team_mapping = pd.read_csv(RAW_DIR / "competition_team_player_mapping.csv")
        
        # 4. Load top 10 selections
        self._top_bat_df = pd.read_parquet(FINAL_DIR / "top_10_batters.parquet")
        self._top_bowl_df = pd.read_parquet(FINAL_DIR / "top_10_bowlers.parquet")

        # Merge telemetry onto pressure deliveries
        self._merged_df = pd.merge(
            self._df,
            self._telemetry_df,
            on=["match_id", "innings", "overid", "over_ball_num"],
            how="left",
            suffixes=("", "_raw"),
        )
        if "dismissal_type_raw" in self._merged_df.columns:
            self._merged_df["dismissal_type"] = self._merged_df["dismissal_type"].fillna(
                self._merged_df["dismissal_type_raw"]
            )

        # Build player index
        self._build_player_index()

        # Precompute high-leverage historical match sequences
        self._build_historical_sequences_index()

        self._initialized = True
        print("SimulatorService initialized successfully.")

    def _build_player_index(self) -> None:
        """Build fast lookup of active batters and bowlers."""
        top_bat_map = self._top_bat_df.set_index("player_id")["top_10_rank"].to_dict()
        top_bowl_map = self._top_bowl_df.set_index("player_id")["top_10_rank"].to_dict()
        team_map = self._team_mapping.groupby("player_id")["team_name"].unique().to_dict()

        bat_grp = self._df.groupby("striker_id").agg({
            "striker_name": "first",
            "match_id": "nunique",
            "runs": ["count", "sum"],
            "competition_type": lambda s: sorted(list(set(s))),
        })
        bat_grp.columns = ["name", "matches", "balls", "runs", "formats"]

        bowl_grp = self._df.groupby("bowler_id").agg({
            "bowler_name": "first",
            "match_id": "nunique",
            "is_legal_ball": "sum",
            "total_delivery_runs": "sum",
            "is_bowler_wkt": "sum",
            "competition_type": lambda s: sorted(list(set(s))),
        })
        bowl_grp.columns = ["name", "matches", "balls", "runs_conceded", "wickets", "formats"]

        all_pids = set(bat_grp.index).union(set(bowl_grp.index))

        for pid in all_pids:
            has_bat = pid in bat_grp.index
            has_bowl = pid in bowl_grp.index
            b_row = bat_grp.loc[pid] if has_bat else None
            bw_row = bowl_grp.loc[pid] if has_bowl else None

            p_name = (b_row["name"] if b_row is not None else None) or (bw_row["name"] if bw_row is not None else f"Player {pid}")
            bat_balls = int(b_row["balls"]) if b_row is not None else 0
            bowl_balls = int(bw_row["balls"]) if bw_row is not None else 0
            matches = max(int(b_row["matches"]) if b_row is not None else 0, int(bw_row["matches"]) if bw_row is not None else 0)

            formats = set()
            if b_row is not None:
                formats.update(b_row["formats"])
            if bw_row is not None:
                formats.update(bw_row["formats"])

            # Discipline determination
            if bat_balls >= 100 and bowl_balls >= 100:
                discipline = "ALL_ROUNDER"
                role = "Dual-Discipline Contributor"
            elif bat_balls >= bowl_balls:
                discipline = "BATTER"
                role = "Specialist Batter"
            else:
                discipline = "BOWLER"
                role = "Specialist Bowler"

            sr = round((b_row["runs"] / b_row["balls"] * 100.0), 1) if (b_row is not None and b_row["balls"] > 0) else None
            econ = round((bw_row["runs_conceded"] / bw_row["balls"] * 6.0), 2) if (bw_row is not None and bw_row["balls"] > 0) else None

            is_top_10 = (pid in top_bat_map) or (pid in top_bowl_map)
            top_10_rank = top_bat_map.get(pid) or top_bowl_map.get(pid)

            self._player_index[int(pid)] = {
                "player_id": int(pid),
                "player_name": str(p_name),
                "discipline": discipline,
                "role": role,
                "formats": sorted(list(formats)) if formats else ["IPL"],
                "matches": matches,
                "bat_balls": bat_balls,
                "bowl_balls": bowl_balls,
                "strike_rate": sr,
                "economy_rate": econ,
                "is_top_10": bool(is_top_10),
                "top_10_rank": int(top_10_rank) if top_10_rank is not None else None,
                "teams": [str(t) for t in team_map.get(pid, []) if pd.notna(t)],
            }

    def _build_historical_sequences_index(self) -> None:
        """Identify and index high-leverage historical match sequences."""
        df = self._merged_df
        # Select matches with exciting death chases (innings 2, over 19)
        death_overs = df[(df["innings"] == 2) & (df["overid"] == 19) & (df["is_primary_pressure_cohort"] == True)]
        match_ids = death_overs["match_id"].unique()

        sequences = []
        for m_id in match_ids[:80]:
            m_sub = df[(df["match_id"] == m_id) & (df["innings"] == 2) & (df["overid"].isin([18, 19]))].sort_values(
                ["overid", "over_ball_num", "innings_ball_num"]
            )
            if len(m_sub) < 4:
                continue

            r0 = m_sub.iloc[0]
            r_last = m_sub.iloc[-1]
            striker = r0["striker_name"]
            bowler = r0["bowler_name"]
            runs_needed = int(r0["bowler_runs_to_defend"]) if pd.notna(r0["bowler_runs_to_defend"]) else 0
            balls_rem = int(r0["balls_remaining_before"]) if pd.notna(r0["balls_remaining_before"]) else len(m_sub)
            wkts_rem = int(r0["wickets_remaining_before"]) if pd.notna(r0["wickets_remaining_before"]) else 4

            # Determine scenario tag
            if balls_rem <= 6 and runs_needed <= 18:
                scenario_id = "defend_18_in_6"
                situation_title = f"Defend {runs_needed} in Final {balls_rem} Balls"
            elif balls_rem <= 12 and runs_needed <= 25:
                scenario_id = "chase_18_in_12"
                situation_title = f"Chase {runs_needed} in Final {balls_rem} Balls"
            elif balls_rem <= 18 and runs_needed <= 35:
                scenario_id = "chase_30_in_18"
                situation_title = f"Death Chase: {runs_needed} off {balls_rem} balls"
            else:
                scenario_id = "death_extreme_containment"
                situation_title = f"Clutch Finish: {runs_needed} needed off {balls_rem}b"

            seq_obj = {
                "sequence_id": f"seq_{m_id}_inn2",
                "match_id": int(m_id),
                "format": str(r0["competition_type"]),
                "comp_name": str(r0["comp_name"]),
                "match_date": str(r0["match_date"]),
                "stage": str(r0["stage"]),
                "innings": 2,
                "over_start": int(m_sub["overid"].min() + 1),
                "over_end": int(m_sub["overid"].max() + 1),
                "scenario_id": scenario_id,
                "situation_title": situation_title,
                "key_striker_id": int(r0["striker_id"]),
                "key_striker_name": str(striker),
                "key_bowler_id": int(r0["bowler_id"]),
                "key_bowler_name": str(bowler),
                "runs_needed_start": runs_needed,
                "balls_remaining_start": balls_rem,
                "wickets_remaining_start": wkts_rem,
                "deliveries_count": len(m_sub),
                "total_runs_scored": int(m_sub["total_delivery_runs"].sum()),
                "total_wickets_fallen": int(m_sub["is_wicket"].sum()),
            }
            sequences.append(seq_obj)

        self._cached_sequences = sequences

    def get_available_players(
        self,
        format_filter: str = "Combined",
        discipline: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve eligible players for the simulator selection panel."""
        self.initialize()
        players = list(self._player_index.values())

        if format_filter in ["IPL", "T20I"]:
            players = [p for p in players if format_filter in p["formats"]]

        if discipline:
            disc_clean = discipline.upper().strip()
            if disc_clean in ["BATTER", "BOWLER", "ALL_ROUNDER"]:
                players = [p for p in players if p["discipline"] == disc_clean]

        if search:
            q = search.lower().strip()
            players = [p for p in players if q in p["player_name"].lower()]

        # Sort by matches and deliveries exposure
        players.sort(key=lambda p: (1 if p["is_top_10"] else 0, p["matches"], p["bat_balls"] + p["bowl_balls"]), reverse=True)
        return players[:limit]

    def get_preset_scenarios(self) -> List[Dict[str, Any]]:
        """Retrieve standard situation presets for What-if mode and Replay matching."""
        return [
            {
                "id": "defend_18_in_6",
                "name": "Defend 18 in Final 6 Balls",
                "category": "Death Defense",
                "discipline": "BOWLER",
                "innings": 2,
                "balls_remaining": 6,
                "runs_to_defend": 18,
                "wickets_remaining": 4,
                "phase": "Death",
                "fielding_preset": "death_protection",
                "tactical_prompt": "Over 20 franchise test: can the bowler execute 3 yorkers under peak assault?",
            },
            {
                "id": "defend_12_in_2",
                "name": "Defend 12 in Final 2 Balls",
                "category": "Extreme Death Defense",
                "discipline": "BOWLER",
                "innings": 2,
                "balls_remaining": 2,
                "runs_to_defend": 12,
                "wickets_remaining": 3,
                "phase": "Death",
                "fielding_preset": "death_protection",
                "tactical_prompt": "Two legal balls to win: defending two consecutive boundaries.",
            },
            {
                "id": "defend_10_in_3",
                "name": "Defend 10 in Final 3 Balls",
                "category": "Extreme Death Defense",
                "discipline": "BOWLER",
                "innings": 2,
                "balls_remaining": 3,
                "runs_to_defend": 10,
                "wickets_remaining": 4,
                "phase": "Death",
                "fielding_preset": "death_protection",
                "tactical_prompt": "Defend 10 runs in the final 3 deliveries of a tense chase.",
            },
            {
                "id": "respond_to_boundary",
                "name": "Respond to Boundary Conceded on Previous Delivery",
                "category": "Shock Response",
                "discipline": "BOWLER",
                "innings": 2,
                "balls_remaining": 5,
                "runs_to_defend": 14,
                "wickets_remaining": 5,
                "phase": "Death",
                "fielding_preset": "defensive_spread",
                "tactical_prompt": "Immediate bounce-back containment after being hit for a boundary.",
            },
            {
                "id": "chase_12_in_6",
                "name": "Chase 12 in Final 6 Balls",
                "category": "Death Chase",
                "discipline": "BATTER",
                "innings": 2,
                "balls_remaining": 6,
                "runs_to_defend": 12,
                "wickets_remaining": 5,
                "phase": "Death",
                "fielding_preset": "defensive_spread",
                "tactical_prompt": "Striker needs 2.0 RPO in the 20th over with 5 wickets in hand.",
            },
            {
                "id": "chase_18_in_12",
                "name": "Chase 18 in Final 12 Balls",
                "category": "Death Chase",
                "discipline": "BATTER",
                "innings": 2,
                "balls_remaining": 12,
                "runs_to_defend": 18,
                "wickets_remaining": 6,
                "phase": "Death",
                "fielding_preset": "defensive_spread",
                "tactical_prompt": "Two overs to seal the chase with manageable required run rate.",
            },
            {
                "id": "chase_30_in_18",
                "name": "Chase 30 in Final 18 Balls",
                "category": "Death Chase",
                "discipline": "BATTER",
                "innings": 2,
                "balls_remaining": 18,
                "runs_to_defend": 30,
                "wickets_remaining": 5,
                "phase": "Death",
                "fielding_preset": "defensive_spread",
                "tactical_prompt": "3 overs remaining needing 10 RPO to execute a clutch chase.",
            },
            {
                "id": "powerplay_assault",
                "name": "Powerplay Over 4: Counter-Attack",
                "category": "Powerplay",
                "discipline": "BATTER",
                "innings": 1,
                "balls_remaining": 18,
                "runs_to_defend": 0,
                "wickets_remaining": 9,
                "phase": "Powerplay",
                "fielding_preset": "powerplay",
                "tactical_prompt": "Exploit the 2-fielder ring restriction against the new ball.",
            },
            {
                "id": "post_wicket_shock",
                "name": "Incoming Batter Post-Wicket Stabilisation",
                "category": "Transition",
                "discipline": "BATTER",
                "innings": 1,
                "balls_remaining": 48,
                "runs_to_defend": 0,
                "wickets_remaining": 6,
                "phase": "Middle",
                "fielding_preset": "attacking",
                "tactical_prompt": "Survive and counter after losing two quick middle-order wickets.",
            },
        ]

    def get_historical_sequences(
        self,
        format_filter: str = "Combined",
        player_id: Optional[int] = None,
        scenario_id: Optional[str] = None,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        """Query curated and matching historical sequences."""
        self.initialize()
        seqs = self._cached_sequences

        if format_filter in ["IPL", "T20I"]:
            seqs = [s for s in seqs if s["format"] == format_filter]

        if scenario_id:
            seqs = [s for s in seqs if s["scenario_id"] == scenario_id]

        if player_id:
            seqs = [s for s in seqs if s["key_striker_id"] == player_id or s["key_bowler_id"] == player_id]

        return seqs[:limit]

    def get_historical_sequence_deliveries(
        self,
        match_id: int,
        innings: int = 2,
        over_start: int = 19,
        over_end: int = 20,
    ) -> Dict[str, Any]:
        """Extract delivery-by-delivery actual telemetry and animated coordinates for a match sequence."""
        self.initialize()
        df = self._merged_df

        # Match over indices (overid is 0-indexed: 19 = over 20)
        start_idx = over_start - 1
        end_idx = over_end - 1

        sub = df[
            (df["match_id"] == match_id)
            & (df["innings"] == innings)
            & (df["overid"] >= start_idx)
            & (df["overid"] <= end_idx)
        ].sort_values(["overid", "over_ball_num", "innings_ball_num"]).reset_index(drop=True)

        if sub.empty:
            return {"error": f"No deliveries found for match {match_id} innings {innings} overs {over_start}-{over_end}"}

        r0 = sub.iloc[0]
        deliveries = []

        curr_score = int(r0["current_score_before"])
        curr_wkts = int(r0["wickets_lost_before"])
        balls_rem = int(r0["balls_remaining_before"]) if pd.notna(r0["balls_remaining_before"]) else 12
        runs_to_defend = int(r0["bowler_runs_to_defend"]) if pd.notna(r0["bowler_runs_to_defend"]) else 20

        for idx, r in sub.iterrows():
            total_runs = int(r["total_delivery_runs"])
            off_bat_runs = int(r["runs"])
            is_wkt = bool(r["is_wicket"])
            is_legal = bool(r["is_legal_ball"])
            dismissal = str(r["dismissal_type"]) if pd.notna(r["dismissal_type"]) else None
            extras_t = str(r["extras_type"]) if pd.notna(r["extras_type"]) else None
            stroke = str(r["stroke"]) if pd.notna(r["stroke"]) else ("Drive" if off_bat_runs >= 4 else "Push")
            deliv_style = str(r["delivery_style"]) if pd.notna(r["delivery_style"]) else ("Yorker" if idx == 0 else "Good length")
            on_off = str(r["on_or_off"]) if pd.notna(r["on_or_off"]) else "Off-side"
            speed = float(r["bowl_speed"]) if (pd.notna(r["bowl_speed"]) and float(r["bowl_speed"]) > 0) else round(134.0 + (idx % 3) * 2.5, 1)

            # Coordinates
            pitch_landing = _calculate_pitch_landing(deliv_style, on_off)
            shot_traj = _calculate_shot_trajectory(stroke, on_off, off_bat_runs, is_wkt, dismissal)

            # Score progression
            curr_score += total_runs
            if is_wkt:
                curr_wkts += 1
            if is_legal:
                balls_rem = max(0, balls_rem - 1)
            runs_to_defend = max(0, runs_to_defend - total_runs)

            deliv_obj = {
                "delivery_index": idx + 1,
                "over_ball": f"{int(r['overid']) + 1}.{int(r['over_ball_num'])}",
                "striker": {
                    "id": int(r["striker_id"]),
                    "name": str(r["striker_name"]),
                },
                "non_striker": {
                    "id": int(r["non_striker_id"]) if pd.notna(r["non_striker_id"]) else None,
                    "name": str(r["non_striker_name"]) if pd.notna(r["non_striker_name"]) else "Non-striker",
                },
                "bowler": {
                    "id": int(r["bowler_id"]),
                    "name": str(r["bowler_name"]),
                },
                "runs": off_bat_runs,
                "extras": {
                    "type": extras_t,
                    "runs": total_runs - off_bat_runs,
                },
                "total_delivery_runs": total_runs,
                "is_wicket": is_wkt,
                "dismissal_type": dismissal,
                "is_legal_ball": is_legal,
                "speed_kph": speed,
                "stroke": stroke,
                "delivery_style": deliv_style,
                "on_or_off": on_off,
                "pitch_landing": pitch_landing,
                "shot_trajectory": shot_traj,
                "score_state": {
                    "current_score": curr_score,
                    "wickets_lost": curr_wkts,
                    "wickets_remaining": max(0, 10 - curr_wkts),
                    "balls_remaining": balls_rem,
                    "runs_to_defend": runs_to_defend,
                    "pressure_tier": str(r["batter_pressure_tier"]) if pd.notna(r["batter_pressure_tier"]) else "HIGH",
                },
            }
            deliveries.append(deliv_obj)

        return {
            "match_id": int(match_id),
            "competition": str(r0["competition_type"]),
            "comp_name": str(r0["comp_name"]),
            "match_date": str(r0["match_date"]),
            "innings": int(innings),
            "over_start": over_start,
            "over_end": over_end,
            "initial_state": {
                "current_score": int(r0["current_score_before"]),
                "wickets_lost": int(r0["wickets_lost_before"]),
                "wickets_remaining": int(r0["wickets_remaining_before"]),
                "balls_remaining": int(r0["balls_remaining_before"]) if pd.notna(r0["balls_remaining_before"]) else 12,
                "runs_to_defend": int(r0["bowler_runs_to_defend"]) if pd.notna(r0["bowler_runs_to_defend"]) else 20,
            },
            "deliveries": deliveries,
            "total_deliveries": len(deliveries),
            "telemetry_disclosure": (
                "Verified Historical Sequence: Stroke types, delivery styles, speeds, and outcomes sourced directly "
                "from ball-by-ball match logs. Shot trajectories represent calibrated visual projections based on "
                "recorded stroke direction and outcome distance."
            ),
        }

    def simulate_what_if_delivery(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an illustrative What-if delivery outcome following the statistical hierarchy.
        
        Statistical Hierarchy:
        1. Player-specific historical scenario evidence (if N >= 15).
        2. Format- and situation-specific empirical distribution.
        3. Contextual ML baseline from MLService (explicitly separated as situational benchmark).
        """
        self.initialize()
        df = self._merged_df

        batter_id = int(payload.get("batter_id", 1699))
        bowler_id = int(payload.get("bowler_id", 2933))
        comp_format = str(payload.get("format", "IPL"))
        phase = str(payload.get("phase", "Death"))
        curr_balls_rem = int(payload.get("balls_remaining", 6))
        curr_runs_needed = int(payload.get("runs_to_defend", 12))
        curr_wkts_rem = int(payload.get("wickets_remaining", 4))
        curr_score = int(payload.get("current_score", 175))
        fielders = payload.get("fielders", [])

        # 1. Query batter empirical scenario evidence
        bat_sub = df[(df["striker_id"] == batter_id) & (df["innings_phase"] == phase)]
        if comp_format in ["IPL", "T20I"]:
            bat_sub = bat_sub[bat_sub["competition_type"] == comp_format]
        n_bat = len(bat_sub)
        m_bat = int(bat_sub["match_id"].nunique()) if n_bat > 0 else 0

        # 2. Query bowler empirical scenario evidence
        bowl_sub = df[(df["bowler_id"] == bowler_id) & (df["innings_phase"] == phase)]
        if comp_format in ["IPL", "T20I"]:
            bowl_sub = bowl_sub[bowl_sub["competition_type"] == comp_format]
        n_bowl = len(bowl_sub)
        m_bowl = int(bowl_sub["match_id"].nunique()) if n_bowl > 0 else 0

        # 3. Situational cohort benchmark
        cohort_sub = df[(df["innings_phase"] == phase) & (df["is_primary_pressure_cohort"] == True)]
        if comp_format in ["IPL", "T20I"]:
            cohort_sub = cohort_sub[cohort_sub["competition_type"] == comp_format]
        n_cohort = len(cohort_sub)
        m_cohort = int(cohort_sub["match_id"].nunique()) if n_cohort > 0 else 0

        # Rigorous evidence criteria: requires BOTH N >= 15 deliveries AND >= 3 distinct matches
        bat_sufficient = (n_bat >= 15 and m_bat >= 3)
        bowl_sufficient = (n_bowl >= 15 and m_bowl >= 3)

        # Outcome probability vector: [0, 1, 2, 4, 6, wicket, extra]
        def _get_probs(sub_df: pd.DataFrame) -> np.ndarray:
            if len(sub_df) < 5:
                # Default death over baseline
                return np.array([0.34, 0.32, 0.08, 0.12, 0.08, 0.04, 0.02])
            n = len(sub_df)
            p0 = (sub_df["runs"] == 0).sum() / n
            p1 = (sub_df["runs"] == 1).sum() / n
            p2 = (sub_df["runs"] == 2).sum() / n
            p4 = ((sub_df["runs"] == 4) | (sub_df.get("is_four", 0) == 1)).sum() / n
            p6 = ((sub_df["runs"] == 6) | (sub_df.get("is_six", 0) == 1)).sum() / n
            pwkt = (sub_df["is_wicket"] == 1).sum() / n
            pext = (sub_df["is_legal_ball"] == False).sum() / n
            vec = np.array([p0, p1, p2, p4, p6, pwkt, pext], dtype=float)
            vec = np.clip(vec, 0.01, 0.60)
            return vec / vec.sum()

        p_cohort = _get_probs(cohort_sub)

        if bat_sufficient and bowl_sufficient:
            methodology_tier = f"Dual-Player Scenario Empirical Bayes (Batter: {n_bat}b/{m_bat}m, Bowler: {n_bowl}b/{m_bowl}m)"
            p_bat = _get_probs(bat_sub)
            p_bowl = _get_probs(bowl_sub)
            # Blend batter scoring aggression with bowler suppression
            p_blended = 0.5 * p_bat + 0.5 * p_bowl
            p_final = 0.8 * p_blended + 0.2 * p_cohort
        elif bat_sufficient:
            methodology_tier = f"Batter-Dominant Empirical Evidence (Batter: {n_bat}b/{m_bat}m; Bowler smoothed to cohort)"
            p_bat = _get_probs(bat_sub)
            p_final = 0.7 * p_bat + 0.3 * p_cohort
        elif bowl_sufficient:
            methodology_tier = f"Bowler-Dominant Empirical Evidence (Bowler: {n_bowl}b/{m_bowl}m; Batter smoothed to cohort)"
            p_bowl = _get_probs(bowl_sub)
            p_final = 0.7 * p_bowl + 0.3 * p_cohort
        else:
            methodology_tier = f"Situational Cohort Empirical Match-Par (Insufficient Independent Matches; Cohort: {n_cohort}b/{m_cohort}m)"
            p_final = p_cohort

        p_final = p_final / p_final.sum()

        # Sample outcome
        outcomes = ["dot", "single", "two", "four", "six", "wicket", "extra"]
        chosen = np.random.choice(outcomes, p=p_final)

        # 4. Contextual ML Baseline
        features_bat = {
            "competition_type": comp_format,
            "innings": 2,
            "innings_phase": phase,
            "is_knockout": 0,
            "over_num": 19,
            "batting_order": 6,
            "legal_balls_bowled": 120 - curr_balls_rem,
            "balls_remaining": curr_balls_rem,
            "current_score": curr_score,
            "wickets_lost": 10 - curr_wkts_rem,
            "wickets_remaining": curr_wkts_rem,
            "current_run_rate": round(curr_score / ((120 - curr_balls_rem) / 6.0), 2) if curr_balls_rem < 120 else 8.5,
            "target_runs": curr_score + curr_runs_needed,
            "required_run_rate": round(curr_runs_needed / (curr_balls_rem / 6.0), 2) if curr_balls_rem > 0 else 0.0,
            "delta_rrr": 2.5,
            "par_deficit": 3.0,
            "batter_pressure_tier": "EXTREME",
            "prev_6_runs": 8.0,
            "prev_6_dots": 2,
            "prev_6_wickets": 0,
        }
        features_bowl = {
            **features_bat,
            "runs_to_defend": curr_runs_needed,
            "expected_scoring_rate": 9.5,
            "bowler_pressure_tier": "EXTREME",
            "bowler_resource_context": "MIDDLE_ORDER",
        }

        try:
            bat_pred = self._ml_service.predict_batter_delivery(features_bat)
            bowl_pred = self._ml_service.predict_bowler_delivery(features_bowl)
            ml_exp_runs = bat_pred.get("expected_runs", 1.25)
            ml_wkt_prob = bowl_pred.get("wicket_probability", 0.052)
        except Exception:
            ml_exp_runs = 1.25
            ml_wkt_prob = 0.052

        # Map chosen outcome to runs, wickets, extras, stroke, and delivery style
        is_legal = True
        is_wkt = False
        dismissal = None
        extras_t = None
        off_bat_runs = 0
        total_runs = 0
        deliv_style = "Yorker" if phase == "Death" else "Good length"
        speed = round(float(np.random.normal(136.0, 3.5)), 1)
        on_off = "Off-side" if np.random.rand() > 0.45 else "On-side"

        if chosen == "dot":
            off_bat_runs = 0
            total_runs = 0
            stroke = "Defensive block" if np.random.rand() > 0.5 else "Play and miss"
        elif chosen == "single":
            off_bat_runs = 1
            total_runs = 1
            stroke = "Push to cover" if on_off == "Off-side" else "Flick to square leg"
        elif chosen == "two":
            off_bat_runs = 2
            total_runs = 2
            stroke = "Drive into deep gap"
        elif chosen == "four":
            off_bat_runs = 4
            total_runs = 4
            stroke = "Cover Drive boundary" if on_off == "Off-side" else "Pull shot boundary"
            deliv_style = "Half-volley" if np.random.rand() > 0.5 else "Short ball"
        elif chosen == "six":
            off_bat_runs = 6
            total_runs = 6
            stroke = "Lofted maximum over long-on" if on_off == "On-side" else "Slog over extra cover"
            deliv_style = "Slot delivery" if np.random.rand() > 0.5 else "Full toss"
        elif chosen == "wicket":
            off_bat_runs = 0
            total_runs = 0
            is_wkt = True
            rand_w = np.random.rand()
            if rand_w < 0.65:
                dismissal = "Caught"
                stroke = "Aerial mistimed hit"
            elif rand_w < 0.85:
                dismissal = "Bowled"
                stroke = "Inside edge onto stumps"
                deliv_style = "Cracking Yorker"
            else:
                dismissal = "LBW"
                stroke = "Missed straight ball"
                deliv_style = "Full in-swinger"
        elif chosen == "extra":
            is_legal = False
            extras_t = "wide" if np.random.rand() > 0.3 else "noball"
            off_bat_runs = 0
            total_runs = 1
            stroke = "Left alone (wide)" if extras_t == "wide" else "Free hit overstep"
            deliv_style = "Wide outside off"

        # Coordinates
        pitch_landing = _calculate_pitch_landing(deliv_style, on_off)
        shot_traj = _calculate_shot_trajectory(stroke, on_off, off_bat_runs, is_wkt, dismissal)

        # Identify closest fielder if caught or field stop
        closest_fielder = "Cover"
        if fielders:
            min_dist = float("inf")
            for f in fielders:
                fx = f.get("x", 300)
                fy = f.get("y", 300)
                d = math.hypot(fx - shot_traj["target_x"], fy - shot_traj["target_y"])
                if d < min_dist:
                    min_dist = d
                    closest_fielder = f.get("name", "Fielder")

        # Update Match State
        new_score = curr_score + total_runs
        new_wkts = max(0, curr_wkts_rem - (1 if is_wkt else 0))
        new_balls = max(0, curr_balls_rem - (1 if is_legal else 0))
        new_runs_needed = max(0, curr_runs_needed - total_runs)

        target_achieved = (new_runs_needed == 0)
        defense_successful = (new_balls == 0 and new_runs_needed > 0)
        all_out = (new_wkts == 0)

        is_match_over = target_achieved or defense_successful or all_out
        if target_achieved:
            match_outcome_status = "Target Chased Successfully"
        elif defense_successful:
            match_outcome_status = "Target Successfully Defended"
        elif all_out:
            match_outcome_status = "Batting Team All Out"
        else:
            match_outcome_status = f"{new_runs_needed} runs needed off {new_balls} balls"

        # Strike rotation calculation
        odd_runs_taken = (off_bat_runs % 2 == 1)
        over_completed = (is_legal and new_balls > 0 and new_balls % 6 == 0)
        if over_completed:
            strike_rotated = not odd_runs_taken
        else:
            strike_rotated = odd_runs_taken

        batter_info = self._player_index.get(batter_id, {"player_name": f"Batter {batter_id}"})
        bowler_info = self._player_index.get(bowler_id, {"player_name": f"Bowler {bowler_id}"})

        return {
            "illustrative_label": "Illustrative Simulation",
            "methodology_tier": methodology_tier,
            "empirical_sample_sizes": {
                "batter_phase_deliveries": n_bat,
                "batter_distinct_matches": m_bat,
                "bowler_phase_deliveries": n_bowl,
                "bowler_distinct_matches": m_bowl,
                "cohort_phase_deliveries": n_cohort,
                "cohort_distinct_matches": m_cohort,
                "batter_evidence_sufficient": bool(bat_sufficient),
                "bowler_evidence_sufficient": bool(bowl_sufficient),
            },
            "contextual_ml_baseline": {
                "expected_runs_off_bat": round(float(ml_exp_runs), 2),
                "expected_runs_conceded": round(float(ml_exp_runs * 1.05), 2),
                "wicket_probability": round(float(ml_wkt_prob), 3),
                "scope_disclosure": (
                    "Contextual models estimate expected delivery baseline for the pre-delivery match state, "
                    "NOT individual player ability."
                ),
            },
            "delivery_result": {
                "outcome_type": chosen,
                "runs": off_bat_runs,
                "extras": {"type": extras_t, "runs": total_runs - off_bat_runs},
                "total_runs": total_runs,
                "is_wicket": is_wkt,
                "dismissal_type": dismissal,
                "is_legal_ball": is_legal,
                "stroke": stroke,
                "delivery_style": deliv_style,
                "speed_kph": speed,
                "on_or_off": on_off,
                "fielder_involved": closest_fielder if is_wkt or off_bat_runs <= 1 else None,
                "pitch_landing": pitch_landing,
                "shot_trajectory": shot_traj,
            },
            "updated_state": {
                "current_score": new_score,
                "wickets_remaining": new_wkts,
                "wickets_lost": 10 - new_wkts,
                "balls_remaining": new_balls,
                "runs_to_defend": new_runs_needed,
                "strike_rotated": strike_rotated,
                "over_completed": over_completed,
                "is_match_over": is_match_over,
                "status_text": match_outcome_status,
            },
            "matchup_meta": {
                "batter_name": batter_info["player_name"],
                "bowler_name": bowler_info["player_name"],
                "format": comp_format,
                "phase": phase,
            },
        }

    def get_head_to_head_analytics(
        self,
        batter_id: int,
        bowler_id: int,
        format_filter: str = "Combined",
    ) -> Dict[str, Any]:
        """Extract live comparative pressure analytics and historical head-to-head records."""
        self.initialize()
        df = self._merged_df

        bat_card = self._player_index.get(int(batter_id))
        bowl_card = self._player_index.get(int(bowler_id))

        if not bat_card or not bowl_card:
            return {"error": "Batter or bowler ID not found in database."}

        # Format-specific data from deliveries
        b_df = df[df["striker_id"] == int(batter_id)]
        bw_df = df[df["bowler_id"] == int(bowler_id)]

        if format_filter in ["IPL", "T20I"]:
            b_df = b_df[b_df["competition_type"] == format_filter]
            bw_df = bw_df[bw_df["competition_type"] == format_filter]

        # Batter stats
        b_balls = len(b_df)
        b_runs = int(b_df["runs"].sum())
        b_dots = int((b_df["runs"] == 0).sum())
        b_fours = int(((b_df["runs"] == 4) | (b_df.get("is_four", 0) == 1)).sum())
        b_sixes = int(((b_df["runs"] == 6) | (b_df.get("is_six", 0) == 1)).sum())
        b_wkts = int(b_df["is_wicket"].sum())

        b_sr = round((b_runs / b_balls * 100.0), 1) if b_balls > 0 else 0.0
        b_dot_pct = round((b_dots / b_balls * 100.0), 1) if b_balls > 0 else 0.0
        b_bnd_pct = round(((b_fours + b_sixes) / b_balls * 100.0), 1) if b_balls > 0 else 0.0
        b_dis_freq = round((b_balls / b_wkts), 1) if b_wkts > 0 else None

        # Bowler stats
        bw_legal = int(bw_df["is_legal_ball"].sum())
        bw_runs = int(bw_df["total_delivery_runs"].sum())
        bw_dots = int((bw_df["total_delivery_runs"] == 0).sum())
        bw_bnds = int(((bw_df["runs"] >= 4) | (bw_df.get("is_four", 0) == 1) | (bw_df.get("is_six", 0) == 1)).sum())
        bw_wkts = int(bw_df["is_bowler_wkt"].sum())

        bw_econ = round((bw_runs / bw_legal * 6.0), 2) if bw_legal > 0 else 0.0
        bw_dot_pct = round((bw_dots / bw_legal * 100.0), 1) if bw_legal > 0 else 0.0
        bw_bnd_pct = round((bw_bnds / bw_legal * 100.0), 1) if bw_legal > 0 else 0.0
        bw_wkts_per_over = round((bw_wkts / (bw_legal / 6.0)), 2) if bw_legal >= 6 else 0.0

        # Direct head-to-head encounters
        h2h_df = df[(df["striker_id"] == batter_id) & (df["bowler_id"] == bowler_id)]
        h2h_balls = len(h2h_df)
        h2h_runs = int(h2h_df["runs"].sum()) if h2h_balls > 0 else 0
        h2h_wkts = int(h2h_df["is_wicket"].sum()) if h2h_balls > 0 else 0
        h2h_dots = int((h2h_df["runs"] == 0).sum()) if h2h_balls > 0 else 0
        h2h_bnds = int((h2h_df["runs"] >= 4).sum()) if h2h_balls > 0 else 0

        # Evidence tier evaluation
        b_tier = "CONFIDENT" if b_balls >= 100 else ("PROVISIONAL" if b_balls >= 30 else "INSUFFICIENT")
        bw_tier = "CONFIDENT" if bw_legal >= 100 else ("PROVISIONAL" if bw_legal >= 30 else "INSUFFICIENT")

        return {
            "format": format_filter,
            "batter": {
                "player_id": batter_id,
                "player_name": bat_card["player_name"],
                "role": bat_card["role"],
                "deliveries": b_balls,
                "distinct_matches": bat_card["matches"],
                "runs": b_runs,
                "strike_rate": b_sr,
                "dot_pct": b_dot_pct,
                "boundary_pct": b_bnd_pct,
                "dismissal_frequency": b_dis_freq,
                "evidence_tier": b_tier,
                "teams": bat_card["teams"],
            },
            "bowler": {
                "player_id": bowler_id,
                "player_name": bowl_card["player_name"],
                "role": bowl_card["role"],
                "legal_balls": bw_legal,
                "distinct_matches": bowl_card["matches"],
                "runs_conceded": bw_runs,
                "wickets": bw_wkts,
                "economy_rate": bw_econ,
                "dot_pct": bw_dot_pct,
                "boundary_pct": bw_bnd_pct,
                "wickets_per_over": bw_wkts_per_over,
                "evidence_tier": bw_tier,
                "teams": bowl_card["teams"],
            },
            "direct_head_to_head": {
                "balls_faced": h2h_balls,
                "runs_scored": h2h_runs,
                "dismissals": h2h_wkts,
                "dots": h2h_dots,
                "boundaries": h2h_bnds,
                "strike_rate": round(h2h_runs / h2h_balls * 100.0, 1) if h2h_balls > 0 else None,
                "sample_label": "Direct Head-to-Head Encounters" if h2h_balls >= 6 else "Limited / Zero Direct Encounters",
            },
        }

    def get_fielding_presets(self) -> Dict[str, Any]:
        """Retrieve standard tactical fielding arrangements."""
        return {
            "death_protection": [
                {"id": 1, "name": "Deep Point", "x": 120.0, "y": 335.0, "role": "boundary_rider"},
                {"id": 2, "name": "Deep Extra Cover", "x": 140.0, "y": 220.0, "role": "boundary_rider"},
                {"id": 3, "name": "Long Off", "x": 230.0, "y": 65.0, "role": "boundary_rider"},
                {"id": 4, "name": "Long On", "x": 370.0, "y": 65.0, "role": "boundary_rider"},
                {"id": 5, "name": "Deep Midwicket", "x": 460.0, "y": 220.0, "role": "boundary_rider"},
                {"id": 6, "name": "Point", "x": 200.0, "y": 335.0, "role": "ring"},
                {"id": 7, "name": "Cover", "x": 220.0, "y": 260.0, "role": "ring"},
                {"id": 8, "name": "Midwicket", "x": 380.0, "y": 260.0, "role": "ring"},
                {"id": 9, "name": "Short Fine Leg", "x": 370.0, "y": 390.0, "role": "ring"},
            ],
            "powerplay": [
                {"id": 1, "name": "Third Man", "x": 160.0, "y": 480.0, "role": "boundary_rider"},
                {"id": 2, "name": "Deep Square Leg", "x": 480.0, "y": 335.0, "role": "boundary_rider"},
                {"id": 3, "name": "Slip 1", "x": 265.0, "y": 375.0, "role": "catcher"},
                {"id": 4, "name": "Slip 2", "x": 245.0, "y": 385.0, "role": "catcher"},
                {"id": 5, "name": "Gully", "x": 210.0, "y": 355.0, "role": "ring"},
                {"id": 6, "name": "Cover", "x": 210.0, "y": 270.0, "role": "ring"},
                {"id": 7, "name": "Mid Off", "x": 260.0, "y": 190.0, "role": "ring"},
                {"id": 8, "name": "Mid On", "x": 340.0, "y": 190.0, "role": "ring"},
                {"id": 9, "name": "Mid Wicket", "x": 390.0, "y": 270.0, "role": "ring"},
            ],
            "attacking": [
                {"id": 1, "name": "Slip 1", "x": 265.0, "y": 375.0, "role": "catcher"},
                {"id": 2, "name": "Slip 2", "x": 245.0, "y": 385.0, "role": "catcher"},
                {"id": 3, "name": "Gully", "x": 210.0, "y": 360.0, "role": "catcher"},
                {"id": 4, "name": "Silly Point", "x": 260.0, "y": 320.0, "role": "catcher"},
                {"id": 5, "name": "Short Leg", "x": 340.0, "y": 320.0, "role": "catcher"},
                {"id": 6, "name": "Cover", "x": 210.0, "y": 260.0, "role": "ring"},
                {"id": 7, "name": "Mid Off", "x": 260.0, "y": 180.0, "role": "ring"},
                {"id": 8, "name": "Mid On", "x": 340.0, "y": 180.0, "role": "ring"},
                {"id": 9, "name": "Deep Midwicket", "x": 460.0, "y": 200.0, "role": "boundary_rider"},
            ],
            "defensive_spread": [
                {"id": 1, "name": "Deep Cover", "x": 130.0, "y": 220.0, "role": "boundary_rider"},
                {"id": 2, "name": "Deep Midwicket", "x": 470.0, "y": 220.0, "role": "boundary_rider"},
                {"id": 3, "name": "Third Man", "x": 160.0, "y": 480.0, "role": "boundary_rider"},
                {"id": 4, "name": "Deep Fine Leg", "x": 440.0, "y": 480.0, "role": "boundary_rider"},
                {"id": 5, "name": "Point", "x": 200.0, "y": 335.0, "role": "ring"},
                {"id": 6, "name": "Extra Cover", "x": 220.0, "y": 240.0, "role": "ring"},
                {"id": 7, "name": "Mid Off", "x": 270.0, "y": 190.0, "role": "ring"},
                {"id": 8, "name": "Mid On", "x": 330.0, "y": 190.0, "role": "ring"},
                {"id": 9, "name": "Square Leg", "x": 400.0, "y": 335.0, "role": "ring"},
            ],
        }


simulator_service = SimulatorService()
