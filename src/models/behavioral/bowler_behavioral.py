"""
Bowler Behavioral Pressure Intelligence Module.

Analyzes observable ball-by-ball concession and bounce-back dynamics for bowlers:
- Post-boundary concession response (economy, dot %, boundary % on delivery immediately following a 4 or 6)
- Post-expensive sequence response (performance following 8+ runs in 3 deliveries)
- Cumulative inning over exposure progression (early overs 1-2 vs late overs 3-4 allocation)
- Pressure vs Normal concession shift (delta economy, dot %, wicket impact)
- Match-to-match pressure consistency (standard deviation, IQR)

Strictly relies on observable event occurrences without psychological speculation.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from src.models.behavioral.config import (
    CLUSTER_MIN_RUNS,
    CLUSTER_WINDOW_BALLS,
    EARLY_SPELL_MAX_BALLS,
    MIN_MATCH_PRESSURE_BALLS_BOWLER,
    HIGH_PRESSURE_TIERS,
    NORMAL_PRESSURE_TIERS,
    determine_confidence,
)


def compute_bowler_behavioral_metrics(deliveries_df: pd.DataFrame) -> pd.DataFrame:
    """Compute observable behavioral pressure metrics for all bowlers in deliveries_df.
    
    Args:
        deliveries_df: Ball-by-ball dataframe containing match context and delivery outcomes.
        
    Returns:
        DataFrame of bowler behavioral metrics indexed by bowler_id.
    """
    df = deliveries_df.copy()
    
    # Ensure correct chronological delivery order
    df = df.sort_values(
        by=['match_id', 'innings', 'overid', 'over_ball_num', 'innings_ball_num']
    ).reset_index(drop=True)
    
    # Filter to legal deliveries for bowler balls
    legal_df = df[df['is_legal_ball'] == True].copy()
    
    results: List[Dict[str, Any]] = []
    bowler_groups = legal_df.groupby('bowler_id', sort=False)
    
    for bowler_id, b_df in bowler_groups:
        bowler_name = b_df['bowler_name'].iloc[0]
        
        # Overall legal balls bowled and conceded metrics
        total_balls = len(b_df)
        total_runs = int(b_df['total_delivery_runs'].sum())
        total_dots = int((b_df['total_delivery_runs'] == 0).sum())
        total_boundaries = int(b_df['runs'].isin([4, 6]).sum())
        total_wickets = int(b_df['is_bowler_wkt'].sum())
        
        overall_economy = (total_runs / total_balls * 6.0) if total_balls > 0 else 0.0
        overall_dot_pct = (total_dots / total_balls * 100.0) if total_balls > 0 else 0.0
        overall_boundary_pct = (total_boundaries / total_balls * 100.0) if total_balls > 0 else 0.0
        overall_wicket_pct = (total_wickets / total_balls * 100.0) if total_balls > 0 else 0.0
        
        # 1. Post-Boundary Response (within the same over)
        # 2. Post-Cluster Response
        # 3. Spell Progression (balls 1-12 vs 13-24 in match)
        post_bnd_balls = 0
        post_bnd_runs = 0
        post_bnd_dots = 0
        post_bnd_boundaries = 0
        post_bnd_wickets = 0
        
        post_cluster_balls = 0
        post_cluster_runs = 0
        post_cluster_dots = 0
        
        early_spell_balls = 0
        early_spell_runs = 0
        early_spell_dots = 0
        
        late_spell_balls = 0
        late_spell_runs = 0
        late_spell_dots = 0
        
        for (_, _), match_inn_df in b_df.groupby(['match_id', 'innings'], sort=False):
            runs_arr = match_inn_df['total_delivery_runs'].values
            off_bat_runs = match_inn_df['runs'].values
            wkt_arr = match_inn_df['is_bowler_wkt'].values
            over_arr = match_inn_df['overid'].values
            n_balls = len(runs_arr)
            
            # Spell progression tracking
            for i in range(n_balls):
                ball_num_in_spell = i + 1
                r = runs_arr[i]
                is_dot = (r == 0)
                
                if ball_num_in_spell <= EARLY_SPELL_MAX_BALLS:
                    early_spell_balls += 1
                    early_spell_runs += int(r)
                    if is_dot:
                        early_spell_dots += 1
                else:
                    late_spell_balls += 1
                    late_spell_runs += int(r)
                    if is_dot:
                        late_spell_dots += 1
            
            # Intra-over Post-boundary bounce-back
            for i in range(n_balls - 1):
                # If current ball conceded boundary
                if off_bat_runs[i] in (4, 6):
                    # Check if next ball is in the same over
                    if over_arr[i] == over_arr[i + 1]:
                        post_bnd_balls += 1
                        next_r = int(runs_arr[i + 1])
                        post_bnd_runs += next_r
                        if next_r == 0:
                            post_bnd_dots += 1
                        if off_bat_runs[i + 1] in (4, 6):
                            post_bnd_boundaries += 1
                        if wkt_arr[i + 1]:
                            post_bnd_wickets += 1
                            
            # Rolling 3-ball cluster analysis within innings
            for i in range(CLUSTER_WINDOW_BALLS - 1, n_balls - 1):
                rolling_runs = sum(runs_arr[i - CLUSTER_WINDOW_BALLS + 1 : i + 1])
                if rolling_runs >= CLUSTER_MIN_RUNS:
                    post_cluster_balls += 1
                    post_cluster_runs += int(runs_arr[i + 1])
                    if runs_arr[i + 1] == 0:
                        post_cluster_dots += 1
                        
        # Post-boundary calculations
        post_bnd_econ = (post_bnd_runs / post_bnd_balls * 6.0) if post_bnd_balls > 0 else 0.0
        post_bnd_dot_pct = (post_bnd_dots / post_bnd_balls * 100.0) if post_bnd_balls > 0 else 0.0
        post_bnd_boundary_pct = (post_bnd_boundaries / post_bnd_balls * 100.0) if post_bnd_balls > 0 else 0.0
        post_bnd_wkt_pct = (post_bnd_wickets / post_bnd_balls * 100.0) if post_bnd_balls > 0 else 0.0
        delta_econ_post_boundary = post_bnd_econ - overall_economy
        
        # Post-cluster calculations
        post_cluster_econ = (post_cluster_runs / post_cluster_balls * 6.0) if post_cluster_balls > 0 else 0.0
        post_cluster_dot_pct = (post_cluster_dots / post_cluster_balls * 100.0) if post_cluster_balls > 0 else 0.0
        
        # Spell progression calculations
        early_spell_econ = (early_spell_runs / early_spell_balls * 6.0) if early_spell_balls > 0 else 0.0
        early_spell_dot_pct = (early_spell_dots / early_spell_balls * 100.0) if early_spell_balls > 0 else 0.0
        late_spell_econ = (late_spell_runs / late_spell_balls * 6.0) if late_spell_balls > 0 else 0.0
        late_spell_dot_pct = (late_spell_dots / late_spell_balls * 100.0) if late_spell_balls > 0 else 0.0
        spell_economy_progression = late_spell_econ - early_spell_econ
        
        # Pressure vs Normal Concession Shift
        p_df = b_df[b_df['bowler_pressure_tier'].isin(HIGH_PRESSURE_TIERS)]
        n_df = b_df[b_df['bowler_pressure_tier'].isin(NORMAL_PRESSURE_TIERS)]
        
        p_balls = len(p_df)
        p_runs = int(p_df['total_delivery_runs'].sum()) if p_balls > 0 else 0
        p_dots = int((p_df['total_delivery_runs'] == 0).sum()) if p_balls > 0 else 0
        p_boundaries = int(p_df['runs'].isin([4, 6]).sum()) if p_balls > 0 else 0
        p_wkts = int(p_df['is_bowler_wkt'].sum()) if p_balls > 0 else 0
        
        n_balls = len(n_df)
        n_runs = int(n_df['total_delivery_runs'].sum()) if n_balls > 0 else 0
        n_dots = int((n_df['total_delivery_runs'] == 0).sum()) if n_balls > 0 else 0
        n_boundaries = int(n_df['runs'].isin([4, 6]).sum()) if n_balls > 0 else 0
        n_wkts = int(n_df['is_bowler_wkt'].sum()) if n_balls > 0 else 0
        
        p_econ = (p_runs / p_balls * 6.0) if p_balls > 0 else 0.0
        n_econ = (n_runs / n_balls * 6.0) if n_balls > 0 else 0.0
        p_dot_pct = (p_dots / p_balls * 100.0) if p_balls > 0 else 0.0
        n_dot_pct = (n_dots / n_balls * 100.0) if n_balls > 0 else 0.0
        p_bnd_pct = (p_boundaries / p_balls * 100.0) if p_balls > 0 else 0.0
        n_bnd_pct = (n_boundaries / n_balls * 100.0) if n_balls > 0 else 0.0
        p_wkt_pct = (p_wkts / p_balls * 100.0) if p_balls > 0 else 0.0
        n_wkt_pct = (n_wkts / n_balls * 100.0) if n_balls > 0 else 0.0
        
        delta_econ_pressure_vs_normal = p_econ - n_econ
        delta_dot_pressure_vs_normal = p_dot_pct - n_dot_pct
        delta_boundary_pressure_vs_normal = p_bnd_pct - n_bnd_pct
        delta_wkt_pressure_vs_normal = p_wkt_pct - n_wkt_pct
        
        # Match-to-Match Pressure Consistency
        match_econ_list: List[float] = []
        if p_balls > 0:
            for _, m_p_df in p_df.groupby('match_id', sort=False):
                if len(m_p_df) >= MIN_MATCH_PRESSURE_BALLS_BOWLER:
                    m_econ = float(m_p_df['total_delivery_runs'].sum() / len(m_p_df) * 6.0)
                    match_econ_list.append(m_econ)
                    
        if len(match_econ_list) >= 3:
            pressure_econ_std = float(np.std(match_econ_list, ddof=1))
            q75, q25 = np.percentile(match_econ_list, [75, 25])
            pressure_econ_iqr = float(q75 - q25)
            qualified_pressure_matches = len(match_econ_list)
        else:
            pressure_econ_std = 0.0
            pressure_econ_iqr = 0.0
            qualified_pressure_matches = len(match_econ_list)
            
        sample_confidence = determine_confidence(post_bnd_balls)
        
        # Observable Bounce-Back Index
        # Positive score indicates containment after boundary (economy drops or dots increase relative to expectation)
        bounceback_index = round(overall_economy - post_bnd_econ, 2)
        
        results.append({
            'bowler_id': bowler_id,
            'bowler_name': bowler_name,
            'total_balls': total_balls,
            'overall_economy': round(overall_economy, 2),
            'overall_dot_pct': round(overall_dot_pct, 2),
            'overall_boundary_pct': round(overall_boundary_pct, 2),
            'overall_wicket_pct': round(overall_wicket_pct, 2),
            # Post-boundary bounce-back
            'post_boundary_legal_balls': post_bnd_balls,
            'post_boundary_economy': round(post_bnd_econ, 2),
            'post_boundary_dot_pct': round(post_bnd_dot_pct, 2),
            'post_boundary_boundary_pct': round(post_bnd_boundary_pct, 2),
            'post_boundary_wicket_pct': round(post_bnd_wkt_pct, 2),
            'delta_econ_post_boundary': round(delta_econ_post_boundary, 2),
            'bounceback_index': bounceback_index,
            # Post-cluster
            'post_cluster_balls': post_cluster_balls,
            'post_cluster_economy': round(post_cluster_econ, 2),
            'post_cluster_dot_pct': round(post_cluster_dot_pct, 2),
            # Spell progression
            'early_spell_balls': early_spell_balls,
            'early_spell_economy': round(early_spell_econ, 2),
            'early_spell_dot_pct': round(early_spell_dot_pct, 2),
            'late_spell_balls': late_spell_balls,
            'late_spell_economy': round(late_spell_econ, 2),
            'late_spell_dot_pct': round(late_spell_dot_pct, 2),
            'spell_economy_progression': round(spell_economy_progression, 2),
            # Pressure vs Normal shift
            'pressure_balls': p_balls,
            'normal_balls': n_balls,
            'pressure_economy': round(p_econ, 2),
            'normal_economy': round(n_econ, 2),
            'delta_econ_pressure_vs_normal': round(delta_econ_pressure_vs_normal, 2),
            'delta_dot_pressure_vs_normal': round(delta_dot_pressure_vs_normal, 2),
            'delta_boundary_pressure_vs_normal': round(delta_boundary_pressure_vs_normal, 2),
            'delta_wkt_pressure_vs_normal': round(delta_wkt_pressure_vs_normal, 2),
            # Consistency
            'qualified_pressure_matches': qualified_pressure_matches,
            'pressure_econ_std': round(pressure_econ_std, 2),
            'pressure_econ_iqr': round(pressure_econ_iqr, 2),
            # Confidence
            'sample_confidence': sample_confidence,
            'has_sufficient_evidence': sample_confidence in [determine_confidence(30), determine_confidence(15)]
        })
        
    res_df = pd.DataFrame(results)
    if not res_df.empty:
        res_df = res_df.sort_values(by='total_balls', ascending=False).reset_index(drop=True)
    return res_df

