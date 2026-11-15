import React from 'react';
import {
  LayoutDashboard,
  Gauge,
  Swords,
  Shield,
  GitCompare,
  BookOpen,
  Database,
  ChevronRight,
  Cpu,
  Activity,
  Target,
  Users,
  Gamepad2,
} from 'lucide-react';

export type PageId =
  | 'overview'
  | 'pressure'
  | 'batters'
  | 'bowlers'
  | 'scenarios'
  | 'simulator'
  | 'gallery'
  | 'comparison'
  | 'behavioral'
  | 'ml_lab'
  | 'methodology'
  | 'explorer';

interface SidebarProps {
  currentPage: PageId;
  onSelectPage: (page: PageId) => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

interface NavItem {
  id: PageId;
  label: string;
  badge?: string;
  icon: React.FC<{ className?: string }>;
}

const navItems: NavItem[] = [
  { id: 'overview', label: 'Executive Overview', icon: LayoutDashboard },
  { id: 'pressure', label: 'Pressure Intelligence', icon: Gauge, badge: 'Core' },
  { id: 'batters', label: 'Batter Intelligence', icon: Swords },
  { id: 'bowlers', label: 'Bowler Intelligence', icon: Shield },
  { id: 'scenarios', label: 'Scenario Lab', icon: Target, badge: 'Lab' },
  { id: 'simulator', label: 'Cricket Simulator', icon: Gamepad2, badge: 'Live 2D' },
  { id: 'gallery', label: 'Player Gallery', icon: Users, badge: '888' },
  { id: 'comparison', label: 'Player Comparison Lab', icon: GitCompare },
  { id: 'behavioral', label: 'Behavioral Dynamics', icon: Activity, badge: 'Behavior' },
  { id: 'ml_lab', label: 'Machine Learning Lab', icon: Cpu, badge: 'ML' },
  { id: 'methodology', label: 'Methodology & Lab', icon: BookOpen },
  { id: 'explorer', label: 'Data Explorer', icon: Database },
];

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onSelectPage,
  mobileOpen,
  onCloseMobile,
}) => {
  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-rr-charcoal/30 backdrop-blur-sm lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      {/* Main Sidebar - strictly bounded by viewport height to prevent off-screen overflow at high zoom */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 xl:w-72 bg-white border-r border-rr-border flex flex-col h-screen max-h-screen overflow-hidden transition-transform duration-300 lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header - Pinned at Top */}
        <div className="shrink-0 h-16 md:h-20 px-4 md:px-5 border-b border-rr-border bg-white flex items-center justify-center">
          <button
            onClick={() => {
              onSelectPage('overview');
              onCloseMobile();
            }}
            className="w-full h-full flex items-center justify-center group cursor-pointer focus:outline-none"
            title="RR EDGE - Return to Executive Overview"
          >
            <div className="w-full py-1 px-2 flex items-center justify-center rounded-xl group-hover:bg-rr-palePink/60 transition-colors">
              <img
                src="/logo.png"
                alt="RR EDGE — Finding the Competitive Edge"
                className="w-auto max-h-10 md:max-h-[46px] object-contain drop-shadow-sm transition-transform group-hover:scale-[1.02]"
              />
            </div>
          </button>
        </div>

        {/* Scrollable Navigation Container with sleek scrollbar */}
        <nav className="flex-1 overflow-y-auto px-2.5 py-2 space-y-1 min-h-0">
          {navItems.map((item) => {
            const active = currentPage === item.id;
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onSelectPage(item.id);
                  onCloseMobile();
                }}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all group ${
                  active
                    ? 'bg-rr-softPink text-rr-deepPink font-bold shadow-sm'
                    : 'text-rr-charcoal hover:bg-rr-palePink hover:text-rr-deepPink'
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <Icon
                    className={`w-4 h-4 shrink-0 transition-colors ${
                      active ? 'text-rr-pink' : 'text-rr-muted group-hover:text-rr-pink'
                    }`}
                  />
                  <span className="truncate">{item.label}</span>
                </div>
                {item.badge ? (
                  <span className="shrink-0 text-[10px] font-extrabold px-1.5 py-0.5 rounded-full bg-rr-pink text-white ml-1">
                    {item.badge}
                  </span>
                ) : active ? (
                  <ChevronRight className="w-4 h-4 shrink-0 text-rr-deepPink ml-1" />
                ) : null}
              </button>
            );
          })}
        </nav>

        {/* Franchise System Information - Pinned at Bottom */}
        <div className="shrink-0 p-3 m-3 rounded-xl bg-rr-palePink border border-pink-100/80 space-y-1">
          <div className="flex items-center gap-1.5">
            <span className="font-black text-xs tracking-wide text-rr-pink">RR EDGE</span>
            <span className="text-xs text-rr-muted">•</span>
            <span className="text-[11px] font-bold text-rr-navy">Platform</span>
          </div>
          <p className="text-[11px] font-semibold text-rr-charcoal leading-snug">
            Rajasthan Royals Cricket Intelligence Platform
          </p>
          <div className="pt-1.5 border-t border-pink-200/50 text-[10px] text-rr-muted leading-normal">
            Confidential Scouting System • Season 2026
          </div>
        </div>
      </aside>
    </>
  );
};
