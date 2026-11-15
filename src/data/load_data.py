"""
Data loading utilities for RR EDGE.

Loads all six raw CSV files from the data/raw/ directory and returns
them as a dictionary of DataFrames. No modifications are applied to
the raw data — that is the job of downstream processing steps.
"""

from pathlib import Path
from typing import Dict, Optional

import pandas as pd


# Default location of the raw CSV files, relative to the project root.
DEFAULT_RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

# Canonical filenames and the short key used in the returned dict.
FILE_REGISTRY: Dict[str, str] = {
    "ball_by_ball": "ball_by_ball.csv",
    "competitions": "competitions.csv",
    "matches": "matches.csv",
    "teams": "teams.csv",
    "playing_eleven": "playing_eleven.csv",
    "player_mapping": "competition_team_player_mapping.csv",
}


def load_single(
    name: str,
    raw_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """Load a single CSV by its registry key.

    Parameters
    ----------
    name : str
        One of the keys in FILE_REGISTRY (e.g. 'ball_by_ball', 'matches').
    raw_dir : Path, optional
        Override the default raw-data directory.

    Returns
    -------
    pd.DataFrame
        The loaded DataFrame, unmodified.

    Raises
    ------
    KeyError
        If *name* is not in FILE_REGISTRY.
    FileNotFoundError
        If the CSV file does not exist at the expected path.
    """
    if name not in FILE_REGISTRY:
        raise KeyError(
            f"Unknown dataset '{name}'. Choose from: {list(FILE_REGISTRY.keys())}"
        )
    raw_dir = raw_dir or DEFAULT_RAW_DIR
    path = raw_dir / FILE_REGISTRY[name]
    if not path.exists():
        raise FileNotFoundError(f"Expected file not found: {path}")
    return pd.read_csv(path)


def load_all(raw_dir: Optional[Path] = None) -> Dict[str, pd.DataFrame]:
    """Load every CSV in FILE_REGISTRY and return a dict keyed by short name.

    Parameters
    ----------
    raw_dir : Path, optional
        Override the default raw-data directory.

    Returns
    -------
    dict[str, pd.DataFrame]
        Keys are the short names from FILE_REGISTRY; values are DataFrames.
    """
    raw_dir = raw_dir or DEFAULT_RAW_DIR
    datasets: Dict[str, pd.DataFrame] = {}
    for key in FILE_REGISTRY:
        datasets[key] = load_single(key, raw_dir)
    return datasets


def get_dataset_info(df: pd.DataFrame, name: str = "") -> Dict:
    """Return a summary dict describing one DataFrame.

    Useful for quick inspection without printing.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to inspect.
    name : str
        Human-readable label for the dataset.

    Returns
    -------
    dict
        Contains shape, column dtypes, null counts, duplicate count, etc.
    """
    info = {
        "name": name,
        "rows": df.shape[0],
        "columns": df.shape[1],
        "column_details": {},
        "duplicate_rows": int(df.duplicated().sum()),
    }
    for col in df.columns:
        info["column_details"][col] = {
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "null_pct": round(df[col].isnull().mean() * 100, 2),
            "n_unique": int(df[col].nunique()),
        }
    return info

