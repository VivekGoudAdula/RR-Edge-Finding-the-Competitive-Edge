import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import {
  Search,
  Filter,
  ArrowUpDown,
  X,
  Swords,
  TrendingUp,
  Activity,
  AlertCircle,
  Shield,
  Layers,
  ChevronRight,
  Brain,
  Target,
  Scale,
  Zap,
  AlertTriangle,
  CheckCircle2,
  Clock,
  GitCompare,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { fetchBatters, fetchBatterDetail } from '../services/api';
import canonicalBatters from '../data/canonicalBatters.json';
import { PlayerOverview, PlayerDetail } from '../types';
import { SectionHeading } from '../components/common/SectionHeading';
import { ArchetypeBadge, TierBadge, Badge } from '../components/common/Badge';
import { PageHeroCard } from '../components/common/PageHeroCard';
import { PlayerAvatar } from '../components/common/PlayerAvatar';

interface BatterIntelligenceProps {
  initialPlayerId?: number;
}

export const BatterIntelligence: React.FC<BatterIntelligenceProps> = ({ initialPlayerId }) => {
  const [batters, setBatters] = useState<PlayerOverview[]>(canonicalBatters as unknown as PlayerOverview[]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('ALL');
  const [tierFilter, setTierFilter] = useState('ALL');
  const [formatView, setFormatView] = useState<'IPL' | 'T20I'>('IPL');
  const [selectedPlayer, setSelectedPlayer] = useState<PlayerDetail | null>(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [dossierTab, setDossierTab] = useState<'overview' | 'pressure' | 'ml' | 'behavioral' | 'reliability'>('overview');

  useEffect(() => {
    setLoading(true);
    fetchBatters({ search, role: roleFilter, tier: tierFilter })
      .then((res) => {
        setBatters(res);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [search, roleFilter, tierFilter]);

  useEffect(() => {
    if (initialPlayerId) {
      handleOpenPlayer(initialPlayerId);
    }
  }, [initialPlayerId]);

  useEffect(() => {
    if (selectedPlayer) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [selectedPlayer]);

  const handleOpenPlayer = (id: number) => {
    setModalLoading(true);
    fetchBatterDetail(id)
      .then((detail) => {
        setSelectedPlayer(detail);
        setDossierTab('overview');
        setModalLoading(false);
      })
      .catch(() => setModalLoading(false));
  };

  return (
    <div className="space-y-6 w-full max-w-[1550px] mx-auto">
      {/* Standardized Compact Hero Section */}
      <PageHeroCard
        badge="Evaluation Engine"
        badgeIcon={<Swords className="w-3.5 h-3.5 text-rr-pink" />}
        title="Batter Intelligence Workspace"
        description="Bayesian shrunk strike rates (M=45), Context RAE, boundary production, and dot-ball avoidance across audited pressure cohorts."
      />

      {/* Filter Controls Bar */}
      <div className="bg-white rounded-xl border border-rr-border p-3.5 shadow-card">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-3 w-4 h-4 text-rr-muted" />
            <input
              type="text"
              placeholder="Search candidate name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-rr-warmWhite border border-rr-border text-xs text-rr-charcoal focus:outline-none focus:border-rr-pink transition-colors"
            />
          </div>

          {/* Role Filter */}
          <div className="relative">
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-rr-warmWhite border border-rr-border text-xs text-rr-charcoal focus:outline-none focus:border-rr-pink transition-colors appearance-none cursor-pointer"
            >
              <option value="ALL">All Batting Roles</option>
              <option value="Top-Order">Top-Order</option>
              <option value="Middle-Order">Middle-Order</option>
              <option value="Lower-Order">Lower-Order</option>
            </select>
          </div>

          {/* Evidence Tier */}
          <div className="relative">
            <select
              value={tierFilter}
              onChange={(e) => setTierFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-rr-warmWhite border border-rr-border text-xs text-rr-charcoal focus:outline-none focus:border-rr-pink transition-colors appearance-none cursor-pointer"
            >
              <option value="ALL">All Evidence Tiers</option>
              <option value="CONFIDENT_EVIDENCE">Confident Evidence (&ge; 60b, 8m)</option>
              <option value="MODERATE_EVIDENCE">Moderate Evidence (&ge; 24b, 4m)</option>
              <option value="PROVISIONAL_EVIDENCE">Provisional Evidence (12-23b)</option>
            </select>
          </div>

          {/* Format View Toggle */}
          <div className="flex rounded-xl bg-rr-warmWhite border border-rr-border p-1">
            <button
              onClick={() => setFormatView('IPL')}
              className={`flex-1 py-1 rounded-lg text-xs font-bold transition-all ${
                formatView === 'IPL'
                  ? 'bg-rr-pink text-white shadow-sm'
                  : 'text-rr-muted hover:text-rr-charcoal'
              }`}
            >
              IPL Metrics
            </button>
            <button
              onClick={() => setFormatView('T20I')}
              className={`flex-1 py-1 rounded-lg text-xs font-bold transition-all ${
                formatView === 'T20I'
                  ? 'bg-rr-pink text-white shadow-sm'
                  : 'text-rr-muted hover:text-rr-charcoal'
              }`}
            >
              T20I Metrics
            </button>
          </div>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white rounded-2xl border border-rr-border shadow-rr-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-rr-warmWhite text-rr-muted font-bold uppercase tracking-wider border-b border-rr-border text-[10.5px] leading-tight">
                <th className="py-2.5 px-2 text-center w-12">Rank</th>
                <th className="py-2.5 px-3 min-w-[170px]">Player Name</th>
                <th className="py-2.5 px-2 text-left">Role</th>
                <th className="py-2 px-2 text-right" title="Deliveries faced under high-pressure context">
                  <div>{formatView}</div>
                  <div>PRESSURE</div>
                  <div>VOL</div>
                </th>
                <th className="py-2 px-2 text-right" title="Raw high-pressure strike rate">
                  <div>{formatView}</div>
                  <div>RAW</div>
                  <div>SR</div>
                </th>
                <th className="py-2 px-2 text-right" title="Empirical Bayes shrunk strike rate (M=45 prior)">
                  <div>{formatView}</div>
                  <div>SHRUNK</div>
                  <div>M45</div>
                </th>
                <th className="py-2 px-2 text-right" title="Context RAE (ΔSR vs contextual expectation)">
                  <div>RAE</div>
                  <div>(ΔSR)</div>
                </th>
                <th className="py-2 px-2 text-right" title="Dot ball percentage under pressure">
                  <div>DOT</div>
                  <div>%</div>
                </th>
                <th className="py-2 px-2 text-right" title="Boundary ball percentage under pressure">
                  <div>BND</div>
                  <div>%</div>
                </th>
                <th className="py-2 px-2 text-right" title="Match pass rate (% matches meeting benchmark)">
                  <div>PASS</div>
                  <div>RATE</div>
                </th>
                <th
                  className="py-2 px-2 text-center"
                  title="Statistical Evidence Tier: Primary candidate qualification portfolio. Evaluates volume (≥60b), distinct matches (≥8), and competitions (≥2)."
                >
                  <div>EVIDENCE</div>
                  <div>TIER</div>
                </th>
                <th className="py-2 px-2 text-left" title="Behavioral stability archetype">
                  <div>STABILITY</div>
                  <div>ARCHETYPE</div>
                </th>
                <th className="py-2.5 px-2 text-center w-10">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rr-border">
              {loading ? (
                <tr>
                  <td colSpan={13} className="py-8 text-center text-rr-muted animate-pulse">
                    Loading audited batter evaluation data...
                  </td>
                </tr>
              ) : batters.length === 0 ? (
                <tr>
                  <td colSpan={13} className="py-8 text-center text-rr-muted">
                    No batter candidates match the selected filters.
                  </td>
                </tr>
              ) : (
                batters.map((b) => {
                  const vol = formatView === 'IPL' ? b.ipl_pressure_volume : b.t20i_pressure_volume;
                  const rawSr = formatView === 'IPL' ? b.ipl_raw_sr : b.t20i_raw_sr;
                  const shrunkSr = formatView === 'IPL' ? b.ipl_shrunk_m45 : b.t20i_shrunk_m45;
                  const rae = formatView === 'IPL' ? b.ipl_context_delta_sr : b.t20i_context_delta_sr;
                  const dot = formatView === 'IPL' ? b.ipl_dot_ball_pct : b.t20i_dot_ball_pct;
                  const bnd = formatView === 'IPL' ? b.ipl_boundary_ball_pct : b.t20i_boundary_ball_pct;
                  const pass = formatView === 'IPL' ? b.ipl_match_pass_rate : b.t20i_match_pass_rate;
                  const tierTooltip = `Primary IPL evidence: ${vol}b across ${b.ipl_matches}m (${b.evidence_tier.replace('_EVIDENCE', '')}). Combined multi-format exposure: ${b.combined_pressure_volume}b across ${b.combined_matches}m.`;

                  return (
                    <tr
                      key={b.player_id}
                      onClick={() => handleOpenPlayer(b.player_id)}
                      className="hover:bg-rr-softPink/40 transition-colors cursor-pointer group whitespace-nowrap"
                    >
                      <td className="py-2.5 px-2 text-center font-extrabold text-rr-pink">
                        {b.top_10_rank ? `#${b.top_10_rank}` : '-'}
                      </td>
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-2.5">
                          <PlayerAvatar
                            playerId={b.player_id}
                            playerName={b.player_name}
                            size="sm"
                            isTop10={!!b.top_10_rank}
                          />
                          <div>
                            <div className="font-bold text-rr-charcoal group-hover:text-rr-deepPink leading-tight">
                              {b.player_name}
                            </div>
                            <div className="text-[10px] text-rr-muted">ID: {b.player_id}</div>
                          </div>
                        </div>
                      </td>
                      <td className="py-2.5 px-2 text-rr-muted">{b.primary_role}</td>
                      <td className="py-2.5 px-2 text-right font-medium">
                        {vol ? `${vol}b` : '0b'}
                      </td>
                      <td className="py-2.5 px-2 text-right font-semibold">
                        {rawSr ? rawSr.toFixed(1) : '-'}
                      </td>
                      <td className="py-2.5 px-2 text-right font-extrabold text-rr-charcoal font-heading text-sm">
                        {shrunkSr ? shrunkSr.toFixed(1) : '-'}
                      </td>
                      <td className="py-2.5 px-2 text-right font-semibold text-emerald-600">
                        {typeof rae === 'number' ? `+${rae.toFixed(1)}` : '-'}
                      </td>
                      <td className="py-2.5 px-2 text-right text-rr-muted">
                        {typeof dot === 'number' ? `${dot.toFixed(1)}%` : '-'}
                      </td>
                      <td className="py-2.5 px-2 text-right font-medium text-rr-charcoal">
                        {typeof bnd === 'number' ? `${bnd.toFixed(1)}%` : '-'}
                      </td>
                      <td className="py-2.5 px-2 text-right text-rr-muted">
                        {typeof pass === 'number' ? `${pass.toFixed(1)}%` : '-'}
                      </td>
                      <td className="py-2.5 px-2 text-center">
                        <TierBadge tier={b.evidence_tier} title={tierTooltip} />
                      </td>
                      <td className="py-2.5 px-2">
                        <ArchetypeBadge archetype={b.stability_archetype} />
                      </td>
                      <td className="py-2.5 px-2 text-center">
                        <span className="p-1 rounded-md text-rr-pink group-hover:bg-rr-softPink transition-colors inline-block">
                          <ChevronRight className="w-4 h-4" />
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Slide-out Unified Player Profile Scout Dossier Modal */}
      {selectedPlayer &&
        createPortal(
          <div
            className="fixed inset-0 z-[100] bg-rr-charcoal/60 backdrop-blur-sm flex justify-end animate-in fade-in duration-150"
            onClick={(e) => {
              if (e.target === e.currentTarget) setSelectedPlayer(null);
            }}
          >
            <div className="relative w-full max-w-3xl bg-white h-full max-h-screen border-l border-rr-border shadow-2xl flex flex-col overflow-hidden">
              {/* Sticky Header with Persistent Close Button & Avatar */}
              <div className="shrink-0 p-6 pb-4 border-b border-rr-border bg-white flex items-start justify-between z-10">
                <div className="flex items-center gap-4">
                  <PlayerAvatar
                    playerId={selectedPlayer.player.player_id}
                    playerName={selectedPlayer.player.player_name}
                    size="xl"
                    isTop10={!!selectedPlayer.player.top_10_rank}
                    className="ring-2 ring-rr-pink"
                  />
                  <div>
                    <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                      {selectedPlayer.player.top_10_rank ? (
                        <span className="px-2.5 py-0.5 rounded-full bg-rr-pink text-white font-extrabold text-xs shadow-sm">
                          RANK #{selectedPlayer.player.top_10_rank}
                        </span>
                      ) : null}
                      <TierBadge tier={selectedPlayer.player.evidence_tier} />
                      <ArchetypeBadge archetype={selectedPlayer.player.stability_archetype} />
                    </div>
                    <h3 className="text-2xl font-extrabold text-rr-charcoal font-heading">
                      {selectedPlayer.player.player_name}
                    </h3>
                    <p className="text-xs text-rr-muted mt-0.5">
                      Striker ID: {selectedPlayer.player.player_id} • Primary Role: {selectedPlayer.player.primary_role} • {selectedPlayer.player.phase_suitability || 'All Phases'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedPlayer(null)}
                  className="p-2 rounded-xl text-rr-muted hover:bg-rr-palePink hover:text-rr-deepPink transition-colors cursor-pointer"
                  title="Close Dossier"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Scrollable Body Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-5">
                {/* Audited Population & Sample Architecture Banner */}
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] font-bold text-slate-700">
                <span className="flex items-center gap-1.5 uppercase tracking-wider text-slate-900">
                  <Layers className="w-3.5 h-3.5 text-rr-pink" />
                  Audited Sample Separation Architecture
                </span>
                <span className="text-slate-500 font-medium">Population Scope Disclosure</span>
              </div>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 text-[10px]">
                <div className="p-2 rounded-lg bg-white border border-slate-200">
                  <span className="font-extrabold text-indigo-700 block">1. 2026 ML Holdout</span>
                  <span className="text-slate-700 font-bold block">31,165 balls (144 matches)</span>
                  <span className="text-slate-400 text-[9px] block">All match deliveries (Normal + Pressure)</span>
                </div>
                <div className="p-2 rounded-lg bg-white border border-slate-200">
                  <span className="font-extrabold text-rr-deepPink block">2. Primary Pressure Cohort</span>
                  <span className="text-slate-700 font-bold block">71,523 balls (837 matches)</span>
                  <span className="text-slate-400 text-[9px] block">Context RAE under L1 &ge; 0.50</span>
                </div>
                <div className="p-2 rounded-lg bg-white border border-slate-200">
                  <span className="font-extrabold text-amber-700 block">3. Behavioral Event Sample</span>
                  <span className="text-slate-700 font-bold block">14,876 triggers (834 matches)</span>
                  <span className="text-slate-400 text-[9px] block">19,818 drought / 12,653 strict t+1</span>
                </div>
                <div className="p-2 rounded-lg bg-white border border-slate-200">
                  <span className="font-extrabold text-emerald-700 block">4. Reliability Evaluation</span>
                  <span className="text-slate-700 font-bold block">{selectedPlayer.pressure_performance?.ipl_pressure_volume || selectedPlayer.player.ipl_pressure_volume || 0} IPL balls ({selectedPlayer.pressure_performance?.ipl_pressure_matches || selectedPlayer.player.ipl_matches || 0}m)</span>
                  <span className="text-slate-400 text-[9px] block">Bayesian Shrinkage (M &isin; [25, 45, 60, 90])</span>
                </div>
              </div>
            </div>

            {/* Dossier Navigation Tabs */}
            <div className="flex border-b border-rr-border gap-1 overflow-x-auto pb-1 text-xs font-bold">
              <button
                onClick={() => setDossierTab('overview')}
                className={`px-3 py-2 rounded-lg transition-all flex items-center gap-1.5 ${
                  dossierTab === 'overview'
                    ? 'bg-rr-softPink text-rr-deepPink border-b-2 border-rr-pink'
                    : 'text-rr-muted hover:text-rr-charcoal'
                }`}
              >
                <Swords className="w-3.5 h-3.5" />
                Overview
              </button>
              <button
                onClick={() => setDossierTab('pressure')}
                className={`px-3 py-2 rounded-lg transition-all flex items-center gap-1.5 ${
                  dossierTab === 'pressure'
                    ? 'bg-rr-softPink text-rr-deepPink border-b-2 border-rr-pink'
                    : 'text-rr-muted hover:text-rr-charcoal'
                }`}
              >
                <Target className="w-3.5 h-3.5" />
                Pressure Engine
              </button>
              <button
                onClick={() => setDossierTab('ml')}
                className={`px-3 py-2 rounded-lg transition-all flex items-center gap-1.5 ${
                  dossierTab === 'ml'
                    ? 'bg-rr-softPink text-rr-deepPink border-b-2 border-rr-pink'
                    : 'text-rr-muted hover:text-rr-charcoal'
                }`}
              >
                <Brain className="w-3.5 h-3.5" />
                ML Context
              </button>
              <button
                onClick={() => setDossierTab('behavioral')}
                className={`px-3 py-2 rounded-lg transition-all flex items-center gap-1.5 ${
                  dossierTab === 'behavioral'
                    ? 'bg-rr-softPink text-rr-deepPink border-b-2 border-rr-pink'
                    : 'text-rr-muted hover:text-rr-charcoal'
                }`}
              >
                <Zap className="w-3.5 h-3.5" />
                Behavioral Response
              </button>
              <button
                onClick={() => setDossierTab('reliability')}
                className={`px-3 py-2 rounded-lg transition-all flex items-center gap-1.5 ${
                  dossierTab === 'reliability'
                    ? 'bg-rr-softPink text-rr-deepPink border-b-2 border-rr-pink'
                    : 'text-rr-muted hover:text-rr-charcoal'
                }`}
              >
                <Scale className="w-3.5 h-3.5" />
                Reliability & Risk
              </button>
            </div>

            {/* TAB 1: OVERVIEW */}
            {dossierTab === 'overview' && (
              <div className="space-y-4">
                {/* Strategic Selection Rationale */}
                {selectedPlayer.player.selection_rationale && (
                  <div className="p-4 rounded-xl bg-rr-palePink border border-pink-200">
                    <div className="text-xs font-bold text-rr-deepPink font-heading uppercase tracking-wider mb-1 flex items-center gap-1.5">
                      <Swords className="w-3.5 h-3.5" />
                      Franchise Selection Rationale & Role Fit
                    </div>
                    <p className="text-xs text-rr-charcoal leading-relaxed">
                      {selectedPlayer.player.selection_rationale}
                    </p>
                  </div>
                )}

                {/* Format-Specific Exposure */}
                <div>
                  <h4 className="text-xs font-bold text-rr-muted uppercase tracking-wider mb-2.5">
                    Format Exposure & Pressure Separation
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="p-3.5 rounded-xl bg-rr-warmWhite border border-rr-border space-y-2">
                      <div className="flex items-center justify-between text-xs pb-1 border-b border-rr-border">
                        <span className="font-bold text-rr-charcoal">IPL Pressure</span>
                        <span className="text-rr-deepPink font-bold">
                          {selectedPlayer.player.ipl_pressure_volume || 0} balls ({selectedPlayer.player.ipl_matches || 0}m)
                        </span>
                      </div>
                      <div className="text-[11px] space-y-1">
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Raw Strike Rate:</span>
                          <span className="font-bold text-rr-charcoal">{selectedPlayer.player.ipl_raw_sr || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Shrunk SR (M=45):</span>
                          <span className="font-extrabold text-rr-pink">{selectedPlayer.player.ipl_shrunk_m45 || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Context RAE (ΔSR):</span>
                          <span className="font-semibold text-emerald-600">+{selectedPlayer.player.ipl_context_delta_sr || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Dot / Boundary %:</span>
                          <span className="font-semibold text-rr-charcoal">{selectedPlayer.player.ipl_dot_ball_pct}% / {selectedPlayer.player.ipl_boundary_ball_pct}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Match Pass Rate:</span>
                          <span className="font-semibold text-rr-charcoal">{selectedPlayer.player.ipl_match_pass_rate ? `${selectedPlayer.player.ipl_match_pass_rate}%` : '-'}</span>
                        </div>
                      </div>
                    </div>

                    <div className="p-3.5 rounded-xl bg-rr-warmWhite border border-rr-border space-y-2">
                      <div className="flex items-center justify-between text-xs pb-1 border-b border-rr-border">
                        <span className="font-bold text-rr-charcoal">Senior T20I Pressure</span>
                        <span className="text-rr-deepPink font-bold">
                          {selectedPlayer.player.t20i_pressure_volume || 0} balls ({selectedPlayer.player.t20i_matches || 0}m)
                        </span>
                      </div>
                      <div className="text-[11px] space-y-1">
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Raw Strike Rate:</span>
                          <span className="font-bold text-rr-charcoal">{selectedPlayer.player.t20i_raw_sr || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Shrunk SR (M=45):</span>
                          <span className="font-extrabold text-rr-pink">{selectedPlayer.player.t20i_shrunk_m45 || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Context RAE (ΔSR):</span>
                          <span className="font-semibold text-emerald-600">{selectedPlayer.player.t20i_context_delta_sr ? `+${selectedPlayer.player.t20i_context_delta_sr}` : '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Dot / Boundary %:</span>
                          <span className="font-semibold text-rr-charcoal">{selectedPlayer.player.t20i_dot_ball_pct || '-'}% / {selectedPlayer.player.t20i_boundary_ball_pct || '-'}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Match Pass Rate:</span>
                          <span className="font-semibold text-rr-charcoal">{selectedPlayer.player.t20i_match_pass_rate ? `${selectedPlayer.player.t20i_match_pass_rate}%` : '-'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Scouting Strengths & Limitations */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                  {selectedPlayer.player.main_strengths && (
                    <div className="p-3.5 rounded-xl bg-emerald-50/80 border border-emerald-200 text-xs">
                      <div className="font-bold text-emerald-900 mb-1 flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        Scouting Strengths
                      </div>
                      <p className="text-emerald-950 leading-relaxed text-[11px]">{selectedPlayer.player.main_strengths}</p>
                    </div>
                  )}
                  {selectedPlayer.player.main_weaknesses && (
                    <div className="p-3.5 rounded-xl bg-amber-50/80 border border-amber-200 text-xs">
                      <div className="font-bold text-amber-900 mb-1 flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                        Exposure Limitations & Vulnerabilities
                      </div>
                      <p className="text-amber-950 leading-relaxed text-[11px]">{selectedPlayer.player.main_weaknesses}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 2: PRESSURE PERFORMANCE */}
            {dossierTab === 'pressure' && (
              <div className="space-y-4">
                {/* Pressure vs Normal Comparison Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  <div className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border text-center">
                    <span className="text-[10px] text-rr-muted uppercase font-bold block">IPL Pressure Strike Rate</span>
                    <span className="text-base font-extrabold text-rr-charcoal font-heading">
                      {selectedPlayer.pressure_performance?.ipl_pressure_strike_rate || selectedPlayer.pressure_performance?.pressure_strike_rate || selectedPlayer.player.ipl_raw_sr || '-'}
                    </span>
                    <span className="text-[10px] text-emerald-600 block mt-0.5">
                      Δ {selectedPlayer.pressure_performance?.delta_strike_rate ? `+${selectedPlayer.pressure_performance.delta_strike_rate}` : '+0.0'} vs Normal
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border text-center">
                    <span className="text-[10px] text-rr-muted uppercase font-bold block">Accepted IPL Context RAE</span>
                    <span className="text-base font-extrabold text-emerald-600 font-heading">
                      +{selectedPlayer.pressure_performance?.ipl_context_adjusted_delta_sr || selectedPlayer.pressure_performance?.context_adjusted_delta_sr || selectedPlayer.player.ipl_context_delta_sr || '-'}
                    </span>
                    <span className="text-[10px] text-rr-muted block mt-0.5">{selectedPlayer.pressure_performance?.ipl_pressure_volume || 0} balls ({selectedPlayer.pressure_performance?.ipl_pressure_matches || 0}m)</span>
                  </div>
                  <div className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border text-center">
                    <span className="text-[10px] text-rr-muted uppercase font-bold block">Pressure Dot %</span>
                    <span className="text-base font-extrabold text-rr-charcoal font-heading">
                      {selectedPlayer.pressure_performance?.pressure_dot_pct || selectedPlayer.player.ipl_dot_ball_pct || '-'}%
                    </span>
                    <span className="text-[10px] text-rr-muted block mt-0.5">
                      Δ {selectedPlayer.pressure_performance?.delta_dot_pct ? `${selectedPlayer.pressure_performance.delta_dot_pct}%` : '-'}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border text-center">
                    <span className="text-[10px] text-rr-muted uppercase font-bold block">Match Pass Rate</span>
                    <span className="text-base font-extrabold text-rr-pink font-heading">
                      {selectedPlayer.pressure_performance?.pressure_match_pass_rate ? `${selectedPlayer.pressure_performance.pressure_match_pass_rate}%` : `${selectedPlayer.player.ipl_match_pass_rate || 0}%`}
                    </span>
                    <span className="text-[10px] text-rr-muted block mt-0.5">Over Target SR</span>
                  </div>
                </div>

                {/* Reconciled Cohort Separation (IPL vs Combined Cross-Format) */}
                <div className="p-3.5 rounded-xl bg-white border border-rr-border space-y-2">
                  <div className="flex items-center justify-between pb-1.5 border-b border-rr-border text-xs font-bold text-rr-charcoal">
                    <span className="flex items-center gap-1.5">
                      <Target className="w-3.5 h-3.5 text-rr-pink" />
                      Audited Cohort Reconciliation: IPL vs Combined Cross-Format RAE
                    </span>
                    <span className="text-[10px] text-rr-muted">Strict Population Separation</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-lg bg-emerald-50/70 border border-emerald-200">
                      <div className="flex justify-between items-center pb-1 border-b border-emerald-200/60 font-bold text-emerald-950">
                        <span>Accepted Primary: IPL Pressure Cohort</span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-100 text-emerald-800">OFFICIAL RANKING</span>
                      </div>
                      <div className="mt-2 space-y-1 text-[11px] text-emerald-900">
                        <div className="flex justify-between">
                          <span className="text-emerald-700">Evaluated Deliveries:</span>
                          <span className="font-extrabold">{selectedPlayer.pressure_performance?.ipl_pressure_volume || selectedPlayer.player.ipl_pressure_volume || 0} balls ({selectedPlayer.pressure_performance?.ipl_pressure_matches || selectedPlayer.player.ipl_matches || 0} matches)</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-emerald-700">Observed Strike Rate:</span>
                          <span className="font-extrabold">{selectedPlayer.pressure_performance?.ipl_observed_pressure_sr || selectedPlayer.pressure_performance?.ipl_pressure_strike_rate || selectedPlayer.player.ipl_raw_sr || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-emerald-700">Context Expected SR:</span>
                          <span className="font-semibold">{selectedPlayer.pressure_performance?.ipl_expected_pressure_sr || '-'}</span>
                        </div>
                        <div className="flex justify-between pt-1 border-t border-emerald-200/60">
                          <span className="font-bold text-emerald-950">IPL Context RAE (ΔSR):</span>
                          <span className="font-extrabold text-emerald-700 text-sm">+{selectedPlayer.pressure_performance?.ipl_context_adjusted_delta_sr || selectedPlayer.player.ipl_context_delta_sr || '-'}</span>
                        </div>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                      <div className="flex justify-between items-center pb-1 border-b border-slate-200 font-bold text-slate-800">
                        <span>Cross-Format: Combined IPL + T20I Cohort</span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-200 text-slate-700">DUAL FORMAT</span>
                      </div>
                      <div className="mt-2 space-y-1 text-[11px] text-slate-700">
                        <div className="flex justify-between">
                          <span className="text-slate-500">Evaluated Deliveries:</span>
                          <span className="font-extrabold">{selectedPlayer.pressure_performance?.combined_pressure_volume || selectedPlayer.player.combined_pressure_volume || 0} balls ({selectedPlayer.pressure_performance?.combined_pressure_matches || selectedPlayer.player.combined_matches || 0} matches)</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Observed Strike Rate:</span>
                          <span className="font-extrabold">{selectedPlayer.pressure_performance?.combined_observed_pressure_sr || selectedPlayer.pressure_performance?.combined_pressure_strike_rate || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Context Expected SR:</span>
                          <span className="font-semibold">{selectedPlayer.pressure_performance?.combined_expected_pressure_sr || '-'}</span>
                        </div>
                        <div className="flex justify-between pt-1 border-t border-slate-200">
                          <span className="font-bold text-slate-900">Combined Context RAE (ΔSR):</span>
                          <span className="font-extrabold text-rr-deepPink text-sm">+{selectedPlayer.pressure_performance?.combined_context_adjusted_delta_sr || '-'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Phase Breakdown */}
                {selectedPlayer.phases && selectedPlayer.phases.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-rr-muted uppercase tracking-wider mb-2">
                      Innings Phase Pressure Performance
                    </h4>
                    <div className="space-y-2">
                      {selectedPlayer.phases.map((ph, idx) => (
                        <div key={idx} className="p-3 rounded-lg bg-rr-warmWhite border border-rr-border flex items-center justify-between text-xs">
                          <div>
                            <div className="font-bold text-rr-charcoal">{ph.innings_phase}</div>
                            <div className="text-[11px] text-rr-muted">{ph.phase_pressure_balls} balls • {ph.phase_pressure_runs} runs</div>
                          </div>
                          <div className="text-right">
                            <div className="font-extrabold text-rr-pink text-sm">{ph.phase_pressure_sr?.toFixed(1)} SR</div>
                            <div className="text-[10px] text-rr-muted">{ph.phase_pressure_dot_pct?.toFixed(1)}% dots • {ph.phase_pressure_boundary_pct?.toFixed(1)}% bnd</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* High Leverage Crunch Subsets */}
                {selectedPlayer.pressure_performance && (
                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                      Crunch & Panic State Exposure (RRR &ge; 12.0 or Wickets &le; 3)
                    </h4>
                    <div className="grid grid-cols-3 gap-2 text-center text-xs">
                      <div className="p-2 bg-white rounded-lg border border-slate-200">
                        <span className="text-[10px] text-slate-500 block font-semibold">Tail Anchor</span>
                        <span className="font-extrabold text-slate-800">{selectedPlayer.pressure_performance.tail_anchor_balls || 0} balls</span>
                        <span className="text-[10px] text-rr-pink block">{selectedPlayer.pressure_performance.tail_anchor_sr ? `${selectedPlayer.pressure_performance.tail_anchor_sr} SR` : '-'}</span>
                      </div>
                      <div className="p-2 bg-white rounded-lg border border-slate-200">
                        <span className="text-[10px] text-slate-500 block font-semibold">Final Crunch</span>
                        <span className="font-extrabold text-slate-800">{selectedPlayer.pressure_performance.final_crunch_balls || 0} balls</span>
                        <span className="text-[10px] text-rr-pink block">{selectedPlayer.pressure_performance.final_crunch_sr ? `${selectedPlayer.pressure_performance.final_crunch_sr} SR` : '-'}</span>
                      </div>
                      <div className="p-2 bg-white rounded-lg border border-slate-200">
                        <span className="text-[10px] text-slate-500 block font-semibold">Combined Panic</span>
                        <span className="font-extrabold text-slate-800">{selectedPlayer.pressure_performance.combined_panic_balls || 0} balls</span>
                        <span className="text-[10px] text-rr-pink block">{selectedPlayer.pressure_performance.combined_panic_sr ? `${selectedPlayer.pressure_performance.combined_panic_sr} SR` : '-'}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: MACHINE LEARNING CONTEXT */}
            {dossierTab === 'ml' && (
              <div className="space-y-4">
                {/* ML Model Benchmark Header */}
                <div className="p-3.5 rounded-xl bg-indigo-50/70 border border-indigo-200 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Brain className="w-5 h-5 text-indigo-700" />
                    <div>
                      <span className="text-xs font-bold text-indigo-950 block">Contextual Expected Runs Regressor</span>
                      <span className="text-[11px] text-indigo-700">LightGBM v1.0 • Chronological Match-Grouped Out-of-Time</span>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-indigo-100 text-indigo-800 border border-indigo-200">
                    TEST SET 2026
                  </span>
                </div>

                {/* Population Scope Tag */}
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 flex items-center justify-between">
                  <span className="font-semibold text-[11px]">Population Scope:</span>
                  <span className="text-[11px] font-bold text-indigo-900">
                    {selectedPlayer.ml_context?.population_scope || 'Season 2026 Out-of-Time Test Partition (covers ALL 31,165 test deliveries across normal and pressure phases)'}
                  </span>
                </div>

                {/* 2026 Holdout Test Evaluation Card */}
                {selectedPlayer.ml_context && (
                  <div className="p-4 rounded-xl bg-white border border-rr-border space-y-3">
                    <div className="flex items-center justify-between pb-2 border-b border-rr-border">
                      <span className="text-xs font-bold text-rr-charcoal font-heading">
                        Holdout Partition Performance (2026 Season)
                      </span>
                      <span className="text-xs text-rr-muted">
                        {selectedPlayer.ml_context.test_eval_deliveries > 0
                          ? `${selectedPlayer.ml_context.test_eval_deliveries} test deliveries`
                          : 'Historical sample only'}
                      </span>
                    </div>

                    {selectedPlayer.ml_context.test_eval_deliveries > 0 ? (
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-center">
                        <div className="p-2.5 bg-rr-warmWhite rounded-lg border border-rr-border">
                          <span className="text-[10px] text-rr-muted block font-semibold">Actual Runs</span>
                          <span className="text-base font-extrabold text-rr-charcoal font-heading">
                            {selectedPlayer.ml_context.actual_runs}
                          </span>
                          <span className="text-[10px] text-rr-muted block">{selectedPlayer.ml_context.actual_rate} SR</span>
                        </div>
                        <div className="p-2.5 bg-rr-warmWhite rounded-lg border border-rr-border">
                          <span className="text-[10px] text-rr-muted block font-semibold">Expected Runs</span>
                          <span className="text-base font-extrabold text-rr-charcoal font-heading">
                            {selectedPlayer.ml_context.expected_runs_lightgbm}
                          </span>
                          <span className="text-[10px] text-rr-muted block">{selectedPlayer.ml_context.expected_rate} Exp SR</span>
                        </div>
                        <div className="p-2.5 bg-emerald-50 rounded-lg border border-emerald-200">
                          <span className="text-[10px] text-emerald-800 block font-semibold">Net Residual</span>
                          <span className="text-base font-extrabold text-emerald-700 font-heading">
                            {selectedPlayer.ml_context.net_residual ? (selectedPlayer.ml_context.net_residual > 0 ? `+${selectedPlayer.ml_context.net_residual}` : selectedPlayer.ml_context.net_residual) : '-'}
                          </span>
                          <span className="text-[10px] text-emerald-800 block">runs added</span>
                        </div>
                        <div className="p-2.5 bg-emerald-50 rounded-lg border border-emerald-200">
                          <span className="text-[10px] text-emerald-800 block font-semibold">Residual / Ball</span>
                          <span className="text-base font-extrabold text-emerald-700 font-heading">
                            {selectedPlayer.ml_context.mean_residual_per_ball ? (selectedPlayer.ml_context.mean_residual_per_ball > 0 ? `+${selectedPlayer.ml_context.mean_residual_per_ball}` : selectedPlayer.ml_context.mean_residual_per_ball) : '-'}
                          </span>
                          <span className="text-[10px] text-emerald-800 block">runs / ball</span>
                        </div>
                      </div>
                    ) : (
                      <div className="p-3 bg-slate-50 rounded-lg text-xs text-slate-600 border border-slate-200">
                        {selectedPlayer.ml_context.test_status}
                      </div>
                    )}
                  </div>
                )}

                {/* Primary Cohort Benchmark Context RAE */}
                <div className="p-3.5 rounded-xl bg-rr-warmWhite border border-rr-border flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-rr-charcoal block">Accepted Primary Context RAE (+ΔSR)</span>
                    <span className="text-[11px] text-rr-muted">Controlling for format, phase, RRR deficit, and pre-delivery wicket resources</span>
                  </div>
                  <span className="text-lg font-extrabold text-emerald-600 font-heading">
                    +{selectedPlayer.pressure_performance?.ipl_context_adjusted_delta_sr || selectedPlayer.player.ipl_context_delta_sr || '-'}
                  </span>
                </div>

                {/* Critical Methodological Disclaimers */}
                <div className="space-y-2 pt-1 text-xs">
                  <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 text-blue-950 space-y-1">
                    <div className="font-bold flex items-center gap-1.5 text-blue-900">
                      <AlertCircle className="w-4 h-4 text-blue-700 flex-shrink-0" />
                      Model Scope & Interpretation
                    </div>
                    <p className="text-[11px] leading-relaxed">
                      Supervised contextual ML models estimate delivery-level match situation expectations (baseline), <strong>NOT individual intrinsic player talent</strong>. Net residual outperformance measures observed player deviation above or below contextual expectation.
                    </p>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-800 space-y-1">
                    <div className="font-bold flex items-center gap-1.5 text-slate-900">
                      <Scale className="w-4 h-4 text-slate-600 flex-shrink-0" />
                      Uncertainty & Limitations
                    </div>
                    <p className="text-[11px] leading-relaxed">
                      Delivery-level unexplainable variance is inherently high in T20 cricket (LightGBM holdout test R&sup2; &asymp; 0.024 across 31,165 test balls). Trajectory/pitch-map and shot execution metrics are absent from standard scorecards; model serves strictly as an objective contextual baseline.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: BEHAVIORAL RESPONSE */}
            {dossierTab === 'behavioral' && (
              <div className="space-y-4">
                {/* Methodological Framework Note */}
                <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200 text-xs text-amber-950 space-y-1">
                  <div className="font-bold flex items-center gap-1.5 text-amber-900">
                    <Zap className="w-4 h-4 text-amber-600" />
                    Observable Event Sequence Analysis (Zero Psychological Speculation)
                  </div>
                  <p className="text-[11px] leading-relaxed">
                    Evaluates observable response sequences strictly partitioned by innings and match boundaries. Analyzes observable event occurrences without inferring unobservable psychological traits.
                  </p>
                </div>

                {/* Behavioral Metrics Grid */}
                {selectedPlayer.behavioral && selectedPlayer.behavioral.striker_id ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-center text-xs">
                      <div className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border">
                        <span className="text-[10px] text-rr-muted uppercase font-bold block">Scoring Resilience Index</span>
                        <span className="text-lg font-extrabold text-rr-pink font-heading">
                          {selectedPlayer.behavioral.scoring_resilience_index ? `${selectedPlayer.behavioral.scoring_resilience_index > 0 ? '+' : ''}${selectedPlayer.behavioral.scoring_resilience_index}` : '-'}
                        </span>
                        <span className="text-[10px] text-rr-muted block">SRI composite</span>
                      </div>
                      <div className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border">
                        <span className="text-[10px] text-rr-muted uppercase font-bold block">Drought-State SR (Streak &ge; 2)</span>
                        <span className="text-lg font-extrabold text-rr-charcoal font-heading">
                          {selectedPlayer.behavioral.drought_state_strike_rate || selectedPlayer.behavioral.post_dot_strike_rate || '-'}
                        </span>
                        <span className="text-[10px] text-emerald-600 font-semibold block">
                          Δ {selectedPlayer.behavioral.delta_sr_drought_state || selectedPlayer.behavioral.delta_sr_post_dot ? `${(selectedPlayer.behavioral.delta_sr_drought_state || selectedPlayer.behavioral.delta_sr_post_dot || 0) > 0 ? '+' : ''}${selectedPlayer.behavioral.delta_sr_drought_state || selectedPlayer.behavioral.delta_sr_post_dot}` : '-'} SR
                        </span>
                      </div>
                      <div className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border">
                        <span className="text-[10px] text-rr-muted uppercase font-bold block">Drought Recovery Latency</span>
                        <span className="text-lg font-extrabold text-rr-charcoal font-heading">
                          {selectedPlayer.behavioral.avg_balls_to_scoring || '-'} balls
                        </span>
                        <span className="text-[10px] text-rr-muted block">avg to scoring shot</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                      {/* 1. Correctly Labeled Drought-State Card */}
                      <div className="p-3.5 rounded-xl bg-white border border-rr-border space-y-1.5">
                        <div className="flex items-center justify-between pb-1 border-b border-rr-border">
                          <span className="font-bold text-rr-charcoal block">Drought-State Scoring Performance</span>
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-rr-palePink text-rr-deepPink font-bold">STREAK &ge; 2 DOTS</span>
                        </div>
                        <div className="text-[11px] space-y-1 pt-1">
                          <div className="flex justify-between">
                            <span className="text-rr-muted">Drought-State Deliveries Faced:</span>
                            <span className="font-bold text-rr-charcoal">{selectedPlayer.behavioral.drought_state_balls || selectedPlayer.behavioral.post_dot_balls} balls</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-rr-muted">Drought-State Strike Rate:</span>
                            <span className="font-extrabold text-rr-pink">{selectedPlayer.behavioral.drought_state_strike_rate || selectedPlayer.behavioral.post_dot_strike_rate} SR</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-rr-muted">Drought Dot Ball %:</span>
                            <span className="font-semibold text-rr-charcoal">{selectedPlayer.behavioral.drought_state_dot_pct || selectedPlayer.behavioral.post_dot_dot_pct}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-rr-muted">Drought Boundary %:</span>
                            <span className="font-semibold text-rr-charcoal">{selectedPlayer.behavioral.drought_state_boundary_pct || selectedPlayer.behavioral.post_dot_boundary_pct}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-rr-muted">Drought Dismissal Risk:</span>
                            <span className="font-semibold text-rr-charcoal">{selectedPlayer.behavioral.drought_state_wicket_pct || selectedPlayer.behavioral.post_dot_wicket_pct}%</span>
                          </div>
                        </div>
                        <p className="text-[10px] text-rr-muted pt-1 border-t border-rr-border leading-relaxed">
                          Evaluates all deliveries faced while remaining in a personal streak of &ge; 2 dots until broken by a scoring shot. (Cohort total: 19,818 deliveries across 14,876 triggers in 834 matches).
                        </p>
                      </div>

                      {/* 2. Strict Immediate t+1 Single-Ball Card */}
                      <div className="p-3.5 rounded-xl bg-white border border-rr-border space-y-1.5">
                        <div className="flex items-center justify-between pb-1 border-b border-rr-border">
                          <span className="font-bold text-rr-charcoal block">Strict Immediate t+1 Recovery</span>
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-100 text-amber-800 font-bold">SINGLE BALL (t+1)</span>
                        </div>
                        <div className="p-2.5 rounded-lg bg-amber-50/70 border border-amber-200 text-amber-950 space-y-1">
                          <div className="flex items-center gap-1 font-bold text-[11px] text-amber-900">
                            <AlertCircle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
                            Insufficient Evidence at Individual Player Level
                          </div>
                          <p className="text-[10px] leading-relaxed">
                            Strict single-ball (t+1) observation data is not preserved at individual candidate level without event-level deduplication. In accordance with competition audit standards, drought-state strike rate is <strong>strictly NOT substituted</strong>.
                          </p>
                        </div>
                        <div className="text-[11px] space-y-1 pt-1">
                          <div className="flex justify-between">
                            <span className="text-rr-muted">Cohort Strict t+1 Balls:</span>
                            <span className="font-semibold text-rr-charcoal">12,653 deliveries</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-rr-muted">Cohort Unique Trigger Episodes:</span>
                            <span className="font-semibold text-rr-charcoal">14,876 episodes</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-rr-muted">Evaluated Matches:</span>
                            <span className="font-semibold text-rr-charcoal">834 matches</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="p-3.5 rounded-xl bg-white border border-rr-border space-y-1.5 text-xs">
                      <div className="flex items-center justify-between pb-1 border-b border-rr-border">
                        <span className="font-bold text-rr-charcoal block">Post-Wicket Team Consolidation Window</span>
                        <span className="font-extrabold text-rr-pink text-[10px]">{selectedPlayer.behavioral.sample_confidence} CONFIDENCE</span>
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center pt-1">
                        <div className="p-2 rounded-lg bg-rr-warmWhite border border-rr-border">
                          <span className="text-[10px] text-rr-muted block">Deliveries Faced</span>
                          <span className="font-extrabold text-rr-charcoal text-sm">{selectedPlayer.behavioral.post_wkt_balls}</span>
                        </div>
                        <div className="p-2 rounded-lg bg-rr-warmWhite border border-rr-border">
                          <span className="text-[10px] text-rr-muted block">Post-Wicket SR</span>
                          <span className="font-extrabold text-rr-charcoal text-sm">{selectedPlayer.behavioral.post_wkt_strike_rate}</span>
                        </div>
                        <div className="p-2 rounded-lg bg-rr-warmWhite border border-rr-border">
                          <span className="text-[10px] text-rr-muted block">Post-Wicket Dot %</span>
                          <span className="font-extrabold text-rr-charcoal text-sm">{selectedPlayer.behavioral.post_wkt_dot_pct}%</span>
                        </div>
                        <div className="p-2 rounded-lg bg-rr-warmWhite border border-rr-border">
                          <span className="text-[10px] text-rr-muted block">Dismissal Risk</span>
                          <span className="font-extrabold text-rr-charcoal text-sm">{selectedPlayer.behavioral.post_wkt_wicket_pct ?? 0}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 text-center">
                    Insufficient post-dot trigger sequences recorded to generate behavioral recovery metrics.
                  </div>
                )}
              </div>
            )}

            {/* TAB 5: RELIABILITY & RISK FLAGS */}
            {dossierTab === 'reliability' && (
              <div className="space-y-4">
                {/* Empirical Bayes Shrinkage Curve */}
                {selectedPlayer.shrinkage_curve && selectedPlayer.shrinkage_curve.length > 0 && (
                  <div className="p-4 rounded-xl bg-white border border-rr-border space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-rr-charcoal font-heading">
                        Empirical Bayes Shrinkage Curve (M = 25 to 90)
                      </h4>
                      <span className="text-[10px] text-rr-muted">Prior Mean = 135.53 SR</span>
                    </div>
                    <div className="h-44 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={selectedPlayer.shrinkage_curve} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#F0E7ED" />
                          <XAxis dataKey="parameter" tick={{ fill: '#77717C', fontSize: 10 }} />
                          <YAxis tick={{ fill: '#77717C', fontSize: 10 }} domain={['dataMin - 10', 'dataMax + 10']} />
                          <Tooltip
                            contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#F0E7ED', borderRadius: '8px' }}
                            formatter={(val: number) => [`${val.toFixed(1)} SR`, 'Strike Rate']}
                          />
                          <ReferenceLine y={135.53} stroke="#A49FA9" strokeDasharray="4 4" label={{ value: 'Prior 135.5', fill: '#77717C', fontSize: 10 }} />
                          <Line type="monotone" dataKey="sr" stroke="#E6007E" strokeWidth={3} dot={{ r: 4, fill: '#E6007E' }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* 95% Credible Intervals */}
                {selectedPlayer.reliability && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border space-y-1">
                      <span className="text-[10px] text-rr-muted uppercase font-bold block">Pressure SR 95% Credible Interval</span>
                      <span className="font-extrabold text-rr-charcoal text-sm font-heading">
                        {selectedPlayer.reliability.pressure_sr_ci_lower_95 && selectedPlayer.reliability.pressure_sr_ci_upper_95
                          ? `[${selectedPlayer.reliability.pressure_sr_ci_lower_95.toFixed(1)} to ${selectedPlayer.reliability.pressure_sr_ci_upper_95.toFixed(1)}] SR`
                          : 'Sample bounds precomputed'}
                      </span>
                      <span className="text-[10px] text-rr-muted block">Posterior credible interval under normal prior</span>
                    </div>

                    <div className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border space-y-1">
                      <span className="text-[10px] text-rr-muted uppercase font-bold block">Posterior Dot % (95% CI)</span>
                      <span className="font-extrabold text-rr-charcoal text-sm font-heading">
                        {selectedPlayer.reliability.pressure_dot_pct_ci_lower_95 && selectedPlayer.reliability.pressure_dot_pct_ci_upper_95
                          ? `[${selectedPlayer.reliability.pressure_dot_pct_ci_lower_95.toFixed(1)}% to ${selectedPlayer.reliability.pressure_dot_pct_ci_upper_95.toFixed(1)}%]`
                          : 'Posterior Wilson bounds'}
                      </span>
                      <span className="text-[10px] text-rr-muted block">Beta-binomial posterior interval</span>
                    </div>
                  </div>
                )}

                {/* Candidate Risk Flags */}
                <div className="p-4 rounded-xl bg-white border border-rr-border space-y-2.5">
                  <div className="flex items-center justify-between pb-2 border-b border-rr-border">
                    <span className="text-xs font-bold text-rr-charcoal font-heading">
                      Identified Candidate Risk Flags & Vulnerabilities
                    </span>
                    <span className="text-[10px] text-rr-muted">Pre-auction vulnerability audit</span>
                  </div>

                  {selectedPlayer.reliability?.risk_flags && selectedPlayer.reliability.risk_flags.length > 0 ? (
                    <div className="space-y-2">
                      {selectedPlayer.reliability.risk_flags.map((rf, idx) => (
                        <div key={idx} className="p-3 rounded-lg bg-rr-warmWhite border border-rr-border space-y-1.5 text-xs">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-rr-charcoal">{rf.format} Cohort ({rf.pressure_volume} balls, {rf.pressure_matches}m)</span>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold ${
                              rf.risk_severity === 'LOW_RISK'
                                ? 'bg-emerald-100 text-emerald-800'
                                : rf.risk_severity === 'MODERATE_RISK'
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {rf.risk_severity} ({rf.risk_flag_count} flags)
                            </span>
                          </div>
                          <p className="text-[11px] text-rr-muted leading-relaxed">
                            {rf.risk_notes || 'No significant tactical vulnerabilities detected.'}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-3 rounded-lg bg-emerald-50 text-emerald-800 text-xs border border-emerald-200">
                      No significant tactical or sample vulnerabilities detected across audited cohorts.
                    </div>
                  )}
                </div>
              </div>
            )}
              </div>
            </div>
          </div>,
          document.body
        )}
    </div>
  );
};
