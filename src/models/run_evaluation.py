"""
Phase 3 Evaluation Runner for RR EDGE.

Loads the pressure deliveries dataset, runs both batter and bowler evaluation
engines, and writes all output tables to data/processed/player_evaluations/.

Usage:
    python src/models/run_evaluation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from src.models.batter_evaluation import build_batter_evaluation, save_batter_evaluation
from src.models.bowler_evaluation import build_bowler_evaluation, save_bowler_evaluation


PRESSURE_PARQUET = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
    / "pressure_deliveries.parquet"
)

OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
    / "player_evaluations"
)


def generate_candidate_overlap_table(
    b_eval: pd.DataFrame,
    bl_eval: pd.DataFrame,
) -> pd.DataFrame:
    """Generate structured candidate overlap analysis comparing 30b/4m, 60b/6m, and 100b/8m thresholds."""
    thresholds = [
        ("Broad / Discovery (30b, 4m)", 30, 4),
        ("Balanced (60b, 6m)", 60, 6),
        ("Strict / High Evidence (100b, 8m)", 100, 8),
    ]
    rows = []
    b_sets = {}
    for label, min_b, min_m in thresholds:
        q = b_eval[(b_eval["pressure_balls_faced"] >= min_b) & (b_eval["pressure_matches"] >= min_m)]
        b_sets[label] = set(q["striker_id"])
        rows.append({
            "discipline": "Batter",
            "threshold_label": label,
            "min_balls": min_b,
            "min_matches": min_m,
            "qualified_count": len(q),
            "retained_pct_of_broad": round(len(q) / max(1, len(b_sets[thresholds[0][0]])) * 100, 1),
        })

    bl_sets = {}
    for label, min_b, min_m in thresholds:
        q = bl_eval[(bl_eval["pressure_legal_balls"] >= min_b) & (bl_eval["pressure_matches"] >= min_m)]
        bl_sets[label] = set(q["bowler_id"])
        rows.append({
            "discipline": "Bowler",
            "threshold_label": label,
            "min_balls": min_b,
            "min_matches": min_m,
            "qualified_count": len(q),
            "retained_pct_of_broad": round(len(q) / max(1, len(bl_sets[thresholds[0][0]])) * 100, 1),
        })

    return pd.DataFrame(rows)


def main() -> None:
    """Run the full batter and bowler evaluation pipeline."""
    print("Loading pressure deliveries dataset …")
    df = pd.read_parquet(PRESSURE_PARQUET)
    primary_count = int(df["is_primary_pressure_cohort"].sum())
    print(f"  Total deliveries : {len(df):,}")
    print(f"  Primary cohort   : {primary_count:,}")

    # --- 1. Overall Combined Evaluation ---
    print("\nRunning overall batter evaluation …")
    batter_result = build_batter_evaluation(df)
    print(f"  Total batters evaluated : {len(batter_result['evaluation']):,}")
    print(f"  Qualified batters (30b) : {len(batter_result['qualified']):,}")
    save_batter_evaluation(batter_result, OUTPUT_DIR)

    print("\nRunning overall bowler evaluation …")
    bowler_result = build_bowler_evaluation(df)
    print(f"  Total bowlers evaluated : {len(bowler_result['evaluation']):,}")
    print(f"  Qualified bowlers (30b) : {len(bowler_result['qualified']):,}")
    save_bowler_evaluation(bowler_result, OUTPUT_DIR)

    # --- 2. Format-Specific Evaluations ---
    print("\nGenerating format-specific evaluation tables …")
    for fmt in ["IPL", "T20I"]:
        fmt_lower = fmt.lower()
        print(f"  Processing {fmt} batters …")
        b_fmt = build_batter_evaluation(df, competition_type=fmt)
        b_fmt["evaluation"].to_parquet(OUTPUT_DIR / f"batter_evaluation_{fmt_lower}.parquet", index=False)
        b_fmt["evaluation"].to_csv(OUTPUT_DIR / f"batter_evaluation_{fmt_lower}.csv", index=False)
        b_fmt["qualified"].to_parquet(OUTPUT_DIR / f"batter_qualified_{fmt_lower}.parquet", index=False)
        b_fmt["qualified"].to_csv(OUTPUT_DIR / f"batter_qualified_{fmt_lower}.csv", index=False)

        print(f"  Processing {fmt} bowlers …")
        bl_fmt = build_bowler_evaluation(df, competition_type=fmt)
        bl_fmt["evaluation"].to_parquet(OUTPUT_DIR / f"bowler_evaluation_{fmt_lower}.parquet", index=False)
        bl_fmt["evaluation"].to_csv(OUTPUT_DIR / f"bowler_evaluation_{fmt_lower}.csv", index=False)
        bl_fmt["qualified"].to_parquet(OUTPUT_DIR / f"bowler_qualified_{fmt_lower}.parquet", index=False)
        bl_fmt["qualified"].to_csv(OUTPUT_DIR / f"bowler_qualified_{fmt_lower}.csv", index=False)

    # --- 3. Candidate Overlap Summary ---
    print("\nGenerating candidate overlap summary …")
    overlap_df = generate_candidate_overlap_table(batter_result["evaluation"], bowler_result["evaluation"])
    overlap_df.to_parquet(OUTPUT_DIR / "candidate_overlap_analysis.parquet", index=False)
    overlap_df.to_csv(OUTPUT_DIR / "candidate_overlap_analysis.csv", index=False)
    print(overlap_df.to_string(index=False))

    print("\nPhase 3 evaluation pipeline complete.")


if __name__ == "__main__":
    main()

