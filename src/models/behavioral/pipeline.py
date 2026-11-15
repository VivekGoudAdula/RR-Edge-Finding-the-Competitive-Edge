"""
Behavioral Pressure Intelligence Processing Pipeline.

Orchestrates the calculation of observable behavioral pressure metrics for
batters and bowlers across the full pressure deliveries dataset.
Exports verified parquet, CSV, and summary metadata artifacts.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any
import pandas as pd

from src.models.behavioral.batter_behavioral import compute_batter_behavioral_metrics
from src.models.behavioral.bowler_behavioral import compute_bowler_behavioral_metrics

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_behavioral_pipeline(
    deliveries_path: str = "data/processed/pressure_deliveries.parquet",
    output_dir: str = "data/processed/behavioral",
) -> Dict[str, Any]:
    """Execute the behavioral analysis pipeline.
    
    Args:
        deliveries_path: Path to pressure_deliveries.parquet.
        output_dir: Directory where behavioral artifacts will be written.
        
    Returns:
        Dictionary containing execution summary and artifact paths.
    """
    logger.info(f"Loading pressure deliveries from {deliveries_path}...")
    df = pd.read_parquet(deliveries_path)
    logger.info(f"Loaded {len(df):,} deliveries across {df['match_id'].nunique()} matches.")
    
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # 1. Compute Batter Behavioral Metrics
    logger.info("Computing batter behavioral pressure metrics...")
    batter_df = compute_batter_behavioral_metrics(df)
    logger.info(f"Computed behavioral metrics for {len(batter_df)} batters.")
    
    batter_parquet = out_path / "batter_behavioral.parquet"
    batter_csv = out_path / "batter_behavioral.csv"
    batter_df.to_parquet(batter_parquet, index=False)
    batter_df.to_csv(batter_csv, index=False)
    logger.info(f"Saved batter behavioral dataset to {batter_parquet}")
    
    # 2. Compute Bowler Behavioral Metrics
    logger.info("Computing bowler behavioral pressure metrics...")
    bowler_df = compute_bowler_behavioral_metrics(df)
    logger.info(f"Computed behavioral metrics for {len(bowler_df)} bowlers.")
    
    bowler_parquet = out_path / "bowler_behavioral.parquet"
    bowler_csv = out_path / "bowler_behavioral.csv"
    bowler_df.to_parquet(bowler_parquet, index=False)
    bowler_df.to_csv(bowler_csv, index=False)
    logger.info(f"Saved bowler behavioral dataset to {bowler_parquet}")
    
    # 3. Generate High-Level Summary Metadata
    summary: Dict[str, Any] = {
        "dataset_version": "v1.0-production",
        "total_deliveries_analyzed": int(len(df)),
        "total_matches_analyzed": int(df['match_id'].nunique()),
        "batters": {
            "total_evaluated": int(len(batter_df)),
            "confident_sample_count": int((batter_df['sample_confidence'] == 'CONFIDENT').sum()),
            "provisional_sample_count": int((batter_df['sample_confidence'] == 'PROVISIONAL').sum()),
            "insufficient_evidence_count": int((batter_df['sample_confidence'] == 'INSUFFICIENT_EVIDENCE').sum()),
            "top_resilience_batters": batter_df[batter_df['sample_confidence'] == 'CONFIDENT']
                .sort_values(by='scoring_resilience_index', ascending=False)
                .head(10)[['striker_id', 'striker_name', 'scoring_resilience_index', 'post_dot_strike_rate', 'delta_sr_post_dot']]
                .to_dict(orient='records'),
        },
        "bowlers": {
            "total_evaluated": int(len(bowler_df)),
            "confident_sample_count": int((bowler_df['sample_confidence'] == 'CONFIDENT').sum()),
            "provisional_sample_count": int((bowler_df['sample_confidence'] == 'PROVISIONAL').sum()),
            "insufficient_evidence_count": int((bowler_df['sample_confidence'] == 'INSUFFICIENT_EVIDENCE').sum()),
            "top_bounceback_bowlers": bowler_df[bowler_df['sample_confidence'] == 'CONFIDENT']
                .sort_values(by='bounceback_index', ascending=False)
                .head(10)[['bowler_id', 'bowler_name', 'bounceback_index', 'post_boundary_economy', 'overall_economy', 'post_boundary_dot_pct']]
                .to_dict(orient='records'),
        }
    }
    
    summary_path = out_path / "behavioral_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved behavioral summary metadata to {summary_path}")
    
    return {
        "status": "SUCCESS",
        "batter_count": len(batter_df),
        "bowler_count": len(bowler_df),
        "summary": summary
    }


if __name__ == "__main__":
    run_behavioral_pipeline()

