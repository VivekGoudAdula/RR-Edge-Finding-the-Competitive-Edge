"""
Batter Behavioral Pressure Intelligence Module.

Analyzes observable ball-by-ball performance patterns for batters under pressure:
- Post-dot scoring recovery (performance on balls following 2+ consecutive dots)
- Post-wicket team consolidation (performance in first 6 balls after team wicket)
- Drought breakout latency (balls to score or hit boundary after drought)
- Pressure vs Normal performance shift (delta strike rate, dot %, boundary %)
- Match-to-match pressure consistency (standard deviation, IQR)

Strictly relies on observable event occurrences without psychological speculation.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from src.models.behavioral.config import (
    MIN_CONSECUTIVE_DOTS,
    POST_WICKET_WINDOW_BALLS,
    MIN_MATCH_PRESSURE_BALLS_BATTER,
    HIGH_PRESSURE_TIERS,
    NORMAL_PRESSURE_TIERS,
    determine_confidence,
)


def compute_batter_behavioral_metrics(deliveries_df: pd.DataFrame) -> pd.DataFrame:
    """Compute observable behavioral pressure metrics for all batters in deliveries_df.
    
    Args:
        deliveries_df: Ball-by-ball dataframe containing match context and delivery outcomes.
        
    Returns:
        DataFrame of batter behavioral metrics indexed by striker_id.
    """
    df = deliveries_df.copy()
    
    # Ensure correct chronological delivery order
    df = df.sort_values(
        by=['match_id', 'innings', 'overid', 'over_ball_num', 'innings_ball_num']
    ).reset_index(drop=True)
    
    # 1. Flag post-wicket transition window at innings level
    df['is_post_wkt'] = False
    
    # Identify wicket delivery points per match and innings
    wkt_mask = df['is_wicket'] == True
    wkt_events = df[wkt_mask][['match_id', 'innings', 'innings_ball_num']].copy()
    
    # Vectorized post-wicket tagging
    if not wkt_events.empty:
        # Merge to find balls within POST_WICKET_WINDOW_BALLS after any wicket
        merged = pd.merge(
            df[['match_id', 'innings', 'innings_ball_num']].reset_index(),
            wkt_events,
            on=['match_id', 'innings'],
            suffixes=('', '_wkt')
        )
        diff = merged['innings_ball_num'] - merged['innings_ball_num_wkt']
        in_window = (diff > 0) & (diff <= POST_WICKET_WINDOW_BALLS)
        post_wkt_indices = merged.loc[in_window, 'index'].unique()
        df.loc[post_wkt_indices, 'is_post_wkt'] = True
    
    # 2. Extract per-batter sequential events (dots, latency)
    # Filter to legal balls for standard batting analysis
    legal_df = df[df['is_legal_ball'] == True].copy()
    
    # Group by match, innings, striker to identify personal dot sequences
    results: List[Dict[str, Any]] = []
    
    # Group deliveries by striker_id
    striker_groups = legal_df.groupby('striker_id', sort=False)
    
    for striker_id, s_df in striker_groups:
        striker_name = s_df['striker_name'].iloc[0]
        comp_types = list(s_df['competition_type'].unique())
        
        # Overall legal balls faced
        total_balls = len(s_df)
        total_runs = int(s_df['runs'].sum())
        total_dots = int((s_df['runs'] == 0).sum())
        total_boundaries = int(s_df['runs'].isin([4, 6]).sum())
        overall_sr = (total_runs / total_balls * 100.0) if total_balls > 0 else 0.0
        overall_dot_pct = (total_dots / total_balls * 100.0) if total_balls > 0 else 0.0
        overall_boundary_pct = (total_boundaries / total_balls * 100.0) if total_balls > 0 else 0.0
        
        # Group by match and innings for sequential analysis
        post_dot_runs = 0
        post_dot_balls = 0
        post_dot_dots = 0
        post_dot_boundaries = 0
        post_dot_dismissals = 0
        
        latency_to_score_list: List[int] = []
        latency_to_boundary_list: List[int] = []
        
        # Iterate matches for this batter
        for (_, _), match_inn_df in s_df.groupby(['match_id', 'innings'], sort=False):
            runs_arr = match_inn_df['runs'].values
            dismissal_arr = match_inn_df['is_wicket'].values
            
            # Identify personal dot sequences
            current_dot_streak = 0
            in_drought = False
            balls_since_drought = 0
            recorded_score_latency = False
            recorded_boundary_latency = False
            
            for i in range(len(runs_arr)):
                r = runs_arr[i]
                w = dismissal_arr[i]
                
                # Check if this ball was immediately preceded by >= MIN_CONSECUTIVE_DOTS
                if current_dot_streak >= MIN_CONSECUTIVE_DOTS:
                    post_dot_balls += 1
                    post_dot_runs += int(r)
                    if r == 0:
                        post_dot_dots += 1
                    if r in (4, 6):
                        post_dot_boundaries += 1
                    if w:
                        post_dot_dismissals += 1
                        
                # Update drought state and latency tracking
                if current_dot_streak >= MIN_CONSECUTIVE_DOTS and not in_drought:
                    in_drought = True
                    balls_since_drought = 0
                    recorded_score_latency = False
                    recorded_boundary_latency = False
                    
                if in_drought:
                    balls_since_drought += 1
                    if not recorded_score_latency and r > 0:
                        latency_to_score_list.append(balls_since_drought)
                        recorded_score_latency = True
                    if not recorded_boundary_latency and r in (4, 6):
                        latency_to_boundary_list.append(balls_since_drought)
                        recorded_boundary_latency = True
                    if r > 0:
                        in_drought = False
                
                if r == 0:
                    current_dot_streak += 1
                else:
                    current_dot_streak = 0
        
        # Calculate post-dot rates
        post_dot_sr = (post_dot_runs / post_dot_balls * 100.0) if post_dot_balls > 0 else 0.0
        post_dot_dot_pct = (post_dot_dots / post_dot_balls * 100.0) if post_dot_balls > 0 else 0.0
        post_dot_boundary_pct = (post_dot_boundaries / post_dot_balls * 100.0) if post_dot_balls > 0 else 0.0
        post_dot_wicket_pct = (post_dot_dismissals / post_dot_balls * 100.0) if post_dot_balls > 0 else 0.0
        delta_sr_post_dot = post_dot_sr - overall_sr
        
        # Post-wicket consolidation metrics
        pw_df = s_df[s_df['is_post_wkt'] == True]
        pw_balls = len(pw_df)
        pw_runs = int(pw_df['runs'].sum()) if pw_balls > 0 else 0
        pw_dots = int((pw_df['runs'] == 0).sum()) if pw_balls > 0 else 0
        pw_boundaries = int(pw_df['runs'].isin([4, 6]).sum()) if pw_balls > 0 else 0
        pw_dismissals = int(pw_df['is_wicket'].sum()) if pw_balls > 0 else 0
        
        pw_sr = (pw_runs / pw_balls * 100.0) if pw_balls > 0 else 0.0
        pw_dot_pct = (pw_dots / pw_balls * 100.0) if pw_balls > 0 else 0.0
        pw_boundary_pct = (pw_boundaries / pw_balls * 100.0) if pw_balls > 0 else 0.0
        pw_wicket_pct = (pw_dismissals / pw_balls * 100.0) if pw_balls > 0 else 0.0
        
        # Recovery latency
        avg_balls_to_scoring = float(np.mean(latency_to_score_list)) if latency_to_score_list else 0.0
        avg_balls_to_boundary = float(np.mean(latency_to_boundary_list)) if latency_to_boundary_list else 0.0
        
        # Pressure vs Normal Performance Delta
        p_df = s_df[s_df['batter_pressure_tier'].isin(HIGH_PRESSURE_TIERS)]
        n_df = s_df[s_df['batter_pressure_tier'].isin(NORMAL_PRESSURE_TIERS)]
        
        p_balls = len(p_df)
        p_runs = int(p_df['runs'].sum()) if p_balls > 0 else 0
        p_dots = int((p_df['runs'] == 0).sum()) if p_balls > 0 else 0
        p_boundaries = int(p_df['runs'].isin([4, 6]).sum()) if p_balls > 0 else 0
        
        n_balls = len(n_df)
        n_runs = int(n_df['runs'].sum()) if n_balls > 0 else 0
        n_dots = int((n_df['runs'] == 0).sum()) if n_balls > 0 else 0
        n_boundaries = int(n_df['runs'].isin([4, 6]).sum()) if n_balls > 0 else 0
        
        p_sr = (p_runs / p_balls * 100.0) if p_balls > 0 else 0.0
        n_sr = (n_runs / n_balls * 100.0) if n_balls > 0 else 0.0
        p_dot_pct = (p_dots / p_balls * 100.0) if p_balls > 0 else 0.0
        n_dot_pct = (n_dots / n_balls * 100.0) if n_balls > 0 else 0.0
        p_boundary_pct = (p_boundaries / p_balls * 100.0) if p_balls > 0 else 0.0
        n_boundary_pct = (n_boundaries / n_balls * 100.0) if n_balls > 0 else 0.0
        
        delta_sr_pressure_vs_normal = p_sr - n_sr
        delta_dot_pressure_vs_normal = p_dot_pct - n_dot_pct
        delta_boundary_pressure_vs_normal = p_boundary_pct - n_boundary_pct
        
        # Match-to-Match Pressure Consistency
        # Group by match for matches with >= MIN_MATCH_PRESSURE_BALLS_BATTER
        match_sr_list: List[float] = []
        if p_balls > 0:
            for _, m_p_df in p_df.groupby('match_id', sort=False):
                if len(m_p_df) >= MIN_MATCH_PRESSURE_BALLS_BATTER:
                    m_sr = float(m_p_df['runs'].sum() / len(m_p_df) * 100.0)
                    match_sr_list.append(m_sr)
                    
        if len(match_sr_list) >= 3:
            pressure_sr_std = float(np.std(match_sr_list, ddof=1))
            q75, q25 = np.percentile(match_sr_list, [75, 25])
            pressure_sr_iqr = float(q75 - q25)
            qualified_pressure_matches = len(match_sr_list)
        else:
            pressure_sr_std = 0.0
            pressure_sr_iqr = 0.0
            qualified_pressure_matches = len(match_sr_list)
            
        # Evidence confidence determination
        sample_confidence = determine_confidence(post_dot_balls)
        
        # Observable Scoring Acceleration Index (composite non-judgmental response metric)
        # Combines post-dot strike rate shift and post-wicket containment
        # Positive value indicates ability to sustain scoring tempo after disruption
        scoring_resilience_index = round(0.5 * delta_sr_post_dot + 0.5 * delta_sr_pressure_vs_normal, 2)
        
        results.append({
            'striker_id': striker_id,
            'striker_name': striker_name,
            'total_balls': total_balls,
            'overall_strike_rate': round(overall_sr, 2),
            'overall_dot_pct': round(overall_dot_pct, 2),
            'overall_boundary_pct': round(overall_boundary_pct, 2),
            # Post-dot recovery metrics
            'post_dot_balls': post_dot_balls,
            'post_dot_strike_rate': round(post_dot_sr, 2),
            'post_dot_dot_pct': round(post_dot_dot_pct, 2),
            'post_dot_boundary_pct': round(post_dot_boundary_pct, 2),
            'post_dot_wicket_pct': round(post_dot_wicket_pct, 2),
            'delta_sr_post_dot': round(delta_sr_post_dot, 2),
            # Post-wicket consolidation metrics
            'post_wkt_balls': pw_balls,
            'post_wkt_strike_rate': round(pw_sr, 2),
            'post_wkt_dot_pct': round(pw_dot_pct, 2),
            'post_wkt_boundary_pct': round(pw_boundary_pct, 2),
            'post_wkt_wicket_pct': round(pw_wicket_pct, 2),
            # Recovery latency
            'avg_balls_to_scoring': round(avg_balls_to_scoring, 2),
            'avg_balls_to_boundary': round(avg_balls_to_boundary, 2),
            # Pressure vs Normal shift
            'pressure_balls': p_balls,
            'normal_balls': n_balls,
            'pressure_strike_rate': round(p_sr, 2),
            'normal_strike_rate': round(n_sr, 2),
            'delta_sr_pressure_vs_normal': round(delta_sr_pressure_vs_normal, 2),
            'delta_dot_pressure_vs_normal': round(delta_dot_pressure_vs_normal, 2),
            'delta_boundary_pressure_vs_normal': round(delta_boundary_pressure_vs_normal, 2),
            # Consistency
            'qualified_pressure_matches': qualified_pressure_matches,
            'pressure_sr_std': round(pressure_sr_std, 2),
            'pressure_sr_iqr': round(pressure_sr_iqr, 2),
            # Composite & Reliability
            'scoring_resilience_index': scoring_resilience_index,
            'sample_confidence': sample_confidence,
            'has_sufficient_evidence': sample_confidence in [determine_confidence(30), determine_confidence(15)]
        })
        
    res_df = pd.DataFrame(results)
    if not res_df.empty:
        res_df = res_df.sort_values(by='total_balls', ascending=False).reset_index(drop=True)
    return res_df

