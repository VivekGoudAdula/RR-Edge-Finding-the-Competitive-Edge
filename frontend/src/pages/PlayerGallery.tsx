import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import {
  Users,
  Search,
  Filter,
  Award,
  ChevronRight,
  Shield,
  Swords,
  Layers,
  Activity,
  Calendar,
  Clock,
  Compass,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle,
  ExternalLink,
  GitCompare,
  X,
  Target,
  BarChart2,
  PieChart,
  HelpCircle,
  RefreshCw,
  ChevronDown,
  Sparkles,
} from 'lucide-react';
import {
  fetchGalleryPlayers,
  fetchGalleryPlayerProfile,
  fetchGalleryPlayerMatches,
  fetchGalleryPlayerSeasons,
} from '../services/api';
import canonicalAllGalleryPlayers from '../data/canonicalAllGalleryPlayers.json';
import {
  GalleryPlayerCard,
  GalleryPlayersResponse,
  PlayerProfileResponse,
} from '../types';
import { PageHeroCard } from '../components/common/PageHeroCard';
import { PlayerAvatar } from '../components/common/PlayerAvatar';

interface PlayerGalleryProps {
  initialPlayerId?: number;
  onNavigateToScenarios?: (scenarioId?: string, playerId?: number) => void;
  onNavigateToComparison?: (playerId?: number) => void;
}

export const PlayerGallery: React.FC<PlayerGalleryProps> = ({
  initialPlayerId,
  onNavigateToScenarios,
  onNavigateToComparison,
}) => {
  // Gallery search and filter state
  const initialPlayers = (canonicalAllGalleryPlayers as unknown as any[]).slice(0, 18);
  const [playersData, setPlayersData] = useState<GalleryPlayersResponse | null>({
    total_players: (canonicalAllGalleryPlayers as unknown as any[]).length,
    page: 1,
    page_size: 18,
    total_pages: Math.ceil((canonicalAllGalleryPlayers as unknown as any[]).length / 18),
    players: initialPlayers,
  });
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState<string>('');
  const [discipline, setDiscipline] = useState<string>('ALL');
  const [format, setFormat] = useState<string>('ALL');
  const [evidenceTier, setEvidenceTier] = useState<string>('ALL');
  const [isTop10Only, setIsTop10Only] = useState<boolean>(false);
  const [sortBy, setSortBy] = useState<string>('deliveries');
  const [ascending, setAscending] = useState<boolean>(false);
  const [page, setPage] = useState<number>(1);
  const pageSize = 18;

  // Selected player for profile modal
  const [selectedPlayerId, setSelectedPlayerId] = useState<number | null>(initialPlayerId || null);
  const [profileData, setProfileData] = useState<PlayerProfileResponse | null>(null);
  const [profileLoading, setProfileLoading] = useState<boolean>(false);
  const [activeProfileTab, setActiveProfileTab] = useState<
    'overview' | 'performance' | 'seasons' | 'phases' | 'pressure' | 'scenarios' | 'behavioral' | 'ml'
  >('overview');

  // Load players on filter change
  useEffect(() => {
    let isMounted = true;
    const loadPlayers = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchGalleryPlayers({
          discipline,
          format,
          evidenceTier,
          search: search.trim() || undefined,
          isTop10Only,
          sortBy,
          ascending,
          page,
          pageSize,
        });
        if (isMounted) {
          setPlayersData(data);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Failed to fetch player gallery');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    const timer = setTimeout(() => {
      loadPlayers();
    }, 200);

    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [discipline, format, evidenceTier, search, isTop10Only, sortBy, ascending, page]);

  // Load selected player profile
  useEffect(() => {
    if (!selectedPlayerId) {
      setProfileData(null);
      return;
    }

    let isMounted = true;
    const loadProfile = async () => {
      try {
        setProfileLoading(true);
        const data = await fetchGalleryPlayerProfile(selectedPlayerId);
        if (isMounted) {
          setProfileData(data);
        }
      } catch (err: any) {
        console.error('Failed to load profile:', err);
      } finally {
        if (isMounted) setProfileLoading(false);
      }
    };

    loadProfile();
    return () => {
      isMounted = false;
    };
  }, [selectedPlayerId]);

  // Handle external initialPlayerId changes
  useEffect(() => {
    if (initialPlayerId) {
      setSelectedPlayerId(initialPlayerId);
    }
  }, [initialPlayerId]);

  // Lock body scroll when profile modal is open
  useEffect(() => {
    if (selectedPlayerId) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [selectedPlayerId]);

  const handleCardClick = (id: number) => {
    setSelectedPlayerId(id);
    setActiveProfileTab('overview');
  };

  const getDisciplineBadge = (disc: string, role: string) => {
    const isWk = role.toLowerCase().includes('wk') || role.toLowerCase().includes('keeper');
    if (disc === 'BATTER') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
          <Swords className="w-3 h-3 mr-1" />
          {isWk ? 'WK-Batter' : 'Batter'}
        </span>
      );
    } else if (disc === 'BOWLER') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
          <Shield className="w-3 h-3 mr-1" />
          Bowler
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">
          <Layers className="w-3 h-3 mr-1" />
          All-Rounder
        </span>
      );
    }
  };

  const getEvidenceBadge = (tier: string) => {
    switch (tier) {
      case 'CONFIDENT':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle className="w-3 h-3 mr-1 text-emerald-500" /> Confident
          </span>
        );
      case 'PROVISIONAL':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
            <AlertCircle className="w-3 h-3 mr-1 text-amber-500" /> Provisional
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
            <HelpCircle className="w-3 h-3 mr-1 text-slate-400" /> Insufficient
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 pb-16">
      {/* Standardized Compact Hero Section */}
      <PageHeroCard
        badge="Intelligence Database"
        badgeIcon={<Users className="w-3.5 h-3.5 text-rr-pink" />}
        badgeContext="888 Total Eligible Players"
        title="Player Intelligence Gallery"
        description="Exhaustive index of every batter, bowler, and all-rounder across IPL and T20I competitions (2022–2026) with verified match records, contextual pressure dynamics, and scenario testing."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => {
                setIsTop10Only(!isTop10Only);
                setPage(1);
              }}
              className={`inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-bold transition-all border ${
                isTop10Only
                  ? 'bg-amber-500 text-white border-amber-600 shadow-sm'
                  : 'bg-white/10 text-white border-white/20 hover:bg-white/20'
              }`}
            >
              <Award className="w-3.5 h-3.5 mr-1 text-rr-gold" />
              {isTop10Only ? 'Showing Top 10 Only' : 'Filter Top 10'}
            </button>
            {onNavigateToScenarios && (
              <button
                onClick={() => onNavigateToScenarios()}
                className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-white/10 hover:bg-white/20 border border-white/20 transition-all"
              >
                <Target className="w-3.5 h-3.5 mr-1 text-rr-pink" />
                Scenario Lab
              </button>
            )}
          </div>
        }
      />

      {/* Filter Controls Bar */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200/80 p-4">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
          {/* Search Box */}
          <div className="relative flex-1 min-w-[240px]">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search player name, franchise, or role..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-8 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-rr-pink/40 focus:border-rr-pink text-slate-800"
            />
            {search && (
              <button
                onClick={() => {
                  setSearch('');
                  setPage(1);
                }}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Discipline Filters */}
          <div className="flex items-center bg-slate-100 p-1 rounded-lg text-xs font-semibold self-start lg:self-auto overflow-x-auto">
            {['ALL', 'BATTER', 'BOWLER', 'ALL_ROUNDER'].map((d) => (
              <button
                key={d}
                onClick={() => {
                  setDiscipline(d);
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded-md transition-all whitespace-nowrap ${
                  discipline === d
                    ? 'bg-white text-rr-navy shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {d === 'ALL'
                  ? 'All Disciplines'
                  : d === 'ALL_ROUNDER'
                  ? 'All-Rounders'
                  : d === 'BATTER'
                  ? 'Batters'
                  : 'Bowlers'}
              </button>
            ))}
          </div>

          {/* Secondary Dropdown Filters */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Format Filter */}
            <select
              value={format}
              onChange={(e) => {
                setFormat(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-rr-pink/40"
            >
              <option value="ALL">All Formats (Combined)</option>
              <option value="IPL">IPL Only</option>
              <option value="T20I">T20I Only</option>
            </select>

            {/* Evidence Tier */}
            <select
              value={evidenceTier}
              onChange={(e) => {
                setEvidenceTier(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-rr-pink/40"
            >
              <option value="ALL">All Evidence Tiers</option>
              <option value="CONFIDENT">Confident Only</option>
              <option value="PROVISIONAL">Provisional Only</option>
              <option value="INSUFFICIENT">Insufficient Only</option>
            </select>

            {/* Sort Field */}
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-rr-pink/40"
            >
              <option value="deliveries">Sort: Deliveries</option>
              <option value="matches">Sort: Matches</option>
              <option value="player_name">Sort: Player Name</option>
              <option value="primary_rate">Sort: Primary Rate</option>
            </select>

            {/* Asc / Desc Toggle */}
            <button
              onClick={() => setAscending(!ascending)}
              className="p-1.5 bg-white border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50"
              title={ascending ? 'Ascending Order' : 'Descending Order'}
            >
              {ascending ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid View */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-24 bg-white rounded-xl border border-slate-200">
          <RefreshCw className="w-8 h-8 text-rr-pink animate-spin mb-3" />
          <p className="text-sm font-semibold text-slate-700">Loading Player Gallery Index...</p>
          <p className="text-xs text-slate-500 mt-1">Filtering across 888 verified player records</p>
        </div>
      ) : error ? (
        <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-center">
          <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
          <h3 className="text-sm font-bold text-rose-800">Error Loading Gallery</h3>
          <p className="text-xs text-rose-600 mt-1">{error}</p>
        </div>
      ) : !playersData || playersData.players.length === 0 ? (
        <div className="p-12 bg-white border border-slate-200 rounded-xl text-center">
          <Users className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No Players Found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            No player records match your search criteria. Try clearing search filters or selecting 'All Disciplines'.
          </p>
          <button
            onClick={() => {
              setSearch('');
              setDiscipline('ALL');
              setFormat('ALL');
              setEvidenceTier('ALL');
              setIsTop10Only(false);
              setPage(1);
            }}
            className="mt-4 px-4 py-2 bg-rr-navy text-white text-xs font-semibold rounded-lg hover:bg-slate-800"
          >
            Reset All Filters
          </button>
        </div>
      ) : (
        <>
          {/* Summary Count Bar */}
          <div className="flex items-center justify-between text-xs text-slate-500 px-1">
            <span>
              Showing <span className="font-bold text-rr-navy">{playersData.players.length}</span> of{' '}
              <span className="font-bold text-rr-navy">{playersData.total_players}</span> eligible players
              {discipline !== 'ALL' && ` (${discipline})`}
            </span>
            <span>
              Page <span className="font-bold text-rr-navy">{playersData.page}</span> of{' '}
              <span className="font-bold text-rr-navy">{playersData.total_pages}</span>
            </span>
          </div>

          {/* Player Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 gap-5">
            {playersData.players.map((p) => {
              // Initials
              const initials = p.player_name
                .split(' ')
                .map((n) => n[0])
                .join('')
                .substring(0, 2)
                .toUpperCase();

              return (
                <div
                  key={p.player_id}
                  onClick={() => handleCardClick(p.player_id)}
                  className="group bg-white rounded-xl border border-slate-200 hover:border-rr-pink/60 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between overflow-hidden"
                >
                  {/* Card Header */}
                  <div className="p-4 border-b border-slate-100">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center space-x-3">
                        <PlayerAvatar
                          playerId={p.player_id}
                          playerName={p.player_name}
                          size="sm"
                          isTop10={p.is_top_10}
                          className="group-hover:scale-105 transition-transform"
                        />
                        <div>
                          <div className="flex items-center space-x-1.5">
                            <h3 className="text-sm font-bold text-rr-navy group-hover:text-rr-pink transition-colors">
                              {p.player_name}
                            </h3>
                            {p.is_top_10 && (
                              <span className="inline-flex items-center px-1.5 py-0.2 rounded text-[10px] font-extrabold bg-amber-100 text-amber-800 border border-amber-300">
                                #{p.top_10_rank}
                              </span>
                            )}
                          </div>
                          <div className="flex flex-wrap items-center gap-1.5 mt-1">
                            {getDisciplineBadge(p.discipline, p.role)}
                            {getEvidenceBadge(p.evidence_tier)}
                            {(p as any).has_dual_records && (
                              <span
                                className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200"
                                title={(p as any).dual_records_detail}
                              >
                                Bat & Bowl
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="text-right">
                        <span className="text-[11px] font-bold text-rr-navy">
                          {p.primary_rate.toFixed(2)}
                        </span>
                        <div className="text-[9px] uppercase tracking-wider text-slate-400">
                          {p.rate_label}
                        </div>
                      </div>
                    </div>

                    {/* Verified Teams */}
                    <div className="mt-3 flex flex-wrap gap-1">
                      {p.verified_teams && p.verified_teams.length > 0 ? (
                        p.verified_teams.slice(0, 3).map((team, idx) => (
                          <span
                            key={idx}
                            className="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700"
                          >
                            {team}
                          </span>
                        ))
                      ) : (
                        <span className="text-[10px] text-slate-400 italic">No franchise mapped</span>
                      )}
                      {p.verified_teams && p.verified_teams.length > 3 && (
                        <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-50 text-slate-500">
                          +{p.verified_teams.length - 3}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Card Metrics Grid */}
                  <div className="p-4 grid grid-cols-3 gap-2 bg-slate-50/50 text-center border-b border-slate-100">
                    <div>
                      <div className="text-xs font-bold text-slate-800">{p.matches}</div>
                      <div className="text-[10px] text-slate-500">Matches</div>
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-800">{p.deliveries.toLocaleString()}</div>
                      <div className="text-[10px] text-slate-500">Deliveries</div>
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-800">
                        {p.formats.join(' / ') || 'T20'}
                      </div>
                      <div className="text-[10px] text-slate-500">Formats</div>
                    </div>
                  </div>

                  {/* Card Footer Actions */}
                  <div className="px-4 py-2.5 bg-white flex items-center justify-between text-xs">
                    <span className="text-[11px] font-medium text-slate-500 flex items-center">
                      <Activity className="w-3 h-3 mr-1 text-slate-400" />
                      {p.pressure_indicator || 'Standard'}
                    </span>
                    <span className="inline-flex items-center text-rr-pink font-semibold group-hover:translate-x-0.5 transition-transform">
                      View Profile <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Pagination Controls */}
          <div className="flex items-center justify-between pt-6 border-t border-slate-200">
            <button
              onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
              disabled={page <= 1}
              className="px-3.5 py-2 text-xs font-bold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <div className="flex items-center space-x-1">
              {Array.from({ length: Math.min(5, playersData.total_pages) }, (_, i) => {
                let pNum = i + 1;
                if (playersData.total_pages > 5 && page > 3) {
                  pNum = page - 2 + i;
                  if (pNum > playersData.total_pages) pNum = playersData.total_pages - (4 - i);
                }
                return (
                  <button
                    key={pNum}
                    onClick={() => setPage(pNum)}
                    className={`w-8 h-8 rounded-lg text-xs font-bold transition-all ${
                      page === pNum
                        ? 'bg-rr-navy text-white shadow-xs'
                        : 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    {pNum}
                  </button>
                );
              })}
            </div>
            <button
              onClick={() => setPage((prev) => Math.min(prev + 1, playersData.total_pages))}
              disabled={page >= playersData.total_pages}
              className="px-3.5 py-2 text-xs font-bold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </>
      )}

      {/* Complete 12-Section Player Profile Modal */}
      {selectedPlayerId &&
        createPortal(
          <div
            className="fixed inset-0 z-[100] overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-6 animate-in fade-in duration-200"
            onClick={(e) => {
              if (e.target === e.currentTarget) setSelectedPlayerId(null);
            }}
          >
            <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-5xl w-full max-h-[92vh] flex flex-col overflow-hidden">
            {profileLoading || !profileData ? (
              <div className="p-16 text-center">
                <RefreshCw className="w-8 h-8 text-rr-pink animate-spin mx-auto mb-3" />
                <p className="text-sm font-semibold text-slate-700">Loading Unified Player Dossier...</p>
                <p className="text-xs text-slate-500 mt-1">
                  Synthesizing match logs, ML residuals, Bayesian shrinkage, and scenario evaluations
                </p>
              </div>
            ) : (
              <>
                {/* Modal Header */}
                <div
                  style={{ background: '#0B192C', backgroundColor: '#0B192C', color: '#FFFFFF' }}
                  className="px-6 py-5 bg-rr-navy text-white flex items-start justify-between border-b border-slate-700"
                >
                  <div className="flex items-center space-x-4">
                    <PlayerAvatar
                      playerId={profileData.card.player_id}
                      playerName={profileData.card.player_name}
                      size="lg"
                      isTop10={profileData.card.is_top_10}
                      className="ring-2 ring-rr-pink"
                    />
                    <div>
                      <div className="flex items-center space-x-2">
                        <h2 className="text-2xl font-black tracking-tight text-white" style={{ color: '#FFFFFF' }}>
                          {profileData.card.player_name}
                        </h2>
                        {profileData.card.is_top_10 && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-extrabold bg-amber-400 text-slate-900 shadow-xs">
                            Top 10 Final Selection #{profileData.card.top_10_rank}
                          </span>
                        )}
                      </div>
                      <div className="flex flex-wrap items-center gap-2 mt-1.5 text-xs text-slate-300">
                        <span className="font-semibold text-white">{profileData.sections.career_overview.role}</span>
                        <span className="text-slate-500">•</span>
                        <span className="font-semibold text-slate-200">{profileData.card.discipline}</span>
                        <span className="text-slate-500">•</span>
                        <span className="text-slate-300">{profileData.card.formats.join(', ')}</span>
                        <span className="text-slate-500">•</span>
                        <span className="text-slate-300">
                          {profileData.sections.career_overview.verified_teams.join(', ') ||
                            'Unattached'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {onNavigateToScenarios && (
                      <button
                        onClick={() => {
                          setSelectedPlayerId(null);
                          onNavigateToScenarios(undefined, profileData.player_id);
                        }}
                        className="px-3 py-1.5 bg-rr-pink text-white text-xs font-bold rounded-lg hover:bg-pink-600 transition-colors flex items-center"
                      >
                        <Target className="w-3.5 h-3.5 mr-1.5" />
                        Test in Scenario Lab
                      </button>
                    )}
                    {onNavigateToComparison && (
                      <button
                        onClick={() => {
                          setSelectedPlayerId(null);
                          onNavigateToComparison(profileData.player_id);
                        }}
                        className="px-3 py-1.5 bg-slate-800 text-slate-200 text-xs font-bold rounded-lg hover:bg-slate-700 border border-slate-700 transition-colors flex items-center"
                      >
                        <GitCompare className="w-3.5 h-3.5 mr-1.5" />
                        Compare
                      </button>
                    )}
                    <button
                      onClick={() => setSelectedPlayerId(null)}
                      className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                {/* Profile Navigation Tabs */}
                <div className="px-6 bg-slate-50 border-b border-slate-200 flex space-x-1 overflow-x-auto text-xs font-semibold">
                  {[
                    { id: 'overview', label: '1. Career Overview' },
                    { id: 'performance', label: '2-3. IPL & T20I Formats' },
                    { id: 'seasons', label: '4-5. Seasons & Match Logs' },
                    { id: 'phases', label: '6. Innings Phases' },
                    { id: 'pressure', label: '7. Pressure Intelligence' },
                    { id: 'scenarios', label: '8. Scenario Lab Results' },
                    { id: 'behavioral', label: '9. Behavioral Dynamics' },
                    { id: 'ml', label: '10-12. ML & Statistical Evidence' },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveProfileTab(tab.id as any)}
                      className={`px-3.5 py-3 border-b-2 whitespace-nowrap transition-colors ${
                        activeProfileTab === tab.id
                          ? 'border-rr-pink text-rr-pink font-bold'
                          : 'border-transparent text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                {/* Tab Content Body */}
                <div className="p-6 overflow-y-auto max-h-[calc(92vh-175px)] space-y-6">
                  {/* TAB 1: Career Overview */}
                  {activeProfileTab === 'overview' && (
                    <div className="space-y-6">
                      <div className="bg-slate-50 rounded-xl p-5 border border-slate-200">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center">
                          <CheckCircle className="w-3.5 h-3.5 mr-1.5 text-emerald-500" />
                          Strictly Verified Metadata (Zero Biographical Speculation)
                        </h4>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                          <div>
                            <span className="text-slate-500 block">Verified Player ID</span>
                            <span className="font-bold text-slate-800">
                              {profileData.sections.career_overview.player_id}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Tactical Discipline</span>
                            <span className="font-bold text-slate-800">
                              {profileData.sections.career_overview.discipline}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Career Matches</span>
                            <span className="font-bold text-slate-800">
                              {profileData.sections.career_overview.career_matches}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Career Deliveries</span>
                            <span className="font-bold text-slate-800">
                              {profileData.sections.career_overview.career_deliveries.toLocaleString()}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Age / Birth Date</span>
                            <span className="font-medium text-slate-600 italic">
                              {profileData.sections.career_overview.age} (Unverified in raw ball-by-ball)
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Nationality</span>
                            <span className="font-medium text-slate-600 italic">
                              {profileData.sections.career_overview.nationality}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Batting Style</span>
                            <span className="font-medium text-slate-600 italic">
                              {profileData.sections.career_overview.batting_style}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Bowling Style</span>
                            <span className="font-medium text-slate-600 italic">
                              {profileData.sections.career_overview.bowling_style}
                            </span>
                          </div>
                        </div>
                        <div className="mt-4 pt-3 border-t border-slate-200 text-xs text-slate-500">
                          <span className="font-semibold text-slate-700">Verified Teams:</span>{' '}
                          {profileData.sections.career_overview.verified_teams.join(', ') ||
                            'No franchise mapping detected'}
                        </div>
                      </div>

                      {/* Summary Metrics */}
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                          <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold">
                            Primary Performance Rate
                          </div>
                          <div className="text-2xl font-black text-rr-navy mt-1">
                            {profileData.card.primary_rate.toFixed(2)}
                          </div>
                          <div className="text-xs text-slate-500 mt-0.5">
                            {profileData.card.rate_label} across all format deliveries
                          </div>
                        </div>
                        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                          <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold">
                            Evidence & Reliability
                          </div>
                          <div className="text-xl font-bold text-slate-800 mt-1 flex items-center">
                            {getEvidenceBadge(profileData.card.evidence_tier)}
                          </div>
                          <div className="text-xs text-slate-500 mt-1">
                            Shrinkage Prior: M = {profileData.sections.reliability_evidence.shrinkage_m_factor} deliveries
                          </div>
                        </div>
                        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                          <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold">
                            Pressure Profile
                          </div>
                          <div className="text-xl font-bold text-rr-pink mt-1">
                            {profileData.card.pressure_indicator || 'Standard Exposure'}
                          </div>
                          <div className="text-xs text-slate-500 mt-0.5">
                            Evaluated in par-deficit & clutch situations
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* TAB 2: Format Comparisons */}
                  {activeProfileTab === 'performance' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* IPL Format Card */}
                      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                        <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                          <div className="flex items-center space-x-2">
                            <span className="w-3 h-3 rounded-full bg-blue-600" />
                            <h4 className="font-bold text-sm text-slate-800">IPL Performance</h4>
                          </div>
                          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700">
                            Domestic Franchise
                          </span>
                        </div>
                        {profileData.sections.ipl_performance.has_data ? (
                          <div className="mt-4 space-y-4">
                            {profileData.sections.ipl_performance.batting && (
                              <div>
                                <h5 className="text-xs font-bold text-slate-600 mb-2">Batting Record</h5>
                                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                                  <div className="bg-slate-50 p-2 rounded">
                                    <div className="font-bold text-slate-800">
                                      {profileData.sections.ipl_performance.batting.runs ?? '-'}
                                    </div>
                                    <div className="text-[10px] text-slate-500">Runs</div>
                                  </div>
                                  <div className="bg-slate-50 p-2 rounded">
                                    <div className="font-bold text-slate-800">
                                      {profileData.sections.ipl_performance.batting.balls ?? '-'}
                                    </div>
                                    <div className="text-[10px] text-slate-500">Balls</div>
                                  </div>
                                  <div className="bg-slate-50 p-2 rounded">
                                    <div className="font-bold text-rr-pink">
                                      {profileData.sections.ipl_performance.batting.strike_rate
                                        ? profileData.sections.ipl_performance.batting.strike_rate.toFixed(1)
                                        : '-'}
                                    </div>
                                    <div className="text-[10px] text-slate-500">Strike Rate</div>
                                  </div>
                                </div>
                              </div>
                            )}

                            {profileData.sections.ipl_performance.bowling && (
                              <div>
                                <h5 className="text-xs font-bold text-slate-600 mb-2">Bowling Record</h5>
                                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                                  <div className="bg-slate-50 p-2 rounded">
                                    <div className="font-bold text-slate-800">
                                      {profileData.sections.ipl_performance.bowling.wickets ?? '-'}
                                    </div>
                                    <div className="text-[10px] text-slate-500">Wickets</div>
                                  </div>
                                  <div className="bg-slate-50 p-2 rounded">
                                    <div className="font-bold text-slate-800">
                                      {profileData.sections.ipl_performance.bowling.balls ?? '-'}
                                    </div>
                                    <div className="text-[10px] text-slate-500">Balls</div>
                                  </div>
                                  <div className="bg-slate-50 p-2 rounded">
                                    <div className="font-bold text-blue-600">
                                      {profileData.sections.ipl_performance.bowling.economy
                                        ? profileData.sections.ipl_performance.bowling.economy.toFixed(2)
                                        : '-'}
                                    </div>
                                    <div className="text-[10px] text-slate-500">Economy</div>
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="py-8 text-center text-xs text-slate-400 italic">
                            No IPL match appearances recorded in 2022–2026 dataset
                          </div>
                        )}
                      </div>

                      {/* T20I Format Card */}
                      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                        <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                          <div className="flex items-center space-x-2">
                            <span className="w-3 h-3 rounded-full bg-emerald-600" />
                            <h4 className="font-bold text-sm text-slate-800">T20I Performance</h4>
                          </div>
                          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700">
                            International Senior
                          </span>
                        </div>
                        {profileData.sections.t20i_performance.has_data ? (
                          <div className="mt-4 space-y-4">
                            {profileData.sections.t20i_performance.batting && (
                              <div>
                                <h5 className="text-xs font-bold text-slate-600 mb-2">Batting Record</h5>
                                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                                  <div className="bg-slate-50 p-2 rounded">
                                    <div className="font-bold text-slate-800">
                                      {profileData.sections.t20i_performance.batting.runs ?? '-'}
                                    </div>
                                    <div className="text-[10px] text-slate-500">Runs</div>
                                  </div>
                                  <div className="bg-slate-50 p-2 rounded">
                                    <div className="font-bold text-slate-800">
                                      {profileData.sections.t20i_performance.batting.balls ?? '-'}
                                    </div>
                                    <div className="text-[10px] text-slate-500">Balls</div>
                                  </div>
                                  <div className="bg-slate-50 p-2 rounded">
                                    <div className="font-bold text-rr-pink">
                                      {profileData.sections.t20i_performance.batting.strike_rate
                                        ? profileData.sections.t20i_performance.batting.strike_rate.toFixed(1)
                                        : '-'}
                                    </div>
                                    <div className="text-[10px] text-slate-500">Strike Rate</div>
                                  </div>
                                </div>
                              </div>
                            )}

                            {profileData.sections.t20i_performance.bowling && (
                              <div>
                                <h5 className="text-xs font-bold text-slate-600 mb-2">Bowling Record</h5>
                                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                                  <div className="bg-slate-50 p-2 rounded">
                                    <div className="font-bold text-slate-800">
                                      {profileData.sections.t20i_performance.bowling.wickets ?? '-'}
                                    </div>
                                    <div className="text-[10px] text-slate-500">Wickets</div>
                                  </div>
                                  <div className="bg-slate-50 p-2 rounded">
                                    <div className="font-bold text-slate-800">
                                      {profileData.sections.t20i_performance.bowling.balls ?? '-'}
                                    </div>
                                    <div className="text-[10px] text-slate-500">Balls</div>
                                  </div>
                                  <div className="bg-slate-50 p-2 rounded">
                                    <div className="font-bold text-blue-600">
                                      {profileData.sections.t20i_performance.bowling.economy
                                        ? profileData.sections.t20i_performance.bowling.economy.toFixed(2)
                                        : '-'}
                                    </div>
                                    <div className="text-[10px] text-slate-500">Economy</div>
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="py-8 text-center text-xs text-slate-400 italic">
                            No T20I appearances recorded in 2022–2026 dataset
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* TAB 3: Seasons & Match Logs */}
                  {activeProfileTab === 'seasons' && (
                    <div className="space-y-6">
                      {/* Season Progression */}
                      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
                        <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-200">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                            Season-by-Season Progression (2022–2026)
                          </h4>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full text-xs text-left">
                            <thead className="bg-slate-100 text-slate-600 uppercase font-semibold">
                              <tr>
                                <th className="px-4 py-2.5">Season</th>
                                <th className="px-4 py-2.5">Matches</th>
                                <th className="px-4 py-2.5">Bat Balls</th>
                                <th className="px-4 py-2.5">Bat Runs</th>
                                <th className="px-4 py-2.5">Bat SR</th>
                                <th className="px-4 py-2.5">Bowl Balls</th>
                                <th className="px-4 py-2.5">Bowl Wkts</th>
                                <th className="px-4 py-2.5">Bowl Econ</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                              {profileData.sections.season_history &&
                              profileData.sections.season_history.length > 0 ? (
                                profileData.sections.season_history.map((s, idx) => (
                                  <tr key={idx} className="hover:bg-slate-50">
                                    <td className="px-4 py-2.5 font-bold text-rr-navy">{s.season}</td>
                                    <td className="px-4 py-2.5 font-medium">{s.matches}</td>
                                    <td className="px-4 py-2.5">{s.batting_balls || '-'}</td>
                                    <td className="px-4 py-2.5">{s.batting_runs || '-'}</td>
                                    <td className="px-4 py-2.5 font-bold text-rr-pink">
                                      {s.batting_strike_rate ? s.batting_strike_rate.toFixed(1) : '-'}
                                    </td>
                                    <td className="px-4 py-2.5">{s.bowling_balls || '-'}</td>
                                    <td className="px-4 py-2.5">{s.bowling_wickets || '-'}</td>
                                    <td className="px-4 py-2.5 font-bold text-blue-600">
                                      {s.bowling_economy ? s.bowling_economy.toFixed(2) : '-'}
                                    </td>
                                  </tr>
                                ))
                              ) : (
                                <tr>
                                  <td colSpan={8} className="px-4 py-4 text-center text-slate-400 italic">
                                    No season breakdown available
                                  </td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      {/* Recent Match Logs */}
                      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
                        <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-200">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                            Recent Match Logs (Last 10 Matches)
                          </h4>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full text-xs text-left">
                            <thead className="bg-slate-100 text-slate-600 uppercase font-semibold">
                              <tr>
                                <th className="px-4 py-2.5">Date</th>
                                <th className="px-4 py-2.5">Comp</th>
                                <th className="px-4 py-2.5">Opponent</th>
                                <th className="px-4 py-2.5">Batting</th>
                                <th className="px-4 py-2.5">Bowling</th>
                                <th className="px-4 py-2.5">Result</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                              {profileData.sections.match_history &&
                              profileData.sections.match_history.length > 0 ? (
                                profileData.sections.match_history.map((m, idx) => (
                                  <tr key={idx} className="hover:bg-slate-50">
                                    <td className="px-4 py-2.5 font-medium text-slate-700 whitespace-nowrap">
                                      {m.match_date}
                                    </td>
                                    <td className="px-4 py-2.5 font-semibold text-slate-600">
                                      {m.competition}
                                    </td>
                                    <td className="px-4 py-2.5 text-slate-800">
                                      vs {m.away_team}
                                    </td>
                                    <td className="px-4 py-2.5">
                                      {m.batting_balls !== null && m.batting_balls > 0 ? (
                                        <span className="font-semibold text-slate-800">
                                          {m.batting_runs} ({m.batting_balls}b) - SR:{' '}
                                          {m.batting_strike_rate?.toFixed(1)}
                                        </span>
                                      ) : (
                                        <span className="text-slate-400">DNB</span>
                                      )}
                                    </td>
                                    <td className="px-4 py-2.5">
                                      {m.bowling_balls !== null && m.bowling_balls > 0 ? (
                                        <span className="font-semibold text-slate-800">
                                          {m.bowling_wickets}/{m.bowling_runs} ({m.bowling_balls}b)
                                        </span>
                                      ) : (
                                        <span className="text-slate-400">DNB</span>
                                      )}
                                    </td>
                                    <td className="px-4 py-2.5 font-semibold text-slate-600">
                                      {m.match_result}
                                    </td>
                                  </tr>
                                ))
                              ) : (
                                <tr>
                                  <td colSpan={6} className="px-4 py-4 text-center text-slate-400 italic">
                                    No recent match logs available
                                  </td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* TAB 4: Innings Phases */}
                  {activeProfileTab === 'phases' && (
                    <div className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {['Powerplay', 'Middle', 'Death'].map((phaseName) => {
                          const batPhase =
                            profileData.sections.phase_statistics.batting_phases?.[phaseName];
                          const bowlPhase =
                            profileData.sections.phase_statistics.bowling_phases?.[phaseName];

                          return (
                            <div
                              key={phaseName}
                              className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs"
                            >
                              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                                <h4 className="font-bold text-sm text-rr-navy">{phaseName} Phase</h4>
                                <span className="text-[10px] font-bold uppercase text-slate-400">
                                  {phaseName === 'Powerplay'
                                    ? 'Overs 1-6'
                                    : phaseName === 'Middle'
                                    ? 'Overs 7-15'
                                    : 'Overs 16-20'}
                                </span>
                              </div>

                              <div className="mt-4 space-y-3">
                                {batPhase ? (
                                  <div>
                                    <div className="text-[11px] font-bold text-slate-500 uppercase">
                                      Batting
                                    </div>
                                    <div className="flex items-center justify-between mt-1 text-xs">
                                      <span className="text-slate-600">Balls: {batPhase.balls || 0}</span>
                                      <span className="font-bold text-rr-pink">
                                        SR: {batPhase.strike_rate ? batPhase.strike_rate.toFixed(1) : '-'}
                                      </span>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="text-[11px] text-slate-400 italic">No batting balls</div>
                                )}

                                {bowlPhase ? (
                                  <div className="pt-2 border-t border-slate-100">
                                    <div className="text-[11px] font-bold text-slate-500 uppercase">
                                      Bowling
                                    </div>
                                    <div className="flex items-center justify-between mt-1 text-xs">
                                      <span className="text-slate-600">Balls: {bowlPhase.balls || 0}</span>
                                      <span className="font-bold text-blue-600">
                                        Econ: {bowlPhase.economy ? bowlPhase.economy.toFixed(2) : '-'}
                                      </span>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="text-[11px] text-slate-400 italic">No bowling balls</div>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* TAB 5: Pressure Intelligence */}
                  {activeProfileTab === 'pressure' && (
                    <div className="space-y-6">
                      <div className="bg-slate-50 p-5 rounded-xl border border-slate-200">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                          Pressure Cohort Exposure & Context Shifts
                        </h4>
                        <p className="text-xs text-slate-600">
                          Deliveries categorized by pre-delivery required run rate, par score deficit, and wicket leverage.
                        </p>

                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 text-center">
                          <div className="bg-white p-3 rounded-lg border border-slate-200">
                            <div className="text-xs text-slate-500">Batting Pressure Balls</div>
                            <div className="text-lg font-bold text-rr-navy mt-1">
                              {profileData.sections.pressure_intelligence.batting_pressure_balls}
                            </div>
                          </div>
                          <div className="bg-white p-3 rounded-lg border border-slate-200">
                            <div className="text-xs text-slate-500">Bowling Pressure Balls</div>
                            <div className="text-lg font-bold text-rr-navy mt-1">
                              {profileData.sections.pressure_intelligence.bowling_pressure_balls}
                            </div>
                          </div>
                          <div className="bg-white p-3 rounded-lg border border-slate-200">
                            <div className="text-xs text-slate-500">Pressure Classification</div>
                            <div className="text-xs font-bold text-rr-pink mt-2">
                              {profileData.card.pressure_indicator || 'Standard'}
                            </div>
                          </div>
                          <div className="bg-white p-3 rounded-lg border border-slate-200">
                            <div className="text-xs text-slate-500">Evidence Level</div>
                            <div className="text-xs font-bold text-slate-800 mt-2">
                              {profileData.card.evidence_tier}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* TAB 6: Scenario Lab Results */}
                  {activeProfileTab === 'scenarios' && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-bold text-rr-navy">
                            Standard Scenario Performance Evaluations
                          </h4>
                          <p className="text-xs text-slate-500">
                            Evaluated across 8 canonical tactical scenarios. Rates report un-shrunk observed sample means; intervals reflect match-cluster bootstrap resampling.
                          </p>
                        </div>
                        {onNavigateToScenarios && (
                          <button
                            onClick={() => {
                              setSelectedPlayerId(null);
                              onNavigateToScenarios(undefined, profileData.player_id);
                            }}
                            className="px-3 py-1.5 bg-rr-warm hover:bg-slate-200 text-rr-navy text-xs font-bold rounded-lg border border-slate-300 transition-colors flex items-center"
                          >
                            <ExternalLink className="w-3.5 h-3.5 mr-1" />
                            Open Full Lab
                          </button>
                        )}
                      </div>

                      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
                        <table className="w-full text-xs text-left">
                          <thead className="bg-slate-100 text-slate-600 uppercase font-semibold">
                            <tr>
                              <th className="px-4 py-2.5">Scenario</th>
                              <th className="px-4 py-2.5">Category</th>
                              <th className="px-4 py-2.5">Balls</th>
                              <th className="px-4 py-2.5">Observed Rate (Unshrunk)</th>
                              <th className="px-4 py-2.5">Cohort Benchmark</th>
                              <th className="px-4 py-2.5">Innings Win % (95% CI)</th>
                              <th className="px-4 py-2.5">Action</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {profileData.sections.scenario_lab_results &&
                            profileData.sections.scenario_lab_results.length > 0 ? (
                              profileData.sections.scenario_lab_results.map((res, idx) => (
                                <tr key={idx} className="hover:bg-slate-50">
                                  <td className="px-4 py-2.5 font-bold text-rr-navy">
                                    {res.scenario_name}
                                  </td>
                                  <td className="px-4 py-2.5">
                                    <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700">
                                      {res.category}
                                    </span>
                                  </td>
                                  <td className="px-4 py-2.5 font-medium">{res.deliveries}</td>
                                  <td className="px-4 py-2.5 font-bold text-rr-pink">
                                    {res.primary_rate !== null ? res.primary_rate.toFixed(2) : '-'}
                                  </td>
                                  <td className="px-4 py-2.5 text-slate-600">
                                    {res.cohort_benchmark_rate.toFixed(2)}
                                  </td>
                                  <td className="px-4 py-2.5">
                                    {res.success_rate !== null ? (
                                      <div>
                                        <span className="font-bold text-emerald-700">
                                          {res.success_rate.toFixed(1)}%
                                        </span>
                                        <span className="text-[10px] text-slate-400 block">
                                          [{res.confidence_interval[0].toFixed(1)}% -{' '}
                                          {res.confidence_interval[1].toFixed(1)}%]
                                        </span>
                                      </div>
                                    ) : (
                                      <span className="text-slate-400 italic">No completed matches</span>
                                    )}
                                  </td>
                                  <td className="px-4 py-2.5">
                                    {onNavigateToScenarios && (
                                      <button
                                        onClick={() => {
                                          setSelectedPlayerId(null);
                                          onNavigateToScenarios(res.scenario_id, profileData.player_id);
                                        }}
                                        className="text-rr-pink hover:text-pink-700 font-bold underline"
                                      >
                                        Simulate
                                      </button>
                                    )}
                                  </td>
                                </tr>
                              ))
                            ) : (
                              <tr>
                                <td colSpan={7} className="px-4 py-4 text-center text-slate-400 italic">
                                  No scenario records available for this player
                                </td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* TAB 7: Behavioral Dynamics */}
                  {activeProfileTab === 'behavioral' && (
                    <div className="space-y-4">
                      <div className="bg-slate-50 p-5 rounded-xl border border-slate-200">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                          Behavioral Response & Post-Shock Recovery
                        </h4>
                        <p className="text-xs text-slate-600">
                          Measures immediate recovery rates at t+1 and post-shock resilience following adverse events (dot-ball droughts or boundary concessions).
                        </p>

                        <div className="mt-4 p-4 bg-white rounded-lg border border-slate-200">
                          {profileData.sections.behavioral_intelligence ? (
                            <div className="text-xs space-y-2">
                              <pre className="text-xs text-slate-700 overflow-x-auto p-2 bg-slate-50 rounded">
                                {JSON.stringify(profileData.sections.behavioral_intelligence, null, 2)}
                              </pre>
                            </div>
                          ) : (
                            <div className="text-xs text-slate-400 italic text-center py-4">
                              Insufficient behavioral trigger episodes in holdout test cohort
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* TAB 8: ML & Statistical Evidence */}
                  {activeProfileTab === 'ml' && (
                    <div className="space-y-6">
                      {/* Supervised ML Context */}
                      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                        <div className="flex items-center space-x-2 mb-3">
                          <Sparkles className="w-4 h-4 text-rr-pink" />
                          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                            Supervised Machine Learning Context (LightGBM Expected Runs)
                          </h4>
                        </div>
                        <p className="text-xs text-slate-600 mb-4">
                          Out-of-sample delivery evaluation against LightGBM expected outcome models, controlling for pitch, par score deficit, over, and field restrictions.
                        </p>

                        {profileData.sections.ml_context ? (
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center text-xs">
                            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                              <div className="text-slate-500">Test Deliveries</div>
                              <div className="text-lg font-bold text-slate-800 mt-1">
                                {profileData.sections.ml_context.test_deliveries || 0}
                              </div>
                            </div>
                            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                              <div className="text-slate-500">Actual Runs</div>
                              <div className="text-lg font-bold text-slate-800 mt-1">
                                {profileData.sections.ml_context.actual_runs || 0}
                              </div>
                            </div>
                            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                              <div className="text-slate-500">Expected Runs (ML)</div>
                              <div className="text-lg font-bold text-blue-600 mt-1">
                                {profileData.sections.ml_context.expected_runs
                                  ? profileData.sections.ml_context.expected_runs.toFixed(1)
                                  : '-'}
                              </div>
                            </div>
                            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                              <div className="text-slate-500">Net Residual</div>
                              <div className="text-lg font-bold text-rr-pink mt-1">
                                {profileData.sections.ml_context.net_residual !== undefined
                                  ? (profileData.sections.ml_context.net_residual > 0 ? '+' : '') +
                                    profileData.sections.ml_context.net_residual.toFixed(2)
                                  : '-'}
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="text-xs text-slate-400 italic py-4 text-center">
                            No 2026 test partition deliveries for this player
                          </div>
                        )}
                      </div>

                      {/* Reliability Evidence */}
                      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                          Statistical Reliability & Bayesian Shrinkage
                        </h4>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center text-xs mt-3">
                          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                            <div className="text-slate-500">Sample Deliveries</div>
                            <div className="text-base font-bold text-slate-800 mt-1">
                              {profileData.sections.reliability_evidence.sample_deliveries}
                            </div>
                          </div>
                          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                            <div className="text-slate-500">Sample Matches</div>
                            <div className="text-base font-bold text-slate-800 mt-1">
                              {profileData.sections.reliability_evidence.sample_matches}
                            </div>
                          </div>
                          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                            <div className="text-slate-500">Shrinkage Prior M</div>
                            <div className="text-base font-bold text-slate-800 mt-1">
                              {profileData.sections.reliability_evidence.shrinkage_m_factor} balls
                            </div>
                          </div>
                          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                            <div className="text-slate-500">Sample Adequacy</div>
                            <div className="text-xs font-bold text-emerald-700 mt-1 truncate" title={profileData.sections.reliability_evidence.sample_adequacy}>
                              {profileData.sections.reliability_evidence.sample_adequacy}
                            </div>
                          </div>
                        </div>

                        {/* Explicit Methodology & Shrinkage Scope Disclosure */}
                        <div className="mt-4 p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                          <div className="font-semibold text-slate-800">
                            {(profileData.sections.reliability_evidence as any).uncertainty_status}
                          </div>
                          <div className="text-[11px] text-slate-500 leading-relaxed">
                            {(profileData.sections.reliability_evidence as any).shrinkage_scope ||
                              'Validated strictly for overall competition pressure Strike Rate and Economy rate via empirical Bayes ANOVA. Scenario evaluations report un-shrunk observed sample means with match-cluster bootstrap intervals.'}
                          </div>
                        </div>
                      </div>

                      {/* Comparison Launcher */}
                      <div className="bg-slate-50 p-5 rounded-xl border border-slate-200">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                              Direct Comparison Launcher
                            </h4>
                            <p className="text-xs text-slate-500 mt-0.5">
                              Compare against top-rated cohort peers or franchise targets
                            </p>
                          </div>
                          {onNavigateToComparison && (
                            <button
                              onClick={() => {
                                setSelectedPlayerId(null);
                                onNavigateToComparison(profileData.player_id);
                              }}
                              className="px-3 py-1.5 bg-rr-navy text-white text-xs font-bold rounded-lg hover:bg-slate-800 flex items-center"
                            >
                              <GitCompare className="w-3.5 h-3.5 mr-1.5" />
                              Launch Comparison Lab
                            </button>
                          )}
                        </div>

                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
                          {profileData.sections.comparison_peers.map((peer) => (
                            <div
                              key={peer.player_id}
                              onClick={() => {
                                setSelectedPlayerId(peer.player_id);
                                setActiveProfileTab('overview');
                              }}
                              className="bg-white p-3 rounded-lg border border-slate-200 hover:border-rr-pink cursor-pointer transition-all text-xs"
                            >
                              <div className="font-bold text-rr-navy truncate">{peer.player_name}</div>
                              <div className="text-[10px] text-slate-500">{peer.role}</div>
                              <div className="mt-1 flex items-center justify-between text-[11px]">
                                <span className="font-bold text-rr-pink">
                                  {peer.primary_rate.toFixed(1)} {peer.rate_label}
                                </span>
                                {peer.is_top_10 && (
                                  <span className="text-[9px] font-bold bg-amber-100 text-amber-800 px-1 rounded">
                                    Top 10
                                  </span>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};

export default PlayerGallery;

