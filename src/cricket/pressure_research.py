"""
Pressure intelligence framework and research utilities for RR EDGE.

Phase 2.1 & 2.1.1: Implements empirical distribution analysis, 1st-innings expected
scoring resource modeling, rolling momentum features, asymmetric batter/bowler pressure,
and Bayesian sample-size shrinkage.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


def compute_previous_legal_runs(df: pd.DataFrame, window: int = 6) -> np.ndarray:
    """Compute rolling sum of runs scored on previous legal deliveries.

    Computed strictly within each (match_id, innings) group before the current delivery.

    Parameters
    ----------
    df : pd.DataFrame
        Delivery DataFrame containing match_id, innings, is_legal_ball, total_delivery_runs.
    window : int, optional
        Number of previous legal balls to aggregate (default: 6, i.e. 1 over).

    Returns
    -------
    np.ndarray
        Array of rolling previous legal runs.
    """
    prev_runs = np.full(len(df), np.nan)
    for (mid, inn), grp in df.groupby(["match_id", "innings"]):
        idxs = grp.index.values
        is_leg = grp["is_legal_ball"].values
        runs = grp["total_delivery_runs"].values
        buf: List[int] = []
        for i, idx in enumerate(idxs):
            if len(buf) >= window:
                prev_runs[idx] = sum(buf[-window:])
            elif len(buf) > 0:
                prev_runs[idx] = sum(buf) * (float(window) / len(buf))
            else:
                prev_runs[idx] = np.nan
            if is_leg[i]:
                buf.append(int(runs[i]))
    return prev_runs


def compute_advanced_momentum(
    df: pd.DataFrame,
    window: int = 6,
) -> pd.DataFrame:
    """Compute 4 pre-delivery rolling momentum features within each (match_id, innings) group.

    Features:
    - prev_6_runs: Runs scored off the last `window` legal deliveries (scaled if < window).
    - prev_6_dots: Count of dot balls (0 total runs) in the last `window` legal deliveries.
    - prev_6_wkts: Count of dismissals in the last `window` legal deliveries.
    - prev_over_runs: Total runs scored in the immediately preceding completed over (6 legal balls).

    Calculated pre-delivery with zero target leakage and zero cross-group boundary leaks.

    Parameters
    ----------
    df : pd.DataFrame
        Delivery-level DataFrame.
    window : int, optional
        Window of prior legal balls (default: 6).

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['prev_6_runs', 'prev_6_dots', 'prev_6_wkts', 'prev_over_runs'].
    """
    orig_index = df.index
    df_work = df.reset_index(drop=True)
    n = len(df_work)

    prev_6_runs = np.full(n, np.nan, dtype=np.float64)
    prev_6_dots = np.full(n, np.nan, dtype=np.float64)
    prev_6_wkts = np.full(n, np.nan, dtype=np.float64)
    prev_over_runs = np.full(n, np.nan, dtype=np.float64)

    is_legal = df_work["is_legal_ball"].values
    tot_runs = df_work["total_delivery_runs"].values
    is_wkt = df_work["is_wicket"].values

    for (mid, inn), grp in df_work.groupby(["match_id", "innings"]):
        idxs = grp.index.values

        run_history: List[int] = []
        dot_history: List[int] = []
        wkt_history: List[int] = []
        completed_overs_runs: Dict[int, int] = {}
        current_over_runs: int = 0
        current_over_legal: int = 0

        for idx in idxs:
            curr_legal_balls = len(run_history)
            completed_overs = curr_legal_balls // 6

            # Feature 1: prev_6_runs
            if curr_legal_balls >= window:
                prev_6_runs[idx] = sum(run_history[-window:])
            elif curr_legal_balls > 0:
                prev_6_runs[idx] = sum(run_history) * (float(window) / curr_legal_balls)

            # Feature 2: prev_6_dots
            if curr_legal_balls >= window:
                prev_6_dots[idx] = sum(dot_history[-window:])
            elif curr_legal_balls > 0:
                prev_6_dots[idx] = sum(dot_history) * (float(window) / curr_legal_balls)

            # Feature 3: prev_6_wkts
            if curr_legal_balls >= window:
                prev_6_wkts[idx] = sum(wkt_history[-window:])
            elif curr_legal_balls > 0:
                prev_6_wkts[idx] = sum(wkt_history)

            # Feature 4: prev_over_runs
            if completed_overs >= 1:
                prev_over_runs[idx] = completed_overs_runs.get(completed_overs - 1, np.nan)

            # Update history with this delivery
            r = int(tot_runs[idx])
            w = 1 if bool(is_wkt[idx]) else 0
            leg = bool(is_legal[idx])

            current_over_runs += r
            if leg:
                current_over_legal += 1
                run_history.append(r)
                dot_history.append(1 if r == 0 else 0)
                wkt_history.append(w)

                if current_over_legal == 6:
                    completed_overs_runs[completed_overs] = current_over_runs
                    current_over_runs = 0
                    current_over_legal = 0

    res = pd.DataFrame(
        {
            "prev_6_runs": prev_6_runs,
            "prev_6_dots": prev_6_dots,
            "prev_6_wkts": prev_6_wkts,
            "prev_over_runs": prev_over_runs,
        },
        index=orig_index,
    )
    return res


class FirstInningsResourceModel:
    """Historical expected scoring model for 1st innings conditioned on match resources.

    Estimates E[Remaining Runs | Legal Balls Bowled, Wickets Lost, Competition]
    trained on historical 1st innings with chronological match-level splitting.
    """

    BENCHMARK_TOTALS = {
        "IPL": 183.0,
        "T20I": 165.2,
        "OVERALL": 173.0,
    }

    def __init__(self, by_competition: bool = True) -> None:
        self.by_competition = by_competition
        self.resource_grid_: Optional[pd.DataFrame] = None
        self.comp_grids_: Dict[str, pd.DataFrame] = {}
        self.over_fallback_: Dict[int, float] = {}
        self.comp_over_fallback_: Dict[str, Dict[int, float]] = {}
        self.comp_benchmarks_: Dict[str, float] = dict(self.BENCHMARK_TOTALS)

    def fit(self, train_df: pd.DataFrame) -> "FirstInningsResourceModel":
        """Fit empirical resource grid on training matches (innings 1 only).

        Parameters
        ----------
        train_df : pd.DataFrame
            Deliveries from 1st innings of training matches.
            Must contain match_id, legal_balls_bowled_before, wickets_lost_before,
            current_score_before, total_delivery_runs, and competition_type.
        """
        df = train_df.copy()
        match_totals = df.groupby("match_id")["total_delivery_runs"].sum().rename("completed_runs")
        df = df.merge(match_totals, on="match_id", how="left")
        df["remaining_runs"] = df["completed_runs"] - df["current_score_before"]
        df["over_bucket"] = df["legal_balls_bowled_before"] // 6

        # Global grid
        self.resource_grid_ = (
            df.groupby(["over_bucket", "wickets_lost_before"])["remaining_runs"].mean().unstack()
        )
        self.over_fallback_ = df.groupby("over_bucket")["remaining_runs"].mean().to_dict()

        # Competition-specific grids
        if self.by_competition and "competition_type" in df.columns:
            for c_type, grp in df.groupby("competition_type"):
                c_str = str(c_type)
                grid_c = grp.groupby(["over_bucket", "wickets_lost_before"])["remaining_runs"].mean().unstack()
                self.comp_grids_[c_str] = grid_c
                self.comp_over_fallback_[c_str] = grp.groupby("over_bucket")["remaining_runs"].mean().to_dict()

                # Actual completed innings mean
                comp_matches = grp.drop_duplicates(subset=["match_id"])
                if len(comp_matches) > 0:
                    self.comp_benchmarks_[c_str] = float(comp_matches["completed_runs"].mean())

        return self

    def predict_remaining_runs(
        self,
        legal_balls_bowled: int,
        wickets_lost: int,
        competition_type: Optional[str] = None,
    ) -> float:
        """Predict expected remaining runs from current match state.

        Parameters
        ----------
        legal_balls_bowled : int
            Legal balls bowled so far (0 to 120).
        wickets_lost : int
            Wickets lost so far (0 to 10).
        competition_type : str, optional
            'IPL', 'T20I', or None for global average.

        Returns
        -------
        float
            Expected remaining runs in the innings.
        """
        if wickets_lost >= 10 or legal_balls_bowled >= 120:
            return 0.0

        over_bucket = min(19, legal_balls_bowled // 6)

        # 1. Try competition-specific grid
        if competition_type and competition_type in self.comp_grids_:
            c_grid = self.comp_grids_[competition_type]
            if over_bucket in c_grid.index and wickets_lost in c_grid.columns:
                val = c_grid.loc[over_bucket, wickets_lost]
                if pd.notna(val):
                    return float(val)
            if over_bucket in self.comp_over_fallback_.get(competition_type, {}):
                return float(self.comp_over_fallback_[competition_type][over_bucket])

        # 2. Try global grid
        if self.resource_grid_ is not None:
            if over_bucket in self.resource_grid_.index and wickets_lost in self.resource_grid_.columns:
                val = self.resource_grid_.loc[over_bucket, wickets_lost]
                if pd.notna(val):
                    return float(val)

        # 3. Fallback
        return float(self.over_fallback_.get(over_bucket, max(0.0, (120 - legal_balls_bowled) * 1.35)))

    def predict_par_score(
        self,
        current_score_before: int,
        legal_balls_bowled: int,
        wickets_lost: int,
        competition_type: Optional[str] = None,
    ) -> float:
        """Predict expected final 1st-innings score (Par Score).

        Mathematical Definition:
        Par Score = Current Score Before + E[Remaining Runs | State, Competition]
        """
        return current_score_before + self.predict_remaining_runs(
            legal_balls_bowled, wickets_lost, competition_type
        )

    def predict_par_deficit(
        self,
        current_score_before: int,
        legal_balls_bowled: int,
        wickets_lost: int,
        competition_type: str = "IPL",
    ) -> float:
        """Compute Par Deficit relative to historical competition baseline score.

        Mathematical Definition:
        Par Deficit = Competition Historical Mean - Par Score

        A positive deficit (> 0) means the team is tracking BELOW historical average,
        creating acute acceleration pressure for the batting team.
        A negative deficit (< 0) indicates the team is tracking ahead of par.
        """
        par_score = self.predict_par_score(
            current_score_before, legal_balls_bowled, wickets_lost, competition_type
        )
        benchmark = self.comp_benchmarks_.get(
            competition_type, self.BENCHMARK_TOTALS.get(competition_type, 173.0)
        )
        return benchmark - par_score


def classify_batter_pressure_multidimensional(
    innings: int,
    balls_remaining: int,
    wickets_remaining: int,
    rrr: Optional[float] = None,
    delta_rrr: Optional[float] = None,
    par_deficit: Optional[float] = None,
    recent_drought_runs: Optional[float] = None,
) -> Dict[str, Any]:
    """Evaluate batter pressure vector facing batter before delivery.

    Batters experience high pressure when:
    - Chase RRR is elevated (>= 12.0) or surging (Delta RRR >= 4.0)
    - 1st innings par deficit is high (lagging behind expected score by >= 20 runs)
    - Wickets are severely depleted (<= 3 wickets in hand), constraining risk-taking
    - Scoring has stalled in the last 6 balls (<= 3 runs scored)
    """
    is_chase = innings == 2

    # Rate pressure
    if is_chase and rrr is not None:
        if rrr >= 14.0 or (delta_rrr is not None and delta_rrr >= 6.0):
            rate_tier = "EXTREME_RATE"
        elif rrr >= 10.5 or (delta_rrr is not None and delta_rrr >= 2.5):
            rate_tier = "HIGH_RATE"
        elif rrr <= 7.0:
            rate_tier = "LOW_RATE"
        else:
            rate_tier = "MODERATE_RATE"
    elif not is_chase and par_deficit is not None:
        if par_deficit >= 25.0:
            rate_tier = "EXTREME_RATE"
        elif par_deficit >= 15.0:
            rate_tier = "HIGH_RATE"
        elif par_deficit <= -15.0:
            rate_tier = "LOW_RATE"
        else:
            rate_tier = "MODERATE_RATE"
    else:
        rate_tier = "MODERATE_RATE"

    # Resource pressure
    if wickets_remaining <= 3:
        resource_tier = "CRITICAL_WICKETS"
    elif wickets_remaining <= 5 and balls_remaining <= 36:
        resource_tier = "HIGH_RESOURCE_STRESS"
    elif wickets_remaining >= 8:
        resource_tier = "AMPLE_RESOURCES"
    else:
        resource_tier = "NORMAL_RESOURCES"

    # Momentum pressure
    if recent_drought_runs is not None and recent_drought_runs <= 3.0:
        momentum_tier = "DROUGHT"
    elif recent_drought_runs is not None and recent_drought_runs >= 12.0:
        momentum_tier = "SURGE"
    else:
        momentum_tier = "STEADY"

    # Composite Classification
    is_high = (
        rate_tier == "EXTREME_RATE"
        or (rate_tier == "HIGH_RATE" and resource_tier in {"CRITICAL_WICKETS", "HIGH_RESOURCE_STRESS"})
        or (resource_tier == "CRITICAL_WICKETS" and balls_remaining <= 30)
        or (rate_tier == "HIGH_RATE" and momentum_tier == "DROUGHT")
    )
    is_low = (
        rate_tier == "LOW_RATE"
        and resource_tier in {"AMPLE_RESOURCES", "NORMAL_RESOURCES"}
        and momentum_tier != "DROUGHT"
    )

    composite_tier = "HIGH" if is_high else ("LOW" if is_low else "MEDIUM")
    return {
        "rate_tier": rate_tier,
        "resource_tier": resource_tier,
        "momentum_tier": momentum_tier,
        "composite_tier": composite_tier,
        "is_high_pressure": is_high,
    }


def classify_bowler_pressure_multidimensional(
    innings: int,
    balls_remaining: int,
    wickets_remaining: int,
    rrr: Optional[float] = None,
    runs_required: Optional[float] = None,
    recent_surge_runs: Optional[float] = None,
) -> Dict[str, Any]:
    """Evaluate bowler pressure vector facing bowler before delivery.

    Crucial Cricket Asymmetry:
    1. High RRR does NOT necessarily equal high bowler pressure. If RRR is 16
       and batting team has only 2 wickets remaining, the bowler is in command
       closing out the tail.
    2. Bowler pressure is EXTREME when:
       - Margin pressure: Opposition needs <= 18 runs in <= 12 balls (single boundary flips match).
       - Firepower under high rate: RRR >= 12.0 but opposition has >= 6 wickets in hand.
       - Opposition has momentum: recent_surge_runs >= 12 in last 6 balls.
       - Death overs defending small margin.
    """
    is_chase = innings == 2

    # 1. Acute Margin Pressure (Finishing overs defense)
    is_margin_critical = False
    if is_chase and runs_required is not None and balls_remaining is not None:
        if balls_remaining <= 12 and runs_required <= 18:
            is_margin_critical = True
        elif balls_remaining <= 24 and runs_required <= 32:
            is_margin_critical = True

    # 2. Bowler Rate vs Resource Interaction
    if is_chase and rrr is not None:
        if is_margin_critical:
            bowler_context_tier = "CRITICAL_MARGIN"
        elif rrr >= 14.0 and wickets_remaining <= 2:
            # Closing out tail: Bowler is dominant
            bowler_context_tier = "CLOSING_OUT_TAIL"
        elif rrr >= 12.0 and wickets_remaining >= 6:
            # Threat of explosive assault
            bowler_context_tier = "HIGH_FIREPOWER_DEFENSE"
        elif rrr >= 14.0:
            bowler_context_tier = "DEFENDING_STEEP_RATE"
        elif rrr <= 7.0:
            bowler_context_tier = "OPPOSITION_CRUISING"
        else:
            bowler_context_tier = "BALANCED_CHASE"
    else:
        # First innings context
        if balls_remaining <= 24:
            bowler_context_tier = "DEATH_OVERS_CONTAINMENT"
        elif balls_remaining >= 84:
            bowler_context_tier = "POWERPLAY_ATTACK"
        else:
            bowler_context_tier = "MIDDLE_OVERS_CONTROL"

    # 3. Momentum against bowler
    if recent_surge_runs is not None and recent_surge_runs >= 12.0:
        momentum_tier = "OPPOSITION_SURGE"
    elif recent_surge_runs is not None and recent_surge_runs <= 4.0:
        momentum_tier = "BOWLER_SQUEEZE"
    else:
        momentum_tier = "STEADY"

    # Composite Bowler Pressure Decision
    is_high = (
        is_margin_critical
        or bowler_context_tier in {"HIGH_FIREPOWER_DEFENSE", "DEFENDING_STEEP_RATE"}
        or (bowler_context_tier == "DEATH_OVERS_CONTAINMENT" and wickets_remaining >= 5)
        or (bowler_context_tier == "POWERPLAY_ATTACK" and momentum_tier == "OPPOSITION_SURGE")
    ) and (bowler_context_tier != "CLOSING_OUT_TAIL")

    composite_tier = "HIGH" if is_high else ("LOW" if bowler_context_tier == "CLOSING_OUT_TAIL" else "MEDIUM")

    return {
        "bowler_context_tier": bowler_context_tier,
        "momentum_tier": momentum_tier,
        "is_margin_critical": is_margin_critical,
        "composite_tier": composite_tier,
        "is_high_pressure": is_high,
    }


def classify_delivery_pressure_multidimensional(
    innings: int,
    balls_remaining: int,
    wickets_remaining: int,
    rrr: Optional[float] = None,
    delta_rrr: Optional[float] = None,
    par_deficit: Optional[float] = None,
    recent_drought_runs: Optional[float] = None,
) -> Dict[str, Any]:
    """Backward compatible wrapper delegating to batter pressure classification."""
    return classify_batter_pressure_multidimensional(
        innings=innings,
        balls_remaining=balls_remaining,
        wickets_remaining=wickets_remaining,
        rrr=rrr,
        delta_rrr=delta_rrr,
        par_deficit=par_deficit,
        recent_drought_runs=recent_drought_runs,
    )


def empirical_bayes_shrinkage(
    observed_metric: float,
    sample_size: int,
    prior_mean: float,
    prior_weight: float = 30.0,
) -> float:
    """Compute Empirical Bayes shrinkage estimate for player rate or event metric.

    Formula:
    theta_shrunk = (n / (n + M)) * theta_obs + (M / (n + M)) * theta_prior

    Where:
    - n: Observed sample size (legal deliveries faced/bowled in high pressure).
    - M: Prior sample weight (pseudo-observations, default 30.0 balls).
    - theta_obs: Raw observed metric (e.g. Strike Rate, Economy Rate, Dot Ball %).
    - theta_prior: Population prior mean across peer cohort.

    Guarantees small samples regress toward the mean without discarding data.
    """
    if sample_size <= 0:
        return float(prior_mean)
    weight_obs = float(sample_size) / (sample_size + prior_weight)
    weight_prior = float(prior_weight) / (sample_size + prior_weight)
    return float(weight_obs * observed_metric + weight_prior * prior_mean)


def evaluate_sample_size_confidence(sample_size: int) -> Dict[str, Any]:
    """Evaluate confidence level and qualification status for a given sample size.

    Tiers:
    - INSUFFICIENT (< 24 balls): Volatility too high; unranked / informational only.
    - PROVISIONAL (24 to 59 balls): Minimum sample threshold; requires heavy shrinkage (M=30).
    - CONFIDENT (>= 60 balls): Robust statistical stability; light shrinkage (M=15).
    """
    if sample_size < 24:
        status = "INSUFFICIENT"
        is_qualified = False
        shrinkage_weight = 40.0
    elif sample_size < 60:
        status = "PROVISIONAL"
        is_qualified = True
        shrinkage_weight = 30.0
    else:
        status = "CONFIDENT"
        is_qualified = True
        shrinkage_weight = 15.0

    return {
        "sample_size": sample_size,
        "status": status,
        "is_qualified": is_qualified,
        "recommended_prior_weight": shrinkage_weight,
    }
