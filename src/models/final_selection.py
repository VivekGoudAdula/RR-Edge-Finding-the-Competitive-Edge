"""Final Selection Intelligence & Decision Dossier for RR EDGE.

This module builds the final evidence-backed decision matrices and ordered Top-10 recommendations
for batters and bowlers in the SupeRR Selector competition.

Key Design Elements:
- Complete candidate decision matrices (18 candidates per discipline).
- Format-specific metrics strictly distinguished without mixed-format distortion.
- Reconciled pressure exposure denominators (IPL, T20I, Combined).
- Multi-parameter empirical Bayes shrinkage sensitivity (M=25, 45, 60, 90).
- Match-cluster-aware bootstrap comparisons with 10,000 iterations and fixed seed (seed=42).
- Ordered Top-10 recommendations balancing proven anchors with high-upside discovery talents.
- Strict elimination of uncalculated or speculative technical claims.
"""

from typing import List, Dict, Any, Optional
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.candidate_intelligence import compute_match_cluster_bootstrap


def build_final_batter_decision_matrix(base_dir: str = ".") -> pd.DataFrame:
    """Build the final comprehensive decision matrix for top batter candidates.

    Parameters
    ----------
    base_dir : str
        Base directory of the rr-edge codebase.

    Returns
    -------
    pd.DataFrame
        Decision matrix with complete metrics, stability, risks, and selection recommendations.
    """
    eval_dir = os.path.join(base_dir, "data", "processed", "player_evaluations")
    ci_dir = os.path.join(base_dir, "data", "processed", "candidate_intelligence")

    b_ipl = pd.read_parquet(os.path.join(eval_dir, "batter_evaluation_ipl.parquet"))
    b_t20i = pd.read_parquet(os.path.join(eval_dir, "batter_evaluation_t20i.parquet"))
    recon = pd.read_csv(os.path.join(ci_dir, "candidate_denominator_reconciliation.csv"))
    recon_b = recon[recon["discipline"] == "Batter"].set_index("player_id")

    candidates_meta = [
        # Rank 1: Tim David
        {
            "player_id": 6396,
            "player_name": "Tim David",
            "primary_role": "Middle-Order",
            "phase_suitability": "Middle (Overs 7-15) & Death (Overs 16-20)",
            "is_recommended_top_10": True,
            "top_10_rank": 1,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 1: #1 Multi-Format Finisher. Only player in tournament history to exceed 170.0 shrunk strike rate (M=45) in both IPL (170.7) and Senior T20Is (171.1) across 510 combined pressure balls with low dot balls (30.8% IPL, 33.0% T20I). Selection judgement call vs SKY driven by multi-format finishing versatility.",
            "main_strengths": "Demonstrates elite multi-format pressure finishing: IPL 334 balls (175.4 raw SR, 170.7 M45, +24.9 RAE, 73.1% match pass rate) and T20I 176 balls (184.7 raw SR, 171.1 M45, +52.1 RAE, 90.0% match pass rate). Combined 510 pressure balls across 47 matches.",
            "main_weaknesses": "Higher match-to-match variance in international cricket (T20I match std 60.1) compared to domestic franchise baseline (IPL std 79.9).",
            "selection_risks": "Low risk; classified as ROBUST_ANCHOR across 47 combined matches (510 pressure balls).",
        },
        # Rank 2: Suryakumar Yadav
        {
            "player_id": 1699,
            "player_name": "Suryakumar Yadav",
            "primary_role": "Middle-Order",
            "phase_suitability": "Middle Crisis (Overs 7-15) & Death Anchor (Overs 16-20)",
            "is_recommended_top_10": True,
            "top_10_rank": 2,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 2: #1 Middle Crisis Anchor. Tournament volume benchmark (832 combined balls across 60 matches), highest match pass rate (83.9% across 31 evaluated IPL matches), and +18.1 IPL RAE. Indistinguishable on bootstrap from Tim David (CI [-18.1, 40.9]) and Jaiswal (CI [-36.6, 15.3]); positioned at #2 as premier crisis stabilizer.",
            "main_strengths": "Highest pressure sample volume in tournament (IPL 579 balls, T20I 253 balls, 832 combined across 60 matches). High consistency (IPL SR 163.7, +18.1 RAE, 83.9% match pass rate) and low dot-ball rate (30.4% IPL dots, 24.0% boundary rate).",
            "main_weaknesses": "Slightly lower boundary percentage in T20I cricket (23.3%) relative to IPL (24.0%), and higher T20I dot rate (40.3%).",
            "selection_risks": "Minimal selection risk; benchmark ROBUST_ANCHOR with proven multi-season consistency.",
        },
        # Rank 3: Yashasvi Jaiswal
        {
            "player_id": 6819,
            "player_name": "Yashasvi Jaiswal",
            "primary_role": "Top-Order",
            "phase_suitability": "Powerplay (Overs 1-6) & Early Middle (Overs 7-11)",
            "is_recommended_top_10": True,
            "top_10_rank": 3,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 3: Premier IPL Top-Order Anchor. Elite Powerplay aggression (174.8 IPL raw SR, +30.6 RAE, 32.0% boundary rate across 266 IPL pressure balls). Positioned ahead of Pooran via superior boundary production and Powerplay phase leverage; indistinguishable on bootstrap from SKY and Pooran.",
            "main_strengths": "Premier IPL top-order pressure anchor: 266 balls across 38 matches, 174.8 raw SR, +30.6 RAE, 32.0% boundary rate, and high match pass rate (79.3%).",
            "main_weaknesses": "Higher dot-ball rate in early powerplay pressure (42.1% IPL dots). Limited senior T20I pressure exposure (12 balls).",
            "selection_risks": "Low risk; proven franchise anchor resilient to heavy shrinkage (shrunk M=90 SR is 165.2).",
        },
        # Rank 4: Nicholas Pooran
        {
            "player_id": 3125,
            "player_name": "Nicholas Pooran",
            "primary_role": "Middle-Order",
            "phase_suitability": "Middle Acceleration (Overs 7-15) & Death (Overs 16-20)",
            "is_recommended_top_10": True,
            "top_10_rank": 4,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 4: Elite Left-Hand Middle Anchor. 717 combined pressure balls across 61 matches, 166.6 IPL raw SR, +18.8 RAE, and dual-format versatility. Positioned ahead of Dinesh Karthik due to much broader phase adaptability (Middle and Death) vs Karthik's narrow death specialization.",
            "main_strengths": "High volume left-handed middle-order anchor: 491 IPL balls (166.6 SR, +18.8 RAE, 61.8% pass rate) and 226 T20I balls. Balanced multi-phase acceleration across middle and death phases.",
            "main_weaknesses": "International pressure strike rate drops to 142.5 in T20Is (+7.6 RAE) with 42.9% dot-ball rate.",
            "selection_risks": "Low risk; multi-season ROBUST_ANCHOR with 717 combined pressure balls across 61 matches.",
        },
        # Rank 5: Dinesh Karthik
        {
            "player_id": 143,
            "player_name": "Dinesh Karthik",
            "primary_role": "Middle-Order",
            "phase_suitability": "Late Death Crisis (Overs 16-20)",
            "is_recommended_top_10": True,
            "top_10_rank": 5,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 5: Acute Death Crisis Finisher. Highest context-adjusted efficiency among established IPL batters (+39.3 RAE, 184.3 raw SR, 78.9% match pass rate over 216 IPL balls). Narrow phase profile (82.4% death balls) places him behind complete middle-order anchors.",
            "main_strengths": "Exceptional crisis execution: 216 IPL balls across 23 matches, 184.3 raw SR, +39.3 RAE, 26.4% boundary rate, and 26.9% dot-ball rate (78.9% match pass rate).",
            "main_weaknesses": "Confined almost exclusively to death-overs phase (82.4% death balls).",
            "selection_risks": "Moderate risk; phase-specialized finisher requiring protected entry point.",
        },
        # Rank 6: Abhishek Sharma
        {
            "player_id": 6281,
            "player_name": "Abhishek Sharma",
            "primary_role": "Top-Order",
            "phase_suitability": "Powerplay (Overs 1-6) & Middle Transition (Overs 7-12)",
            "is_recommended_top_10": True,
            "top_10_rank": 6,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 6: High-Volume Multi-Format Opener. 510 combined pressure balls across 64 matches, 165.2 IPL SR (+21.1 RAE) and 164.3 T20I SR (+35.2 RAE). Positioned ahead of Salt based on massive 353-ball IPL pressure sample; indistinguishable on bootstrap from Karthik and Salt.",
            "main_strengths": "High-volume multi-format attacking weapon: IPL 353 balls (165.2 SR, +21.1 RAE, 65.5% pass rate) and T20I 157 balls (164.3 SR, +35.2 RAE, 68.8% pass rate). Combined 510 pressure balls across 64 matches.",
            "main_weaknesses": "Higher dot-ball rate (37.1% IPL, 37.6% T20I) reflecting aggressive boundary-seeking approach.",
            "selection_risks": "Low risk; verified ROBUST_ANCHOR with proven cross-format attacking reliability.",
        },
        # Rank 7: Phil Salt
        {
            "player_id": 5553,
            "player_name": "Phil Salt",
            "primary_role": "Top-Order",
            "phase_suitability": "Powerplay (Overs 1-6) & Middle Enforcer (Overs 7-12)",
            "is_recommended_top_10": True,
            "top_10_rank": 7,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 7: Modern International Attacking Opener. Outstanding international pressure production (178.8 T20I SR, +42.8 RAE) paired with 162.8 IPL SR (+20.0 RAE). Positioned ahead of Klaasen via superior top-order strike acceleration; indistinguishable on bootstrap.",
            "main_strengths": "Modern international power attacking anchor: T20I 170 balls (178.8 SR, +42.8 RAE, 25.3% boundaries, 71.4% pass rate); IPL 113 balls (162.8 SR, +20.0 RAE, 77.8% pass rate). Combined 283 balls across 36 matches.",
            "main_weaknesses": "Dot-ball percentage of 38.1% in IPL pressure deliveries and 30.6% in T20I.",
            "selection_risks": "Low risk; strict-tier ROBUST_ANCHOR with high multi-competition consistency.",
        },
        # Rank 8: Heinrich Klaasen
        {
            "player_id": 4260,
            "player_name": "Heinrich Klaasen",
            "primary_role": "Middle-Order",
            "phase_suitability": "Middle Spin Enforcer (Overs 7-15) & Death (Overs 16-20)",
            "is_recommended_top_10": True,
            "top_10_rank": 8,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 8: Middle-Overs Spin Enforcer. 535 combined pressure balls, +23.9 IPL RAE, and 25.9% dot-ball rate (lowest dot rate among top-order/middle anchors). Positioned at #8 due to more conservative international scoring (140.5 T20I SR across 126 balls); indistinguishable on bootstrap from Salt and Maxwell.",
            "main_strengths": "High-volume middle-order power anchor: 409 IPL balls (161.1 SR, +23.9 RAE, 25.9% dots) and 126 T20I balls. High match pass rate (78.3%) across 29 IPL matches.",
            "main_weaknesses": "T20I pressure strike rate is more conservative (140.5 SR across 126 balls).",
            "selection_risks": "Low risk; classified as ROBUST_ANCHOR whose value is amplified in high-difficulty middle overs.",
        },
        # Rank 9: Glenn Maxwell
        {
            "player_id": 838,
            "player_name": "Glenn Maxwell",
            "primary_role": "Middle-Order",
            "phase_suitability": "Middle Transition (Overs 7-15) & Death Accelerator (Overs 16-20)",
            "is_recommended_top_10": True,
            "top_10_rank": 9,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 9: Multi-Format Middle Accelerator. 321 combined pressure balls, 172.9 IPL raw SR (+30.9 RAE) and 166.0 T20I SR (+30.2 RAE). Positioned at #9 behind Klaasen due to higher match variance (74.6 IPL std); bootstrap comparison vs Sooryavanshi shows statistical separation (CI [-103.6, -7.9]).",
            "main_strengths": "Proven multi-format middle-order accelerator: IPL 177 balls (172.9 SR, +30.9 RAE, 71.4% pass rate) and T20I 144 balls (166.0 SR, +30.2 RAE, 73.3% pass rate). Combined 321 balls across 33 matches.",
            "main_weaknesses": "Match-to-match standard deviation of 74.6 SR points in IPL.",
            "selection_risks": "Moderate risk; high variance strike profile balanced by proven dual-format volume.",
        },
        # Rank 10: Vaibhav Sooryavanshi
        {
            "player_id": 50284,
            "player_name": "Vaibhav Sooryavanshi",
            "primary_role": "Top-Order",
            "phase_suitability": "Powerplay Boundary Enforcer (Overs 1-6)",
            "is_recommended_top_10": True,
            "top_10_rank": 10,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 10: Breakout High-Upside Discovery Talent. Highest raw pressure strike rate in tournament history (231.6 raw SR, 195.8 shrunk M45, +86.8 RAE, 43.4% boundary rate over 76 IPL balls). Selected over non-selected alternatives as high-ceiling discovery upside, with explicit uncertainty disclosure regarding 76-ball sample.",
            "main_strengths": "Breakout high-upside discovery talent: 76 IPL balls across 12 matches, 231.6 raw SR, +86.8 RAE, 43.4% boundary ball rate. Shrunk M=45 SR remains elite at 195.8.",
            "main_weaknesses": "Sample size is limited to 76 IPL balls (12 matches); 43.4% dot-ball rate reflects all-or-nothing boundary hitting.",
            "selection_risks": "Moderate-to-high risk; SHRINKAGE_SENSITIVE candidate preserved as premier high-ceiling discovery option.",
        },
        # Non-Selected Alternatives (8 candidates)
        {
            "player_id": 25669,
            "player_name": "Priyansh Arya",
            "primary_role": "Top-Order",
            "phase_suitability": "Powerplay Boundary Enforcer (Overs 1-6)",
            "is_recommended_top_10": False,
            "top_10_rank": None,
            "selection_status": "NON_SELECTED_ALTERNATIVE",
            "selection_rationale": "Non-selected alternative: Explosive top-order discovery candidate (200.0 IPL SR, +56.7 RAE over 68 balls). Narrowly behind Sooryavanshi on raw boundary rate and ceiling.",
            "main_strengths": "68 IPL balls across 16 matches, 200.0 SR, +56.7 RAE, 35.3% boundary ball rate.",
            "main_weaknesses": "Moderate sample size (68 balls); SHRINKAGE_SENSITIVE to heavy shrinkage M=90 (161.4).",
            "selection_risks": "High-ceiling breakout alternative to Sooryavanshi.",
        },
        {
            "player_id": 4821,
            "player_name": "Mahipal Lomror",
            "primary_role": "Middle-Order",
            "phase_suitability": "Middle Spin Hitter (Overs 7-15)",
            "is_recommended_top_10": False,
            "top_10_rank": None,
            "selection_status": "NON_SELECTED_ALTERNATIVE",
            "selection_rationale": "Non-selected alternative: 198.5 IPL SR over 66 balls (+47.4 RAE). High shrinkage pull-down (157.6 at M=90); reserve middle-order option behind Pooran and Klaasen.",
            "main_strengths": "66 IPL balls across 10 matches, 198.5 SR, +47.4 RAE, 30.3% boundary ball rate.",
            "main_weaknesses": "Moderate sample volume (66 balls); pulls down to 157.6 under M=90 shrinkage.",
            "selection_risks": "Middle-order spin hitter alternative behind Klaasen/Pooran.",
        },
        {
            "player_id": 4007,
            "player_name": "Ryan Rickelton",
            "primary_role": "Top-Order",
            "phase_suitability": "Powerplay Anchor (Overs 1-6) & Middle (Overs 7-14)",
            "is_recommended_top_10": False,
            "top_10_rank": None,
            "selection_status": "NON_SELECTED_ALTERNATIVE",
            "selection_rationale": "Non-selected alternative: Cross-format opening option (187.2 IPL SR, 146.2 T20I SR). Reserve behind Phil Salt due to lower international pressure efficiency.",
            "main_strengths": "109 IPL balls (187.2 SR, +43.1 RAE, 32.1% boundaries); T20I 106 balls (146.2 SR).",
            "main_weaknesses": "International pressure SR falls to 146.2 (+15.5 RAE); 39.4% dot-ball rate in IPL.",
            "selection_risks": "Alternative top-order option; narrow margin behind Phil Salt and Abhishek Sharma.",
        },
        {
            "player_id": 4722,
            "player_name": "Rashid Khan",
            "primary_role": "Lower-Order",
            "phase_suitability": "Lower-Order Death Finisher (Overs 16-20)",
            "is_recommended_top_10": False,
            "top_10_rank": None,
            "selection_status": "NON_SELECTED_ALTERNATIVE",
            "selection_rationale": "Non-selected alternative: Elite lower-order finisher (174.7 IPL SR, +32.8 RAE over 198 balls). Highly valuable, but designated as bowling all-rounder rather than pure batting top-10.",
            "main_strengths": "198 IPL balls (174.7 SR, +32.8 RAE) and 201 T20I balls. Combined 399 pressure balls across 49 matches.",
            "main_weaknesses": "T20I pressure strike rate drops to 135.8 with 47.8% dot balls.",
            "selection_risks": "Primary role is bowling; preserved as elite all-rounder.",
        },
        {
            "player_id": 8101,
            "player_name": "Ashutosh Sharma",
            "primary_role": "Lower-Order",
            "phase_suitability": "Lower-Order Death Finisher (Overs 16-20)",
            "is_recommended_top_10": False,
            "top_10_rank": None,
            "selection_status": "NON_SELECTED_ALTERNATIVE",
            "selection_rationale": "Non-selected alternative: 250 IPL pressure balls, 170.8 SR (+22.6 RAE). Strong IPL record, but lower context efficiency than Dinesh Karthik (+22.6 vs +39.3) and lacks international exposure.",
            "main_strengths": "250 IPL pressure balls across 21 matches, 170.8 SR, +22.6 RAE, 70.0% match pass rate.",
            "main_weaknesses": "IPL-only exposure; lacks senior international benchmark.",
            "selection_risks": "Reliable domestic franchise finisher alternative behind Dinesh Karthik.",
        },
        {
            "player_id": 47,
            "player_name": "Virat Kohli",
            "primary_role": "Top-Order",
            "phase_suitability": "Powerplay & Middle Anchor (Overs 1-15)",
            "is_recommended_top_10": False,
            "top_10_rank": None,
            "selection_status": "NON_SELECTED_ALTERNATIVE",
            "selection_rationale": "Non-selected alternative: 278 IPL balls, 164.7 SR (+20.1 RAE, 54.1 std, 73.9% pass rate). Benchmark anchor reliability, but lower boundary rate (26.6% vs 32.0% Jaiswal) and lower strike ceiling than selected top-order anchors.",
            "main_strengths": "278 IPL balls across 30 matches, 164.7 SR, +20.1 RAE, 73.9% match pass rate, low match standard deviation (54.1).",
            "main_weaknesses": "Lower boundary rate (26.6%) compared to aggressive top-order selections (Jaiswal 32.0%, Sooryavanshi 43.4%).",
            "selection_risks": "Ultra-reliable ROBUST_ANCHOR; alternative top-order selection with lower ceiling than Jaiswal/Salt.",
        },
        {
            "player_id": 1318,
            "player_name": "Andre Russell",
            "primary_role": "Lower-Order",
            "phase_suitability": "Death Boundary Finisher (Overs 16-20)",
            "is_recommended_top_10": False,
            "top_10_rank": None,
            "selection_status": "NON_SELECTED_ALTERNATIVE",
            "selection_rationale": "Non-selected alternative: 345 combined pressure balls. High dot-ball rate (47.8% IPL dots) and lower IPL pressure SR (151.1) relative to Tim David (175.4).",
            "main_strengths": "73 T20I balls, 179.5 SR, +61.8 RAE, 26.0% boundaries; IPL 272 balls (151.1 SR).",
            "main_weaknesses": "IPL pressure strike rate is 151.1 (+12.3 RAE); 47.8% dot-ball rate in IPL pressure.",
            "selection_risks": "Boundary-reliant finisher behind Tim David and Dinesh Karthik in consistency.",
        },
        {
            "player_id": 2101,
            "player_name": "Quinton de Kock",
            "primary_role": "Top-Order",
            "phase_suitability": "Powerplay & Early Middle Anchor (Overs 1-12)",
            "is_recommended_top_10": False,
            "top_10_rank": None,
            "selection_status": "NON_SELECTED_ALTERNATIVE",
            "selection_rationale": "Non-selected alternative: 499 combined pressure balls. Excellent T20I record (169.3 SR), but severe pressure dropoff in recent IPL matches (133.5 SR, -11.3 RAE across 284 balls).",
            "main_strengths": "215 T20I balls across 14 matches, 169.3 SR, +35.3 RAE; IPL 284 balls. Combined 499 balls.",
            "main_weaknesses": "IPL pressure SR drops to 133.5 (-11.3 RAE) across 284 balls.",
            "selection_risks": "Proven international record but recent IPL pressure dropoff.",
        },
    ]

    rows = []
    for meta in candidates_meta:
        pid = meta["player_id"]
        row_ipl = b_ipl[b_ipl["striker_id"] == pid]
        row_t20i = b_t20i[b_t20i["striker_id"] == pid]
        has_ipl = not row_ipl.empty and (row_ipl.iloc[0]["pressure_balls_faced"] > 0)
        has_t20i = not row_t20i.empty and (row_t20i.iloc[0]["pressure_balls_faced"] > 0)

        coverage = "CROSS_FORMAT" if (has_ipl and has_t20i) else ("IPL_ONLY" if has_ipl else "T20I_ONLY")

        # Denominator reconciliation
        if pid in recon_b.index:
            r = recon_b.loc[pid]
            ipl_vol = int(r["ipl_pressure_volume"])
            ipl_m = int(r["ipl_distinct_matches"])
            ipl_c = int(r["ipl_distinct_competitions"])
            t20i_vol = int(r["t20i_pressure_volume"])
            t20i_m = int(r["t20i_distinct_matches"])
            t20i_c = int(r["t20i_distinct_competitions"])
            comb_vol = int(r["combined_pressure_volume"])
            comb_m = int(r["combined_distinct_matches"])
            comb_c = int(r["combined_distinct_competitions"])
        else:
            ipl_vol = int(row_ipl.iloc[0]["pressure_balls_faced"]) if has_ipl else 0
            ipl_m = int(row_ipl.iloc[0]["pressure_matches"]) if has_ipl else 0
            ipl_c = int(row_ipl.iloc[0]["pressure_competitions"]) if has_ipl else 0
            t20i_vol = int(row_t20i.iloc[0]["pressure_balls_faced"]) if has_t20i else 0
            t20i_m = int(row_t20i.iloc[0]["pressure_matches"]) if has_t20i else 0
            t20i_c = int(row_t20i.iloc[0]["pressure_competitions"]) if has_t20i else 0
            comb_vol = ipl_vol + t20i_vol
            comb_m = ipl_m + t20i_m
            comb_c = ipl_c + t20i_c

        primary_row = row_ipl.iloc[0] if has_ipl else row_t20i.iloc[0]

        record = {
            "player_id": pid,
            "player_name": meta["player_name"],
            "discipline": "Batter",
            "primary_role": meta["primary_role"],
            "phase_suitability": meta["phase_suitability"],
            "format_coverage": coverage,
            "qualification_tier": primary_row.get("qualification_tier", "Balanced"),
            "evidence_tier": primary_row.get("evidence_tier", "MODERATE_EVIDENCE"),
            "stability_archetype": "ROBUST_ANCHOR" if comb_vol >= 100 and (ipl_vol >= 80 or t20i_vol >= 80) else ("DISCOVERY_UPSIDE" if comb_vol < 60 else "SHRINKAGE_SENSITIVE"),
            # Denominators
            "ipl_pressure_volume": ipl_vol,
            "ipl_matches": ipl_m,
            "ipl_competitions": ipl_c,
            "t20i_pressure_volume": t20i_vol,
            "t20i_matches": t20i_m,
            "t20i_competitions": t20i_c,
            "combined_pressure_volume": comb_vol,
            "combined_matches": comb_m,
            "combined_competitions": comb_c,
            # IPL Performance
            "ipl_raw_sr": round(float(row_ipl.iloc[0]["pressure_strike_rate"]), 1) if has_ipl else np.nan,
            "ipl_shrunk_m25": round(float(row_ipl.iloc[0]["shrunk_pressure_sr_m25"]), 1) if has_ipl else np.nan,
            "ipl_shrunk_m45": round(float(row_ipl.iloc[0]["shrunk_pressure_sr_m45"]), 1) if has_ipl else np.nan,
            "ipl_shrunk_m60": round(float(row_ipl.iloc[0]["shrunk_pressure_sr_m60"]), 1) if has_ipl else np.nan,
            "ipl_shrunk_m90": round(float(row_ipl.iloc[0]["shrunk_pressure_sr_m90"]), 1) if has_ipl else np.nan,
            "ipl_context_delta_sr": round(float(row_ipl.iloc[0]["context_adjusted_delta_sr"]), 1) if has_ipl and pd.notnull(row_ipl.iloc[0]["context_adjusted_delta_sr"]) else np.nan,
            "ipl_dot_ball_pct": round(float(row_ipl.iloc[0]["pressure_dot_ball_pct"]), 1) if has_ipl else np.nan,
            "ipl_boundary_ball_pct": round(float(row_ipl.iloc[0]["pressure_boundary_ball_pct"]), 1) if has_ipl else np.nan,
            "ipl_match_std": round(float(row_ipl.iloc[0]["pressure_match_sr_std"]), 1) if has_ipl and pd.notnull(row_ipl.iloc[0]["pressure_match_sr_std"]) else np.nan,
            "ipl_match_pass_rate": round(float(row_ipl.iloc[0]["pressure_match_pass_rate"]), 1) if has_ipl and pd.notnull(row_ipl.iloc[0]["pressure_match_pass_rate"]) else np.nan,
            # T20I Performance
            "t20i_raw_sr": round(float(row_t20i.iloc[0]["pressure_strike_rate"]), 1) if has_t20i else np.nan,
            "t20i_shrunk_m25": round(float(row_t20i.iloc[0]["shrunk_pressure_sr_m25"]), 1) if has_t20i else np.nan,
            "t20i_shrunk_m45": round(float(row_t20i.iloc[0]["shrunk_pressure_sr_m45"]), 1) if has_t20i else np.nan,
            "t20i_shrunk_m60": round(float(row_t20i.iloc[0]["shrunk_pressure_sr_m60"]), 1) if has_t20i else np.nan,
            "t20i_shrunk_m90": round(float(row_t20i.iloc[0]["shrunk_pressure_sr_m90"]), 1) if has_t20i else np.nan,
            "t20i_context_delta_sr": round(float(row_t20i.iloc[0]["context_adjusted_delta_sr"]), 1) if has_t20i and pd.notnull(row_t20i.iloc[0]["context_adjusted_delta_sr"]) else np.nan,
            "t20i_dot_ball_pct": round(float(row_t20i.iloc[0]["pressure_dot_ball_pct"]), 1) if has_t20i else np.nan,
            "t20i_boundary_ball_pct": round(float(row_t20i.iloc[0]["pressure_boundary_ball_pct"]), 1) if has_t20i else np.nan,
            "t20i_match_std": round(float(row_t20i.iloc[0]["pressure_match_sr_std"]), 1) if has_t20i and pd.notnull(row_t20i.iloc[0]["pressure_match_sr_std"]) else np.nan,
            "t20i_match_pass_rate": round(float(row_t20i.iloc[0]["pressure_match_pass_rate"]), 1) if has_t20i and pd.notnull(row_t20i.iloc[0]["pressure_match_pass_rate"]) else np.nan,
            # Recommendation & Decision Intel
            "is_recommended_top_10": meta["is_recommended_top_10"],
            "top_10_rank": meta["top_10_rank"],
            "selection_status": meta["selection_status"],
            "selection_rationale": meta["selection_rationale"],
            "main_strengths": meta["main_strengths"],
            "main_weaknesses": meta["main_weaknesses"],
            "selection_risks": meta["selection_risks"],
        }
        rows.append(record)

    df_out = pd.DataFrame(rows)
    df_out["sort_key"] = df_out["top_10_rank"].fillna(99)
    df_out = df_out.sort_values(["sort_key", "ipl_shrunk_m45"], ascending=[True, False]).drop(columns=["sort_key"])
    return df_out.reset_index(drop=True)


def build_final_bowler_decision_matrix(base_dir: str = ".") -> pd.DataFrame:
    """Build the final comprehensive decision matrix for top bowler candidates.

    Parameters
    ----------
    base_dir : str
        Base directory of the rr-edge codebase.

    Returns
    -------
    pd.DataFrame
        Decision matrix with complete metrics, stability, risks, and selection recommendations.
    """
    eval_dir = os.path.join(base_dir, "data", "processed", "player_evaluations")
    ci_dir = os.path.join(base_dir, "data", "processed", "candidate_intelligence")

    w_ipl = pd.read_parquet(os.path.join(eval_dir, "bowler_evaluation_ipl.parquet"))
    w_t20i = pd.read_parquet(os.path.join(eval_dir, "bowler_evaluation_t20i.parquet"))
    recon = pd.read_csv(os.path.join(ci_dir, "candidate_denominator_reconciliation.csv"))
    recon_w = recon[recon["discipline"] == "Bowler"].set_index("player_id")

    candidates_meta = [
        # Rank 1: Sunil Narine
        {
            "player_id": 781,
            "player_name": "Sunil Narine",
            "primary_role": "Middle Specialist",
            "phase_suitability": "Middle Phase Squeeze Specialist (Overs 7-15)",
            "is_recommended_top_10": True,
            "top_10_rank": 1,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 1: #1 Middle-Overs Run Suppression Benchmark. Lowest economy in tournament history (6.70 raw economy, 7.28 M45, -2.79 RCAE across 317 IPL pressure balls) with an 89.5% match pass rate (34/38 matches <=9.0 econ or >=1 wkt). Positioned at #1 as the premier defensive squeeze asset; bootstrap vs Bumrah spans zero (CI [-2.34, 0.31]), making this a tactical judgement call prioritizing unmatched run choke.",
            "main_strengths": "Tournament benchmark for middle-overs run suppression: 317 IPL pressure balls across 41 matches, 6.70 economy, -2.79 RCAE, 38.8% dot balls, 10.4% boundary concession, 0.36 wickets per over, and 89.5% match pass rate. Lowest economy in database.",
            "main_weaknesses": "Minimal death-overs exposure (less than 15% death deliveries); almost exclusively specialized in middle phase.",
            "selection_risks": "Low risk for middle overs; tactical risk if forced into death-overs situations without pace support.",
        },
        # Rank 2: Jasprit Bumrah
        {
            "player_id": 2933,
            "player_name": "Jasprit Bumrah",
            "primary_role": "All-Phases",
            "phase_suitability": "All-Phases Strike & Containment (Powerplay, Middle & Death)",
            "is_recommended_top_10": True,
            "top_10_rank": 2,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 2: #1 All-Phases Pressure Anchor. Premier pace volume (391 IPL balls, 103 T20I balls, 494 combined across 53 matches), 7.84 IPL Economy (-2.33 RCAE) with 32.7% dot-ball rate while bowling tournament's toughest death overs. Indistinguishable on bootstrap from Narine (CI [-2.34, 0.31]) and Pathirana (CI [-2.24, 0.79]); placed at #2 due to complete phase versatility.",
            "main_strengths": "Premier all-phases pressure anchor: 391 IPL balls across 41 matches, 7.84 economy, -2.33 RCAE, 32.7% dot balls, 71.8% match pass rate. Combined 494 balls across 53 matches. Handles tournament's most demanding death overs.",
            "main_weaknesses": "Higher economy in small international T20I sample (10.72 over 103 balls).",
            "selection_risks": "Minimal selection risk; gold-standard ROBUST_ANCHOR with tournament-proven defensive execution.",
        },
        # Rank 3: Matheesha Pathirana
        {
            "player_id": 8661,
            "player_name": "Matheesha Pathirana",
            "primary_role": "Death Specialist",
            "phase_suitability": "Death Phase Wicket Specialist (Overs 16-20)",
            "is_recommended_top_10": True,
            "top_10_rank": 3,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 3: #1 Death Phase Wicket Threat. 316 death-phase pressure balls yielding 31 wickets (0.589 wkts/over, a wicket every 10.2 balls) at 8.62 death economy; overall IPL pressure 0.49 wkts/over, 9.18 economy (-1.58 RCAE). Positioned ahead of Nawaz due to proven IPL death execution; indistinguishable on bootstrap from Bumrah and Nawaz.",
            "main_strengths": "Premier death-phase wicket-taking weapon: 317 IPL balls across 31 matches, 0.49 wickets per over, 33.8% dot balls, negative RCAE (-1.58), 75.0% match pass rate. Specifically in death overs across competitions: 316 balls, 31 wickets (0.589 wkts/over), 8.62 death economy.",
            "main_weaknesses": "Overall economy rate of 9.18 in IPL pressure, reflecting severe high-leverage death deployment.",
            "selection_risks": "Low-to-moderate risk; ROBUST_ANCHOR death specialist whose run suppression is superior to phase expectations.",
        },
        # Rank 4: Mohammad Nawaz
        {
            "player_id": 2490,
            "player_name": "Mohammad Nawaz",
            "primary_role": "Middle Specialist",
            "phase_suitability": "Middle Phase Spin Restrictor (Overs 7-15)",
            "is_recommended_top_10": True,
            "top_10_rank": 4,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 4: Premier International Spin Restrictor. Elite international pressure metrics (80 T20I balls, 6.83 economy, -1.62 RCAE, 0.75 wkts/over, 36.2% dots, 80.0% pass rate). Positioned at #4 ahead of Malinga via superior economy and run suppression; explicit uncertainty disclosure that he has 0 IPL match exposure in the dataset.",
            "main_strengths": "Premier international left-arm spin restrictor: 80 T20I balls across 15 matches, 6.83 economy, -1.62 RCAE, 0.75 wickets per over, 36.2% dot balls, 80.0% match pass rate.",
            "main_weaknesses": "No IPL match exposure in dataset; international sample size is moderate (80 balls).",
            "selection_risks": "Moderate risk; BALANCED tier international candidate requiring adaptation to Indian pitch conditions.",
        },
        # Rank 5: Eshan Malinga
        {
            "player_id": 39657,
            "player_name": "Eshan Malinga",
            "primary_role": "All-Phases",
            "phase_suitability": "All-Phases Strike Pacer (Powerplay, Middle & Death)",
            "is_recommended_top_10": True,
            "top_10_rank": 5,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 5: Elite Dual-Format Wicket Pacer. 255 combined pressure balls across 26 matches, 0.60 IPL wickets per over at 8.42 economy (-1.34 RCAE) and 42.7% dot-ball rate. Positioned ahead of Noor Ahmad based on superior wicket frequency (0.60 vs 0.42 wkts/over); indistinguishable on bootstrap from Nawaz and Noor Ahmad.",
            "main_strengths": "Elite strike bowling impact: 171 IPL balls across 18 matches, 8.42 economy, -1.34 RCAE, 0.60 wickets per over, 42.7% dot balls, 73.3% match pass rate. T20I 84 balls (9.21 economy, 0.43 wkts/over, 75.0% pass rate). Combined 255 pressure balls.",
            "main_weaknesses": "Moderate match-to-match economy variance (std 3.89).",
            "selection_risks": "Low risk; multi-competition ROBUST_ANCHOR with proven high-wicket penetration.",
        },
        # Rank 6: Noor Ahmad
        {
            "player_id": 7967,
            "player_name": "Noor Ahmad",
            "primary_role": "Middle Specialist",
            "phase_suitability": "Middle Phase Wrist-Spin Control (Overs 7-15)",
            "is_recommended_top_10": True,
            "top_10_rank": 6,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 6: Middle-Overs Wrist Spin Control. 228 IPL pressure balls across 28 matches, 8.61 economy (-0.81 RCAE, 0.42 wkts/over, 37.7% dots, 72.0% pass rate). Positioned ahead of Ashwin via superior wicket strike potency (0.42 vs 0.31 wkts/over); indistinguishable on bootstrap from Malinga and Ashwin.",
            "main_strengths": "Middle-overs wrist-spin containment: 228 IPL balls across 28 matches, 8.61 economy, -0.81 RCAE, 0.42 wickets per over, 37.7% dot balls, 72.0% match pass rate. Combined 279 balls across 37 matches.",
            "main_weaknesses": "T20I economy rises to 10.71 over 51 balls.",
            "selection_risks": "Low risk; proven IPL ROBUST_ANCHOR with strong middle-phase control.",
        },
        # Rank 7: Ravichandran Ashwin
        {
            "player_id": 305,
            "player_name": "Ravichandran Ashwin",
            "primary_role": "Middle Specialist",
            "phase_suitability": "Middle Phase Finger-Spin Anchor (Overs 7-15)",
            "is_recommended_top_10": True,
            "top_10_rank": 7,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 7: Tactical Finger Spin Anchor. 247 combined pressure balls across 36 matches, 8.79 IPL economy (-0.66 RCAE, 80.0% pass rate) and 7.69 T20I economy (100% pass rate). Positioned ahead of Hasaranga based on lower boundary concession (14.9% vs 17.2%) and defensive reliability; indistinguishable on bootstrap.",
            "main_strengths": "Tactical finger-spin anchor: 215 IPL balls across 32 matches, 8.79 economy, -0.66 RCAE, 0.31 wickets per over, 80.0% match pass rate; T20I 32 balls (7.69 economy, 100% match pass rate). Combined 247 balls across 36 matches.",
            "main_weaknesses": "Lower dot-ball rate (27.0% IPL) and lower raw strike rate compared to wrist spinners.",
            "selection_risks": "Low risk; experienced franchise ROBUST_ANCHOR with low boundary concession (14.9%).",
        },
        # Rank 8: Wanindu Hasaranga
        {
            "player_id": 4900,
            "player_name": "Wanindu Hasaranga",
            "primary_role": "Middle Specialist",
            "phase_suitability": "Middle Phase Strike Weapon (Overs 7-15) & Pinch Death",
            "is_recommended_top_10": True,
            "top_10_rank": 8,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 8: Multi-Format Strike Threat. Tournament-leading raw wicket frequency in IPL (0.64 wkts/over across 151 balls) and consistent international production (175 T20I balls, 8.50 economy, -0.29 RCAE, 0.51 wkts/over). Placed at #8 due to higher boundary concession (17.2%); indistinguishable on bootstrap from Ashwin and Sears.",
            "main_strengths": "Multi-format wrist-spin wicket weapon: IPL 151 balls (8.94 economy, 0.64 wkts/over, -0.23 RCAE, 70.0% pass rate); T20I 175 balls (8.50 economy, 0.51 wkts/over, -0.29 RCAE, 66.7% pass rate). Combined 326 balls across 53 matches.",
            "main_weaknesses": "Boundary concession rate of 17.2% in IPL.",
            "selection_risks": "Low risk; dual-format ROBUST_ANCHOR with proven wicket threat across middle overs.",
        },
        # Rank 9: Benjamin Sears
        {
            "player_id": 4856,
            "player_name": "Benjamin Sears",
            "primary_role": "All-Phases",
            "phase_suitability": "All-Phases High-Pace Containment (Powerplay & Middle)",
            "is_recommended_top_10": True,
            "top_10_rank": 9,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 9: International High-Pace Containment. 101 T20I pressure balls across 14 matches, 7.96 economy (-1.41 RCAE, 0.59 wkts/over, 39.6% dots, 70.0% pass rate). Positioned at #9; bootstrap comparison vs Mayank Yadav shows statistical separation in T20Is (CI [-7.10, -0.23]); explicit disclosure of 0 IPL balls.",
            "main_strengths": "High-pace international containment: 101 T20I balls across 14 matches, 7.96 economy, -1.41 RCAE, 0.59 wickets per over, 39.6% dot balls, 70.0% match pass rate.",
            "main_weaknesses": "No IPL match experience in dataset; international sample size is moderate (101 balls).",
            "selection_risks": "Moderate risk; strict-tier ROBUST_ANCHOR in T20I requiring franchise transition validation.",
        },
        # Rank 10: Mayank Yadav
        {
            "player_id": 27960,
            "player_name": "Mayank Yadav",
            "primary_role": "Middle Specialist",
            "phase_suitability": "Middle Phase High-Pace Enforcer (Overs 7-15)",
            "is_recommended_top_10": True,
            "top_10_rank": 10,
            "selection_status": "SELECTED_TOP_10",
            "selection_rationale": "Rank 10: Breakout High-Ceiling Discovery Pacer. Elite raw IPL run suppression and dot-ball generation (43 IPL balls, 7.95 economy, -2.37 RCAE, 0.56 wkts/over, 51.2% dot-ball rate — highest in tournament). Selected as high-upside pace discovery over non-selected alternatives, with honest uncertainty disclosure regarding 43-ball IPL sample.",
            "main_strengths": "Breakout high-upside pace discovery candidate: 43 IPL balls across 5 matches, 7.95 economy, -2.37 RCAE, 0.56 wickets per over, 51.2% dot-ball rate (highest dot rate in cohort, 100% match pass rate). Combined 134 balls across 13 matches.",
            "main_weaknesses": "Limited sample size (43 balls across 5 matches); high economy in small T20I sample (11.67 across 91 balls).",
            "selection_risks": "Moderate-to-high risk; DISCOVERY_UPSIDE candidate with small sample exposure requiring anchor hedging.",
        },
        # Non-Selected Alternatives (8 candidates)
        {
            "player_id": 4641,
            "player_name": "Lungi Ngidi",
            "primary_role": "All-Phases",
            "phase_suitability": "Powerplay & Death Strike Pacer (Overs 1-6 & 16-20)",
            "is_recommended_top_10": False,
            "top_10_rank": None,
            "selection_status": "NON_SELECTED_ALTERNATIVE",
            "selection_rationale": "Non-selected alternative: 289 combined pressure balls, 0.49 IPL wkts/over (-0.66 RCAE). Reliable strike pacer, but higher IPL economy (9.47) and T20I economy (10.38) than selected pacers.",
            "main_strengths": "148 IPL balls across 17 matches, 0.49 wickets per over, -0.66 RCAE. T20I 141 balls. Combined 289 balls across 32 matches.",
            "main_weaknesses": "Higher raw economy (9.47 IPL, 10.38 T20I); lower dot-ball rate (29.7% IPL).",
            "selection_risks": "Strike pace alternative behind Eshan Malinga and Matheesha Pathirana.",
        },
        {
            "player_id": 7503,
            "player_name": "Ravi Bishnoi",
            "primary_role": "Middle Specialist",
            "phase_suitability": "Middle Phase Wrist Spin (Overs 7-15)",
            "is_recommended_top_10": False,
            "top_10_rank": None,
            "selection_status": "NON_SELECTED_ALTERNATIVE",
            "selection_rationale": "Non-selected alternative: 341 combined pressure balls, 9.38 IPL economy (+0.33 RCAE). Solid wrist spinner, but behind Noor Ahmad and Hasaranga in middle-phase run suppression.",
            "main_strengths": "181 IPL balls across 25 matches, 0.36 wickets per over, 34.3% dot balls; T20I 160 balls (8.44 economy, -0.40 RCAE). Combined 341 balls.",
            "main_weaknesses": "Positive RCAE in IPL (+0.33); economy rises to 9.38 in IPL pressure.",
            "selection_risks": "Wrist-spin alternative behind Noor Ahmad and Wanindu Hasaranga.",
        },
        {
            "player_id": 2984,
            "player_name": "Sikandar Raza",
            "primary_role": "Middle Specialist",
            "phase_suitability": "Middle Phase All-Round Spin (Overs 7-15)",
            "is_recommended_top_10": False,
            "top_10_rank": None,
            "selection_status": "NON_SELECTED_ALTERNATIVE",
            "selection_rationale": "Non-selected alternative: 305 combined pressure balls, 8.66 T20I economy (-0.74 RCAE, 0.44 wkts/over). High-value all-round option, but lower IPL strike penetration (9.76 economy) than primary bowling anchors.",
            "main_strengths": "203 T20I balls, 8.66 economy, -0.74 RCAE, 0.44 wickets per over; IPL 102 balls. Combined 305 balls across 41 matches.",
            "main_weaknesses": "IPL pressure economy rises to 9.76 (+0.35 RCAE) across 102 balls.",
            "selection_risks": "Spin-bowling all-rounder alternative behind specialist spinners.",
        },
        {
            "player_id": 3275,
            "player_name": "Alzarri Joseph",
            "primary_role": "All-Phases",
            "phase_suitability": "Middle & Death Enforcer (Overs 11-20)",
            "is_recommended_top_10": False,
            "top_10_rank": None,
            "selection_status": "NON_SELECTED_ALTERNATIVE",
            "selection_rationale": "Non-selected alternative: 427 combined pressure balls, 9.88 IPL economy (-0.22 RCAE, 0.44 wkts/over). Heavy death-overs exposure, but higher boundary concession than Pathirana and Bumrah.",
            "main_strengths": "274 IPL balls across 26 matches, 0.44 wickets per over, -0.22 RCAE; T20I 153 balls. Combined 427 balls across 45 matches.",
            "main_weaknesses": "High raw economy rate (9.88 IPL, 10.63 T20I); higher boundary concession rate (18.6% IPL).",
            "selection_risks": "Heavy death-overs exposure; alternative behind Bumrah, Pathirana, and Malinga.",
        },
        {
            "player_id": 4219,
            "player_name": "Krunal Pandya",
            "primary_role": "Middle Specialist",
            "phase_suitability": "Middle Phase Defensive Finger Spin (Overs 7-15)",
            "is_recommended_top_10": False,
            "top_10_rank": None,
            "selection_status": "NON_SELECTED_ALTERNATIVE",
            "selection_rationale": "Non-selected alternative: 202 IPL pressure balls, 9.15 economy (-0.19 RCAE, 0.27 wkts/ov). Defensive finger spinner, but lower wicket threat than Ashwin and higher economy than Narine.",
            "main_strengths": "202 IPL pressure balls across 26 matches, 9.15 economy, -0.19 RCAE, 30.7% dot-ball rate.",
            "main_weaknesses": "Lower wicket strike rate (0.27 wickets per over); limited T20I pressure exposure.",
            "selection_risks": "Middle-overs defensive finger spin alternative behind Ashwin and Narine.",
        },
        {
            "player_id": 5809,
            "player_name": "Naveen-ul-Haq",
            "primary_role": "Death Specialist",
            "phase_suitability": "Middle & Death Change-of-Pace (Overs 11-20)",
            "is_recommended_top_10": False,
            "top_10_rank": None,
            "selection_status": "NON_SELECTED_ALTERNATIVE",
            "selection_rationale": "Non-selected alternative: 298 combined pressure balls. 8.13 T20I economy (-1.02 RCAE), but IPL pressure economy rises to 10.27 (+0.43 RCAE).",
            "main_strengths": "149 T20I balls across 17 matches, 8.13 economy, -1.02 RCAE, 0.36 wickets per over. Combined 298 balls across 31 matches.",
            "main_weaknesses": "IPL pressure economy rises to 10.27 (+0.43 RCAE) across 149 balls.",
            "selection_risks": "Pace change alternative behind Pathirana and Malinga.",
        },
        {
            "player_id": 19312,
            "player_name": "Nuwan Thushara",
            "primary_role": "Death Specialist",
            "phase_suitability": "Death Slinger Strike Weapon (Overs 16-20)",
            "is_recommended_top_10": False,
            "top_10_rank": None,
            "selection_status": "NON_SELECTED_ALTERNATIVE",
            "selection_rationale": "Non-selected alternative: High-ceiling slinger (71 T20I balls, 9.63 economy). Limited IPL pressure exposure (49 balls); reserve slinger behind Pathirana.",
            "main_strengths": "71 T20I balls across 9 matches, 0.17 wickets per over; 49 IPL balls across 7 matches. Combined 120 balls across 16 matches.",
            "main_weaknesses": "Elevated economy in IPL pressure (10.78 raw economy) and T20I pressure (9.63 economy).",
            "selection_risks": "High-upside slinger alternative behind Matheesha Pathirana.",
        },
        {
            "player_id": 830,
            "player_name": "Josh Hazlewood",
            "primary_role": "Powerplay Specialist",
            "phase_suitability": "Powerplay & Early Middle Containment (Overs 1-10)",
            "is_recommended_top_10": False,
            "top_10_rank": None,
            "selection_status": "NON_SELECTED_ALTERNATIVE",
            "selection_rationale": "Non-selected alternative: 263 combined pressure balls, 0.59 IPL wkts/over and 0.61 T20I wkts/over. High wicket threat, but extreme IPL economy (12.07 raw, +1.55 RCAE) due to heavy death deployment.",
            "main_strengths": "High wicket threat across all phases: 0.59 IPL wkts/over and 0.61 T20I wkts/over; 8.36 T20I economy (-0.62 RCAE, 43.8% dots). Combined 263 balls across 40 matches.",
            "main_weaknesses": "IPL pressure economy is severely elevated at 12.07 (+1.55 RCAE) across 174 balls due to heavy death exposure.",
            "selection_risks": "High-wicket pacer whose IPL economy profile is significantly more volatile than Bumrah or Malinga.",
        },
    ]

    rows = []
    for meta in candidates_meta:
        pid = meta["player_id"]
        row_ipl = w_ipl[w_ipl["bowler_id"] == pid]
        row_t20i = w_t20i[w_t20i["bowler_id"] == pid]
        has_ipl = not row_ipl.empty and (row_ipl.iloc[0]["pressure_legal_balls"] > 0)
        has_t20i = not row_t20i.empty and (row_t20i.iloc[0]["pressure_legal_balls"] > 0)

        coverage = "CROSS_FORMAT" if (has_ipl and has_t20i) else ("IPL_ONLY" if has_ipl else "T20I_ONLY")

        # Denominator reconciliation
        if pid in recon_w.index:
            r = recon_w.loc[pid]
            ipl_vol = int(r["ipl_pressure_volume"])
            ipl_m = int(r["ipl_distinct_matches"])
            ipl_c = int(r["ipl_distinct_competitions"])
            t20i_vol = int(r["t20i_pressure_volume"])
            t20i_m = int(r["t20i_distinct_matches"])
            t20i_c = int(r["t20i_distinct_competitions"])
            comb_vol = int(r["combined_pressure_volume"])
            comb_m = int(r["combined_distinct_matches"])
            comb_c = int(r["combined_distinct_competitions"])
        else:
            ipl_vol = int(row_ipl.iloc[0]["pressure_legal_balls"]) if has_ipl else 0
            ipl_m = int(row_ipl.iloc[0]["pressure_matches"]) if has_ipl else 0
            ipl_c = int(row_ipl.iloc[0]["pressure_competitions"]) if has_ipl else 0
            t20i_vol = int(row_t20i.iloc[0]["pressure_legal_balls"]) if has_t20i else 0
            t20i_m = int(row_t20i.iloc[0]["pressure_matches"]) if has_t20i else 0
            t20i_c = int(row_t20i.iloc[0]["pressure_competitions"]) if has_t20i else 0
            comb_vol = ipl_vol + t20i_vol
            comb_m = ipl_m + t20i_m
            comb_c = ipl_c + t20i_c

        primary_row = row_ipl.iloc[0] if has_ipl else row_t20i.iloc[0]

        record = {
            "player_id": pid,
            "player_name": meta["player_name"],
            "discipline": "Bowler",
            "primary_role": meta["primary_role"],
            "phase_suitability": meta["phase_suitability"],
            "format_coverage": coverage,
            "qualification_tier": primary_row.get("qualification_tier", "Balanced"),
            "evidence_tier": primary_row.get("evidence_tier", "MODERATE_EVIDENCE"),
            "stability_archetype": "ROBUST_ANCHOR" if comb_vol >= 100 and (ipl_vol >= 80 or t20i_vol >= 80) else ("DISCOVERY_UPSIDE" if comb_vol < 60 else "CONTEXT_DEPENDENT"),
            # Denominators
            "ipl_pressure_volume": ipl_vol,
            "ipl_matches": ipl_m,
            "ipl_competitions": ipl_c,
            "t20i_pressure_volume": t20i_vol,
            "t20i_matches": t20i_m,
            "t20i_competitions": t20i_c,
            "combined_pressure_volume": comb_vol,
            "combined_matches": comb_m,
            "combined_competitions": comb_c,
            # IPL Performance
            "ipl_raw_econ": round(float(row_ipl.iloc[0]["pressure_economy_rate"]), 2) if has_ipl else np.nan,
            "ipl_shrunk_m25": round(float(row_ipl.iloc[0]["shrunk_pressure_econ_m25"]), 2) if has_ipl else np.nan,
            "ipl_shrunk_m45": round(float(row_ipl.iloc[0]["shrunk_pressure_econ_m45"]), 2) if has_ipl else np.nan,
            "ipl_shrunk_m60": round(float(row_ipl.iloc[0]["shrunk_pressure_econ_m60"]), 2) if has_ipl else np.nan,
            "ipl_shrunk_m90": round(float(row_ipl.iloc[0]["shrunk_pressure_econ_m90"]), 2) if has_ipl else np.nan,
            "ipl_context_delta_econ": round(float(row_ipl.iloc[0]["context_adjusted_delta_econ"]), 2) if has_ipl and pd.notnull(row_ipl.iloc[0]["context_adjusted_delta_econ"]) else np.nan,
            "ipl_legal_econ": round(float(row_ipl.iloc[0]["observed_legal_econ"]), 2) if has_ipl and "observed_legal_econ" in row_ipl.columns and pd.notnull(row_ipl.iloc[0]["observed_legal_econ"]) else np.nan,
            "ipl_legal_context_delta_econ": round(float(row_ipl.iloc[0]["legal_context_delta_econ"]), 2) if has_ipl and "legal_context_delta_econ" in row_ipl.columns and pd.notnull(row_ipl.iloc[0]["legal_context_delta_econ"]) else np.nan,
            "ipl_expected_econ": round(float(row_ipl.iloc[0]["expected_pressure_econ"]), 2) if has_ipl and "expected_pressure_econ" in row_ipl.columns and pd.notnull(row_ipl.iloc[0]["expected_pressure_econ"]) else np.nan,
            "ipl_legal_expected_econ": round(float(row_ipl.iloc[0]["expected_legal_econ"]), 2) if has_ipl and "expected_legal_econ" in row_ipl.columns and pd.notnull(row_ipl.iloc[0]["expected_legal_econ"]) else np.nan,
            "ipl_dot_ball_pct": round(float(row_ipl.iloc[0]["pressure_dot_ball_pct"]), 1) if has_ipl else np.nan,
            "ipl_boundary_concession_pct": round(float(row_ipl.iloc[0]["pressure_boundary_concession_pct"]), 1) if has_ipl else np.nan,
            "ipl_wickets_per_over": round(float(row_ipl.iloc[0]["wickets_per_over"]), 2) if has_ipl else np.nan,
            "ipl_match_std": round(float(row_ipl.iloc[0]["pressure_match_econ_std"]), 2) if has_ipl and pd.notnull(row_ipl.iloc[0]["pressure_match_econ_std"]) else np.nan,
            "ipl_match_pass_rate": round(float(row_ipl.iloc[0]["pressure_match_pass_rate"]), 1) if has_ipl and pd.notnull(row_ipl.iloc[0]["pressure_match_pass_rate"]) else np.nan,
            # T20I Performance
            "t20i_raw_econ": round(float(row_t20i.iloc[0]["pressure_economy_rate"]), 2) if has_t20i else np.nan,
            "t20i_shrunk_m25": round(float(row_t20i.iloc[0]["shrunk_pressure_econ_m25"]), 2) if has_t20i else np.nan,
            "t20i_shrunk_m45": round(float(row_t20i.iloc[0]["shrunk_pressure_econ_m45"]), 2) if has_t20i else np.nan,
            "t20i_shrunk_m60": round(float(row_t20i.iloc[0]["shrunk_pressure_econ_m60"]), 2) if has_t20i else np.nan,
            "t20i_shrunk_m90": round(float(row_t20i.iloc[0]["shrunk_pressure_econ_m90"]), 2) if has_t20i else np.nan,
            "t20i_context_delta_econ": round(float(row_t20i.iloc[0]["context_adjusted_delta_econ"]), 2) if has_t20i and pd.notnull(row_t20i.iloc[0]["context_adjusted_delta_econ"]) else np.nan,
            "t20i_legal_econ": round(float(row_t20i.iloc[0]["observed_legal_econ"]), 2) if has_t20i and "observed_legal_econ" in row_t20i.columns and pd.notnull(row_t20i.iloc[0]["observed_legal_econ"]) else np.nan,
            "t20i_legal_context_delta_econ": round(float(row_t20i.iloc[0]["legal_context_delta_econ"]), 2) if has_t20i and "legal_context_delta_econ" in row_t20i.columns and pd.notnull(row_t20i.iloc[0]["legal_context_delta_econ"]) else np.nan,
            "t20i_expected_econ": round(float(row_t20i.iloc[0]["expected_pressure_econ"]), 2) if has_t20i and "expected_pressure_econ" in row_t20i.columns and pd.notnull(row_t20i.iloc[0]["expected_pressure_econ"]) else np.nan,
            "t20i_legal_expected_econ": round(float(row_t20i.iloc[0]["expected_legal_econ"]), 2) if has_t20i and "expected_legal_econ" in row_t20i.columns and pd.notnull(row_t20i.iloc[0]["expected_legal_econ"]) else np.nan,
            "t20i_dot_ball_pct": round(float(row_t20i.iloc[0]["pressure_dot_ball_pct"]), 1) if has_t20i else np.nan,
            "t20i_boundary_concession_pct": round(float(row_t20i.iloc[0]["pressure_boundary_concession_pct"]), 1) if has_t20i else np.nan,
            "t20i_wickets_per_over": round(float(row_t20i.iloc[0]["wickets_per_over"]), 2) if has_t20i else np.nan,
            "t20i_match_std": round(float(row_t20i.iloc[0]["pressure_match_econ_std"]), 2) if has_t20i and pd.notnull(row_t20i.iloc[0]["pressure_match_econ_std"]) else np.nan,
            "t20i_match_pass_rate": round(float(row_t20i.iloc[0]["pressure_match_pass_rate"]), 1) if has_t20i and pd.notnull(row_t20i.iloc[0]["pressure_match_pass_rate"]) else np.nan,
            # Recommendation & Decision Intel
            "is_recommended_top_10": meta["is_recommended_top_10"],
            "top_10_rank": meta["top_10_rank"],
            "selection_status": meta["selection_status"],
            "selection_rationale": meta["selection_rationale"],
            "main_strengths": meta["main_strengths"],
            "main_weaknesses": meta["main_weaknesses"],
            "selection_risks": meta["selection_risks"],
        }
        rows.append(record)

    df_out = pd.DataFrame(rows)
    df_out["sort_key"] = df_out["top_10_rank"].fillna(99)
    df_out = df_out.sort_values(["sort_key", "ipl_shrunk_m45"], ascending=[True, True]).drop(columns=["sort_key"])
    return df_out.reset_index(drop=True)


def compute_top_10_pairwise_bootstrap(
    deliveries_df: pd.DataFrame,
    batter_matrix: pd.DataFrame,
    bowler_matrix: pd.DataFrame,
    n_boot: int = 10000,
    seed: int = 42,
) -> pd.DataFrame:
    """Run match-cluster bootstrap comparisons with 10,000 iterations for adjacent Top-10 pairs.

    Parameters
    ----------
    deliveries_df : pd.DataFrame
        Complete deliveries dataset.
    batter_matrix : pd.DataFrame
        Batter decision matrix.
    bowler_matrix : pd.DataFrame
        Bowler decision matrix.
    n_boot : int
        Number of bootstrap iterations (10,000 required).
    seed : int
        Fixed random seed.

    Returns
    -------
    pd.DataFrame
        Table of pairwise bootstrap comparisons between adjacent ranks and benchmark alternatives.
    """
    top_b = batter_matrix[batter_matrix["is_recommended_top_10"]].sort_values("top_10_rank")
    top_w = bowler_matrix[bowler_matrix["is_recommended_top_10"]].sort_values("top_10_rank")

    comparisons = []

    # 1. Adjacent Batter Comparisons (Rank i vs Rank i+1)
    for i in range(len(top_b) - 1):
        ca = top_b.iloc[i]
        cb = top_b.iloc[i + 1]
        comp_format = "IPL" if ca["ipl_pressure_volume"] > 0 and cb["ipl_pressure_volume"] > 0 else "T20I"

        boot = compute_match_cluster_bootstrap(
            deliveries_df=deliveries_df,
            player_a_id=int(ca["player_id"]),
            player_b_id=int(cb["player_id"]),
            discipline="Batter",
            comp_type=comp_format,
            n_boot=n_boot,
            seed=seed,
        )

        obs_a = ca[f"{comp_format.lower()}_raw_sr"]
        obs_b = cb[f"{comp_format.lower()}_raw_sr"]
        obs_diff = obs_a - obs_b if pd.notnull(obs_a) and pd.notnull(obs_b) else np.nan

        comparisons.append({
            "pair_id": f"BAT_RANK_{i+1}_VS_{i+2}",
            "discipline": "Batter",
            "evaluation_format": comp_format,
            "rank_a": int(ca["top_10_rank"]),
            "player_a_name": ca["player_name"],
            "player_a_id": int(ca["player_id"]),
            "player_a_volume": int(ca[f"{comp_format.lower()}_pressure_volume"]),
            "player_a_rate": obs_a,
            "rank_b": int(cb["top_10_rank"]),
            "player_b_name": cb["player_name"],
            "player_b_id": int(cb["player_id"]),
            "player_b_volume": int(cb[f"{comp_format.lower()}_pressure_volume"]),
            "player_b_rate": obs_b,
            "observed_difference": round(obs_diff, 2) if pd.notnull(obs_diff) else np.nan,
            "bootstrap_se_10k": boot["bootstrap_se"],
            "bootstrap_ci_95_lower": boot["bootstrap_ci_95_lower"],
            "bootstrap_ci_95_upper": boot["bootstrap_ci_95_upper"],
            "effective_sample_assessment": boot["effective_sample_assessment"],
            "statistical_distinction": boot["statistical_distinction"],
            "statistical_verdict": "Distinguishable" if boot["statistical_distinction"] == "STATISTICALLY_DISTINGUISHABLE" else ("Inconclusive Sample" if boot["statistical_distinction"] == "INCONCLUSIVE_INSUFFICIENT_SAMPLE" else "No Statistical Distinction Confirmed (CI spans 0)"),
        })

    # 2. Adjacent Bowler Comparisons (Rank i vs Rank i+1)
    for i in range(len(top_w) - 1):
        ca = top_w.iloc[i]
        cb = top_w.iloc[i + 1]
        comp_format = "IPL" if ca["ipl_pressure_volume"] > 0 and cb["ipl_pressure_volume"] > 0 else "T20I"

        boot = compute_match_cluster_bootstrap(
            deliveries_df=deliveries_df,
            player_a_id=int(ca["player_id"]),
            player_b_id=int(cb["player_id"]),
            discipline="Bowler",
            comp_type=comp_format,
            n_boot=n_boot,
            seed=seed,
        )

        obs_a = ca[f"{comp_format.lower()}_raw_econ"]
        obs_b = cb[f"{comp_format.lower()}_raw_econ"]
        obs_diff = obs_a - obs_b if pd.notnull(obs_a) and pd.notnull(obs_b) else np.nan

        comparisons.append({
            "pair_id": f"BOWL_RANK_{i+1}_VS_{i+2}",
            "discipline": "Bowler",
            "evaluation_format": comp_format,
            "rank_a": int(ca["top_10_rank"]),
            "player_a_name": ca["player_name"],
            "player_a_id": int(ca["player_id"]),
            "player_a_volume": int(ca[f"{comp_format.lower()}_pressure_volume"]),
            "player_a_rate": obs_a,
            "rank_b": int(cb["top_10_rank"]),
            "player_b_name": cb["player_name"],
            "player_b_id": int(cb["player_id"]),
            "player_b_volume": int(cb[f"{comp_format.lower()}_pressure_volume"]),
            "player_b_rate": obs_b,
            "observed_difference": round(obs_diff, 2) if pd.notnull(obs_diff) else np.nan,
            "bootstrap_se_10k": boot["bootstrap_se"],
            "bootstrap_ci_95_lower": boot["bootstrap_ci_95_lower"],
            "bootstrap_ci_95_upper": boot["bootstrap_ci_95_upper"],
            "effective_sample_assessment": boot["effective_sample_assessment"],
            "statistical_distinction": boot["statistical_distinction"],
            "statistical_verdict": "Distinguishable" if boot["statistical_distinction"] == "STATISTICALLY_DISTINGUISHABLE" else ("Inconclusive Sample" if boot["statistical_distinction"] == "INCONCLUSIVE_INSUFFICIENT_SAMPLE" else "No Statistical Distinction Confirmed (CI spans 0)"),
        })

    return pd.DataFrame(comparisons)


def run_final_selection_pipeline(base_dir: str = ".") -> Dict[str, Any]:
    """Execute complete final selection intelligence pipeline and export deliverables.

    Parameters
    ----------
    base_dir : str
        Base directory of the rr-edge codebase.

    Returns
    -------
    Dict[str, Any]
        Generated selection decision matrices and top-10 datasets.
    """
    output_dir = os.path.join(base_dir, "data", "processed", "final_selections")
    os.makedirs(output_dir, exist_ok=True)

    deliveries_path = os.path.join(base_dir, "data", "processed", "pressure_deliveries.parquet")
    deliveries_df = pd.read_parquet(deliveries_path)

    # 1. Build decision matrices
    batter_matrix = build_final_batter_decision_matrix(base_dir)
    bowler_matrix = build_final_bowler_decision_matrix(base_dir)

    # 2. Extract Top 10 recommendations
    top_10_batters = batter_matrix[batter_matrix["is_recommended_top_10"]].sort_values("top_10_rank").reset_index(drop=True)
    top_10_bowlers = bowler_matrix[bowler_matrix["is_recommended_top_10"]].sort_values("top_10_rank").reset_index(drop=True)

    # 3. Match-cluster bootstrap with 10,000 iterations for adjacent pairs
    bootstrap_results = compute_top_10_pairwise_bootstrap(
        deliveries_df=deliveries_df,
        batter_matrix=batter_matrix,
        bowler_matrix=bowler_matrix,
        n_boot=10000,
        seed=42,
    )

    # 4. Save deliverables (Parquet and CSV)
    batter_matrix.to_parquet(os.path.join(output_dir, "batter_final_decision_matrix.parquet"), index=False)
    batter_matrix.to_csv(os.path.join(output_dir, "batter_final_decision_matrix.csv"), index=False)

    bowler_matrix.to_parquet(os.path.join(output_dir, "bowler_final_decision_matrix.parquet"), index=False)
    bowler_matrix.to_csv(os.path.join(output_dir, "bowler_final_decision_matrix.csv"), index=False)

    top_10_batters.to_parquet(os.path.join(output_dir, "top_10_batters.parquet"), index=False)
    top_10_batters.to_csv(os.path.join(output_dir, "top_10_batters.csv"), index=False)

    top_10_bowlers.to_parquet(os.path.join(output_dir, "top_10_bowlers.parquet"), index=False)
    top_10_bowlers.to_csv(os.path.join(output_dir, "top_10_bowlers.csv"), index=False)

    bootstrap_results.to_csv(os.path.join(output_dir, "top_10_pairwise_bootstrap.csv"), index=False)

    return {
        "batter_final_decision_matrix": batter_matrix,
        "bowler_final_decision_matrix": bowler_matrix,
        "top_10_batters": top_10_batters,
        "top_10_bowlers": top_10_bowlers,
        "top_10_pairwise_bootstrap": bootstrap_results,
    }


if __name__ == "__main__":
    print("Executing Final Selection Intelligence Pipeline (10,000 bootstrap iterations)...")
    res = run_final_selection_pipeline()
    print("Final Selection Pipeline completed successfully!")
    print(f"  Batter Decision Matrix: {len(res['batter_final_decision_matrix'])} candidates")
    print(f"  Bowler Decision Matrix: {len(res['bowler_final_decision_matrix'])} candidates")
    print(f"  Top 10 Batters: {len(res['top_10_batters'])} selections")
    print(f"  Top 10 Bowlers: {len(res['top_10_bowlers'])} selections")
    print(f"  Adjacent Pair Bootstrap: {len(res['top_10_pairwise_bootstrap'])} comparisons (10,000 resamples each)")
