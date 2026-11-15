"""
Cricket-specific data quality checks for RR EDGE.

Validates ball-by-ball records against cricket rules: innings numbering,
over/ball sequencing, runs/extras accounting, wicket alignment, and
playing XI completeness.
"""

from typing import Any, Dict, List

import pandas as pd


def check_innings_coverage(bbb: pd.DataFrame) -> Dict[str, Any]:
    """Summarise innings numbering and delivery counts per innings number."""
    innings_counts = bbb.groupby("innings").size().to_dict()
    super_over_matches = bbb[bbb["innings"] > 2]["match_id"].nunique()
    return {
        "innings_values": sorted(bbb["innings"].unique()),
        "deliveries_per_innings_number": innings_counts,
        "super_over_match_count": super_over_matches,
    }


def check_over_ball_numbering(bbb: pd.DataFrame) -> Dict[str, Any]:
    """Check over and ball numbering for anomalies."""
    balls_per_over = bbb.groupby(["match_id", "innings", "overid"]).size()
    short_overs = balls_per_over[balls_per_over < 6]
    long_overs = balls_per_over[balls_per_over > 6]

    return {
        "over_range": (int(bbb["overid"].min()), int(bbb["overid"].max())),
        "ball_num_range": (int(bbb["over_ball_num"].min()), int(bbb["over_ball_num"].max())),
        "innings_ball_max": int(bbb["innings_ball_num"].max()),
        "balls_per_over_distribution": balls_per_over.value_counts().sort_index().to_dict(),
        "short_over_count": len(short_overs),
        "long_over_count": len(long_overs),
    }


def check_runs_and_extras(bbb: pd.DataFrame) -> Dict[str, Any]:
    """Validate runs and extras columns."""
    result: Dict[str, Any] = {}

    # Runs distribution
    result["runs_distribution"] = bbb["runs"].value_counts().sort_index().to_dict()
    result["extras_type_distribution"] = bbb["extras_type"].value_counts().to_dict()

    # Wide: runs should be 0, extras1 carries the wide run
    wides = bbb[bbb["extras_type"] == "wide"]
    result["wide_runs_always_zero"] = (wides["runs"] == 0).all() if len(wides) > 0 else True

    # No-ball (Overstep): extras1 should be 1, batter can score runs
    noballs = bbb[bbb["extras_type"] == "Overstep"]
    result["noball_extras1_always_one"] = (noballs["extras1_runs"] == 1).all() if len(noballs) > 0 else True

    # Boundary consistency
    fours = bbb[bbb["is_four"]]
    sixes = bbb[bbb["is_six"]]
    runs4_not_four = bbb[(bbb["runs"] == 4) & (~bbb["is_four"])]
    runs6_not_six = bbb[(bbb["runs"] == 6) & (~bbb["is_six"])]

    result["is_four_all_runs_4"] = (fours["runs"] == 4).all() if len(fours) > 0 else True
    result["is_six_all_runs_6"] = (sixes["runs"] == 6).all() if len(sixes) > 0 else True
    result["runs_4_but_not_four_count"] = len(runs4_not_four)
    result["runs_6_but_not_six_count"] = len(runs6_not_six)

    return result


def check_wickets(bbb: pd.DataFrame) -> Dict[str, Any]:
    """Validate wicket and dismissal records."""
    result: Dict[str, Any] = {}

    result["total_wickets"] = int(bbb["is_wicket"].sum())
    result["dismissal_type_distribution"] = bbb["dismissal_type"].value_counts().to_dict()

    # Alignment checks
    wicket_no_type = bbb[bbb["is_wicket"] & bbb["dismissal_type"].isna()]
    type_no_wicket = bbb[~bbb["is_wicket"] & bbb["dismissal_type"].notna()]
    result["is_wicket_but_no_type"] = len(wicket_no_type)
    result["type_but_no_is_wicket"] = len(type_no_wicket)

    # dismissed_player_id set but is_wicket=False (anomalous)
    dismissed_no_wicket = bbb[bbb["dismissed_player_id"].notna() & ~bbb["is_wicket"]]
    result["dismissed_id_but_no_wicket_count"] = len(dismissed_no_wicket)

    # Max wickets per innings (should be ≤10)
    wickets_per_innings = bbb.groupby(["match_id", "innings"])["is_wicket"].sum()
    result["max_wickets_in_innings"] = int(wickets_per_innings.max())
    result["innings_over_10_wickets"] = int((wickets_per_innings > 10).sum())

    # Typo check: "Obstracting" vs "Obstructing"
    if "Obstracting the field" in bbb["dismissal_type"].values:
        result["dismissal_type_typo"] = {
            "Obstracting the field": int((bbb["dismissal_type"] == "Obstracting the field").sum()),
            "Obstructing the field": int((bbb["dismissal_type"] == "Obstructing the field").sum()),
        }

    return result


def check_playing_xi(
    p11: pd.DataFrame,
    bbb: pd.DataFrame,
) -> Dict[str, Any]:
    """Check playing XI completeness and impact player usage."""
    played = p11[p11["is_played"]]
    players_per_team = played.groupby(["match_id", "team_id"]).size()

    result: Dict[str, Any] = {
        "total_rows": len(p11),
        "played_count": len(played),
        "not_played_count": len(p11[~p11["is_played"]]),
        "players_per_team_distribution": players_per_team.value_counts().sort_index().to_dict(),
        "impact_player_count": int((p11["is_impact"] == 1).sum()),
        "impact_off_count": int((p11["is_impact_off"] == 1).sum()),
    }

    # Check: batting_order nulls are from non-played entries
    null_order_played = played[played["batting_order"].isna()]
    result["played_but_no_batting_order"] = len(null_order_played)

    return result


def check_bowl_speed(bbb: pd.DataFrame) -> Dict[str, Any]:
    """Analyse bowl_speed quality — many zeros suggest missing data."""
    zero_count = int((bbb["bowl_speed"] == 0.0).sum())
    nonzero = bbb[bbb["bowl_speed"] > 0.0]["bowl_speed"]

    result = {
        "zero_speed_count": zero_count,
        "zero_speed_pct": round(zero_count / len(bbb) * 100, 1),
        "nonzero_speed_count": len(nonzero),
    }
    if len(nonzero) > 0:
        result["nonzero_stats"] = {
            "mean": round(float(nonzero.mean()), 1),
            "median": round(float(nonzero.median()), 1),
            "min": round(float(nonzero.min()), 1),
            "max": round(float(nonzero.max()), 1),
        }
    return result


def run_all_cricket_checks(
    datasets: Dict[str, pd.DataFrame],
) -> Dict[str, Any]:
    """Run every cricket-specific check and return a combined results dict.

    Parameters
    ----------
    datasets : dict[str, pd.DataFrame]
        From load_data.load_all().

    Returns
    -------
    dict
        Keys are check names; values are the individual check results.
    """
    bbb = datasets["ball_by_ball"]
    p11 = datasets["playing_eleven"]

    return {
        "innings_coverage": check_innings_coverage(bbb),
        "over_ball_numbering": check_over_ball_numbering(bbb),
        "runs_and_extras": check_runs_and_extras(bbb),
        "wickets": check_wickets(bbb),
        "playing_xi": check_playing_xi(p11, bbb),
        "bowl_speed": check_bowl_speed(bbb),
    }

