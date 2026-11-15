import React from 'react';
import { Menu, ShieldCheck, Sparkles } from 'lucide-react';
import { PageId } from './Sidebar';

interface HeaderProps {
  currentPage: PageId;
  onOpenMobile: () => void;
}

const pageTitles: Record<PageId, { title: string; subtitle: string }> = {
  overview: {
    title: 'Executive Intelligence Overview',
    subtitle: 'Strategic recommendations, Top-10 rosters, and key empirical discoveries under pressure.',
  },
  pressure: {
    title: 'Pressure Intelligence Framework',
    subtitle: 'Asymmetric leverage modeling, tier distributions, and resource deficit dynamics.',
  },
  batters: {
    title: 'Batter Evaluation & Ranking Engine',
    subtitle: 'Bayesian shrunk strike rates, Context RAE, and boundary/dot trade-off analysis.',
  },
  bowlers: {
    title: 'Bowler Evaluation & Ranking Engine',
    subtitle: 'Defensive containment (RCAE), wicket penetration, and phase-specific execution.',
  },
  scenarios: {
    title: 'Scenario Lab & Tactical Simulations',
    subtitle: 'Standardized match situation stress-testing, custom scenario builder, and cohort benchmarks.',
  },
  simulator: {
    title: 'Interactive 2D Cricket Simulator',
    subtitle: 'Top-down ground physics, historical sequence replays, and What-if situational delivery simulations.',
  },
  gallery: {
    title: 'Player Intelligence Gallery',
    subtitle: 'Searchable directory of 888 eligible players with unified dossiers, ML residuals, and scenario records.',
  },
  comparison: {
    title: 'Player Comparison Lab',
    subtitle: 'Head-to-head evaluation with 10,000-resample match-cluster bootstrap confidence intervals.',
  },
  behavioral: {
    title: 'Observable Behavioral Pressure Intelligence',
    subtitle: 'Ball-by-ball empirical reactions: post-dot scoring acceleration, bowler bounce-back containment, and spell progression.',
  },
  ml_lab: {
    title: 'Machine Learning Intelligence Lab',
    subtitle: 'Validated chronological LightGBM & XGBoost predictive models for batter runs, bowler concession, and wicket probability.',
  },
  methodology: {
    title: 'Methodology & Model Lab',
    subtitle: 'Empirical Bayes ANOVA, shrinkage sensitivity grid, and data verification protocols.',
  },
  explorer: {
    title: 'Candidate Data Explorer',
    subtitle: 'Direct query and pagination across audited primary pressure candidate records.',
  },
};

export const Header: React.FC<HeaderProps> = ({ currentPage, onOpenMobile }) => {
  const meta = pageTitles[currentPage] || pageTitles.overview;

  return (
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-rr-border px-4 sm:px-6 h-16 md:h-20 flex items-center">
      <div className="w-full flex items-center justify-between gap-4">
        {/* Left Title Section with min-w-0 to prevent layout blow-up */}
        <div className="flex items-center gap-2.5 sm:gap-3 min-w-0 flex-1">
          <button
            onClick={onOpenMobile}
            className="p-2 -ml-2 rounded-lg text-rr-charcoal hover:bg-rr-palePink lg:hidden shrink-0"
            aria-label="Open navigation"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-base sm:text-lg md:text-xl font-extrabold text-rr-charcoal tracking-tight font-heading truncate">
                {meta.title}
              </h1>
              <span className="hidden sm:inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-rr-palePink text-rr-deepPink border border-pink-200 shrink-0">
                <Sparkles className="w-3 h-3 text-rr-pink" />
                RR EDGE
              </span>
            </div>
            <p className="text-xs text-rr-muted hidden sm:block mt-0.5 truncate max-w-md md:max-w-xl xl:max-w-3xl">
              {meta.subtitle}
            </p>
          </div>
        </div>

        {/* Right Badges Section */}
        <div className="shrink-0 flex items-center gap-2 sm:gap-3">
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span className="whitespace-nowrap">Audited Cohort</span>
          </div>
          <div className="text-xs px-2.5 py-1 rounded-md bg-rr-palePink text-rr-deepPink font-bold border border-pink-100 whitespace-nowrap">
            IPL & T20I
          </div>
        </div>
      </div>
    </header>
  );
};
