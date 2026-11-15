"""General utility and formatting helpers for RR EDGE."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning a default value if denominator is zero.

    Parameters
    ----------
    numerator : float
        The dividend.
    denominator : float
        The divisor.
    default : float, optional
        Value to return if denominator is 0 (default: 0.0).

    Returns
    -------
    float
        Computed quotient or default value.
    """
    if denominator == 0 or pd.isna(denominator):
        return default
    return numerator / denominator


def format_overs(balls: int) -> str:
    """Convert an integer count of legal balls into standard cricket overs notation.

    Examples:
    ---------
    >>> format_overs(6)
    '1.0'
    >>> format_overs(7)
    '1.1'

    Parameters
    ----------
    balls : int
        Number of legal deliveries.

    Returns
    -------
    str
        Formatted string representing overs (e.g. '3.4').
    """
    complete_overs = balls // 6
    remaining_balls = balls % 6
    return f"{complete_overs}.{remaining_balls}"


def get_innings_phase(over_id: int) -> str:
    """Classify over number into standard T20 match phase.

    Parameters
    ----------
    over_id : int
        Over number (1-indexed, typically 1 to 20).

    Returns
    -------
    str
        'Powerplay' (1-6), 'Middle' (7-15), or 'Death' (16-20).
    """
    if over_id <= 6:
        return "Powerplay"
    if over_id <= 15:
        return "Middle"
    return "Death"

