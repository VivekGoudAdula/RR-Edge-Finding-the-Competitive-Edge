"""
Unit tests for Behavioral Pressure Intelligence Engine.

Tests:
- Confidence tier determinations and threshold rules.
- Batter behavioral calculations (post-dot scoring recovery, post-wicket consolidation, drought latency).
- Bowler behavioral calculations (post-boundary bounce-back, cluster concession, spell progression).
- Data artifact consistency and non-negative constraints.
"""

import json
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.models.behavioral.config import (
    determine_confidence,
    CONFIDENCE_HIGH,
    CONFIDENCE_PROVISIONAL,
    CONFIDENCE_INSUFFICIENT,
    MIN_EVENT_SAMPLE_HIGH_CONFIDENCE,
    MIN_EVENT_SAMPLE_PROVISIONAL,
)


def test_confidence_tiers():
    """Verify statistical confidence grading rules based on sample size."""
    assert determine_confidence(45) == CONFIDENCE_HIGH
    assert determine_confidence(30) == CONFIDENCE_HIGH
    assert determine_confidence(29) == CONFIDENCE_PROVISIONAL
    assert determine_confidence(15) == CONFIDENCE_PROVISIONAL
    assert determine_confidence(14) == CONFIDENCE_INSUFFICIENT
    assert determine_confidence(0) == CONFIDENCE_INSUFFICIENT


def test_behavioral_artifacts_exist():
    """Verify that all production behavioral artifacts are generated and non-empty."""
    base_dir = Path("data/processed/behavioral")
    assert (base_dir / "batter_behavioral.parquet").exists()
    assert (base_dir / "batter_behavioral.csv").exists()
    assert (base_dir / "bowler_behavioral.parquet").exists()
    assert (base_dir / "bowler_behavioral.csv").exists()
    assert (base_dir / "behavioral_summary.json").exists()

    with open(base_dir / "behavioral_summary.json", "r", encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["dataset_version"] == "v1.0-production"
    assert summary["batters"]["confident_sample_count"] > 100
    assert summary["bowlers"]["confident_sample_count"] > 100


def test_batter_behavioral_schema_and_bounds():
    """Verify batter behavioral dataset schema, bounds, and mathematical integrity."""
    df = pd.read_parquet("data/processed/behavioral/batter_behavioral.parquet")
    assert len(df) > 500
    
    # Check expected columns
    expected_cols = [
        'striker_id', 'striker_name', 'total_balls', 'overall_strike_rate',
        'post_dot_balls', 'post_dot_strike_rate', 'delta_sr_post_dot',
        'post_wkt_balls', 'post_wkt_strike_rate', 'avg_balls_to_scoring',
        'pressure_balls', 'normal_balls', 'delta_sr_pressure_vs_normal',
        'scoring_resilience_index', 'sample_confidence', 'has_sufficient_evidence'
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing column {col} in batter behavioral dataset"
        
    # Check non-negative invariants
    assert (df['total_balls'] >= 0).all()
    assert (df['post_dot_balls'] >= 0).all()
    assert (df['post_dot_strike_rate'] >= 0).all()
    assert (df['avg_balls_to_scoring'] >= 0).all()
    
    # Verify Tim David has confident sample and positive post-dot acceleration
    david = df[df['striker_name'] == 'Tim David']
    assert not david.empty
    row = david.iloc[0]
    assert row['sample_confidence'] == CONFIDENCE_HIGH
    assert row['post_dot_balls'] >= MIN_EVENT_SAMPLE_HIGH_CONFIDENCE
    assert row['post_dot_strike_rate'] > 180.0


def test_bowler_behavioral_schema_and_bounds():
    """Verify bowler behavioral dataset schema, bounds, and mathematical integrity."""
    df = pd.read_parquet("data/processed/behavioral/bowler_behavioral.parquet")
    assert len(df) > 400
    
    expected_cols = [
        'bowler_id', 'bowler_name', 'total_balls', 'overall_economy',
        'post_boundary_legal_balls', 'post_boundary_economy', 'post_boundary_dot_pct',
        'bounceback_index', 'early_spell_balls', 'late_spell_balls',
        'spell_economy_progression', 'sample_confidence', 'has_sufficient_evidence'
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing column {col} in bowler behavioral dataset"
        
    # Check non-negative invariants
    assert (df['total_balls'] >= 0).all()
    assert (df['post_boundary_legal_balls'] >= 0).all()
    assert (df['post_boundary_economy'] >= 0).all()
    assert (df['post_boundary_dot_pct'] >= 0).all()
    assert (df['early_spell_balls'] + df['late_spell_balls'] == df['total_balls']).all()
    
    # Verify Jasprit Bumrah bounceback containment
    bumrah = df[df['bowler_name'] == 'Jasprit Bumrah']
    assert not bumrah.empty
    b_row = bumrah.iloc[0]
    assert b_row['sample_confidence'] == CONFIDENCE_HIGH
    assert b_row['post_boundary_legal_balls'] >= 100
    assert b_row['post_boundary_dot_pct'] > 35.0
    assert b_row['bounceback_index'] > 0.0  # Tighter economy immediately after boundary

