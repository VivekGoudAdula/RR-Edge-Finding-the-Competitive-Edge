"""Data access service for RR EDGE API.

Loads and caches analytical datasets from data/processed to ensure high-performance,
zero-redundancy querying for the RR EDGE Cricket Intelligence Dashboard.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
FINAL_DIR = PROCESSED_DIR / "final_selections"
EVAL_DIR = PROCESSED_DIR / "player_evaluations"
CI_DIR = PROCESSED_DIR / "candidate_intelligence"
BEH_DIR = PROCESSED_DIR / "behavioral"
ML_DIR = PROCESSED_DIR / "ml"


def _clean_val(v: Any) -> Any:
    """Recursively clean NaN, inf, and numpy types for clean JSON serialization."""
    if isinstance(v, (float, np.floating)):
        if np.isnan(v) or np.isinf(v):
            return None
        return round(float(v), 2)
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    if isinstance(v, dict):
        return {k: _clean_val(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_clean_val(item) for item in v]
    return v


def _safe_int(val: Any) -> int:
    """Safely convert value to integer, returning 0 if None, NaN, or invalid."""
    if val is None or pd.isna(val):
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


class DataService:
    """Singleton service for loading and querying RR EDGE datasets."""

    def __init__(self):
        self._top_10_batters: Optional[pd.DataFrame] = None
        self._top_10_bowlers: Optional[pd.DataFrame] = None
        self._batter_matrix: Optional[pd.DataFrame] = None
        self._bowler_matrix: Optional[pd.DataFrame] = None
        self._batter_phase: Optional[pd.DataFrame] = None
        self._bowler_phase: Optional[pd.DataFrame] = None
        self._pairwise_bootstrap: Optional[pd.DataFrame] = None
        self._batter_candidates_ipl: Optional[pd.DataFrame] = None
        self._bowler_candidates_ipl: Optional[pd.DataFrame] = None
        self._risk_flags: Optional[pd.DataFrame] = None
        self._batter_eval: Optional[pd.DataFrame] = None
        self._bowler_eval: Optional[pd.DataFrame] = None
        self._batter_eval_ipl: Optional[pd.DataFrame] = None
        self._bowler_eval_ipl: Optional[pd.DataFrame] = None
        self._batter_behavioral: Optional[pd.DataFrame] = None
        self._bowler_behavioral: Optional[pd.DataFrame] = None
        self._batter_test_preds: Optional[pd.DataFrame] = None
        self._bowler_test_preds: Optional[pd.DataFrame] = None
        self._batter_h2h: Optional[pd.DataFrame] = None
        self._bowler_h2h: Optional[pd.DataFrame] = None
        self._loaded = False

    def load_data(self) -> None:
        """Load and cache analytical tables from disk."""
        if self._loaded:
            return

        # Top 10 lists
        self._top_10_batters = pd.read_parquet(FINAL_DIR / "top_10_batters.parquet")
        self._top_10_bowlers = pd.read_parquet(FINAL_DIR / "top_10_bowlers.parquet")

        # Full Decision Matrices (18 candidates each)
        self._batter_matrix = pd.read_parquet(FINAL_DIR / "batter_final_decision_matrix.parquet")
        self._bowler_matrix = pd.read_parquet(FINAL_DIR / "bowler_final_decision_matrix.parquet")

        # Phase breakdowns
        self._batter_phase = pd.read_parquet(EVAL_DIR / "batter_phase_metrics.parquet")
        self._bowler_phase = pd.read_parquet(EVAL_DIR / "bowler_phase_metrics.parquet")

        # Full player evaluations (contains pressure vs normal, credible intervals, crunch stats)
        if (EVAL_DIR / "batter_evaluation.parquet").exists():
            self._batter_eval = pd.read_parquet(EVAL_DIR / "batter_evaluation.parquet")
        if (EVAL_DIR / "bowler_evaluation.parquet").exists():
            self._bowler_eval = pd.read_parquet(EVAL_DIR / "bowler_evaluation.parquet")
        if (EVAL_DIR / "batter_evaluation_ipl.parquet").exists():
            self._batter_eval_ipl = pd.read_parquet(EVAL_DIR / "batter_evaluation_ipl.parquet")
        if (EVAL_DIR / "bowler_evaluation_ipl.parquet").exists():
            self._bowler_eval_ipl = pd.read_parquet(EVAL_DIR / "bowler_evaluation_ipl.parquet")

        # Behavioral response parquets
        if (BEH_DIR / "batter_behavioral.parquet").exists():
            self._batter_behavioral = pd.read_parquet(BEH_DIR / "batter_behavioral.parquet")
        if (BEH_DIR / "bowler_behavioral.parquet").exists():
            self._bowler_behavioral = pd.read_parquet(BEH_DIR / "bowler_behavioral.parquet")

        # Supervised ML holdout test predictions
        if (ML_DIR / "batter_test_predictions.parquet").exists():
            self._batter_test_preds = pd.read_parquet(ML_DIR / "batter_test_predictions.parquet")
        if (ML_DIR / "bowler_test_predictions.parquet").exists():
            self._bowler_test_preds = pd.read_parquet(ML_DIR / "bowler_test_predictions.parquet")

        # Pairwise bootstrap results
        self._pairwise_bootstrap = pd.read_csv(FINAL_DIR / "top_10_pairwise_bootstrap.csv")

        # Head to head pairwise candidate profiles
        if (CI_DIR / "batter_head_to_head.csv").exists():
            self._batter_h2h = pd.read_csv(CI_DIR / "batter_head_to_head.csv")
        if (CI_DIR / "bowler_head_to_head.csv").exists():
            self._bowler_h2h = pd.read_csv(CI_DIR / "bowler_head_to_head.csv")

        # Candidate pool tables for explorer and discovery
        self._batter_candidates_ipl = pd.read_parquet(CI_DIR / "batter_candidates_ipl.parquet")
        self._bowler_candidates_ipl = pd.read_parquet(CI_DIR / "bowler_candidates_ipl.parquet")

        if (CI_DIR / "candidate_risk_flags.csv").exists():
            self._risk_flags = pd.read_csv(CI_DIR / "candidate_risk_flags.csv")

        self._loaded = True

    def get_overview(self) -> Dict[str, Any]:
        """Produce executive overview metrics, top 10 showcases, and key insights."""
        self.load_data()

        # Precise Audited Delivery and Entity Counts
        total_eligible_deliveries = 194014
        primary_cohort_deliveries = 192373
        excluded_uncertain_deliveries = 1641
        batter_high_extreme_deliveries = 71523
        bowler_high_extreme_deliveries = 44333
        matches_count = 837  # 367 IPL + 470 T20I
        competitions = ["IPL (2022-2026)", "Senior Men's T20I (2022-2026)"]
        batters_count = 819
        bowlers_count = 595

        # Top 10 lists as dictionaries
        t10_batters = [_clean_val(r) for r in self._top_10_batters.to_dict(orient="records")]
        t10_bowlers = [_clean_val(r) for r in self._top_10_bowlers.to_dict(orient="records")]

        discoveries = [
            {
                "id": "DISC_01",
                "headline": "Tim David (#1 Batter) — Unmatched Dual-Format Pressure Finisher",
                "detail": "Only qualified batter in database exceeding 170.0 shrunk strike rate (M=45) in both IPL (170.7) and Senior T20Is (171.1). Sustains 23.7% IPL boundary rate and +24.9 Context RAE.",
                "discipline": "Batter",
                "tag": "ROBUST_ANCHOR",
            },
            {
                "id": "DISC_02",
                "headline": "Sunil Narine (#1 Bowler) — Benchmark Middle-Overs Defensive Squeeze",
                "detail": "Conceded tournament-lowest 6.70 raw economy, -3.07 All-Runs RCAE, and -2.79 Legal-Ball RCAE across 317 legal IPL pressure deliveries. 89.5% match pass rate across 38 evaluated matches (34/38).",
                "discipline": "Bowler",
                "tag": "ROBUST_ANCHOR",
            },
            {
                "id": "DISC_03",
                "headline": "Matheesha Pathirana (#3 Bowler) — #1 Seamer Death Wicket Strike Rate",
                "detail": "Across 316 combined death-phase pressure deliveries, captured 31 wickets at 8.62 runs/over (0.589 wkts/over / 1 wicket every 10.2 balls), leading all specialist death seamers.",
                "discipline": "Bowler",
                "tag": "ROBUST_ANCHOR",
            },
            {
                "id": "DISC_04",
                "headline": "Yashasvi Jaiswal (#3 Batter) — Elite Powerplay Boundary Production",
                "detail": "Recorded 31.5% boundary rate (69 boundaries in 219 balls) in IPL Powerplay pressure, ranking #1 among batters with >= 200 Powerplay pressure balls.",
                "discipline": "Batter",
                "tag": "ROBUST_ANCHOR",
            },
            {
                "id": "DISC_05",
                "headline": "Vaibhav Sooryavanshi (#10 Batter) — High-Ceiling Boundary Discovery",
                "detail": "Highest raw strike rate (231.6) and #1 shrunk M=45 SR (195.8) among all 141 batters with >= 50 pressure balls. Polar 43.4% boundary and 43.4% dot-ball distribution in 76 balls.",
                "discipline": "Batter",
                "tag": "DISCOVERY_UPSIDE",
            },
            {
                "id": "DISC_06",
                "headline": "Mayank Yadav (#10 Bowler) — #1 Dot-Ball Rate in Qualifying Cohort",
                "detail": "Produced 46.5% dot-ball rate (20 dots in 43 legal deliveries), ranking #1 among all 125 bowlers with >= 40 IPL pressure balls, with 7.95 raw economy.",
                "discipline": "Bowler",
                "tag": "DISCOVERY_UPSIDE",
            },
        ]

        return {
            "metadata": {
                "product": "RR EDGE",
                "tagline": "Finding the Competitive Edge.",
                "descriptor": "An Explainable Multi-Model Cricket Intelligence System for Pressure Performance & Player Reliability.",
                "theme": "Light Theme (RR Pink & White)",
                "total_deliveries": total_eligible_deliveries,
                "primary_deliveries": primary_cohort_deliveries,
                "total_eligible_deliveries": total_eligible_deliveries,
                "primary_cohort_deliveries": primary_cohort_deliveries,
                "excluded_uncertain_deliveries": excluded_uncertain_deliveries,
                "batter_high_extreme_deliveries": batter_high_extreme_deliveries,
                "bowler_high_extreme_deliveries": bowler_high_extreme_deliveries,
                "matches_analysed": matches_count,
                "matches_included": matches_count,
                "competitions": competitions,
                "batters_analysed": batters_count,
                "bowlers_analysed": bowlers_count,
                "unique_batters": batters_count,
                "unique_bowlers": bowlers_count,
            },
            "top_10_batters": t10_batters,
            "top_10_bowlers": t10_bowlers,
            "key_discoveries": discoveries,
        }

    def get_batters(
        self,
        format_filter: str = "IPL",
        role: Optional[str] = None,
        search: Optional[str] = None,
        tier: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query batter candidates and rankings with dynamic filters."""
        self.load_data()
        df = self._batter_matrix.copy()

        if search:
            df = df[df["player_name"].str.contains(search, case=False, na=False)]
        if role and role != "ALL":
            df = df[df["primary_role"] == role]
        if tier and tier != "ALL":
            df = df[df["evidence_tier"] == tier]

        records = df.to_dict(orient="records")
        return [_clean_val(r) for r in records]

    def get_batter_detail(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve complete unified scouting dossier for a single batter."""
        self.load_data()
        row_match = self._batter_matrix[self._batter_matrix["player_id"] == player_id]
        if row_match.empty:
            # Check candidate pool
            row_match = self._batter_candidates_ipl[self._batter_candidates_ipl["striker_id"] == player_id]
            if row_match.empty:
                return None
            player_info = _clean_val(row_match.iloc[0].to_dict())
            player_info["player_name"] = player_info.get("striker_name")
            player_info["player_id"] = player_id
        else:
            player_info = _clean_val(row_match.iloc[0].to_dict())

        # 1. Pressure Performance from full evaluation tables (IPL-specific + Combined)
        pressure_perf = {}
        eval_row_ipl = None
        eval_row_comb = None

        if self._batter_eval_ipl is not None:
            e_sub_ipl = self._batter_eval_ipl[self._batter_eval_ipl["striker_id"] == player_id]
            if not e_sub_ipl.empty:
                eval_row_ipl = e_sub_ipl.iloc[0]

        if self._batter_eval is not None:
            e_sub_comb = self._batter_eval[self._batter_eval["striker_id"] == player_id]
            if not e_sub_comb.empty:
                eval_row_comb = e_sub_comb.iloc[0]

        eval_primary = eval_row_ipl if eval_row_ipl is not None else eval_row_comb

        if eval_primary is not None:
            ipl_context_rae = _clean_val(eval_row_ipl.get("context_adjusted_delta_sr")) if eval_row_ipl is not None else _clean_val(player_info.get("ipl_context_delta_sr"))
            comb_context_rae = _clean_val(eval_row_comb.get("context_adjusted_delta_sr")) if eval_row_comb is not None else None

            pressure_perf = {
                "pressure_volume": _safe_int(eval_primary.get("pressure_balls_faced")),
                "pressure_matches": _safe_int(eval_primary.get("pressure_matches")),
                "normal_volume": _safe_int(eval_primary.get("normal_balls_faced")),
                "normal_matches": _safe_int(eval_primary.get("normal_matches")),
                "pressure_strike_rate": _clean_val(eval_primary.get("pressure_strike_rate")),
                "normal_strike_rate": _clean_val(eval_primary.get("normal_strike_rate")),
                "delta_strike_rate": _clean_val(eval_primary.get("delta_strike_rate")),
                "pressure_dot_pct": _clean_val(eval_primary.get("pressure_dot_ball_pct")),
                "normal_dot_pct": _clean_val(eval_primary.get("normal_dot_ball_pct")),
                "delta_dot_pct": _clean_val(eval_primary.get("delta_dot_ball_pct")),
                "pressure_boundary_pct": _clean_val(eval_primary.get("pressure_boundary_ball_pct")),
                "normal_boundary_pct": _clean_val(eval_primary.get("normal_boundary_ball_pct")),
                "delta_boundary_pct": _clean_val(eval_primary.get("delta_boundary_ball_pct")),
                "context_adjusted_delta_sr": ipl_context_rae,
                "observed_pressure_sr": _clean_val(eval_primary.get("observed_pressure_sr")),
                "expected_pressure_sr": _clean_val(eval_primary.get("expected_pressure_sr")),
                "pressure_match_pass_rate": _clean_val(eval_primary.get("pressure_match_pass_rate")),
                "pressure_match_sr_std": _clean_val(eval_primary.get("pressure_match_sr_std")),
                "pressure_match_sr_median": _clean_val(eval_primary.get("pressure_match_sr_median")),
                "pressure_match_sr_iqr": _clean_val(eval_primary.get("pressure_match_sr_iqr")),
                "tail_anchor_balls": _safe_int(eval_primary.get("tail_anchor_balls")),
                "tail_anchor_sr": _clean_val(eval_primary.get("tail_anchor_sr")),
                "final_crunch_balls": _safe_int(eval_primary.get("final_crunch_balls")),
                "final_crunch_sr": _clean_val(eval_primary.get("final_crunch_sr")),
                "combined_panic_balls": _safe_int(eval_primary.get("combined_panic_balls")),
                "combined_panic_sr": _clean_val(eval_primary.get("combined_panic_sr")),

                # Explicit Cohort Separation for Audit Consistency
                "ipl_pressure_volume": _safe_int(eval_row_ipl.get("pressure_balls_faced")) if eval_row_ipl is not None else _safe_int(player_info.get("ipl_pressure_volume")),
                "ipl_pressure_matches": _safe_int(eval_row_ipl.get("pressure_matches")) if eval_row_ipl is not None else _safe_int(player_info.get("ipl_matches")),
                "ipl_pressure_strike_rate": _clean_val(eval_row_ipl.get("pressure_strike_rate")) if eval_row_ipl is not None else _clean_val(player_info.get("ipl_raw_sr")),
                "ipl_context_adjusted_delta_sr": ipl_context_rae,
                "ipl_observed_pressure_sr": _clean_val(eval_row_ipl.get("observed_pressure_sr")) if eval_row_ipl is not None else None,
                "ipl_expected_pressure_sr": _clean_val(eval_row_ipl.get("expected_pressure_sr")) if eval_row_ipl is not None else None,

                "combined_pressure_volume": _safe_int(eval_row_comb.get("pressure_balls_faced")) if eval_row_comb is not None else _safe_int(player_info.get("combined_pressure_volume")),
                "combined_pressure_matches": _safe_int(eval_row_comb.get("pressure_matches")) if eval_row_comb is not None else _safe_int(player_info.get("combined_matches")),
                "combined_pressure_strike_rate": _clean_val(eval_row_comb.get("pressure_strike_rate")) if eval_row_comb is not None else None,
                "combined_context_adjusted_delta_sr": comb_context_rae,
                "combined_observed_pressure_sr": _clean_val(eval_row_comb.get("observed_pressure_sr")) if eval_row_comb is not None else None,
                "combined_expected_pressure_sr": _clean_val(eval_row_comb.get("expected_pressure_sr")) if eval_row_comb is not None else None,
            }

        # 2. Machine Learning Context (Holdout Test Evaluation & Contextual Baseline)
        ml_context = {
            "model_champion": "LightGBM Regressor v1.0 (Off-Bat Runs)",
            "benchmark_context_delta_sr": _clean_val(player_info.get("ipl_context_delta_sr")),
            "combined_benchmark_context_delta_sr": _clean_val(eval_row_comb.get("context_adjusted_delta_sr")) if eval_row_comb is not None else None,
            "population_scope": "Season 2026 Out-of-Time Test Partition (144 matches; covers ALL 31,165 test deliveries across both normal and pressure phases)",
            "test_eval_deliveries": 0,
            "actual_runs": None,
            "expected_runs_lightgbm": None,
            "net_residual": None,
            "mean_residual_per_ball": None,
            "actual_rate": None,
            "expected_rate": None,
            "test_status": "Historical cohort sample (2022-2025); 0 deliveries faced in 2026 holdout test partition",
            "disclaimer": "Contextual ML models estimate delivery-level match expectations (baseline), NOT intrinsic individual player talent. Residual outperformance measures player deviation from contextual match baseline.",
            "limitations": "Delivery-level unexplainable variance is high in T20 cricket (R² ≈ 0.024 across 31,165 test balls). Trajectory/pitch-map and shot execution metrics are absent from standard scorecards; model acts strictly as an objective contextual baseline.",
        }
        if self._batter_test_preds is not None:
            sub_pred = self._batter_test_preds[self._batter_test_preds["striker_id"] == player_id]
            if not sub_pred.empty:
                n_del = len(sub_pred)
                act_r = float(sub_pred["actual_runs"].sum())
                exp_r = float(sub_pred["pred_lightgbm"].sum())
                res = float(sub_pred["residual_lightgbm"].sum())
                ml_context.update({
                    "test_eval_deliveries": n_del,
                    "actual_runs": round(act_r, 1),
                    "expected_runs_lightgbm": round(exp_r, 1),
                    "net_residual": round(res, 2),
                    "mean_residual_per_ball": round(res / n_del, 3),
                    "actual_rate": round(act_r / n_del * 100, 1),
                    "expected_rate": round(exp_r / n_del * 100, 1),
                    "test_status": f"Evaluated across {n_del} holdout deliveries in 2026 test partition",
                })

        # 3. Behavioral Response (Observable Drought-State vs Strict t+1 Separation)
        behavioral_profile = {}
        if self._batter_behavioral is not None:
            sub_beh = self._batter_behavioral[self._batter_behavioral["striker_id"] == player_id]
            if not sub_beh.empty:
                b_raw = sub_beh.iloc[0].to_dict()
                behavioral_profile = _clean_val(b_raw)
                behavioral_profile.update({
                    "drought_metric_name": "Post-Dot Drought-State Scoring Recovery (Streak >= 2 Dots)",
                    "drought_state_balls": _safe_int(b_raw.get("post_dot_balls")),
                    "drought_state_strike_rate": _clean_val(b_raw.get("post_dot_strike_rate")),
                    "drought_state_dot_pct": _clean_val(b_raw.get("post_dot_dot_pct")),
                    "drought_state_boundary_pct": _clean_val(b_raw.get("post_dot_boundary_pct")),
                    "drought_state_wicket_pct": _clean_val(b_raw.get("post_dot_wicket_pct")),
                    "delta_sr_drought_state": _clean_val(b_raw.get("delta_sr_post_dot")),
                    "drought_state_definition": "Evaluates all deliveries faced while in personal streak of >= 2 consecutive dots until a scoring shot occurs.",
                    "drought_cohort_summary": "19,818 drought-state deliveries observed (mean 1.33 balls per episode) across 14,876 unique drought episodes in 834 matches.",

                    # Strict t+1 immediate recovery separation
                    "strict_t1_available": False,
                    "strict_t1_metric_name": "Strict Immediate t+1 Single-Ball Recovery (Next Ball After Episode Trigger)",
                    "strict_t1_status": "Insufficient Evidence at Individual Player Level",
                    "strict_t1_cohort_summary": "12,653 strict single-ball t+1 deliveries across 14,876 unique drought episodes in 834 matches.",
                    "strict_t1_note": "Individual player-level strict single-ball partition is not preserved without event deduplication. In accordance with competition audit standards, drought-state strike rate is NOT substituted.",

                    "interpretation": (
                        "Observable sequence pattern: evaluates performance while in an observable dot drought state (streak >= 2 dots) without assuming psychological traits."
                    ),
                })

        # 4. Reliability & Risk Flags
        risk_records = []
        if self._risk_flags is not None:
            sub_rf = self._risk_flags[self._risk_flags["player_id"] == player_id]
            if not sub_rf.empty:
                risk_records = [_clean_val(r) for r in sub_rf.to_dict(orient="records")]

        eval_rel = eval_row_ipl if eval_row_ipl is not None else eval_row_comb
        reliability = {
            "evidence_tier": player_info.get("evidence_tier"),
            "stability_archetype": player_info.get("stability_archetype"),
            "shrunk_m25": player_info.get("ipl_shrunk_m25"),
            "shrunk_m45": player_info.get("ipl_shrunk_m45"),
            "shrunk_m60": player_info.get("ipl_shrunk_m60"),
            "shrunk_m90": player_info.get("ipl_shrunk_m90"),
            "pressure_sr_ci_lower_95": _clean_val(eval_rel.get("pressure_sr_ci_lower_95")) if eval_rel is not None else None,
            "pressure_sr_ci_upper_95": _clean_val(eval_rel.get("pressure_sr_ci_upper_95")) if eval_rel is not None else None,
            "pressure_dot_pct_posterior": _clean_val(eval_rel.get("pressure_dot_pct_posterior")) if eval_rel is not None else None,
            "pressure_dot_pct_ci_lower_95": _clean_val(eval_rel.get("pressure_dot_pct_ci_lower_95")) if eval_rel is not None else None,
            "pressure_dot_pct_ci_upper_95": _clean_val(eval_rel.get("pressure_dot_pct_ci_upper_95")) if eval_rel is not None else None,
            "risk_flags": risk_records,
            "has_risk_flags": len(risk_records) > 0 and any(r.get("risk_flag_count", 0) > 0 for r in risk_records),
        }

        # 5. Distinct Populations Mapping
        populations = {
            "ml_holdout": "Season 2026 Out-of-Time Test Partition (144 matches, 31,165 batter balls across ALL match phases, normal and pressure)",
            "pressure_evaluation": "2022-2026 Primary Pressure Cohort (837 matches, 71,523 batter balls under L1 >= 0.50)",
            "behavioral": "Observable Event Sample (14,876 drought episodes, 19,818 drought-state deliveries in 834 matches)",
            "reliability": f"Format-Specific Candidate Pool (IPL: {player_info.get('ipl_pressure_volume', 0)} balls, {player_info.get('ipl_matches', 0)} matches for empirical Bayes shrinkage)",
        }

        # Phase breakdown
        phases = []
        if self._batter_phase is not None:
            p_sub = self._batter_phase[self._batter_phase["striker_id"] == player_id]
            phases = [_clean_val(r) for r in p_sub.to_dict(orient="records")]

        # Shrinkage sensitivity curve
        shrinkage_curve = [
            {"parameter": "Raw SR", "m_value": 0, "sr": player_info.get("ipl_raw_sr")},
            {"parameter": "Shrunk M=25", "m_value": 25, "sr": player_info.get("ipl_shrunk_m25")},
            {"parameter": "Shrunk M=45", "m_value": 45, "sr": player_info.get("ipl_shrunk_m45")},
            {"parameter": "Shrunk M=60", "m_value": 60, "sr": player_info.get("ipl_shrunk_m60")},
            {"parameter": "Shrunk M=90", "m_value": 90, "sr": player_info.get("ipl_shrunk_m90")},
        ]

        return {
            "player": player_info,
            "pressure_performance": pressure_perf,
            "ml_context": ml_context,
            "behavioral": behavioral_profile,
            "reliability": reliability,
            "phases": phases,
            "shrinkage_curve": shrinkage_curve,
            "populations": populations,
        }

    def get_bowlers(
        self,
        format_filter: str = "IPL",
        role: Optional[str] = None,
        search: Optional[str] = None,
        tier: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query bowler candidates and rankings with dynamic filters."""
        self.load_data()
        df = self._bowler_matrix.copy()

        # Exclude Sikandar Raza from bowler evaluation UI
        df = df[~df["player_name"].str.contains("Sikandar Raza", case=False, na=False)]

        if search:
            df = df[df["player_name"].str.contains(search, case=False, na=False)]
        if role and role != "ALL":
            df = df[df["primary_role"] == role]
        if tier and tier != "ALL":
            df = df[df["evidence_tier"] == tier]

        records = df.to_dict(orient="records")
        return [_clean_val(r) for r in records]

    def get_bowler_detail(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve complete unified scouting dossier for a single bowler."""
        self.load_data()
        row_match = self._bowler_matrix[self._bowler_matrix["player_id"] == player_id]
        if row_match.empty:
            row_match = self._bowler_candidates_ipl[self._bowler_candidates_ipl["bowler_id"] == player_id]
            if row_match.empty:
                return None
            player_info = _clean_val(row_match.iloc[0].to_dict())
            player_info["player_name"] = player_info.get("bowler_name")
            player_info["player_id"] = player_id
        else:
            player_info = _clean_val(row_match.iloc[0].to_dict())

        # 1. Pressure Performance from full evaluation tables (IPL-specific + Combined)
        pressure_perf = {}
        eval_row_ipl = None
        eval_row_comb = None

        if self._bowler_eval_ipl is not None:
            e_sub_ipl = self._bowler_eval_ipl[self._bowler_eval_ipl["bowler_id"] == player_id]
            if not e_sub_ipl.empty:
                eval_row_ipl = e_sub_ipl.iloc[0]

        if self._bowler_eval is not None:
            e_sub_comb = self._bowler_eval[self._bowler_eval["bowler_id"] == player_id]
            if not e_sub_comb.empty:
                eval_row_comb = e_sub_comb.iloc[0]

        eval_primary = eval_row_ipl if eval_row_ipl is not None else eval_row_comb

        if eval_primary is not None:
            ipl_all_runs_rcae = _clean_val(eval_row_ipl.get("all_runs_rcae_delta_econ")) if eval_row_ipl is not None else _clean_val(player_info.get("ipl_context_delta_econ"))
            ipl_legal_rcae = _clean_val(eval_row_ipl.get("legal_rcae_delta_econ")) if eval_row_ipl is not None else _clean_val(player_info.get("ipl_legal_context_delta_econ"))
            comb_all_runs_rcae = _clean_val(eval_row_comb.get("all_runs_rcae_delta_econ")) if eval_row_comb is not None else None
            comb_legal_rcae = _clean_val(eval_row_comb.get("legal_rcae_delta_econ")) if eval_row_comb is not None else None

            pressure_perf = {
                "pressure_legal_balls": _safe_int(eval_primary.get("pressure_legal_balls")),
                "pressure_total_deliveries": _safe_int(eval_primary.get("pressure_total_deliveries")),
                "pressure_overs": _clean_val(eval_primary.get("pressure_overs")),
                "pressure_runs_conceded": _safe_int(eval_primary.get("pressure_runs_conceded")),
                "pressure_wickets": _safe_int(eval_primary.get("pressure_wickets")),
                "pressure_economy_rate": _clean_val(eval_primary.get("pressure_economy_rate")),
                "normal_economy_rate": _clean_val(eval_primary.get("normal_economy_rate")),
                "delta_economy": _clean_val(eval_primary.get("delta_economy")),
                "pressure_dot_pct": _clean_val(eval_primary.get("pressure_dot_ball_pct")),
                "normal_dot_pct": _clean_val(eval_primary.get("normal_dot_ball_pct")),
                "delta_dot_pct": _clean_val(eval_primary.get("delta_dot_ball_pct")),
                "pressure_boundary_concession_pct": _clean_val(eval_primary.get("pressure_boundary_concession_pct")),
                "normal_boundary_concession_pct": _clean_val(eval_primary.get("normal_boundary_concession_pct")),
                "delta_boundary_concession_pct": _clean_val(eval_primary.get("delta_boundary_concession_pct")),
                "all_runs_rcae_delta_econ": ipl_all_runs_rcae,
                "observed_pressure_econ": _clean_val(eval_primary.get("observed_pressure_econ")),
                "expected_pressure_econ": _clean_val(eval_primary.get("expected_pressure_econ")),
                "legal_rcae_delta_econ": ipl_legal_rcae,
                "observed_legal_econ": _clean_val(eval_primary.get("observed_legal_econ")),
                "expected_legal_econ": _clean_val(eval_primary.get("expected_legal_econ")),
                "pressure_match_pass_rate": _clean_val(eval_primary.get("pressure_match_pass_rate")),
                "pressure_match_econ_std": _clean_val(eval_primary.get("pressure_match_econ_std")),
                "pressure_match_econ_median": _clean_val(eval_primary.get("pressure_match_econ_median")),
                "pressure_match_econ_iqr": _clean_val(eval_primary.get("pressure_match_econ_iqr")),
                "vs_top_order_balls": _safe_int(eval_primary.get("vs_top_order_balls")),
                "vs_top_order_economy": _clean_val(eval_primary.get("vs_top_order_economy")),
                "vs_tail_balls": _safe_int(eval_primary.get("vs_tail_balls")),
                "vs_tail_economy": _clean_val(eval_primary.get("vs_tail_economy")),
                "chase_crunch_balls": _safe_int(eval_primary.get("chase_crunch_balls")),
                "chase_crunch_economy": _clean_val(eval_primary.get("chase_crunch_economy")),
                "wickets_per_over": _clean_val(eval_primary.get("wickets_per_over")),
                "wicket_impact_score": _clean_val(eval_primary.get("wicket_impact_score")),

                # Explicit Cohort Separation for Audit Consistency
                "ipl_pressure_legal_balls": _safe_int(eval_row_ipl.get("pressure_legal_balls")) if eval_row_ipl is not None else _safe_int(player_info.get("ipl_pressure_volume")),
                "ipl_pressure_matches": _safe_int(eval_row_ipl.get("pressure_matches")) if eval_row_ipl is not None else _safe_int(player_info.get("ipl_matches")),
                "ipl_pressure_economy_rate": _clean_val(eval_row_ipl.get("pressure_economy_rate")) if eval_row_ipl is not None else _clean_val(player_info.get("ipl_raw_econ")),
                "ipl_all_runs_rcae_delta_econ": ipl_all_runs_rcae,
                "ipl_observed_pressure_econ": _clean_val(eval_row_ipl.get("observed_pressure_econ")) if eval_row_ipl is not None else None,
                "ipl_expected_pressure_econ": _clean_val(eval_row_ipl.get("expected_pressure_econ")) if eval_row_ipl is not None else None,
                "ipl_legal_rcae_delta_econ": ipl_legal_rcae,
                "ipl_observed_legal_econ": _clean_val(eval_row_ipl.get("observed_legal_econ")) if eval_row_ipl is not None else None,
                "ipl_expected_legal_econ": _clean_val(eval_row_ipl.get("expected_legal_econ")) if eval_row_ipl is not None else None,

                "combined_pressure_legal_balls": _safe_int(eval_row_comb.get("pressure_legal_balls")) if eval_row_comb is not None else _safe_int(player_info.get("combined_pressure_volume")),
                "combined_pressure_matches": _safe_int(eval_row_comb.get("pressure_matches")) if eval_row_comb is not None else _safe_int(player_info.get("combined_matches")),
                "combined_pressure_economy_rate": _clean_val(eval_row_comb.get("pressure_economy_rate")) if eval_row_comb is not None else None,
                "combined_all_runs_rcae_delta_econ": comb_all_runs_rcae,
                "combined_observed_pressure_econ": _clean_val(eval_row_comb.get("observed_pressure_econ")) if eval_row_comb is not None else None,
                "combined_expected_pressure_econ": _clean_val(eval_row_comb.get("expected_pressure_econ")) if eval_row_comb is not None else None,
                "combined_legal_rcae_delta_econ": comb_legal_rcae,
                "combined_observed_legal_econ": _clean_val(eval_row_comb.get("observed_legal_econ")) if eval_row_comb is not None else None,
                "combined_expected_legal_econ": _clean_val(eval_row_comb.get("expected_legal_econ")) if eval_row_comb is not None else None,
            }

        # 2. Machine Learning Context (Holdout Test Evaluation & Contextual Baseline)
        # Note: Actual-vs-expected wickets strictly moved to experimental_wicket_classifier
        ml_context = {
            "model_champion": "LightGBM Regressor v1.0 (Defensive Conceded Runs)",
            "benchmark_all_runs_rcae": _clean_val(player_info.get("ipl_context_delta_econ")),
            "benchmark_legal_rcae": _clean_val(player_info.get("ipl_legal_context_delta_econ")),
            "combined_benchmark_all_runs_rcae": _clean_val(eval_row_comb.get("all_runs_rcae_delta_econ")) if eval_row_comb is not None else None,
            "population_scope": "Season 2026 Out-of-Time Test Partition (144 matches; covers ALL 32,529 test deliveries across both normal and pressure phases)",
            "test_eval_deliveries": 0,
            "actual_runs_conceded": None,
            "expected_runs_lightgbm": None,
            "net_residual_runs": None,
            "mean_residual_per_ball": None,
            "actual_economy": None,
            "expected_economy": None,
            "suppression_per_over": None,
            "experimental_wicket_classifier": None,
            "test_status": "Historical cohort sample (2022-2025); 0 deliveries bowled in 2026 holdout test partition",
            "disclaimer": "Contextual ML models estimate delivery-level match expectations (baseline), NOT intrinsic individual player skill. Net defensive suppression measures conceded runs below match context expectation.",
            "limitations": "Individual delivery outcome variance is high in T20 cricket (R² ≈ 0.021 for conceded runs). Pitch friction, ball condition, and exact landing map are absent; model acts strictly as an objective contextual baseline.",
        }
        if self._bowler_test_preds is not None:
            sub_pred = self._bowler_test_preds[self._bowler_test_preds["bowler_id"] == player_id]
            if not sub_pred.empty:
                n_del = len(sub_pred)
                act_r = float(sub_pred["actual_runs_conceded"].sum())
                exp_r = float(sub_pred["pred_lightgbm_runs"].sum())
                res = float(sub_pred["residual_runs"].sum())
                act_w = int(sub_pred["actual_wicket"].sum())
                exp_w = float(sub_pred["pred_lightgbm_wkt"].sum())
                ml_context.update({
                    "test_eval_deliveries": n_del,
                    "actual_runs_conceded": round(act_r, 1),
                    "expected_runs_lightgbm": round(exp_r, 1),
                    "net_residual_runs": round(res, 2),
                    "mean_residual_per_ball": round(res / n_del, 3),
                    "actual_economy": round(act_r / n_del * 6, 2),
                    "expected_economy": round(exp_r / n_del * 6, 2),
                    "suppression_per_over": round(-res / n_del * 6, 2),
                    "experimental_wicket_classifier": {
                        "model": "LightGBM Binary Classifier (Wicket Event)",
                        "actual_wickets": act_w,
                        "expected_wickets": round(exp_w, 2),
                        "residual_wickets": round(act_w - exp_w, 2),
                        "brier_score": 0.0481,
                        "prior_brier_baseline": 0.0480,
                        "pr_auc": 0.0715,
                        "empirical_base_rate": 0.0509,
                        "roc_auc": 0.5902,
                        "status": "EXPERIMENTAL_DIAGNOSTIC",
                        "advisory": "Due to high unexplainable delivery-level variance in T20 dismissals and marginal separation over base rates (PR-AUC 0.0715 vs 0.0509 base rate; Brier 0.0481 vs 0.0480 dummy prior), this classifier serves strictly as an exploratory situational diagnostic. It does NOT represent validated individual bowler wicket-taking skill or bowler underperformance.",
                    },
                    "test_status": f"Evaluated across {n_del} holdout deliveries in 2026 test partition",
                })

        # 3. Behavioral Response (Observable Bounce-Back Sequences)
        behavioral_profile = {}
        if self._bowler_behavioral is not None:
            sub_beh = self._bowler_behavioral[self._bowler_behavioral["bowler_id"] == player_id]
            if not sub_beh.empty:
                b_raw = sub_beh.iloc[0].to_dict()
                behavioral_profile = _clean_val(b_raw)
                behavioral_profile.update({
                    "post_boundary_metric_name": "Post-Boundary Bounce-Back Containment (t+1)",
                    "post_boundary_cohort_summary": "29,219 intra-over (t+1) deliveries observed across 32,662 boundary triggers in 836 matches.",
                    "post_cluster_metric_name": "Cluster Hemorrhage Resistance (Post 8+ runs in 3 balls)",
                    "post_cluster_cohort_summary": "24,303 cluster trigger events evaluated in 834 matches.",
                    "progression_metric_name": "Cumulative Inning Over Exposure Progression (Early 1-12 vs Late 13-24+)",
                    "interpretation": (
                        "Observable sequence pattern: evaluates defensive suppression on immediate subsequent legal deliveries following an observable boundary event."
                    ),
                })

        # 4. Reliability & Risk Flags
        risk_records = []
        if self._risk_flags is not None:
            sub_rf = self._risk_flags[self._risk_flags["player_id"] == player_id]
            if not sub_rf.empty:
                risk_records = [_clean_val(r) for r in sub_rf.to_dict(orient="records")]

        eval_rel = eval_row_ipl if eval_row_ipl is not None else eval_row_comb
        reliability = {
            "evidence_tier": player_info.get("evidence_tier"),
            "stability_archetype": player_info.get("stability_archetype"),
            "shrunk_m25": player_info.get("ipl_shrunk_m25"),
            "shrunk_m45": player_info.get("ipl_shrunk_m45"),
            "shrunk_m60": player_info.get("ipl_shrunk_m60"),
            "shrunk_m90": player_info.get("ipl_shrunk_m90"),
            "pressure_econ_ci_lower_95": _clean_val(eval_rel.get("pressure_econ_ci_lower_95")) if eval_rel is not None else None,
            "pressure_econ_ci_upper_95": _clean_val(eval_rel.get("pressure_econ_ci_upper_95")) if eval_rel is not None else None,
            "pressure_dot_pct_posterior": _clean_val(eval_rel.get("pressure_dot_pct_posterior")) if eval_rel is not None else None,
            "pressure_dot_pct_ci_lower_95": _clean_val(eval_rel.get("pressure_dot_pct_ci_lower_95")) if eval_rel is not None else None,
            "pressure_dot_pct_ci_upper_95": _clean_val(eval_rel.get("pressure_dot_pct_ci_upper_95")) if eval_rel is not None else None,
            "risk_flags": risk_records,
            "has_risk_flags": len(risk_records) > 0 and any(r.get("risk_flag_count", 0) > 0 for r in risk_records),
        }

        # 5. Distinct Populations Mapping
        populations = {
            "ml_holdout": "Season 2026 Out-of-Time Test Partition (144 matches, 32,529 bowler balls across ALL match phases, normal and pressure)",
            "pressure_evaluation": "2022-2026 Primary Pressure Cohort (837 matches, 44,333 bowler balls under L1 >= 0.50)",
            "behavioral": "Observable Event Sample (32,662 boundary triggers -> 29,219 intra-over t+1 deliveries in 836 matches)",
            "reliability": f"Format-Specific Candidate Pool (IPL: {player_info.get('ipl_pressure_volume', 0)} legal balls, {player_info.get('ipl_matches', 0)} matches for empirical Bayes shrinkage)",
        }

        # Phase breakdown
        phases = []
        if self._bowler_phase is not None:
            p_sub = self._bowler_phase[self._bowler_phase["bowler_id"] == player_id]
            phases = [_clean_val(r) for r in p_sub.to_dict(orient="records")]

        # Shrinkage sensitivity curve
        shrinkage_curve = [
            {"parameter": "Raw Econ", "m_value": 0, "econ": player_info.get("ipl_raw_econ")},
            {"parameter": "Shrunk M=25", "m_value": 25, "econ": player_info.get("ipl_shrunk_m25")},
            {"parameter": "Shrunk M=45", "m_value": 45, "econ": player_info.get("ipl_shrunk_m45")},
            {"parameter": "Shrunk M=60", "m_value": 60, "econ": player_info.get("ipl_shrunk_m60")},
            {"parameter": "Shrunk M=90", "m_value": 90, "econ": player_info.get("ipl_shrunk_m90")},
        ]

        return {
            "player": player_info,
            "pressure_performance": pressure_perf,
            "ml_context": ml_context,
            "behavioral": behavioral_profile,
            "reliability": reliability,
            "phases": phases,
            "shrinkage_curve": shrinkage_curve,
            "populations": populations,
        }

    def get_comparison(self, player_a_id: int, player_b_id: int, discipline: str) -> Dict[str, Any]:
        """Compare two players with side-by-side metrics, pairwise bootstrap test, and sample comparability analysis."""
        self.load_data()

        is_batter = discipline.lower().startswith("bat")
        if is_batter:
            p_a = self.get_batter_detail(player_a_id)
            p_b = self.get_batter_detail(player_b_id)
        else:
            p_a = self.get_bowler_detail(player_a_id)
            p_b = self.get_bowler_detail(player_b_id)

        # Check if pair is in top_10_pairwise_bootstrap
        bootstrap_match = None
        if self._pairwise_bootstrap is not None:
            b_df = self._pairwise_bootstrap
            sub = b_df[
                ((b_df["player_a_id"] == player_a_id) & (b_df["player_b_id"] == player_b_id)) |
                ((b_df["player_a_id"] == player_b_id) & (b_df["player_b_id"] == player_a_id))
            ]
            if not sub.empty:
                bootstrap_match = _clean_val(sub.iloc[0].to_dict())

        # Also check candidate_intelligence head-to-head files if not matched
        h2h_match = None
        h2h_df = self._batter_h2h if is_batter else self._bowler_h2h
        if h2h_df is not None:
            sub_h2h = h2h_df[
                ((h2h_df["player_a_id"] == player_a_id) & (h2h_df["player_b_id"] == player_b_id)) |
                ((h2h_df["player_a_id"] == player_b_id) & (h2h_df["player_b_id"] == player_a_id))
            ]
            if not sub_h2h.empty:
                h2h_match = _clean_val(sub_h2h.iloc[0].to_dict())

        # Sample Comparability Audit
        vol_a = (p_a.get("player", {}).get("ipl_pressure_volume") or 0) if p_a else 0
        vol_b = (p_b.get("player", {}).get("ipl_pressure_volume") or 0) if p_b else 0
        tier_a = p_a.get("player", {}).get("evidence_tier") if p_a else "UNKNOWN"
        tier_b = p_b.get("player", {}).get("evidence_tier") if p_b else "UNKNOWN"

        ratio = round(max(vol_a, vol_b) / max(1, min(vol_a, vol_b)), 2) if min(vol_a, vol_b) > 0 else 999.0
        sample_divergence = ratio > 2.5 or tier_a != tier_b

        comparability_audit = {
            "volume_ratio": ratio,
            "sample_divergence": sample_divergence,
            "tier_a": tier_a,
            "tier_b": tier_b,
            "status": "DIVERGENT_SAMPLES" if sample_divergence else "HIGHLY_COMPARABLE",
            "disclosure": (
                f"Sample volume disparity detected ({vol_a}b vs {vol_b}b, ratio {ratio}x; {tier_a} vs {tier_b}). Candidate with smaller sample is subject to substantially stronger Bayesian shrinkage toward the prior mean. Do NOT declare artificial superiority based on unadjusted rates."
                if sample_divergence else
                f"Both candidates possess comparable evidence tiers ({tier_a}) and balanced pressure volumes ({vol_a}b vs {vol_b}b)."
            ),
        }

        return {
            "player_a": p_a,
            "player_b": p_b,
            "pairwise_bootstrap": bootstrap_match,
            "curated_h2h": h2h_match,
            "comparability_audit": comparability_audit,
        }

    def get_pressure_distributions(self) -> Dict[str, Any]:
        """Return analytical distributions for pressure framework."""
        return {
            "tiers": [
                {"tier": "EXTREME", "batter_pct": 8.4, "bowler_pct": 9.1, "description": "High required rate (RRR >= 12.0) or death overs crunch with multiple wickets down"},
                {"tier": "HIGH", "batter_pct": 14.0, "bowler_pct": 13.3, "description": "Accelerating chase demand (RRR >= 9.5) or middle overs resource scarcity"},
                {"tier": "MODERATE", "batter_pct": 28.5, "bowler_pct": 27.2, "description": "Standard match tension; balanced resource states"},
                {"tier": "LOW", "batter_pct": 49.1, "bowler_pct": 50.4, "description": "Base match baseline with ample balls remaining and comfortable required rates"},
            ],
            "pressure_vs_normal": {
                "batters": [
                    {"metric": "Strike Rate", "normal": 128.27, "pressure": 135.53, "unit": "SR points", "delta": "+7.26"},
                    {"metric": "Dot Ball %", "normal": 32.14, "pressure": 34.78, "unit": "%", "delta": "+2.64%"},
                    {"metric": "Boundary %", "normal": 23.79, "pressure": 25.06, "unit": "%", "delta": "+1.27%"},
                    {"metric": "Dismissal Rate", "normal": 4.82, "pressure": 7.15, "unit": "%", "delta": "+2.33%"},
                ],
                "bowlers": [
                    {"metric": "Economy Rate", "normal": 8.41, "pressure": 9.82, "unit": "runs/over", "delta": "+1.41"},
                    {"metric": "Dot Ball %", "normal": 38.52, "pressure": 32.84, "unit": "%", "delta": "-5.68%"},
                    {"metric": "Wickets / Over", "normal": 0.28, "pressure": 0.42, "unit": "wkts/over", "delta": "+0.14"},
                    {"metric": "Boundary Concession %", "normal": 14.21, "pressure": 18.65, "unit": "%", "delta": "+4.44%"},
                ],
            },
            "phase_breakdown": [
                {"phase": "Powerplay (Overs 1-6)", "pressure_deliveries_pct": 18.5, "normal_deliveries_pct": 33.2},
                {"phase": "Middle (Overs 7-15)", "pressure_deliveries_pct": 43.8, "normal_deliveries_pct": 45.6},
                {"phase": "Death (Overs 16-20)", "pressure_deliveries_pct": 37.7, "normal_deliveries_pct": 21.2},
            ],
            "asymmetry_principles": [
                {
                    "title": "Chasing Run-Rate Pressure vs Tail Closure",
                    "explanation": "Batters face severe pressure when the required run rate climbs above 10.0 rpo regardless of wickets lost, whereas bowlers experience pressure when defending narrow margins or facing top-order power hitters.",
                },
                {
                    "title": "First-Innings Resource Modeling",
                    "explanation": "Because chasing targets do not exist in the first innings, pressure leverage is modeled via FirstInningsResourceModel estimating E[Remaining Runs | Competition, Over Bucket, Wickets Lost] against competition-level empirical resource grids (IPL benchmark: 183.0, Senior T20I: 165.2). The first-innings resource grid does not use innings-phase conditioning.",
                },
                {
                    "title": "DLS Uncertainty Isolation",
                    "explanation": "Deliveries bowled during rain-interrupted chases prior to revised target confirmation are strictly flagged and excluded from primary player ranking models to prevent artificial rate distortion.",
                },
            ],
        }

    def get_methodology(self) -> Dict[str, Any]:
        """Return explainable methodology documentation and mathematical models."""
        return {
            "title": "RR EDGE Explainable Cricket Intelligence Architecture",
            "framework_steps": [
                {"step": 1, "name": "Event Attribution & Match-State Reconstruction", "description": "Pre-delivery state calculation (balls remaining, score, required run rate, phase, wickets down) avoiding any outcome leakage."},
                {"step": 2, "name": "Asymmetric Pressure Framework & First-Innings Resource Model", "description": "Independent batter and bowler pressure classifications into EXTREME, HIGH, MODERATE, and LOW tiers. In innings 1, par deficit is derived from FirstInningsResourceModel conditioned on Competition, Over bucket, and Wickets lost (no innings-phase conditioning)."},
                {"step": 3, "name": "Context Adjustment (RAE & RCAE)", "description": "Rate-normalized delivery performance relative to contextual expectations: Batter RAE (ΔSR) in strike-rate points ((Runs_obs - Runs_exp) / Balls * 100), Primary Bowler All-Runs RCAE (ΔEconomy) in runs per over ((All_Runs_obs - All_Runs_exp) / Legal Balls * 6) including wide and no-ball extras against legal exposure, and Secondary Diagnostic Legal-Ball RCAE (ΔLegal Economy) ((Legal_Runs_obs - Legal_Runs_exp) / Legal Balls * 6), conditioned on Competition type, Innings phase, and Wickets bucket."},
                {"step": 4, "name": "Empirical Bayes Shrinkage & Uncertainty Bounds", "description": "Format-specific shrinkage across M=25, 45, 60, and 90, alongside 10,000-resample match-cluster bootstrap testing."},
            ],
            "model_conditioning_variables": {
                "first_innings_resource_model": [
                    "Competition",
                    "Over bucket",
                    "Wickets lost",
                ],
                "context_adjusted_performance_models": [
                    "Competition type",
                    "Innings phase",
                    "Wickets bucket",
                ],
                "distinction_note": "The first-innings resource grid conditions strictly on Competition, Over bucket, and Wickets lost; it does not use innings-phase conditioning.",
            },
            "shrinkage_grid": [
                {"m": 25, "weight_76b": "75.2%", "weight_334b": "93.0%", "use_case": "Conservative shrinkage preserving discovery ceiling for breakout talents"},
                {"m": 45, "weight_76b": "62.8%", "weight_334b": "88.1%", "use_case": "Primary recommended evaluation benchmark balancing upside and reliability"},
                {"m": 60, "weight_76b": "55.9%", "weight_334b": "84.8%", "use_case": "Holdout RMSE minimum empirically validated in holdout testing"},
                {"m": 90, "weight_76b": "45.8%", "weight_334b": "78.8%", "use_case": "Heavy shrinkage pulling small-sample performers towards cohort mean"},
            ],
            "evidence_tiers": [
                {"tier": "CONFIDENT_EVIDENCE", "criteria": ">= 60 pressure balls across >= 8 matches and >= 2 competitions", "reliability": "High parameter stability; eligible for primary squad anchor roles"},
                {"tier": "MODERATE_EVIDENCE", "criteria": ">= 24 pressure balls across >= 4 matches", "reliability": "Moderate stability; suitable for role-specific rotational evaluation"},
                {"tier": "PROVISIONAL_EVIDENCE", "criteria": "12 to 23 pressure balls across >= 2 matches", "reliability": "High parameter uncertainty; exploratory scouting flag"},
                {"tier": "INSUFFICIENT_EVIDENCE", "criteria": "< 12 pressure balls", "reliability": "Excluded from statistical ranking models"},
            ],
        }

    def get_explorer_data(
        self,
        discipline: str = "BATTER",
        format_filter: str = "IPL",
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 15,
    ) -> Dict[str, Any]:
        """Query tabular candidate records with pagination."""
        self.load_data()

        if discipline.upper() == "BATTER":
            df = self._batter_candidates_ipl.copy()
            if search:
                df = df[df["striker_name"].str.contains(search, case=False, na=False)]
            total = len(df)
            start = (page - 1) * page_size
            end = start + page_size
            rows = [_clean_val(r) for r in df.iloc[start:end].to_dict(orient="records")]
            # Standardize names
            for r in rows:
                r["player_name"] = r.get("striker_name")
                r["player_id"] = r.get("striker_id")
        else:
            df = self._bowler_candidates_ipl.copy()
            if search:
                df = df[df["bowler_name"].str.contains(search, case=False, na=False)]
            total = len(df)
            start = (page - 1) * page_size
            end = start + page_size
            rows = [_clean_val(r) for r in df.iloc[start:end].to_dict(orient="records")]
            for r in rows:
                r["player_name"] = r.get("bowler_name")
                r["player_id"] = r.get("bowler_id")

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": int(np.ceil(total / page_size)),
            "rows": rows,
        }


# Global singleton instance
data_service = DataService()

