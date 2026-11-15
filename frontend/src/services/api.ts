import {
  OverviewData,
  PlayerOverview,
  PlayerDetail,
  ComparisonData,
  PressureDistributions,
  MethodologyData,
  ExplorerData,
  Discipline,
} from '../types';

const BASE_URL = '/api';

export async function fetchOverview(): Promise<OverviewData> {
  const res = await fetch(`${BASE_URL}/overview`);
  if (!res.ok) throw new Error('Failed to fetch overview data');
  return res.json();
}

export async function fetchBatters(params?: {
  format?: string;
  role?: string;
  search?: string;
  tier?: string;
}): Promise<PlayerOverview[]> {
  const query = new URLSearchParams();
  if (params?.format) query.append('format', params.format);
  if (params?.role && params.role !== 'ALL') query.append('role', params.role);
  if (params?.search) query.append('search', params.search);
  if (params?.tier && params.tier !== 'ALL') query.append('tier', params.tier);

  const res = await fetch(`${BASE_URL}/batters?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch batters');
  return res.json();
}

export async function fetchBatterDetail(playerId: number): Promise<PlayerDetail> {
  const res = await fetch(`${BASE_URL}/batters/${playerId}`);
  if (!res.ok) throw new Error(`Failed to fetch batter detail for ${playerId}`);
  return res.json();
}

export async function fetchBowlers(params?: {
  format?: string;
  role?: string;
  search?: string;
  tier?: string;
}): Promise<PlayerOverview[]> {
  const query = new URLSearchParams();
  if (params?.format) query.append('format', params.format);
  if (params?.role && params.role !== 'ALL') query.append('role', params.role);
  if (params?.search) query.append('search', params.search);
  if (params?.tier && params.tier !== 'ALL') query.append('tier', params.tier);

  const res = await fetch(`${BASE_URL}/bowlers?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch bowlers');
  return res.json();
}

export async function fetchBowlerDetail(playerId: number): Promise<PlayerDetail> {
  const res = await fetch(`${BASE_URL}/bowlers/${playerId}`);
  if (!res.ok) throw new Error(`Failed to fetch bowler detail for ${playerId}`);
  return res.json();
}

export async function fetchComparison(
  playerAId: number,
  playerBId: number,
  discipline: Discipline
): Promise<ComparisonData> {
  const query = new URLSearchParams({
    player_a_id: playerAId.toString(),
    player_b_id: playerBId.toString(),
    discipline: discipline,
  });

  const res = await fetch(`${BASE_URL}/comparisons?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch player comparison');
  return res.json();
}

export async function fetchPressureDistributions(): Promise<PressureDistributions> {
  const res = await fetch(`${BASE_URL}/pressure/distributions`);
  if (!res.ok) throw new Error('Failed to fetch pressure distributions');
  return res.json();
}

export async function fetchMethodology(): Promise<MethodologyData> {
  const res = await fetch(`${BASE_URL}/methodology`);
  if (!res.ok) throw new Error('Failed to fetch methodology data');
  return res.json();
}

export async function fetchExplorerData(params: {
  discipline: Discipline;
  format?: string;
  search?: string;
  page?: number;
  pageSize?: number;
}): Promise<ExplorerData> {
  const query = new URLSearchParams({
    discipline: params.discipline,
    page: (params.page || 1).toString(),
    page_size: (params.pageSize || 15).toString(),
  });
  if (params.format) query.append('format', params.format);
  if (params.search) query.append('search', params.search);

  const res = await fetch(`${BASE_URL}/explorer?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch explorer records');
  return res.json();
}

// -------------------------------------------------------------
// Behavioral Pressure Intelligence API Calls
// -------------------------------------------------------------
export async function fetchBehavioralOverview(): Promise<any> {
  const res = await fetch(`${BASE_URL}/behavioral/overview`);
  if (!res.ok) throw new Error('Failed to fetch behavioral overview');
  return res.json();
}

export async function fetchBehavioralBatters(params?: {
  query?: string;
  confidence?: string;
  sortBy?: string;
  ascending?: boolean;
  limit?: number;
  offset?: number;
}): Promise<any> {
  const query = new URLSearchParams();
  if (params?.query) query.append('query', params.query);
  if (params?.confidence && params.confidence !== 'ALL') query.append('confidence', params.confidence);
  if (params?.sortBy) query.append('sort_by', params.sortBy);
  if (params?.ascending !== undefined) query.append('ascending', params.ascending.toString());
  if (params?.limit) query.append('limit', params.limit.toString());
  if (params?.offset) query.append('offset', params.offset.toString());

  const res = await fetch(`${BASE_URL}/behavioral/batters?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch behavioral batters');
  return res.json();
}

export async function fetchBatterBehavioralProfile(playerId: number): Promise<any> {
  const res = await fetch(`${BASE_URL}/behavioral/batters/${playerId}`);
  if (!res.ok) throw new Error(`Failed to fetch batter behavioral profile for ${playerId}`);
  return res.json();
}

export async function fetchBehavioralBowlers(params?: {
  query?: string;
  confidence?: string;
  sortBy?: string;
  ascending?: boolean;
  limit?: number;
  offset?: number;
}): Promise<any> {
  const query = new URLSearchParams();
  if (params?.query) query.append('query', params.query);
  if (params?.confidence && params.confidence !== 'ALL') query.append('confidence', params.confidence);
  if (params?.sortBy) query.append('sort_by', params.sortBy);
  if (params?.ascending !== undefined) query.append('ascending', params.ascending.toString());
  if (params?.limit) query.append('limit', params.limit.toString());
  if (params?.offset) query.append('offset', params.offset.toString());

  const res = await fetch(`${BASE_URL}/behavioral/bowlers?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch behavioral bowlers');
  return res.json();
}

export async function fetchBowlerBehavioralProfile(playerId: number): Promise<any> {
  const res = await fetch(`${BASE_URL}/behavioral/bowlers/${playerId}`);
  if (!res.ok) throw new Error(`Failed to fetch bowler behavioral profile for ${playerId}`);
  return res.json();
}

// -------------------------------------------------------------
// Scenario Lab API Methods
// -------------------------------------------------------------
export async function fetchScenarioCatalog(): Promise<any> {
  const res = await fetch(`${BASE_URL}/scenarios/catalog`);
  if (!res.ok) throw new Error('Failed to fetch scenario catalog');
  return res.json();
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
}): Promise<any> {
  const query = new URLSearchParams({ scenario_id: params.scenarioId });
  if (params.format) query.append('format', params.format);
  if (params.minEvidence) query.append('min_evidence', params.minEvidence);
  if (params.useRelaxed !== undefined) query.append('use_relaxed', params.useRelaxed.toString());
  if (params.search) query.append('search', params.search);
  if (params.sortBy) query.append('sort_by', params.sortBy);
  if (params.ascending !== undefined) query.append('ascending', params.ascending.toString());
  if (params.limit) query.append('limit', params.limit.toString());
  if (params.offset) query.append('offset', params.offset.toString());

  const res = await fetch(`${BASE_URL}/scenarios/execute?${query.toString()}`);
  if (!res.ok) throw new Error(`Failed to execute scenario ${params.scenarioId}`);
  return res.json();
}

export async function executeCustomScenario(
  config: Record<string, any>,
  params?: { format?: string; search?: string; limit?: number; offset?: number }
): Promise<any> {
  const query = new URLSearchParams();
  if (params?.format) query.append('format', params.format);
  if (params?.search) query.append('search', params.search);
  if (params?.limit) query.append('limit', params.limit.toString());
  if (params?.offset) query.append('offset', params.offset.toString());

  const res = await fetch(`${BASE_URL}/scenarios/custom?${query.toString()}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error('Failed to execute custom scenario');
  return res.json();
}

export async function compareScenarioPlayers(
  scenarioId: string,
  playerIds: number[],
  format: string = 'Combined',
  useRelaxed: boolean = false
): Promise<any> {
  const query = new URLSearchParams({
    scenario_id: scenarioId,
    player_ids: playerIds.join(','),
    format: format,
    use_relaxed: useRelaxed.toString(),
  });
  const res = await fetch(`${BASE_URL}/scenarios/compare?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to compare players on scenario');
  return res.json();
}

// -------------------------------------------------------------
// Player Intelligence Gallery API Methods
// -------------------------------------------------------------
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
}): Promise<any> {
  const query = new URLSearchParams();
  if (params?.discipline && params.discipline !== 'ALL') query.append('discipline', params.discipline);
  if (params?.format && params.format !== 'ALL') query.append('format', params.format);
  if (params?.season && params.season !== 'ALL') query.append('season', params.season);
  if (params?.evidenceTier && params.evidenceTier !== 'ALL') query.append('evidence_tier', params.evidenceTier);
  if (params?.search) query.append('search', params.search);
  if (params?.isTop10Only) query.append('is_top_10_only', 'true');
  if (params?.sortBy) query.append('sort_by', params.sortBy);
  if (params?.ascending !== undefined) query.append('ascending', params.ascending.toString());
  if (params?.page) query.append('page', params.page.toString());
  if (params?.pageSize) query.append('page_size', params.pageSize.toString());

  const res = await fetch(`${BASE_URL}/gallery/players?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch gallery players');
  return res.json();
}

export async function fetchGalleryPlayerProfile(playerId: number): Promise<any> {
  const res = await fetch(`${BASE_URL}/gallery/players/${playerId}`);
  if (!res.ok) throw new Error(`Failed to fetch player profile for ${playerId}`);
  return res.json();
}

export async function fetchGalleryPlayerMatches(playerId: number, limit: number = 25): Promise<any> {
  const res = await fetch(`${BASE_URL}/gallery/players/${playerId}/matches?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch player matches for ${playerId}`);
  return res.json();
}

export async function fetchGalleryPlayerSeasons(playerId: number): Promise<any> {
  const res = await fetch(`${BASE_URL}/gallery/players/${playerId}/seasons`);
  if (!res.ok) throw new Error(`Failed to fetch player seasons for ${playerId}`);
  return res.json();
}



