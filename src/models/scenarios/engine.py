"""Historical Scenario Matching Engine for RR EDGE.

Grounds hypothetical match situations strictly in actual historical deliveries,
pre-delivery match states, and complete match-innings outcomes.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from .definitions import ALL_SCENARIOS, ScenarioDefinition

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"


def _wilson_score_interval(successes: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate Wilson score continuity-corrected confidence interval for proportions on distinct matches."""
    if total <= 0:
        return (0.0, 0.0)
    z = 1.96  # 95% confidence
    p = successes / total
    denominator = 1 + z**2 / total
    centre = (p + z**2 / (2 * total)) / denominator
    spread = (z * np.sqrt((p * (1 - p) + z**2 / (4 * total)) / total)) / denominator
    lower = max(0.0, float(centre - spread)) * 100.0
    upper = min(1.0, float(centre + spread)) * 100.0
    return (round(lower, 1), round(upper, 1))


def _match_cluster_bootstrap_rate_ci(
    p_df: pd.DataFrame,
    discipline: str,
    n_boot: int = 500,
    seed: int = 42,
) -> Tuple[float, float]:
    """Calculate 95% match-cluster bootstrap confidence interval for player's scenario rate.

    Accounts for intra-match correlation across deliveries by resampling distinct
    match clusters with replacement rather than assuming delivery independence.
    """
    scale = 6.0 if discipline == "BOWLER" else 100.0
    r_col = "total_delivery_runs" if discipline == "BOWLER" else "runs"

    legal_df = p_df[p_df["is_legal_ball"] == True]
    if len(legal_df) < 5 or p_df["match_id"].nunique() < 2:
        return (0.0, 0.0)

    m_agg = legal_df.groupby("match_id").agg(
        runs=(r_col, "sum"),
        balls=("is_legal_ball", "count")
    ).values

    n_matches = len(m_agg)
    if n_matches < 2 or m_agg[:, 1].sum() == 0:
        return (0.0, 0.0)

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n_matches, size=(n_boot, n_matches))

    resampled_runs = m_agg[idx, 0].sum(axis=1)
    resampled_balls = m_agg[idx, 1].sum(axis=1)

    valid = resampled_balls > 0
    if not np.any(valid):
        return (0.0, 0.0)

    resampled_rates = (resampled_runs[valid] / resampled_balls[valid]) * scale
    ci_lower = round(float(np.percentile(resampled_rates, 2.5)), 1)
    ci_upper = round(float(np.percentile(resampled_rates, 97.5)), 1)
    return (max(0.0, ci_lower), ci_upper)


def pairwise_match_cluster_bootstrap(
    p1_df: pd.DataFrame,
    p2_df: pd.DataFrame,
    discipline: str,
    n_boot: int = 1000,
    seed: int = 42,
) -> Dict[str, Any]:
    """Calculate match-cluster bootstrap difference between two players under an identical scenario."""
    scale = 6.0 if discipline == "BOWLER" else 100.0
    r_col = "total_delivery_runs" if discipline == "BOWLER" else "runs"

    l1 = p1_df[p1_df["is_legal_ball"] == True]
    l2 = p2_df[p2_df["is_legal_ball"] == True]

    m1 = l1.groupby("match_id").agg(runs=(r_col, "sum"), balls=("is_legal_ball", "count")).values
    m2 = l2.groupby("match_id").agg(runs=(r_col, "sum"), balls=("is_legal_ball", "count")).values

    if len(m1) < 2 or len(m2) < 2 or m1[:, 1].sum() == 0 or m2[:, 1].sum() == 0:
        return {
            "bootstrap_se": None,
            "bootstrap_ci_95": [0.0, 0.0],
            "spans_zero": True,
            "sample_adequacy": "INSUFFICIENT_MATCHES",
        }

    rng = np.random.default_rng(seed)
    idx1 = rng.integers(0, len(m1), size=(n_boot, len(m1)))
    idx2 = rng.integers(0, len(m2), size=(n_boot, len(m2)))

    r1 = np.where(m1[idx1, 1].sum(axis=1) == 0, 1, m1[idx1, 1].sum(axis=1))
    r2 = np.where(m2[idx2, 1].sum(axis=1) == 0, 1, m2[idx2, 1].sum(axis=1))

    rates1 = (m1[idx1, 0].sum(axis=1) / r1) * scale
    rates2 = (m2[idx2, 0].sum(axis=1) / r2) * scale
    diffs = rates1 - rates2

    se = round(float(np.std(diffs)), 2)
    low = round(float(np.percentile(diffs, 2.5)), 2)
    high = round(float(np.percentile(diffs, 97.5)), 2)
    spans_zero = bool(low <= 0.0 <= high)

    return {
        "bootstrap_se": se,
        "bootstrap_ci_95": [low, high],
        "spans_zero": spans_zero,
        "sample_adequacy": "ROBUST" if min(len(m1), len(m2)) >= 5 else "MODERATE",
    }


class ScenarioEngine:
    """Singleton engine for querying, matching, and aggregating cricket scenarios."""

    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
        self._matches_df: Optional[pd.DataFrame] = None
        self._initialized = False

    def initialize(self) -> None:
        """Load datasets and prepare indexed matching columns."""
        if self._initialized:
            return

        deliv_path = PROCESSED_DIR / "pressure_deliveries.parquet"
        match_path = RAW_DIR / "matches.csv"

        df = pd.read_parquet(deliv_path)
        matches = pd.read_csv(match_path)

        # Merge match winner info for complete innings outcome calculations
        match_win_map = matches.set_index("match_id")["win_team_id"].to_dict()
        match_result_map = matches.set_index("match_id")["result"].to_dict()

        df["win_team_id"] = df["match_id"].map(match_win_map)
        df["match_result"] = df["match_id"].map(match_result_map).fillna("No Result")

        # Win outcomes for complete match context (never duplicated across deliveries)
        df["chase_won"] = (df["innings"] == 2) & (df["batting_team_id"] == df["win_team_id"])
        df["defend_won"] = (df["innings"] == 2) & (df["bowling_team_id"] == df["win_team_id"])
        df["batter_team_won"] = (df["batting_team_id"] == df["win_team_id"])
        df["bowler_team_won"] = (df["bowling_team_id"] == df["win_team_id"])

        # Enforce strict chronological order for sequential lookups
        df = df.sort_values(
            by=["match_id", "innings", "overid", "over_ball_num", "innings_ball_num"]
        ).reset_index(drop=True)

        # Precompute sequential event contexts (vectorized)
        # 1. Bowler post-boundary intra-over flag (next legal ball within the same over)
        df["bowler_prev_ball_boundary"] = False
        bowler_legal = df[df["is_legal_ball"] == True].copy()
        
        # Shift strictly within bowler match-innings-over
        same_bowler_over = (
            (bowler_legal["match_id"] == bowler_legal["match_id"].shift(1))
            & (bowler_legal["innings"] == bowler_legal["innings"].shift(1))
            & (bowler_legal["bowler_id"] == bowler_legal["bowler_id"].shift(1))
            & (bowler_legal["overid"] == bowler_legal["overid"].shift(1))
        )
        prev_was_boundary = bowler_legal["runs"].shift(1).isin([4, 6])
        bnd_indices = bowler_legal[same_bowler_over & prev_was_boundary].index
        df.loc[bnd_indices, "bowler_prev_ball_boundary"] = True

        # 2. Bowler post-cluster flag (>= 8 runs in rolling 3 balls within spell)
        df["bowler_post_cluster_8"] = False
        rolling_3_runs = (
            bowler_legal["total_delivery_runs"]
            .shift(1)
            .fillna(0)
            + bowler_legal["total_delivery_runs"].shift(2).fillna(0)
            + bowler_legal["total_delivery_runs"].shift(3).fillna(0)
        )
        same_spell = (
            (bowler_legal["match_id"] == bowler_legal["match_id"].shift(3))
            & (bowler_legal["bowler_id"] == bowler_legal["bowler_id"].shift(3))
        )
        cluster_indices = bowler_legal[same_spell & (rolling_3_runs >= 8)].index
        df.loc[cluster_indices, "bowler_post_cluster_8"] = True

        # 3. Batter post-wicket window: incoming batter facing first recovery deliveries
        # Strictly verify current striker is the incoming batter (was neither striker nor non-striker on dismissal ball)
        df["batter_post_wkt"] = False
        df["is_incoming_batter"] = False
        same_team_inn = (
            (df["match_id"] == df["match_id"].shift(1))
            & (df["innings"] == df["innings"].shift(1))
        )
        prev_ball_wkt = (df["is_wicket"].shift(1) == True) & same_team_inn
        prev_striker = df["striker_id"].shift(1)
        prev_non_striker = df["non_striker_id"].shift(1)
        curr_striker = df["striker_id"]

        is_incoming = prev_ball_wkt & (curr_striker != prev_striker) & (curr_striker != prev_non_striker)
        df["is_incoming_batter"] = is_incoming
        df["batter_post_wkt"] = is_incoming & (df["is_legal_ball"] == True)

        # 4. Batter post-dot drought state (batter streak >= 2 dots)
        df["batter_post_2dots"] = (df["batter_prev_6_dots"] >= 2)

        self._df = df
        self._matches_df = matches
        self._initialized = True

    def _build_filter_mask(
        self,
        discipline: str,
        rules: Dict[str, Any],
        format_filter: str = "Combined",
    ) -> pd.Series:
        """Construct a boolean mask for the given scenario conditions."""
        df = self._df
        # Base filter: Primary cohort, strictly pre-delivery
        mask = df["is_primary_pressure_cohort"] == True

        # Format filter
        if format_filter == "IPL":
            mask &= df["competition_type"] == "IPL"
        elif format_filter == "T20I":
            mask &= df["competition_type"] == "T20I"

        # Innings
        if "innings" in rules and rules["innings"] is not None:
            mask &= df["innings"] == rules["innings"]

        # Balls remaining
        if "balls_remaining_max" in rules and rules["balls_remaining_max"] is not None:
            mask &= df["balls_remaining_before"] <= rules["balls_remaining_max"]
        if "balls_remaining_min" in rules and rules["balls_remaining_min"] is not None:
            mask &= df["balls_remaining_before"] >= rules["balls_remaining_min"]

        # Runs to defend / chase
        if "runs_to_defend_max" in rules and rules["runs_to_defend_max"] is not None:
            mask &= df["bowler_runs_to_defend"] <= rules["runs_to_defend_max"]
        if "runs_to_defend_min" in rules and rules["runs_to_defend_min"] is not None:
            mask &= df["bowler_runs_to_defend"] >= rules["runs_to_defend_min"]

        if "runs_to_chase_max" in rules and rules["runs_to_chase_max"] is not None:
            mask &= df["bowler_runs_to_defend"] <= rules["runs_to_chase_max"]
        if "runs_to_chase_min" in rules and rules["runs_to_chase_min"] is not None:
            mask &= df["bowler_runs_to_defend"] >= rules["runs_to_chase_min"]

        # Wickets remaining
        if "wickets_remaining_max" in rules and rules["wickets_remaining_max"] is not None:
            mask &= df["wickets_remaining_before"] <= rules["wickets_remaining_max"]
        if "wickets_remaining_min" in rules and rules["wickets_remaining_min"] is not None:
            mask &= df["wickets_remaining_before"] >= rules["wickets_remaining_min"]

        # Required run rate
        if "required_run_rate_min" in rules and rules["required_run_rate_min"] is not None:
            if discipline == "BOWLER":
                mask &= df["bowler_required_run_rate"] >= rules["required_run_rate_min"]
            else:
                mask &= df["batter_required_run_rate"] >= rules["required_run_rate_min"]

        # Delta RRR
        if "delta_rrr_min" in rules and rules["delta_rrr_min"] is not None:
            mask &= df["batter_delta_rrr"] >= rules["delta_rrr_min"]

        # Innings phase
        if "innings_phase" in rules and rules["innings_phase"] is not None:
            mask &= df["innings_phase"] == rules["innings_phase"]

        # Pressure tier
        if "pressure_tier" in rules and rules["pressure_tier"] is not None:
            if discipline == "BOWLER":
                mask &= df["bowler_pressure_tier"] == rules["pressure_tier"]
            else:
                mask &= df["batter_pressure_tier"] == rules["pressure_tier"]

        if "pressure_tier_in" in rules and rules["pressure_tier_in"] is not None:
            if discipline == "BOWLER":
                mask &= df["bowler_pressure_tier"].isin(rules["pressure_tier_in"])
            else:
                mask &= df["batter_pressure_tier"].isin(rules["pressure_tier_in"])

        # Context triggers
        ctx = rules.get("previous_context")
        if ctx == "boundary_conceded_same_over":
            mask &= df["bowler_prev_ball_boundary"] == True
        elif ctx == "boundary_conceded_recent_2_balls":
            mask &= (df["bowler_prev_ball_boundary"] == True) | (df["bowler_prev_6_runs"] >= 4)
        elif ctx == "cluster_8_runs_in_3_balls":
            mask &= df["bowler_post_cluster_8"] == True
        elif ctx == "cluster_7_runs_in_3_balls":
            mask &= (df["bowler_post_cluster_8"] == True) | (df["bowler_prev_6_runs"] >= 7)
        elif ctx == "team_wicket_in_last_6_balls":
            mask &= (df["batter_post_wkt"] == True) | (df["batter_prev_6_wickets"] >= 1)
        elif ctx == "team_wicket_in_last_10_balls":
            mask &= (df["batter_post_wkt"] == True) | (df["batter_prev_6_wickets"] >= 1)
        elif ctx == "personal_dot_streak_ge_2":
            mask &= df["batter_post_2dots"] == True
        elif ctx == "personal_dot_streak_ge_1":
            mask &= df["batter_prev_6_dots"] >= 1

        return mask

    def execute_scenario(
        self,
        scenario_id: str,
        format_filter: str = "IPL",
        min_evidence: str = "ALL",  # 'ALL' | 'PROVISIONAL' | 'CONFIDENT'
        use_relaxed: bool = False,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        ascending: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Execute a scenario and return ranked player table, cohort stats, and episodes."""
        self.initialize()
        scenario_def = ALL_SCENARIOS.get(scenario_id)
        if not scenario_def:
            raise ValueError(f"Scenario '{scenario_id}' not found in catalog.")

        discipline = scenario_def.discipline
        rules = scenario_def.relaxed_rules if use_relaxed else scenario_def.exact_rules

        mask = self._build_filter_mask(discipline, rules, format_filter)
        cohort_df = self._df[mask].copy()

        # Handle legal ball filtering for rates
        legal_cohort = cohort_df[cohort_df["is_legal_ball"] == True].copy()

        # Calculate cohort benchmark stats
        total_deliveries = len(cohort_df)
        total_matches = int(cohort_df["match_id"].nunique())
        
        if discipline == "BOWLER":
            total_runs = int(cohort_df["total_delivery_runs"].sum())
            total_legal = len(legal_cohort)
            cohort_rate = round((total_runs / total_legal * 6.0), 2) if total_legal > 0 else 0.0
            cohort_dot_pct = round((cohort_df["total_delivery_runs"] == 0).mean() * 100.0, 1) if total_deliveries > 0 else 0.0
            cohort_boundary_pct = round(cohort_df["runs"].isin([4, 6]).mean() * 100.0, 1) if total_deliveries > 0 else 0.0
            cohort_wicket_pct = round(cohort_df["is_bowler_wkt"].mean() * 100.0, 1) if total_deliveries > 0 else 0.0
            
            # Innings outcome success rate (team defended target)
            inn_outcomes = cohort_df.groupby("match_id")["defend_won"].first()
            cohort_success_rate = round(float(inn_outcomes.mean() * 100.0), 1) if len(inn_outcomes) > 0 else None
            player_id_col = "bowler_id"
            player_name_col = "bowler_name"
        else:
            total_runs = int(cohort_df["runs"].sum())
            total_legal = len(legal_cohort)
            cohort_rate = round((total_runs / total_legal * 100.0), 1) if total_legal > 0 else 0.0
            cohort_dot_pct = round((cohort_df["runs"] == 0).mean() * 100.0, 1) if total_deliveries > 0 else 0.0
            cohort_boundary_pct = round(cohort_df["runs"].isin([4, 6]).mean() * 100.0, 1) if total_deliveries > 0 else 0.0
            cohort_wicket_pct = round(cohort_df["is_wicket"].mean() * 100.0, 1) if total_deliveries > 0 else 0.0
            
            # Innings outcome success rate (team chased target)
            inn_outcomes = cohort_df.groupby("match_id")["chase_won"].first()
            cohort_success_rate = round(float(inn_outcomes.mean() * 100.0), 1) if len(inn_outcomes) > 0 else None
            player_id_col = "striker_id"
            player_name_col = "striker_name"

        # Aggregate per player
        players: List[Dict[str, Any]] = []
        if total_deliveries > 0:
            for pid, p_df in cohort_df.groupby(player_id_col, sort=False):
                p_name = p_df[player_name_col].iloc[0]
                p_legal = p_df[p_df["is_legal_ball"] == True]
                p_balls = len(p_legal)
                p_total_balls = len(p_df)
                p_matches = int(p_df["match_id"].nunique())

                if p_balls == 0:
                    continue

                # Operational Evidence Tier: Requires BOTH delivery volume AND independent match exposure
                if p_balls >= 30 and p_matches >= 5:
                    evidence_tier = "CONFIDENT"
                elif (p_balls >= 15 and p_matches >= 3) or p_balls >= 30:
                    evidence_tier = "PROVISIONAL"
                else:
                    evidence_tier = "INSUFFICIENT"

                # Filter by min_evidence
                if min_evidence == "CONFIDENT" and evidence_tier != "CONFIDENT":
                    continue
                if min_evidence == "PROVISIONAL" and evidence_tier == "INSUFFICIENT":
                    continue

                # Search filter
                if search and search.lower() not in p_name.lower():
                    continue

                # Compute player metrics
                if discipline == "BOWLER":
                    p_runs = int(p_df["total_delivery_runs"].sum())
                    p_dots = int((p_df["total_delivery_runs"] == 0).sum())
                    p_bnds = int(p_df["runs"].isin([4, 6]).sum())
                    p_wkts = int(p_df["is_bowler_wkt"].sum())

                    primary_rate = round((p_runs / p_balls * 6.0), 2)
                    dot_pct = round((p_dots / p_total_balls * 100.0), 1)
                    boundary_pct = round((p_bnds / p_total_balls * 100.0), 1)
                    wicket_pct = round((p_wkts / p_total_balls * 100.0), 1)
                    wkts_per_over = round((p_wkts / p_balls * 6.0), 2)

                    # Innings outcome defense win rate across distinct eligible matches
                    win_col = "defend_won" if rules.get("innings") == 2 else "bowler_team_won"
                    p_match_wins = p_df.groupby("match_id")[win_col].first()
                    p_distinct_matches = len(p_match_wins)
                    p_distinct_wins = int(p_match_wins.sum())
                    success_rate = round(float(p_match_wins.mean() * 100.0), 1) if p_distinct_matches > 0 else None
                    success_ci = _wilson_score_interval(p_distinct_wins, p_distinct_matches) if p_distinct_matches >= 3 else (0.0, 0.0)

                    # Comparison vs cohort benchmark & match-cluster bootstrap CI
                    context_diff = round(primary_rate - cohort_rate, 2)  # negative is good for bowling
                    ci_lower, ci_upper = _match_cluster_bootstrap_rate_ci(p_df, discipline="BOWLER")
                else:
                    p_runs = int(p_df["runs"].sum())
                    p_dots = int((p_df["runs"] == 0).sum())
                    p_bnds = int(p_df["runs"].isin([4, 6]).sum())
                    p_wkts = int(p_df["is_wicket"].sum())

                    primary_rate = round((p_runs / p_balls * 100.0), 1)
                    dot_pct = round((p_dots / p_total_balls * 100.0), 1)
                    boundary_pct = round((p_bnds / p_total_balls * 100.0), 1)
                    wicket_pct = round((p_wkts / p_total_balls * 100.0), 1)
                    wkts_per_over = 0.0

                    # Innings outcome chase win rate across distinct eligible matches
                    win_col = "chase_won" if rules.get("innings") == 2 else "batter_team_won"
                    p_match_wins = p_df.groupby("match_id")[win_col].first()
                    p_distinct_matches = len(p_match_wins)
                    p_distinct_wins = int(p_match_wins.sum())
                    success_rate = round(float(p_match_wins.mean() * 100.0), 1) if p_distinct_matches > 0 else None
                    success_ci = _wilson_score_interval(p_distinct_wins, p_distinct_matches) if p_distinct_matches >= 3 else (0.0, 0.0)

                    # Comparison vs cohort benchmark & match-cluster bootstrap CI
                    context_diff = round(primary_rate - cohort_rate, 1)  # positive is good for batting
                    ci_lower, ci_upper = _match_cluster_bootstrap_rate_ci(p_df, discipline="BATTER")

                players.append({
                    "player_id": int(pid),
                    "player_name": str(p_name),
                    "discipline": discipline,
                    "format": format_filter,
                    "deliveries": p_total_balls,
                    "legal_balls": p_balls,
                    "matches": p_matches,
                    "runs": p_runs,
                    "primary_rate": primary_rate,  # Economy or Strike Rate
                    "dot_pct": dot_pct,
                    "boundary_pct": boundary_pct,
                    "wicket_pct": wicket_pct,
                    "wickets_per_over": wkts_per_over,
                    "success_rate": success_rate,
                    "success_ci": [success_ci[0], success_ci[1]],
                    "context_diff": context_diff,
                    "confidence_interval": [ci_lower, ci_upper],
                    "evidence_tier": evidence_tier,
                })

        # Sorting logic
        default_sort = "primary_rate"
        sort_col = sort_by or default_sort
        if discipline == "BOWLER" and sort_by is None:
            # For bowlers, lower economy is better
            ascending = True
        elif discipline == "BATTER" and sort_by is None:
            # For batters, higher strike rate is better
            ascending = False

        if players:
            # Sort with secondary sort on deliveries descending
            players.sort(
                key=lambda x: (
                    0 if x["evidence_tier"] == "CONFIDENT" else (1 if x["evidence_tier"] == "PROVISIONAL" else 2),
                    x.get(sort_col, 0) if ascending else -(x.get(sort_col, 0) or 0),
                    -x["deliveries"],
                )
            )

        # Pagination
        total_count = len(players)
        paginated_players = players[offset : offset + limit]

        # Extract sample recent episodes (up to 15) for inspection
        episodes: List[Dict[str, Any]] = []
        if total_deliveries > 0:
            sample_df = cohort_df.tail(15)
            for _, r in sample_df.iterrows():
                episodes.append({
                    "match_id": int(r["match_id"]),
                    "match_date": str(r["match_date"]),
                    "comp_name": str(r["comp_name"]),
                    "innings": int(r["innings"]),
                    "over_ball": f"{int(r['overid'])}.{int(r['over_ball_num'])}",
                    "striker": str(r["striker_name"]),
                    "bowler": str(r["bowler_name"]),
                    "runs": int(r["runs"]),
                    "total_runs": int(r["total_delivery_runs"]),
                    "is_wicket": bool(r["is_wicket"]),
                    "dismissal_type": str(r["dismissal_type"]) if pd.notna(r["dismissal_type"]) else None,
                    "balls_remaining": int(r["balls_remaining_before"]),
                    "runs_to_defend": int(r["bowler_runs_to_defend"]) if pd.notna(r["bowler_runs_to_defend"]) else None,
                    "match_result": str(r["match_result"]),
                })

        return {
            "scenario": {
                "id": scenario_def.id,
                "name": scenario_def.name,
                "discipline": scenario_def.discipline,
                "category": scenario_def.category,
                "description": scenario_def.description,
                "tactical_intent": scenario_def.tactical_intent,
                "is_relaxed": use_relaxed,
                "relaxation_explanation": scenario_def.relaxation_explanation if use_relaxed else None,
                "applied_rules": rules,
            },
            "format": format_filter,
            "cohort_benchmarks": {
                "total_deliveries": total_deliveries,
                "total_matches": total_matches,
                "total_players": len(players),
                "cohort_rate": cohort_rate,
                "cohort_dot_pct": cohort_dot_pct,
                "cohort_boundary_pct": cohort_boundary_pct,
                "cohort_wicket_pct": cohort_wicket_pct,
                "cohort_success_rate": cohort_success_rate,
            },
            "total_players": total_count,
            "players": paginated_players,
            "sample_episodes": episodes,
        }

    def execute_custom_scenario(
        self,
        config: Dict[str, Any],
        format_filter: str = "Combined",
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Execute a user-configured dynamic scenario."""
        self.initialize()
        discipline = config.get("discipline", "BOWLER").upper()

        # Strict rules from config
        rules = {
            "innings": config.get("innings"),
            "balls_remaining_max": config.get("balls_remaining_max"),
            "balls_remaining_min": config.get("balls_remaining_min"),
            "runs_to_defend_max": config.get("runs_to_defend_max"),
            "runs_to_defend_min": config.get("runs_to_defend_min"),
            "runs_to_chase_max": config.get("runs_to_chase_max"),
            "runs_to_chase_min": config.get("runs_to_chase_min"),
            "wickets_remaining_max": config.get("wickets_remaining_max"),
            "wickets_remaining_min": config.get("wickets_remaining_min"),
            "required_run_rate_min": config.get("required_run_rate_min"),
            "innings_phase": config.get("innings_phase"),
            "previous_context": config.get("previous_context"),
        }

        mask = self._build_filter_mask(discipline, rules, format_filter)
        cohort_df = self._df[mask].copy()

        # Check sample size; if < 15, provide relaxed fallback option
        total_deliveries = len(cohort_df)
        is_relaxed = False
        relaxation_explanation = None

        if total_deliveries < 15:
            # Relax conditions
            relaxed_rules = rules.copy()
            if relaxed_rules.get("balls_remaining_max") is not None:
                relaxed_rules["balls_remaining_max"] += 2
            if relaxed_rules.get("runs_to_defend_max") is not None:
                relaxed_rules["runs_to_defend_max"] += 4
            if relaxed_rules.get("runs_to_chase_max") is not None:
                relaxed_rules["runs_to_chase_max"] += 4
            if relaxed_rules.get("wickets_remaining_max") is not None:
                relaxed_rules["wickets_remaining_max"] += 1
            if relaxed_rules.get("required_run_rate_min") is not None:
                relaxed_rules["required_run_rate_min"] = max(6.0, relaxed_rules["required_run_rate_min"] - 1.5)

            relaxed_mask = self._build_filter_mask(discipline, relaxed_rules, format_filter)
            if relaxed_mask.sum() > total_deliveries:
                cohort_df = self._df[relaxed_mask].copy()
                total_deliveries = len(cohort_df)
                is_relaxed = True
                relaxation_explanation = (
                    "Exact historical matches were below 15 deliveries. Relaxed balls remaining by +2, "
                    "runs by +4, and RRR threshold by -1.5 RPO to construct a comparable cohort."
                )
                rules = relaxed_rules

        # Reuse aggregation logic
        # (similar to execute_scenario)
        legal_cohort = cohort_df[cohort_df["is_legal_ball"] == True].copy()
        total_matches = int(cohort_df["match_id"].nunique())

        if discipline == "BOWLER":
            total_runs = int(cohort_df["total_delivery_runs"].sum())
            total_legal = len(legal_cohort)
            cohort_rate = round((total_runs / total_legal * 6.0), 2) if total_legal > 0 else 0.0
            cohort_dot_pct = round((cohort_df["total_delivery_runs"] == 0).mean() * 100.0, 1) if total_deliveries > 0 else 0.0
            cohort_boundary_pct = round(cohort_df["runs"].isin([4, 6]).mean() * 100.0, 1) if total_deliveries > 0 else 0.0
            cohort_wicket_pct = round(cohort_df["is_bowler_wkt"].mean() * 100.0, 1) if total_deliveries > 0 else 0.0
            inn_outcomes = cohort_df.groupby("match_id")["defend_won"].first()
            cohort_success_rate = round(float(inn_outcomes.mean() * 100.0), 1) if len(inn_outcomes) > 0 else None
            player_id_col = "bowler_id"
            player_name_col = "bowler_name"
        else:
            total_runs = int(cohort_df["runs"].sum())
            total_legal = len(legal_cohort)
            cohort_rate = round((total_runs / total_legal * 100.0), 1) if total_legal > 0 else 0.0
            cohort_dot_pct = round((cohort_df["runs"] == 0).mean() * 100.0, 1) if total_deliveries > 0 else 0.0
            cohort_boundary_pct = round(cohort_df["runs"].isin([4, 6]).mean() * 100.0, 1) if total_deliveries > 0 else 0.0
            cohort_wicket_pct = round(cohort_df["is_wicket"].mean() * 100.0, 1) if total_deliveries > 0 else 0.0
            inn_outcomes = cohort_df.groupby("match_id")["chase_won"].first()
            cohort_success_rate = round(float(inn_outcomes.mean() * 100.0), 1) if len(inn_outcomes) > 0 else None
            player_id_col = "striker_id"
            player_name_col = "striker_name"

        players: List[Dict[str, Any]] = []
        if total_deliveries > 0:
            for pid, p_df in cohort_df.groupby(player_id_col, sort=False):
                p_name = p_df[player_name_col].iloc[0]
                p_legal = p_df[p_df["is_legal_ball"] == True]
                p_balls = len(p_legal)
                p_total_balls = len(p_df)
                p_matches = int(p_df["match_id"].nunique())

                if p_balls == 0:
                    continue

                # Operational Evidence Tier: Requires BOTH delivery volume AND independent match exposure
                if p_balls >= 30 and p_matches >= 5:
                    evidence_tier = "CONFIDENT"
                elif (p_balls >= 15 and p_matches >= 3) or p_balls >= 30:
                    evidence_tier = "PROVISIONAL"
                else:
                    evidence_tier = "INSUFFICIENT"

                if search and search.lower() not in p_name.lower():
                    continue

                if discipline == "BOWLER":
                    p_runs = int(p_df["total_delivery_runs"].sum())
                    p_dots = int((p_df["total_delivery_runs"] == 0).sum())
                    p_bnds = int(p_df["runs"].isin([4, 6]).sum())
                    p_wkts = int(p_df["is_bowler_wkt"].sum())

                    primary_rate = round((p_runs / p_balls * 6.0), 2)
                    dot_pct = round((p_dots / p_total_balls * 100.0), 1)
                    boundary_pct = round((p_bnds / p_total_balls * 100.0), 1)
                    wicket_pct = round((p_wkts / p_total_balls * 100.0), 1)
                    wkts_per_over = round((p_wkts / p_balls * 6.0), 2)

                    win_col = "defend_won" if rules.get("innings") == 2 else "bowler_team_won"
                    p_match_wins = p_df.groupby("match_id")[win_col].first()
                    p_distinct_matches = len(p_match_wins)
                    p_distinct_wins = int(p_match_wins.sum())
                    success_rate = round(float(p_match_wins.mean() * 100.0), 1) if p_distinct_matches > 0 else None
                    success_ci = _wilson_score_interval(p_distinct_wins, p_distinct_matches) if p_distinct_matches >= 3 else (0.0, 0.0)

                    context_diff = round(primary_rate - cohort_rate, 2)
                    ci_lower, ci_upper = _match_cluster_bootstrap_rate_ci(p_df, discipline="BOWLER")
                else:
                    p_runs = int(p_df["runs"].sum())
                    p_dots = int((p_df["runs"] == 0).sum())
                    p_bnds = int(p_df["runs"].isin([4, 6]).sum())
                    p_wkts = int(p_df["is_wicket"].sum())

                    primary_rate = round((p_runs / p_balls * 100.0), 1)
                    dot_pct = round((p_dots / p_total_balls * 100.0), 1)
                    boundary_pct = round((p_bnds / p_total_balls * 100.0), 1)
                    wicket_pct = round((p_wkts / p_total_balls * 100.0), 1)
                    wkts_per_over = 0.0

                    win_col = "chase_won" if rules.get("innings") == 2 else "batter_team_won"
                    p_match_wins = p_df.groupby("match_id")[win_col].first()
                    p_distinct_matches = len(p_match_wins)
                    p_distinct_wins = int(p_match_wins.sum())
                    success_rate = round(float(p_match_wins.mean() * 100.0), 1) if p_distinct_matches > 0 else None
                    success_ci = _wilson_score_interval(p_distinct_wins, p_distinct_matches) if p_distinct_matches >= 3 else (0.0, 0.0)

                    context_diff = round(primary_rate - cohort_rate, 1)
                    ci_lower, ci_upper = _match_cluster_bootstrap_rate_ci(p_df, discipline="BATTER")

                players.append({
                    "player_id": int(pid),
                    "player_name": str(p_name),
                    "discipline": discipline,
                    "format": format_filter,
                    "deliveries": p_total_balls,
                    "legal_balls": p_balls,
                    "matches": p_matches,
                    "runs": p_runs,
                    "primary_rate": primary_rate,
                    "dot_pct": dot_pct,
                    "boundary_pct": boundary_pct,
                    "wicket_pct": wicket_pct,
                    "wickets_per_over": wkts_per_over,
                    "success_rate": success_rate,
                    "success_ci": [success_ci[0], success_ci[1]],
                    "context_diff": context_diff,
                    "confidence_interval": [ci_lower, ci_upper],
                    "evidence_tier": evidence_tier,
                })

        # Sort
        ascending = (discipline == "BOWLER")
        if players:
            players.sort(
                key=lambda x: (
                    0 if x["evidence_tier"] == "CONFIDENT" else (1 if x["evidence_tier"] == "PROVISIONAL" else 2),
                    x["primary_rate"] if ascending else -x["primary_rate"],
                    -x["deliveries"],
                )
            )

        total_count = len(players)
        paginated_players = players[offset : offset + limit]

        return {
            "scenario": {
                "id": "custom",
                "name": "Custom User Scenario",
                "discipline": discipline,
                "category": "Custom Simulation",
                "description": "User-configured match state scenario matching historical database deliveries.",
                "tactical_intent": "Ad-hoc tactical scouting and stress testing.",
                "is_relaxed": is_relaxed,
                "relaxation_explanation": relaxation_explanation,
                "applied_rules": rules,
            },
            "format": format_filter,
            "cohort_benchmarks": {
                "total_deliveries": total_deliveries,
                "total_matches": total_matches,
                "total_players": len(players),
                "cohort_rate": cohort_rate,
                "cohort_dot_pct": cohort_dot_pct,
                "cohort_boundary_pct": cohort_boundary_pct,
                "cohort_wicket_pct": cohort_wicket_pct,
                "cohort_success_rate": cohort_success_rate,
            },
            "total_players": total_count,
            "players": paginated_players,
        }

    def compare_players_on_scenario(
        self,
        scenario_id: str,
        player_ids: List[int],
        format_filter: str = "Combined",
        use_relaxed: bool = False,
    ) -> Dict[str, Any]:
        """Compare multiple players side-by-side on a given scenario."""
        res = self.execute_scenario(
            scenario_id=scenario_id,
            format_filter=format_filter,
            min_evidence="ALL",
            use_relaxed=use_relaxed,
            limit=500,
        )

        p_map = {p["player_id"]: p for p in res["players"]}
        compared: List[Dict[str, Any]] = []
        for pid in player_ids:
            if pid in p_map:
                compared.append(p_map[pid])
            else:
                # Player has zero deliveries in this scenario
                compared.append({
                    "player_id": pid,
                    "player_name": f"Player {pid}",
                    "discipline": res["scenario"]["discipline"],
                    "format": format_filter,
                    "deliveries": 0,
                    "legal_balls": 0,
                    "matches": 0,
                    "runs": 0,
                    "primary_rate": 0.0,
                    "dot_pct": 0.0,
                    "boundary_pct": 0.0,
                    "wicket_pct": 0.0,
                    "wickets_per_over": 0.0,
                    "success_rate": None,
                    "success_ci": [0.0, 0.0],
                    "context_diff": 0.0,
                    "confidence_interval": [0.0, 0.0],
                    "evidence_tier": "INSUFFICIENT",
                })

        pairwise_comparison = None
        if len(player_ids) == 2:
            p1_id, p2_id = player_ids[0], player_ids[1]
            scenario_def = ALL_SCENARIOS.get(scenario_id)
            if scenario_def:
                p_col = "bowler_id" if res["scenario"]["discipline"] == "BOWLER" else "striker_id"
                rules = scenario_def.relaxed_rules if use_relaxed else scenario_def.exact_rules
                mask = self._build_filter_mask(res["scenario"]["discipline"], rules, format_filter)
                cohort_df = self._df[mask]
                p1_df = cohort_df[cohort_df[p_col] == p1_id]
                p2_df = cohort_df[cohort_df[p_col] == p2_id]
                if not p1_df.empty and not p2_df.empty:
                    pairwise_comparison = pairwise_match_cluster_bootstrap(
                        p1_df, p2_df, discipline=res["scenario"]["discipline"]
                    )

        return {
            "scenario": res["scenario"],
            "cohort_benchmarks": res["cohort_benchmarks"],
            "compared_players": compared,
            "pairwise_comparison": pairwise_comparison,
        }


# Singleton instance
scenario_engine = ScenarioEngine()

