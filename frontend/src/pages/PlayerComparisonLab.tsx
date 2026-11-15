import React, { useEffect, useState } from 'react';
import {
  GitCompare,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Shield,
  Layers,
  Brain,
  Target,
  Scale,
  Zap,
  Swords,
  AlertCircle,
  Clock,
} from 'lucide-react';
import { fetchBatters, fetchBowlers, fetchComparison } from '../services/api';
import { PlayerOverview, ComparisonData, Discipline } from '../types';
import { SectionHeading } from '../components/common/SectionHeading';
import { ArchetypeBadge, TierBadge } from '../components/common/Badge';
import { PageHeroCard } from '../components/common/PageHeroCard';
import { PlayerAvatar } from '../components/common/PlayerAvatar';

export const PlayerComparisonLab: React.FC = () => {
  const [discipline, setDiscipline] = useState<Discipline>('BATTER');
  const [playersList, setPlayersList] = useState<PlayerOverview[]>([]);
  const [playerAId, setPlayerAId] = useState<number>(6396); // Tim David default
  const [playerBId, setPlayerBId] = useState<number>(1699); // SKY default
  const [comparison, setComparison] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(false);

  // Load player options when discipline changes
  useEffect(() => {
    if (discipline === 'BATTER') {
      fetchBatters().then((list) => {
        setPlayersList(list);
        if (list.length >= 2) {
          setPlayerAId(list[0].player_id);
          setPlayerBId(list[1].player_id);
        }
      });
    } else {
      fetchBowlers().then((list) => {
        setPlayersList(list);
        if (list.length >= 2) {
          setPlayerAId(list[0].player_id);
          setPlayerBId(list[1].player_id);
        }
      });
    }
  }, [discipline]);

  // Load comparison when player IDs change
  useEffect(() => {
    if (playerAId && playerBId) {
      setLoading(true);
      fetchComparison(playerAId, playerBId, discipline)
        .then((res) => {
          setComparison(res);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [playerAId, playerBId, discipline]);

  const pA = comparison?.player_a?.player;
  const pB = comparison?.player_b?.player;
  const boot = comparison?.pairwise_bootstrap;

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Standardized Compact Hero Section */}
      <PageHeroCard
        badge="Statistical Decision Support"
        badgeIcon={<Scale className="w-3.5 h-3.5 text-rr-pink" />}
        title="Player Comparison Lab & Bootstrap Verification"
        description="Side-by-side evaluation of candidates with 10,000-resample match-cluster bootstrap testing to distinguish genuine performance separation from sample variance."
        actions={
          <div className="flex items-center rounded-xl bg-white/10 p-1 border border-white/20">
            <button
              onClick={() => setDiscipline('BATTER')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                discipline === 'BATTER'
                  ? 'bg-rr-pink text-white shadow-sm'
                  : 'text-white/70 hover:text-white'
              }`}
            >
              Compare Batters
            </button>
            <button
              onClick={() => setDiscipline('BOWLER')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                discipline === 'BOWLER'
                  ? 'bg-rr-deepPink text-white shadow-sm'
                  : 'text-white/70 hover:text-white'
              }`}
            >
              Compare Bowlers
            </button>
          </div>
        }
      />

      {/* Player Selectors Card */}
      <div className="bg-white rounded-xl border border-rr-border p-4 shadow-card">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center gap-3">
            {(pA || playersList.find((p) => p.player_id === playerAId)) && (
              <PlayerAvatar
                playerId={playerAId}
                playerName={(pA || playersList.find((p) => p.player_id === playerAId))!.player_name}
                size="md"
                isTop10={!!(pA || playersList.find((p) => p.player_id === playerAId))?.top_10_rank}
              />
            )}
            <div className="flex-1">
              <label className="block text-xs font-bold text-rr-muted uppercase tracking-wider mb-1.5">
                Select Player A:
              </label>
              <select
                value={playerAId}
                onChange={(e) => setPlayerAId(Number(e.target.value))}
                className="w-full px-4 py-2.5 rounded-xl bg-rr-warmWhite border border-rr-border text-xs md:text-sm font-bold text-rr-charcoal focus:outline-none focus:border-rr-pink cursor-pointer"
              >
                {playersList.map((p) => (
                  <option key={p.player_id} value={p.player_id}>
                    {p.top_10_rank ? `#${p.top_10_rank} - ` : ''}{p.player_name} ({p.primary_role})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {(pB || playersList.find((p) => p.player_id === playerBId)) && (
              <PlayerAvatar
                playerId={playerBId}
                playerName={(pB || playersList.find((p) => p.player_id === playerBId))!.player_name}
                size="md"
                isTop10={!!(pB || playersList.find((p) => p.player_id === playerBId))?.top_10_rank}
              />
            )}
            <div className="flex-1">
              <label className="block text-xs font-bold text-rr-muted uppercase tracking-wider mb-1.5">
                Select Player B:
              </label>
              <select
                value={playerBId}
                onChange={(e) => setPlayerBId(Number(e.target.value))}
                className="w-full px-4 py-2.5 rounded-xl bg-rr-warmWhite border border-rr-border text-xs md:text-sm font-bold text-rr-charcoal focus:outline-none focus:border-rr-pink cursor-pointer"
              >
                {playersList.map((p) => (
                  <option key={p.player_id} value={p.player_id}>
                    {p.top_10_rank ? `#${p.top_10_rank} - ` : ''}{p.player_name} ({p.primary_role})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {loading || !pA || !pB ? (
        <div className="p-8 text-center text-rr-muted animate-pulse">
          Running comparison and loading bootstrap intervals...
        </div>
      ) : (
        <>
          {/* 1. Sample Comparability Audit Container */}
          {comparison?.comparability_audit && (
            <div className={`p-4 rounded-2xl border transition-all ${
              comparison.comparability_audit.sample_divergence
                ? 'bg-amber-50/70 border-amber-200 text-amber-950'
                : 'bg-emerald-50/70 border-emerald-200 text-emerald-950'
            }`}>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-current/15">
                <div className="flex items-center gap-2">
                  {comparison.comparability_audit.sample_divergence ? (
                    <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
                  ) : (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                  )}
                  <span className="text-xs font-bold font-heading uppercase tracking-wider">
                    {comparison.comparability_audit.sample_divergence
                      ? 'Sample Comparability Disparity Alert'
                      : 'High Comparability Evidence Cohort'}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-[11px] font-semibold">
                  <span>Exposure Ratio: {comparison.comparability_audit.volume_ratio}x</span>
                  <span>•</span>
                  <span>Tiers: {comparison.comparability_audit.tier_a} vs {comparison.comparability_audit.tier_b}</span>
                </div>
              </div>
              <p className="text-xs leading-relaxed mt-2">
                {comparison.comparability_audit.disclosure}
              </p>
            </div>
          )}

          {/* 2. Pairwise Comparison Uncertainty Container */}
          <div className="bg-white rounded-2xl border border-rr-border p-6 shadow-rr-card space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-rr-border">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-rr-pink"></span>
                <h3 className="text-base font-extrabold text-rr-charcoal font-heading">
                  {boot
                    ? 'Precomputed Pairwise Match-Cluster Bootstrap (B = 10,000, seed = 42)'
                    : 'Individual Parameter Empirical Bayes Uncertainty (M ∈ [25, 45, 60, 90])'}
                </h3>
              </div>
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${
                boot ? 'bg-rr-palePink text-rr-deepPink' : 'bg-gray-100 text-rr-charcoal'
              }`}>
                {boot ? 'Adjacent Top-10 Pairwise Bootstrap' : 'Independent Empirical Bayes Posterior'}
              </span>
            </div>

            {boot ? (
              <div className="p-4 rounded-xl bg-rr-warmWhite border border-rr-border space-y-3">
                <div className="text-[11px] font-semibold text-rr-deep">
                  Method: Precomputed Adjacent Match-Cluster Bootstrap Resampling (B = 10,000 iterations, seed = 42). Preserves within-match delivery dependencies.
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-center">
                  <div className="p-3 bg-white rounded-lg border border-rr-border">
                    <span className="text-[11px] font-bold text-rr-muted uppercase">Observed Difference (&Delta;)</span>
                    <div className="text-xl font-extrabold text-rr-charcoal mt-1 font-heading">
                      {typeof boot.observed_difference === 'number'
                        ? (boot.observed_difference > 0 ? `+${boot.observed_difference.toFixed(2)}` : boot.observed_difference.toFixed(2))
                        : '-'}
                    </div>
                    <span className="text-[10px] text-rr-muted">{discipline === 'BATTER' ? 'SR Points' : 'Economy Rate'}</span>
                  </div>

                  <div className="p-3 bg-white rounded-lg border border-rr-border">
                    <span className="text-[11px] font-bold text-rr-muted uppercase">Bootstrap Std Error</span>
                    <div className="text-xl font-extrabold text-rr-charcoal mt-1 font-heading">
                      {typeof boot.bootstrap_se_10k === 'number' ? boot.bootstrap_se_10k.toFixed(2) : '-'}
                    </div>
                    <span className="text-[10px] text-rr-muted">Across 10k cluster resamples</span>
                  </div>

                  <div className="p-3 bg-white rounded-lg border border-rr-border sm:col-span-2">
                    <span className="text-[11px] font-bold text-rr-muted uppercase">95% Bootstrap Confidence Interval</span>
                    <div className="text-xl font-extrabold text-rr-pink mt-1 font-heading">
                      {typeof boot.bootstrap_ci_95_lower === 'number' && typeof boot.bootstrap_ci_95_upper === 'number'
                        ? `[${boot.bootstrap_ci_95_lower.toFixed(2)}, ${boot.bootstrap_ci_95_upper > 0 ? `+${boot.bootstrap_ci_95_upper.toFixed(2)}` : boot.bootstrap_ci_95_upper.toFixed(2)}]`
                        : '-'}
                    </div>
                    <span className="text-[10px] text-rr-muted">
                      {boot.bootstrap_ci_95_lower <= 0 && boot.bootstrap_ci_95_upper >= 0
                        ? 'Interval spans zero &rarr; Statistical superiority has NOT been established at 95% level'
                        : 'Interval excludes zero &rarr; Statistically significant separation established at 95% level'}
                    </span>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-white border border-rr-border flex items-start gap-3">
                  {boot.bootstrap_ci_95_lower <= 0 && boot.bootstrap_ci_95_upper >= 0 ? (
                    <HelpCircle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                  ) : (
                    <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                  )}
                  <div>
                    <h5 className="text-xs font-bold text-rr-charcoal font-heading">
                      Analytical Verdict: {boot.bootstrap_ci_95_lower <= 0 && boot.bootstrap_ci_95_upper >= 0
                        ? 'Statistical superiority not established (Interval spans 0)'
                        : 'Statistically significant separation confirmed at 95% level'}
                    </h5>
                    <p className="text-xs text-rr-muted mt-1 leading-relaxed">
                      {boot.bootstrap_ci_95_lower <= 0 && boot.bootstrap_ci_95_upper >= 0
                        ? `The 95% bootstrap confidence interval spans zero; statistical superiority has NOT been established between ${pA.player_name} and ${pB.player_name}. Relative ranking represents an explicit strategic franchise judgement between nearby candidates rather than statistical certainty.`
                        : boot.observed_difference < 0
                        ? `The 95% bootstrap confidence interval excludes zero and is entirely negative (${boot.bootstrap_ci_95_lower.toFixed(2)} to ${boot.bootstrap_ci_95_upper.toFixed(2)}), confirming that ${pB.player_name}'s observed rate is statistically higher than ${pA.player_name}'s under match-cluster resampling. ${pA.player_name}'s higher placement (#${pA.top_10_rank} vs #${pB.top_10_rank}) is strictly a tactical reliability and sample-volume decision prioritizing multi-season stability over small-sample breakout upside.`
                        : `The 95% bootstrap confidence interval excludes zero, confirming genuine statistical separation between ${pA.player_name} and ${pB.player_name} under match-cluster resampling.`}
                    </p>
                  </div>
                </div>
              </div>
            ) : comparison?.curated_h2h ? (
              <div className="p-4 rounded-xl bg-rr-palePink/60 border border-pink-200 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-rr-deepPink font-heading uppercase tracking-wider flex items-center gap-1.5">
                    <Swords className="w-3.5 h-3.5" />
                    Curated Franchise Head-to-Head Profile ({comparison.curated_h2h.profile_id})
                  </span>
                  <span className="text-[10px] font-bold text-rr-muted">
                    95% CI: [{comparison.curated_h2h.bootstrap_ci_95_lower?.toFixed(1)}, {comparison.curated_h2h.bootstrap_ci_95_upper?.toFixed(1)}]
                  </span>
                </div>
                <p className="text-xs text-rr-charcoal leading-relaxed">
                  {comparison.curated_h2h.tactical_tradeoff_evidence}
                </p>
              </div>
            ) : (
              <div className="p-5 rounded-xl bg-amber-50/50 border border-amber-200/80 space-y-3">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-900 border border-amber-200">
                    Methodological Disclosure: Non-Adjacent Candidate Comparison
                  </span>
                </div>
                <p className="text-xs text-rr-charcoal leading-relaxed">
                  Pairwise match-cluster bootstrap resampling is strictly precomputed for <strong>adjacent Top-10 candidates</strong> (e.g., Rank 1 vs 2, 2 vs 3). For non-adjacent candidate pairs like <strong>{pA.player_name}</strong> and <strong>{pB.player_name}</strong>, <strong>no direct pairwise bootstrap inference is available</strong>.
                </p>
                <div className="p-3 bg-white rounded-lg border border-amber-200 text-xs text-amber-950 space-y-1.5 leading-relaxed">
                  <div className="font-semibold flex items-center gap-1.5 text-amber-900">
                    <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                    Important Statistical Distinction:
                  </div>
                  <p>
                    &bull; <strong>Individual parameter credible intervals are NOT pairwise difference intervals.</strong> Individual bounds quantify single-player estimation variance under prior weights (M &isin; [25, 45, 60, 90]), not the distribution of differences between two players.
                  </p>
                  <p>
                    &bull; <strong>Do not infer statistical equivalence or superiority from overlapping individual intervals.</strong> Overlapping marginal intervals do not establish that two players are statistically indistinguishable, nor do non-overlapping bounds substitute for a joint pairwise significance test.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* 3. Comprehensive Side-by-Side Candidate Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Candidate A Card */}
            <div className="bg-white rounded-2xl border-2 border-rr-pink/50 p-6 shadow-rr-card space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-rr-border">
                <div className="flex items-center gap-3.5">
                  <PlayerAvatar
                    playerId={pA.player_id}
                    playerName={pA.player_name}
                    size="lg"
                    isTop10={!!pA.top_10_rank}
                  />
                  <div>
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-rr-softPink text-rr-deepPink">
                      Candidate A
                    </span>
                    <h3 className="text-2xl font-extrabold text-rr-charcoal font-heading mt-1">
                      {pA.player_name}
                    </h3>
                    <p className="text-xs text-rr-muted">{pA.primary_role} • Rank #{pA.top_10_rank || '-'}</p>
                  </div>
                </div>
                <div className="text-right space-y-1">
                  <TierBadge tier={pA.evidence_tier} />
                  <div><ArchetypeBadge archetype={pA.stability_archetype} /></div>
                </div>
              </div>

              {/* Pressure Performance Metrics */}
              <div className="space-y-1.5 text-xs">
                <span className="font-bold text-rr-muted uppercase text-[10px] tracking-wider block">1. Pressure Performance</span>
                <div className="p-2.5 rounded-lg bg-rr-warmWhite flex justify-between">
                  <span className="text-rr-muted">IPL Exposure:</span>
                  <span className="font-bold text-rr-charcoal">{pA.ipl_pressure_volume || 0} balls ({pA.ipl_matches || 0} matches)</span>
                </div>
                <div className="p-2.5 rounded-lg bg-rr-warmWhite flex justify-between">
                  <span className="text-rr-muted">Senior T20I Exposure:</span>
                  <span className="font-bold text-rr-charcoal">{pA.t20i_pressure_volume || 0} balls ({pA.t20i_matches || 0} matches)</span>
                </div>
                <div className="p-2.5 rounded-lg bg-rr-palePink border border-pink-100 flex justify-between">
                  <span className="font-bold text-rr-charcoal">
                    {discipline === 'BATTER' ? 'IPL Shrunk SR (M=45):' : 'IPL Raw Economy:'}
                  </span>
                  <span className="font-extrabold text-rr-pink text-sm">
                    {discipline === 'BATTER' ? pA.ipl_shrunk_m45?.toFixed(1) : pA.ipl_raw_econ?.toFixed(2)}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-rr-warmWhite flex justify-between">
                  <span className="text-rr-muted">
                    {discipline === 'BATTER' ? 'Context RAE (ΔSR):' : 'All-Runs RCAE (ΔEcon):'}
                  </span>
                  <span className="font-bold text-emerald-600">
                    {discipline === 'BATTER' ? `+${pA.ipl_context_delta_sr?.toFixed(1)}` : pA.ipl_context_delta_econ?.toFixed(2)}
                  </span>
                </div>
                {discipline === 'BOWLER' && typeof pA.ipl_legal_context_delta_econ === 'number' && (
                  <div className="p-2 rounded-lg bg-slate-50 flex justify-between text-[11px]">
                    <span className="text-rr-muted">Legal-Ball RCAE (ΔLegal):</span>
                    <span className="font-medium text-slate-600">{pA.ipl_legal_context_delta_econ.toFixed(2)}</span>
                  </div>
                )}
                <div className="p-2.5 rounded-lg bg-rr-warmWhite flex justify-between">
                  <span className="text-rr-muted">Dot % / Boundary %:</span>
                  <span className="font-bold text-rr-charcoal">
                    {discipline === 'BATTER'
                      ? `${pA.ipl_dot_ball_pct}% / ${pA.ipl_boundary_ball_pct}%`
                      : `${pA.ipl_dot_ball_pct}% / ${pA.ipl_boundary_concession_pct}%`}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-rr-warmWhite flex justify-between">
                  <span className="text-rr-muted">Match Pass Rate:</span>
                  <span className="font-bold text-rr-charcoal">{pA.ipl_match_pass_rate?.toFixed(1)}%</span>
                </div>
              </div>

              {/* Machine Learning Context */}
              <div className="space-y-1.5 text-xs pt-1 border-t border-rr-border">
                <span className="font-bold text-indigo-900 uppercase text-[10px] tracking-wider block flex items-center gap-1">
                  <Brain className="w-3 h-3 text-indigo-600" />
                  2. ML Contextual Outperformance (2026 Test Deliveries)
                </span>
                {comparison?.player_a?.ml_context && comparison.player_a.ml_context.test_eval_deliveries > 0 ? (
                  <div className="p-2.5 rounded-lg bg-indigo-50/60 border border-indigo-100 space-y-1">
                    <div className="flex justify-between">
                      <span className="text-indigo-800">Evaluated Holdout Balls:</span>
                      <span className="font-bold text-indigo-950">{comparison.player_a.ml_context.test_eval_deliveries} deliveries</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-indigo-800">
                        {discipline === 'BATTER' ? 'Actual vs Expected Runs:' : 'Actual vs Expected Conceded:'}
                      </span>
                      <span className="font-bold text-indigo-950">
                        {discipline === 'BATTER'
                          ? `${comparison.player_a.ml_context.actual_runs} vs ${comparison.player_a.ml_context.expected_runs_lightgbm}`
                          : `${comparison.player_a.ml_context.actual_runs_conceded} vs ${comparison.player_a.ml_context.expected_runs_lightgbm}`}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-indigo-800 font-bold">
                        {discipline === 'BATTER' ? 'Net Residual Runs Added:' : 'Defensive Suppression / Over:'}
                      </span>
                      <span className="font-extrabold text-emerald-600">
                        {discipline === 'BATTER'
                          ? (comparison.player_a.ml_context.net_residual ? `+${comparison.player_a.ml_context.net_residual}` : '-')
                          : (comparison.player_a.ml_context.suppression_per_over ? `-${comparison.player_a.ml_context.suppression_per_over.toFixed(2)}` : '-')}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="p-2 bg-slate-50 rounded-lg text-[11px] text-slate-500">
                    Historical cohort; 0 deliveries in 2026 holdout partition.
                  </div>
                )}
              </div>

              {/* Behavioral Response Dynamics */}
              <div className="space-y-1.5 text-xs pt-1 border-t border-rr-border">
                <span className="font-bold text-amber-900 uppercase text-[10px] tracking-wider block flex items-center gap-1">
                  <Zap className="w-3 h-3 text-amber-600" />
                  3. Behavioral Response Dynamics
                </span>
                {comparison?.player_a?.behavioral ? (
                  <div className="p-2.5 rounded-lg bg-amber-50/60 border border-amber-100 space-y-1">
                    <div className="flex justify-between">
                      <span className="text-amber-800">
                        {discipline === 'BATTER' ? 'Scoring Resilience Index (SRI):' : 'Bounceback Index:'}
                      </span>
                      <span className="font-extrabold text-rr-deepPink">
                        {discipline === 'BATTER'
                          ? comparison.player_a.behavioral.scoring_resilience_index
                          : comparison.player_a.behavioral.bounceback_index?.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-amber-800">
                        {discipline === 'BATTER' ? 'Drought-State SR (Streak >= 2):' : 'Post-Boundary Economy (t+1):'}
                      </span>
                      <span className="font-bold text-rr-charcoal">
                        {discipline === 'BATTER'
                          ? `${comparison.player_a.behavioral.post_dot_strike_rate} SR`
                          : `${comparison.player_a.behavioral.post_boundary_economy?.toFixed(2)} Econ`}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-amber-800">
                        {discipline === 'BATTER' ? 'Avg Balls to Scoring Shot:' : 'Early vs Late Spell Drift:'}
                      </span>
                      <span className="font-semibold text-rr-charcoal">
                        {discipline === 'BATTER'
                          ? `${comparison.player_a.behavioral.avg_balls_to_scoring} balls`
                          : `${comparison.player_a.behavioral.spell_economy_progression?.toFixed(2)} Econ`}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="p-2 bg-slate-50 rounded-lg text-[11px] text-slate-500">
                    Insufficient trigger sequences for behavioral profiling.
                  </div>
                )}
              </div>

              {/* Reliability & Risk Flags */}
              <div className="space-y-1.5 text-xs pt-1 border-t border-rr-border">
                <span className="font-bold text-rr-muted uppercase text-[10px] tracking-wider block flex items-center gap-1">
                  <Scale className="w-3 h-3 text-rr-muted" />
                  4. Reliability & Risk Vulnerabilities
                </span>
                <div className="p-2.5 rounded-lg bg-rr-warmWhite space-y-1">
                  <div className="flex justify-between">
                    <span className="text-rr-muted">Identified Risk Severity:</span>
                    <span className="font-bold text-rr-charcoal">
                      {comparison?.player_a?.reliability?.risk_flags?.[0]?.risk_severity || 'LOW_RISK'}
                    </span>
                  </div>
                  {comparison?.player_a?.reliability?.risk_flags?.[0]?.risk_notes && (
                    <p className="text-[10px] text-rr-muted mt-1 leading-relaxed">
                      {comparison.player_a.reliability.risk_flags[0].risk_notes}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Candidate B Card */}
            <div className="bg-white rounded-2xl border-2 border-rr-border p-6 shadow-rr-card space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-rr-border">
                <div className="flex items-center gap-3.5">
                  <PlayerAvatar
                    playerId={pB.player_id}
                    playerName={pB.player_name}
                    size="lg"
                    isTop10={!!pB.top_10_rank}
                  />
                  <div>
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-gray-100 text-rr-charcoal">
                      Candidate B
                    </span>
                    <h3 className="text-2xl font-extrabold text-rr-charcoal font-heading mt-1">
                      {pB.player_name}
                    </h3>
                    <p className="text-xs text-rr-muted">{pB.primary_role} • Rank #{pB.top_10_rank || '-'}</p>
                  </div>
                </div>
                <div className="text-right space-y-1">
                  <TierBadge tier={pB.evidence_tier} />
                  <div><ArchetypeBadge archetype={pB.stability_archetype} /></div>
                </div>
              </div>

              {/* Pressure Performance Metrics */}
              <div className="space-y-1.5 text-xs">
                <span className="font-bold text-rr-muted uppercase text-[10px] tracking-wider block">1. Pressure Performance</span>
                <div className="p-2.5 rounded-lg bg-rr-warmWhite flex justify-between">
                  <span className="text-rr-muted">IPL Exposure:</span>
                  <span className="font-bold text-rr-charcoal">{pB.ipl_pressure_volume || 0} balls ({pB.ipl_matches || 0} matches)</span>
                </div>
                <div className="p-2.5 rounded-lg bg-rr-warmWhite flex justify-between">
                  <span className="text-rr-muted">Senior T20I Exposure:</span>
                  <span className="font-bold text-rr-charcoal">{pB.t20i_pressure_volume || 0} balls ({pB.t20i_matches || 0} matches)</span>
                </div>
                <div className="p-2.5 rounded-lg bg-rr-palePink border border-pink-100 flex justify-between">
                  <span className="font-bold text-rr-charcoal">
                    {discipline === 'BATTER' ? 'IPL Shrunk SR (M=45):' : 'IPL Raw Economy:'}
                  </span>
                  <span className="font-extrabold text-rr-pink text-sm">
                    {discipline === 'BATTER' ? pB.ipl_shrunk_m45?.toFixed(1) : pB.ipl_raw_econ?.toFixed(2)}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-rr-warmWhite flex justify-between">
                  <span className="text-rr-muted">
                    {discipline === 'BATTER' ? 'Context RAE (ΔSR):' : 'All-Runs RCAE (ΔEcon):'}
                  </span>
                  <span className="font-bold text-emerald-600">
                    {discipline === 'BATTER' ? `+${pB.ipl_context_delta_sr?.toFixed(1)}` : pB.ipl_context_delta_econ?.toFixed(2)}
                  </span>
                </div>
                {discipline === 'BOWLER' && typeof pB.ipl_legal_context_delta_econ === 'number' && (
                  <div className="p-2 rounded-lg bg-slate-50 flex justify-between text-[11px]">
                    <span className="text-rr-muted">Legal-Ball RCAE (ΔLegal):</span>
                    <span className="font-medium text-slate-600">{pB.ipl_legal_context_delta_econ.toFixed(2)}</span>
                  </div>
                )}
                <div className="p-2.5 rounded-lg bg-rr-warmWhite flex justify-between">
                  <span className="text-rr-muted">Dot % / Boundary %:</span>
                  <span className="font-bold text-rr-charcoal">
                    {discipline === 'BATTER'
                      ? `${pB.ipl_dot_ball_pct}% / ${pB.ipl_boundary_ball_pct}%`
                      : `${pB.ipl_dot_ball_pct}% / ${pB.ipl_boundary_concession_pct}%`}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-rr-warmWhite flex justify-between">
                  <span className="text-rr-muted">Match Pass Rate:</span>
                  <span className="font-bold text-rr-charcoal">{pB.ipl_match_pass_rate?.toFixed(1)}%</span>
                </div>
              </div>

              {/* Machine Learning Context */}
              <div className="space-y-1.5 text-xs pt-1 border-t border-rr-border">
                <span className="font-bold text-indigo-900 uppercase text-[10px] tracking-wider block flex items-center gap-1">
                  <Brain className="w-3 h-3 text-indigo-600" />
                  2. ML Contextual Outperformance (2026 Test Deliveries)
                </span>
                {comparison?.player_b?.ml_context && comparison.player_b.ml_context.test_eval_deliveries > 0 ? (
                  <div className="p-2.5 rounded-lg bg-indigo-50/60 border border-indigo-100 space-y-1">
                    <div className="flex justify-between">
                      <span className="text-indigo-800">Evaluated Holdout Balls:</span>
                      <span className="font-bold text-indigo-950">{comparison.player_b.ml_context.test_eval_deliveries} deliveries</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-indigo-800">
                        {discipline === 'BATTER' ? 'Actual vs Expected Runs:' : 'Actual vs Expected Conceded:'}
                      </span>
                      <span className="font-bold text-indigo-950">
                        {discipline === 'BATTER'
                          ? `${comparison.player_b.ml_context.actual_runs} vs ${comparison.player_b.ml_context.expected_runs_lightgbm}`
                          : `${comparison.player_b.ml_context.actual_runs_conceded} vs ${comparison.player_b.ml_context.expected_runs_lightgbm}`}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-indigo-800 font-bold">
                        {discipline === 'BATTER' ? 'Net Residual Runs Added:' : 'Defensive Suppression / Over:'}
                      </span>
                      <span className="font-extrabold text-emerald-600">
                        {discipline === 'BATTER'
                          ? (comparison.player_b.ml_context.net_residual ? `+${comparison.player_b.ml_context.net_residual}` : '-')
                          : (comparison.player_b.ml_context.suppression_per_over ? `-${comparison.player_b.ml_context.suppression_per_over.toFixed(2)}` : '-')}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="p-2 bg-slate-50 rounded-lg text-[11px] text-slate-500">
                    Historical cohort; 0 deliveries in 2026 holdout partition.
                  </div>
                )}
              </div>

              {/* Behavioral Response Dynamics */}
              <div className="space-y-1.5 text-xs pt-1 border-t border-rr-border">
                <span className="font-bold text-amber-900 uppercase text-[10px] tracking-wider block flex items-center gap-1">
                  <Zap className="w-3 h-3 text-amber-600" />
                  3. Behavioral Response Dynamics
                </span>
                {comparison?.player_b?.behavioral ? (
                  <div className="p-2.5 rounded-lg bg-amber-50/60 border border-amber-100 space-y-1">
                    <div className="flex justify-between">
                      <span className="text-amber-800">
                        {discipline === 'BATTER' ? 'Scoring Resilience Index (SRI):' : 'Bounceback Index:'}
                      </span>
                      <span className="font-extrabold text-rr-deepPink">
                        {discipline === 'BATTER'
                          ? comparison.player_b.behavioral.scoring_resilience_index
                          : comparison.player_b.behavioral.bounceback_index?.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-amber-800">
                        {discipline === 'BATTER' ? 'Drought-State SR (Streak >= 2):' : 'Post-Boundary Economy (t+1):'}
                      </span>
                      <span className="font-bold text-rr-charcoal">
                        {discipline === 'BATTER'
                          ? `${comparison.player_b.behavioral.post_dot_strike_rate} SR`
                          : `${comparison.player_b.behavioral.post_boundary_economy?.toFixed(2)} Econ`}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-amber-800">
                        {discipline === 'BATTER' ? 'Avg Balls to Scoring Shot:' : 'Early vs Late Spell Drift:'}
                      </span>
                      <span className="font-semibold text-rr-charcoal">
                        {discipline === 'BATTER'
                          ? `${comparison.player_b.behavioral.avg_balls_to_scoring} balls`
                          : `${comparison.player_b.behavioral.spell_economy_progression?.toFixed(2)} Econ`}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="p-2 bg-slate-50 rounded-lg text-[11px] text-slate-500">
                    Insufficient trigger sequences for behavioral profiling.
                  </div>
                )}
              </div>

              {/* Reliability & Risk Flags */}
              <div className="space-y-1.5 text-xs pt-1 border-t border-rr-border">
                <span className="font-bold text-rr-muted uppercase text-[10px] tracking-wider block flex items-center gap-1">
                  <Scale className="w-3 h-3 text-rr-muted" />
                  4. Reliability & Risk Vulnerabilities
                </span>
                <div className="p-2.5 rounded-lg bg-rr-warmWhite space-y-1">
                  <div className="flex justify-between">
                    <span className="text-rr-muted">Identified Risk Severity:</span>
                    <span className="font-bold text-rr-charcoal">
                      {comparison?.player_b?.reliability?.risk_flags?.[0]?.risk_severity || 'LOW_RISK'}
                    </span>
                  </div>
                  {comparison?.player_b?.reliability?.risk_flags?.[0]?.risk_notes && (
                    <p className="text-[10px] text-rr-muted mt-1 leading-relaxed">
                      {comparison.player_b.reliability.risk_flags[0].risk_notes}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

