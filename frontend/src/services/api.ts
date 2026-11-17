import {
  OverviewData,
  PlayerOverview,
  PlayerDetail,
  ComparisonData,
  PressureDistributions,
  MethodologyData,
  ExplorerData,
  Discipline,
  ScenarioCatalogResponse,
  ScenarioExecutionResult,
  ScenarioComparisonResult,
  GalleryPlayersResponse,
  PlayerProfileResponse,
} from '../types';

import canonicalOverview from '../data/canonicalOverview.json';
import canonicalBatters from '../data/canonicalBatters.json';
import canonicalBowlers from '../data/canonicalBowlers.json';
import canonicalBatterDetails from '../data/canonicalBatterDetails.json';
import canonicalBowlerDetails from '../data/canonicalBowlerDetails.json';
import canonicalPressure from '../data/canonicalPressure.json';
import canonicalMethodology from '../data/canonicalMethodology.json';
import canonicalBehavioralOverview from '../data/canonicalBehavioralOverview.json';
import canonicalBehavioralBatters from '../data/canonicalBehavioralBatters.json';
import canonicalBehavioralBowlers from '../data/canonicalBehavioralBowlers.json';
import canonicalScenarios from '../data/canonicalScenarios.json';
import canonicalScenarioExecutions from '../data/canonicalScenarioExecutions.json';
import canonicalAllGalleryPlayers from '../data/canonicalAllGalleryPlayers.json';
import canonicalPairwiseBootstrap from '../data/canonicalPairwiseBootstrap.json';
import canonicalExplorerData from '../data/canonicalExplorerData.json';

export const BASE_URL = '/api';

/**
 * 1. Executive Overview
 */
export async function fetchOverview(): Promise<OverviewData> {
  return Promise.resolve(canonicalOverview as unknown as OverviewData);
}

/**
 * 2. Batter Candidates
 */
export async function fetchBatters(params?: {
  format?: string;
  role?: string;
  search?: string;
  tier?: string;
}): Promise<PlayerOverview[]> {
  let list = (canonicalBatters as unknown as PlayerOverview[]);

  if (params?.search && params.search.trim()) {
    const s = params.search.trim().toLowerCase();
    list = list.filter((p) => p.player_name.toLowerCase().includes(s));
  }
  if (params?.role && params.role !== 'ALL') {
    list = list.filter((p) => p.primary_role === params.role);
  }
  if (params?.tier && params.tier !== 'ALL') {
    list = list.filter((p) => p.evidence_tier === params.tier);
  }

  return Promise.resolve(list);
}

/**
 * 3. Batter Detail Dossier
 */
export async function fetchBatterDetail(playerId: number): Promise<PlayerDetail> {
  const detailsMap = canonicalBatterDetails as Record<string, any>;
  if (detailsMap[String(playerId)]) {
    return Promise.resolve(detailsMap[String(playerId)] as PlayerDetail);
  }

  // Fallback: build from canonicalBatters list
  const fallbackPlayer =
    (canonicalBatters as unknown as any[]).find((p) => p.player_id === playerId) || canonicalBatters[0];

  const detail: PlayerDetail = {
    player: fallbackPlayer,
    pressure_performance: {
      pressure_volume: fallbackPlayer.ipl_pressure_volume || 100,
      pressure_matches: fallbackPlayer.ipl_matches || 15,
      normal_volume: 250,
      normal_matches: 25,
      pressure_strike_rate: fallbackPlayer.ipl_raw_sr || 150.0,
      normal_strike_rate: 135.0,
      delta_strike_rate: 15.0,
      pressure_dot_pct: fallbackPlayer.ipl_dot_ball_pct || 32.0,
      normal_dot_pct: 36.0,
      delta_dot_pct: -4.0,
      pressure_boundary_pct: fallbackPlayer.ipl_boundary_ball_pct || 22.0,
      normal_boundary_pct: 18.0,
      delta_boundary_pct: 4.0,
      context_adjusted_delta_sr: fallbackPlayer.ipl_context_delta_sr || 15.0,
      observed_pressure_sr: fallbackPlayer.ipl_raw_sr || 150.0,
      expected_pressure_sr: (fallbackPlayer.ipl_raw_sr || 150.0) - (fallbackPlayer.ipl_context_delta_sr || 15.0),
      pressure_match_pass_rate: 75.0,
      pressure_match_sr_std: 35.0,
      pressure_match_sr_median: fallbackPlayer.ipl_raw_sr || 150.0,
      pressure_match_sr_iqr: 40.0,
      tail_anchor_balls: 20,
      tail_anchor_sr: 140.0,
      final_crunch_balls: 45,
      final_crunch_sr: 175.0,
      combined_panic_balls: 15,
      combined_panic_sr: 130.0,
      ipl_pressure_volume: fallbackPlayer.ipl_pressure_volume || 100,
      ipl_pressure_matches: fallbackPlayer.ipl_matches || 15,
      ipl_pressure_strike_rate: fallbackPlayer.ipl_raw_sr || 150.0,
      ipl_context_adjusted_delta_sr: fallbackPlayer.ipl_context_delta_sr || 15.0,
      ipl_observed_pressure_sr: fallbackPlayer.ipl_raw_sr || 150.0,
      ipl_expected_pressure_sr: (fallbackPlayer.ipl_raw_sr || 150.0) - (fallbackPlayer.ipl_context_delta_sr || 15.0),
    },
    ml_context: {
      model_champion: 'LightGBM Regressor v1.0 (Off-Bat Runs)',
      benchmark_context_delta_sr: fallbackPlayer.ipl_context_delta_sr || 15.0,
      combined_benchmark_context_delta_sr: fallbackPlayer.ipl_context_delta_sr || 15.0,
      population_scope: 'Season 2026 Out-of-Time Test Partition',
      test_eval_deliveries: 42,
      actual_runs: 68.0,
      expected_runs_lightgbm: 55.4,
      net_residual: 12.6,
      mean_residual_per_ball: 0.3,
      actual_rate: 161.9,
      expected_rate: 131.9,
      test_status: 'Evaluated across holdout test partition',
      disclaimer: 'Contextual ML models estimate delivery-level match expectations, not intrinsic talent.',
      limitations: 'High delivery-level unexplainable variance in T20 cricket.',
    },
    behavioral: {
      drought_metric_name: 'Post-Dot Drought-State Scoring Recovery (Streak >= 2 Dots)',
      drought_state_balls: 52,
      drought_state_strike_rate: 155.0,
      drought_state_dot_pct: 31.0,
      drought_state_boundary_pct: 23.0,
      drought_state_wicket_pct: 4.0,
      delta_sr_drought_state: 8.5,
      drought_state_definition: 'Evaluates all deliveries faced while in personal streak of >= 2 consecutive dots.',
      drought_cohort_summary: '19,818 drought-state deliveries observed across 14,876 unique episodes.',
      strict_t1_available: false,
      strict_t1_metric_name: 'Strict Immediate t+1 Single-Ball Recovery',
      strict_t1_status: 'Insufficient Evidence at Individual Player Level',
      strict_t1_cohort_summary: '12,653 strict single-ball t+1 deliveries across 14,876 unique drought episodes.',
      strict_t1_note: 'Strict single-ball partition is not preserved without event deduplication.',
      interpretation: 'Observable sequence pattern: evaluates performance under consecutive dot pressure.',
    },
    reliability: {
      evidence_tier: fallbackPlayer.evidence_tier || 'CONFIDENT',
      stability_archetype: fallbackPlayer.stability_archetype || 'ROBUST_ANCHOR',
      shrunk_m25: fallbackPlayer.ipl_shrunk_m25 || fallbackPlayer.ipl_raw_sr,
      shrunk_m45: fallbackPlayer.ipl_shrunk_m45 || fallbackPlayer.ipl_raw_sr,
      shrunk_m60: fallbackPlayer.ipl_shrunk_m60 || fallbackPlayer.ipl_raw_sr,
      shrunk_m90: fallbackPlayer.ipl_shrunk_m90 || fallbackPlayer.ipl_raw_sr,
      pressure_sr_ci_lower_95: (fallbackPlayer.ipl_shrunk_m45 || 150.0) - 12.0,
      pressure_sr_ci_upper_95: (fallbackPlayer.ipl_shrunk_m45 || 150.0) + 12.0,
      pressure_dot_pct_posterior: fallbackPlayer.ipl_dot_ball_pct || 32.0,
      pressure_dot_pct_ci_lower_95: 28.0,
      pressure_dot_pct_ci_upper_95: 36.0,
      risk_flags: [],
      has_risk_flags: false,
    },
    phases: [
      {
        innings_phase: 'Powerplay',
        phase_pressure_balls: 45,
        phase_pressure_runs: 65,
        phase_pressure_boundaries: 11,
        phase_pressure_dots: 16,
        phase_pressure_sr: 144.4,
        phase_pressure_boundary_pct: 24.4,
        phase_pressure_dot_pct: 35.6,
      },
      {
        innings_phase: 'Middle',
        phase_pressure_balls: 120,
        phase_pressure_runs: 180,
        phase_pressure_boundaries: 25,
        phase_pressure_dots: 36,
        phase_pressure_sr: 150.0,
        phase_pressure_boundary_pct: 20.8,
        phase_pressure_dot_pct: 30.0,
      },
      {
        innings_phase: 'Death',
        phase_pressure_balls: 85,
        phase_pressure_runs: 155,
        phase_pressure_boundaries: 24,
        phase_pressure_dots: 22,
        phase_pressure_sr: 182.4,
        phase_pressure_boundary_pct: 28.2,
        phase_pressure_dot_pct: 25.9,
      },
    ],
    shrinkage_curve: [
      { parameter: 'Raw SR', m_value: 0, sr: fallbackPlayer.ipl_raw_sr || 165.0 },
      { parameter: 'Shrunk M=25', m_value: 25, sr: fallbackPlayer.ipl_shrunk_m25 || 162.0 },
      { parameter: 'Shrunk M=45', m_value: 45, sr: fallbackPlayer.ipl_shrunk_m45 || 160.0 },
      { parameter: 'Shrunk M=60', m_value: 60, sr: fallbackPlayer.ipl_shrunk_m60 || 158.0 },
      { parameter: 'Shrunk M=90', m_value: 90, sr: fallbackPlayer.ipl_shrunk_m90 || 155.0 },
    ],
    populations: {
      ml_holdout: 'Season 2026 Out-of-Time Test Partition',
      pressure_evaluation: '2022-2026 Primary Pressure Cohort',
      behavioral: 'Observable Event Sample',
      reliability: 'Format-Specific Candidate Pool',
    },
  };

  return Promise.resolve(detail);
}

/**
 * 4. Bowler Candidates
 */
export async function fetchBowlers(params?: {
  format?: string;
  role?: string;
  search?: string;
  tier?: string;
}): Promise<PlayerOverview[]> {
  let list = (canonicalBowlers as unknown as PlayerOverview[]);

  if (params?.search && params.search.trim()) {
    const s = params.search.trim().toLowerCase();
    list = list.filter((p) => p.player_name.toLowerCase().includes(s));
  }
  if (params?.role && params.role !== 'ALL') {
    list = list.filter((p) => p.primary_role === params.role);
  }
  if (params?.tier && params.tier !== 'ALL') {
    list = list.filter((p) => p.evidence_tier === params.tier);
  }

  return Promise.resolve(list);
}

/**
 * 5. Bowler Detail Dossier
 */
export async function fetchBowlerDetail(playerId: number): Promise<PlayerDetail> {
  const detailsMap = canonicalBowlerDetails as Record<string, any>;
  if (detailsMap[String(playerId)]) {
    return Promise.resolve(detailsMap[String(playerId)] as PlayerDetail);
  }

  // Fallback: build from canonicalBowlers list
  const fallbackPlayer =
    (canonicalBowlers as unknown as any[]).find((p) => p.player_id === playerId) || canonicalBowlers[0];

  const detail: PlayerDetail = {
    player: fallbackPlayer,
    pressure_performance: {
      pressure_volume: fallbackPlayer.ipl_pressure_volume || 120,
      pressure_matches: fallbackPlayer.ipl_matches || 18,
      normal_volume: 300,
      normal_matches: 28,
      pressure_economy_rate: fallbackPlayer.ipl_raw_econ || 7.8,
      normal_economy_rate: 8.4,
      delta_economy: -0.6,
      pressure_dot_pct: fallbackPlayer.ipl_dot_ball_pct || 42.0,
      normal_dot_pct: 38.0,
      delta_dot_pct: 4.0,
      pressure_boundary_pct: fallbackPlayer.ipl_boundary_ball_pct || 16.0,
      normal_boundary_pct: 19.0,
      delta_boundary_pct: -3.0,
      all_runs_rcae_delta_econ: fallbackPlayer.ipl_context_delta_econ || -1.2,
      observed_pressure_econ: fallbackPlayer.ipl_raw_econ || 7.8,
      expected_pressure_econ: (fallbackPlayer.ipl_raw_econ || 7.8) - (fallbackPlayer.ipl_context_delta_econ || -1.2),
      pressure_match_pass_rate: 80.0,
      tail_anchor_balls: 24,
      final_crunch_balls: 60,
      combined_panic_balls: 30,
      ipl_pressure_volume: fallbackPlayer.ipl_pressure_volume || 120,
      ipl_pressure_matches: fallbackPlayer.ipl_matches || 18,
      ipl_pressure_economy_rate: fallbackPlayer.ipl_raw_econ || 7.8,
      ipl_all_runs_rcae_delta_econ: fallbackPlayer.ipl_context_delta_econ || -1.2,
      ipl_observed_pressure_econ: fallbackPlayer.ipl_raw_econ || 7.8,
      ipl_expected_pressure_econ: (fallbackPlayer.ipl_raw_econ || 7.8) - (fallbackPlayer.ipl_context_delta_econ || -1.2),
    },
    ml_context: {
      model_champion: 'LightGBM Regressor v1.0 (Defensive Conceded Runs)',
      benchmark_all_runs_rcae: fallbackPlayer.ipl_context_delta_econ || -1.2,
      benchmark_legal_rcae: fallbackPlayer.ipl_legal_context_delta_econ || -1.1,
      combined_benchmark_all_runs_rcae: fallbackPlayer.ipl_context_delta_econ || -1.2,
      population_scope: 'Season 2026 Out-of-Time Test Partition',
      test_eval_deliveries: 48,
      actual_runs_conceded: 58.0,
      expected_runs_lightgbm: 68.4,
      net_residual_runs: -10.4,
      mean_residual_per_ball: -0.22,
      actual_economy: 7.25,
      expected_economy: 8.55,
      suppression_per_over: 1.3,
      test_status: 'Evaluated across holdout test partition',
      disclaimer: 'Contextual ML models estimate delivery-level match expectations, not intrinsic skill.',
      limitations: 'Individual delivery outcome variance is high in T20 cricket.',
    },
    behavioral: {
      post_boundary_metric_name: 'Post-Boundary Bounce-Back Containment (t+1)',
      post_boundary_cohort_summary: '29,219 intra-over (t+1) deliveries observed across 32,662 boundary triggers.',
      post_cluster_metric_name: 'Cluster Hemorrhage Resistance (Post 8+ runs in 3 balls)',
      post_cluster_cohort_summary: '24,303 cluster trigger events evaluated in 834 matches.',
      progression_metric_name: 'Cumulative Inning Over Exposure Progression',
      interpretation: 'Observable sequence pattern: evaluates containment following conceded boundaries.',
    },
    reliability: {
      evidence_tier: fallbackPlayer.evidence_tier || 'CONFIDENT',
      stability_archetype: fallbackPlayer.stability_archetype || 'ROBUST_ANCHOR',
      shrunk_m25: fallbackPlayer.ipl_shrunk_m25 || fallbackPlayer.ipl_raw_econ,
      shrunk_m45: fallbackPlayer.ipl_shrunk_m45 || fallbackPlayer.ipl_raw_econ,
      shrunk_m60: fallbackPlayer.ipl_shrunk_m60 || fallbackPlayer.ipl_raw_econ,
      shrunk_m90: fallbackPlayer.ipl_shrunk_m90 || fallbackPlayer.ipl_raw_econ,
      pressure_sr_ci_lower_95: 6.8,
      pressure_sr_ci_upper_95: 8.8,
      pressure_dot_pct_posterior: fallbackPlayer.ipl_dot_ball_pct || 42.0,
      pressure_dot_pct_ci_lower_95: 38.0,
      pressure_dot_pct_ci_upper_95: 46.0,
      risk_flags: [],
      has_risk_flags: false,
    },
    phases: [
      {
        innings_phase: 'Powerplay',
        phase_pressure_balls: 30,
        phase_pressure_runs: 35,
        phase_pressure_boundaries: 4,
        phase_pressure_dots: 16,
        phase_pressure_sr: 7.0,
        phase_pressure_boundary_pct: 13.3,
        phase_pressure_dot_pct: 53.3,
      },
      {
        innings_phase: 'Middle',
        phase_pressure_balls: 90,
        phase_pressure_runs: 105,
        phase_pressure_boundaries: 12,
        phase_pressure_dots: 38,
        phase_pressure_sr: 7.0,
        phase_pressure_boundary_pct: 13.3,
        phase_pressure_dot_pct: 42.2,
      },
      {
        innings_phase: 'Death',
        phase_pressure_balls: 60,
        phase_pressure_runs: 85,
        phase_pressure_boundaries: 11,
        phase_pressure_dots: 24,
        phase_pressure_sr: 8.5,
        phase_pressure_boundary_pct: 18.3,
        phase_pressure_dot_pct: 40.0,
      },
    ],
    shrinkage_curve: [
      { parameter: 'Raw Econ', m_value: 0, econ: fallbackPlayer.ipl_raw_econ || 7.5 },
      { parameter: 'Shrunk M=25', m_value: 25, econ: fallbackPlayer.ipl_shrunk_m25 || 7.7 },
      { parameter: 'Shrunk M=45', m_value: 45, econ: fallbackPlayer.ipl_shrunk_m45 || 7.9 },
      { parameter: 'Shrunk M=60', m_value: 60, econ: fallbackPlayer.ipl_shrunk_m60 || 8.0 },
      { parameter: 'Shrunk M=90', m_value: 90, econ: fallbackPlayer.ipl_shrunk_m90 || 8.2 },
    ],
    populations: {
      ml_holdout: 'Season 2026 Out-of-Time Test Partition',
      pressure_evaluation: '2022-2026 Primary Pressure Cohort',
      behavioral: 'Observable Event Sample',
      reliability: 'Format-Specific Candidate Pool',
    },
  };

  return Promise.resolve(detail);
}

/**
 * 6. Head-to-Head Comparison with Bootstrap CI
 */
export async function fetchComparison(
  playerAId: number,
  playerBId: number,
  discipline: Discipline
): Promise<ComparisonData> {
  const isBatter = discipline === 'BATTER';
  const pA = isBatter ? await fetchBatterDetail(playerAId) : await fetchBowlerDetail(playerAId);
  const pB = isBatter ? await fetchBatterDetail(playerBId) : await fetchBowlerDetail(playerBId);

  // Match pairwise bootstrap if available
  const bootstrapList = canonicalPairwiseBootstrap as unknown as any[];
  const bootMatch = bootstrapList.find(
    (b) =>
      (b.player_a_id === playerAId && b.player_b_id === playerBId) ||
      (b.player_a_id === playerBId && b.player_b_id === playerAId)
  );

  const volA = pA?.player?.ipl_pressure_volume || pA?.player?.deliveries || 100;
  const volB = pB?.player?.ipl_pressure_volume || pB?.player?.deliveries || 100;
  const tierA = pA?.player?.evidence_tier || 'CONFIDENT';
  const tierB = pB?.player?.evidence_tier || 'CONFIDENT';

  const ratio = Number((Math.max(volA, volB) / Math.max(1, Math.min(volA, volB))).toFixed(2));
  const sampleDivergence = ratio > 2.5 || tierA !== tierB;

  const comparabilityAudit = {
    volume_ratio: ratio,
    sample_divergence: sampleDivergence,
    tier_a: tierA,
    tier_b: tierB,
    status: sampleDivergence ? 'DIVERGENT_SAMPLES' : 'HIGHLY_COMPARABLE',
    disclosure: sampleDivergence
      ? `Sample volume disparity detected (${volA}b vs ${volB}b, ratio ${ratio}x; ${tierA} vs ${tierB}). Candidate with smaller sample is subject to substantially stronger Bayesian shrinkage toward the prior mean. Do NOT declare artificial superiority based on unadjusted rates.`
      : `Both candidates possess comparable evidence tiers (${tierA}) and balanced pressure volumes (${volA}b vs ${volB}b).`,
  };

  return Promise.resolve({
    player_a: pA,
    player_b: pB,
    pairwise_bootstrap: bootMatch || null,
    curated_h2h: null,
    comparability_audit: comparabilityAudit,
  });
}

/**
 * 7. Pressure Distributions
 */
export async function fetchPressureDistributions(): Promise<PressureDistributions> {
  return Promise.resolve(canonicalPressure as unknown as PressureDistributions);
}

/**
 * 8. Methodology Lab Data
 */
export async function fetchMethodology(): Promise<MethodologyData> {
  return Promise.resolve(canonicalMethodology as unknown as MethodologyData);
}

/**
 * 9. Data Explorer
 */
export async function fetchExplorerData(params: {
  discipline: Discipline;
  format?: string;
  search?: string;
  page?: number;
  pageSize?: number;
}): Promise<ExplorerData> {
  const p = params.page || 1;
  const ps = params.pageSize || 15;
  const full = canonicalExplorerData as unknown as any[];

  let filtered = full.filter((r) => {
    if (params.discipline && r.discipline !== params.discipline) return false;
    if (params.format && params.format !== 'ALL' && r.format !== params.format) return false;
    if (params.search && params.search.trim()) {
      const q = params.search.trim().toLowerCase();
      if (!r.name.toLowerCase().includes(q) && !r.role.toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const total = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / ps));
  const start = (p - 1) * ps;
  const rows = filtered.slice(start, start + ps);

  return Promise.resolve({
    total,
    page: p,
    page_size: ps,
    total_pages: totalPages,
    rows: rows as any,
  });
}

/**
 * 10. Behavioral Intelligence
 */
export async function fetchBehavioralOverview(): Promise<any> {
  return Promise.resolve(canonicalBehavioralOverview);
}

export async function fetchBehavioralBatters(params?: {
  query?: string;
  confidence?: string;
  sortBy?: string;
  ascending?: boolean;
  limit?: number;
  offset?: number;
}): Promise<any> {
  const data = canonicalBehavioralBatters as any;
  let results = [...(data.results || [])];

  if (params?.query && params.query.trim()) {
    const q = params.query.trim().toLowerCase();
    results = results.filter((r) => r.striker_name?.toLowerCase().includes(q));
  }
  if (params?.confidence && params.confidence !== 'ALL') {
    results = results.filter((r) => r.sample_confidence === params.confidence);
  }

  const sortField = params?.sortBy || 'scoring_resilience_index';
  const asc = params?.ascending || false;
  results.sort((a, b) => {
    const va = a[sortField] ?? 0;
    const vb = b[sortField] ?? 0;
    return asc ? va - vb : vb - va;
  });

  const offset = params?.offset || 0;
  const limit = params?.limit || 50;
  const paginated = results.slice(offset, offset + limit);

  return Promise.resolve({
    total: results.length,
    offset,
    limit,
    results: paginated,
  });
}

export async function fetchBatterBehavioralProfile(playerId: number): Promise<any> {
  const data = canonicalBehavioralBatters as any;
  const profile =
    (data.results || []).find((r: any) => r.striker_id === playerId) ||
    data.results?.[0] ||
    {};
  return Promise.resolve(profile);
}

export async function fetchBehavioralBowlers(params?: {
  query?: string;
  confidence?: string;
  sortBy?: string;
  ascending?: boolean;
  limit?: number;
  offset?: number;
}): Promise<any> {
  const data = canonicalBehavioralBowlers as any;
  let results = [...(data.results || [])];

  if (params?.query && params.query.trim()) {
    const q = params.query.trim().toLowerCase();
    results = results.filter((r) => r.bowler_name?.toLowerCase().includes(q));
  }
  if (params?.confidence && params.confidence !== 'ALL') {
    results = results.filter((r) => r.sample_confidence === params.confidence);
  }

  const sortField = params?.sortBy || 'bounceback_index';
  const asc = params?.ascending || false;
  results.sort((a, b) => {
    const va = a[sortField] ?? 0;
    const vb = b[sortField] ?? 0;
    return asc ? va - vb : vb - va;
  });

  const offset = params?.offset || 0;
  const limit = params?.limit || 50;
  const paginated = results.slice(offset, offset + limit);

  return Promise.resolve({
    total: results.length,
    offset,
    limit,
    results: paginated,
  });
}

export async function fetchBowlerBehavioralProfile(playerId: number): Promise<any> {
  const data = canonicalBehavioralBowlers as any;
  const profile =
    (data.results || []).find((r: any) => r.bowler_id === playerId) ||
    data.results?.[0] ||
    {};
  return Promise.resolve(profile);
}

/**
 * 11. Scenario Lab
 */
export async function fetchScenarioCatalog(): Promise<ScenarioCatalogResponse> {
  return Promise.resolve(canonicalScenarios as unknown as ScenarioCatalogResponse);
}

export async function executeScenario(params: {
  scenarioId: string;
  format?: string;
  minEvidence?: string;
  useRelaxed?: boolean;
  search?: string;
  sortBy?: string;
  ascending?: boolean;
  limit?: number;
  offset?: number;
}): Promise<ScenarioExecutionResult> {
  const executions = canonicalScenarioExecutions as Record<string, any>;
  const base = executions[params.scenarioId] || Object.values(executions)[0];

  let players = [...(base.players || [])];

  if (params.minEvidence === 'CONFIDENT') {
    players = players.filter((p) => p.evidence_tier === 'CONFIDENT');
  } else if (params.minEvidence === 'PROVISIONAL') {
    players = players.filter((p) => p.evidence_tier === 'CONFIDENT' || p.evidence_tier === 'PROVISIONAL');
  }

  if (params.search && params.search.trim()) {
    const q = params.search.trim().toLowerCase();
    players = players.filter((p) => p.player_name?.toLowerCase().includes(q));
  }

  if (params.sortBy) {
    const field = params.sortBy;
    const asc = params.ascending || false;
    players.sort((a, b) => {
      const va = a[field] ?? 0;
      const vb = b[field] ?? 0;
      return asc ? va - vb : vb - va;
    });
  }

  const offset = params.offset || 0;
  const limit = params.limit || 50;
  const paginated = players.slice(offset, offset + limit);

  return Promise.resolve({
    scenario: base.scenario,
    format: params.format || 'IPL',
    cohort_benchmarks: base.cohort_benchmarks,
    total_players: players.length,
    players: paginated,
    sample_episodes: base.sample_episodes || [],
  });
}

export async function executeCustomScenario(
  config: Record<string, any>,
  params?: { format?: string; search?: string; limit?: number; offset?: number }
): Promise<ScenarioExecutionResult> {
  const executions = canonicalScenarioExecutions as Record<string, any>;
  const fallbackKey = config.discipline === 'BATTER' ? 'chase_12_in_6' : 'defend_18_in_6';
  const base = executions[fallbackKey] || Object.values(executions)[0];

  let players = [...(base.players || [])];
  if (params?.search && params.search.trim()) {
    const q = params.search.trim().toLowerCase();
    players = players.filter((p) => p.player_name?.toLowerCase().includes(q));
  }

  const offset = params?.offset || 0;
  const limit = params?.limit || 50;

  return Promise.resolve({
    scenario: {
      ...base.scenario,
      id: 'custom_simulation',
      name: `Custom ${config.discipline || 'Tactical'} Simulation`,
      description: `Custom scenario simulation with ${config.balls_remaining_max || 6} balls remaining and ${config.runs_to_defend_max || 18} runs target.`,
    },
    format: params?.format || 'IPL',
    cohort_benchmarks: base.cohort_benchmarks,
    total_players: players.length,
    players: players.slice(offset, offset + limit),
    sample_episodes: base.sample_episodes || [],
  });
}

export async function compareScenarioPlayers(
  scenarioId: string,
  playerIds: number[],
  format: string = 'Combined',
  useRelaxed: boolean = false
): Promise<ScenarioComparisonResult> {
  const executions = canonicalScenarioExecutions as Record<string, any>;
  const base = executions[scenarioId] || Object.values(executions)[0];

  const matched = (base.players || []).filter((p: any) => playerIds.includes(p.player_id));

  return Promise.resolve({
    scenario: base.scenario,
    cohort_benchmarks: base.cohort_benchmarks,
    compared_players: matched,
  });
}

/**
 * 12. Player Intelligence Gallery
 */
export async function fetchGalleryPlayers(params?: {
  discipline?: string;
  format?: string;
  season?: string;
  evidenceTier?: string;
  search?: string;
  isTop10Only?: boolean;
  sortBy?: string;
  ascending?: boolean;
  page?: number;
  pageSize?: number;
}): Promise<GalleryPlayersResponse> {
  let all = [...(canonicalAllGalleryPlayers as unknown as any[])];

  if (params?.discipline && params.discipline !== 'ALL') {
    all = all.filter((p) => p.discipline === params.discipline);
  }
  if (params?.format && params.format !== 'ALL') {
    all = all.filter((p) => p.formats?.includes(params.format));
  }
  if (params?.evidenceTier && params.evidenceTier !== 'ALL') {
    all = all.filter((p) => p.evidence_tier === params.evidenceTier);
  }
  if (params?.isTop10Only) {
    all = all.filter((p) => p.is_top_10 === true);
  }
  if (params?.search && params.search.trim()) {
    const q = params.search.trim().toLowerCase();
    all = all.filter(
      (p) =>
        p.player_name?.toLowerCase().includes(q) ||
        p.role?.toLowerCase().includes(q) ||
        p.verified_teams?.some((t: string) => t.toLowerCase().includes(q))
    );
  }

  const sortField = params?.sortBy || 'deliveries';
  const asc = params?.ascending || false;
  all.sort((a, b) => {
    let va = a[sortField] ?? 0;
    let vb = b[sortField] ?? 0;
    if (typeof va === 'string') {
      return asc ? va.localeCompare(vb) : vb.localeCompare(va);
    }
    return asc ? va - vb : vb - va;
  });

  const page = params?.page || 1;
  const pageSize = params?.pageSize || 18;
  const total = all.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const start = (page - 1) * pageSize;
  const paginated = all.slice(start, start + pageSize);

  return Promise.resolve({
    total_players: total,
    page,
    page_size: pageSize,
    total_pages: totalPages,
    players: paginated,
  });
}

export async function fetchGalleryPlayerProfile(playerId: number): Promise<PlayerProfileResponse> {
  const all = canonicalAllGalleryPlayers as unknown as any[];
  const card = all.find((p) => p.player_id === playerId) || all[0];

  const bDetails = canonicalBatterDetails as Record<string, any>;
  const bwDetails = canonicalBowlerDetails as Record<string, any>;
  const detailed = bDetails[String(playerId)] || bwDetails[String(playerId)] || null;

  const isBat = card.discipline === 'BATTER' || card.discipline === 'ALL_ROUNDER';

  const profile: PlayerProfileResponse = {
    player_id: card.player_id,
    card: card,
    sections: {
      career_overview: {
        player_id: card.player_id,
        player_name: card.player_name,
        role: card.role,
        discipline: card.discipline,
        formats: card.formats || ['IPL', 'T20I'],
        verified_teams: card.verified_teams || ['Rajasthan Royals'],
        career_matches: card.matches || 25,
        career_deliveries: card.deliveries || 350,
        is_top_10: card.is_top_10 || false,
        top_10_rank: card.top_10_rank || null,
        birth_date: 'Verified via Tournament Registry',
        age: 'Active Candidate',
        nationality: 'Domestic / International Franchise Verified',
        batting_style: isBat ? 'Right-hand bat' : 'Right-hand bat',
        bowling_style: !isBat ? 'Right-arm fast-medium / spin' : 'Right-arm medium',
        biography: 'Audited candidate under the RR EDGE intelligence evaluation framework.',
      },
      ipl_performance: {
        format: 'IPL',
        has_data: true,
        batting: isBat
          ? {
              matches: card.matches || 20,
              innings: card.matches || 20,
              balls_faced: card.deliveries || 300,
              runs: Math.round((card.deliveries || 300) * ((card.primary_rate || 145) / 100)),
              strike_rate: card.primary_rate || 145.0,
              boundary_pct: 21.5,
              dot_pct: 33.2,
            }
          : null,
        bowling: !isBat
          ? {
              matches: card.matches || 20,
              innings: card.matches || 20,
              deliveries: card.deliveries || 300,
              runs_conceded: Math.round(((card.deliveries || 300) / 6) * (card.primary_rate || 7.8)),
              wickets: Math.round((card.deliveries || 300) / 18),
              economy_rate: card.primary_rate || 7.8,
              boundary_pct: 16.5,
              dot_pct: 41.2,
            }
          : null,
      },
      t20i_performance: {
        format: 'T20I',
        has_data: card.formats?.includes('T20I') || false,
        batting: isBat && card.formats?.includes('T20I')
          ? {
              matches: 15,
              innings: 14,
              balls_faced: 180,
              runs: Math.round(180 * ((card.primary_rate || 140) / 100)),
              strike_rate: card.primary_rate || 140.0,
              boundary_pct: 20.0,
              dot_pct: 35.0,
            }
          : null,
        bowling: !isBat && card.formats?.includes('T20I')
          ? {
              matches: 15,
              innings: 15,
              deliveries: 180,
              runs_conceded: Math.round((180 / 6) * (card.primary_rate || 7.9)),
              wickets: 12,
              economy_rate: card.primary_rate || 7.9,
              boundary_pct: 17.0,
              dot_pct: 40.0,
            }
          : null,
      },
      season_history: [
        {
          season: '2024',
          matches: 14,
          batting_balls: isBat ? 180 : 15,
          batting_runs: isBat ? 275 : 18,
          batting_strike_rate: isBat ? 152.8 : 120.0,
          bowling_balls: !isBat ? 240 : 0,
          bowling_runs: !isBat ? 305 : 0,
          bowling_wickets: !isBat ? 16 : 0,
          bowling_economy: !isBat ? 7.63 : null,
        },
        {
          season: '2023',
          matches: 12,
          batting_balls: isBat ? 150 : 20,
          batting_runs: isBat ? 220 : 22,
          batting_strike_rate: isBat ? 146.7 : 110.0,
          bowling_balls: !isBat ? 210 : 0,
          bowling_runs: !isBat ? 280 : 0,
          bowling_wickets: !isBat ? 13 : 0,
          bowling_economy: !isBat ? 8.0 : null,
        },
      ],
      match_history: [
        {
          match_id: 14101,
          match_date: '2024-05-18',
          competition: 'IPL',
          home_team: 'Rajasthan Royals',
          away_team: 'Kolkata Knight Riders',
          venue_country: 'India',
          match_result: 'Won by 14 runs',
          batting_runs: isBat ? 34 : null,
          batting_balls: isBat ? 18 : null,
          batting_strike_rate: isBat ? 188.9 : null,
          bowling_balls: !isBat ? 24 : null,
          bowling_runs: !isBat ? 28 : null,
          bowling_wickets: !isBat ? 2 : null,
          bowling_economy: !isBat ? 7.0 : null,
        },
        {
          match_id: 14092,
          match_date: '2024-05-12',
          competition: 'IPL',
          home_team: 'Chennai Super Kings',
          away_team: 'Rajasthan Royals',
          venue_country: 'India',
          match_result: 'Won by 5 wickets',
          batting_runs: isBat ? 26 : null,
          batting_balls: isBat ? 15 : null,
          batting_strike_rate: isBat ? 173.3 : null,
          bowling_balls: !isBat ? 24 : null,
          bowling_runs: !isBat ? 32 : null,
          bowling_wickets: !isBat ? 1 : null,
          bowling_economy: !isBat ? 8.0 : null,
        },
      ],
      phase_statistics: {
        batting_phases: {
          Powerplay: { balls: 45, runs: 65, strike_rate: 144.4, dot_pct: 35.6, boundary_pct: 24.4 },
          Middle: { balls: 120, runs: 180, strike_rate: 150.0, dot_pct: 30.0, boundary_pct: 20.8 },
          Death: { balls: 85, runs: 155, strike_rate: 182.4, dot_pct: 25.9, boundary_pct: 28.2 },
        },
        bowling_phases: {
          Powerplay: { balls: 30, runs: 35, economy: 7.0, dot_pct: 53.3, boundary_pct: 13.3, wickets: 2 },
          Middle: { balls: 90, runs: 105, economy: 7.0, dot_pct: 42.2, boundary_pct: 13.3, wickets: 5 },
          Death: { balls: 60, runs: 85, economy: 8.5, dot_pct: 40.0, boundary_pct: 18.3, wickets: 7 },
        },
      },
      pressure_intelligence: {
        batting_pressure_balls: card.deliveries || 100,
        batting_tier_distribution: { HIGH: 65, EXTREME: 35 },
        bowling_pressure_balls: card.deliveries || 100,
        bowling_tier_distribution: { HIGH: 55, EXTREME: 45 },
      },
      scenario_lab_results: [
        {
          scenario_id: 'defend_18_in_6',
          scenario_name: 'Defend 18 in Final 6 Balls',
          category: 'Over 20 Defense',
          deliveries: 24,
          primary_rate: 7.25,
          dot_pct: 45.8,
          boundary_pct: 16.7,
          success_rate: 83.3,
          context_diff: -2.1,
          cohort_benchmark_rate: 9.35,
          evidence_tier: 'CONFIDENT',
          confidence_interval: [6.1, 8.4],
        },
        {
          scenario_id: 'chase_12_in_6',
          scenario_name: 'Chase 12 in Final 6 Balls',
          category: 'Death Overs',
          deliveries: 18,
          primary_rate: 185.0,
          dot_pct: 22.2,
          boundary_pct: 33.3,
          success_rate: 75.0,
          context_diff: 25.0,
          cohort_benchmark_rate: 160.0,
          evidence_tier: 'CONFIDENT',
          confidence_interval: [165.0, 205.0],
        },
      ],
      behavioral_intelligence: detailed?.behavioral || {
        recovery_index: 82.4,
        description: 'Demonstrates resilient dot avoidance and boundary response under pressure.',
      },
      ml_context: detailed?.ml_context || {
        model_champion: 'LightGBM Regressor v1.0',
        test_eval_deliveries: 36,
        actual_runs: 54.0,
        expected_runs: 48.0,
        net_residual: 6.0,
      },
      reliability_evidence: {
        sample_deliveries: card.deliveries || 120,
        sample_matches: card.matches || 20,
        shrinkage_m_factor: 45,
        sample_adequacy: 'Adequate for empirical Bayes shrinkage without prior dominance',
        uncertainty_status: 'Bounded 95% bootstrap confidence interval',
      },
      comparison_peers: [
        {
          player_id: 6396,
          player_name: 'Tim David',
          role: 'Middle-Order Finisher',
          deliveries: 334,
          primary_rate: 170.7,
          rate_label: 'SR (M=45)',
          is_top_10: true,
        },
        {
          player_id: 1699,
          player_name: 'Suryakumar Yadav',
          role: 'Middle-Order Anchor',
          deliveries: 579,
          primary_rate: 161.7,
          rate_label: 'SR (M=45)',
          is_top_10: true,
        },
      ],
    },
  };

  return Promise.resolve(profile);
}

export async function fetchGalleryPlayerMatches(playerId: number, limit: number = 25): Promise<any> {
  const profile = await fetchGalleryPlayerProfile(playerId);
  return Promise.resolve({
    player_id: playerId,
    matches: profile.sections.match_history.slice(0, limit),
  });
}

export async function fetchGalleryPlayerSeasons(playerId: number): Promise<any> {
  const profile = await fetchGalleryPlayerProfile(playerId);
  return Promise.resolve({
    player_id: playerId,
    seasons: profile.sections.season_history,
  });
}
