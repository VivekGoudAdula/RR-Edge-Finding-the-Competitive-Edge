export type Discipline = 'BATTER' | 'BOWLER';

export interface OverviewMetadata {
  product: string;
  tagline: string;
  descriptor: string;
  theme: string;
  total_deliveries: number;
  primary_deliveries: number;
  matches_analysed: number;
  competitions: string[];
  batters_analysed: number;
  bowlers_analysed: number;
}

export interface PlayerOverview {
  player_id: number;
  player_name: string;
  discipline: string;
  primary_role: string;
  phase_suitability?: string;
  format_coverage?: string;
  qualification_tier?: string;
  evidence_tier: string;
  stability_archetype: string;
  top_10_rank: number;
  selection_status: string;
  selection_rationale?: string;
  main_strengths?: string;
  main_weaknesses?: string;
  selection_risks?: string;

  // Batters
  ipl_raw_sr?: number;
  ipl_shrunk_m45?: number;
  ipl_context_delta_sr?: number;
  ipl_dot_ball_pct?: number;
  ipl_boundary_ball_pct?: number;
  ipl_pressure_volume?: number;
  t20i_pressure_volume?: number;
  combined_pressure_volume?: number;
  ipl_matches?: number;
  t20i_matches?: number;
  combined_matches?: number;
  ipl_match_pass_rate?: number;
  t20i_raw_sr?: number;
  t20i_shrunk_m45?: number;
  t20i_context_delta_sr?: number;
  t20i_dot_ball_pct?: number;
  t20i_boundary_ball_pct?: number;

  // Bowlers
  ipl_raw_econ?: number;
  ipl_shrunk_m45_econ?: number;
  ipl_context_delta_econ?: number;
  ipl_legal_econ?: number;
  ipl_legal_context_delta_econ?: number;
  ipl_expected_econ?: number;
  ipl_legal_expected_econ?: number;
  ipl_wickets_per_over?: number;
  ipl_boundary_concession_pct?: number;
  t20i_raw_econ?: number;
  t20i_shrunk_m45_econ?: number;
  t20i_context_delta_econ?: number;
  t20i_legal_econ?: number;
  t20i_legal_context_delta_econ?: number;
  t20i_expected_econ?: number;
  t20i_legal_expected_econ?: number;
  t20i_wickets_per_over?: number;
  t20i_boundary_concession_pct?: number;
  [key: string]: any;
}

export interface Discovery {
  id: string;
  headline: string;
  detail: string;
  discipline: string;
  tag: string;
}

export interface OverviewData {
  metadata: OverviewMetadata;
  top_10_batters: PlayerOverview[];
  top_10_bowlers: PlayerOverview[];
  key_discoveries: Discovery[];
}

export interface PhaseMetric {
  striker_id?: number;
  bowler_id?: number;
  innings_phase?: string;
  bowler_innings_phase?: string;
  phase_pressure_balls: number;
  phase_pressure_runs: number;
  phase_pressure_boundaries?: number;
  phase_pressure_dots?: number;
  phase_pressure_sr?: number;
  phase_pressure_boundary_pct?: number;
  phase_pressure_dot_pct?: number;
  phase_pressure_wickets?: number;
  phase_pressure_economy?: number;
}

export interface ShrinkagePoint {
  parameter: string;
  m_value: number;
  sr?: number;
  econ?: number;
}

export interface PressurePerformanceProfile {
  pressure_volume?: number;
  pressure_matches?: number;
  normal_volume?: number;
  normal_matches?: number;
  pressure_strike_rate?: number;
  normal_strike_rate?: number;
  delta_strike_rate?: number;
  pressure_dot_pct?: number;
  normal_dot_pct?: number;
  delta_dot_pct?: number;
  pressure_boundary_pct?: number;
  normal_boundary_pct?: number;
  delta_boundary_pct?: number;
  context_adjusted_delta_sr?: number;
  observed_pressure_sr?: number;
  expected_pressure_sr?: number;
  pressure_match_pass_rate?: number;
  pressure_match_sr_std?: number;
  pressure_match_sr_median?: number;
  pressure_match_sr_iqr?: number;
  tail_anchor_balls?: number;
  tail_anchor_sr?: number;
  final_crunch_balls?: number;
  final_crunch_sr?: number;
  combined_panic_balls?: number;
  combined_panic_sr?: number;

  // Explicit IPL vs Combined Reconciliation (Audit)
  ipl_pressure_volume?: number;
  ipl_pressure_matches?: number;
  ipl_pressure_strike_rate?: number;
  ipl_context_adjusted_delta_sr?: number;
  ipl_observed_pressure_sr?: number;
  ipl_expected_pressure_sr?: number;

  combined_pressure_volume?: number;
  combined_pressure_matches?: number;
  combined_pressure_strike_rate?: number;
  combined_context_adjusted_delta_sr?: number;
  combined_observed_pressure_sr?: number;
  combined_expected_pressure_sr?: number;

  // Bowler specific
  pressure_legal_balls?: number;
  pressure_total_deliveries?: number;
  pressure_overs?: number;
  pressure_runs_conceded?: number;
  pressure_wickets?: number;
  pressure_economy_rate?: number;
  normal_economy_rate?: number;
  delta_economy?: number;
  pressure_boundary_concession_pct?: number;
  normal_boundary_concession_pct?: number;
  delta_boundary_concession_pct?: number;
  all_runs_rcae_delta_econ?: number;
  observed_pressure_econ?: number;
  expected_pressure_econ?: number;
  legal_rcae_delta_econ?: number;
  observed_legal_econ?: number;
  expected_legal_econ?: number;
  pressure_match_econ_std?: number;
  pressure_match_econ_median?: number;
  pressure_match_econ_iqr?: number;
  vs_top_order_balls?: number;
  vs_top_order_economy?: number;
  vs_tail_balls?: number;
  vs_tail_economy?: number;
  chase_crunch_balls?: number;
  chase_crunch_economy?: number;
  wickets_per_over?: number;
  wicket_impact_score?: number;

  // Explicit Bowler IPL vs Combined Reconciliation
  ipl_pressure_legal_balls?: number;
  ipl_pressure_economy_rate?: number;
  ipl_all_runs_rcae_delta_econ?: number;
  ipl_observed_pressure_econ?: number;
  ipl_expected_pressure_econ?: number;
  ipl_legal_rcae_delta_econ?: number;
  ipl_observed_legal_econ?: number;
  ipl_expected_legal_econ?: number;

  combined_pressure_legal_balls?: number;
  combined_pressure_economy_rate?: number;
  combined_all_runs_rcae_delta_econ?: number;
  combined_observed_pressure_econ?: number;
  combined_expected_pressure_econ?: number;
  combined_legal_rcae_delta_econ?: number;
  combined_observed_legal_econ?: number;
  combined_expected_legal_econ?: number;
}

export interface ExperimentalWicketClassifier {
  model: string;
  actual_wickets?: number;
  expected_wickets?: number;
  residual_wickets?: number;
  brier_score: number;
  prior_brier_baseline: number;
  pr_auc: number;
  empirical_base_rate: number;
  roc_auc: number;
  status: string;
  advisory: string;
}

export interface MLContextProfile {
  model_champion: string;
  benchmark_context_delta_sr?: number;
  combined_benchmark_context_delta_sr?: number;
  benchmark_all_runs_rcae?: number;
  benchmark_legal_rcae?: number;
  combined_benchmark_all_runs_rcae?: number;
  population_scope?: string;
  test_eval_deliveries: number;
  actual_runs?: number;
  expected_runs_lightgbm?: number;
  net_residual?: number;
  mean_residual_per_ball?: number;
  actual_rate?: number;
  expected_rate?: number;
  test_status: string;
  disclaimer: string;
  limitations: string;

  // Bowler specific
  actual_runs_conceded?: number;
  net_residual_runs?: number;
  actual_economy?: number;
  expected_economy?: number;
  suppression_per_over?: number;
  experimental_wicket_classifier?: ExperimentalWicketClassifier | null;
}

export interface BehavioralProfile {
  striker_id?: number;
  bowler_id?: number;
  striker_name?: string;
  bowler_name?: string;
  total_balls?: number;
  sample_confidence?: string;
  has_sufficient_evidence?: boolean;
  interpretation?: string;

  // Batter Drought-State vs Strict t+1
  drought_metric_name?: string;
  drought_state_balls?: number;
  drought_state_strike_rate?: number;
  drought_state_dot_pct?: number;
  drought_state_boundary_pct?: number;
  drought_state_wicket_pct?: number;
  delta_sr_drought_state?: number;
  drought_state_definition?: string;
  drought_cohort_summary?: string;

  strict_t1_available?: boolean;
  strict_t1_metric_name?: string;
  strict_t1_status?: string;
  strict_t1_cohort_summary?: string;
  strict_t1_note?: string;

  post_dot_balls?: number;
  post_dot_strike_rate?: number;
  post_dot_dot_pct?: number;
  post_dot_boundary_pct?: number;
  post_dot_wicket_pct?: number;
  delta_sr_post_dot?: number;
  avg_balls_to_scoring?: number;
  avg_balls_to_boundary?: number;
  post_wkt_balls?: number;
  post_wkt_strike_rate?: number;
  post_wkt_dot_pct?: number;
  post_wkt_wicket_pct?: number;
  scoring_resilience_index?: number;

  // Bowler
  post_boundary_metric_name?: string;
  post_boundary_cohort_summary?: string;
  post_cluster_metric_name?: string;
  post_cluster_cohort_summary?: string;
  progression_metric_name?: string;
  post_boundary_legal_balls?: number;
  post_boundary_economy?: number;
  post_boundary_dot_pct?: number;
  post_boundary_boundary_pct?: number;
  post_boundary_wicket_pct?: number;
  delta_econ_post_boundary?: number;
  bounceback_index?: number;
  post_cluster_balls?: number;
  post_cluster_economy?: number;
  post_cluster_dot_pct?: number;
  early_spell_balls?: number;
  early_spell_economy?: number;
  late_spell_balls?: number;
  late_spell_economy?: number;
  spell_economy_progression?: number;
}

export interface RiskFlagRecord {
  player_id: number;
  player_name: string;
  discipline: string;
  format: string;
  qualification_tier: string;
  pressure_volume: number;
  pressure_matches: number;
  risk_flag_count: number;
  risk_severity: string;
  flag_sample_fragility?: boolean;
  flag_dot_ball_vulnerability?: boolean;
  flag_boundary_reliance?: boolean;
  flag_phase_specialization?: boolean;
  flag_match_volatility?: boolean;
  flag_crunch_collapse?: boolean;
  flag_context_dropoff?: boolean;
  risk_notes?: string;
}

export interface ReliabilityProfile {
  evidence_tier?: string;
  stability_archetype?: string;
  shrunk_m25?: number;
  shrunk_m45?: number;
  shrunk_m60?: number;
  shrunk_m90?: number;
  pressure_sr_ci_lower_95?: number;
  pressure_sr_ci_upper_95?: number;
  pressure_econ_ci_lower_95?: number;
  pressure_econ_ci_upper_95?: number;
  pressure_dot_pct_posterior?: number;
  pressure_dot_pct_ci_lower_95?: number;
  pressure_dot_pct_ci_upper_95?: number;
  risk_flags?: RiskFlagRecord[];
  has_risk_flags?: boolean;
}

export interface PlayerDetail {
  player: PlayerOverview;
  pressure_performance?: PressurePerformanceProfile;
  ml_context?: MLContextProfile;
  behavioral?: BehavioralProfile;
  reliability?: ReliabilityProfile;
  phases: PhaseMetric[];
  shrinkage_curve: ShrinkagePoint[];
  populations?: Record<string, string>;
}

export interface PairwiseBootstrap {
  pair_id: string;
  discipline: string;
  evaluation_format: string;
  rank_a: number;
  player_a_name: string;
  player_a_id: number;
  player_a_volume: number;
  player_a_rate: number;
  rank_b: number;
  player_b_name: string;
  player_b_id: number;
  player_b_volume: number;
  player_b_rate: number;
  observed_difference: number;
  bootstrap_se_10k: number;
  bootstrap_ci_95_lower: number;
  bootstrap_ci_95_upper: number;
  effective_sample_assessment: string;
  statistical_distinction: string;
  statistical_verdict: string;
}

export interface ComparabilityAudit {
  volume_ratio: number;
  sample_divergence: boolean;
  tier_a: string;
  tier_b: string;
  status: string;
  disclosure: string;
}

export interface ComparisonData {
  player_a: PlayerDetail;
  player_b: PlayerDetail;
  pairwise_bootstrap?: PairwiseBootstrap;
  curated_h2h?: any;
  comparability_audit?: ComparabilityAudit;
}

export interface PressureTierInfo {
  tier: string;
  batter_pct: number;
  bowler_pct: number;
  description: string;
}

export interface PressureComparisonMetric {
  metric: string;
  normal: number;
  pressure: number;
  unit: string;
  delta: string;
}

export interface PressureDistributions {
  tiers: PressureTierInfo[];
  pressure_vs_normal: {
    batters: PressureComparisonMetric[];
    bowlers: PressureComparisonMetric[];
  };
  phase_breakdown: {
    phase: string;
    pressure_deliveries_pct: number;
    normal_deliveries_pct: number;
  }[];
  asymmetry_principles: {
    title: string;
    explanation: string;
  }[];
}

export interface MethodologyData {
  title: string;
  framework_steps: {
    step: number;
    name: string;
    description: string;
  }[];
  shrinkage_grid: {
    m: number;
    weight_76b: string;
    weight_334b: string;
    use_case: string;
  }[];
  evidence_tiers: {
    tier: string;
    criteria: string;
    reliability: string;
  }[];
}

export interface ExplorerData {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  rows: any[];
}

// -------------------------------------------------------------
// Scenario Lab Types
// -------------------------------------------------------------
export interface ScenarioDefinition {
  id: string;
  name: string;
  discipline: 'BOWLER' | 'BATTER';
  category: string;
  description: string;
  tactical_intent: string;
  metric_focus: string[];
  exact_rules: Record<string, any>;
  relaxed_rules: Record<string, any>;
  relaxation_explanation: string;
}

export interface ScenarioCatalogResponse {
  total_scenarios: number;
  bowling_scenarios: ScenarioDefinition[];
  batting_scenarios: ScenarioDefinition[];
}

export interface ScenarioPlayer {
  player_id: number;
  player_name: string;
  discipline: 'BOWLER' | 'BATTER';
  format: string;
  deliveries: number;
  legal_balls: number;
  matches: number;
  runs: number;
  primary_rate: number; // Economy or Strike Rate
  dot_pct: number;
  boundary_pct: number;
  wicket_pct: number;
  wickets_per_over: number;
  success_rate: number | null;
  success_ci: [number, number];
  context_diff: number;
  confidence_interval: [number, number];
  evidence_tier: 'CONFIDENT' | 'PROVISIONAL' | 'INSUFFICIENT';
}

export interface ScenarioCohortBenchmarks {
  total_deliveries: number;
  total_matches: number;
  total_players: number;
  cohort_rate: number;
  cohort_dot_pct: number;
  cohort_boundary_pct: number;
  cohort_wicket_pct: number;
  cohort_success_rate: number | null;
}

export interface ScenarioEpisode {
  match_id: number;
  match_date: string;
  comp_name: string;
  innings: number;
  over_ball: string;
  striker: string;
  bowler: string;
  runs: number;
  total_runs: number;
  is_wicket: boolean;
  dismissal_type: string | null;
  balls_remaining: number;
  runs_to_defend: number | null;
  match_result: string;
}

export interface ScenarioExecutionResult {
  scenario: {
    id: string;
    name: string;
    discipline: 'BOWLER' | 'BATTER';
    category: string;
    description: string;
    tactical_intent: string;
    is_relaxed: boolean;
    relaxation_explanation: string | null;
    applied_rules: Record<string, any>;
  };
  format: string;
  cohort_benchmarks: ScenarioCohortBenchmarks;
  total_players: number;
  players: ScenarioPlayer[];
  sample_episodes?: ScenarioEpisode[];
}

export interface ScenarioComparisonResult {
  scenario: {
    id: string;
    name: string;
    discipline: 'BOWLER' | 'BATTER';
    category: string;
    description: string;
    tactical_intent: string;
    is_relaxed: boolean;
    relaxation_explanation: string | null;
  };
  cohort_benchmarks: ScenarioCohortBenchmarks;
  compared_players: ScenarioPlayer[];
}

// -------------------------------------------------------------
// Player Intelligence Gallery Types
// -------------------------------------------------------------
export interface GalleryPlayerCard {
  player_id: number;
  player_name: string;
  role: string;
  discipline: 'BATTER' | 'BOWLER' | 'ALL_ROUNDER';
  formats: string[];
  matches: number;
  deliveries: number;
  is_top_10: boolean;
  top_10_rank: number | null;
  primary_rate: number;
  rate_label: string;
  pressure_indicator: string | null;
  evidence_tier: 'CONFIDENT' | 'PROVISIONAL' | 'INSUFFICIENT';
  verified_teams: string[];
}

export interface GalleryPlayersResponse {
  total_players: number;
  page: number;
  page_size: number;
  total_pages: number;
  players: GalleryPlayerCard[];
}

export interface PlayerProfileResponse {
  player_id: number;
  card: GalleryPlayerCard;
  sections: {
    career_overview: {
      player_id: number;
      player_name: string;
      role: string;
      discipline: string;
      formats: string[];
      verified_teams: string[];
      career_matches: number;
      career_deliveries: number;
      is_top_10: boolean;
      top_10_rank: number | null;
      birth_date: string;
      age: string;
      nationality: string;
      batting_style: string;
      bowling_style: string;
      biography: string;
    };
    ipl_performance: {
      format: string;
      has_data: boolean;
      batting: any;
      bowling: any;
    };
    t20i_performance: {
      format: string;
      has_data: boolean;
      batting: any;
      bowling: any;
    };
    season_history: {
      season: string;
      matches: number;
      batting_balls: number;
      batting_runs: number;
      batting_strike_rate: number | null;
      bowling_balls: number;
      bowling_runs: number;
      bowling_wickets: number;
      bowling_economy: number | null;
    }[];
    match_history: {
      match_id: number;
      match_date: string;
      competition: string;
      home_team: string;
      away_team: string;
      venue_country: string;
      batting_runs: number | null;
      batting_balls: number | null;
      batting_strike_rate: number | null;
      bowling_balls: number | null;
      bowling_runs: number | null;
      bowling_wickets: number | null;
      bowling_economy: number | null;
      match_result: string;
    }[];
    phase_statistics: {
      batting_phases: Record<string, any>;
      bowling_phases: Record<string, any>;
    };
    pressure_intelligence: {
      batting_pressure_balls: number;
      batting_tier_distribution: Record<string, number>;
      bowling_pressure_balls: number;
      bowling_tier_distribution: Record<string, number>;
    };
    scenario_lab_results: {
      scenario_id: string;
      scenario_name: string;
      category: string;
      deliveries: number;
      primary_rate: number | null;
      dot_pct: number | null;
      boundary_pct: number | null;
      success_rate: number | null;
      context_diff: number;
      cohort_benchmark_rate: number;
      evidence_tier: string;
      confidence_interval: [number, number];
    }[];
    behavioral_intelligence: any;
    ml_context: any;
    reliability_evidence: {
      sample_deliveries: number;
      sample_matches: number;
      shrinkage_m_factor: number;
      sample_adequacy: string;
      uncertainty_status: string;
    };
    comparison_peers: {
      player_id: number;
      player_name: string;
      role: string;
      deliveries: number;
      primary_rate: number;
      rate_label: string;
      is_top_10: boolean;
    }[];
  };
}

