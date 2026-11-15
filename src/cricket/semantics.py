"""
Cricket semantics, rules verification, and domain logic for RR EDGE.

Phase 1.1: Provides verified rules for:
1. Competition classification and scope filtering.
2. Extras classification and legal delivery identification.
3. Overs, balls remaining, and scheduled innings balls reconstruction.
4. Target and chase reconstruction hierarchy (avoiding target leakage).
5. Dismissal attribution for batter dismissals and bowler wickets.
"""

from typing import Any, Dict, Optional, Tuple
import pandas as pd


# ---------------------------------------------------------------------------
# 1. Competition Scope & Classification
# ---------------------------------------------------------------------------

def classify_competition(comp_name: str, match_format: str) -> str:
    """Classify competition into standardized domain categories.

    Categories:
    - 'IPL': Indian Premier League editions (2022-2026).
    - 'T20I_SENIOR': Senior Men's T20 Internationals (bilateral/multilateral).
    - 'EMERGING_A_TEAMS': Development / A-team tournaments (Emerging Teams, Rising Stars).
    - 'OTHER': Unclassified competitions.

    Parameters
    ----------
    comp_name : str
        Competition title from competitions.csv.
    match_format : str
        Format identifier ('T20' or 'T20I').

    Returns
    -------
    str
        Standardized category label.
    """
    comp_lower = comp_name.strip().lower()
    if comp_lower.startswith("ipl ") or comp_lower == "ipl":
        return "IPL"
    if "emerging" in comp_lower or "rising stars" in comp_lower:
        return "EMERGING_A_TEAMS"
    if match_format == "T20I":
        return "T20I_SENIOR"
    return "OTHER"


def is_senior_ipl_or_t20i(comp_name: str, match_format: str) -> bool:
    """Determine whether competition meets primary analysis scope (IPL + Senior T20I).

    Parameters
    ----------
    comp_name : str
        Competition title.
    match_format : str
        Match format ('T20' or 'T20I').

    Returns
    -------
    bool
        True if senior IPL or senior T20I from 2022 onwards, False otherwise.
    """
    category = classify_competition(comp_name, match_format)
    return category in {"IPL", "T20I_SENIOR"}


# ---------------------------------------------------------------------------
# 2. Extras & Legal Delivery Classification
# ---------------------------------------------------------------------------

# Empirical classification based on dataset evidence:
# - wide: illegal delivery (does not advance legal ball count; re-bowled)
# - Overstep: front-foot no-ball (illegal delivery; does not advance legal ball count; re-bowled)
# - other: height/beamer/fielding no-ball (illegal delivery; extras1_runs=1; over extended; re-bowled)
# - Penalty: award of 5 penalty runs on a legal delivery (over NOT extended)
# - byes, legbyes, NaN: legal deliveries (advance legal ball count)

ILLEGAL_EXTRAS = {"wide", "Overstep", "other"}


def is_legal_delivery(extras_type: Optional[str]) -> bool:
    """Determine whether a delivery counts towards the legal balls of the over.

    Parameters
    ----------
    extras_type : str or float/NaN
        The extras_type value from ball_by_ball.csv.

    Returns
    -------
    bool
        True if the delivery is legal (increments legal balls count).
        False if illegal (wide, Overstep, or other no-ball).
    """
    if pd.isna(extras_type):
        return True
    return extras_type not in ILLEGAL_EXTRAS


def is_wide(extras_type: Optional[str]) -> bool:
    """Check if delivery is a wide."""
    if pd.isna(extras_type):
        return False
    return extras_type == "wide"


def is_no_ball(extras_type: Optional[str]) -> bool:
    """Check if delivery is a no-ball (either front-foot Overstep or other no-ball)."""
    if pd.isna(extras_type):
        return False
    return extras_type in {"Overstep", "other"}


# ---------------------------------------------------------------------------
# 3. Overs, Scheduled Balls, & Match Phase
# ---------------------------------------------------------------------------

def get_scheduled_balls(
    innings: int,
    first_inn_revised_overs: Optional[float] = None,
    second_inn_revised_overs: Optional[float] = None,
) -> int:
    """Determine scheduled legal balls for an innings.

    Note on data semantics:
    In matches.csv, `first_inn_revised_overs` and `second_inn_revised_overs`
    are recorded in UNITS OF LEGAL BALLS (e.g. 30.0 = 5 overs, 90.0 = 15 overs,
    114.0 = 19 overs), NOT in fractional overs.

    Parameters
    ----------
    innings : int
        Innings number (1, 2, 3, 4).
    first_inn_revised_overs : float, optional
        Recorded scheduled legal balls for 1st innings from matches.csv.
    second_inn_revised_overs : float, optional
        Recorded scheduled legal balls for 2nd innings from matches.csv.

    Returns
    -------
    int
        Scheduled legal balls (e.g. 120 for standard 20-over match, 6 for super over).
    """
    if innings in {3, 4}:
        return 6  # Super over is 1 over = 6 legal balls

    if innings == 1:
        if pd.notna(first_inn_revised_overs) and first_inn_revised_overs > 0:
            return int(first_inn_revised_overs)
        return 120

    if innings == 2:
        if pd.notna(second_inn_revised_overs) and second_inn_revised_overs > 0:
            return int(second_inn_revised_overs)
        return 120

    return 120


def get_match_phase(over_id: int) -> str:
    """Return standard T20 match phase based on overid (1-indexed: 1 to 20).

    Parameters
    ----------
    over_id : int
        Over number (1 to 20).

    Returns
    -------
    str
        'Powerplay' (overs 1-6), 'Middle' (overs 7-15), or 'Death' (overs 16-20).
    """
    if over_id <= 6:
        return "Powerplay"
    if over_id <= 15:
        return "Middle"
    return "Death"


# ---------------------------------------------------------------------------
# 4. Target & Chase Reconstruction Hierarchy
# ---------------------------------------------------------------------------

def determine_chase_target(
    innings: int,
    first_innings_total_runs: Optional[int],
    revised_target: Optional[float] = None,
    super_over_inn3_total: Optional[int] = None,
) -> Optional[int]:
    """Determine second-innings target using strict priority hierarchy.

    Hierarchy:
    1. Innings 1 / Innings 3: No chase target (batting first / setting target) -> returns None.
    2. Innings 4 (Super Over Chase): Target is super_over_inn3_total + 1.
    3. Innings 2 with DLS/revised_target: Explicit target from matches.csv.
    4. Innings 2 Standard: first_innings_total_runs + 1.

    Parameters
    ----------
    innings : int
        Innings number (1, 2, 3, or 4).
    first_innings_total_runs : int, optional
        Completed aggregate score of 1st innings (runs + extras1 + extras2).
    revised_target : float, optional
        DLS target from matches.csv.
    super_over_inn3_total : int, optional
        Total runs scored in innings 3 (if super over).

    Returns
    -------
    int or None
        Target runs required to win the match, or None if setting a target.
    """
    if innings in {1, 3}:
        return None

    if innings == 4:
        if super_over_inn3_total is not None:
            return int(super_over_inn3_total + 1)
        return None

    if innings == 2:
        if pd.notna(revised_target) and revised_target > 0:
            return int(revised_target)
        if first_innings_total_runs is not None:
            return int(first_innings_total_runs + 1)
        return None

    return None


# ---------------------------------------------------------------------------
# 5. Dismissal Attribution
# ---------------------------------------------------------------------------

BOWLER_CREDITED_DISMISSALS = {
    "Bowled",
    "Caught",
    "LBW",
    "Stump",
    "Hit Wicket",
}

NON_BOWLER_DISMISSALS = {
    "RunOut",
    "Retire Out",
    "Obstracting the field",
    "Obstructing the field",
}


def is_bowler_wicket(is_wicket: bool, dismissal_type: Optional[str]) -> bool:
    """Determine whether a delivery resulted in a wicket credited to the bowler.

    Parameters
    ----------
    is_wicket : bool
        Wicket boolean indicator.
    dismissal_type : str or float/NaN
        Type of dismissal.

    Returns
    -------
    bool
        True if credited to bowler (Bowled, Caught, LBW, Stump, Hit Wicket).
        False for RunOut, Retire Out, Obstructing the field, or no wicket.
    """
    if not is_wicket or pd.isna(dismissal_type):
        return False
    return dismissal_type in BOWLER_CREDITED_DISMISSALS


def is_batter_dismissal(is_wicket: bool, dismissal_type: Optional[str]) -> bool:
    """Determine whether a delivery resulted in an official batter dismissal.

    Note: All 9 dismissal types in the dataset (including RunOut and Retire Out)
    end a batter's innings.

    Parameters
    ----------
    is_wicket : bool
    dismissal_type : str or float/NaN

    Returns
    -------
    bool
        True if an active batter lost their wicket.
    """
    if not is_wicket or pd.isna(dismissal_type):
        return False
    return True


def get_dismissed_player_id(
    is_wicket: bool,
    dismissed_player_id: Optional[float],
    striker_id: int,
    non_striker_id: int,
    dismissal_type: Optional[str],
) -> Optional[int]:
    """Resolve the player ID of the batter dismissed on the delivery.

    For Bowled, Caught, LBW, Stump, Hit Wicket: authoritative dismissed player
    is always the striker.
    For RunOut, Retire Out, Obstructing: dismissed_player_id resolves striker vs
    non-striker.

    Parameters
    ----------
    is_wicket : bool
    dismissed_player_id : float or NaN
    striker_id : int
    non_striker_id : int
    dismissal_type : str or float/NaN

    Returns
    -------
    int or None
        Resolved player ID of the dismissed batter.
    """
    if not is_wicket:
        return None

    if pd.notna(dismissed_player_id):
        return int(dismissed_player_id)

    # Fallback when dismissed_player_id is NaN but is_wicket is True
    if dismissal_type in BOWLER_CREDITED_DISMISSALS:
        return striker_id

    return striker_id

