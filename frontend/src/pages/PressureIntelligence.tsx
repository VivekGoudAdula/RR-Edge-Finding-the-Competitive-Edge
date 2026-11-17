import React, { useEffect, useState } from 'react';
import {
  Gauge,
  Flame,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  Info,
  Clock,
  Shield,
  Layers,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from 'recharts';
import { fetchPressureDistributions } from '../services/api';
import canonicalPressure from '../data/canonicalPressure.json';
import { PressureDistributions } from '../types';
import { SectionHeading } from '../components/common/SectionHeading';
import { MetricCard } from '../components/common/MetricCard';
import { PageHeroCard } from '../components/common/PageHeroCard';

export const PressureIntelligence: React.FC = () => {
  const [data, setData] = useState<PressureDistributions>(canonicalPressure as unknown as PressureDistributions);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchPressureDistributions().then((res) => {
      setData(res);
      setLoading(false);
    });
  }, []);

  if (loading || !data) {
    return (
      <div className="p-8 space-y-6 animate-pulse">
        <div className="h-28 bg-white rounded-xl border border-rr-border"></div>
        <div className="h-80 bg-white rounded-xl border border-rr-border"></div>
      </div>
    );
  }

  // Tier data for chart
  const tierChartData = data.tiers.map((t) => ({
    name: t.tier,
    Batters: t.batter_pct,
    Bowlers: t.bowler_pct,
  }));

  const phaseChartData = data.phase_breakdown.map((p) => ({
    name: p.phase.split(' ')[0], // Powerplay, Middle, Death
    'Pressure Deliveries': p.pressure_deliveries_pct,
    'Normal Deliveries': p.normal_deliveries_pct,
  }));

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Standardized Compact Hero Section */}
      <PageHeroCard
        badge="Pressure Intelligence Framework"
        badgeIcon={<Gauge className="w-3.5 h-3.5 text-rr-pink" />}
        badgeContext="Primary Audited Cohort"
        title="Asymmetric Pressure Framework"
        description="Cricket matches are fundamentally asymmetric: batters face steep required rates and collapses, while bowlers defend low totals and death overs. RR EDGE independently identifies delivery-level match leverage before the ball is bowled."
      />

      {/* KPI Highlights */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Pressure Deliveries"
          value="23.0% / 37.2%"
          subtitle="44,333 bowl / 71,523 bat"
          accentEdge
          icon={<Flame className="w-5 h-5" />}
        />
        <MetricCard
          title="Extreme Tier"
          value="8.4%"
          subtitle="Batters in critical leverage states"
          accentEdge
          icon={<AlertTriangle className="w-5 h-5" />}
        />
        <MetricCard
          title="Death Concentration"
          value="37.7%"
          subtitle="Pressure deliveries in overs 16–20"
          accentEdge
          icon={<Clock className="w-5 h-5" />}
        />
        <MetricCard
          title="DLS Isolation"
          value="100%"
          subtitle="Rain-interrupted uncertainty excluded"
          accentEdge
          icon={<Shield className="w-5 h-5" />}
        />
      </div>

      {/* Pressure Tier Distribution Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 bg-white rounded-2xl border border-rr-border p-6 shadow-rr-card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-extrabold text-rr-charcoal font-heading">
                Distribution Across Pressure Tiers
              </h3>
              <p className="text-xs text-rr-muted">Percentage of evaluated deliveries by discipline</p>
            </div>
            <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-rr-palePink text-rr-deepPink">
              Primary Cohort
            </span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={tierChartData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F0E7ED" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: '#77717C', fontSize: 12 }} />
                <YAxis unit="%" tick={{ fill: '#77717C', fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#F0E7ED',
                    borderRadius: '8px',
                    boxShadow: '0 4px 12px rgba(37,33,42,0.06)',
                  }}
                  formatter={(val: number) => [`${val}%`, '']}
                />
                <Legend wrapperStyle={{ paddingTop: 10, fontSize: 12 }} />
                <Bar dataKey="Batters" fill="#E6007E" radius={[6, 6, 0, 0]} />
                <Bar dataKey="Bowlers" fill="#25212A" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Tier Explanations */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-rr-border p-6 shadow-rr-card flex flex-col justify-between">
          <div>
            <h3 className="text-base font-extrabold text-rr-charcoal font-heading mb-3">
              Pressure Tier Definitions
            </h3>
            <div className="space-y-3">
              {data.tiers.map((t) => (
                <div key={t.tier} className="p-3 rounded-xl bg-rr-warmWhite border border-rr-border">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-extrabold text-rr-charcoal font-heading">
                      {t.tier}
                    </span>
                    <span className="text-[11px] font-bold text-rr-deepPink">
                      Bat: {t.batter_pct}% • Bowl: {t.bowler_pct}%
                    </span>
                  </div>
                  <p className="mt-1 text-[11px] text-rr-muted leading-relaxed">
                    {t.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Pressure vs Normal Impact Breakdown */}
      <div className="bg-white rounded-2xl border border-rr-border p-6 shadow-rr-card">
        <SectionHeading
          badge="Cohort Comparison"
          title="Pressure vs Normal Delivery Performance"
          description="How aggregate batting and bowling metrics shift under acute pressure conditions."
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Batters Shift */}
          <div>
            <div className="flex items-center gap-2 mb-3 pb-2 border-b border-rr-border">
              <span className="w-2.5 h-2.5 rounded-full bg-rr-pink"></span>
              <h4 className="text-sm font-bold text-rr-charcoal font-heading">Batter Performance Shift</h4>
            </div>
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-rr-muted font-semibold border-b border-rr-border">
                  <th className="py-2">Metric</th>
                  <th className="py-2 text-right">Normal</th>
                  <th className="py-2 text-right">Pressure</th>
                  <th className="py-2 text-right">Delta Shift</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-rr-border">
                {data.pressure_vs_normal.batters.map((m) => (
                  <tr key={m.metric} className="hover:bg-rr-warmWhite">
                    <td className="py-2.5 font-medium text-rr-charcoal">{m.metric}</td>
                    <td className="py-2.5 text-right text-rr-muted">{m.normal} {m.unit}</td>
                    <td className="py-2.5 text-right font-bold text-rr-charcoal">{m.pressure} {m.unit}</td>
                    <td className="py-2.5 text-right font-bold text-rr-deepPink">
                      {m.delta}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Bowlers Shift */}
          <div>
            <div className="flex items-center gap-2 mb-3 pb-2 border-b border-rr-border">
              <span className="w-2.5 h-2.5 rounded-full bg-rr-charcoal"></span>
              <h4 className="text-sm font-bold text-rr-charcoal font-heading">Bowler Performance Shift</h4>
            </div>
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-rr-muted font-semibold border-b border-rr-border">
                  <th className="py-2">Metric</th>
                  <th className="py-2 text-right">Normal</th>
                  <th className="py-2 text-right">Pressure</th>
                  <th className="py-2 text-right">Delta Shift</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-rr-border">
                {data.pressure_vs_normal.bowlers.map((m) => (
                  <tr key={m.metric} className="hover:bg-rr-warmWhite">
                    <td className="py-2.5 font-medium text-rr-charcoal">{m.metric}</td>
                    <td className="py-2.5 text-right text-rr-muted">{m.normal} {m.unit}</td>
                    <td className="py-2.5 text-right font-bold text-rr-charcoal">{m.pressure} {m.unit}</td>
                    <td className="py-2.5 text-right font-bold text-emerald-700">
                      {m.delta}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Innings Phase Distribution & Methodological Principles */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6 bg-white rounded-2xl border border-rr-border p-6 shadow-rr-card">
          <h3 className="text-base font-extrabold text-rr-charcoal font-heading mb-1">
            Pressure Concentration by Match Phase
          </h3>
          <p className="text-xs text-rr-muted mb-4">
            Notice the significant inflation of pressure deliveries in death overs (overs 16–20)
          </p>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={phaseChartData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F0E7ED" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: '#77717C', fontSize: 12 }} />
                <YAxis unit="%" tick={{ fill: '#77717C', fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#F0E7ED',
                    borderRadius: '8px',
                  }}
                  formatter={(val: number) => [`${val}%`, '']}
                />
                <Legend wrapperStyle={{ paddingTop: 8, fontSize: 12 }} />
                <Bar dataKey="Pressure Deliveries" fill="#E6007E" radius={[6, 6, 0, 0]} />
                <Bar dataKey="Normal Deliveries" fill="#A49FA9" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="lg:col-span-6 bg-white rounded-2xl border border-rr-border p-6 shadow-rr-card flex flex-col justify-between">
          <div>
            <h3 className="text-base font-extrabold text-rr-charcoal font-heading mb-3">
              Core Methodological Principles
            </h3>
            <div className="space-y-3.5">
              {data.asymmetry_principles.map((pr) => (
                <div key={pr.title} className="p-3.5 rounded-xl bg-rr-palePink border border-pink-100">
                  <h4 className="text-xs font-bold text-rr-deepPink font-heading">
                    {pr.title}
                  </h4>
                  <p className="mt-1 text-xs text-rr-charcoal leading-relaxed">
                    {pr.explanation}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

