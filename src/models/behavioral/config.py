"""
Behavioral Pressure Intelligence Configuration.

Defines sample thresholds, event observation windows, and metric standards
for observable ball-by-ball behavioral response analysis.
Strictly adheres to observable metrics without psychometric or personality speculation.
"""

from typing import Final, List, Dict

# Minimum event exposures for evidence grading
MIN_EVENT_SAMPLE_HIGH_CONFIDENCE: Final[int] = 30
MIN_EVENT_SAMPLE_PROVISIONAL: Final[int] = 15

# Confidence Tier Labels
CONFIDENCE_HIGH: Final[str] = "CONFIDENT"
CONFIDENCE_PROVISIONAL: Final[str] = "PROVISIONAL"
CONFIDENCE_INSUFFICIENT: Final[str] = "INSUFFICIENT_EVIDENCE"

# Post-dot scoring drought definition (minimum consecutive dots faced by batter)
MIN_CONSECUTIVE_DOTS: Final[int] = 2

# Post-wicket consolidation observation window (balls faced after team wicket)
POST_WICKET_WINDOW_BALLS: Final[int] = 6

# Bowler expensive cluster definition (runs in 3 consecutive deliveries)
CLUSTER_MIN_RUNS: Final[int] = 8
CLUSTER_WINDOW_BALLS: Final[int] = 3

# Bowler spell phase thresholds (balls bowled in match)
EARLY_SPELL_MAX_BALLS: Final[int] = 12  # Overs 1-2
LATE_SPELL_MIN_BALLS: Final[int] = 13   # Overs 3-4

# Minimum balls faced in a single match to include match in consistency variance calculation
MIN_MATCH_PRESSURE_BALLS_BATTER: Final[int] = 5
MIN_MATCH_PRESSURE_BALLS_BOWLER: Final[int] = 6

# Pressure Tiers
HIGH_PRESSURE_TIERS: Final[List[str]] = ["HIGH", "EXTREME"]
NORMAL_PRESSURE_TIERS: Final[List[str]] = ["LOW", "MODERATE"]


def determine_confidence(sample_count: int, high_thresh: int = MIN_EVENT_SAMPLE_HIGH_CONFIDENCE, prov_thresh: int = MIN_EVENT_SAMPLE_PROVISIONAL) -> str:
    """Determine statistical confidence tier based on observable event sample size.
    
    Args:
        sample_count: Number of observed event opportunities.
        high_thresh: Cutoff for confident classification.
        prov_thresh: Cutoff for provisional classification.
        
    Returns:
        Confidence tier string.
    """
    if sample_count >= high_thresh:
        return CONFIDENCE_HIGH
    elif sample_count >= prov_thresh:
        return CONFIDENCE_PROVISIONAL
    return CONFIDENCE_INSUFFICIENT

