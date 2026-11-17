import React, { useEffect, useState } from 'react';
import {
  Flame,
  Award,
  TrendingUp,
  Activity,
  Layers,
  ArrowRight,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import { fetchOverview } from '../services/api';
import canonicalOverview from '../data/canonicalOverview.json';
import { OverviewData } from '../types';
import { MetricCard } from '../components/common/MetricCard';
import { SectionHeading } from '../components/common/SectionHeading';
import { ArchetypeBadge, TierBadge } from '../components/common/Badge';
import { PageHeroCard } from '../components/common/PageHeroCard';
import { PlayerAvatar } from '../components/common/PlayerAvatar';
import { PageId } from '../components/layout/Sidebar';

interface ExecutiveOverviewProps {
  onNavigate: (page: PageId, playerId?: number) => void;
}

export const ExecutiveOverview: React.FC<ExecutiveOverviewProps> = ({ onNavigate }) => {
  const [data, setData] = useState<OverviewData>(canonicalOverview as unknown as OverviewData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchOverview()
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="p-8 space-y-6 animate-pulse">
        <div className="h-44 bg-pink-50 rounded-2xl border border-pink-100"></div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-28 bg-white rounded-xl border border-rr-border"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8">
        <div className="p-6 bg-red-50 text-red-700 rounded-xl border border-red-200">
          Failed to load executive overview: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Standardized Compact Hero Section */}
      <PageHeroCard
        badge="Official Intelligence Report • RR EDGE 2026"
        badgeIcon={<Flame className="w-3.5 h-3.5 text-rr-pink" />}
        title={
          <span>
            Finding the <span className="text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-rose-300">Competitive Edge</span> Under Pressure
          </span>
        }
        description="Evaluating true latent talent across 192,373 primary pressure deliveries in IPL 2022–2026 and Senior Men's T20Is using Empirical Bayes shrinkage, Context RAE/RCAE, and match-cluster bootstrap uncertainty."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => onNavigate('batters')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rr-pink text-white text-xs font-bold shadow-sm hover:bg-rr-deepPink transition-all"
            >
              <span>Explore Batters</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => onNavigate('bowlers')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 text-white border border-white/20 text-xs font-semibold hover:bg-white/20 transition-all"
            >
              <span>Explore Bowlers</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => onNavigate('comparison')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 text-white border border-white/20 text-xs font-semibold hover:bg-white/20 transition-all"
            >
              <Sparkles className="w-3.5 h-3.5 text-rr-gold" />
              <span>Head-to-Head</span>
            </button>
          </div>
        }
      />

      {/* Dataset Scope Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Primary Deliveries"
          value={data.metadata.primary_deliveries.toLocaleString()}
          subtitle="Strict cohort (excl. 1,641 DLS-quarantined)"
          accentEdge
          icon={<Layers className="w-5 h-5" />}
        />
        <MetricCard
          title="Matches Included"
          value={data.metadata.matches_analysed}
          subtitle="367 IPL (2022–2026) + 470 Senior T20Is"
          accentEdge
          icon={<Activity className="w-5 h-5" />}
        />
        <MetricCard
          title="Candidate Universe"
          value={data.metadata.batters_analysed + data.metadata.bowlers_analysed}
          subtitle={`${data.metadata.batters_analysed} batters • ${data.metadata.bowlers_analysed} bowlers`}
          accentEdge
          icon={<Award className="w-5 h-5" />}
        />
        <MetricCard
          title="Empirical Bayes M"
          value="M=45"
          subtitle="Validated shrinkage grid: 25, 45, 60, 90"
          accentEdge
          icon={<TrendingUp className="w-5 h-5" />}
        />
      </div>

      {/* Key Strategic Discoveries */}
      <div>
        <SectionHeading
          badge="Empirical Discoveries"
          title="Key Pressure-Performance Discoveries"
          description="Actionable scouting findings revealed by isolating delivery-level match leverage and applying Bayesian shrinkage."
        />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.key_discoveries.map((disc) => (
            <div
              key={disc.id}
              className="bg-white rounded-xl border border-rr-border p-5 shadow-rr-card hover:border-pink-300 transition-all duration-200 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-rr-muted">
                    {disc.discipline} Insight
                  </span>
                  <ArchetypeBadge archetype={disc.tag} />
                </div>
                <h3 className="text-base font-bold text-rr-charcoal tracking-tight font-heading leading-snug">
                  {disc.headline}
                </h3>
                <p className="mt-2 text-xs text-rr-muted leading-relaxed">
                  {disc.detail}
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-rr-border flex items-center justify-between">
                <span className="text-[11px] font-semibold text-rr-muted">{disc.id}</span>
                <button
                  onClick={() => onNavigate(disc.discipline === 'Batter' ? 'batters' : 'bowlers')}
                  className="text-xs font-bold text-rr-pink hover:text-rr-deepPink inline-flex items-center gap-1"
                >
                  <span>View Dossier</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Showcase: Top 10 Batters & Bowlers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Batters Top 10 Card */}
        <div className="bg-white rounded-2xl border border-rr-border shadow-rr-card overflow-hidden">
          <div className="p-5 border-b border-rr-border bg-gradient-to-r from-white to-rr-palePink flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-rr-pink text-white flex items-center justify-center font-bold text-sm">
                B
              </div>
              <div>
                <h3 className="text-lg font-extrabold text-rr-charcoal tracking-tight font-heading">
                  Top 10 Pressure Batters
                </h3>
                <p className="text-xs text-rr-muted">Ordered by verified pressure impact and role fit</p>
              </div>
            </div>
            <button
              onClick={() => onNavigate('batters')}
              className="text-xs font-bold text-rr-pink hover:text-rr-deepPink inline-flex items-center gap-1"
            >
              <span>Full Table</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-rr-warmWhite text-[11px] font-bold text-rr-muted border-b border-rr-border uppercase tracking-wider whitespace-nowrap">
                  <th className="py-2.5 px-3">#</th>
                  <th className="py-2.5 px-3">Player</th>
                  <th className="py-2.5 px-3">Role</th>
                  <th className="py-2.5 px-3 text-right">Shrunk M45</th>
                  <th className="py-2.5 px-3 text-right">RAE (ΔSR)</th>
                  <th className="py-2.5 px-3 text-right">Bnd %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-rr-border text-xs whitespace-nowrap">
                {data.top_10_batters.map((b) => (
                  <tr
                    key={b.player_id}
                    onClick={() => onNavigate('batters', b.player_id)}
                    className="hover:bg-rr-softPink/40 transition-colors cursor-pointer group"
                  >
                    <td className="py-2.5 px-3 font-extrabold text-rr-pink">
                      {b.top_10_rank}
                    </td>
                    <td className="py-2 px-3">
                      <div className="flex items-center gap-2.5">
                        <PlayerAvatar
                          playerId={b.player_id}
                          playerName={b.player_name}
                          size="sm"
                          isTop10={true}
                        />
                        <span className="font-bold text-rr-charcoal group-hover:text-rr-deepPink">
                          {b.player_name}
                        </span>
                      </div>
                    </td>
                    <td className="py-2.5 px-3 text-rr-muted text-[11px]">{b.primary_role}</td>
                    <td className="py-2.5 px-3 text-right font-extrabold text-rr-charcoal font-heading">
                      {b.ipl_shrunk_m45?.toFixed(1) || b.t20i_shrunk_m45?.toFixed(1)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-semibold text-emerald-600">
                      +{b.ipl_context_delta_sr?.toFixed(1) || b.t20i_context_delta_sr?.toFixed(1)}
                    </td>
                    <td className="py-2.5 px-3 text-right text-rr-muted">
                      {b.ipl_boundary_ball_pct?.toFixed(1) || b.t20i_boundary_ball_pct?.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Bowlers Top 10 Card */}
        <div className="bg-white rounded-2xl border border-rr-border shadow-rr-card overflow-hidden">
          <div className="p-5 border-b border-rr-border bg-gradient-to-r from-white to-rr-palePink flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-rr-deepPink text-white flex items-center justify-center font-bold text-sm">
                BW
              </div>
              <div>
                <h3 className="text-lg font-extrabold text-rr-charcoal tracking-tight font-heading">
                  Top 10 Pressure Bowlers
                </h3>
                <p className="text-xs text-rr-muted">Ordered by defensive suppression and wicket threat</p>
              </div>
            </div>
            <button
              onClick={() => onNavigate('bowlers')}
              className="text-xs font-bold text-rr-pink hover:text-rr-deepPink inline-flex items-center gap-1"
            >
              <span>Full Table</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-rr-warmWhite text-[11px] font-bold text-rr-muted border-b border-rr-border uppercase tracking-wider whitespace-nowrap">
                  <th className="py-2.5 px-3">#</th>
                  <th className="py-2.5 px-3">Player</th>
                  <th className="py-2.5 px-3">Role</th>
                  <th className="py-2.5 px-3 text-right">Econ</th>
                  <th className="py-2.5 px-3 text-right" title="Primary All-Runs RCAE (ΔEconomy). Standard economy minus all-runs contextual expectation.">All-Runs RCAE</th>
                  <th className="py-2.5 px-3 text-right">Dot %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-rr-border text-xs whitespace-nowrap">
                {data.top_10_bowlers.map((bw) => (
                  <tr
                    key={bw.player_id}
                    onClick={() => onNavigate('bowlers', bw.player_id)}
                    className="hover:bg-rr-softPink/40 transition-colors cursor-pointer group"
                  >
                    <td className="py-2.5 px-3 font-extrabold text-rr-deepPink">
                      {bw.top_10_rank}
                    </td>
                    <td className="py-2 px-3">
                      <div className="flex items-center gap-2.5">
                        <PlayerAvatar
                          playerId={bw.player_id}
                          playerName={bw.player_name}
                          size="sm"
                          isTop10={true}
                        />
                        <span className="font-bold text-rr-charcoal group-hover:text-rr-deepPink">
                          {bw.player_name}
                        </span>
                      </div>
                    </td>
                    <td className="py-2.5 px-3 text-rr-muted text-[11px]">{bw.primary_role}</td>
                    <td className="py-2.5 px-3 text-right font-extrabold text-rr-charcoal font-heading">
                      {bw.ipl_raw_econ?.toFixed(2) || bw.t20i_raw_econ?.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-semibold text-emerald-600">
                      {bw.ipl_context_delta_econ?.toFixed(2) || bw.t20i_context_delta_econ?.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-3 text-right text-rr-muted">
                      {bw.ipl_dot_ball_pct?.toFixed(1) || bw.t20i_dot_ball_pct?.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Uncertainty & Statistical Protocol Banner */}
      <div className="p-6 rounded-xl bg-white border border-rr-border shadow-rr-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-pink-50 text-rr-pink border border-pink-200">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-rr-charcoal font-heading">
              Evidence-Based Decision Support Architecture
            </h4>
            <p className="text-xs text-rr-muted max-w-3xl leading-relaxed mt-0.5">
              RR EDGE avoids arbitrary composite scoring formulas. Rankings represent transparent strategic judgements between players evaluated across independently visible dimensions. Where bootstrap confidence intervals span zero, no statistically significant difference is established at the 95% level, and ordering reflects tactical franchise priorities.
            </p>
          </div>
        </div>
        <button
          onClick={() => onNavigate('methodology')}
          className="text-xs font-bold px-4 py-2 rounded-lg bg-rr-palePink text-rr-deepPink border border-pink-200 hover:bg-rr-softPink transition-colors whitespace-nowrap"
        >
          View Model Lab
        </button>
      </div>
    </div>
  );
};

