import React, { useState, useEffect, useMemo } from 'react';
import { SectionHeading } from '../components/common/SectionHeading';
import { TierBadge } from '../components/common/Badge';
import { PageHeroCard } from '../components/common/PageHeroCard';
import { fetchBatters, fetchBowlers } from '../services/api';
import { PlayerOverview } from '../types';
import { 
  Search, 
  ChevronLeft, 
  ChevronRight, 
  ArrowUpDown,
  FileSpreadsheet,
  CheckCircle2
} from 'lucide-react';

interface ExplorerRecord {
  id: string;
  name: string;
  discipline: 'BATTER' | 'BOWLER';
  format: 'IPL' | 'T20I';
  role: string;
  balls: number;
  matches: number;
  primaryMetricName: string;
  primaryMetricVal: number;
  contextDelta: number;
  dotPct: number;
  boundaryPct: number;
  tier: string;
  archetype: string;
}

export const DataExplorer: React.FC = () => {
  const [records, setRecords] = useState<ExplorerRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [disciplineFilter, setDisciplineFilter] = useState<'ALL' | 'BATTER' | 'BOWLER'>('ALL');
  const [formatFilter, setFormatFilter] = useState<'ALL' | 'IPL' | 'T20I'>('ALL');
  const [tierFilter, setTierFilter] = useState<'ALL' | 'CONFIDENT' | 'MODERATE' | 'PROVISIONAL'>('ALL');
  const [sortField, setSortField] = useState<keyof ExplorerRecord>('balls');
  const [sortAsc, setSortAsc] = useState(false);
  const [page, setPage] = useState(1);
  const pageSize = 15;
  const [exportSuccess, setExportSuccess] = useState(false);

  useEffect(() => {
    const loadAll = async () => {
      try {
        const [batters, bowlers] = await Promise.all([
          fetchBatters(),
          fetchBowlers()
        ]);

        const combined: ExplorerRecord[] = [];

        batters.forEach((b: PlayerOverview) => {
          // Add IPL record
          if (b.ipl_pressure_volume && b.ipl_pressure_volume > 0) {
            combined.push({
              id: `bat-ipl-${b.player_id}`,
              name: b.player_name,
              discipline: 'BATTER',
              format: 'IPL',
              role: b.primary_role || 'Specialist',
              balls: b.ipl_pressure_volume,
              matches: b.ipl_matches || 0,
              primaryMetricName: 'SR (M=45)',
              primaryMetricVal: b.ipl_shrunk_m45 || b.ipl_raw_sr || 0,
              contextDelta: b.ipl_context_delta_sr || 0,
              dotPct: b.ipl_dot_ball_pct || 0,
              boundaryPct: b.ipl_boundary_ball_pct || 0,
              tier: b.evidence_tier || 'MODERATE',
              archetype: b.stability_archetype || 'BALANCED'
            });
          }
          // Add T20I record if present
          if (b.t20i_pressure_volume && b.t20i_pressure_volume > 0) {
            combined.push({
              id: `bat-t20i-${b.player_id}`,
              name: b.player_name,
              discipline: 'BATTER',
              format: 'T20I',
              role: b.primary_role || 'Specialist',
              balls: b.t20i_pressure_volume,
              matches: b.t20i_matches || 0,
              primaryMetricName: 'SR (M=45)',
              primaryMetricVal: b.t20i_shrunk_m45 || b.t20i_raw_sr || 0,
              contextDelta: b.t20i_context_delta_sr || 0,
              dotPct: b.t20i_dot_ball_pct || 0,
              boundaryPct: b.t20i_boundary_ball_pct || 0,
              tier: b.evidence_tier || 'MODERATE',
              archetype: b.stability_archetype || 'BALANCED'
            });
          }
        });

        bowlers.forEach((bw: PlayerOverview) => {
          if (bw.ipl_pressure_volume && bw.ipl_pressure_volume > 0) {
            combined.push({
              id: `bowl-ipl-${bw.player_id}`,
              name: bw.player_name,
              discipline: 'BOWLER',
              format: 'IPL',
              role: bw.primary_role || 'Specialist',
              balls: bw.ipl_pressure_volume,
              matches: bw.ipl_matches || 0,
              primaryMetricName: 'Econ',
              primaryMetricVal: bw.ipl_raw_econ || 0,
              contextDelta: bw.ipl_context_delta_econ || 0,
              dotPct: bw.ipl_boundary_concession_pct ? (100 - bw.ipl_boundary_concession_pct) : 0,
              boundaryPct: bw.ipl_boundary_concession_pct || 0,
              tier: bw.evidence_tier || 'MODERATE',
              archetype: bw.stability_archetype || 'BALANCED'
            });
          }
        });

        setRecords(combined);
      } catch (err) {
        console.error('Failed to load explorer data:', err);
      } finally {
        setLoading(false);
      }
    };

    loadAll();
  }, []);

  const filtered = useMemo(() => {
    return records.filter((r) => {
      const matchSearch = r.name.toLowerCase().includes(search.toLowerCase()) ||
                          r.role.toLowerCase().includes(search.toLowerCase());
      const matchDisc = disciplineFilter === 'ALL' || r.discipline === disciplineFilter;
      const matchFmt = formatFilter === 'ALL' || r.format === formatFilter;
      const matchTier = tierFilter === 'ALL' || r.tier.includes(tierFilter);
      return matchSearch && matchDisc && matchFmt && matchTier;
    }).sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }
      return sortAsc ? Number(aVal) - Number(bVal) : Number(bVal) - Number(aVal);
    });
  }, [records, search, disciplineFilter, formatFilter, tierFilter, sortField, sortAsc]);

  const totalPages = Math.ceil(filtered.length / pageSize) || 1;
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  const handleSort = (field: keyof ExplorerRecord) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const handleExportCSV = () => {
    if (filtered.length === 0) return;
    const headers = ['Player', 'Discipline', 'Format', 'Role', 'Balls', 'Matches', 'Primary Metric', 'Context Delta', 'Dot %', 'Boundary %', 'Tier', 'Archetype'];
    const rows = filtered.map((r) => [
      `"${r.name}"`,
      r.discipline,
      r.format,
      `"${r.role}"`,
      r.balls,
      r.matches,
      r.primaryMetricVal.toFixed(1),
      r.contextDelta.toFixed(1),
      r.dotPct.toFixed(1),
      r.boundaryPct.toFixed(1),
      r.tier,
      r.archetype || 'N/A'
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `RR_EDGE_DATASET_EXPORT_${disciplineFilter}_${formatFilter}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setExportSuccess(true);
    setTimeout(() => setExportSuccess(false), 3000);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Standardized Compact Hero Section */}
      <PageHeroCard
        badge="Audited Dataset"
        badgeIcon={<FileSpreadsheet className="w-3.5 h-3.5 text-rr-pink" />}
        title="Data Explorer & Cohort Export"
        description="Explore the entire verified player cohort across IPL and Senior T20I with multi-dimensional filtering, statistical ranking, and full CSV export capabilities."
        actions={
          <button
            onClick={handleExportCSV}
            disabled={loading || filtered.length === 0}
            className="flex items-center gap-1.5 bg-rr-pink text-white hover:bg-rr-deep px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow-sm active:scale-95 disabled:opacity-50"
          >
            {exportSuccess ? <CheckCircle2 className="w-3.5 h-3.5" /> : <FileSpreadsheet className="w-3.5 h-3.5" />}
            <span>{exportSuccess ? 'Exported CSV!' : 'Export CSV'}</span>
          </button>
        }
      />

      {/* Control Filters Bar */}
      <div className="bg-white p-4 rounded-xl border border-rr-border shadow-card space-y-4">
        <div className="flex flex-col md:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-rr-muted" />
            <input
              type="text"
              placeholder="Search by player name or tactical role..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-4 py-2 text-xs bg-rr-warm border border-rr-border rounded-lg text-rr-charcoal focus:outline-none focus:border-rr-pink transition-colors"
            />
          </div>

          {/* Discipline Toggle */}
          <div className="flex bg-rr-warm rounded-lg p-1 border border-rr-border">
            {(['ALL', 'BATTER', 'BOWLER'] as const).map((d) => (
              <button
                key={d}
                onClick={() => { setDisciplineFilter(d); setPage(1); }}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                  disciplineFilter === d
                    ? 'bg-rr-pink text-white shadow-sm'
                    : 'text-rr-muted hover:text-rr-charcoal'
                }`}
              >
                {d === 'ALL' ? 'All Disciplines' : d === 'BATTER' ? 'Batters' : 'Bowlers'}
              </button>
            ))}
          </div>

          {/* Format Toggle */}
          <div className="flex bg-rr-warm rounded-lg p-1 border border-rr-border">
            {(['ALL', 'IPL', 'T20I'] as const).map((f) => (
              <button
                key={f}
                onClick={() => { setFormatFilter(f); setPage(1); }}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                  formatFilter === f
                    ? 'bg-rr-pink text-white shadow-sm'
                    : 'text-rr-muted hover:text-rr-charcoal'
                }`}
              >
                {f === 'ALL' ? 'All Formats' : f}
              </button>
            ))}
          </div>

          {/* Tier Toggle */}
          <div className="flex bg-rr-warm rounded-lg p-1 border border-rr-border">
            {(['ALL', 'CONFIDENT', 'MODERATE', 'PROVISIONAL'] as const).map((t) => (
              <button
                key={t}
                onClick={() => { setTierFilter(t); setPage(1); }}
                className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all ${
                  tierFilter === t
                    ? 'bg-rr-pink text-white shadow-sm'
                    : 'text-rr-muted hover:text-rr-charcoal'
                }`}
              >
                {t === 'ALL' ? 'All Tiers' : t.slice(0, 4)}
              </button>
            ))}
          </div>
        </div>

        {/* Results Counter */}
        <div className="flex justify-between items-center text-xs text-rr-muted pt-2 border-t border-rr-border">
          <span>Showing <strong className="text-rr-charcoal font-semibold">{filtered.length}</strong> verified player records</span>
          <span>Page {page} of {totalPages}</span>
        </div>
      </div>

      {/* Explorer Table */}
      <div className="bg-white rounded-xl border border-rr-border shadow-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-rr-border bg-rr-warm text-rr-muted text-xs uppercase tracking-wider">
                <th className="py-3 px-4 font-semibold cursor-pointer select-none" onClick={() => handleSort('name')}>
                  <div className="flex items-center gap-1">Player <ArrowUpDown className="w-3 h-3" /></div>
                </th>
                <th className="py-3 px-4 font-semibold">Discipline</th>
                <th className="py-3 px-4 font-semibold">Format</th>
                <th className="py-3 px-4 font-semibold">Tactical Role</th>
                <th className="py-3 px-4 font-semibold text-right cursor-pointer select-none" onClick={() => handleSort('balls')}>
                  <div className="flex items-center justify-end gap-1">Balls <ArrowUpDown className="w-3 h-3" /></div>
                </th>
                <th className="py-3 px-4 font-semibold text-right cursor-pointer select-none" onClick={() => handleSort('matches')}>
                  <div className="flex items-center justify-end gap-1">Matches <ArrowUpDown className="w-3 h-3" /></div>
                </th>
                <th className="py-3 px-4 font-semibold text-right cursor-pointer select-none" onClick={() => handleSort('primaryMetricVal')}>
                  <div className="flex items-center justify-end gap-1">Metric <ArrowUpDown className="w-3 h-3" /></div>
                </th>
                <th className="py-3 px-4 font-semibold text-right cursor-pointer select-none" onClick={() => handleSort('contextDelta')}>
                  <div className="flex items-center justify-end gap-1">&Delta; Context <ArrowUpDown className="w-3 h-3" /></div>
                </th>
                <th className="py-3 px-4 font-semibold text-right cursor-pointer select-none" onClick={() => handleSort('dotPct')}>
                  <div className="flex items-center justify-end gap-1">Dot % <ArrowUpDown className="w-3 h-3" /></div>
                </th>
                <th className="py-3 px-4 font-semibold text-right cursor-pointer select-none" onClick={() => handleSort('boundaryPct')}>
                  <div className="flex items-center justify-end gap-1">Bnd % <ArrowUpDown className="w-3 h-3" /></div>
                </th>
                <th className="py-3 px-4 font-semibold">Tier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rr-border text-xs">
              {loading ? (
                <tr>
                  <td colSpan={11} className="py-12 text-center text-rr-muted">Loading cohort records...</td>
                </tr>
              ) : paginated.length === 0 ? (
                <tr>
                  <td colSpan={11} className="py-12 text-center text-rr-muted">No records match the selected filters.</td>
                </tr>
              ) : (
                paginated.map((r) => (
                  <tr key={r.id} className="hover:bg-rr-pale transition-colors">
                    <td className="py-3 px-4 font-bold text-rr-charcoal">{r.name}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        r.discipline === 'BATTER' ? 'bg-rr-soft text-rr-deep' : 'bg-blue-50 text-rr-rare'
                      }`}>
                        {r.discipline}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rr-warm text-rr-muted border border-rr-border">
                        {r.format}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-rr-charcoal">{r.role}</td>
                    <td className="py-3 px-4 text-right font-mono font-medium">{r.balls}</td>
                    <td className="py-3 px-4 text-right font-mono text-rr-muted">{r.matches}</td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-rr-charcoal">
                      {typeof r.primaryMetricVal === 'number' ? r.primaryMetricVal.toFixed(1) : '-'}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-rr-charcoal">
                      {typeof r.contextDelta === 'number'
                        ? (r.contextDelta > 0 ? `+${r.contextDelta.toFixed(1)}` : r.contextDelta.toFixed(1))
                        : '-'}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-rr-muted">
                      {typeof r.dotPct === 'number' ? `${r.dotPct.toFixed(1)}%` : '-'}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-rr-muted">
                      {typeof r.boundaryPct === 'number' ? `${r.boundaryPct.toFixed(1)}%` : '-'}
                    </td>
                    <td className="py-3 px-4">
                      <TierBadge tier={r.tier} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="flex items-center justify-between px-4 py-3 bg-rr-warm border-t border-rr-border text-xs">
          <div className="text-rr-muted">
            Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, filtered.length)} of {filtered.length} entries
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(p - 1, 1))}
              disabled={page === 1}
              className="p-1 rounded border border-rr-border bg-white text-rr-charcoal hover:bg-rr-soft disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2 font-medium text-rr-charcoal">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
              disabled={page === totalPages}
              className="p-1 rounded border border-rr-border bg-white text-rr-charcoal hover:bg-rr-soft disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
