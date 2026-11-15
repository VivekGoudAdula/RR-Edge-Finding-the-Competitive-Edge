import React, { useState, useEffect } from 'react';
import {
  Activity,
  Zap,
  Shield,
  Search,
  Filter,
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  Clock,
  ArrowUpRight,
  Flame,
  ChevronDown,
  Info,
  Layers,
  Sparkles,
  BarChart2,
  RefreshCw,
} from 'lucide-react';
import {
  fetchBehavioralOverview,
  fetchBehavioralBatters,
  fetchBehavioralBowlers,
} from '../services/api';
import { PageHeroCard } from '../components/common/PageHeroCard';

export const BehavioralIntelligence: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'batting' | 'bowling' | 'methodology'>('batting');
  const [overview, setOverview] = useState<any>(null);
  const [batters, setBatters] = useState<any[]>([]);
  const [bowlers, setBowlers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [confidenceFilter, setConfidenceFilter] = useState('ALL');
  const [selectedPlayer, setSelectedPlayer] = useState<any | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [ovData, bData, bwData] = await Promise.all([
        fetchBehavioralOverview(),
        fetchBehavioralBatters({ limit: 100 }),
        fetchBehavioralBowlers({ limit: 100 }),
      ]);
      setOverview(ovData);
      setBatters(bData.results || []);
      setBowlers(bwData.results || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load behavioral intelligence data');
    } finally {
      setLoading(false);
    }
  };

  const filteredBatters = batters.filter((b) => {
    const matchQuery = !searchQuery || b.striker_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchConf = confidenceFilter === 'ALL' || b.sample_confidence === confidenceFilter;
    return matchQuery && matchConf;
  });

  const filteredBowlers = bowlers.filter((bw) => {
    const matchQuery = !searchQuery || bw.bowler_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchConf = confidenceFilter === 'ALL' || bw.sample_confidence === confidenceFilter;
    return matchQuery && matchConf;
  });

  const getConfidenceBadge = (tier: string) => {
    if (tier === 'CONFIDENT') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Confident (N ≥ 30)
        </span>
      );
    }
    if (tier === 'PROVISIONAL') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
          <AlertCircle className="w-3 h-3 text-amber-600" /> Provisional (15-29)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-600 border border-gray-200">
        <AlertCircle className="w-3 h-3 text-gray-400" /> Insufficient Evidence (&lt; 15)
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] text-rr-muted space-y-4">
        <RefreshCw className="w-8 h-8 animate-spin text-rr-pink" />
        <p className="text-sm font-medium">Extracting observable ball-by-ball behavioral response curves...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700 space-y-2">
        <div className="flex items-center gap-2 font-bold text-base">
          <AlertCircle className="w-5 h-5 text-red-600" /> Failed to load Behavioral Intelligence
        </div>
        <p className="text-sm">{error}</p>
        <button
          onClick={loadData}
          className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fadeIn pb-12">
      {/* Standardized Compact Hero Section */}
      <PageHeroCard
        badge="Observable Behavioral Intelligence Layer"
        badgeIcon={<Activity className="w-3.5 h-3.5 text-rr-pink" />}
        badgeContext="Audited Cohort"
        title="Observable Behavioral Pressure Intelligence"
        description="Quantifying ball-by-ball empirical reactions to high-leverage match events (post-dot acceleration, post-boundary containment bounce-back, and transition stabilization)—grounded in observable delivery sequences."
      />

      {/* Behavioral Intelligence Architecture Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-rr-border shadow-card space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-rr-muted uppercase tracking-wider">
            <span>Deliveries Analyzed</span>
            <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-[10px]">Audited</span>
          </div>
          <div className="text-2xl font-black text-rr-charcoal">
            {overview?.total_deliveries_analyzed?.toLocaleString() || '194,014'}
          </div>
          <div className="text-xs text-rr-muted">Ball-by-Ball Observations</div>
          <div className="text-[11px] font-mono text-emerald-700 pt-1 border-t border-rr-soft flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> 837 Audited Matches
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-rr-border shadow-card space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-rr-muted uppercase tracking-wider">
            <span>Confident Batters</span>
            <span className="px-2 py-0.5 rounded bg-pink-50 text-rr-pink text-[10px]">N ≥ 30 Balls</span>
          </div>
          <div className="text-2xl font-black text-rr-pink">
            {overview?.batters?.confident_sample_count || 185}
          </div>
          <div className="text-xs text-rr-muted">Post-Dot Event Accelerators</div>
          <div className="text-[11px] font-mono text-slate-500 pt-1 border-t border-rr-soft">
            Immediate Recovery Sequences
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-rr-border shadow-card space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-rr-muted uppercase tracking-wider">
            <span>Confident Bowlers</span>
            <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-700 text-[10px]">N ≥ 30 Balls</span>
          </div>
          <div className="text-2xl font-black text-rr-charcoal">
            {overview?.bowlers?.confident_sample_count || 229}
          </div>
          <div className="text-xs text-rr-muted">Post-Boundary Containment</div>
          <div className="text-[11px] font-mono text-slate-500 pt-1 border-t border-rr-soft">
            Next-Legal Ball Bounce-Back
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-rr-border shadow-card space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-rr-muted uppercase tracking-wider">
            <span>Methodological Rule</span>
            <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 text-[10px]">Verified</span>
          </div>
          <div className="text-2xl font-black text-rr-charcoal">Zero Leakage</div>
          <div className="text-xs text-rr-muted">Non-Judgmental Metrics</div>
          <div className="text-[11px] font-mono text-emerald-700 pt-1 border-t border-rr-soft flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Empirical Sequences Only
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-rr-border space-x-6">
        <button
          onClick={() => { setActiveTab('batting'); setSelectedPlayer(null); }}
          className={`pb-3 text-sm font-bold transition-all relative ${
            activeTab === 'batting' ? 'text-rr-pink border-b-2 border-rr-pink' : 'text-rr-muted hover:text-rr-charcoal'
          }`}
        >
          Batting Recovery Dynamics
        </button>
        <button
          onClick={() => { setActiveTab('bowling'); setSelectedPlayer(null); }}
          className={`pb-3 text-sm font-bold transition-all relative ${
            activeTab === 'bowling' ? 'text-rr-pink border-b-2 border-rr-pink' : 'text-rr-muted hover:text-rr-charcoal'
          }`}
        >
          Bowling Bounce-Back &amp; Over Progression
        </button>
        <button
          onClick={() => { setActiveTab('methodology'); setSelectedPlayer(null); }}
          className={`pb-3 text-sm font-bold transition-all relative ${
            activeTab === 'methodology' ? 'text-rr-pink border-b-2 border-rr-pink' : 'text-rr-muted hover:text-rr-charcoal'
          }`}
        >
          Behavioral Taxonomy &amp; Rubric
        </button>
      </div>

      {/* Tab 1: Batting Behavioral Dynamics */}
      {activeTab === 'batting' && (
        <div className="space-y-6">
          {/* Key Insights Banner */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-5 rounded-xl border border-rr-border shadow-sm flex flex-col justify-between">
              <div>
                <span className="text-xs font-bold text-rr-pink tracking-wide uppercase">Top Post-Dot Accelerator</span>
                <h3 className="text-lg font-extrabold text-rr-navy mt-1">Tim David</h3>
                <p className="text-xs text-rr-muted mt-1 leading-relaxed">
                  Generates an explosive <strong>192.22 Strike Rate</strong> on balls immediately following 2+ consecutive dots (+15.20 ΔSR over baseline), scoring boundaries on 25.6% of recovery deliveries.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-rr-border/60 flex justify-between items-center text-xs">
                <span className="font-semibold text-rr-charcoal">Resilience Index (Expl.): +9.57</span>
                <span className="text-emerald-600 font-bold">Confident (N=90)</span>
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-rr-border shadow-sm flex flex-col justify-between">
              <div>
                <span className="text-xs font-bold text-rr-gold tracking-wide uppercase">Highest Scoring Resilience (Exploratory)</span>
                <h3 className="text-lg font-extrabold text-rr-navy mt-1">Yashasvi Jaiswal</h3>
                <p className="text-xs text-rr-muted mt-1 leading-relaxed">
                  Surges to <strong>181.66 Strike Rate</strong> post-dot sequence (+26.13 ΔSR), breaking drought sequences with exceptional strike rotation (scoring latency 1.4 balls).
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-rr-border/60 flex justify-between items-center text-xs">
                <span className="font-semibold text-rr-charcoal">Resilience Index (Expl.): +27.78</span>
                <span className="text-emerald-600 font-bold">Confident (N=229)</span>
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-rr-border shadow-sm flex flex-col justify-between">
              <div>
                <span className="text-xs font-bold text-rr-navy tracking-wide uppercase">Tactical Strike Consolidator</span>
                <h3 className="text-lg font-extrabold text-rr-navy mt-1">Nicholas Pooran</h3>
                <p className="text-xs text-rr-muted mt-1 leading-relaxed">
                  Adjusts tempo deliberately following dots (116.90 SR, -40.37 ΔSR) to protect wicket, while maintaining a high 145.70 SR in post-wicket transition windows.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-rr-border/60 flex justify-between items-center text-xs">
                <span className="font-semibold text-rr-charcoal">Post-Wkt Dot: 38.0%</span>
                <span className="text-emerald-600 font-bold">Confident (N=213)</span>
              </div>
            </div>
          </div>

          {/* Controls: Search & Filter */}
          <div className="bg-white p-4 rounded-xl border border-rr-border shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-rr-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search batter by name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 border border-rr-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-rr-pink/30 focus:border-rr-pink"
              />
            </div>
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <span className="text-xs font-semibold text-rr-muted flex items-center gap-1">
                <Filter className="w-3.5 h-3.5" /> Confidence:
              </span>
              <div className="flex bg-rr-palePink p-1 rounded-lg text-xs font-bold">
                {['ALL', 'CONFIDENT', 'PROVISIONAL', 'INSUFFICIENT_EVIDENCE'].map((tier) => (
                  <button
                    key={tier}
                    onClick={() => setConfidenceFilter(tier)}
                    className={`px-3 py-1 rounded-md transition ${
                      confidenceFilter === tier
                        ? 'bg-rr-navy text-white shadow-sm'
                        : 'text-rr-charcoal hover:text-rr-pink'
                    }`}
                  >
                    {tier === 'ALL' ? 'All' : tier === 'CONFIDENT' ? 'Confident' : tier === 'PROVISIONAL' ? 'Provisional' : 'Insufficient'}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Exploratory Metric Governance Note */}
          <div className="bg-blue-50/60 border border-blue-200/80 rounded-xl p-3.5 flex items-start gap-3 text-xs text-blue-900">
            <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold text-blue-950">Exploratory Composite Metric Disclosure:</span>
              <p className="text-blue-800 leading-relaxed">
                The <em>Scoring Resilience Index</em> = 0.5 &times; &Delta;SR<sub>post-dot</sub> + 0.5 &times; &Delta;SR<sub>pressure-vs-normal</sub> combines two disparate reference baselines (career average strike rate vs. normal-pressure strike rate) and lacks contextual match-par normalization. It is retained strictly as an exploratory composite indicator. Tactical talent evaluation should prioritize the individual observable metrics (&Delta;SR post-dot, post-wicket strike rate, and balls-to-boundary latency).
              </p>
            </div>
          </div>

          {/* Batting Leaderboard Table */}
          <div className="bg-white rounded-xl border border-rr-border shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-rr-palePink/60 text-rr-navy text-xs font-extrabold uppercase tracking-wider border-b border-rr-border">
                  <tr>
                    <th className="py-3.5 px-4">Batter</th>
                    <th className="py-3.5 px-3 text-right">Post-Dot Balls</th>
                    <th className="py-3.5 px-3 text-right">Post-Dot SR</th>
                    <th className="py-3.5 px-3 text-right">Δ SR (Post-Dot)</th>
                    <th className="py-3.5 px-3 text-right">Post-Wkt SR</th>
                    <th className="py-3.5 px-3 text-right">Breakout Latency</th>
                    <th className="py-3.5 px-3 text-right">Resilience Index (Expl.)</th>
                    <th className="py-3.5 px-4 text-center">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-rr-border">
                  {filteredBatters.slice(0, 25).map((b) => (
                    <tr
                      key={b.striker_id}
                      onClick={() => setSelectedPlayer(b)}
                      className="hover:bg-rr-palePink/30 cursor-pointer transition"
                    >
                      <td className="py-3 px-4 font-bold text-rr-navy">
                        <div className="flex items-center gap-2">
                          <span>{b.striker_name}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 font-mono">
                            ID: {b.striker_id}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-3 text-right font-mono text-xs">{b.post_dot_balls}</td>
                      <td className="py-3 px-3 text-right font-mono font-bold text-rr-charcoal">
                        {b.post_dot_strike_rate.toFixed(1)}
                      </td>
                      <td className="py-3 px-3 text-right font-mono">
                        <span
                          className={`font-semibold ${
                            b.delta_sr_post_dot > 0
                              ? 'text-emerald-600'
                              : b.delta_sr_post_dot < -10
                              ? 'text-rose-600'
                              : 'text-gray-600'
                          }`}
                        >
                          {b.delta_sr_post_dot > 0 ? `+${b.delta_sr_post_dot.toFixed(1)}` : b.delta_sr_post_dot.toFixed(1)}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right font-mono text-xs">{b.post_wkt_strike_rate.toFixed(1)}</td>
                      <td className="py-3 px-3 text-right font-mono text-xs text-rr-muted">
                        {b.avg_balls_to_scoring > 0 ? `${b.avg_balls_to_scoring.toFixed(1)} balls` : '—'}
                      </td>
                      <td className="py-3 px-3 text-right font-mono font-bold">
                        <span
                          className={`px-2 py-0.5 rounded text-xs ${
                            b.scoring_resilience_index > 10
                              ? 'bg-emerald-50 text-emerald-700 font-extrabold'
                              : b.scoring_resilience_index > 0
                              ? 'bg-blue-50 text-blue-700'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {b.scoring_resilience_index > 0 ? `+${b.scoring_resilience_index.toFixed(1)}` : b.scoring_resilience_index.toFixed(1)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">{getConfidenceBadge(b.sample_confidence)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="p-3 bg-gray-50 border-t border-rr-border text-xs text-rr-muted flex justify-between items-center">
              <span>Showing {Math.min(25, filteredBatters.length)} of {filteredBatters.length} filtered batter candidates</span>
              <span className="font-medium text-rr-navy">Click any batter to inspect complete behavioral response dossier</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Bowling Behavioral Dynamics */}
      {activeTab === 'bowling' && (
        <div className="space-y-6">
          {/* Key Insights Banner */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-5 rounded-xl border border-rr-border shadow-sm flex flex-col justify-between">
              <div>
                <span className="text-xs font-bold text-rr-pink tracking-wide uppercase">Elite Post-Boundary Strangler</span>
                <h3 className="text-lg font-extrabold text-rr-navy mt-1">Jasprit Bumrah</h3>
                <p className="text-xs text-rr-muted mt-1 leading-relaxed">
                  Concedes just <strong>6.28 Economy</strong> on deliveries immediately following a boundary (tighter than his 7.03 overall economy!), forcing a remarkable <strong>42.20% dot-ball rate</strong> on bounce-back balls.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-rr-border/60 flex justify-between items-center text-xs">
                <span className="font-semibold text-rr-charcoal">Bounce-Back Index: +0.75</span>
                <span className="text-emerald-600 font-bold">Confident (N=218)</span>
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-rr-border shadow-sm flex flex-col justify-between">
              <div>
                <span className="text-xs font-bold text-rr-gold tracking-wide uppercase">Boundary Containment Master</span>
                <h3 className="text-lg font-extrabold text-rr-navy mt-1">Sunil Narine</h3>
                <p className="text-xs text-rr-muted mt-1 leading-relaxed">
                  Maintains an 8.10 post-boundary economy with a <strong>37.14% dot rate</strong>. Concedes secondary boundaries on only 14.3% of post-boundary balls, preventing cluster hemorrhaging.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-rr-border/60 flex justify-between items-center text-xs">
                <span className="font-semibold text-rr-charcoal">Post-Bnd Dots: 37.1%</span>
                <span className="text-emerald-600 font-bold">Confident (N=140)</span>
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-rr-border shadow-sm flex flex-col justify-between">
              <div>
                <span className="text-xs font-bold text-rr-navy tracking-wide uppercase">Late Match Phase Fortress</span>
                <h3 className="text-lg font-extrabold text-rr-navy mt-1">Matheesha Pathirana</h3>
                <p className="text-xs text-rr-muted mt-1 leading-relaxed">
                  Excels in late match over allocations (overs 3-4 / balls 13-24+), conceding lower economy under heavy death-overs fire while sustaining high wicket penetration (post-bnd wicket rate 7.1%).
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-rr-border/60 flex justify-between items-center text-xs">
                <span className="font-semibold text-rr-charcoal">Post-Bnd Wkts: 7.1%</span>
                <span className="text-emerald-600 font-bold">Confident (N=155)</span>
              </div>
            </div>
          </div>

          {/* Controls: Search & Filter */}
          <div className="bg-white p-4 rounded-xl border border-rr-border shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-rr-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search bowler by name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 border border-rr-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-rr-pink/30 focus:border-rr-pink"
              />
            </div>
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <span className="text-xs font-semibold text-rr-muted flex items-center gap-1">
                <Filter className="w-3.5 h-3.5" /> Confidence:
              </span>
              <div className="flex bg-rr-palePink p-1 rounded-lg text-xs font-bold">
                {['ALL', 'CONFIDENT', 'PROVISIONAL', 'INSUFFICIENT_EVIDENCE'].map((tier) => (
                  <button
                    key={tier}
                    onClick={() => setConfidenceFilter(tier)}
                    className={`px-3 py-1 rounded-md transition ${
                      confidenceFilter === tier
                        ? 'bg-rr-navy text-white shadow-sm'
                        : 'text-rr-charcoal hover:text-rr-pink'
                    }`}
                  >
                    {tier === 'ALL' ? 'All' : tier === 'CONFIDENT' ? 'Confident' : tier === 'PROVISIONAL' ? 'Provisional' : 'Insufficient'}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Bowling Metric Governance Note */}
          <div className="bg-blue-50/60 border border-blue-200/80 rounded-xl p-3.5 flex items-start gap-3 text-xs text-blue-900">
            <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold text-blue-950">Metric Direction & Contextual Over Allocation Governance:</span>
              <p className="text-blue-800 leading-relaxed">
                <strong>Bounce-Back Index</strong> = Overall Economy &minus; Post-Boundary Economy. <em>Positive values indicate tighter containment/run suppression after conceding a boundary</em>; negative values denote elevated concession drift. <strong>Over Progression (Overs 1-2 vs Overs 3-4)</strong> measures personal match-over allocation (balls 1&ndash;12 vs. 13&ndash;24+ within the innings). Because T20 bowling spells are rarely continuous 4-over spells and depend heavily on tactical match phase (e.g. death overs), differences reflect role allocation and phase exposure rather than biological fatigue.
              </p>
            </div>
          </div>

          {/* Bowler Leaderboard Table */}
          <div className="bg-white rounded-xl border border-rr-border shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-rr-palePink/60 text-rr-navy text-xs font-extrabold uppercase tracking-wider border-b border-rr-border">
                  <tr>
                    <th className="py-3.5 px-4">Bowler</th>
                    <th className="py-3.5 px-3 text-right">Post-Bnd Balls</th>
                    <th className="py-3.5 px-3 text-right">Post-Bnd Econ</th>
                    <th className="py-3.5 px-3 text-right">Overall Econ</th>
                    <th className="py-3.5 px-3 text-right">Post-Bnd Dot %</th>
                    <th className="py-3.5 px-3 text-right">Overs 1-2 Econ</th>
                    <th className="py-3.5 px-3 text-right">Overs 3-4 Econ</th>
                    <th className="py-3.5 px-3 text-right">Bounce-Back</th>
                    <th className="py-3.5 px-4 text-center">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-rr-border">
                  {filteredBowlers.slice(0, 25).map((bw) => (
                    <tr
                      key={bw.bowler_id}
                      onClick={() => setSelectedPlayer(bw)}
                      className="hover:bg-rr-palePink/30 cursor-pointer transition"
                    >
                      <td className="py-3 px-4 font-bold text-rr-navy">
                        <div className="flex items-center gap-2">
                          <span>{bw.bowler_name}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 font-mono">
                            ID: {bw.bowler_id}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-3 text-right font-mono text-xs">{bw.post_boundary_legal_balls}</td>
                      <td className="py-3 px-3 text-right font-mono font-bold text-rr-charcoal">
                        {bw.post_boundary_economy.toFixed(2)}
                      </td>
                      <td className="py-3 px-3 text-right font-mono text-xs text-rr-muted">
                        {bw.overall_economy.toFixed(2)}
                      </td>
                      <td className="py-3 px-3 text-right font-mono text-xs font-semibold">
                        <span className={bw.post_boundary_dot_pct >= 35.0 ? 'text-emerald-600 font-bold' : 'text-gray-700'}>
                          {bw.post_boundary_dot_pct.toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right font-mono text-xs">{bw.early_spell_economy.toFixed(2)}</td>
                      <td className="py-3 px-3 text-right font-mono text-xs">{bw.late_spell_economy.toFixed(2)}</td>
                      <td className="py-3 px-3 text-right font-mono font-bold">
                        <span
                          className={`px-2 py-0.5 rounded text-xs ${
                            bw.bounceback_index > 0
                              ? 'bg-emerald-50 text-emerald-700 font-extrabold'
                              : bw.bounceback_index > -1.0
                              ? 'bg-blue-50 text-blue-700'
                              : 'bg-rose-50 text-rose-700'
                          }`}
                        >
                          {bw.bounceback_index > 0 ? `+${bw.bounceback_index.toFixed(2)}` : bw.bounceback_index.toFixed(2)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">{getConfidenceBadge(bw.sample_confidence)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="p-3 bg-gray-50 border-t border-rr-border text-xs text-rr-muted flex justify-between items-center">
              <span>Showing {Math.min(25, filteredBowlers.length)} of {filteredBowlers.length} filtered bowler candidates</span>
              <span className="font-medium text-rr-navy">Click any bowler to inspect complete bounce-back and spell progression dossier</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Methodology & Behavioral Taxonomy */}
      {activeTab === 'methodology' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-rr-border shadow-sm space-y-4">
            <div className="flex items-center gap-2 text-rr-navy font-extrabold text-lg">
              <Info className="w-5 h-5 text-rr-pink" /> Observable Behavioral Taxonomy & Principles
            </div>
            <p className="text-sm text-rr-charcoal leading-relaxed">
              Unlike subjective scout opinions or psychometric speculation (e.g. "clutch temperament", "mental freeze"), RR EDGE behavioral metrics are defined strictly through empirical ball-by-ball sequence observations:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="border border-rr-border rounded-xl p-4 bg-gray-50/50 space-y-2">
                <span className="text-xs font-bold text-rr-pink uppercase tracking-wide">Batting Dynamics & Audited Events</span>
                <ul className="text-xs text-rr-muted space-y-2 leading-relaxed">
                  <li>
                    <strong className="text-rr-charcoal">Post-Dot Drought State Recovery (Preceded by &ge; 2 Dots):</strong> Evaluates scoring rate and boundary probability across all deliveries faced while remaining in a drought state (&ge; 2 consecutive personal dots) until broken by a scoring shot. <em>Reconciliation: 14,876 trigger sequences &rarr; 19,818 deliveries observed under drought state (mean 1.33 balls/sequence due to compounding dots; 12,653 strictly at immediate t+1) across 834 matches and 689 batters.</em>
                  </li>
                  <li>
                    <strong className="text-rr-charcoal">Post-Wicket Consolidation Window:</strong> Evaluates batter strike rate, dot percentage, and survival across the first 6 deliveries faced after a team wicket falls.
                  </li>
                  <li>
                    <strong className="text-rr-charcoal">Drought Breakout Latency:</strong> Mean deliveries taken by the batter to score or hit a boundary after entering a drought sequence.
                  </li>
                  <li>
                    <strong className="text-rr-charcoal">Exploratory Scoring Resilience Index:</strong> 0.5 &times; &Delta;SR<sub>post-dot</sub> + 0.5 &times; &Delta;SR<sub>pressure-vs-normal</sub>. Blends career-baseline shift with normal-pressure shift; retained strictly as an exploratory composite indicator.
                  </li>
                </ul>
              </div>

              <div className="border border-rr-border rounded-xl p-4 bg-gray-50/50 space-y-2">
                <span className="text-xs font-bold text-rr-gold uppercase tracking-wide">Bowling Dynamics & Audited Events</span>
                <ul className="text-xs text-rr-muted space-y-2 leading-relaxed">
                  <li>
                    <strong className="text-rr-charcoal">Post-Boundary Bounce-Back (t+1):</strong> Concession economy, dot percentage, and wicket probability on the legal ball bowled immediately after conceding a 4 or 6 in the same over (ball 6 triggers excluded). <em>Audit: 32,662 boundary triggers &rarr; 29,219 subsequent deliveries observed across 836 matches and 577 bowlers.</em>
                  </li>
                  <li>
                    <strong className="text-rr-charcoal">Cluster Hemorrhage Resistance:</strong> Concession rate on deliveries following a 3-ball rolling window conceding &ge; 8 runs.
                  </li>
                  <li>
                    <strong className="text-rr-charcoal">Cumulative Inning Over Exposure Progression:</strong> Comparative containment in early match allocation (overs 1-2 / balls 1-12, N=110,664) vs late match allocation (overs 3-4 / balls 13-24+, N=75,051). Governed by phase tactics rather than physical fatigue.
                  </li>
                  <li>
                    <strong className="text-rr-charcoal">Bounce-Back Index:</strong> Overall Economy &minus; Post-Boundary Economy. <em>Positive indicates tighter containment/suppression</em> after conceding a boundary; negative indicates increased leakage.
                  </li>
                </ul>
              </div>
            </div>

            <div className="mt-4 p-4 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-900 space-y-1">
              <div className="font-bold flex items-center gap-1.5 text-amber-950">
                <AlertCircle className="w-4 h-4 text-amber-600" /> Statistical Sample Safeguards & Masking Policy
              </div>
              <p>
                To prevent misleading conclusions drawn from microscopic samples, RR EDGE enforces strict sample thresholds: candidates with &lt; 15 event opportunities are labeled as <strong>Insufficient Evidence</strong>, while candidates with 15–29 events are designated as <strong>Provisional</strong>. Full strategic weight is accorded only to <strong>Confident</strong> candidates (N ≥ 30 events).
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Selected Player Detailed Drawer / Modal */}
      {selectedPlayer && (
        <div className="fixed inset-0 z-[100] bg-rr-darkNavy/60 backdrop-blur-sm flex justify-end">
          <div className="bg-white w-full max-w-xl h-full shadow-2xl p-6 overflow-y-auto space-y-6">
            <div className="flex items-center justify-between border-b border-rr-border pb-4">
              <div>
                <span className="text-xs font-bold text-rr-pink uppercase tracking-wide">
                  {selectedPlayer.striker_name ? 'Batter Behavioral Dossier' : 'Bowler Behavioral Dossier'}
                </span>
                <h2 className="text-xl font-black text-rr-navy mt-1">
                  {selectedPlayer.striker_name || selectedPlayer.bowler_name}
                </h2>
              </div>
              <button
                onClick={() => setSelectedPlayer(null)}
                className="text-gray-400 hover:text-gray-600 p-2 rounded-lg hover:bg-gray-100 transition"
              >
                ✕
              </button>
            </div>

            {/* Confidence Banner */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-rr-border">
              <span className="text-xs font-semibold text-rr-muted">Sample Statistical Grade</span>
              <div>{getConfidenceBadge(selectedPlayer.sample_confidence)}</div>
            </div>

            {/* Batter Details */}
            {selectedPlayer.striker_name && (
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-rr-navy uppercase tracking-wider">
                  Post-Dot Drought Recovery Dynamics
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-rr-palePink/40 rounded-xl border border-rr-border">
                    <span className="text-[11px] text-rr-muted">Post-Dot Deliveries</span>
                    <div className="text-lg font-black text-rr-navy mt-0.5">{selectedPlayer.post_dot_balls}</div>
                    <span className="text-[10px] text-gray-500">Balls after ≥ 2 dots</span>
                  </div>
                  <div className="p-3 bg-rr-palePink/40 rounded-xl border border-rr-border">
                    <span className="text-[11px] text-rr-muted">Post-Dot Strike Rate</span>
                    <div className="text-lg font-black text-rr-pink mt-0.5">
                      {selectedPlayer.post_dot_strike_rate.toFixed(1)}
                    </div>
                    <span className="text-[10px] text-emerald-600 font-bold">
                      {selectedPlayer.delta_sr_post_dot > 0 ? `+${selectedPlayer.delta_sr_post_dot.toFixed(1)} ΔSR` : `${selectedPlayer.delta_sr_post_dot.toFixed(1)} ΔSR`}
                    </span>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-xl border border-rr-border">
                    <span className="text-[11px] text-rr-muted">Post-Dot Boundary %</span>
                    <div className="text-lg font-black text-rr-navy mt-0.5">{selectedPlayer.post_dot_boundary_pct}%</div>
                    <span className="text-[10px] text-gray-500">4s & 6s frequency</span>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-xl border border-rr-border">
                    <span className="text-[11px] text-rr-muted">Post-Dot Wicket Risk</span>
                    <div className="text-lg font-black text-rose-600 mt-0.5">{selectedPlayer.post_dot_wicket_pct}%</div>
                    <span className="text-[10px] text-gray-500">Dismissal rate</span>
                  </div>
                </div>

                <h4 className="text-xs font-bold text-rr-navy uppercase tracking-wider pt-2">
                  Transition Window & Latency
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-gray-50 rounded-xl border border-rr-border">
                    <span className="text-[11px] text-rr-muted">Post-Wicket SR (1st 6 balls)</span>
                    <div className="text-lg font-black text-rr-navy mt-0.5">{selectedPlayer.post_wkt_strike_rate.toFixed(1)}</div>
                    <span className="text-[10px] text-gray-500">{selectedPlayer.post_wkt_balls} balls observed</span>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-xl border border-rr-border">
                    <span className="text-[11px] text-rr-muted">Balls to Scoring Shot</span>
                    <div className="text-lg font-black text-rr-navy mt-0.5">{selectedPlayer.avg_balls_to_scoring.toFixed(1)}</div>
                    <span className="text-[10px] text-gray-500">Rotation latency</span>
                  </div>
                </div>

                <h4 className="text-xs font-bold text-rr-navy uppercase tracking-wider pt-2">
                  Pressure vs Normal Performance Delta
                </h4>
                <div className="p-4 bg-gray-50 rounded-xl border border-rr-border space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-rr-muted">High Pressure SR:</span>
                    <span className="font-mono font-bold">{selectedPlayer.pressure_strike_rate.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-rr-muted">Normal Pressure SR:</span>
                    <span className="font-mono font-bold">{selectedPlayer.normal_strike_rate.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between pt-1 border-t border-rr-border">
                    <span className="font-semibold text-rr-navy">Pressure Shift (ΔSR):</span>
                    <span className={`font-mono font-extrabold ${selectedPlayer.delta_sr_pressure_vs_normal > 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                      {selectedPlayer.delta_sr_pressure_vs_normal > 0 ? `+${selectedPlayer.delta_sr_pressure_vs_normal.toFixed(1)}` : selectedPlayer.delta_sr_pressure_vs_normal.toFixed(1)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Bowler Details */}
            {selectedPlayer.bowler_name && (
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-rr-navy uppercase tracking-wider">
                  Post-Boundary Bounce-Back Dynamics
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-rr-palePink/40 rounded-xl border border-rr-border">
                    <span className="text-[11px] text-rr-muted">Post-Boundary Deliveries</span>
                    <div className="text-lg font-black text-rr-navy mt-0.5">{selectedPlayer.post_boundary_legal_balls}</div>
                    <span className="text-[10px] text-gray-500">Legal balls immediately after 4/6</span>
                  </div>
                  <div className="p-3 bg-rr-palePink/40 rounded-xl border border-rr-border">
                    <span className="text-[11px] text-rr-muted">Post-Boundary Economy</span>
                    <div className="text-lg font-black text-rr-navy mt-0.5">
                      {selectedPlayer.post_boundary_economy.toFixed(2)}
                    </div>
                    <span className="text-[10px] text-emerald-600 font-bold">
                      {selectedPlayer.bounceback_index > 0 ? `+${selectedPlayer.bounceback_index.toFixed(2)} containment` : `${selectedPlayer.bounceback_index.toFixed(2)} drift`}
                    </span>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-xl border border-rr-border">
                    <span className="text-[11px] text-rr-muted">Post-Boundary Dot %</span>
                    <div className="text-lg font-black text-emerald-600 mt-0.5">{selectedPlayer.post_boundary_dot_pct.toFixed(1)}%</div>
                    <span className="text-[10px] text-gray-500">Immediate recovery dots</span>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-xl border border-rr-border">
                    <span className="text-[11px] text-rr-muted">Compounding Boundary %</span>
                    <div className="text-lg font-black text-rose-600 mt-0.5">{selectedPlayer.post_boundary_boundary_pct.toFixed(1)}%</div>
                    <span className="text-[10px] text-gray-500">Back-to-back boundaries</span>
                  </div>
                </div>

                <h4 className="text-xs font-bold text-rr-navy uppercase tracking-wider pt-2">
                  Cumulative Inning Over Exposure Progression (Overs 1-2 vs Overs 3-4 Allocation)
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-gray-50 rounded-xl border border-rr-border">
                    <span className="text-[11px] text-rr-muted">Overs 1-2 Economy (Balls 1-12)</span>
                    <div className="text-lg font-black text-rr-navy mt-0.5">{selectedPlayer.early_spell_economy.toFixed(2)}</div>
                    <span className="text-[10px] text-gray-500">{selectedPlayer.early_spell_balls} balls bowled</span>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-xl border border-rr-border">
                    <span className="text-[11px] text-rr-muted">Overs 3-4 Economy (Balls 13-24+)</span>
                    <div className="text-lg font-black text-rr-navy mt-0.5">{selectedPlayer.late_spell_economy.toFixed(2)}</div>
                    <span className="text-[10px] text-gray-500">{selectedPlayer.late_spell_balls} balls bowled</span>
                  </div>
                </div>

                <h4 className="text-xs font-bold text-rr-navy uppercase tracking-wider pt-2">
                  Pressure vs Normal Concession Shift
                </h4>
                <div className="p-4 bg-gray-50 rounded-xl border border-rr-border space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-rr-muted">High Pressure Economy:</span>
                    <span className="font-mono font-bold">{selectedPlayer.pressure_economy.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-rr-muted">Normal Pressure Economy:</span>
                    <span className="font-mono font-bold">{selectedPlayer.normal_economy.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between pt-1 border-t border-rr-border">
                    <span className="font-semibold text-rr-navy">Pressure Concession Shift (ΔEcon):</span>
                    <span className={`font-mono font-extrabold ${selectedPlayer.delta_econ_pressure_vs_normal <= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                      {selectedPlayer.delta_econ_pressure_vs_normal > 0 ? `+${selectedPlayer.delta_econ_pressure_vs_normal.toFixed(2)}` : selectedPlayer.delta_econ_pressure_vs_normal.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            <button
              onClick={() => setSelectedPlayer(null)}
              className="w-full py-2.5 bg-rr-navy text-white rounded-xl text-sm font-bold hover:bg-rr-darkNavy transition"
            >
              Close Dossier
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

