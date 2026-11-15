"""
Pressure-analysis feasibility assessment for RR EDGE.

Phase 1.2 Revised: Classifies features into strict tiers based on empirical
data verification:
1. Directly observed variables.
2. Safely derivable variables (ball-level).
3. Variables requiring match-level reconstruction (multi-innings context & DLS).
4. Variables with look-ahead bias risks or data corruption (documented limitations).
"""

from typing import Any, Dict, List


def assess_pressure_features() -> Dict[str, Any]:
    """Return a structured, verified assessment of pressure-feature feasibility.

    Returns
    -------
    dict
        Categorized dictionary of feature groups and derivation constraints.
    """
    directly_observed = {
        "runs": "Batter runs scored off the bat on this delivery (0, 1, 2, 3, 4, 5, 6).",
        "extras1_runs": "Primary extras (penalty or runs from wide, no-ball, bye, leg-bye, penalty).",
        "extras_2_runs": "Secondary extras (overthrows or additional runs on no-balls).",
        "is_wicket": "Authoritative binary flag (True/False) indicating a dismissal occurred.",
        "dismissal_type": "Specific dismissal mechanism (9 categories).",
        "innings": "Innings index (1: first innings, 2: chase, 3/4: super over).",
        "overid": "Current over number (1-indexed: 1 to 20).",
        "over_ball_num": "Delivery sequence within the over (1 to 13, includes extras).",
        "batting_team_id": "Team ID of team currently batting.",
        "bowling_team_id": "Team ID of team currently bowling.",
        "striker_id": "Player ID facing the delivery.",
        "non_striker_id": "Player ID at the bowler's end.",
        "bowler_id": "Player ID delivering the ball.",
        "batting_type": "RHB or LHB.",
        "bowling_type": "12 granular bowling types.",
        "pace_or_spin": "Binary classification (Pace vs Spin).",
        "batting_order": "Raw batting position in the lineup (preserved as-is, including rare 12-13).",
        "stroke": "Categorical shot played (30 types, 3.1% missing).",
        "delivery_style": "Specific ball trajectory/variation (34 types, 0.2% missing).",
        "over_or_around": "Over or Around the wicket.",
        "on_or_off": "On-side or Off-side field bias.",
        "stage": "Tournament stage from matches.csv (League, Qualifier, Eliminator, Final).",
        "knock_out": "Binary knockout indicator from matches.csv (0: league, 1: playoff/knockout).",
        "toss_opted": "Toss winner decision (Batting or Fielding).",
        "revised_target": "Match-level revised target score from matches.csv (populated for 23 matches).",
    }

    safely_derivable = {
        "is_legal_ball": "extras_type not in {'wide', 'Overstep', 'other'}.",
        "is_bowler_wicket": "is_wicket is True and dismissal_type in {'Bowled', 'Caught', 'LBW', 'Stump', 'Hit Wicket'}.",
        "is_batter_dismissal": "is_wicket is True (all dismissal types end batter's innings).",
        "innings_phase": "Classified from overid: Powerplay (1-6), Middle (7-15), Death (16-20).",
        "total_delivery_runs": "runs + extras1_runs + extras_2_runs.",
        "is_dot_ball": "total_delivery_runs == 0 and is_wicket is False.",
        "is_boundary": "is_four is True or is_six is True.",
        "dismissed_batter_id": "striker_id for bowler wickets; resolved via dismissed_player_id for run-outs.",
        "batting_order_raw": "Exact raw batting order preserved without clamping.",
    }

    requires_match_reconstruction = {
        "current_score_before": (
            "Cumulative sum of total_delivery_runs within (match_id, innings), "
            "lagged by 1 delivery via inside-group transform so current delivery is excluded."
        ),
        "wickets_lost_before": (
            "Cumulative sum of is_wicket within (match_id, innings), lagged by 1 delivery via inside-group transform."
        ),
        "wickets_remaining_before": "10 - wickets_lost_before.",
        "legal_balls_bowled_before": (
            "Cumulative count of is_legal_ball within (match_id, innings), lagged by 1 delivery via inside-group transform."
        ),
        "scheduled_innings_balls": (
            "Resolved per innings: 120 for standard T20; for shortened matches, "
            "derived from first_inn_revised_overs or second_inn_revised_overs (recorded in units of legal balls); 6 for Super Overs."
        ),
        "legal_balls_remaining_before": "scheduled_innings_balls - legal_balls_bowled_before.",
        "innings_target_uninterrupted": (
            "For standard chases: completed 1st innings total runs + 1. Zero leakage."
        ),
        "current_run_rate_before": (
            "current_score_before / (legal_balls_bowled_before / 6) when legal_balls_bowled_before > 0."
        ),
        "striker_balls_faced_before": "Count of legal deliveries faced by current striker before this delivery.",
        "striker_runs_before": "Cumulative runs scored off the bat by current striker before this delivery.",
    }

    dls_and_timing_limitations = {
        "dls_target_timing_uncertainty": (
            "In matches.csv, revised_target is a single scalar at match level. "
            "The dataset does NOT provide delivery-level target update timestamps. "
            "If rain stopped play during the chase, the target established mid-innings "
            "would introduce look-ahead bias if applied to deliveries bowled before the interruption. "
            "Matches with revised_target must be tagged with target_certainty='UNCERTAIN_DLS_TIMING'."
        ),
        "bowl_speed_unreliability": (
            "38.7% (77,861 rows) are 0.0 (unrecorded/missing). 126 entire matches "
            "have zero bowl speeds. Outliers exist up to 1456 kph. "
            "Must be strictly an optional conditioning feature."
        ),
        "innings_ball_num_misuse": (
            "innings_ball_num increments on ALL deliveries including wides and no-balls. "
            "Must never be used as legal balls bowled."
        ),
        "revised_overs_unit_misconception": (
            "In matches.csv, values like 90.0, 60.0, 48.0 represent SCHEDULED BALLS, "
            "not overs. Treating 90.0 as 90 overs would completely break over math."
        ),
    }

    return {
        "directly_observed": directly_observed,
        "safely_derivable": safely_derivable,
        "requires_match_reconstruction": requires_match_reconstruction,
        "dls_and_timing_limitations": dls_and_timing_limitations,
        # Backward-compatibility aliases for legacy exploration notebooks
        "directly_available": directly_observed,
        "derivable": safely_derivable,
        "not_reliable": dls_and_timing_limitations,
        "derivation_notes": list(dls_and_timing_limitations.values()),
    }
