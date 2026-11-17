import React, { useState, useEffect } from 'react';
import {
  Target,
  Shield,
  Swords,
  Filter,
  Search,
  Sliders,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  HelpCircle,
  ExternalLink,
  GitCompare,
  TrendingUp,
  TrendingDown,
  Layers,
  Clock,
  Award,
  X,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  fetchScenarioCatalog,
  executeScenario,
  executeCustomScenario,
  compareScenarioPlayers,
} from '../services/api';
import canonicalScenarios from '../data/canonicalScenarios.json';
import canonicalScenarioExecutions from '../data/canonicalScenarioExecutions.json';
import {
  ScenarioCatalogResponse,
  ScenarioDefinition,
  ScenarioExecutionResult,
  ScenarioPlayer,
  ScenarioEpisode,
} from '../types';
import { PageHeroCard } from '../components/common/PageHeroCard';

const FALLBACK_BOWLING_SCENARIOS: any[] = [
  { id: 'defend_18_in_6', name: 'Defend 18 Runs in Final 6 Balls', category: 'Death Overs', discipline: 'BOWLER' },
  { id: 'defend_12_in_2', name: 'Defend 12 Runs in Final 2 Balls', category: 'Death Overs', discipline: 'BOWLER' },
  { id: 'defend_10_in_3', name: 'Defend 10 Runs in Final 3 Balls', category: 'Death Overs', discipline: 'BOWLER' },
  { id: 'post_boundary_response', name: 'Post-Boundary Response', category: 'Behavioral Recovery', discipline: 'BOWLER' },
  { id: 'post_cluster_response', name: 'Post-Cluster Response (2+ Boundaries)', category: 'Behavioral Recovery', discipline: 'BOWLER' },
  { id: 'defend_small_target_tail', name: 'Defend Small Target Tail (8+ Wickets)', category: 'Target Defence', discipline: 'BOWLER' },
  { id: 'defend_high_rrr_wickets_in_hand', name: 'Defend High RRR (>12) Wickets in Hand', category: 'High RRR Defence', discipline: 'BOWLER' },
  { id: 'death_extreme_containment', name: 'Death Extreme Containment (Overs 19-20)', category: 'Death Overs', discipline: 'BOWLER' },
];

const FALLBACK_BATTING_SCENARIOS: any[] = [
  { id: 'chase_12_in_6', name: 'Chase 12 Runs in Final 6 Balls', category: 'Death Overs', discipline: 'BATTER' },
  { id: 'chase_18_in_12', name: 'Chase 18 Runs in Final 12 Balls', category: 'Death Overs', discipline: 'BATTER' },
  { id: 'chase_30_in_18', name: 'Chase 30 Runs in Final 18 Balls', category: 'Death Overs', discipline: 'BATTER' },
  { id: 'post_wicket_recovery', name: 'Post-Wicket Recovery', category: 'Behavioral Shock', discipline: 'BATTER' },
  { id: 'post_dot_drought_recovery', name: 'Post-Dot Drought Recovery (3+ Dots)', category: 'Behavioral Shock', discipline: 'BATTER' },
  { id: 'sharp_rrr_surge', name: 'Sharp RRR Surge (+2.0 in 2 Overs)', category: 'Pressure Surge', discipline: 'BATTER' },
  { id: 'death_acceleration_wickets_in_hand', name: 'Death Acceleration (Overs 16-20, 6+ Wkts)', category: 'Power Surge', discipline: 'BATTER' },
  { id: 'preserve_wickets_high_rrr', name: 'Preserve Wickets Under High RRR (>10)', category: 'Crisis Management', discipline: 'BATTER' },
];

interface ScenarioLabProps {
  onNavigateToGallery?: (playerId: number) => void;
}

export const ScenarioLab: React.FC<ScenarioLabProps> = ({ onNavigateToGallery }) => {
  const [catalog, setCatalog] = useState<ScenarioCatalogResponse | null>(
    canonicalScenarios as unknown as ScenarioCatalogResponse
  );
  const [selectedDiscipline, setSelectedDiscipline] = useState<'BOWLER' | 'BATTER'>('BOWLER');
  const [activeScenarioId, setActiveScenarioId] = useState<string>('defend_18_in_6');
  const [formatFilter, setFormatFilter] = useState<string>('IPL');
  const [minEvidence, setMinEvidence] = useState<string>('ALL');
  const [useRelaxed, setUseRelaxed] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  
  // Results
  const [loading, setLoading] = useState<boolean>(false);
  const [executionError, setExecutionError] = useState<string | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [results, setResults] = useState<ScenarioExecutionResult | null>(
    (canonicalScenarioExecutions as Record<string, any>)['defend_18_in_6'] as unknown as ScenarioExecutionResult
  );

  // Custom scenario builder state
  const [customModalOpen, setCustomModalOpen] = useState<boolean>(false);
  const [customConfig, setCustomConfig] = useState<Record<string, any>>({
    discipline: 'BOWLER',
    runs_to_defend_max: 18,
    balls_remaining_max: 6,
    wickets_remaining_max: 10,
    innings: 2,
    innings_phase: 'Death',
    previous_context: 'none',
  });

  // Comparison state
  const [comparisonModalOpen, setComparisonModalOpen] = useState<boolean>(false);
  const [selectedForCompare, setSelectedForCompare] = useState<number[]>([]);
  const [comparisonData, setComparisonData] = useState<any>(null);
  const [comparingLoading, setComparingLoading] = useState<boolean>(false);

  // Historical Episodes Drawer state
  const [episodesOpen, setEpisodesOpen] = useState<boolean>(false);

  // Load catalog on mount
  useEffect(() => {
    async function loadCatalog() {
      try {
        setCatalogError(null);
        const cat = await fetchScenarioCatalog();
        setCatalog(cat);
      } catch (err: any) {
        setCatalogError(err.message || 'Failed to load scenario catalog');
      }
    }
    loadCatalog();
  }, []);

  // Fetch results when scenario or filters change
  useEffect(() => {
    async function runScenario() {
      if (!activeScenarioId) return;
      setLoading(true);
      setExecutionError(null);
      try {
        if (activeScenarioId === 'custom') {
          const res = await executeCustomScenario(customConfig, {
            format: formatFilter,
            search: searchQuery,
            limit: 100,
          });
          setResults(res);
        } else {
          const res = await executeScenario({
            scenarioId: activeScenarioId,
            format: formatFilter,
            minEvidence: minEvidence,
            useRelaxed: useRelaxed,
            search: searchQuery,
            limit: 100,
          });
          setResults(res);
        }
      } catch (err: any) {
        setExecutionError(err.message || 'Failed to execute scenario');
      } finally {
        setLoading(false);
      }
    }
    runScenario();
  }, [activeScenarioId, formatFilter, minEvidence, useRelaxed, searchQuery]);

  // Handle player selection for comparison
  const togglePlayerComparison = (playerId: number) => {
    if (selectedForCompare.includes(playerId)) {
      setSelectedForCompare(selectedForCompare.filter((id) => id !== playerId));
    } else {
      if (selectedForCompare.length >= 4) {
        alert('You can compare at most 4 players simultaneously.');
        return;
      }
      setSelectedForCompare([...selectedForCompare, playerId]);
    }
  };

  // Run multi-player comparison
  const handleOpenComparison = async () => {
    if (selectedForCompare.length < 2) {
      alert('Please select at least 2 players from the table to compare.');
      return;
    }
    setComparingLoading(true);
    setComparisonModalOpen(true);
    try {
      const comp = await compareScenarioPlayers(
        activeScenarioId,
        selectedForCompare,
        formatFilter,
        useRelaxed
      );
      setComparisonData(comp);
    } catch (err: any) {
      alert('Failed to compare players: ' + err.message);
    } finally {
      setComparingLoading(false);
    }
  };

  const currentScenarios =
    catalog && (selectedDiscipline === 'BOWLER' ? catalog.bowling_scenarios : catalog.batting_scenarios)?.length
      ? (selectedDiscipline === 'BOWLER' ? catalog.bowling_scenarios : catalog.batting_scenarios)
      : (selectedDiscipline === 'BOWLER' ? FALLBACK_BOWLING_SCENARIOS : FALLBACK_BATTING_SCENARIOS);

  return (
    <div className="space-y-6">
      {/* Standardized Compact Hero Section */}
      <PageHeroCard
        badge="Grounded Simulation"
        badgeIcon={<Target className="w-3.5 h-3.5 text-rr-pink" />}
        badgeContext="Standardized Hypothetical Match States"
        title="Scenario Lab"
        description="Stress-test every eligible batter and bowler against standardized match crucibles using actual historical ball-by-ball contexts."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => {
                setCustomModalOpen(true);
              }}
              className="px-3 py-1.5 bg-white/10 text-white border border-white/20 text-xs font-semibold rounded-lg hover:bg-white/20 transition shadow-sm flex items-center gap-1.5"
            >
              <Sliders className="w-3.5 h-3.5 text-rr-gold" />
              Custom Scenario Builder
            </button>
            {results?.sample_episodes && results.sample_episodes.length > 0 && (
              <button
                onClick={() => setEpisodesOpen(true)}
                className="px-3 py-1.5 bg-white/10 text-white border border-white/20 text-xs font-semibold rounded-lg hover:bg-white/20 transition shadow-sm flex items-center gap-1.5"
              >
                <Layers className="w-3.5 h-3.5 text-rr-pink" />
                Historical Episodes ({results.sample_episodes.length})
              </button>
            )}
          </div>
        }
      />

      {/* Scenario Selection Deck */}
      <div className="bg-white rounded-xl shadow-card border border-rr-border p-4">
        {/* Discipline Tabs */}
        <div className="flex items-center gap-3 border-b border-gray-100 pb-3">
          <button
            type="button"
            onClick={() => {
              setSelectedDiscipline('BOWLER');
              setActiveScenarioId('defend_18_in_6');
              setSelectedForCompare([]);
            }}
            style={
              selectedDiscipline === 'BOWLER'
                ? { backgroundColor: '#0B192C', color: '#FFFFFF', borderColor: '#0B192C' }
                : { backgroundColor: '#FFFFFF', color: '#25212A', borderColor: '#E2E8F0' }
            }
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition border ${
              selectedDiscipline === 'BOWLER'
                ? 'bg-rr-navy text-white shadow-sm border-rr-navy'
                : 'text-slate-800 hover:bg-slate-100 border-slate-200'
            }`}
          >
            <Shield className="w-4 h-4 text-rr-gold" />
            <span>Bowling Scenarios (8)</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setSelectedDiscipline('BATTER');
              setActiveScenarioId('chase_12_in_6');
              setSelectedForCompare([]);
            }}
            style={
              selectedDiscipline === 'BATTER'
                ? { backgroundColor: '#E6007E', color: '#FFFFFF', borderColor: '#E6007E' }
                : { backgroundColor: '#FFFFFF', color: '#25212A', borderColor: '#E2E8F0' }
            }
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition border ${
              selectedDiscipline === 'BATTER'
                ? 'bg-rr-pink text-white shadow-sm border-rr-pink'
                : 'text-slate-800 hover:bg-slate-100 border-slate-200'
            }`}
          >
            <Swords className="w-4 h-4 text-white" />
            <span>Batting Scenarios (8)</span>
          </button>
        </div>

        {/* Scenario Carousel / Quick Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 mt-4">
          {currentScenarios.map((scen: ScenarioDefinition) => {
            const isSelected = activeScenarioId === scen.id;
            return (
              <button
                type="button"
                key={scen.id}
                onClick={() => {
                  setActiveScenarioId(scen.id);
                  setSelectedForCompare([]);
                }}
                style={
                  isSelected
                    ? {
                        backgroundColor: '#0B192C',
                        color: '#FFFFFF',
                        borderColor: '#D4AF37',
                        borderWidth: '1.5px',
                        boxShadow: '0 4px 12px rgba(11, 25, 44, 0.25)',
                      }
                    : {
                        backgroundColor: '#FFFFFF',
                        color: '#25212A',
                        borderColor: '#E2E8F0',
                        borderWidth: '1px',
                      }
                }
                className={`p-2.5 rounded-lg text-left text-xs transition border flex flex-col justify-between h-20 ${
                  isSelected
                    ? 'bg-rr-navy text-white shadow-sm ring-1 ring-rr-gold'
                    : 'bg-white hover:border-rr-pink/40 hover:bg-slate-50 text-slate-800'
                }`}
              >
                <div
                  style={{ color: isSelected ? '#FFFFFF' : '#25212A' }}
                  className="font-bold line-clamp-2 leading-tight"
                >
                  {scen.name}
                </div>
                <div
                  style={{ color: isSelected ? '#D4AF37' : '#77717C' }}
                  className="text-[10px] uppercase font-bold tracking-wider"
                >
                  {scen.category}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Scenario Banner & Filters */}
      {results && (
        <div className="bg-white rounded-xl shadow-card border border-rr-navy/5 p-5">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-gray-100 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-rr-navy/10 text-rr-navy">
                  {results.scenario.category}
                </span>
                {results.scenario.is_relaxed && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    Relaxed Comparable Cohort
                  </span>
                )}
              </div>
              <h2 className="text-xl font-display font-bold text-rr-navy mt-1">
                {results.scenario.name}
              </h2>
              <p className="text-xs text-rr-muted mt-0.5 max-w-3xl">
                {results.scenario.description}{' '}
                <span className="font-semibold text-rr-charcoal">
                  Tactical Value: {results.scenario.tactical_intent}
                </span>
              </p>
              {results.scenario.is_relaxed && results.scenario.relaxation_explanation && (
                <div className="mt-2 text-xs bg-amber-50 text-amber-800 p-2 rounded border border-amber-200">
                  <span className="font-bold">Relaxation Disclosure:</span>{' '}
                  {results.scenario.relaxation_explanation}
                </div>
              )}
            </div>

            {/* Format & Evidence Controls */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Format Toggle */}
              <div className="flex items-center bg-rr-warm p-1 rounded-lg border border-gray-200 text-xs font-medium">
                <button
                  onClick={() => setFormatFilter('IPL')}
                  style={
                    formatFilter === 'IPL'
                      ? { backgroundColor: '#0B192C', color: '#FFFFFF' }
                      : {}
                  }
                  className={`px-3 py-1 rounded transition ${
                    formatFilter === 'IPL'
                      ? 'bg-[#0B192C] text-white font-bold shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  IPL Only
                </button>
                <button
                  onClick={() => setFormatFilter('T20I')}
                  style={
                    formatFilter === 'T20I'
                      ? { backgroundColor: '#0B192C', color: '#FFFFFF' }
                      : {}
                  }
                  className={`px-3 py-1 rounded transition ${
                    formatFilter === 'T20I'
                      ? 'bg-[#0B192C] text-white font-bold shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  T20I Only
                </button>
                <button
                  onClick={() => setFormatFilter('Combined')}
                  style={
                    formatFilter === 'Combined'
                      ? { backgroundColor: '#0B192C', color: '#FFFFFF' }
                      : {}
                  }
                  className={`px-3 py-1 rounded transition ${
                    formatFilter === 'Combined'
                      ? 'bg-[#0B192C] text-white font-bold shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Dual-Format
                </button>
              </div>

              {/* Evidence Tier Filter */}
              <div className="flex items-center gap-1.5 text-xs">
                <span className="text-rr-muted font-medium">Evidence:</span>
                <select
                  value={minEvidence}
                  onChange={(e) => setMinEvidence(e.target.value)}
                  className="bg-white border border-gray-200 rounded px-2.5 py-1 text-xs text-rr-navy font-semibold focus:outline-none focus:ring-1 focus:ring-rr-pink"
                >
                  <option value="ALL">All Players</option>
                  <option value="PROVISIONAL">Provisional+ (&ge;15b)</option>
                  <option value="CONFIDENT">Confident Only (&ge;30b)</option>
                </select>
              </div>

              {/* Relaxed Toggle */}
              {activeScenarioId !== 'custom' && (
                <label className="flex items-center gap-1.5 text-xs text-rr-charcoal cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useRelaxed}
                    onChange={(e) => setUseRelaxed(e.target.checked)}
                    className="rounded border-gray-300 text-rr-pink focus:ring-rr-pink"
                  />
                  <span>Relax Conditions</span>
                </label>
              )}
            </div>
          </div>

          {/* Scenario Cohort Benchmarks (4 KPI Cards) */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
            <div className="bg-rr-warm p-3 rounded-lg border border-gray-100">
              <span className="text-[11px] text-rr-muted font-medium uppercase tracking-wider block">
                Scenario Cohort Volume
              </span>
              <div className="text-lg font-bold text-rr-navy mt-0.5">
                {results.cohort_benchmarks.total_deliveries.toLocaleString()} Balls
              </div>
              <span className="text-[11px] text-rr-muted">
                Across {results.cohort_benchmarks.total_matches} matches ({results.cohort_benchmarks.total_players} players)
              </span>
            </div>

            <div className="bg-rr-warm p-3 rounded-lg border border-gray-100">
              <span className="text-[11px] text-rr-muted font-medium uppercase tracking-wider block">
                Cohort Benchmark Rate
              </span>
              <div className="text-lg font-bold text-rr-navy mt-0.5">
                {selectedDiscipline === 'BOWLER'
                  ? `${results.cohort_benchmarks.cohort_rate.toFixed(2)} RPO`
                  : `${results.cohort_benchmarks.cohort_rate.toFixed(1)} SR`}
              </div>
              <span className="text-[11px] text-rr-muted">
                {selectedDiscipline === 'BOWLER'
                  ? 'Average economy in this match state'
                  : 'Average strike rate in this match state'}
              </span>
            </div>

            <div className="bg-rr-warm p-3 rounded-lg border border-gray-100">
              <span className="text-[11px] text-rr-muted font-medium uppercase tracking-wider block">
                Dot % vs Boundary %
              </span>
              <div className="text-lg font-bold text-rr-navy mt-0.5">
                {results.cohort_benchmarks.cohort_dot_pct.toFixed(1)}% /{' '}
                {results.cohort_benchmarks.cohort_boundary_pct.toFixed(1)}%
              </div>
              <span className="text-[11px] text-rr-muted">
                Cohort boundary and containment rate
              </span>
            </div>

            <div className="bg-rr-warm p-3 rounded-lg border border-gray-100">
              <span className="text-[11px] text-rr-muted font-medium uppercase tracking-wider block">
                Innings Outcome Success
              </span>
              <div className="text-lg font-bold text-rr-navy mt-0.5">
                {results.cohort_benchmarks.cohort_success_rate !== null
                  ? `${results.cohort_benchmarks.cohort_success_rate.toFixed(1)}%`
                  : 'N/A'}
              </div>
              <span className="text-[11px] text-rr-muted">
                {selectedDiscipline === 'BOWLER'
                  ? 'Complete innings target defense win %'
                  : 'Complete innings target chase win %'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Main Table Controls & Search */}
      <div className="bg-white rounded-xl shadow-card border border-rr-navy/5 p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-display font-bold text-rr-navy">
              Ranked Candidate Performance ({results?.total_players || 0} Players)
            </h3>
            {selectedForCompare.length > 0 && (
              <span className="text-xs bg-rr-pink/10 text-rr-pink font-semibold px-2 py-0.5 rounded">
                {selectedForCompare.length} selected for head-to-head
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-rr-muted absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search player name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 text-xs border border-gray-200 rounded-lg text-rr-navy focus:outline-none focus:ring-1 focus:ring-rr-pink w-48 sm:w-60"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-2 text-rr-muted hover:text-rr-navy"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>

            {selectedForCompare.length >= 2 && (
              <button
                onClick={handleOpenComparison}
                className="px-3 py-1.5 bg-rr-pink text-white text-xs font-semibold rounded-lg hover:bg-rr-pink-light transition shadow-xs flex items-center gap-1.5"
              >
                <GitCompare className="w-3.5 h-3.5" />
                Compare Selected ({selectedForCompare.length})
              </button>
            )}
          </div>
        </div>

        {/* Table Content */}
        {loading ? (
          <div className="py-16 text-center text-rr-muted">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-rr-pink" />
            <p className="text-xs">Evaluating historical match-state deliveries...</p>
          </div>
        ) : executionError ? (
          <div className="py-12 text-center text-red-600 bg-red-50 rounded-lg p-4 text-xs">
            {executionError}
          </div>
        ) : !results?.players || results.players.length === 0 ? (
          <div className="py-12 text-center text-rr-muted bg-rr-warm rounded-lg text-xs">
            No player observations met the specified scenario filters. Try relaxing filters or selecting Dual-Format.
          </div>
        ) : (
          <div className="space-y-3">
            <div className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-[11px] text-slate-600 flex flex-wrap items-center justify-between gap-2">
              <span className="flex items-center gap-1.5">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                <span className="font-semibold text-slate-800">Methodological Standard:</span> Rates report un-shrunk observed sample means. Confidence intervals computed via match-cluster bootstrap resampling (clustering by match ID to account for intra-match correlation).
              </span>
              <span className="text-[10px] text-slate-500 font-medium">
                Innings Win % evaluated across distinct eligible matches
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-gray-200 text-rr-muted font-semibold uppercase tracking-wider text-[11px] bg-rr-warm/50">
                    <th className="py-2.5 px-3 w-10">Comp</th>
                    <th className="py-2.5 px-3">Player</th>
                    <th className="py-2.5 px-3 text-center">Operational Tier</th>
                    <th className="py-2.5 px-3 text-right">Volume</th>
                    <th className="py-2.5 px-3 text-right">Matches</th>
                    <th className="py-2.5 px-3 text-right">
                      {selectedDiscipline === 'BOWLER' ? 'Scenario Econ' : 'Scenario SR'}
                    </th>
                    <th className="py-2.5 px-3 text-right">vs Cohort</th>
                    <th className="py-2.5 px-3 text-right">Dot %</th>
                    <th className="py-2.5 px-3 text-right">Boundary %</th>
                    <th className="py-2.5 px-3 text-right">
                      {selectedDiscipline === 'BOWLER' ? 'Wkts / Over' : 'Dismissal %'}
                    </th>
                    <th className="py-2.5 px-3 text-right">Innings Win % (95% CI)</th>
                    <th className="py-2.5 px-3 text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {results.players.map((p: ScenarioPlayer, idx: number) => {
                    const isChecked = selectedForCompare.includes(p.player_id);
                    const isPositiveDiff =
                      selectedDiscipline === 'BOWLER'
                        ? p.context_diff < 0
                        : p.context_diff > 0;

                    return (
                      <tr
                        key={p.player_id}
                        className={`hover:bg-rr-warm/40 transition ${
                          isChecked ? 'bg-rr-pink/5' : ''
                        }`}
                      >
                        {/* Compare Checkbox */}
                        <td className="py-2 px-3 text-center">
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => togglePlayerComparison(p.player_id)}
                            className="rounded border-gray-300 text-rr-pink focus:ring-rr-pink cursor-pointer"
                          />
                        </td>

                        {/* Player Info */}
                        <td className="py-2 px-3">
                          <div className="font-bold text-rr-navy flex items-center gap-1.5">
                            <span>{p.player_name}</span>
                            {idx < 3 && p.evidence_tier === 'CONFIDENT' && (
                              <span title="Top 3 Confident Evidence Rank">
                                <Award className="w-3.5 h-3.5 text-rr-gold" />
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] text-rr-muted">
                            {p.format}
                          </span>
                        </td>

                        {/* Evidence Tier */}
                        <td className="py-2 px-3 text-center">
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                              p.evidence_tier === 'CONFIDENT'
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : p.evidence_tier === 'PROVISIONAL'
                                ? 'bg-amber-50 text-amber-700 border border-amber-200'
                                : 'bg-gray-100 text-gray-500 border border-gray-200'
                            }`}
                            title={
                              p.evidence_tier === 'CONFIDENT'
                                ? 'Operational Tier: N >= 30 balls across M >= 5 matches'
                                : p.evidence_tier === 'PROVISIONAL'
                                ? 'Operational Tier: N >= 15 balls across M >= 3 matches'
                                : 'Operational Tier: Insufficient balls or matches'
                            }
                          >
                            {p.evidence_tier}
                          </span>
                        </td>

                        {/* Volume */}
                        <td className="py-2 px-3 text-right">
                          <span className="font-semibold text-rr-charcoal">
                            {p.legal_balls}b
                          </span>
                          {p.deliveries > p.legal_balls && (
                            <span className="text-[10px] text-rr-muted block">
                              ({p.deliveries} total)
                            </span>
                          )}
                        </td>

                        {/* Matches */}
                        <td className="py-2 px-3 text-right font-semibold text-slate-700">
                          {p.matches}
                        </td>

                      {/* Primary Rate */}
                      <td className="py-2 px-3 text-right font-mono font-bold text-rr-navy">
                        {p.primary_rate.toFixed(
                          selectedDiscipline === 'BOWLER' ? 2 : 1
                        )}
                        <span className="text-[10px] text-rr-muted block font-sans">
                          [{p.confidence_interval[0]}–{p.confidence_interval[1]}]
                        </span>
                      </td>

                      {/* Context Difference */}
                      <td className="py-2 px-3 text-right font-mono">
                        <span
                          className={`inline-flex items-center gap-0.5 font-bold ${
                            isPositiveDiff
                              ? 'text-emerald-600'
                              : p.context_diff === 0
                              ? 'text-gray-400'
                              : 'text-red-500'
                          }`}
                        >
                          {p.context_diff > 0 ? `+${p.context_diff}` : p.context_diff}
                          {isPositiveDiff ? (
                            <TrendingUp className="w-3 h-3" />
                          ) : (
                            <TrendingDown className="w-3 h-3" />
                          )}
                        </span>
                      </td>

                      {/* Dot % */}
                      <td className="py-2 px-3 text-right font-mono text-rr-charcoal">
                        {p.dot_pct.toFixed(1)}%
                      </td>

                      {/* Boundary % */}
                      <td className="py-2 px-3 text-right font-mono text-rr-charcoal">
                        {p.boundary_pct.toFixed(1)}%
                      </td>

                      {/* Wicket rate */}
                      <td className="py-2 px-3 text-right font-mono text-rr-charcoal">
                        {selectedDiscipline === 'BOWLER'
                          ? p.wickets_per_over.toFixed(2)
                          : `${p.wicket_pct.toFixed(1)}%`}
                      </td>

                      {/* Innings Win % */}
                      <td className="py-2 px-3 text-right font-mono">
                        {p.success_rate !== null ? (
                          <>
                            <span className="font-bold text-rr-navy">
                              {p.success_rate.toFixed(1)}%
                            </span>
                            <span className="text-[10px] text-rr-muted block font-sans">
                              [{p.success_ci[0]}–{p.success_ci[1]}%]
                            </span>
                          </>
                        ) : (
                          <span className="text-gray-400">N/A</span>
                        )}
                      </td>

                      {/* Action */}
                      <td className="py-2 px-3 text-center">
                        <button
                          onClick={() => {
                            if (onNavigateToGallery) {
                              onNavigateToGallery(p.player_id);
                            }
                          }}
                          className="px-2 py-1 text-[11px] font-semibold text-rr-navy hover:text-rr-pink transition flex items-center gap-1 mx-auto"
                        >
                          Profile
                          <ExternalLink className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
        )}
      </div>

      {/* Top 10 Scenario Validation Commentary */}
      <div className="bg-white rounded-xl shadow-card border border-rr-navy/5 p-5">
        <div className="flex items-center gap-2 mb-2">
          <Award className="w-4 h-4 text-rr-gold" />
          <h3 className="text-sm font-display font-bold text-rr-navy">
            Franchise Top 10 Scenario Validation & Decision Science
          </h3>
        </div>
        <p className="text-xs text-rr-muted leading-relaxed">
          Scenario Lab serves as an independent stress-testing layer for our franchise recommendations. 
          When analyzing <span className="font-semibold text-rr-navy">Defend 18 in Final 6 Balls</span>, our #2 bowler <span className="font-semibold text-rr-navy">Jasprit Bumrah</span> consistently limits boundaries and sustains defensive suppression, validating his auction rating. Similarly, in <span className="font-semibold text-rr-navy">Chase 12 in Final 6</span>, #1 batter <span className="font-semibold text-rr-navy">Tim David</span> demonstrates positive contextual attacking separation above the tournament baseline.
          Scenario results never automatically overwrite our locked Bayesian rankings without formal sensitivity audit.
        </p>
      </div>

      {/* Historical Episodes Drawer / Modal */}
      {episodesOpen && results?.sample_episodes && (
        <div className="fixed inset-0 bg-rr-navy/40 backdrop-blur-xs flex items-center justify-center z-[100] p-4">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[85vh] shadow-2xl flex flex-col overflow-hidden border border-rr-navy/10">
            <div
              style={{ backgroundColor: '#0B192C' }}
              className="p-4 border-b border-gray-100 flex items-center justify-between bg-[#0B192C] text-white"
            >
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-rr-gold" />
                <h4 className="text-sm font-bold font-display">
                  Historical Scenario Episodes &mdash; {results.scenario.name}
                </h4>
              </div>
              <button
                onClick={() => setEpisodesOpen(false)}
                className="text-gray-300 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 overflow-y-auto flex-1 space-y-3">
              <p className="text-xs text-rr-muted">
                Displaying audited historical deliveries from our primary cohort that satisfied the exact match-state conditions of this scenario.
              </p>
              <div className="divide-y divide-gray-100 border rounded-lg overflow-hidden">
                {results.sample_episodes.map((ep: ScenarioEpisode, idx: number) => (
                  <div key={idx} className="p-3 text-xs bg-white hover:bg-rr-warm/40 transition">
                    <div className="flex flex-wrap items-center justify-between gap-1 mb-1">
                      <span className="font-bold text-rr-navy">
                        {ep.comp_name} &bull; Over {ep.over_ball}
                      </span>
                      <span className="text-rr-muted text-[11px]">{ep.match_date}</span>
                    </div>
                    <div className="flex items-center justify-between text-rr-charcoal mt-1">
                      <div>
                        <span className="font-semibold">{ep.bowler}</span> to{' '}
                        <span className="font-semibold">{ep.striker}</span>: {ep.total_runs} runs{' '}
                        {ep.is_wicket && (
                          <span className="text-red-600 font-bold">
                            (WICKET: {ep.dismissal_type || 'Dismissed'})
                          </span>
                        )}
                      </div>
                      <div className="text-right">
                        <span className="text-rr-muted">Remaining: </span>
                        <span className="font-semibold">{ep.balls_remaining}b</span>
                        {ep.runs_to_defend !== null && (
                          <span className="font-semibold ml-2 text-rr-pink">
                            ({ep.runs_to_defend} needed)
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-[11px] text-rr-muted mt-1">
                      Match Result: <span className="font-medium text-rr-navy">{ep.match_result}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-3 bg-rr-warm border-t border-gray-100 flex justify-end">
              <button
                onClick={() => setEpisodesOpen(false)}
                className="px-4 py-1.5 bg-rr-navy text-white text-xs font-semibold rounded-lg hover:bg-rr-navy-light"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Multi-Player Comparison Modal */}
      {comparisonModalOpen && (
        <div className="fixed inset-0 bg-rr-navy/40 backdrop-blur-xs flex items-center justify-center z-[100] p-4">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[85vh] shadow-2xl flex flex-col overflow-hidden border border-rr-navy/10">
            <div
              style={{ backgroundColor: '#0B192C' }}
              className="p-4 border-b border-gray-100 flex items-center justify-between bg-[#0B192C] text-white"
            >
              <div className="flex items-center gap-2">
                <GitCompare className="w-4 h-4 text-rr-gold" />
                <h4 className="text-sm font-bold font-display">
                  Head-to-Head Scenario Comparison &mdash; {results?.scenario.name}
                </h4>
              </div>
              <button
                onClick={() => setComparisonModalOpen(false)}
                className="text-gray-300 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 overflow-y-auto flex-1 space-y-4">
              {comparingLoading ? (
                <div className="py-12 text-center text-rr-muted">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-rr-pink" />
                  <p className="text-xs">Computing paired statistical intervals...</p>
                </div>
              ) : comparisonData ? (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                    {comparisonData.compared_players.map((cp: ScenarioPlayer) => (
                      <div
                        key={cp.player_id}
                        className="bg-rr-warm/60 p-4 rounded-xl border border-rr-navy/10 space-y-2"
                      >
                        <div className="font-bold text-rr-navy text-sm">
                          {cp.player_name}
                        </div>
                        <div className="text-[11px] text-rr-muted">
                          {cp.legal_balls} balls &bull; {cp.matches} matches
                        </div>
                        <div className="text-xl font-mono font-bold text-rr-navy">
                          {cp.primary_rate > 0 ? cp.primary_rate.toFixed(selectedDiscipline === 'BOWLER' ? 2 : 1) : 'No data'}
                        </div>
                        <div className="text-xs text-rr-charcoal space-y-1 pt-1 border-t border-gray-200">
                          <div className="flex justify-between">
                            <span>Dot %:</span>
                            <span className="font-mono font-semibold">{cp.dot_pct}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Boundary %:</span>
                            <span className="font-mono font-semibold">{cp.boundary_pct}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Outcome Win %:</span>
                            <span className="font-mono font-semibold">
                              {cp.success_rate !== null ? `${cp.success_rate}%` : 'N/A'}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Evidence:</span>
                            <span className="font-bold">{cp.evidence_tier}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Paired Match-Cluster Bootstrap Result */}
                  {comparisonData.pairwise_comparison && (
                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-rr-navy flex items-center gap-1.5">
                          <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                          Paired Match-Cluster Bootstrap Analysis (1,000 Resamples)
                        </span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            comparisonData.pairwise_comparison.spans_zero
                              ? 'bg-amber-100 text-amber-800 border border-amber-300'
                              : 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                          }`}
                        >
                          {comparisonData.pairwise_comparison.spans_zero
                            ? 'Indistinguishable (CI Spans Zero)'
                            : 'Statistically Separated'}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-center text-xs">
                        <div className="bg-white p-2 rounded border border-slate-200">
                          <span className="text-slate-500 block text-[10px]">Difference 95% CI</span>
                          <span className="font-mono font-bold text-slate-800">
                            [{comparisonData.pairwise_comparison.bootstrap_ci_95[0]}, {comparisonData.pairwise_comparison.bootstrap_ci_95[1]}]
                          </span>
                        </div>
                        <div className="bg-white p-2 rounded border border-slate-200">
                          <span className="text-slate-500 block text-[10px]">Bootstrap SE</span>
                          <span className="font-mono font-bold text-slate-800">
                            {comparisonData.pairwise_comparison.bootstrap_se !== null
                              ? comparisonData.pairwise_comparison.bootstrap_se
                              : 'N/A'}
                          </span>
                        </div>
                        <div className="bg-white p-2 rounded border border-slate-200">
                          <span className="text-slate-500 block text-[10px]">Match Cluster Sample</span>
                          <span className="font-bold text-slate-800">
                            {comparisonData.pairwise_comparison.sample_adequacy}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="p-3 bg-amber-50 rounded-lg text-xs text-amber-800 border border-amber-200">
                    <span className="font-bold">Methodological Reminder:</span> In micro-window scenarios with low delivery counts, pairwise differences frequently cross zero in paired bootstrap intervals. Treat differences below 30 deliveries across 5 matches as provisional evidence.
                  </div>
                </>
              ) : null}
            </div>

            <div className="p-3 bg-rr-warm border-t border-gray-100 flex justify-end">
              <button
                onClick={() => setComparisonModalOpen(false)}
                className="px-4 py-1.5 bg-rr-navy text-white text-xs font-semibold rounded-lg hover:bg-rr-navy-light"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Custom Scenario Builder Modal */}
      {customModalOpen && (
        <div className="fixed inset-0 bg-rr-navy/40 backdrop-blur-xs flex items-center justify-center z-[100] p-4">
          <div className="bg-white rounded-xl max-w-xl w-full shadow-2xl flex flex-col overflow-hidden border border-rr-navy/10">
            <div
              style={{ backgroundColor: '#0B192C' }}
              className="p-4 border-b border-gray-100 flex items-center justify-between bg-[#0B192C] text-white"
            >
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-rr-gold" />
                <h4 className="text-sm font-bold font-display">
                  Custom Scenario Builder
                </h4>
              </div>
              <button
                onClick={() => setCustomModalOpen(false)}
                className="text-gray-300 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-rr-navy block mb-1">
                    Discipline
                  </label>
                  <select
                    value={customConfig.discipline}
                    onChange={(e) =>
                      setCustomConfig({ ...customConfig, discipline: e.target.value })
                    }
                    className="w-full bg-rr-warm border border-gray-200 rounded p-1.5 font-medium"
                  >
                    <option value="BOWLER">Bowler Defense</option>
                    <option value="BATTER">Batter Chase</option>
                  </select>
                </div>
                <div>
                  <label className="font-semibold text-rr-navy block mb-1">
                    Match Phase
                  </label>
                  <select
                    value={customConfig.innings_phase || 'All'}
                    onChange={(e) =>
                      setCustomConfig({
                        ...customConfig,
                        innings_phase: e.target.value === 'All' ? null : e.target.value,
                      })
                    }
                    className="w-full bg-rr-warm border border-gray-200 rounded p-1.5 font-medium"
                  >
                    <option value="All">All Phases</option>
                    <option value="Death">Death (Overs 16-20)</option>
                    <option value="Middle">Middle (Overs 7-15)</option>
                    <option value="Powerplay">Powerplay (Overs 1-6)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-rr-navy block mb-1">
                    Balls Remaining (&le; {customConfig.balls_remaining_max || 6})
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="36"
                    value={customConfig.balls_remaining_max || 6}
                    onChange={(e) =>
                      setCustomConfig({
                        ...customConfig,
                        balls_remaining_max: parseInt(e.target.value),
                      })
                    }
                    className="w-full accent-rr-pink"
                  />
                </div>
                <div>
                  <label className="font-semibold text-rr-navy block mb-1">
                    Runs to Defend/Chase (&le; {customConfig.runs_to_defend_max || 18})
                  </label>
                  <input
                    type="range"
                    min="2"
                    max="60"
                    value={customConfig.runs_to_defend_max || 18}
                    onChange={(e) =>
                      setCustomConfig({
                        ...customConfig,
                        runs_to_defend_max: parseInt(e.target.value),
                        runs_to_chase_max: parseInt(e.target.value),
                      })
                    }
                    className="w-full accent-rr-pink"
                  />
                </div>
              </div>

              <div>
                <label className="font-semibold text-rr-navy block mb-1">
                  Previous Context Shock
                </label>
                <select
                  value={customConfig.previous_context || 'none'}
                  onChange={(e) =>
                    setCustomConfig({
                      ...customConfig,
                      previous_context: e.target.value,
                    })
                  }
                  className="w-full bg-rr-warm border border-gray-200 rounded p-1.5 font-medium"
                >
                  <option value="none">Standard Pre-Delivery State</option>
                  <option value="boundary_conceded_same_over">
                    Bowler Conceded Boundary on Prior Ball
                  </option>
                  <option value="cluster_8_runs_in_3_balls">
                    Bowler Conceded 8+ Runs in Prior 3 Balls
                  </option>
                  <option value="team_wicket_in_last_6_balls">
                    Batting Team Lost Wicket in Prior 6 Balls
                  </option>
                  <option value="personal_dot_streak_ge_2">
                    Batter on Personal Streak of 2+ Dots
                  </option>
                </select>
              </div>
            </div>

            <div className="p-3 bg-rr-warm border-t border-gray-100 flex justify-end gap-2">
              <button
                onClick={() => setCustomModalOpen(false)}
                className="px-3 py-1.5 text-xs text-rr-muted hover:text-rr-navy"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setActiveScenarioId('custom');
                  setCustomModalOpen(false);
                }}
                className="px-4 py-1.5 bg-rr-navy text-white text-xs font-semibold rounded-lg hover:bg-rr-navy-light"
              >
                Run Custom Simulation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

