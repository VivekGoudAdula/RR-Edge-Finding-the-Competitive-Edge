/**
 * API client service for the RR EDGE Interactive 2D Cricket Simulator.
 */

import { BASE_URL } from './api';
import canonicalSimulatorPlayers from '../data/canonicalSimulatorPlayers.json';
import canonicalSimulatorScenarios from '../data/canonicalSimulatorScenarios.json';
import canonicalSimulatorPresets from '../data/canonicalSimulatorPresets.json';
import canonicalSimulatorSequences from '../data/canonicalSimulatorSequences.json';

async function safeFetchSim<T>(url: string, fallback: T): Promise<T> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 6000);
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(timer);
    if (!res.ok) return fallback;
    const ct = res.headers.get('content-type') || '';
    if (!ct.includes('application/json')) return fallback;
    const data = await res.json();
    return data || fallback;
  } catch {
    return fallback;
  }
}

export interface SimulatorPlayer {
  player_id: number;
  player_name: string;
  discipline: 'BATTER' | 'BOWLER' | 'ALL_ROUNDER';
  role: string;
  formats: string[];
  matches: number;
  bat_balls: number;
  bowl_balls: number;
  strike_rate: number | null;
  economy_rate: number | null;
  is_top_10: boolean;
  top_10_rank: number | null;
  teams: string[];
}

export interface PresetScenario {
  id: string;
  name: string;
  category: string;
  discipline: 'BATTER' | 'BOWLER';
  innings: number;
  balls_remaining: number;
  runs_to_defend: number;
  wickets_remaining: number;
  phase: string;
  fielding_preset: string;
  tactical_prompt: string;
}

export interface HistoricalSequenceMeta {
  sequence_id: string;
  match_id: number;
  format: string;
  comp_name: string;
  match_date: string;
  stage: string;
  innings: number;
  over_start: number;
  over_end: number;
  scenario_id: string;
  situation_title: string;
  key_striker_id: number;
  key_striker_name: string;
  key_bowler_id: number;
  key_bowler_name: string;
  runs_needed_start: number;
  balls_remaining_start: number;
  wickets_remaining_start: number;
  deliveries_count: number;
  total_runs_scored: number;
  total_wickets_fallen: number;
}

export interface DeliveryRecord {
  delivery_index: number;
  over_ball: string;
  striker: { id: number; name: string };
  non_striker: { id: number | null; name: string };
  bowler: { id: number; name: string };
  runs: number;
  extras: { type: string | null; runs: number };
  total_delivery_runs: number;
  is_wicket: boolean;
  dismissal_type: string | null;
  is_legal_ball: boolean;
  speed_kph: number;
  stroke: string;
  delivery_style: string;
  on_or_off: string;
  pitch_landing: { x: number; y: number; length_label: string; line_label: string };
  shot_trajectory: {
    start_x: number;
    start_y: number;
    target_x: number;
    target_y: number;
    is_boundary: boolean;
    is_six: boolean;
    stroke_category: string;
  };
  score_state: {
    current_score: number;
    wickets_lost: number;
    wickets_remaining: number;
    balls_remaining: number;
    runs_to_defend: number;
    pressure_tier: string;
  };
}

export interface HistoricalSequenceData {
  match_id: number;
  competition: string;
  comp_name: string;
  match_date: string;
  stage: string;
  innings: number;
  total_deliveries: number;
  final_runs: number;
  final_wickets: number;
  deliveries: DeliveryRecord[];
}

export interface WhatIfSimulationResult {
  illustrative_label: string;
  methodology_tier: 'empirical_player' | 'empirical_cohort' | 'contextual_ml_baseline';
  empirical_sample_sizes: {
    batter_phase_deliveries: number;
    bowler_phase_deliveries: number;
    cohort_phase_deliveries: number;
  };
  contextual_ml_baseline: {
    expected_runs_off_bat: number;
    expected_runs_conceded: number;
    wicket_probability: number;
    scope_disclosure: string;
  };
  delivery_result: {
    outcome_type: string;
    runs: number;
    extras: { type: string | null; runs: number };
    total_runs: number;
    is_wicket: boolean;
    dismissal_type: string | null;
    is_legal_ball: boolean;
    stroke: string;
    delivery_style: string;
    speed_kph: number;
    on_or_off: string;
    fielder_involved: string | null;
    pitch_landing: { x: number; y: number; length_label: string; line_label: string };
    shot_trajectory: {
      start_x: number;
      start_y: number;
      target_x: number;
      target_y: number;
      is_boundary: boolean;
      is_six: boolean;
      stroke_category: string;
    };
  };
  updated_state: {
    current_score: number;
    wickets_remaining: number;
    balls_remaining: number;
    runs_needed: number;
    match_outcome_status: string;
    is_match_over: boolean;
    strike_rotated?: boolean;
    over_completed?: boolean;
  };
}

export interface FielderPosition {
  id: number;
  name: string;
  x: number;
  y: number;
  role: 'boundary_rider' | 'ring' | 'catcher';
}

export interface FieldingPresets {
  death_protection: FielderPosition[];
  powerplay: FielderPosition[];
  attacking: FielderPosition[];
  defensive_spread: FielderPosition[];
}

export interface HeadToHeadAnalytics {
  format_scope: string;
  batter: {
    player_id: number;
    player_name: string;
    role: string;
    deliveries: number;
    distinct_matches: number;
    runs: number;
    strike_rate: number;
    dot_pct: number;
    boundary_pct: number;
    dismissal_frequency: number | null;
    evidence_tier: string;
    teams: string[];
  };
  bowler: {
    player_id: number;
    player_name: string;
    role: string;
    legal_balls: number;
    distinct_matches: number;
    runs_conceded: number;
    wickets: number;
    economy_rate: number;
    dot_pct: number;
    boundary_pct: number;
    wickets_per_over: number;
    evidence_tier: string;
    teams: string[];
  };
  direct_head_to_head: {
    balls_faced: number;
    runs_scored: number;
    dismissals: number;
    dots: number;
    boundaries: number;
    strike_rate: number | null;
    sample_label: string;
  };
}

export async function fetchSimulatorPlayers(params?: {
  discipline?: string;
  format?: string;
  search?: string;
  limit?: number;
}): Promise<SimulatorPlayer[]> {
  const query = new URLSearchParams();
  if (params?.discipline) query.append('discipline', params.discipline);
  if (params?.format) query.append('format', params.format);
  if (params?.search) query.append('search', params.search);
  if (params?.limit) query.append('limit', params.limit.toString());

  let fallback = canonicalSimulatorPlayers as unknown as SimulatorPlayer[];
  if (params?.discipline) {
    fallback = fallback.filter((p) => p.discipline === params.discipline);
  }
  if (params?.search) {
    const s = params.search.toLowerCase();
    fallback = fallback.filter((p) => p.player_name.toLowerCase().includes(s));
  }
  return safeFetchSim<SimulatorPlayer[]>(`${BASE_URL}/simulator/players?${query.toString()}`, fallback);
}

export async function fetchSimulatorScenarios(): Promise<PresetScenario[]> {
  return safeFetchSim<PresetScenario[]>(
    `${BASE_URL}/simulator/scenarios`,
    canonicalSimulatorScenarios as unknown as PresetScenario[]
  );
}

export async function fetchSimulatorHistoricalSequences(params?: {
  format?: string;
  scenario_type?: string;
  limit?: number;
}): Promise<HistoricalSequenceMeta[]> {
  const query = new URLSearchParams();
  if (params?.format) query.append('format', params.format);
  if (params?.scenario_type) query.append('scenario_type', params.scenario_type);
  if (params?.limit) query.append('limit', params.limit.toString());

  return safeFetchSim<HistoricalSequenceMeta[]>(
    `${BASE_URL}/simulator/historical/sequences?${query.toString()}`,
    canonicalSimulatorSequences as unknown as HistoricalSequenceMeta[]
  );
}

export async function fetchSimulatorSequenceDeliveries(
  matchId: number,
  params?: { innings?: number; over_start?: number; over_end?: number }
): Promise<HistoricalSequenceData> {
  const query = new URLSearchParams();
  if (params?.innings) query.append('innings', params.innings.toString());
  if (params?.over_start) query.append('over_start', params.over_start.toString());
  if (params?.over_end) query.append('over_end', params.over_end.toString());

  const res = await fetch(`${BASE_URL}/simulator/historical/match/${matchId}/sequence?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch sequence deliveries');
  return res.json();
}

export async function simulateWhatIfDelivery(payload: {
  format: string;
  innings: number;
  batter_id: number;
  bowler_id: number;
  balls_remaining: number;
  runs_to_defend: number;
  wickets_remaining: number;
  current_score: number;
  target_runs?: number;
  previous_context?: string;
  fielding_preset?: string;
  fielders?: FielderPosition[];
}): Promise<WhatIfSimulationResult> {
  const res = await fetch(`${BASE_URL}/simulator/simulate/delivery`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to simulate delivery');
  return res.json();
}

export async function fetchSimulatorHeadToHead(
  batterId: number,
  bowlerId: number,
  format: string = 'ALL'
): Promise<HeadToHeadAnalytics> {
  const res = await fetch(
    `${BASE_URL}/simulator/analytics/head-to-head?batter_id=${batterId}&bowler_id=${bowlerId}&format=${format}`
  );
  if (!res.ok) throw new Error('Failed to fetch head-to-head analytics');
  return res.json();
}

export async function fetchSimulatorFieldingPresets(): Promise<FieldingPresets> {
  return safeFetchSim<FieldingPresets>(
    `${BASE_URL}/simulator/fielding/presets`,
    canonicalSimulatorPresets as unknown as FieldingPresets
  );
}

