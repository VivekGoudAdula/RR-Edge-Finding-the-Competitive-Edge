import React from 'react';
import { Shield, Swords, Activity, Info, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { HeadToHeadAnalytics } from '../../services/simulatorApi';

interface AnalyticsPanelProps {
  analytics: HeadToHeadAnalytics | null;
  loading?: boolean;
  mlBaseline?: {
    expected_runs_off_bat?: number;
    expected_runs_conceded?: number;
    wicket_probability?: number;
    scope_disclosure?: string;
  } | null;
}

export const AnalyticsPanel: React.FC<AnalyticsPanelProps> = ({
  analytics,
  loading = false,
  mlBaseline,
}) => {
  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-card border border-slate-200 p-6 text-center text-xs text-slate-500 animate-pulse">
        Computing live contextual performance & head-to-head metrics...
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="bg-white rounded-xl shadow-card border border-slate-200 p-6 text-center text-xs text-slate-500">
        Select a batter and bowler to inspect live pressure profiles and head-to-head encounters.
      </div>
    );
  }

  const { batter, bowler, direct_head_to_head } = analytics;

  return (
    <div className="space-y-4">
      {/* Dual Player Comparative Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* Batter Profile Card */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-card p-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-full bg-rr-pink text-white flex items-center justify-center font-bold text-xs">
                {batter.player_name.substring(0, 2).toUpperCase()}
              </div>
              <div>
                <h4 className="text-sm font-bold text-rr-navy truncate">{batter.player_name}</h4>
                <p className="text-[10px] text-slate-500">{batter.role}</p>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-pink-50 text-rr-pink border border-pink-200">
              {batter.evidence_tier} ({batter.deliveries}b)
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="bg-slate-50 p-2 rounded-lg border border-slate-100">
              <div className="text-[10px] text-slate-500">Pressure SR</div>
              <div className="text-sm font-black text-rr-pink mt-0.5">{batter.strike_rate}</div>
            </div>
            <div className="bg-slate-50 p-2 rounded-lg border border-slate-100">
              <div className="text-[10px] text-slate-500">Dot %</div>
              <div className="text-sm font-bold text-slate-700 mt-0.5">{batter.dot_pct}%</div>
            </div>
            <div className="bg-slate-50 p-2 rounded-lg border border-slate-100">
              <div className="text-[10px] text-slate-500">Boundary %</div>
              <div className="text-sm font-bold text-amber-600 mt-0.5">{batter.boundary_pct}%</div>
            </div>
          </div>
        </div>

        {/* Bowler Profile Card */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-card p-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-full bg-[#0B192C] text-rr-gold flex items-center justify-center font-bold text-xs">
                {bowler.player_name.substring(0, 2).toUpperCase()}
              </div>
              <div>
                <h4 className="text-sm font-bold text-rr-navy truncate">{bowler.player_name}</h4>
                <p className="text-[10px] text-slate-500">{bowler.role}</p>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
              {bowler.evidence_tier} ({bowler.legal_balls}b)
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="bg-slate-50 p-2 rounded-lg border border-slate-100">
              <div className="text-[10px] text-slate-500">Pressure Econ</div>
              <div className="text-sm font-black text-blue-800 mt-0.5">{bowler.economy_rate}</div>
            </div>
            <div className="bg-slate-50 p-2 rounded-lg border border-slate-100">
              <div className="text-[10px] text-slate-500">Dot %</div>
              <div className="text-sm font-bold text-slate-700 mt-0.5">{bowler.dot_pct}%</div>
            </div>
            <div className="bg-slate-50 p-2 rounded-lg border border-slate-100">
              <div className="text-[10px] text-slate-500">Wkts / Over</div>
              <div className="text-sm font-bold text-emerald-700 mt-0.5">{bowler.wickets_per_over}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Direct Head-to-Head Encounter Bar */}
      <div className="bg-slate-50 rounded-xl border border-slate-200 p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2">
          <Swords className="w-4 h-4 text-rr-gold" />
          <span className="font-bold text-slate-800">Historical Head-to-Head Encounters:</span>
          <span className="text-slate-600">
            {direct_head_to_head.balls_faced > 0
              ? `${direct_head_to_head.runs_scored} runs off ${direct_head_to_head.balls_faced} balls (${direct_head_to_head.dismissals} dismissal)`
              : 'Zero direct historical deliveries'}
          </span>
        </div>
        <span className="text-[11px] text-slate-500 font-mono">
          {direct_head_to_head.strike_rate ? `SR: ${direct_head_to_head.strike_rate}` : direct_head_to_head.sample_label}
        </span>
      </div>

      {/* Contextual Supervised ML Benchmark Disclosure */}
      <div className="bg-white rounded-xl border border-amber-200/80 p-3.5 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
            <Activity className="w-3.5 h-3.5 text-rr-pink" />
            <span>Supervised Delivery-Outcome ML Baseline</span>
          </div>
          <span className="text-[10px] uppercase font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
            Situational Par Benchmark
          </span>
        </div>

        <div className="grid grid-cols-3 gap-2 text-center text-xs pt-1">
          <div className="p-2 bg-slate-50 rounded-lg">
            <div className="text-[10px] text-slate-500">Exp. Runs Off Bat</div>
            <div className="font-bold text-slate-800 mt-0.5">
              {mlBaseline?.expected_runs_off_bat ?? 1.25}
            </div>
          </div>
          <div className="p-2 bg-slate-50 rounded-lg">
            <div className="text-[10px] text-slate-500">Exp. Conceded</div>
            <div className="font-bold text-slate-800 mt-0.5">
              {mlBaseline?.expected_runs_conceded ?? 1.31}
            </div>
          </div>
          <div className="p-2 bg-slate-50 rounded-lg">
            <div className="text-[10px] text-slate-500">Wicket Probability</div>
            <div className="font-bold text-red-600 mt-0.5">
              {mlBaseline?.wicket_probability ? `${(mlBaseline.wicket_probability * 100).toFixed(1)}%` : '5.2%'}
            </div>
          </div>
        </div>

        <p className="text-[11px] text-slate-500 leading-relaxed border-t border-slate-100 pt-2">
          {mlBaseline?.scope_disclosure ||
            'Contextual delivery models estimate expected delivery baseline for the pre-delivery match state, NOT individual player talent or skill. They establish the objective situational benchmark.'}
        </p>
      </div>
    </div>
  );
};

