"""
Behavioral Intelligence Service Layer.

Provides fast, in-memory cached query interfaces for batter and bowler
behavioral datasets to power FastAPI endpoints.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import pandas as pd

_CACHE: Dict[str, Any] = {}


def _load_data() -> Dict[str, Any]:
    """Load and cache behavioral datasets and summary."""
    if "loaded" in _CACHE:
        return _CACHE
        
    base_dir = Path("data/processed/behavioral")
    
    # Load summary
    summary_path = base_dir / "behavioral_summary.json"
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
    else:
        summary = {}
        
    # Load dataframes
    batter_path = base_dir / "batter_behavioral.parquet"
    if batter_path.exists():
        batter_df = pd.read_parquet(batter_path)
    else:
        batter_df = pd.DataFrame()
        
    bowler_path = base_dir / "bowler_behavioral.parquet"
    if bowler_path.exists():
        bowler_df = pd.read_parquet(bowler_path)
    else:
        bowler_df = pd.DataFrame()
        
    _CACHE["summary"] = summary
    _CACHE["batters"] = batter_df
    _CACHE["bowlers"] = bowler_df
    _CACHE["loaded"] = True
    return _CACHE


def get_behavioral_overview() -> Dict[str, Any]:
    """Get high-level behavioral overview and summary metrics."""
    data = _load_data()
    return data.get("summary", {})


def query_batters_behavioral(
    query: Optional[str] = None,
    confidence: Optional[str] = None,
    sort_by: str = "scoring_resilience_index",
    ascending: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """Query batter behavioral profiles with filtering, sorting, and pagination."""
    data = _load_data()
    df: pd.DataFrame = data.get("batters", pd.DataFrame())
    if df.empty:
        return {"total": 0, "results": []}
        
    filtered = df.copy()
    if query:
        q = query.strip().lower()
        filtered = filtered[filtered["striker_name"].str.lower().str.contains(q, na=False)]
        
    if confidence:
        filtered = filtered[filtered["sample_confidence"] == confidence.upper()]
        
    if sort_by in filtered.columns:
        filtered = filtered.sort_values(by=sort_by, ascending=ascending)
        
    total = len(filtered)
    page = filtered.iloc[offset : offset + limit]
    
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": page.to_dict(orient="records"),
    }


def get_batter_behavioral_profile(player_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve detailed behavioral profile for a single batter by striker_id."""
    data = _load_data()
    df: pd.DataFrame = data.get("batters", pd.DataFrame())
    if df.empty:
        return None
    match = df[df["striker_id"] == player_id]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def query_bowlers_behavioral(
    query: Optional[str] = None,
    confidence: Optional[str] = None,
    sort_by: str = "bounceback_index",
    ascending: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """Query bowler behavioral profiles with filtering, sorting, and pagination."""
    data = _load_data()
    df: pd.DataFrame = data.get("bowlers", pd.DataFrame())
    if df.empty:
        return {"total": 0, "results": []}
        
    filtered = df.copy()
    if query:
        q = query.strip().lower()
        filtered = filtered[filtered["bowler_name"].str.lower().str.contains(q, na=False)]
        
    if confidence:
        filtered = filtered[filtered["sample_confidence"] == confidence.upper()]
        
    if sort_by in filtered.columns:
        filtered = filtered.sort_values(by=sort_by, ascending=ascending)
        
    total = len(filtered)
    page = filtered.iloc[offset : offset + limit]
    
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": page.to_dict(orient="records"),
    }


def get_bowler_behavioral_profile(player_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve detailed behavioral profile for a single bowler by bowler_id."""
    data = _load_data()
    df: pd.DataFrame = data.get("bowlers", pd.DataFrame())
    if df.empty:
        return None
    match = df[df["bowler_id"] == player_id]
    if match.empty:
        return None
    return match.iloc[0].to_dict()

