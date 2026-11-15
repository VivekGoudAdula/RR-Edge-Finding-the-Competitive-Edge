"""
Relationship validation checks across the RR EDGE datasets.

Verifies foreign-key consistency between ball_by_ball, matches,
competitions, teams, playing_eleven, and competition_team_player_mapping.
Each check returns a structured result dict for programmatic use and
optional human-readable printing.
"""

from typing import Any, Dict, List, Set

import pandas as pd


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def check_foreign_key(
    child_df: pd.DataFrame,
    child_col: str,
    parent_df: pd.DataFrame,
    parent_col: str,
    child_label: str = "child",
    parent_label: str = "parent",
) -> Dict[str, Any]:
    """Check that all values in child_col exist in parent_col.

    Parameters
    ----------
    child_df, parent_df : pd.DataFrame
    child_col, parent_col : str
    child_label, parent_label : str
        Human-readable names for reporting.

    Returns
    -------
    dict
        orphan_count, orphan_values (first 20), is_valid.
    """
    child_vals = set(child_df[child_col].dropna().unique())
    parent_vals = set(parent_df[parent_col].dropna().unique())
    orphans = sorted(child_vals - parent_vals)
    return {
        "check": f"{child_label}.{child_col} → {parent_label}.{parent_col}",
        "is_valid": len(orphans) == 0,
        "orphan_count": len(orphans),
        "orphan_values": orphans[:20],
    }


def check_reverse_coverage(
    parent_df: pd.DataFrame,
    parent_col: str,
    child_df: pd.DataFrame,
    child_col: str,
    parent_label: str = "parent",
    child_label: str = "child",
) -> Dict[str, Any]:
    """Check which parent values have no child references (coverage gaps).

    Returns
    -------
    dict
        uncovered_count, uncovered_values (first 20).
    """
    parent_vals = set(parent_df[parent_col].dropna().unique())
    child_vals = set(child_df[child_col].dropna().unique())
    uncovered = sorted(parent_vals - child_vals)
    return {
        "check": f"{parent_label}.{parent_col} coverage in {child_label}.{child_col}",
        "fully_covered": len(uncovered) == 0,
        "uncovered_count": len(uncovered),
        "uncovered_values": uncovered[:20],
    }


# ---------------------------------------------------------------------------
# Dataset-specific relationship checks
# ---------------------------------------------------------------------------

def validate_all_relationships(datasets: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
    """Run all inter-dataset relationship checks.

    Parameters
    ----------
    datasets : dict[str, pd.DataFrame]
        Keyed by the short names from load_data.FILE_REGISTRY.

    Returns
    -------
    list[dict]
        One result dict per check.
    """
    bbb = datasets["ball_by_ball"]
    matches = datasets["matches"]
    comp = datasets["competitions"]
    teams = datasets["teams"]
    p11 = datasets["playing_eleven"]
    ctpm = datasets["player_mapping"]

    results: List[Dict[str, Any]] = []

    # --- match_id linkages ---
    results.append(check_foreign_key(
        bbb, "match_id", matches, "match_id",
        "ball_by_ball", "matches",
    ))
    results.append(check_reverse_coverage(
        matches, "match_id", bbb, "match_id",
        "matches", "ball_by_ball",
    ))
    results.append(check_foreign_key(
        p11, "match_id", matches, "match_id",
        "playing_eleven", "matches",
    ))
    results.append(check_reverse_coverage(
        matches, "match_id", p11, "match_id",
        "matches", "playing_eleven",
    ))

    # --- comp_id linkages ---
    results.append(check_foreign_key(
        matches, "comp_id", comp, "comp_id",
        "matches", "competitions",
    ))
    results.append(check_reverse_coverage(
        comp, "comp_id", matches, "comp_id",
        "competitions", "matches",
    ))
    results.append(check_foreign_key(
        teams, "comp_id", comp, "comp_id",
        "teams", "competitions",
    ))
    results.append(check_foreign_key(
        ctpm, "comp_id", comp, "comp_id",
        "player_mapping", "competitions",
    ))

    # --- team_id linkages ---
    # Combine batting and bowling team IDs from BBB
    bbb_team_ids = set(bbb["batting_team_id"].unique()) | set(bbb["bowling_team_id"].unique())
    match_team_ids = set(matches["home_team_id"].unique()) | set(matches["away_team_id"].unique())
    teams_ids = set(teams["team_id"].unique())

    results.append({
        "check": "ball_by_ball team_ids → teams.team_id",
        "is_valid": bbb_team_ids.issubset(teams_ids),
        "orphan_count": len(bbb_team_ids - teams_ids),
        "orphan_values": sorted(bbb_team_ids - teams_ids)[:20],
    })
    results.append({
        "check": "matches team_ids → teams.team_id",
        "is_valid": match_team_ids.issubset(teams_ids),
        "orphan_count": len(match_team_ids - teams_ids),
        "orphan_values": sorted(match_team_ids - teams_ids)[:20],
    })

    # --- player_id linkages ---
    bbb_player_ids = (
        set(bbb["striker_id"].unique())
        | set(bbb["non_striker_id"].unique())
        | set(bbb["bowler_id"].unique())
    )
    p11_player_ids = set(p11["player_id"].unique())
    ctpm_player_ids = set(ctpm["player_id"].unique())

    results.append({
        "check": "ball_by_ball player_ids → playing_eleven.player_id",
        "is_valid": bbb_player_ids.issubset(p11_player_ids),
        "orphan_count": len(bbb_player_ids - p11_player_ids),
        "orphan_values": sorted(bbb_player_ids - p11_player_ids)[:20],
    })
    results.append({
        "check": "ball_by_ball player_ids → player_mapping.player_id",
        "is_valid": bbb_player_ids.issubset(ctpm_player_ids),
        "orphan_count": len(bbb_player_ids - ctpm_player_ids),
        "orphan_values": sorted(bbb_player_ids - ctpm_player_ids)[:20],
    })
    results.append({
        "check": "playing_eleven.player_id → player_mapping.player_id",
        "is_valid": p11_player_ids.issubset(ctpm_player_ids),
        "orphan_count": len(p11_player_ids - ctpm_player_ids),
        "orphan_values": sorted(p11_player_ids - ctpm_player_ids)[:20],
    })

    # --- dismissed_player_id linkage ---
    dismissed = bbb.dropna(subset=["dismissed_player_id"])
    dismissed_ids = set(dismissed["dismissed_player_id"].astype(int).unique())
    results.append({
        "check": "dismissed_player_id → playing_eleven.player_id",
        "is_valid": dismissed_ids.issubset(p11_player_ids),
        "orphan_count": len(dismissed_ids - p11_player_ids),
        "orphan_values": sorted(dismissed_ids - p11_player_ids)[:20],
    })

    return results


def print_relationship_results(results: List[Dict[str, Any]]) -> None:
    """Pretty-print the output of validate_all_relationships."""
    print("\n" + "=" * 70)
    print("  RELATIONSHIP VALIDATION RESULTS")
    print("=" * 70)
    for r in results:
        status = "✓ PASS" if r.get("is_valid", r.get("fully_covered", False)) else "✗ FAIL"
        label = r["check"]
        count = r.get("orphan_count", r.get("uncovered_count", 0))
        print(f"  {status}  {label}  ({count} issues)")
        if count > 0:
            values = r.get("orphan_values", r.get("uncovered_values", []))
            print(f"         Sample: {values}")

