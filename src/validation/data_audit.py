"""
General-purpose data audit utilities for RR EDGE.

Provides functions to profile any DataFrame: shape, types, missing values,
duplicates, and categorical distributions. All functions are designed to be
reusable across different datasets.
"""

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


def profile_dataframe(df: pd.DataFrame, name: str = "") -> Dict[str, Any]:
    """Build a comprehensive profile of a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to profile.
    name : str
        Human-readable label for the dataset.

    Returns
    -------
    dict
        Keys: name, shape, columns (list of per-column dicts),
        duplicate_row_count, memory_mb.
    """
    columns_info = []
    for col in df.columns:
        col_info = {
            "name": col,
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "null_pct": round(df[col].isnull().mean() * 100, 2),
            "n_unique": int(df[col].nunique()),
            "sample_values": df[col].dropna().unique()[:5].tolist(),
        }
        # Add numeric stats if applicable
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info["min"] = float(df[col].min()) if not df[col].isnull().all() else None
            col_info["max"] = float(df[col].max()) if not df[col].isnull().all() else None
        columns_info.append(col_info)

    return {
        "name": name,
        "shape": df.shape,
        "columns": columns_info,
        "duplicate_row_count": int(df.duplicated().sum()),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1e6, 2),
    }


def find_duplicates(
    df: pd.DataFrame,
    subset: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Return duplicate rows (all copies) for inspection.

    Parameters
    ----------
    df : pd.DataFrame
        Source DataFrame.
    subset : list[str], optional
        Columns to consider for duplicate detection.  If None, all columns.

    Returns
    -------
    pd.DataFrame
        All rows that have at least one duplicate, sorted by the subset cols.
    """
    mask = df.duplicated(subset=subset, keep=False)
    result = df[mask]
    if subset:
        result = result.sort_values(subset)
    return result


def missing_value_report(df: pd.DataFrame) -> pd.DataFrame:
    """Return a summary of missing values per column.

    Returns
    -------
    pd.DataFrame
        Columns: column, null_count, null_pct, dtype.
        Only columns with at least one null are included.
    """
    records = []
    for col in df.columns:
        n_null = int(df[col].isnull().sum())
        if n_null > 0:
            records.append({
                "column": col,
                "null_count": n_null,
                "null_pct": round(n_null / len(df) * 100, 2),
                "dtype": str(df[col].dtype),
            })
    return pd.DataFrame(records)


def categorical_distribution(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    max_values: int = 20,
) -> Dict[str, pd.Series]:
    """Return value-count distributions for categorical columns.

    Parameters
    ----------
    df : pd.DataFrame
        Source DataFrame.
    columns : list[str], optional
        Which columns to inspect.  If None, automatically picks object/bool columns.
    max_values : int
        Maximum number of distinct values to return per column.

    Returns
    -------
    dict[str, pd.Series]
        Mapping from column name to its value counts (truncated to *max_values*).
    """
    if columns is None:
        columns = df.select_dtypes(include=["object", "bool", "category"]).columns.tolist()
    result = {}
    for col in columns:
        vc = df[col].value_counts(dropna=False).head(max_values)
        result[col] = vc
    return result


def id_uniqueness_check(
    df: pd.DataFrame,
    id_columns: List[str],
) -> Dict[str, Any]:
    """Check whether a set of columns forms a unique key.

    Parameters
    ----------
    df : pd.DataFrame
        Source DataFrame.
    id_columns : list[str]
        Column(s) expected to be unique together.

    Returns
    -------
    dict
        is_unique (bool), total_rows, unique_combos, duplicate_count.
    """
    n_unique = df[id_columns].drop_duplicates().shape[0]
    return {
        "id_columns": id_columns,
        "is_unique": n_unique == len(df),
        "total_rows": len(df),
        "unique_combos": n_unique,
        "duplicate_count": len(df) - n_unique,
    }


def print_profile(profile: Dict[str, Any]) -> None:
    """Pretty-print the output of profile_dataframe to stdout."""
    print(f"\n{'='*70}")
    print(f"  {profile['name']}  —  {profile['shape'][0]:,} rows × {profile['shape'][1]} columns")
    print(f"  Memory: {profile['memory_mb']} MB | Duplicate rows: {profile['duplicate_row_count']}")
    print(f"{'='*70}")
    header = f"  {'Column':<40s} {'Type':<12s} {'Nulls':>8s} {'%':>7s} {'Unique':>8s}"
    print(header)
    print("  " + "-" * 75)
    for c in profile["columns"]:
        print(
            f"  {c['name']:<40s} {c['dtype']:<12s} "
            f"{c['null_count']:>8,d} {c['null_pct']:>6.1f}% {c['n_unique']:>8,d}"
        )

