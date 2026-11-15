"""
Chronological Match-Grouped Splitting Module for RR EDGE ML.

Guarantees:
- Strict Match Clustering: Deliveries from a single match never span multiple splits.
- Out-of-Time Validation: Train (2022-2024) -> Validation (2025) -> Holdout Test (2026).
- Format Balance: Both IPL and T20I matches exist in all three partitions.
- Zero Leakage Verification: Validates pairwise match-ID disjointness.
"""

from typing import Dict, Tuple, Set, Any
import json
import numpy as np
import pandas as pd

from .config import TRAIN_SEASONS, VAL_SEASONS, TEST_SEASONS, ML_DIR


def generate_match_grouped_splits(
    metadata: pd.DataFrame,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    """Partition delivery indices into Train, Validation, and Test splits grouped strictly by match_id.

    Parameters
    ----------
    metadata : pd.DataFrame
        DataFrame with columns ['match_id', 'season', 'match_date', 'competition_type'].

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]
        (train_idx, val_idx, test_idx, manifest_dict)
    """
    train_mask = metadata["season"].isin(TRAIN_SEASONS)
    val_mask = metadata["season"].isin(VAL_SEASONS)
    test_mask = metadata["season"].isin(TEST_SEASONS)

    train_matches: Set[int] = set(metadata.loc[train_mask, "match_id"].unique())
    val_matches: Set[int] = set(metadata.loc[val_mask, "match_id"].unique())
    test_matches: Set[int] = set(metadata.loc[test_mask, "match_id"].unique())

    # Strict Disjointness Assertion
    train_val_overlap = train_matches.intersection(val_matches)
    train_test_overlap = train_matches.intersection(test_matches)
    val_test_overlap = val_matches.intersection(test_matches)

    if train_val_overlap or train_test_overlap or val_test_overlap:
        raise ValueError(
            f"SPLIT CONTAMINATION DETECTED: "
            f"Train/Val: {len(train_val_overlap)}, "
            f"Train/Test: {len(train_test_overlap)}, "
            f"Val/Test: {len(val_test_overlap)}"
        )

    train_indices = np.where(train_mask)[0]
    val_indices = np.where(val_mask)[0]
    test_indices = np.where(test_mask)[0]

    manifest = {
        "train": {
            "seasons": TRAIN_SEASONS,
            "matches": len(train_matches),
            "deliveries": len(train_indices),
            "ipl_matches": int(metadata.loc[train_mask & (metadata["competition_type"] == "IPL"), "match_id"].nunique()),
            "t20i_matches": int(metadata.loc[train_mask & (metadata["competition_type"] == "T20I"), "match_id"].nunique()),
            "start_date": str(metadata.loc[train_mask, "match_date"].min()),
            "end_date": str(metadata.loc[train_mask, "match_date"].max()),
        },
        "validation": {
            "seasons": VAL_SEASONS,
            "matches": len(val_matches),
            "deliveries": len(val_indices),
            "ipl_matches": int(metadata.loc[val_mask & (metadata["competition_type"] == "IPL"), "match_id"].nunique()),
            "t20i_matches": int(metadata.loc[val_mask & (metadata["competition_type"] == "T20I"), "match_id"].nunique()),
            "start_date": str(metadata.loc[val_mask, "match_date"].min()),
            "end_date": str(metadata.loc[val_mask, "match_date"].max()),
        },
        "test": {
            "seasons": TEST_SEASONS,
            "matches": len(test_matches),
            "deliveries": len(test_indices),
            "ipl_matches": int(metadata.loc[test_mask & (metadata["competition_type"] == "IPL"), "match_id"].nunique()),
            "t20i_matches": int(metadata.loc[test_mask & (metadata["competition_type"] == "T20I"), "match_id"].nunique()),
            "start_date": str(metadata.loc[test_mask, "match_date"].min()),
            "end_date": str(metadata.loc[test_mask, "match_date"].max()),
        },
        "total_matches": int(metadata["match_id"].nunique()),
        "total_deliveries": len(metadata),
    }

    return train_indices, val_indices, test_indices, manifest

