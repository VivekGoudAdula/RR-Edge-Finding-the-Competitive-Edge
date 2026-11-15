"""
Reliability, match-level consistency, and Empirical Bayes shrinkage models for RR EDGE.

Phase 2.3: Implements match-level performance aggregation, consistency dispersion metrics,
Empirical Bayes shrinkage sensitivity analysis, statistical posterior credible intervals,
and multidimensional evidence tier classification.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats


# -----------------------------------------------------------------------------
# 1. MATCH-LEVEL CONSISTENCY METHODOLOGY
# -----------------------------------------------------------------------------

def compute_batter_match_consistency(
    df_pressure_deliveries: pd.DataFrame,
    min_balls_per_match: int = 3,
) -> pd.DataFrame:
    """Aggregate batter pressure performance at match level before measuring consistency.

    Computes:
    - Number of distinct pressure matches.
    - Match strike rate standard deviation (ddof=1 across matches with >= min_balls_per_match).
    - Match strike rate median and interquartile range (IQR).
    - Benchmark pass rate: percentage of pressure matches with SR >= 130.0 (or >= 15 runs).

    Parameters
    ----------
    df_pressure_deliveries : pd.DataFrame
        Deliveries where batter_pressure_tier is HIGH or EXTREME.
        Must contain striker_id, striker_name, match_id, is_ball_faced, batter_runs.
    min_balls_per_match : int, optional
        Minimum balls faced in a match to evaluate match rate metrics (default: 3).

    Returns
    -------
    pd.DataFrame
        Match consistency metrics indexed by striker_id.
    """
    if len(df_pressure_deliveries) == 0:
        return pd.DataFrame()

    # Step 1: Match-level aggregation
    match_grp = df_pressure_deliveries.groupby(["striker_id", "striker_name", "match_id"])
    match_df = pd.DataFrame(
        {
            "match_balls": match_grp["is_ball_faced"].sum(),
            "match_runs": match_grp["batter_runs"].sum(),
        }
    ).reset_index()

    match_df["match_sr"] = np.where(
        match_df["match_balls"] > 0,
        (match_df["match_runs"] * 100.0) / match_df["match_balls"],
        np.nan,
    )

    # Benchmark: Match SR >= 130.0 or match runs >= 15 with SR >= 115.0
    match_df["match_pass"] = (match_df["match_sr"] >= 130.0) | (
        (match_df["match_runs"] >= 15) & (match_df["match_sr"] >= 115.0)
    )

    # Step 2: Player-level aggregation across matches
    records: List[Dict[str, Any]] = []
    for (sid, sname), p_matches in match_df.groupby(["striker_id", "striker_name"]):
        total_p_matches = len(p_matches)
        qual_matches = p_matches[p_matches["match_balls"] >= min_balls_per_match]
        n_qual = len(qual_matches)

        if n_qual >= 2:
            sr_std = float(qual_matches["match_sr"].std(ddof=1))
        else:
            sr_std = np.nan

        if n_qual >= 1:
            sr_median = float(qual_matches["match_sr"].median())
            q75 = float(qual_matches["match_sr"].quantile(0.75))
            q25 = float(qual_matches["match_sr"].quantile(0.25))
            sr_iqr = q75 - q25
            pass_rate = float(qual_matches["match_pass"].mean() * 100.0)
        else:
            sr_median = np.nan
            sr_iqr = np.nan
            pass_rate = np.nan

        records.append(
            {
                "striker_id": sid,
                "striker_name": sname,
                "pressure_matches_count": total_p_matches,
                "pressure_matches_evaluated": n_qual,
                "pressure_match_sr_std": sr_std,
                "pressure_match_sr_median": sr_median,
                "pressure_match_sr_iqr": sr_iqr,
                "pressure_match_pass_rate": pass_rate,
            }
        )

    return pd.DataFrame(records)


def compute_bowler_match_consistency(
    df_pressure_deliveries: pd.DataFrame,
    min_balls_per_match: int = 3,
) -> pd.DataFrame:
    """Aggregate bowler pressure performance at match level before measuring consistency.

    Computes:
    - Number of distinct pressure matches.
    - Match economy standard deviation (ddof=1 across matches with >= min_balls_per_match).
    - Match economy median and IQR.
    - Benchmark pass rate: percentage of pressure matches with economy <= 9.0 (or >= 1 wkt and economy <= 10.5).

    Parameters
    ----------
    df_pressure_deliveries : pd.DataFrame
        Deliveries where bowler_pressure_tier is HIGH or EXTREME.
        Must contain bowler_id, bowler_name, match_id, is_legal_bowler_ball, bowler_runs_conceded, bowler_wicket_credit.
    min_balls_per_match : int, optional
        Minimum legal balls bowled in a match to evaluate match rate metrics (default: 3).

    Returns
    -------
    pd.DataFrame
        Match consistency metrics indexed by bowler_id.
    """
    if len(df_pressure_deliveries) == 0:
        return pd.DataFrame()

    # Step 1: Match-level aggregation
    match_grp = df_pressure_deliveries.groupby(["bowler_id", "bowler_name", "match_id"])
    match_df = pd.DataFrame(
        {
            "match_legal_balls": match_grp["is_legal_bowler_ball"].sum(),
            "match_runs_conceded": match_grp["bowler_runs_conceded"].sum(),
            "match_wickets": match_grp["bowler_wicket_credit"].sum(),
        }
    ).reset_index()

    match_df["match_economy"] = np.where(
        match_df["match_legal_balls"] > 0,
        (match_df["match_runs_conceded"] * 6.0) / match_df["match_legal_balls"],
        np.nan,
    )

    # Benchmark: Match Economy <= 9.0 (or >= 1 wicket and economy <= 10.5)
    match_df["match_pass"] = (match_df["match_economy"] <= 9.0) | (
        (match_df["match_wickets"] >= 1) & (match_df["match_economy"] <= 10.5)
    )

    # Step 2: Player-level aggregation across matches
    records: List[Dict[str, Any]] = []
    for (bid, bname), p_matches in match_df.groupby(["bowler_id", "bowler_name"]):
        total_p_matches = len(p_matches)
        qual_matches = p_matches[p_matches["match_legal_balls"] >= min_balls_per_match]
        n_qual = len(qual_matches)

        if n_qual >= 2:
            econ_std = float(qual_matches["match_economy"].std(ddof=1))
        else:
            econ_std = np.nan

        if n_qual >= 1:
            econ_median = float(qual_matches["match_economy"].median())
            q75 = float(qual_matches["match_economy"].quantile(0.75))
            q25 = float(qual_matches["match_economy"].quantile(0.25))
            econ_iqr = q75 - q25
            pass_rate = float(qual_matches["match_pass"].mean() * 100.0)
        else:
            econ_median = np.nan
            econ_iqr = np.nan
            pass_rate = np.nan

        records.append(
            {
                "bowler_id": bid,
                "bowler_name": bname,
                "pressure_matches_count": total_p_matches,
                "pressure_matches_evaluated": n_qual,
                "pressure_match_econ_std": econ_std,
                "pressure_match_econ_median": econ_median,
                "pressure_match_econ_iqr": econ_iqr,
                "pressure_match_pass_rate": pass_rate,
            }
        )

    return pd.DataFrame(records)


# -----------------------------------------------------------------------------
# 2. EMPIRICAL BAYES SHRINKAGE & POSTERIOR UNCERTAINTY
# -----------------------------------------------------------------------------

def empirical_bayes_shrink(
    observed_metric: float,
    sample_size: int,
    prior_mean: float,
    prior_weight: float = 30.0,
) -> float:
    """Compute Empirical Bayes point estimate for a rate or event metric.

    Formula:
    theta_shrunk = (n / (n + M)) * theta_obs + (M / (n + M)) * theta_prior

    Statistical Interpretation:
    - n: Observed sample size (balls faced or legal balls bowled).
    - M: Pseudo-observations assigned to the population prior.
    - Reflects expected posterior mean under a conjugate prior.

    Parameters
    ----------
    observed_metric : float
        Raw observed rate metric (e.g. SR, Economy).
    sample_size : int
        Sample size (balls).
    prior_mean : float
        Population mean across the competition peer cohort.
    prior_weight : float, optional
        Prior pseudo-observation strength M (default: 30.0).

    Returns
    -------
    float
        Shrunk performance metric.
    """
    if sample_size <= 0 or pd.isna(observed_metric):
        return float(prior_mean)
    w_obs = float(sample_size) / (sample_size + prior_weight)
    w_prior = float(prior_weight) / (sample_size + prior_weight)
    return float(w_obs * observed_metric + w_prior * prior_mean)


def compute_beta_binomial_credible_interval(
    successes: int,
    trials: int,
    prior_alpha: float = 2.0,
    prior_beta: float = 8.0,
    confidence_level: float = 0.95,
) -> Tuple[float, float, float]:
    """Compute exact Bayesian posterior mean and credible interval for event probabilities.

    Used for Dot Ball % and Boundary Ball % under a Beta-Binomial conjugate model:
    Posterior ~ Beta(alpha + k, beta + n - k).

    Parameters
    ----------
    successes : int
        Count of events (e.g. dot balls or boundaries).
    trials : int
        Total trials (balls faced or legal balls bowled).
    prior_alpha : float, optional
        Prior shape parameter alpha (default: 2.0).
    prior_beta : float, optional
        Prior shape parameter beta (default: 8.0).
    confidence_level : float, optional
        Bayesian credible interval mass (default: 0.95).

    Returns
    -------
    Tuple[float, float, float]
        (posterior_mean_pct, lower_credible_bound_pct, upper_credible_bound_pct) in percentage.
    """
    alpha_post = prior_alpha + max(0, successes)
    beta_post = prior_beta + max(0, trials - successes)

    # Posterior distribution
    dist = stats.beta(alpha_post, beta_post)
    post_mean = float(dist.mean() * 100.0)

    # Equal-tailed credible interval
    tail = (1.0 - confidence_level) / 2.0
    lower = float(dist.ppf(tail) * 100.0)
    upper = float(dist.ppf(1.0 - tail) * 100.0)

    return post_mean, lower, upper


def compute_rate_uncertainty_interval(
    observed_rate: float,
    sample_size: int,
    prior_mean: float,
    prior_weight: float = 30.0,
    population_std: float = 25.0,
    confidence_level: float = 0.95,
) -> Tuple[float, float, float]:
    """Compute Empirical Bayes normal-conjugate uncertainty interval for continuous rates.

    Statistical Derivation & Assumptions:
    - Likelihood: Assumes sample mean rate asymptotically follows Normal likelihood
      via the Central Limit Theorem: x_bar ~ N(theta, sigma_0^2 / n).
    - Prior: Conjugate Normal prior on true rate theta ~ N(mu_0, sigma_0^2 / M).
    - Posterior: theta | x_bar ~ N( (n*x_bar + M*mu_0)/(n+M), sigma_0^2 / (n+M) ).
    - Posterior Standard Error: sigma_post = population_std / sqrt(sample_size + prior_weight).
    - Interval: [shrunk - z_crit * sigma_post, shrunk + z_crit * sigma_post].

    Limitations & Audit Disclosures:
    - Discrete Delivery Runs: Individual ball outcomes are discrete {0,1,2,3,4,6}, not Normal.
    - Intra-Over Correlation: Consecutive deliveries within an over exhibit tactical autocorrelation.
    - Bounded Support: Strike rates and economies cannot be negative (clamped at 0.0).
    - Interpretation: This represents an Empirical Bayes normal-conjugate uncertainty interval
      under CLT asymptotics, rather than an exact discrete compound-Poisson posterior.

    Parameters
    ----------
    observed_rate : float
        Observed Strike Rate or Economy Rate.
    sample_size : int
        Sample size (balls).
    prior_mean : float
        Population mean across peer players.
    prior_weight : float, optional
        Prior weight M (default: 30.0).
    population_std : float, optional
        Observed standard deviation across peer players (default: 25.0).
    confidence_level : float, optional
        Credible mass level (default: 0.95).

    Returns
    -------
    Tuple[float, float, float]
        (shrunk_estimate, lower_bound, upper_bound).
    """
    if sample_size <= 0 or pd.isna(observed_rate):
        shrunk = float(prior_mean)
        eff_n = prior_weight
    else:
        shrunk = empirical_bayes_shrink(observed_rate, sample_size, prior_mean, prior_weight)
        eff_n = sample_size + prior_weight

    post_se = population_std / np.sqrt(eff_n)
    z_crit = float(stats.norm.ppf(1.0 - (1.0 - confidence_level) / 2.0))

    lower = max(0.0, shrunk - z_crit * post_se)
    upper = shrunk + z_crit * post_se
    return shrunk, lower, upper


def compute_posterior_predictive_interval(
    observed_rate: float,
    sample_size: int,
    future_balls: int,
    prior_mean: float,
    prior_weight: float = 30.0,
    delivery_std: float = 172.0,
    confidence_level: float = 0.95,
) -> Tuple[float, float, float]:
    """Compute Posterior Predictive Interval for future observed match performance over m balls.

    Statistical Derivation:
    - Measures where an empirical sample average over m future balls Y_future is expected to fall:
      Var(Y_future | data) = Var(theta | data) + Var(Y_future | theta)
                          = (delivery_std^2) / (n + M) + (delivery_std^2) / future_balls
    - Predictive SE: sigma_pred = delivery_std * sqrt( 1/(n + M) + 1/future_balls ).
    - Predictive Interval: [shrunk - z_crit * sigma_pred, shrunk + z_crit * sigma_pred].

    Parameters
    ----------
    observed_rate : float
        Historical observed rate (Strike Rate or Economy Rate).
    sample_size : int
        Historical sample size n (balls).
    future_balls : int
        Number of future balls m to predict.
    prior_mean : float
        Cohort prior mean.
    prior_weight : float, optional
        Prior shrinkage weight M (default: 30.0).
    delivery_std : float, optional
        Standard deviation of individual delivery outcomes on rate scale
        (default: 172.0 for strike rate, 11.4 for economy).
    confidence_level : float, optional
        Nominal predictive coverage mass (default: 0.95).

    Returns
    -------
    Tuple[float, float, float]
        (shrunk_point_estimate, predictive_lower_bound, predictive_upper_bound).
    """
    if sample_size <= 0 or pd.isna(observed_rate):
        shrunk = float(prior_mean)
        eff_n = prior_weight
    else:
        shrunk = empirical_bayes_shrink(observed_rate, sample_size, prior_mean, prior_weight)
        eff_n = sample_size + prior_weight

    m_future = max(1, future_balls)
    pred_var = (delivery_std**2) * (1.0 / eff_n + 1.0 / m_future)
    pred_se = np.sqrt(pred_var)
    z_crit = float(stats.norm.ppf(1.0 - (1.0 - confidence_level) / 2.0))

    lower = max(0.0, shrunk - z_crit * pred_se)
    upper = shrunk + z_crit * pred_se
    return shrunk, lower, upper


def empirical_bayes_shrink_by_format(
    observed_metric: float,
    sample_size: int,
    format_type: str,
    discipline: str = "batter",
    prior_weight: float = 30.0,
) -> float:
    """Compute format-specific Empirical Bayes shrinkage using format-calibrated priors.

    Calibrated Population Priors:
    - Batting Strike Rate under pressure: IPL = 135.3, T20I = 118.0.
    - Bowling Economy Rate under pressure: IPL = 11.4, T20I = 10.2.

    Parameters
    ----------
    observed_metric : float
        Raw observed rate metric (Strike Rate or Economy Rate).
    sample_size : int
        Sample size (balls faced or legal balls bowled).
    format_type : str
        'IPL' or 'T20I'.
    discipline : str, optional
        'batter' or 'bowler' (default: 'batter').
    prior_weight : float, optional
        Prior pseudo-observation weight M (default: 30.0).

    Returns
    -------
    float
        Shrunk metric calibrated to format environment.
    """
    format_upper = str(format_type).upper()
    if discipline == "bowler":
        prior_mean = 11.4 if format_upper == "IPL" else 10.2
    else:
        prior_mean = 135.3 if format_upper == "IPL" else 118.0

    return empirical_bayes_shrink(observed_metric, sample_size, prior_mean, prior_weight)


def evaluate_holdout_shrinkage_grid(
    qual_stints_df: pd.DataFrame,
    metric_type: str = "strike_rate",
    m_values: Optional[List[float]] = None,
    prior_mean: Optional[float] = None,
    min_balls_half: int = 10,
) -> pd.DataFrame:
    """Evaluate out-of-sample prediction error across candidate shrinkage strengths M.

    Splits each qualified player's match stints chronologically 50/50.
    Uses first-half shrunk performance to predict second-half observed performance.

    Parameters
    ----------
    qual_stints_df : pd.DataFrame
        DataFrame with columns [player_id, match_id, match_balls, match_runs].
    metric_type : str, optional
        'strike_rate' or 'economy' (default: 'strike_rate').
    m_values : List[float], optional
        List of candidate M values to benchmark.
    prior_mean : float, optional
        Cohort prior mean (default: 130.0 for SR, 9.80 for Economy).
    min_balls_half : int, optional
        Minimum balls in each half for inclusion (default: 10).

    Returns
    -------
    pd.DataFrame
        Summary table comparing MAE, RMSE, and bias across candidate M values.
    """
    if m_values is None:
        m_values = [0.0, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0, 100.0]
    if prior_mean is None:
        prior_mean = 130.0 if metric_type == "strike_rate" else 9.80

    id_col = "striker_id" if "striker_id" in qual_stints_df.columns else "bowler_id"
    records: List[Dict[str, Any]] = []

    for pid, p_matches in qual_stints_df.groupby(id_col):
        n_m = len(p_matches)
        if n_m < 2:
            continue
        n_first = n_m // 2
        first_half = p_matches.iloc[:n_first]
        second_half = p_matches.iloc[n_first:]

        n1 = first_half["match_balls"].sum()
        r1 = first_half["match_runs"].sum()
        n2 = second_half["match_balls"].sum()
        r2 = second_half["match_runs"].sum()

        if n1 >= min_balls_half and n2 >= min_balls_half:
            rate1 = (r1 * 100.0) / n1 if metric_type == "strike_rate" else (r1 * 6.0) / n1
            rate2 = (r2 * 100.0) / n2 if metric_type == "strike_rate" else (r2 * 6.0) / n2
            records.append({"player_id": pid, "n1": n1, "rate1": rate1, "n2": n2, "rate2": rate2})

    if len(records) == 0:
        return pd.DataFrame()

    ho_df = pd.DataFrame(records)
    results = []
    for m in m_values:
        pred_rates = [
            empirical_bayes_shrink(row["rate1"], int(row["n1"]), prior_mean, prior_weight=m)
            for _, row in ho_df.iterrows()
        ]
        diffs = np.array(pred_rates) - ho_df["rate2"].values
        mae = float(np.mean(np.abs(diffs)))
        rmse = float(np.sqrt(np.mean(diffs**2)))
        bias = float(np.mean(diffs))
        spread = float(np.std(pred_rates))
        corr = float(np.corrcoef(pred_rates, ho_df["rate2"].values)[0, 1]) if len(ho_df) > 1 else np.nan
        results.append({
            "M": m,
            "sample_players": len(ho_df),
            "holdout_mae": round(mae, 2),
            "holdout_rmse": round(rmse, 2),
            "mean_bias": round(bias, 2),
            "shrunk_std": round(spread, 2),
            "test_correlation": round(corr, 3),
        })

    return pd.DataFrame(results)


def evaluate_three_way_chronological_holdout(
    deliveries_df: pd.DataFrame,
    matches_df: pd.DataFrame,
    discipline: str = "batter",
    m_values: Optional[List[float]] = None,
    min_balls_period: int = 15,
) -> Dict[str, pd.DataFrame]:
    """Execute a strict 3-way chronological holdout validation (Train 60%, Val 20%, Test 20%).

    Guarantees:
    - Train (60%) is used for base player stats and prior estimation.
    - Validation (20%) is used for hyperparameter M benchmarking.
    - Test (20%) is reserved untouched for final unbiased verification.

    Parameters
    ----------
    deliveries_df : pd.DataFrame
        Deliveries DataFrame with match_id, runs, extras_type, batter/bowler IDs.
    matches_df : pd.DataFrame
        Matches DataFrame with match_id and match_date.
    discipline : str, optional
        'batter' or 'bowler' (default: 'batter').
    m_values : List[float], optional
        Candidate M values.
    min_balls_period : int, optional
        Minimum balls in period for inclusion (default: 15).

    Returns
    -------
    Dict[str, pd.DataFrame]
        Dictionary with 'validation_results' and 'test_results'.
    """
    if m_values is None:
        m_values = [0.0, 10.0, 20.0, 25.0, 30.0, 45.0, 60.0, 100.0]

    # Chronological sort
    matches_sorted = matches_df[["match_id", "match_date"]].drop_duplicates("match_id").sort_values("match_date")
    n_m = len(matches_sorted)
    n_tr = int(n_m * 0.60)
    n_v = int(n_m * 0.20)

    tr_mids = set(matches_sorted.iloc[:n_tr]["match_id"])
    v_mids = set(matches_sorted.iloc[n_tr:n_tr + n_v]["match_id"])
    te_mids = set(matches_sorted.iloc[n_tr + n_v:]["match_id"])

    # Prepare deliveries
    if discipline == "bowler":
        from src.models.bowler_performance import prepare_bowler_delivery_attributes
        prep = prepare_bowler_delivery_attributes(deliveries_df)
        legal = prep[prep["is_legal_bowler_ball"] & prep["is_bowler_pressure"]].copy()
        id_col = "bowler_id"
        vol_col = "is_legal_bowler_ball"
        run_col = "bowler_runs_conceded"
        mult = 6.0
    else:
        from src.models.batter_performance import prepare_batter_delivery_attributes
        prep = prepare_batter_delivery_attributes(deliveries_df)
        legal = prep[prep["is_ball_faced"] & prep["is_pressure"]].copy()
        id_col = "striker_id"
        vol_col = "is_ball_faced"
        run_col = "batter_runs"
        mult = 100.0

    # 1. Validation split: Train -> Val
    tr_deliv = legal[legal["match_id"].isin(tr_mids)]
    v_deliv = legal[legal["match_id"].isin(v_mids)]
    prior_tr = (tr_deliv[run_col].sum() * mult) / max(1, len(tr_deliv))

    tr_p = tr_deliv.groupby(id_col).agg(n1=(vol_col, "count"), r1=(run_col, "sum"))
    v_p = v_deliv.groupby(id_col).agg(n2=(vol_col, "count"), r2=(run_col, "sum"))
    val_merged = tr_p.join(v_p, how="inner")
    val_merged = val_merged[(val_merged["n1"] >= min_balls_period) & (val_merged["n2"] >= min_balls_period)].copy()
    val_merged["rate1"] = (val_merged["r1"] * mult) / val_merged["n1"]
    val_merged["rate2"] = (val_merged["r2"] * mult) / val_merged["n2"]

    val_res = []
    for m in m_values:
        preds = [empirical_bayes_shrink(r["rate1"], int(r["n1"]), prior_tr, prior_weight=m) for _, r in val_merged.iterrows()]
        diffs = np.array(preds) - val_merged["rate2"].values
        mae = float(np.mean(np.abs(diffs)))
        rmse = float(np.sqrt(np.mean(diffs**2)))
        spread = float(np.std(preds))
        corr = float(np.corrcoef(preds, val_merged["rate2"].values)[0, 1]) if len(val_merged) > 1 else np.nan
        val_res.append({"M": m, "players": len(val_merged), "rmse": round(rmse, 2), "mae": round(mae, 2), "corr": round(corr, 3), "shrunk_sd": round(spread, 2)})

    # 2. Final Test split: (Train + Val) -> Test
    tv_deliv = legal[legal["match_id"].isin(tr_mids | v_mids)]
    te_deliv = legal[legal["match_id"].isin(te_mids)]
    prior_tv = (tv_deliv[run_col].sum() * mult) / max(1, len(tv_deliv))

    tv_p = tv_deliv.groupby(id_col).agg(n1=(vol_col, "count"), r1=(run_col, "sum"))
    te_p = te_deliv.groupby(id_col).agg(n2=(vol_col, "count"), r2=(run_col, "sum"))
    te_merged = tv_p.join(te_p, how="inner")
    te_merged = te_merged[(te_merged["n1"] >= min_balls_period) & (te_merged["n2"] >= min_balls_period)].copy()
    te_merged["rate1"] = (te_merged["r1"] * mult) / te_merged["n1"]
    te_merged["rate2"] = (te_merged["r2"] * mult) / te_merged["n2"]

    te_res = []
    for m in m_values:
        preds = [empirical_bayes_shrink(r["rate1"], int(r["n1"]), prior_tv, prior_weight=m) for _, r in te_merged.iterrows()]
        diffs = np.array(preds) - te_merged["rate2"].values
        mae = float(np.mean(np.abs(diffs)))
        rmse = float(np.sqrt(np.mean(diffs**2)))
        spread = float(np.std(preds))
        corr = float(np.corrcoef(preds, te_merged["rate2"].values)[0, 1]) if len(te_merged) > 1 else np.nan
        te_res.append({"M": m, "players": len(te_merged), "rmse": round(rmse, 2), "mae": round(mae, 2), "corr": round(corr, 3), "shrunk_sd": round(spread, 2)})

    return {"validation_results": pd.DataFrame(val_res), "test_results": pd.DataFrame(te_res)}


def evaluate_shrinkage_sensitivity(
    player_df: pd.DataFrame,
    metric_col: str,
    sample_size_col: str,
    prior_mean: float,
    m_values: List[float] = [10.0, 15.0, 20.0, 30.0, 45.0, 60.0],
) -> pd.DataFrame:
    """Evaluate metric and rank sensitivity across varying prior strengths M.

    Parameters
    ----------
    player_df : pd.DataFrame
        Player summary DataFrame.
    metric_col : str
        Name of metric column to shrink (e.g. 'pressure_strike_rate').
    sample_size_col : str
        Name of sample size column (e.g. 'pressure_balls_faced').
    prior_mean : float
        Prior benchmark mean.
    m_values : List[float], optional
        List of candidate M values.

    Returns
    -------
    pd.DataFrame
        DataFrame with original metric, shrunk metrics for each M, and rank delta analysis.
    """
    df_out = player_df[["striker_id" if "striker_id" in player_df.columns else "bowler_id",
                       "striker_name" if "striker_name" in player_df.columns else "bowler_name",
                       sample_size_col, metric_col]].copy()

    for m in m_values:
        col_name = f"shrunk_m{int(m)}"
        df_out[col_name] = [
            empirical_bayes_shrink(val, n, prior_mean, prior_weight=m)
            for val, n in zip(df_out[metric_col], df_out[sample_size_col])
        ]
        df_out[f"rank_m{int(m)}"] = df_out[col_name].rank(ascending=False, method="min")

    return df_out


# -----------------------------------------------------------------------------
# 3. EVIDENCE TIER CLASSIFICATION
# -----------------------------------------------------------------------------

def classify_evidence_tier(
    sample_size: int,
    distinct_matches: int,
    distinct_competitions: int,
) -> Dict[str, Any]:
    """Classify statistical evidence strength across volume, match breadth, and competition breadth.

    Evidence Tiers:
    - CONFIDENT_EVIDENCE: >= 60 balls across >= 8 distinct matches and >= 2 tournaments.
    - MODERATE_EVIDENCE: >= 24 balls across >= 4 distinct matches.
    - PROVISIONAL_EVIDENCE: 12 to 23 balls across >= 2 matches.
    - INSUFFICIENT_EVIDENCE: < 12 balls (data too sparse for reliable inference).

    Parameters
    ----------
    sample_size : int
        Number of pressure deliveries faced or bowled.
    distinct_matches : int
        Number of unique matches with pressure exposure.
    distinct_competitions : int
        Number of unique tournaments / series.

    Returns
    -------
    Dict[str, Any]
        Evidence tier and recommended prior shrinkage strength.
    """
    if sample_size >= 60 and distinct_matches >= 8 and distinct_competitions >= 2:
        tier = "CONFIDENT_EVIDENCE"
        rec_m = 15.0
        is_reliable = True
    elif sample_size >= 24 and distinct_matches >= 4:
        tier = "MODERATE_EVIDENCE"
        rec_m = 30.0
        is_reliable = True
    elif sample_size >= 12 and distinct_matches >= 2:
        tier = "PROVISIONAL_EVIDENCE"
        rec_m = 45.0
        is_reliable = False
    else:
        tier = "INSUFFICIENT_EVIDENCE"
        rec_m = 60.0
        is_reliable = False

    return {
        "evidence_tier": tier,
        "is_reliable": is_reliable,
        "recommended_m": rec_m,
        "sample_size": sample_size,
        "distinct_matches": distinct_matches,
        "distinct_competitions": distinct_competitions,
    }

