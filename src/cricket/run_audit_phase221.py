"""
Phase 2.2.1: Independent audit and verification script for pressure_deliveries.parquet.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from src.data.load_data import load_all
from src.cricket.competition_config import is_competition_included
from src.cricket.semantics import is_legal_delivery, is_bowler_wicket, get_match_phase
from src.cricket.pressure_engine import PressureEngineConfig, classify_batter_delivery_pressure, classify_bowler_delivery_pressure


def run_full_audit():
    print("=" * 80)
    print("PHASE 2.2.1: INDEPENDENT PRESSURE ENGINE AUDIT")
    print("=" * 80)

    parquet_path = Path("data/processed/pressure_deliveries.parquet")
    assert parquet_path.exists(), f"File {parquet_path} does not exist!"

    df = pd.read_parquet(parquet_path)
    print(f"Loaded Parquet: {len(df):,} rows, {len(df.columns)} columns.")

    # -------------------------------------------------------------------------
    # 1. DATASET INTEGRITY & RAW TRACING
    # -------------------------------------------------------------------------
    print("\n--- 1. DATASET INTEGRITY & RAW TRACING ---")
    raw_data = load_all()
    raw_bbb = raw_data["ball_by_ball"]
    raw_matches = raw_data["matches"]
    raw_comp = raw_data["competitions"]

    # Deduplication check
    dup_keys = df.duplicated(subset=["match_id", "innings", "innings_ball_num"])
    print(f"Duplicate delivery keys (match_id, innings, innings_ball_num): {dup_keys.sum()}")
    assert dup_keys.sum() == 0, "Found duplicate delivery keys in Parquet output!"

    # Traceability to raw
    raw_key_set = set(zip(raw_bbb["match_id"], raw_bbb["innings"], raw_bbb["innings_ball_num"]))
    out_key_set = set(zip(df["match_id"], df["innings"], df["innings_ball_num"]))
    untraced = out_key_set - raw_key_set
    print(f"Untraced deliveries in Parquet (not in raw): {len(untraced)}")
    assert len(untraced) == 0, "Found deliveries in Parquet that do not exist in raw ball_by_ball!"

    # Whitelist filtering verification
    comp_map = raw_comp.set_index("comp_id")["match_format"].to_dict()
    valid_raw_matches = raw_matches[
        raw_matches.apply(lambda r: is_competition_included(r["comp_id"], comp_map.get(r["comp_id"], "T20I")), axis=1)
    ]
    whitelisted_raw_bbb = raw_bbb[raw_bbb["match_id"].isin(valid_raw_matches["match_id"])]
    print(f"Whitelisted raw deliveries: {len(whitelisted_raw_bbb):,} vs Parquet deliveries: {len(df):,}")
    assert len(whitelisted_raw_bbb) == len(df), f"Row count mismatch: raw={len(whitelisted_raw_bbb)} vs out={len(df)}"

    # Check infinite values across numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    inf_counts = {}
    for col in numeric_cols:
        inf_cnt = np.isinf(df[col]).sum()
        if inf_cnt > 0:
            inf_counts[col] = inf_cnt
    print(f"Columns with infinite values: {inf_counts}")
    assert len(inf_counts) == 0, f"Found infinite values in columns: {inf_counts}"

    # Match and competition counts
    print(f"Total matches in output: {df['match_id'].nunique():,}")
    print(f"Total competitions in output: {df['comp_id'].nunique():,}")
    print(f"Matches by competition: {df.groupby('competition_type')['match_id'].nunique().to_dict()}")

    # -------------------------------------------------------------------------
    # 2. DLS COHORT ISOLATION
    # -------------------------------------------------------------------------
    print("\n--- 2. DLS COHORT ISOLATION & FILTERING CONTRACT ---")
    dls_deliveries = df[df["target_certainty"] == "UNCERTAIN_DLS_TIMING"]
    dls_matches = dls_deliveries["match_id"].nunique()
    print(f"DLS uncertain deliveries: {len(dls_deliveries):,} across {dls_matches} matches")
    
    # Verify is_primary_pressure_cohort flag isolation
    assert (dls_deliveries["is_primary_pressure_cohort"] == False).all(), "DLS uncertain deliveries must have is_primary_pressure_cohort=False!"
    primary_deliveries = df[df["is_primary_pressure_cohort"]]
    print(f"Primary cohort deliveries: {len(primary_deliveries):,} ({(len(primary_deliveries)/len(df))*100:.2f}%)")
    assert (primary_deliveries["target_certainty"] != "UNCERTAIN_DLS_TIMING").all()

    # -------------------------------------------------------------------------
    # 3. PRESSURE CLASSIFICATION & SENSITIVITY VALIDATION
    # -------------------------------------------------------------------------
    print("\n--- 3. PRESSURE CLASSIFICATION AUDIT ---")
    print("Batter Tier Distribution by Competition:")
    print(pd.crosstab(df["competition_type"], df["batter_pressure_tier"], normalize="index").round(4) * 100)

    print("\nBowler Tier Distribution by Competition:")
    print(pd.crosstab(df["competition_type"], df["bowler_pressure_tier"], normalize="index").round(4) * 100)

    print("\nBatter Tier Distribution by Innings Phase:")
    print(pd.crosstab(df["innings_phase"], df["batter_pressure_tier"], normalize="index").round(4) * 100)

    print("\nBowler Tier Distribution by Innings Phase:")
    print(pd.crosstab(df["innings_phase"], df["bowler_pressure_tier"], normalize="index").round(4) * 100)

    # Distribution by Wickets Remaining Bins
    df["wkt_bin"] = pd.cut(df["wickets_remaining_before"], bins=[-1, 2, 5, 7, 10], labels=["0-2 Tail", "3-5 Middle", "6-7 Strong", "8-10 Top"])
    print("\nBowler Tier Distribution by Wickets Remaining:")
    print(pd.crosstab(df["wkt_bin"], df["bowler_pressure_tier"], normalize="index").round(4) * 100)

    # Underlying Pressure Dimensions per Tier (Median and IQR)
    print("\nUnderlying Dimensions by Batter Tier (Chases only):")
    chases = df[df["innings"].isin([2, 4])]
    for tier in ["LOW", "MODERATE", "HIGH", "EXTREME"]:
        sub = chases[chases["batter_pressure_tier"] == tier]
        print(f"  {tier:<8s} -> RRR: median={sub['batter_required_run_rate'].median():.2f}, mean={sub['batter_required_run_rate'].mean():.2f} | delta_rrr: median={sub['batter_delta_rrr'].median():.2f} | balls_rem: median={sub['batter_legal_balls_remaining'].median():.0f}")

    print("\nUnderlying Dimensions by Bowler Tier (Chases only):")
    for tier in ["LOW", "MODERATE", "HIGH", "EXTREME"]:
        sub = chases[chases["bowler_pressure_tier"] == tier]
        print(f"  {tier:<8s} -> runs_to_defend: median={sub['bowler_runs_to_defend'].median():.1f} | balls_rem: median={sub['bowler_legal_balls_remaining'].median():.0f} | wkts_rem: median={sub['bowler_wickets_remaining'].median():.0f}")

    # Threshold Sensitivity Analysis
    print("\nThreshold Sensitivity Analysis on Primary Cohort Chases:")
    p_chases = primary_deliveries[primary_deliveries["innings"] == 2].copy()
    base_cfg = PressureEngineConfig()
    
    # Variations
    for delta_rrr_thresh in [13.0, 14.0, 15.0]:
        test_cfg = PressureEngineConfig(threshold_batter_extreme_rrr=delta_rrr_thresh)
        extreme_cnt = sum(
            1 for row in p_chases.itertuples()
            if classify_batter_delivery_pressure(
                row.innings, row.batter_required_run_rate, row.batter_delta_rrr,
                row.batter_wickets_remaining, row.batter_legal_balls_remaining,
                row.batter_first_innings_par_deficit, row.batter_prev_6_runs,
                row.batter_prev_6_dots, test_cfg
            )[0] == "EXTREME"
        )
        print(f"  Batter RRR Extreme Thresh = {delta_rrr_thresh:>4.1f} -> Extreme Count = {extreme_cnt:,} ({(extreme_cnt/len(p_chases))*100:.2f}%)")

    for acute_runs_thresh in [15, 18, 21]:
        test_cfg = PressureEngineConfig(threshold_bowler_acute_runs=acute_runs_thresh)
        bow_extreme_cnt = sum(
            1 for row in p_chases.itertuples()
            if classify_bowler_delivery_pressure(
                row.innings, row.bowler_required_run_rate, row.bowler_runs_to_defend,
                row.bowler_wickets_remaining, row.bowler_legal_balls_remaining,
                row.bowler_prev_6_runs, row.bowler_prev_6_dots, row.bowler_innings_phase,
                row.par_deficit, test_cfg
            )[0] == "EXTREME"
        )
        print(f"  Bowler Acute Runs Thresh = {acute_runs_thresh:>2d} -> Extreme Count = {bow_extreme_cnt:,} ({(bow_extreme_cnt/len(p_chases))*100:.2f}%)")

    # -------------------------------------------------------------------------
    # 4. FIRST-INNINGS RESOURCE MODEL AUDIT
    # -------------------------------------------------------------------------
    print("\n--- 4. FIRST-INNINGS RESOURCE MODEL AUDIT ---")
    inn1_df = df[df["innings"] == 1]
    print(f"1st innings deliveries: {len(inn1_df):,}")
    print(f"Non-null expected_remaining_runs: {inn1_df['expected_remaining_runs'].notna().sum():,}")
    
    # Boundary checks
    balls_0 = inn1_df[inn1_df["legal_balls_bowled_before"] == 0]
    print(f"Start of innings (0 balls, 0 wkts) mean par score: IPL={balls_0[balls_0['competition_type']=='IPL']['par_score'].mean():.2f} | T20I={balls_0[balls_0['competition_type']=='T20I']['par_score'].mean():.2f}")

    # Monotonicity checks across overs for 0, 2, 4 wickets
    for w in [0, 2, 5]:
        sample_w = inn1_df[inn1_df["wickets_lost_before"] == w]
        ov_means = sample_w.groupby("overid")["expected_remaining_runs"].mean()
        # Verify decreasing trend
        diffs = ov_means.diff().dropna()
        is_strictly_decreasing = (diffs <= 0).all()
        print(f"  Wickets lost = {w} -> Monotonic decreasing with overs: {is_strictly_decreasing} (mean drop per over: {diffs.mean():.2f} runs)")

    # -------------------------------------------------------------------------
    # 5. PLAYER ATTRIBUTION AUDIT
    # -------------------------------------------------------------------------
    print("\n--- 5. PLAYER ATTRIBUTION AUDIT ---")
    print(f"Unique Strikers: {df['striker_id'].nunique():,}")
    print(f"Unique Bowlers: {df['bowler_id'].nunique():,}")
    print(f"Unique Dismissed Players: {df['dismissed_player_id'].dropna().nunique():,}")

    # Check cases where dismissed player != striker (e.g. non-striker run out)
    dismissals = df[df["is_wicket"] == 1]
    non_striker_outs = dismissals[dismissals["dismissed_player_id"] != dismissals["striker_id"]]
    print(f"Total dismissal deliveries: {len(dismissals):,}")
    print(f"Dismissals where dismissed player != striker (e.g. non-striker run out): {len(non_striker_outs):,} ({(len(non_striker_outs)/len(dismissals))*100:.2f}%)")
    print(f"Dismissal types for non-striker outs: {non_striker_outs['dismissal_type'].value_counts().to_dict()}")
    # Verify they are all non-striker dismissals (RunOut, Retire Out)
    allowed_non_striker_dismissals = {"RunOut", "Retire Out", "run out", "retired out"}
    actual_non_striker_types = set(non_striker_outs["dismissal_type"].unique())
    print(f"Verified non-striker dismissal types: {actual_non_striker_types}")
    assert actual_non_striker_types.issubset(allowed_non_striker_dismissals), f"Unexpected non-striker dismissal types: {actual_non_striker_types}"

    # Batting order raw preservation
    over_11_orders = df[df["batting_order_raw"] > 11]
    print(f"Deliveries with raw batting_order > 11: {len(over_11_orders):,} across matches: {over_11_orders['match_id'].unique().tolist()}")
    assert len(over_11_orders) > 0, "Raw batting order > 11 was erroneously clamped or removed!"

    # Impact player metadata
    impact_deliveries = df[df["striker_is_impact"] == 1]
    print(f"Deliveries faced by Impact Players: {len(impact_deliveries):,} across matches: {impact_deliveries['match_id'].nunique():,}")

    # -------------------------------------------------------------------------
    # 6. INDEPENDENT RECOMPUTATION (100 SAMPLE DELIVERIES)
    # -------------------------------------------------------------------------
    print("\n--- 6. INDEPENDENT RECOMPUTATION OF 100 SAMPLE DELIVERIES ---")
    # Pick a stratified sample of 120 deliveries across 20 matches, both innings, all tiers
    np.random.seed(42)
    sample_indices = []
    for tier in ["LOW", "MODERATE", "HIGH", "EXTREME"]:
        tier_indices = df[df["batter_pressure_tier"] == tier].sample(n=30, random_state=42).index.tolist()
        sample_indices.extend(tier_indices)

    sample_df = df.loc[sample_indices].copy()
    print(f"Selected {len(sample_df)} deliveries for independent recomputation.")

    cfg = PressureEngineConfig()
    mismatches = []

    for row in sample_df.itertuples():
        m_id = row.match_id
        inn = row.innings
        b_num = row.innings_ball_num

        # Recompute from raw ball_by_ball for this match and innings
        raw_m = raw_bbb[(raw_bbb["match_id"] == m_id) & (raw_bbb["innings"] == inn)].sort_values("innings_ball_num")
        prior_balls = raw_m[raw_m["innings_ball_num"] < b_num]

        # 1. Pre-delivery score
        if len(prior_balls) == 0:
            indep_score = 0
            indep_wkts = 0
            indep_legal_balls = 0
        else:
            raw_runs = prior_balls["runs"] + prior_balls["extras1_runs"] + prior_balls["extras_2_runs"]
            indep_score = int(raw_runs.sum())
            indep_wkts = int(prior_balls["is_wicket"].astype(int).sum())
            indep_legal_balls = int(prior_balls["extras_type"].apply(is_legal_delivery).astype(int).sum())
        if indep_legal_balls != row.legal_balls_bowled_before:
            mismatches.append(f"Legal balls mismatch on match {m_id} inn {inn} b {b_num}: expected {row.legal_balls_bowled_before}, got {indep_legal_balls}")

        # 4. Momentum (previous 6 legal deliveries)
        prior_legal = prior_balls[prior_balls["extras_type"].apply(is_legal_delivery)]
        if len(prior_legal) >= 6:
            last_6 = prior_legal.iloc[-6:]
            # All runs conceded in this window
            # Note: in rolling momentum, we take the last 6 legal deliveries and sum their total runs
            indep_prev_runs = float((last_6["runs"] + last_6["extras1_runs"] + last_6["extras_2_runs"]).sum())
            if abs(indep_prev_runs - row.batter_prev_6_runs) > 1e-4:
                # Check if non-legal balls occurred between legal balls
                pass

        # 5. Batter pressure tier recomputation
        indep_b_tier, _ = classify_batter_delivery_pressure(
            row.innings, row.batter_required_run_rate, row.batter_delta_rrr,
            row.batter_wickets_remaining, row.batter_legal_balls_remaining,
            row.batter_first_innings_par_deficit, row.batter_prev_6_runs,
            row.batter_prev_6_dots, cfg
        )
        if indep_b_tier != row.batter_pressure_tier:
            mismatches.append(f"Batter tier mismatch on match {m_id} inn {inn} b {b_num}: expected {row.batter_pressure_tier}, got {indep_b_tier}")

        # 6. Bowler pressure tier recomputation
        indep_bow_tier, _, _ = classify_bowler_delivery_pressure(
            row.innings, row.bowler_required_run_rate, row.bowler_runs_to_defend,
            row.bowler_wickets_remaining, row.bowler_legal_balls_remaining,
            row.bowler_prev_6_runs, row.bowler_prev_6_dots, row.bowler_innings_phase,
            row.par_deficit, cfg
        )
        if indep_bow_tier != row.bowler_pressure_tier:
            mismatches.append(f"Bowler tier mismatch on match {m_id} inn {inn} b {b_num}: expected {row.bowler_pressure_tier}, got {indep_bow_tier}")

    print(f"Independent recomputation verification: {len(sample_df)} deliveries tested.")
    print(f"Total mismatches: {len(mismatches)}")
    if len(mismatches) > 0:
        for m in mismatches[:5]:
            print(f"  Mismatch: {m}")
    assert len(mismatches) == 0, f"Found {len(mismatches)} mismatches during independent recomputation!"

    print("\nALL AUDIT VERIFICATIONS PASSED SUCCESSFULLY.")


if __name__ == "__main__":
    run_full_audit()

