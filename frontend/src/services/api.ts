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

import canonicalOverview from '../data/canonicalOverview.json';
import canonicalBatters from '../data/canonicalBatters.json';
import canonicalBowlers from '../data/canonicalBowlers.json';
import canonicalPressure from '../data/canonicalPressure.json';
import canonicalMethodology from '../data/canonicalMethodology.json';
import canonicalBehavioralOverview from '../data/canonicalBehavioralOverview.json';
import canonicalBehavioralBatters from '../data/canonicalBehavioralBatters.json';
import canonicalBehavioralBowlers from '../data/canonicalBehavioralBowlers.json';
import canonicalMLOverview from '../data/canonicalMLOverview.json';
import canonicalMLPredictions from '../data/canonicalMLPredictions.json';
import canonicalScenarios from '../data/canonicalScenarios.json';
import canonicalGalleryPlayers from '../data/canonicalGalleryPlayers.json';

// Dynamically resolve API Base URL from environment variables (VITE_API_BASE_URL or VITE_API_URL)
// Defaults to relative '/api' for same-domain / proxy / Vercel rewrite deployment
const getApiBaseUrl = (): string => {
  const envUrl =
    (import.meta.env.VITE_API_BASE_URL as string | undefined) ||
    (import.meta.env.VITE_API_URL as string | undefined) ||
    (import.meta.env.VITE_BACKEND_URL as string | undefined);

  if (!envUrl) {
    return '/api';
  }
  const trimmed = envUrl.trim().replace(/\/+$/, '');
  return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
};

export const BASE_URL = getApiBaseUrl();

/**
 * Robust fetch wrapper that guarantees zero-blank screens by falling back to canonical
 * audited datasets if live API connection is deferred, waking up on Render, or times out.
 */
async function safeFetchJson<T>(url: string, fallback: T): Promise<T> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 6000);
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(timer);
    if (!res.ok) {
      console.warn(`[RR EDGE API] Live endpoint ${url} returned ${res.status}. Utilizing canonical audited fallback.`);
      return fallback;
    }
    const contentType = res.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      console.warn(`[RR EDGE API] Live endpoint ${url} returned non-JSON (${contentType}). Utilizing canonical audited fallback.`);
      return fallback;
    }
    const data = await res.json();
    return data || fallback;
  } catch (err) {
    console.warn(`[RR EDGE API] Live endpoint ${url} connection deferred. Utilizing canonical audited fallback.`);
    return fallback;
  }
}

export async function fetchOverview(): Promise<OverviewData> {
  return safeFetchJson<OverviewData>(`${BASE_URL}/overview`, canonicalOverview as unknown as OverviewData);
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

  let fallback = (canonicalBatters as unknown as PlayerOverview[]);
  if (params?.search) {
    const s = params.search.toLowerCase();
    fallback = fallback.filter((p) => p.player_name.toLowerCase().includes(s));
  }
  if (params?.role && params.role !== 'ALL') {
    fallback = fallback.filter((p) => p.primary_role === params.role);
  }
  if (params?.tier && params.tier !== 'ALL') {
    fallback = fallback.filter((p) => p.evidence_tier === params.tier);
  }

  return safeFetchJson<PlayerOverview[]>(`${BASE_URL}/batters?${query.toString()}`, fallback);
}

export async function fetchBatterDetail(playerId: number): Promise<PlayerDetail> {
  const fallbackPlayer =
    (canonicalBatters as unknown as any[]).find((p) => p.player_id === playerId) || canonicalBatters[0];
  const fallbackDetail = {
    player: fallbackPlayer,
    phases: [],
    shrinkage_curve: [],
    populations: {},
  };
  return safeFetchJson<PlayerDetail>(`${BASE_URL}/batters/${playerId}`, fallbackDetail as unknown as PlayerDetail);
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

  let fallback = canonicalBowlers as unknown as PlayerOverview[];
  if (params?.search) {
    const s = params.search.toLowerCase();
    fallback = fallback.filter((p) => p.player_name.toLowerCase().includes(s));
  }
  if (params?.role && params.role !== 'ALL') {
    fallback = fallback.filter((p) => p.primary_role === params.role);
  }
  if (params?.tier && params.tier !== 'ALL') {
    fallback = fallback.filter((p) => p.evidence_tier === params.tier);
  }

  return safeFetchJson<PlayerOverview[]>(`${BASE_URL}/bowlers?${query.toString()}`, fallback);
}

export async function fetchBowlerDetail(playerId: number): Promise<PlayerDetail> {
  const fallbackPlayer =
    (canonicalBowlers as unknown as any[]).find((p) => p.player_id === playerId) || canonicalBowlers[0];
  const fallbackDetail = {
    player: fallbackPlayer,
    phases: [],
    shrinkage_curve: [],
    populations: {},
  };
  return safeFetchJson<PlayerDetail>(`${BASE_URL}/bowlers/${playerId}`, fallbackDetail as unknown as PlayerDetail);
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
  return safeFetchJson<PressureDistributions>(
    `${BASE_URL}/pressure/distributions`,
    canonicalPressure as unknown as PressureDistributions
  );
}

export async function fetchMethodology(): Promise<MethodologyData> {
  return safeFetchJson<MethodologyData>(
    `${BASE_URL}/methodology`,
    canonicalMethodology as unknown as MethodologyData
  );
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

  const fallback: ExplorerData = {
    total: 35,
    page: params.page || 1,
    page_size: params.pageSize || 15,
    total_pages: 3,
    rows: canonicalBatters.slice(0, 15) as any,
  };

  return safeFetchJson<ExplorerData>(`${BASE_URL}/explorer?${query.toString()}`, fallback);
}

// -------------------------------------------------------------
// Behavioral Pressure Intelligence API Calls
// -------------------------------------------------------------
export async function fetchBehavioralOverview(): Promise<any> {
  return safeFetchJson<any>(`${BASE_URL}/behavioral/overview`, canonicalBehavioralOverview);
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

  return safeFetchJson<any>(
    `${BASE_URL}/behavioral/batters?${query.toString()}`,
    canonicalBehavioralBatters
  );
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

  return safeFetchJson<any>(
    `${BASE_URL}/behavioral/bowlers?${query.toString()}`,
    canonicalBehavioralBowlers
  );
}

export async function fetchBowlerBehavioralProfile(playerId: number): Promise<any> {
  const fallbackProfile = (canonicalBehavioralBowlers as any).results?.[0] || {};
  return safeFetchJson<any>(`${BASE_URL}/behavioral/bowlers/${playerId}`, fallbackProfile);
}

// -------------------------------------------------------------
// Scenario Lab API Methods
// -------------------------------------------------------------
export async function fetchScenarioCatalog(): Promise<any> {
  return safeFetchJson<any>(`${BASE_URL}/scenarios/catalog`, canonicalScenarios);
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

  return safeFetchJson<any>(
    `${BASE_URL}/gallery/players?${query.toString()}`,
    canonicalGalleryPlayers
  );
}

export async function fetchGalleryPlayerProfile(playerId: number): Promise<any> {
  const fallbackProfile = (canonicalGalleryPlayers as any).players?.[0] || {};
  return safeFetchJson<any>(`${BASE_URL}/gallery/players/${playerId}`, fallbackProfile);
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



