"""
Competition whitelist and scope configuration for RR EDGE.

Phase 1.2: Explicit competition IDs and inclusion/exclusion configuration.
Excludes A-team and developmental competitions (Emerging Teams, Rising Stars)
while including all 5 IPL editions (2022-2026) and 134 Senior T20 Internationals.
"""

from typing import Dict, List, Set, Tuple


# Explicitly excluded competition IDs (Development / A-team tournaments)
EXCLUDED_COMPETITION_IDS: Set[int] = {
    2670,  # Mens T20 Emerging Teams Asia Cup 2024 (A-teams: India A, Pakistan A, etc.)
    3289,  # Asia Cup Rising Stars 2025 (A-teams: India A, Pakistan A, etc.)
}

# Core IPL Competition IDs (2022-2026)
IPL_COMPETITION_IDS: Set[int] = {
    1358,  # IPL 2022
    1715,  # IPL 2023
    2193,  # IPL 2024
    2725,  # IPL 2025
    3298,  # IPL 2026
}

# Exclusion rationales
EXCLUSION_REASONS: Dict[int, str] = {
    2670: "Emerging Teams tournament featuring A-teams (India A, Pakistan A, Bangladesh A, Sri Lanka A, Afghanistan A) rather than senior national teams.",
    3289: "Rising Stars tournament featuring developmental A-teams rather than senior national teams.",
}

# Inclusion rationales
INCLUSION_CATEGORIES: Dict[str, str] = {
    "IPL": "Tier-1 Franchise League (Indian Premier League 2022-2026)",
    "T20I_SENIOR": "Senior Men's T20 International Series and Tournaments (2022-2026)",
}


def is_competition_included(comp_id: int, match_format: str = "T20I") -> bool:
    """Determine whether competition ID is part of primary evaluation whitelist.

    Parameters
    ----------
    comp_id : int
        Unique competition ID from competitions.csv.
    match_format : str
        Match format string ('T20' or 'T20I').

    Returns
    -------
    bool
        True if senior IPL or senior T20I; False if developmental / A-team.
    """
    if comp_id in EXCLUDED_COMPETITION_IDS:
        return False
    if comp_id in IPL_COMPETITION_IDS:
        return True
    if match_format == "T20I":
        return True
    return False


def get_competition_status(comp_id: int, comp_name: str, match_format: str) -> Tuple[bool, str]:
    """Return inclusion flag and human-readable rationale for competition.

    Parameters
    ----------
    comp_id : int
    comp_name : str
    match_format : str

    Returns
    -------
    (bool, str)
        Tuple of (is_included, rationale).
    """
    if comp_id in EXCLUDED_COMPETITION_IDS:
        return False, EXCLUSION_REASONS.get(comp_id, "Excluded developmental competition")
    if comp_id in IPL_COMPETITION_IDS:
        return True, f"Included: {INCLUSION_CATEGORIES['IPL']}"
    if match_format == "T20I":
        return True, f"Included: {INCLUSION_CATEGORIES['T20I_SENIOR']}"
    return False, "Excluded: Non-whitelisted format/tournament"

