import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import {
  Search,
  Filter,
  X,
  Shield,
  TrendingDown,
  Activity,
  Layers,
  ChevronRight,
  Flame,
  Brain,
  Target,
  Scale,
  Zap,
  AlertTriangle,
  CheckCircle2,
  Clock,
  GitCompare,
  AlertCircle,
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
import { fetchBowlers, fetchBowlerDetail } from '../services/api';
import { PlayerOverview, PlayerDetail } from '../types';
import { SectionHeading } from '../components/common/SectionHeading';
import { ArchetypeBadge, TierBadge, Badge } from '../components/common/Badge';
import { PageHeroCard } from '../components/common/PageHeroCard';
import { PlayerAvatar } from '../components/common/PlayerAvatar';

interface BowlerIntelligenceProps {
  initialPlayerId?: number;
}

export const BowlerIntelligence: React.FC<BowlerIntelligenceProps> = ({ initialPlayerId }) => {
  const [bowlers, setBowlers] = useState<PlayerOverview[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('ALL');
  const [tierFilter, setTierFilter] = useState('ALL');
  const [formatView, setFormatView] = useState<'IPL' | 'T20I'>('IPL');
  const [selectedPlayer, setSelectedPlayer] = useState<PlayerDetail | null>(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [dossierTab, setDossierTab] = useState<'overview' | 'pressure' | 'ml' | 'behavioral' | 'reliability'>('overview');

  useEffect(() => {
    setLoading(true);
    fetchBowlers({ search, role: roleFilter, tier: tierFilter })
      .then((res) => {
        // Exclude Sikandar Raza from bowler intelligence UI candidate evaluation
        const filtered = (res || []).filter(
          (bw) => !bw.player_name.toLowerCase().includes('sikandar raza')
        );
        setBowlers(filtered);
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
    fetchBowlerDetail(id)
      .then((detail) => {
        setSelectedPlayer(detail);
        setDossierTab('overview');
        setModalLoading(false);
      })
      .catch(() => setModalLoading(false));
  };

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Standardized Compact Hero Section */}
      <PageHeroCard
        badge="Evaluation Engine"
        badgeIcon={<Shield className="w-3.5 h-3.5 text-rr-pink" />}
        title="Bowler Intelligence Workspace"
        description="Context-adjusted defensive suppression (RCAE), Bayesian shrunk economy rates (M=45), wicket penetration, and phase-specific execution."
      />

      {/* Filter Controls Bar */}
      <div className="bg-white rounded-xl border border-rr-border p-3.5 shadow-card">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-3 w-4 h-4 text-rr-muted" />
            <input
              type="text"
              placeholder="Search bowler name..."
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
              <option value="ALL">All Bowling Roles</option>
              <option value="Middle Specialist">Middle Specialist</option>
              <option value="Death Specialist">Death Specialist</option>
              <option value="All-Phases">All-Phases</option>
              <option value="Powerplay Specialist">Powerplay Specialist</option>
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
                  ? 'bg-rr-deepPink text-white shadow-sm'
                  : 'text-rr-muted hover:text-rr-charcoal'
              }`}
            >
              IPL Metrics
            </button>
            <button
              onClick={() => setFormatView('T20I')}
              className={`flex-1 py-1 rounded-lg text-xs font-bold transition-all ${
                formatView === 'T20I'
                  ? 'bg-rr-deepPink text-white shadow-sm'
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
                <th className="py-2 px-2 text-right" title="Legal balls bowled in high-pressure context">
                  <div>{formatView}</div>
                  <div>PRESSURE</div>
                  <div>BALLS</div>
                </th>
                <th className="py-2 px-2 text-right" title="Raw high-pressure economy rate">
                  <div>{formatView}</div>
                  <div>RAW</div>
                  <div>ECON</div>
                </th>
                <th className="py-2 px-2 text-right" title="Empirical Bayes shrunk economy (M=45 prior)">
                  <div>{formatView}</div>
                  <div>SHRUNK</div>
                  <div>M45</div>
                </th>
                <th className="py-2 px-2 text-right" title="Primary All-Runs RCAE (ΔEconomy vs contextual expectation)">
                  <div>RCAE</div>
                  <div>(ΔECON)</div>
                </th>
                <th className="py-2 px-2 text-right" title="Wickets per 6 legal balls under pressure">
                  <div>WKTS</div>
                  <div>/ OV</div>
                </th>
                <th className="py-2 px-2 text-right" title="Dot ball percentage under pressure">
                  <div>DOT</div>
                  <div>%</div>
                </th>
                <th className="py-2 px-2 text-right" title="Boundary concession percentage">
                  <div>BND</div>
                  <div>%</div>
                </th>
                <th className="py-2 px-2 text-right" title="Match pass rate (% matches meeting benchmark)">
                  <div>PASS</div>
                  <div>RATE</div>
                </th>
                <th
                  className="py-2 px-2 text-center"
                  title="Statistical Evidence Tier: Primary candidate qualification portfolio (IPL when available, or T20I international for non-IPL selections). Evaluates volume (≥60b), distinct matches (≥8), and competitions (≥2)."
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
                  <td colSpan={14} className="py-8 text-center text-rr-muted animate-pulse">
                    Loading audited bowler evaluation data...
                  </td>
                </tr>
              ) : bowlers.length === 0 ? (
                <tr>
                  <td colSpan={14} className="py-8 text-center text-rr-muted">
                    No bowler candidates match the selected filters.
                  </td>
                </tr>
              ) : (
                bowlers.map((bw) => {
                  const vol = formatView === 'IPL' ? bw.ipl_pressure_volume : bw.t20i_pressure_volume;
                  const rawEcon = formatView === 'IPL' ? bw.ipl_raw_econ : bw.t20i_raw_econ;
                  const shrunkEcon = formatView === 'IPL' ? bw.ipl_shrunk_m45 : bw.t20i_shrunk_m45;
                  const rcae = formatView === 'IPL' ? bw.ipl_context_delta_econ : bw.t20i_context_delta_econ;
                  const wktsOv = formatView === 'IPL' ? bw.ipl_wickets_per_over : bw.t20i_wickets_per_over;
                  const dot = formatView === 'IPL' ? bw.ipl_dot_ball_pct : bw.t20i_dot_ball_pct;
                  const bndConc = formatView === 'IPL' ? bw.ipl_boundary_concession_pct : bw.t20i_boundary_concession_pct;
                  const pass = formatView === 'IPL' ? bw.ipl_match_pass_rate : bw.t20i_match_pass_rate;
                  const isT20IOnlyCandidate = (!vol || vol === 0) && ((bw.t20i_pressure_volume ?? 0) > 0);
                  const tierTooltip = isT20IOnlyCandidate
                    ? `Qualified via T20I international portfolio (${bw.t20i_pressure_volume ?? 0}b across ${bw.t20i_matches ?? 0}m, ${bw.t20i_competitions ?? 0}c)`
                    : (bw.combined_pressure_volume ?? 0) > (vol || 0)
                    ? `Primary IPL evidence: ${vol}b across ${bw.ipl_matches ?? 0}m (${bw.evidence_tier.replace('_EVIDENCE', '')}). Combined multi-format exposure: ${bw.combined_pressure_volume ?? 0}b across ${bw.combined_matches ?? 0}m.`
                    : `Evaluated across ${vol}b across ${bw.ipl_matches || bw.t20i_matches || 0} matches.`;

                  return (
                    <tr
                      key={bw.player_id}
                      onClick={() => handleOpenPlayer(bw.player_id)}
                      className="hover:bg-rr-softPink/40 transition-colors cursor-pointer group whitespace-nowrap"
                    >
                      <td className="py-2.5 px-2 text-center font-extrabold text-rr-deepPink">
                        {bw.top_10_rank ? `#${bw.top_10_rank}` : '-'}
                      </td>
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-2.5">
                          <PlayerAvatar
                            playerId={bw.player_id}
                            playerName={bw.player_name}
                            size="sm"
                            isTop10={!!bw.top_10_rank}
                          />
                          <div>
                            <div className="font-bold text-rr-charcoal group-hover:text-rr-deepPink leading-tight">
                              {bw.player_name}
                            </div>
                            <div className="text-[10px] text-rr-muted">ID: {bw.player_id}</div>
                          </div>
                        </div>
                      </td>
                      <td className="py-2.5 px-2 text-rr-muted">{bw.primary_role}</td>
                      <td className="py-2.5 px-2 text-right font-medium">
                        {vol ? `${vol}b` : '0b'}
                      </td>
                      <td className="py-2.5 px-2 text-right font-bold text-rr-charcoal font-heading text-sm">
                        {rawEcon ? rawEcon.toFixed(2) : '-'}
                      </td>
                      <td className="py-2.5 px-2 text-right font-semibold text-rr-muted">
                        {shrunkEcon ? shrunkEcon.toFixed(2) : '-'}
                      </td>
                      <td className="py-2.5 px-2 text-right font-semibold text-emerald-600">
                        {typeof rcae === 'number' ? rcae.toFixed(2) : '-'}
                      </td>
                      <td className="py-2.5 px-2 text-right font-extrabold text-rr-pink">
                        {typeof wktsOv === 'number' ? wktsOv.toFixed(2) : '-'}
                      </td>
                      <td className="py-2.5 px-2 text-right text-rr-muted">
                        {typeof dot === 'number' ? `${dot.toFixed(1)}%` : '-'}
                      </td>
                      <td className="py-2.5 px-2 text-right font-medium text-rr-charcoal">
                        {typeof bndConc === 'number' ? `${bndConc.toFixed(1)}%` : '-'}
                      </td>
                      <td className="py-2.5 px-2 text-right text-rr-muted">
                        {typeof pass === 'number' ? `${pass.toFixed(1)}%` : '-'}
                      </td>
                      <td className="py-2.5 px-2 text-center">
                        <TierBadge tier={bw.evidence_tier} title={tierTooltip} />
                      </td>
                      <td className="py-2.5 px-2">
                        <ArchetypeBadge archetype={bw.stability_archetype} />
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

      {/* Slide-out Bowler Profile Scout Dossier Modal */}
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
                    className="ring-2 ring-rr-deepPink"
                  />
                  <div>
                    <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                      {selectedPlayer.player.top_10_rank ? (
                        <span className="px-2.5 py-0.5 rounded-full bg-rr-deepPink text-white font-extrabold text-xs shadow-sm">
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
                      Bowler ID: {selectedPlayer.player.player_id} • Primary Role: {selectedPlayer.player.primary_role} • {selectedPlayer.player.phase_suitability || 'All Phases'}
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
                  <span className="text-slate-700 font-bold block">32,529 deliveries (144 matches)</span>
                  <span className="text-slate-400 text-[9px] block">All match deliveries (Normal + Pressure)</span>
                </div>
                <div className="p-2 rounded-lg bg-white border border-slate-200">
                  <span className="font-extrabold text-rr-deepPink block">2. Primary Pressure Cohort</span>
                  <span className="text-slate-700 font-bold block">44,333 legal balls (837 matches)</span>
                  <span className="text-slate-400 text-[9px] block">All-Runs RCAE under L1 &ge; 0.50</span>
                </div>
                <div className="p-2 rounded-lg bg-white border border-slate-200">
                  <span className="font-extrabold text-amber-700 block">3. Behavioral Event Sample</span>
                  <span className="text-slate-700 font-bold block">32,662 triggers (836 matches)</span>
                  <span className="text-slate-400 text-[9px] block">29,219 intra-over (t+1) recoveries</span>
                </div>
                <div className="p-2 rounded-lg bg-white border border-slate-200">
                  <span className="font-extrabold text-emerald-700 block">4. Reliability Evaluation</span>
                  <span className="text-slate-700 font-bold block">{selectedPlayer.pressure_performance?.ipl_pressure_legal_balls || selectedPlayer.player.ipl_pressure_volume || 0} IPL legal balls ({selectedPlayer.pressure_performance?.ipl_pressure_matches || selectedPlayer.player.ipl_matches || 0}m)</span>
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
                <Shield className="w-3.5 h-3.5" />
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
                Behavioral Bounce-Back
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
                      <Shield className="w-3.5 h-3.5" />
                      Franchise Selection Rationale & Defensive Fit
                    </div>
                    <p className="text-xs text-rr-charcoal leading-relaxed">
                      {selectedPlayer.player.selection_rationale}
                    </p>
                  </div>
                )}

                {/* Format-Specific Exposure */}
                <div>
                  <h4 className="text-xs font-bold text-rr-muted uppercase tracking-wider mb-2.5">
                    Format Exposure & Defensive Containment
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="p-3.5 rounded-xl bg-rr-warmWhite border border-rr-border space-y-2">
                      <div className="flex items-center justify-between text-xs pb-1 border-b border-rr-border">
                        <span className="font-bold text-rr-charcoal">IPL Pressure</span>
                        <span className="text-rr-deepPink font-bold">
                          {selectedPlayer.player.ipl_pressure_volume || 0} legal balls ({selectedPlayer.player.ipl_matches || 0}m)
                        </span>
                      </div>
                      <div className="text-[11px] space-y-1">
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Raw Economy (Std):</span>
                          <span className="font-bold text-rr-charcoal">{selectedPlayer.player.ipl_raw_econ?.toFixed(2) || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Shrunk Econ (M=45):</span>
                          <span className="font-extrabold text-rr-pink">{selectedPlayer.player.ipl_shrunk_m45?.toFixed(2) || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted" title="Primary All-Runs RCAE (ΔEconomy)">All-Runs RCAE (ΔEcon):</span>
                          <span className="font-semibold text-emerald-600">{selectedPlayer.player.ipl_context_delta_econ?.toFixed(2) || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted" title="Secondary Diagnostic Legal-Ball RCAE">Legal-Ball RCAE (ΔLegal):</span>
                          <span className="font-medium text-slate-600">{selectedPlayer.player.ipl_legal_context_delta_econ?.toFixed(2) || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Wickets / Over:</span>
                          <span className="font-extrabold text-rr-charcoal">{selectedPlayer.player.ipl_wickets_per_over?.toFixed(2) || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Dot / Boundary Conc %:</span>
                          <span className="font-semibold text-rr-charcoal">{selectedPlayer.player.ipl_dot_ball_pct}% / {selectedPlayer.player.ipl_boundary_concession_pct}%</span>
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
                          {selectedPlayer.player.t20i_pressure_volume || 0} legal balls ({selectedPlayer.player.t20i_matches || 0}m)
                        </span>
                      </div>
                      <div className="text-[11px] space-y-1">
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Raw Economy (Std):</span>
                          <span className="font-bold text-rr-charcoal">{selectedPlayer.player.t20i_raw_econ?.toFixed(2) || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Shrunk Econ (M=45):</span>
                          <span className="font-extrabold text-rr-pink">{selectedPlayer.player.t20i_shrunk_m45?.toFixed(2) || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted">All-Runs RCAE (ΔEcon):</span>
                          <span className="font-semibold text-emerald-600">{typeof selectedPlayer.player.t20i_context_delta_econ === 'number' ? selectedPlayer.player.t20i_context_delta_econ.toFixed(2) : '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Legal-Ball RCAE (ΔLegal):</span>
                          <span className="font-medium text-slate-600">{typeof selectedPlayer.player.t20i_legal_context_delta_econ === 'number' ? selectedPlayer.player.t20i_legal_context_delta_econ.toFixed(2) : '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Wickets / Over:</span>
                          <span className="font-extrabold text-rr-charcoal">{selectedPlayer.player.t20i_wickets_per_over?.toFixed(2) || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rr-muted">Dot / Boundary Conc %:</span>
                          <span className="font-semibold text-rr-charcoal">{selectedPlayer.player.t20i_dot_ball_pct || '-'}% / {selectedPlayer.player.t20i_boundary_concession_pct || '-'}%</span>
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
                    <span className="text-[10px] text-rr-muted uppercase font-bold block">IPL Pressure Economy</span>
                    <span className="text-base font-extrabold text-rr-charcoal font-heading">
                      {selectedPlayer.pressure_performance?.ipl_pressure_economy_rate?.toFixed(2) || selectedPlayer.pressure_performance?.pressure_economy_rate?.toFixed(2) || selectedPlayer.player.ipl_raw_econ?.toFixed(2) || '-'}
                    </span>
                    <span className="text-[10px] text-emerald-600 block mt-0.5">
                      Δ {selectedPlayer.pressure_performance?.delta_economy ? `${selectedPlayer.pressure_performance.delta_economy > 0 ? '+' : ''}${selectedPlayer.pressure_performance.delta_economy.toFixed(2)}` : '-'} vs Normal
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border text-center">
                    <span className="text-[10px] text-rr-muted uppercase font-bold block">Accepted IPL All-Runs RCAE</span>
                    <span className="text-base font-extrabold text-emerald-600 font-heading">
                      {selectedPlayer.pressure_performance?.ipl_all_runs_rcae_delta_econ ? selectedPlayer.pressure_performance.ipl_all_runs_rcae_delta_econ.toFixed(2) : (selectedPlayer.pressure_performance?.all_runs_rcae_delta_econ ? selectedPlayer.pressure_performance.all_runs_rcae_delta_econ.toFixed(2) : selectedPlayer.player.ipl_context_delta_econ?.toFixed(2) || '-')}
                    </span>
                    <span className="text-[10px] text-rr-muted block mt-0.5">{selectedPlayer.pressure_performance?.ipl_pressure_legal_balls || 0} legal balls ({selectedPlayer.pressure_performance?.ipl_pressure_matches || 0}m)</span>
                  </div>
                  <div className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border text-center">
                    <span className="text-[10px] text-rr-muted uppercase font-bold block">Pressure Dot %</span>
                    <span className="text-base font-extrabold text-rr-charcoal font-heading">
                      {selectedPlayer.pressure_performance?.pressure_dot_pct?.toFixed(1) || selectedPlayer.player.ipl_dot_ball_pct || '-'}%
                    </span>
                    <span className="text-[10px] text-rr-muted block mt-0.5">
                      Δ {selectedPlayer.pressure_performance?.delta_dot_pct ? `${selectedPlayer.pressure_performance.delta_dot_pct.toFixed(1)}%` : '-'}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border text-center">
                    <span className="text-[10px] text-rr-muted uppercase font-bold block">Match Pass Rate</span>
                    <span className="text-base font-extrabold text-rr-pink font-heading">
                      {selectedPlayer.pressure_performance?.pressure_match_pass_rate ? `${selectedPlayer.pressure_performance.pressure_match_pass_rate}%` : `${selectedPlayer.player.ipl_match_pass_rate || 0}%`}
                    </span>
                    <span className="text-[10px] text-rr-muted block mt-0.5">Below Target Econ</span>
                  </div>
                </div>

                {/* Reconciled Cohort Separation (IPL vs Combined Cross-Format) */}
                <div className="p-3.5 rounded-xl bg-white border border-rr-border space-y-2">
                  <div className="flex items-center justify-between pb-1.5 border-b border-rr-border text-xs font-bold text-rr-charcoal">
                    <span className="flex items-center gap-1.5">
                      <Target className="w-3.5 h-3.5 text-rr-pink" />
                      Audited Cohort Reconciliation: IPL vs Combined Cross-Format RCAE
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
                          <span className="text-emerald-700">Legal Balls Bowled:</span>
                          <span className="font-extrabold">{selectedPlayer.pressure_performance?.ipl_pressure_legal_balls || selectedPlayer.player.ipl_pressure_volume || 0} balls ({selectedPlayer.pressure_performance?.ipl_pressure_matches || selectedPlayer.player.ipl_matches || 0} matches)</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-emerald-700">Observed Economy Rate:</span>
                          <span className="font-extrabold">{selectedPlayer.pressure_performance?.ipl_observed_pressure_econ?.toFixed(2) || selectedPlayer.pressure_performance?.ipl_pressure_economy_rate?.toFixed(2) || selectedPlayer.player.ipl_raw_econ?.toFixed(2) || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-emerald-700">Context Expected Econ:</span>
                          <span className="font-semibold">{selectedPlayer.pressure_performance?.ipl_expected_pressure_econ?.toFixed(2) || '-'}</span>
                        </div>
                        <div className="flex justify-between pt-1 border-t border-emerald-200/60">
                          <span className="font-bold text-emerald-950">IPL All-Runs RCAE (ΔEcon):</span>
                          <span className="font-extrabold text-emerald-700 text-sm">{selectedPlayer.pressure_performance?.ipl_all_runs_rcae_delta_econ ? selectedPlayer.pressure_performance.ipl_all_runs_rcae_delta_econ.toFixed(2) : '-'}</span>
                        </div>
                        <div className="flex justify-between text-[10px] text-emerald-800">
                          <span>Secondary Legal-Ball RCAE:</span>
                          <span className="font-semibold">{selectedPlayer.pressure_performance?.ipl_legal_rcae_delta_econ ? selectedPlayer.pressure_performance.ipl_legal_rcae_delta_econ.toFixed(2) : '-'}</span>
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
                          <span className="text-slate-500">Legal Balls Bowled:</span>
                          <span className="font-extrabold">{selectedPlayer.pressure_performance?.combined_pressure_legal_balls || selectedPlayer.player.combined_pressure_volume || 0} balls ({selectedPlayer.pressure_performance?.combined_pressure_matches || selectedPlayer.player.combined_matches || 0} matches)</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Observed Economy Rate:</span>
                          <span className="font-extrabold">{selectedPlayer.pressure_performance?.combined_observed_pressure_econ?.toFixed(2) || selectedPlayer.pressure_performance?.combined_pressure_economy_rate?.toFixed(2) || '-'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Context Expected Econ:</span>
                          <span className="font-semibold">{selectedPlayer.pressure_performance?.combined_expected_pressure_econ?.toFixed(2) || '-'}</span>
                        </div>
                        <div className="flex justify-between pt-1 border-t border-slate-200">
                          <span className="font-bold text-slate-900">Combined All-Runs RCAE (ΔEcon):</span>
                          <span className="font-extrabold text-rr-deepPink text-sm">{selectedPlayer.pressure_performance?.combined_all_runs_rcae_delta_econ ? selectedPlayer.pressure_performance.combined_all_runs_rcae_delta_econ.toFixed(2) : '-'}</span>
                        </div>
                        <div className="flex justify-between text-[10px] text-slate-600">
                          <span>Secondary Legal-Ball RCAE:</span>
                          <span className="font-semibold">{selectedPlayer.pressure_performance?.combined_legal_rcae_delta_econ ? selectedPlayer.pressure_performance.combined_legal_rcae_delta_econ.toFixed(2) : '-'}</span>
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
                            <div className="font-bold text-rr-charcoal">{ph.bowler_innings_phase}</div>
                            <div className="text-[11px] text-rr-muted">{ph.phase_pressure_balls} legal balls • {ph.phase_pressure_wickets || 0} wickets</div>
                          </div>
                          <div className="text-right">
                            <div className="font-extrabold text-rr-deepPink text-sm">{ph.phase_pressure_economy?.toFixed(2)} Econ</div>
                            <div className="text-[10px] text-rr-muted">{ph.phase_pressure_dot_pct?.toFixed(1)}% dots • {ph.phase_pressure_boundary_pct?.toFixed(1)}% bnd conc</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Tactical Matchup Subsets */}
                {selectedPlayer.pressure_performance && (
                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                      Tactical Matchup Splits & Crisis Execution
                    </h4>
                    <div className="grid grid-cols-3 gap-2 text-center text-xs">
                      <div className="p-2 bg-white rounded-lg border border-slate-200">
                        <span className="text-[10px] text-slate-500 block font-semibold">vs Top Order</span>
                        <span className="font-extrabold text-slate-800">{selectedPlayer.pressure_performance.vs_top_order_balls || 0} balls</span>
                        <span className="text-[10px] text-rr-deepPink block">{selectedPlayer.pressure_performance.vs_top_order_economy ? `${selectedPlayer.pressure_performance.vs_top_order_economy.toFixed(2)} Econ` : '-'}</span>
                      </div>
                      <div className="p-2 bg-white rounded-lg border border-slate-200">
                        <span className="text-[10px] text-slate-500 block font-semibold">Chase Crunch</span>
                        <span className="font-extrabold text-slate-800">{selectedPlayer.pressure_performance.chase_crunch_balls || 0} balls</span>
                        <span className="text-[10px] text-rr-deepPink block">{selectedPlayer.pressure_performance.chase_crunch_economy ? `${selectedPlayer.pressure_performance.chase_crunch_economy.toFixed(2)} Econ` : '-'}</span>
                      </div>
                      <div className="p-2 bg-white rounded-lg border border-slate-200">
                        <span className="text-[10px] text-slate-500 block font-semibold">Wicket Impact</span>
                        <span className="font-extrabold text-slate-800">{selectedPlayer.pressure_performance.wickets_per_over ? `${selectedPlayer.pressure_performance.wickets_per_over.toFixed(2)} / over` : '-'}</span>
                        <span className="text-[10px] text-emerald-600 block">{selectedPlayer.pressure_performance.wicket_impact_score ? `Score: ${selectedPlayer.pressure_performance.wicket_impact_score.toFixed(1)}` : '-'}</span>
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
                      <span className="text-xs font-bold text-indigo-950 block">Contextual Defensive Suppression Regressor</span>
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
                    {selectedPlayer.ml_context?.population_scope || 'Season 2026 Out-of-Time Test Partition (covers ALL 32,529 test deliveries across normal and pressure phases)'}
                  </span>
                </div>

                {/* 2026 Holdout Test Evaluation Card (Conceded Runs Primary Focus) */}
                {selectedPlayer.ml_context && (
                  <div className="p-4 rounded-xl bg-white border border-rr-border space-y-3">
                    <div className="flex items-center justify-between pb-2 border-b border-rr-border">
                      <span className="text-xs font-bold text-rr-charcoal font-heading">
                        Holdout Partition Performance (2026 Season — Defensive Conceded Runs)
                      </span>
                      <span className="text-xs text-rr-muted">
                        {selectedPlayer.ml_context.test_eval_deliveries > 0
                          ? `${selectedPlayer.ml_context.test_eval_deliveries} deliveries bowled`
                          : 'Historical sample only'}
                      </span>
                    </div>

                    {selectedPlayer.ml_context.test_eval_deliveries > 0 ? (
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-center">
                        <div className="p-2.5 bg-rr-warmWhite rounded-lg border border-rr-border">
                          <span className="text-[10px] text-rr-muted block font-semibold">Actual Runs Conceded</span>
                          <span className="text-base font-extrabold text-rr-charcoal font-heading">
                            {selectedPlayer.ml_context.actual_runs_conceded}
                          </span>
                          <span className="text-[10px] text-rr-muted block">{selectedPlayer.ml_context.actual_economy?.toFixed(2)} Econ</span>
                        </div>
                        <div className="p-2.5 bg-rr-warmWhite rounded-lg border border-rr-border">
                          <span className="text-[10px] text-rr-muted block font-semibold">Expected Runs</span>
                          <span className="text-base font-extrabold text-rr-charcoal font-heading">
                            {selectedPlayer.ml_context.expected_runs_lightgbm}
                          </span>
                          <span className="text-[10px] text-rr-muted block">{selectedPlayer.ml_context.expected_economy?.toFixed(2)} Exp Econ</span>
                        </div>
                        <div className="p-2.5 bg-emerald-50 rounded-lg border border-emerald-200">
                          <span className="text-[10px] text-emerald-800 block font-semibold">Net Residual Conceded</span>
                          <span className="text-base font-extrabold text-emerald-700 font-heading">
                            {selectedPlayer.ml_context.net_residual_runs ? (selectedPlayer.ml_context.net_residual_runs > 0 ? `+${selectedPlayer.ml_context.net_residual_runs}` : selectedPlayer.ml_context.net_residual_runs) : '-'}
                          </span>
                          <span className="text-[10px] text-emerald-800 block">runs saved / added</span>
                        </div>
                        <div className="p-2.5 bg-emerald-50 rounded-lg border border-emerald-200">
                          <span className="text-[10px] text-emerald-800 block font-semibold">Suppression / Over</span>
                          <span className="text-base font-extrabold text-emerald-700 font-heading">
                            {selectedPlayer.ml_context.suppression_per_over ? (selectedPlayer.ml_context.suppression_per_over > 0 ? `-${selectedPlayer.ml_context.suppression_per_over.toFixed(2)}` : `+${Math.abs(selectedPlayer.ml_context.suppression_per_over).toFixed(2)}`) : '-'}
                          </span>
                          <span className="text-[10px] text-emerald-800 block">runs/over saved</span>
                        </div>
                      </div>
                    ) : (
                      <div className="p-3 bg-slate-50 rounded-lg text-xs text-slate-600 border border-slate-200">
                        {selectedPlayer.ml_context.test_status}
                      </div>
                    )}
                  </div>
                )}

                {/* Dedicated Sub-Card: Experimental Delivery Wicket Classifier Diagnostics */}
                {selectedPlayer.ml_context?.experimental_wicket_classifier && (
                  <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-amber-200">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                        <span className="text-xs font-bold text-amber-950 font-heading uppercase tracking-wider">
                          Experimental Diagnostic: Delivery Wicket Classifier (LightGBM)
                        </span>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-amber-100 text-amber-900 border border-amber-300">
                        EXPERIMENTAL DIAGNOSTIC ONLY
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                      <div className="p-2 bg-white rounded-lg border border-amber-200">
                        <span className="text-[10px] text-slate-500 block">Actual Test Wkts</span>
                        <span className="text-sm font-extrabold text-slate-800">
                          {selectedPlayer.ml_context.experimental_wicket_classifier.actual_wickets}
                        </span>
                        <span className="text-[9px] text-slate-400">2026 Test Deliveries</span>
                      </div>
                      <div className="p-2 bg-white rounded-lg border border-amber-200">
                        <span className="text-[10px] text-slate-500 block">Expected Wkts</span>
                        <span className="text-sm font-extrabold text-slate-800">
                          {selectedPlayer.ml_context.experimental_wicket_classifier.expected_wickets}
                        </span>
                        <span className="text-[9px] text-slate-400">Model Expected Sum</span>
                      </div>
                      <div className="p-2 bg-white rounded-lg border border-amber-200">
                        <span className="text-[10px] text-slate-500 block">Brier Score</span>
                        <span className="text-sm font-extrabold text-slate-800">
                          {selectedPlayer.ml_context.experimental_wicket_classifier.brier_score}
                        </span>
                        <span className="text-[9px] text-slate-500">vs {selectedPlayer.ml_context.experimental_wicket_classifier.prior_brier_baseline} dummy prior</span>
                      </div>
                      <div className="p-2 bg-white rounded-lg border border-amber-200">
                        <span className="text-[10px] text-slate-500 block">PR-AUC / ROC-AUC</span>
                        <span className="text-sm font-extrabold text-slate-800">
                          {selectedPlayer.ml_context.experimental_wicket_classifier.pr_auc} / {selectedPlayer.ml_context.experimental_wicket_classifier.roc_auc}
                        </span>
                        <span className="text-[9px] text-slate-500">Base rate: {selectedPlayer.ml_context.experimental_wicket_classifier.empirical_base_rate}</span>
                      </div>
                    </div>

                    <div className="p-2.5 rounded-lg bg-white border border-amber-200 text-[11px] text-amber-950 space-y-1 leading-relaxed">
                      <div className="font-bold text-amber-900 flex items-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5 text-amber-700 flex-shrink-0" />
                        Critical Model Interpretation Advisory:
                      </div>
                      <p>
                        {selectedPlayer.ml_context.experimental_wicket_classifier.advisory}
                      </p>
                    </div>
                  </div>
                )}

                {/* Primary Cohort Benchmark RCAE */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3.5 rounded-xl bg-rr-warmWhite border border-rr-border flex items-center justify-between">
                    <div>
                      <span className="font-bold text-rr-charcoal block">Accepted Primary All-Runs RCAE (ΔEcon)</span>
                      <span className="text-[11px] text-rr-muted">Controls for all conceded runs including extras</span>
                    </div>
                    <span className="text-lg font-extrabold text-emerald-600 font-heading">
                      {selectedPlayer.pressure_performance?.ipl_all_runs_rcae_delta_econ ? selectedPlayer.pressure_performance.ipl_all_runs_rcae_delta_econ.toFixed(2) : (selectedPlayer.player.ipl_context_delta_econ?.toFixed(2) || '-')}
                    </span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-rr-warmWhite border border-rr-border flex items-center justify-between">
                    <div>
                      <span className="font-bold text-rr-charcoal block">Secondary Legal-Ball RCAE (ΔLegal)</span>
                      <span className="text-[11px] text-rr-muted">Diagnostic control strictly on legal deliveries</span>
                    </div>
                    <span className="text-lg font-extrabold text-slate-700 font-heading">
                      {selectedPlayer.pressure_performance?.ipl_legal_rcae_delta_econ ? selectedPlayer.pressure_performance.ipl_legal_rcae_delta_econ.toFixed(2) : (selectedPlayer.player.ipl_legal_context_delta_econ?.toFixed(2) || '-')}
                    </span>
                  </div>
                </div>

                {/* Critical Methodological Disclaimers */}
                <div className="space-y-2 pt-1 text-xs">
                  <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 text-blue-950 space-y-1">
                    <div className="font-bold flex items-center gap-1.5 text-blue-900">
                      <AlertCircle className="w-4 h-4 text-blue-700 flex-shrink-0" />
                      Model Scope & Defensive Benchmark Interpretation
                    </div>
                    <p className="text-[11px] leading-relaxed">
                      Contextual ML models estimate delivery-level match expectations (baseline), <strong>NOT individual intrinsic player skill</strong>. Net defensive suppression measures observed conceded runs below match context baseline.
                    </p>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-800 space-y-1">
                    <div className="font-bold flex items-center gap-1.5 text-slate-900">
                      <Scale className="w-4 h-4 text-slate-600 flex-shrink-0" />
                      Uncertainty & Limitations
                    </div>
                    <p className="text-[11px] leading-relaxed">
                      Delivery-level unexplainable variance is inherently high (LightGBM holdout test R&sup2; &asymp; 0.021 for conceded runs; Wicket PR-AUC &asymp; 0.071 vs 0.051 baseline). Pitch friction, ball condition, and exact release trajectory are unrecorded in scorecards; model functions strictly as an objective match context baseline.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: BEHAVIORAL BOUNCE-BACK */}
            {dossierTab === 'behavioral' && (
              <div className="space-y-4">
                {/* Methodological Framework Note */}
                <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200 text-xs text-amber-950 space-y-1">
                  <div className="font-bold flex items-center gap-1.5 text-amber-900">
                    <Zap className="w-4 h-4 text-amber-600" />
                    Observable Bounce-Back Dynamics
                  </div>
                  <p className="text-[11px] leading-relaxed">
                    Evaluates defensive suppression on the <strong>immediate subsequent legal delivery</strong> following a boundary conceded (four or six). Analyzes observable event sequences strictly without inferring unobservable psychological traits.
                  </p>
                </div>

                {/* Behavioral Metrics Grid */}
                {selectedPlayer.behavioral && selectedPlayer.behavioral.bowler_id ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-center text-xs">
                      <div className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border">
                        <span className="text-[10px] text-rr-muted uppercase font-bold block">Bounceback Index</span>
                        <span className="text-lg font-extrabold text-rr-pink font-heading">
                          {selectedPlayer.behavioral.bounceback_index ? `${selectedPlayer.behavioral.bounceback_index > 0 ? '+' : ''}${selectedPlayer.behavioral.bounceback_index.toFixed(2)}` : '-'}
                        </span>
                        <span className="text-[10px] text-rr-muted block">defensive economy drop</span>
                      </div>
                      <div className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border">
                        <span className="text-[10px] text-rr-muted uppercase font-bold block">Post-Boundary Economy (t+1)</span>
                        <span className="text-lg font-extrabold text-rr-charcoal font-heading">
                          {selectedPlayer.behavioral.post_boundary_economy?.toFixed(2) || '-'}
                        </span>
                        <span className="text-[10px] text-emerald-600 font-semibold block">
                          Δ {selectedPlayer.behavioral.delta_econ_post_boundary ? `${selectedPlayer.behavioral.delta_econ_post_boundary.toFixed(2)}` : '-'} Econ
                        </span>
                      </div>
                      <div className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border">
                        <span className="text-[10px] text-rr-muted uppercase font-bold block">Post-Boundary Dot %</span>
                        <span className="text-lg font-extrabold text-rr-charcoal font-heading">
                          {selectedPlayer.behavioral.post_boundary_dot_pct?.toFixed(1) || '-'}%
                        </span>
                        <span className="text-[10px] text-rr-muted block">immediate containment</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                      <div className="p-3.5 rounded-xl bg-white border border-rr-border space-y-1.5">
                        <span className="font-bold text-rr-charcoal block">Post-Cluster Containment (2+ Boundaries)</span>
                        <div className="text-[11px] space-y-1 pt-1 border-t border-rr-border">
                          <div className="flex justify-between">
                            <span className="text-rr-muted">Post-Cluster Balls Bowled:</span>
                            <span className="font-bold text-rr-charcoal">{selectedPlayer.behavioral.post_cluster_balls} legal deliveries</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-rr-muted">Post-Cluster Economy:</span>
                            <span className="font-semibold text-rr-charcoal">{selectedPlayer.behavioral.post_cluster_economy?.toFixed(2)} Econ</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-rr-muted">Post-Cluster Dot %:</span>
                            <span className="font-semibold text-rr-charcoal">{selectedPlayer.behavioral.post_cluster_dot_pct?.toFixed(1)}%</span>
                          </div>
                        </div>
                      </div>

                      <div className="p-3.5 rounded-xl bg-white border border-rr-border space-y-1.5">
                        <span className="font-bold text-rr-charcoal block">Spell Economy Progression</span>
                        <div className="text-[11px] space-y-1 pt-1 border-t border-rr-border">
                          <div className="flex justify-between">
                            <span className="text-rr-muted">Early Spell Economy (Overs 1-2):</span>
                            <span className="font-semibold text-rr-charcoal">{selectedPlayer.behavioral.early_spell_economy?.toFixed(2)} Econ</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-rr-muted">Late Spell Economy (Overs 3-4):</span>
                            <span className="font-semibold text-rr-charcoal">{selectedPlayer.behavioral.late_spell_economy?.toFixed(2)} Econ</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-rr-muted">Spell Progression Drift:</span>
                            <span className="font-semibold text-rr-charcoal">{selectedPlayer.behavioral.spell_economy_progression ? `${selectedPlayer.behavioral.spell_economy_progression > 0 ? '+' : ''}${selectedPlayer.behavioral.spell_economy_progression.toFixed(2)}` : '-'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-rr-muted">Sample Confidence:</span>
                            <span className="font-extrabold text-rr-deepPink">{selectedPlayer.behavioral.sample_confidence}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 text-center">
                    Insufficient post-boundary trigger episodes recorded to evaluate behavioral bounce-back metrics.
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
                        Empirical Bayes Economy Shrinkage Curve (M = 25 to 90)
                      </h4>
                      <span className="text-[10px] text-rr-muted">Prior Mean = 9.82 Economy</span>
                    </div>
                    <div className="h-44 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={selectedPlayer.shrinkage_curve} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#F0E7ED" />
                          <XAxis dataKey="parameter" tick={{ fill: '#77717C', fontSize: 10 }} />
                          <YAxis tick={{ fill: '#77717C', fontSize: 10 }} domain={['dataMin - 1', 'dataMax + 1']} />
                          <Tooltip
                            contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#F0E7ED', borderRadius: '8px' }}
                            formatter={(val: number) => [`${val.toFixed(2)} Econ`, 'Economy Rate']}
                          />
                          <ReferenceLine y={9.82} stroke="#A49FA9" strokeDasharray="4 4" label={{ value: 'Prior 9.82', fill: '#77717C', fontSize: 10 }} />
                          <Line type="monotone" dataKey="econ" stroke="#B90063" strokeWidth={3} dot={{ r: 4, fill: '#B90063' }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* 95% Credible Intervals */}
                {selectedPlayer.reliability && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border space-y-1">
                      <span className="text-[10px] text-rr-muted uppercase font-bold block">Pressure Economy 95% Credible Interval</span>
                      <span className="font-extrabold text-rr-charcoal text-sm font-heading">
                        {selectedPlayer.reliability.pressure_econ_ci_lower_95 && selectedPlayer.reliability.pressure_econ_ci_upper_95
                          ? `[${selectedPlayer.reliability.pressure_econ_ci_lower_95.toFixed(2)} to ${selectedPlayer.reliability.pressure_econ_ci_upper_95.toFixed(2)}] Econ`
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
