import React, { useState } from 'react';
import { SectionHeading } from '../components/common/SectionHeading';
import { PageHeroCard } from '../components/common/PageHeroCard';
import { MathView } from '../components/MathView';
import { 
  GitBranch, 
  Layers, 
  Sigma, 
  ShieldAlert, 
  CheckCircle2, 
  Scale, 
  Database,
  ArrowRight,
  Info,
  TrendingDown,
  Cpu
} from 'lucide-react';

export const MethodologyLab: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'pipeline' | 'shrinkage' | 'tiers' | 'disclosures'>('pipeline');
  const [selectedM, setSelectedM] = useState<number>(45);

  const shrinkageExamples = [
    {
      player: 'Tim David',
      archetype: 'ROBUST_ANCHOR',
      rawSR: 175.4,
      balls: 334,
      m25: 172.7,
      m45: 170.7,
      m60: 169.3,
      m90: 166.9,
      retention: '97.3%',
      verdict: 'Proven multi-format finisher; high volume retains 97.3% of raw strike rate'
    },
    {
      player: 'Suryakumar Yadav',
      archetype: 'ROBUST_ANCHOR',
      rawSR: 163.7,
      balls: 579,
      m25: 162.5,
      m45: 161.7,
      m60: 161.0,
      m90: 159.9,
      retention: '98.8%',
      verdict: 'Massive 579-ball IPL pressure sample virtually impervious to prior shrinkage'
    },
    {
      player: 'Nicholas Pooran',
      archetype: 'ROBUST_ANCHOR',
      rawSR: 166.6,
      balls: 491,
      m25: 165.1,
      m45: 164.0,
      m60: 163.2,
      m90: 161.7,
      retention: '98.4%',
      verdict: 'Multi-season middle-overs anchor with high sample stability across franchises'
    },
    {
      player: 'Vaibhav Sooryavanshi',
      archetype: 'DISCOVERY_UPSIDE',
      rawSR: 231.6,
      balls: 76,
      m25: 207.8,
      m45: 195.8,
      m60: 187.9,
      m90: 178.1,
      retention: '84.5%',
      verdict: 'Tournament-high raw strike rate regressed towards prior; retains #1 shrunk SR (195.8) at M=45'
    }
  ];

  return (
    <div className="space-y-8 pb-12">
      {/* Standardized Compact Hero Section */}
      <PageHeroCard
        badge="Analytical Standards"
        badgeIcon={<Layers className="w-3.5 h-3.5 text-rr-pink" />}
        title="Methodology & Analytical Architecture"
        description="Mathematical architecture, Empirical Bayes shrinkage, bootstrap inference, and data governance standards powering RR EDGE."
      />

      {/* Navigation Tabs */}
      <div className="flex border-b border-rr-border space-x-8">
        <button
          onClick={() => setActiveTab('pipeline')}
          className={`pb-4 px-1 flex items-center gap-2 text-sm font-semibold transition-colors border-b-2 ${
            activeTab === 'pipeline'
              ? 'border-rr-pink text-rr-pink'
              : 'border-transparent text-rr-muted hover:text-rr-charcoal'
          }`}
        >
          <Layers className="w-4 h-4" />
          4-Phase Evaluation Engine
        </button>
        <button
          onClick={() => setActiveTab('shrinkage')}
          className={`pb-4 px-1 flex items-center gap-2 text-sm font-semibold transition-colors border-b-2 ${
            activeTab === 'shrinkage'
              ? 'border-rr-pink text-rr-pink'
              : 'border-transparent text-rr-muted hover:text-rr-charcoal'
          }`}
        >
          <Sigma className="w-4 h-4" />
          Empirical Bayes Shrinkage
        </button>
        <button
          onClick={() => setActiveTab('tiers')}
          className={`pb-4 px-1 flex items-center gap-2 text-sm font-semibold transition-colors border-b-2 ${
            activeTab === 'tiers'
              ? 'border-rr-pink text-rr-pink'
              : 'border-transparent text-rr-muted hover:text-rr-charcoal'
          }`}
        >
          <Scale className="w-4 h-4" />
          Evidence Tier Rubric
        </button>
        <button
          onClick={() => setActiveTab('disclosures')}
          className={`pb-4 px-1 flex items-center gap-2 text-sm font-semibold transition-colors border-b-2 ${
            activeTab === 'disclosures'
              ? 'border-rr-pink text-rr-pink'
              : 'border-transparent text-rr-muted hover:text-rr-charcoal'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          Governance & Exclusions
        </button>
      </div>

      {/* Tab 1: 4-Phase Evaluation Pipeline */}
      {activeTab === 'pipeline' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-xl border border-rr-border shadow-card relative">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-rr-pink uppercase tracking-wider">Phase 01</span>
                <Database className="w-4 h-4 text-rr-muted" />
              </div>
              <h3 className="text-base font-bold text-rr-charcoal mb-2">State Reconstruction</h3>
              <p className="text-xs text-rr-muted leading-relaxed">
                Reconstructs ball-by-ball game states: Required Run Rate (RRR), balls remaining, wickets in hand, innings leverage, and target context.
              </p>
            </div>

            <div className="bg-white p-5 rounded-xl border border-rr-border shadow-card relative">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-rr-pink uppercase tracking-wider">Phase 02</span>
                <Cpu className="w-4 h-4 text-rr-muted" />
              </div>
              <h3 className="text-base font-bold text-rr-charcoal mb-2">Pressure Engine</h3>
              <p className="text-xs text-rr-muted leading-relaxed">
                Applies rule-based asymmetric contextual thresholds. Tiers every ball into Low, Moderate, High, or Extreme pressure regimes.
              </p>
            </div>

            <div className="bg-white p-5 rounded-xl border border-rr-border shadow-card relative">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-rr-pink uppercase tracking-wider">Phase 03</span>
                <TrendingDown className="w-4 h-4 text-rr-muted" />
              </div>
              <h3 className="text-base font-bold text-rr-charcoal mb-2">Context Efficiencies</h3>
              <p className="text-xs text-rr-muted leading-relaxed">
                Computes Relative Attacking Efficiency (RAE) for batters and Concession Efficiency (RCAE) for bowlers conditioned on competition type, innings phase, and wickets bucket.
              </p>
            </div>

            <div className="bg-white p-5 rounded-xl border border-rr-border shadow-card relative">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-rr-pink uppercase tracking-wider">Phase 04</span>
                <Sigma className="w-4 h-4 text-rr-muted" />
              </div>
              <h3 className="text-base font-bold text-rr-charcoal mb-2">Bayesian & Bootstrap</h3>
              <p className="text-xs text-rr-muted leading-relaxed">
                Applies Empirical Bayes shrinkage (<MathView math="M \in \{25, 45, 60, 90\}" />) and <MathView math="B=10{,}000" /> cluster-aware bootstrap resampling for statistically rigorous ranking.
              </p>
            </div>
          </div>

          {/* Mathematical Formulations Card */}
          <div className="bg-white p-6 rounded-xl border border-rr-border shadow-card space-y-6">
            <h3 className="text-base font-bold text-rr-charcoal flex items-center gap-2">
              <Sigma className="w-5 h-5 text-rr-pink" />
              Formal Mathematical Formulations & Production Rule Engine
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-rr-pale p-5 rounded-lg border border-rr-soft">
                <h4 className="text-xs font-bold text-rr-deep uppercase tracking-wider mb-2">1. Asymmetric Rule-Based Pressure Architecture</h4>
                <div className="bg-white p-3.5 rounded-lg border border-rr-border space-y-2.5 mb-3 shadow-subtle text-rr-charcoal">
                  <div className="border-b border-rr-soft/50 pb-2">
                    <div className="text-[10.5px] font-bold text-rr-deep uppercase tracking-wider mb-1">Chase Batter — Extreme Pressure:</div>
                    <div className="bg-rr-warm p-2 rounded border border-rr-border/60">
                      <MathView
                        block
                        math={`\\mathrm{RRR} \\ge 14.0 \\;\\lor\\; \\Delta\\mathrm{RRR} \\ge 6.0 \\;\\lor\\; (\\mathrm{RRR} \\ge 12.0 \\land W \\le 3) \\;\\lor\\; (B_{\\mathrm{rem}} \\le 18 \\land \\mathrm{RRR} \\ge 11.0 \\land W \\le 4)`}
                      />
                    </div>
                  </div>
                  <div className="border-b border-rr-soft/50 pb-2">
                    <div className="text-[10.5px] font-bold text-rr-deep uppercase tracking-wider mb-1">Chase Batter — High Pressure:</div>
                    <div className="bg-rr-warm p-2 rounded border border-rr-border/60">
                      <MathView
                        block
                        math={`\\mathrm{RRR} \\ge 10.5 \\;\\lor\\; \\Delta\\mathrm{RRR} \\ge 2.5 \\;\\lor\\; (W \\le 3 \\land B_{\\mathrm{rem}} \\le 36) \\;\\lor\\; (\\mathrm{RRR} \\ge 9.5 \\land \\mathrm{Dots}_6 \\ge 4)`}
                      />
                    </div>
                  </div>
                  <div className="border-b border-rr-soft/50 pb-2">
                    <div className="text-[10.5px] font-bold text-rr-deep uppercase tracking-wider mb-1">1st Innings Batter — Par Deficit:</div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      <div className="bg-rr-warm p-1.5 rounded border border-rr-border/60">
                        <span className="text-[9.5px] font-bold text-rr-pink block mb-0.5">EXTREME TIER</span>
                        <MathView
                          block
                          math={`\\Delta_{\\mathrm{Par}} \\ge 25.0 \\;\\lor\\; (\\Delta_{\\mathrm{Par}} \\ge 15.0 \\land W \\le 3)`}
                        />
                      </div>
                      <div className="bg-rr-warm p-1.5 rounded border border-rr-border/60">
                        <span className="text-[9.5px] font-bold text-blue-600 block mb-0.5">HIGH TIER</span>
                        <MathView
                          block
                          math={`\\Delta_{\\mathrm{Par}} \\ge 15.0 \\;\\lor\\; (W \\le 3 \\land B_{\\mathrm{rem}} \\le 36)`}
                        />
                      </div>
                    </div>
                  </div>
                  <div>
                    <div className="text-[10.5px] font-bold text-rr-deep uppercase tracking-wider mb-1">Bowler Defense — Asymmetric Context:</div>
                    <div className="space-y-1">
                      <div className="bg-rr-warm p-1.5 px-2.5 rounded border border-rr-border/60 flex items-center justify-between text-xs">
                        <span className="text-[11px] font-semibold text-rr-charcoal">Acute Margin:</span>
                        <MathView math={`(B_{\\mathrm{rem}} \\le 12 \\land \\mathrm{Runs}_{\\mathrm{rem}} \\le 18) \\implies \\mathbf{EXTREME}`} />
                      </div>
                      <div className="bg-rr-warm p-1.5 px-2.5 rounded border border-rr-border/60 flex items-center justify-between text-xs">
                        <span className="text-[11px] font-semibold text-rr-charcoal">High Firepower:</span>
                        <MathView math={`(\\mathrm{RRR} \\ge 13.0 \\land W \\ge 6) \\implies \\mathbf{EXTREME}`} />
                      </div>
                      <div className="bg-rr-warm p-1.5 px-2.5 rounded border border-rr-border/60 flex items-center justify-between text-xs">
                        <span className="text-[11px] font-semibold text-rr-charcoal">Tail Dominance:</span>
                        <MathView math={`(\\mathrm{RRR} \\ge 12.0 \\land W \\le 2) \\implies \\mathbf{LOW}`} />
                      </div>
                    </div>
                  </div>
                </div>
                <div className="text-[11px] text-rr-muted space-y-1.5 leading-relaxed">
                  <p>
                    <strong>Execution Order & Multiplier Verification:</strong> Implemented in <code className="font-mono text-rr-deep">src/cricket/pressure_engine.py</code>. Evaluation executes sequentially: (1) Acute chase death leverage, (2) Wicket crisis / collapse, (3) RRR departure, (4) First-innings par deficit.
                  </p>
                  <p>
                    <strong>First-Innings Resource Model:</strong> In innings 1, pressure leverage uses <code className="font-mono text-rr-deep">FirstInningsResourceModel</code> estimating <MathView math={`\\mathbb{E}[\\mathrm{Remaining\\;Runs} \\mid \\mathrm{Over\\;Bucket},\\; \\mathrm{Wickets\\;Lost},\\; \\mathrm{Competition}]`} />. Conditioning variables are strictly:
                  </p>
                  <ul className="list-disc list-inside space-y-0.5 ml-2 font-semibold text-rr-charcoal">
                    <li>Competition (IPL benchmark: 183.0, Senior T20I: 165.2)</li>
                    <li>Over bucket (legal balls // 6)</li>
                    <li>Wickets lost</li>
                  </ul>
                  <p className="text-amber-900 font-medium">
                    <em>The first-innings resource grid does not use innings-phase conditioning.</em>
                  </p>
                  <p>
                    <strong>Knockout Stage & Phase Verification:</strong> Match phase (POWERPLAY, MIDDLE, DEATH) serves as discrete categorical thresholds in chase rules. Knockout stage status (<code className="font-mono text-rr-deep">is_knockout</code>) is retained strictly as a metadata filtering attribute. <em>There are zero mathematical multipliers</em> applied to pressure scores in the production pipeline.
                  </p>
                </div>
              </div>

              <div className="bg-rr-pale p-5 rounded-lg border border-rr-soft">
                <h4 className="text-xs font-bold text-rr-deep uppercase tracking-wider mb-2">2. Empirical Bayes Shrinkage</h4>
                <div className="bg-white p-4 rounded-lg border border-rr-border mb-3 shadow-subtle">
                  <div className="bg-rr-warm p-3 rounded-md border border-rr-border/60 text-center mb-3">
                    <MathView
                      block
                      math={`\\theta_i^* = w_i \\cdot \\hat{\\theta}_i + (1 - w_i) \\cdot \\mu_0 \\qquad \\text{where} \\qquad w_i = \\frac{N_i}{N_i + M}`}
                    />
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px] text-rr-charcoal pt-1">
                    <div className="bg-rr-pale p-2 rounded border border-rr-soft text-center">
                      <MathView math={`\\hat{\\theta}_i`} className="font-bold text-rr-deep" />
                      <div className="text-[10px] text-rr-muted mt-0.5">Observed Raw SR</div>
                    </div>
                    <div className="bg-rr-pale p-2 rounded border border-rr-soft text-center">
                      <MathView math={`\\mu_0 = 135.2`} className="font-bold text-rr-deep" />
                      <div className="text-[10px] text-rr-muted mt-0.5">IPL Grand Mean</div>
                    </div>
                    <div className="bg-rr-pale p-2 rounded border border-rr-soft text-center">
                      <MathView math={`N_i`} className="font-bold text-rr-deep" />
                      <div className="text-[10px] text-rr-muted mt-0.5">Pressure Balls Faced</div>
                    </div>
                    <div className="bg-rr-pale p-2 rounded border border-rr-soft text-center">
                      <MathView math={`M = 45`} className="font-bold text-rr-deep" />
                      <div className="text-[10px] text-rr-muted mt-0.5">Prior Sample Weight</div>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-rr-muted leading-relaxed">
                  Here, <MathView math={`\\hat{\\theta}_i`} /> is the raw observed strike rate, <MathView math={`\\mu_0`} /> is the cohort empirical grand mean (135.2 in IPL), <MathView math={`N_i`} /> is sample balls faced under pressure, and <MathView math={`M`} /> is the shrinkage parameter representing prior sample weight.
                </p>
              </div>

              <div className="bg-rr-pale p-5 rounded-lg border border-rr-soft">
                <h4 className="text-xs font-bold text-rr-deep uppercase tracking-wider mb-2">3. Context-Adjusted Performance Models (RAE &amp; RCAE)</h4>
                <div className="bg-white p-4 rounded-lg border border-rr-border mb-3 space-y-3.5 shadow-subtle">
                  <div className="border-b border-rr-soft/60 pb-3">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] font-bold text-rr-deep uppercase tracking-wider">
                        Batter Relative Attacking Efficiency (RAE &Delta;SR):
                      </span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Higher is better
                      </span>
                    </div>
                    <div className="bg-rr-warm p-2.5 rounded border border-rr-border/60 mb-1.5">
                      <MathView
                        block
                        math={`\\mathrm{RAE}_i = \\left[ \\frac{\\sum_{j=1}^{N_i} \\bigl(\\mathrm{Runs}_{\\mathrm{obs}, j} - \\mathbb{E}[\\mathrm{Runs} \\mid \\text{Format}, \\text{Phase}, \\text{Wickets}]\\bigr)}{N_i} \\right] \\times 100`}
                      />
                    </div>
                    <div className="text-[10px] text-rr-muted flex items-center justify-between px-1">
                      <span><MathView math={`= \\mathrm{SR}_{\\mathrm{obs}} - \\mathbb{E}[\\mathrm{SR}_{\\mathrm{context}}]`} /></span>
                      <span className="font-medium text-rr-charcoal">Units: Strike Rate points (&Delta;SR)</span>
                    </div>
                  </div>

                  <div className="border-b border-rr-soft/60 pb-3">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] font-bold text-rr-deep uppercase tracking-wider">
                        Primary Bowler Metric: All-Runs RCAE (&Delta;Economy):
                      </span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                        Lower is better
                      </span>
                    </div>
                    <div className="bg-rr-warm p-2.5 rounded border border-rr-border/60 mb-1.5">
                      <MathView
                        block
                        math={`\\mathrm{RCAE}_{\\mathrm{All\\text{-}Runs}, i} = \\left[ \\frac{\\sum_{k=1}^{L_i} \\bigl(\\mathrm{AllRuns}_{\\mathrm{obs}, k} - \\mathbb{E}[\\mathrm{AllRuns} \\mid \\text{Format}, \\text{Phase}, \\text{Wickets}]\\bigr)}{L_i} \\right] \\times 6`}
                      />
                    </div>
                    <div className="text-[10px] text-rr-muted flex items-center justify-between px-1 mb-1">
                      <span><MathView math={`= \\mathrm{Economy}_{\\mathrm{obs}} - \\mathbb{E}[\\mathrm{Economy}_{\\mathrm{context}}]`} /></span>
                      <span className="font-medium text-rr-charcoal">Units: Runs per over (&Delta;Econ)</span>
                    </div>
                    <div className="text-[9.5px] text-slate-500 bg-slate-50 p-1.5 rounded border border-slate-200/60 leading-relaxed">
                      Includes all bowler-conceded runs (wides and no-balls); excludes byes, leg-byes, and penalty runs; normalized by legal balls bowled (<MathView math={`L_i`} />).
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] font-bold text-rr-deep uppercase tracking-wider">
                        Secondary Diagnostic Metric: Legal-Ball RCAE (&Delta;Legal Economy):
                      </span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200">
                        Lower is better
                      </span>
                    </div>
                    <div className="bg-rr-warm p-2.5 rounded border border-rr-border/60 mb-1.5">
                      <MathView
                        block
                        math={`\\mathrm{RCAE}_{\\mathrm{Legal\\text{-}Ball}, i} = \\left[ \\frac{\\sum_{k=1}^{L_i} \\bigl(\\mathrm{LegalRuns}_{\\mathrm{obs}, k} - \\mathbb{E}[\\mathrm{LegalRuns} \\mid \\text{Format}, \\text{Phase}, \\text{Wickets}]\\bigr)}{L_i} \\right] \\times 6`}
                      />
                    </div>
                    <div className="text-[10px] text-rr-muted flex items-center justify-between px-1 mb-1">
                      <span><MathView math={`= \\mathrm{LegalEcon}_{\\mathrm{obs}} - \\mathbb{E}[\\mathrm{LegalEcon}_{\\mathrm{context}}]`} /></span>
                      <span className="font-medium text-rr-charcoal">Units: Runs per legal over (&Delta;Legal Econ)</span>
                    </div>
                    <div className="text-[9.5px] text-slate-500 bg-slate-50 p-1.5 rounded border border-slate-200/60 leading-relaxed">
                      Diagnostic execution metric strictly on valid deliveries; excludes wides and no-balls from both observed concession and contextual expectation.
                    </div>
                  </div>
                </div>
                <div className="text-[11px] text-rr-muted space-y-1.5 leading-relaxed">
                  <p>
                    Isolates individual execution from match context by benchmarking each delivery against its empirical contextual expectation. Conditioning variables are strictly:
                  </p>
                  <ul className="list-disc list-inside space-y-0.5 ml-2 font-semibold text-rr-charcoal">
                    <li><strong>Competition type</strong> (IPL vs Senior T20I)</li>
                    <li><strong>Innings phase</strong> (POWERPLAY, MIDDLE, DEATH)</li>
                    <li><strong>Wickets bucket</strong> (0–3, 4–6, 7–10 wickets remaining)</li>
                  </ul>
                  <div className="p-2.5 rounded bg-white border border-rr-border text-[10px] text-rr-charcoal space-y-1 mt-2">
                    <p className="font-semibold text-rr-deep">
                      Model Conditioning &amp; Metric Separation:
                    </p>
                    <p>
                      &bull; <em>First-Innings Resource Model:</em> Conditions strictly on <strong>Competition, Over bucket, and Wickets lost</strong> (does not use innings-phase conditioning).
                    </p>
                    <p>
                      &bull; <em>Context-Adjusted Performance Models (RAE/RCAE):</em> Conditions strictly on <strong>Competition type, Innings phase, and Wickets bucket</strong>.
                    </p>
                    <p>
                      &bull; <em>RCAE Dual Metric Architecture:</em> Primary <strong>All-Runs RCAE</strong> evaluates standard match economy against expected all-runs concession per legal ball; <strong>Legal-Ball RCAE</strong> provides a clean secondary diagnostic of pure legal-ball execution.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-rr-pale p-5 rounded-lg border border-rr-soft">
                <h4 className="text-xs font-bold text-rr-deep uppercase tracking-wider mb-2">4. Cluster-Aware Match Bootstrap</h4>
                <div className="bg-white p-4 rounded-lg border border-rr-border mb-3 shadow-subtle">
                  <div className="bg-rr-warm p-3 rounded-md border border-rr-border/60 text-center mb-2">
                    <MathView
                      block
                      math={`\\Delta_b = \\widehat{\\theta}_A^{(b)} - \\widehat{\\theta}_B^{(b)}, \\quad \\forall\\, b \\in \\{1, 2, \\dots, 10\\,000\\} \\qquad \\implies \\qquad \\mathrm{CI}_{95\\%} = \\left[\\Delta_{(250)}, \\; \\Delta_{(9750)}\\right]`}
                    />
                  </div>
                  <p className="text-xs text-rr-muted leading-relaxed">
                    Deliveries within the same match are not independent. RR EDGE performs match-cluster resampling (seed=42, <MathView math={`B = 10\\,000`} />) to establish defensible 95% confidence intervals on comparative margins without violating intra-match correlation assumptions.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Empirical Bayes Shrinkage */}
      {activeTab === 'shrinkage' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-rr-border shadow-card">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
              <div>
                <h3 className="text-base font-bold text-rr-charcoal flex items-center gap-2">
                  <span>Shrinkage Parameter Sensitivity</span>
                  <span className="text-sm font-normal text-rr-muted">
                    (<MathView math="M \in \{25, 45, 60, 90\}" />)
                  </span>
                </h3>
                <p className="text-xs text-rr-muted mt-1">
                  How prior strength modulates player evaluations between small-sample volatility and multi-season robustness.
                </p>
              </div>
              <div className="flex items-center gap-2 bg-rr-pale p-1.5 rounded-lg border border-rr-soft">
                <span className="text-xs font-semibold text-rr-charcoal px-2">Select Active M:</span>
                {[25, 45, 60, 90].map((mVal) => (
                  <button
                    key={mVal}
                    onClick={() => setSelectedM(mVal)}
                    className={`px-3 py-1 rounded text-xs font-bold transition-all ${
                      selectedM === mVal
                        ? 'bg-rr-pink text-white shadow-sm'
                        : 'bg-white text-rr-charcoal hover:bg-rr-soft'
                    }`}
                  >
                    M = {mVal}
                  </button>
                ))}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-rr-border bg-rr-warm text-rr-muted text-xs uppercase tracking-wider">
                    <th className="py-3 px-4 font-semibold">Player</th>
                    <th className="py-3 px-4 font-semibold">Archetype</th>
                    <th className="py-3 px-4 font-semibold text-right">Pressure Balls</th>
                    <th className="py-3 px-4 font-semibold text-right">Raw SR</th>
                    <th className={`py-3 px-4 font-semibold text-right ${selectedM === 25 ? 'bg-rr-soft font-bold text-rr-pink' : ''}`}>M=25</th>
                    <th className={`py-3 px-4 font-semibold text-right ${selectedM === 45 ? 'bg-rr-soft font-bold text-rr-pink' : ''}`}>M=45 (Core)</th>
                    <th className={`py-3 px-4 font-semibold text-right ${selectedM === 60 ? 'bg-rr-soft font-bold text-rr-pink' : ''}`}>M=60</th>
                    <th className={`py-3 px-4 font-semibold text-right ${selectedM === 90 ? 'bg-rr-soft font-bold text-rr-pink' : ''}`}>M=90</th>
                    <th className="py-3 px-4 font-semibold">Analytical Interpretation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-rr-border text-xs">
                  {shrinkageExamples.map((ex) => (
                    <tr key={ex.player} className="hover:bg-rr-pale transition-colors">
                      <td className="py-3 px-4 font-bold text-rr-charcoal">{ex.player}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rr-soft text-rr-deep">
                          {ex.archetype}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-medium">{ex.balls}</td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-rr-charcoal">{ex.rawSR.toFixed(1)}</td>
                      <td className={`py-3 px-4 text-right font-mono ${selectedM === 25 ? 'bg-rr-pale font-bold text-rr-pink' : 'text-rr-muted'}`}>
                        {ex.m25.toFixed(1)}
                      </td>
                      <td className={`py-3 px-4 text-right font-mono ${selectedM === 45 ? 'bg-rr-pale font-bold text-rr-pink' : 'text-rr-charcoal font-semibold'}`}>
                        {ex.m45.toFixed(1)}
                      </td>
                      <td className={`py-3 px-4 text-right font-mono ${selectedM === 60 ? 'bg-rr-pale font-bold text-rr-pink' : 'text-rr-muted'}`}>
                        {ex.m60.toFixed(1)}
                      </td>
                      <td className={`py-3 px-4 text-right font-mono ${selectedM === 90 ? 'bg-rr-pale font-bold text-rr-pink' : 'text-rr-muted'}`}>
                        {ex.m90.toFixed(1)}
                      </td>
                      <td className="py-3 px-4 text-rr-muted">{ex.verdict}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-6 p-4 bg-rr-pale rounded-lg border border-rr-soft flex items-start gap-3">
              <Info className="w-5 h-5 text-rr-pink flex-shrink-0 mt-0.5" />
              <div className="text-xs text-rr-charcoal leading-relaxed">
                <span className="font-bold text-rr-deep">Why M=45 as Primary Baseline:</span> An empirical parameter grid search established that M=45 provides the optimal trade-off between dampening single-innings flukes (sample sizes &lt; 30) while preserving 75–85% of genuine high-velocity discovery upside for emerging young talent.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Evidence Tier Rubric */}
      {activeTab === 'tiers' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-rr-border shadow-card">
            <h3 className="text-base font-bold text-rr-charcoal mb-4">Evidence Tier Qualification Architecture</h3>
            <p className="text-xs text-rr-muted mb-6">
              Every candidate is classified into a rigorous evidence tier based on statistical exposure, match diversity, and multi-phase presence.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="border border-emerald-200 bg-emerald-50/40 rounded-xl p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="px-2.5 py-1 rounded bg-emerald-100 text-emerald-800 text-xs font-bold uppercase tracking-wider">
                    Tier 1: Confident
                  </span>
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                </div>
                <h4 className="font-bold text-sm text-emerald-950 mb-2">Strict Sample Quality</h4>
                <ul className="text-xs text-emerald-800 space-y-2 mb-4">
                  <li>&bull; Minimum 60+ pressure deliveries</li>
                  <li>&bull; Minimum 5+ distinct high-leverage matches</li>
                  <li>&bull; 2+ innings phases represented</li>
                  <li>&bull; Shrinkage retention &gt; 80%</li>
                </ul>
                <p className="text-[11px] text-emerald-700 italic border-t border-emerald-200/60 pt-3">
                  Eligible for primary starting XI tactical roles and core auction targets.
                </p>
              </div>

              <div className="border border-blue-200 bg-blue-50/40 rounded-xl p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="px-2.5 py-1 rounded bg-blue-100 text-blue-800 text-xs font-bold uppercase tracking-wider">
                    Tier 2: Moderate
                  </span>
                  <Info className="w-5 h-5 text-blue-600" />
                </div>
                <h4 className="font-bold text-sm text-blue-950 mb-2">Balanced Evidence</h4>
                <ul className="text-xs text-blue-800 space-y-2 mb-4">
                  <li>&bull; Minimum 30–59 pressure deliveries</li>
                  <li>&bull; Minimum 3+ distinct matches</li>
                  <li>&bull; Demonstrable role consistency</li>
                  <li>&bull; Shrinkage retention 65% – 80%</li>
                </ul>
                <p className="text-[11px] text-blue-700 italic border-t border-blue-200/60 pt-3">
                  High strategic value; reliable baseline with moderate sample volatility.
                </p>
              </div>

              <div className="border border-amber-200 bg-amber-50/40 rounded-xl p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="px-2.5 py-1 rounded bg-amber-100 text-amber-800 text-xs font-bold uppercase tracking-wider">
                    Tier 3: Provisional
                  </span>
                  <GitBranch className="w-5 h-5 text-amber-600" />
                </div>
                <h4 className="font-bold text-sm text-amber-950 mb-2">Discovery Upside</h4>
                <ul className="text-xs text-amber-800 space-y-2 mb-4">
                  <li>&bull; &lt; 30 pressure deliveries or &lt; 3 matches</li>
                  <li>&bull; Extreme raw velocity or strike rate</li>
                  <li>&bull; Heavy shrinkage compression (&gt; 25%)</li>
                  <li>&bull; Wider bootstrap confidence intervals</li>
                </ul>
                <p className="text-[11px] text-amber-700 italic border-t border-amber-200/60 pt-3">
                  Uncapped prodigies and emerging disruptors flagged for squad development.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Governance & Exclusions */}
      {activeTab === 'disclosures' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-rr-border shadow-card space-y-6">
            <h3 className="text-base font-bold text-rr-charcoal flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-rr-pink" />
              Scientific Integrity & Critical Governance Audits
            </h3>
            <p className="text-xs text-rr-muted">
              To preserve professional credibility with Rajasthan Royals' analytics staff, the following explicit exclusions and corrections are hardcoded into the pipeline:
            </p>

            <div className="space-y-4">
              <div className="p-4 rounded-lg border border-red-200 bg-red-50/30">
                <div className="flex items-center gap-2 text-red-900 font-bold text-xs uppercase tracking-wider mb-1">
                  <span>Audit Correction 1: Removal of Arbitrary "Wicket Impact Score"</span>
                </div>
                <p className="text-xs text-rr-charcoal leading-relaxed">
                  The initial formula <em>(Wickets / Overs) - (Economy / 10)</em> lacked defensible dimensional justification (the divisor of 10 was arbitrary). It has been completely removed from primary ranking. Wickets per over and economy are retained as independent, unmerged dimensions.
                </p>
              </div>

              <div className="p-4 rounded-lg border border-amber-200 bg-amber-50/30">
                <div className="flex items-center gap-2 text-amber-900 font-bold text-xs uppercase tracking-wider mb-1">
                  <span>Governance Exclusion 2: DLS-Uncertain Deliveries (1,641 Quarantined Deliveries)</span>
                </div>
                <p className="text-xs text-rr-charcoal leading-relaxed">
                  Exactly 1,641 deliveries with ambiguous in-play DLS target calculations or curtailed overs were quarantined from primary analysis (leaving 192,373 primary pressure cohort deliveries out of 194,014 total eligible deliveries). Developmental A-team competitions (e.g. Emerging Teams Asia Cup 2024, Rising Stars 2025) were excluded upstream during competition whitelisting in <code className="font-mono text-amber-900">src/cricket/competition_config.py</code>, not conflated with this 1,641 count.
                </p>
              </div>

              <div className="p-4 rounded-lg border border-blue-200 bg-blue-50/30">
                <div className="flex items-center gap-2 text-blue-900 font-bold text-xs uppercase tracking-wider mb-1">
                  <span>Data Quality Exclusion 3: Exclusion of Corrupted bowl_speed Attribute</span>
                </div>
                <p className="text-xs text-rr-charcoal leading-relaxed">
                  The raw <code className="font-mono text-blue-900">bowl_speed</code> attribute exhibits severe data quality issues, missing records, and calibration drift across tournament venues. It was completely excluded from primary player ranking models. No unverified speed metrics, release trajectories, or physical speed assertions are made.
                </p>
              </div>

              <div className="p-4 rounded-lg border border-purple-200 bg-purple-50/30">
                <div className="flex items-center gap-2 text-purple-900 font-bold text-xs uppercase tracking-wider mb-1">
                  <span>Integrity Standard 4: Strict Format Separation</span>
                </div>
                <p className="text-xs text-rr-charcoal leading-relaxed">
                  IPL and Senior T20I represent distinct competitive ecosystems with differing bowling depth, ground dimensions, and tactical phases. Performances are never averaged together into an unweighted pool; combined metrics reflect volume exposure only.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
