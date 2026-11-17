import React, { useState } from 'react';
import { Analytics } from '@vercel/analytics/react';
import { Sidebar, PageId } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { ExecutiveOverview } from './pages/ExecutiveOverview';
import { PressureIntelligence } from './pages/PressureIntelligence';
import { BatterIntelligence } from './pages/BatterIntelligence';
import { BowlerIntelligence } from './pages/BowlerIntelligence';
import { PlayerComparisonLab } from './pages/PlayerComparisonLab';
import { BehavioralIntelligence } from './pages/BehavioralIntelligence';
import { MethodologyLab } from './pages/MethodologyLab';
import { ModelLab } from './pages/ModelLab';
import { DataExplorer } from './pages/DataExplorer';
import { ScenarioLab } from './pages/ScenarioLab';
import { PlayerGallery } from './pages/PlayerGallery';
import { CricketSimulator } from './pages/CricketSimulator';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('overview');
  const [mobileOpen, setMobileOpen] = useState(false);
  const [selectedPlayerId, setSelectedPlayerId] = useState<number | undefined>(undefined);

  const handleNavigate = (page: PageId, playerId?: number) => {
    setCurrentPage(page);
    setSelectedPlayerId(playerId);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-rr-warm bg-grid-pattern flex text-rr-charcoal font-sans antialiased">
      {/* Left Navigation Sidebar */}
      <Sidebar
        currentPage={currentPage}
        onSelectPage={(page) => handleNavigate(page)}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64 xl:pl-72 transition-all bg-grid-pattern">
        {/* Top Header */}
        <Header
          currentPage={currentPage}
          onOpenMobile={() => setMobileOpen(true)}
        />

        {/* Dynamic Page Views */}
        <main className="flex-1 px-3 sm:px-5 lg:px-6 py-5 max-w-[1600px] mx-auto w-full">
          <ErrorBoundary>
            {currentPage === 'overview' && (
              <ExecutiveOverview onNavigate={handleNavigate} />
            )}
            {currentPage === 'pressure' && (
              <PressureIntelligence />
            )}
            {currentPage === 'batters' && (
              <BatterIntelligence initialPlayerId={selectedPlayerId} />
            )}
            {currentPage === 'bowlers' && (
              <BowlerIntelligence initialPlayerId={selectedPlayerId} />
            )}
            {currentPage === 'scenarios' && (
              <ScenarioLab
                onNavigateToGallery={(playerId) => handleNavigate('gallery', playerId)}
              />
            )}
            {currentPage === 'simulator' && (
              <CricketSimulator />
            )}
            {currentPage === 'gallery' && (
              <PlayerGallery
                initialPlayerId={selectedPlayerId}
                onNavigateToScenarios={(scenarioId, playerId) => handleNavigate('scenarios', playerId)}
                onNavigateToComparison={(playerId) => handleNavigate('comparison', playerId)}
              />
            )}
            {currentPage === 'comparison' && (
              <PlayerComparisonLab />
            )}
            {currentPage === 'behavioral' && (
              <BehavioralIntelligence />
            )}
            {currentPage === 'ml_lab' && (
              <ModelLab />
            )}
            {currentPage === 'methodology' && (
              <MethodologyLab />
            )}
            {currentPage === 'explorer' && (
              <DataExplorer />
            )}
          </ErrorBoundary>
        </main>
      </div>
      <Analytics />
    </div>
  );
};

export default App;

