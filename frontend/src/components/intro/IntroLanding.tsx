import React, { useState, useEffect, useCallback } from 'react';
import { ArrowRight, Sparkles, Shield, Swords, Gauge, Gamepad2, Database, Compass, Award } from 'lucide-react';
import { PageId } from '../layout/Sidebar';

interface IntroLandingProps {
  onEnterDashboard: (targetPage?: PageId) => void;
}

export const IntroLanding: React.FC<IntroLandingProps> = ({ onEnterDashboard }) => {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [isExiting, setIsExiting] = useState(false);

  // Parallax pointer tracking (normalized -1 to 1)
  const handleMouseMove = useCallback((e: MouseEvent) => {
    const { innerWidth, innerHeight } = window;
    const x = (e.clientX / innerWidth) * 2 - 1;
    const y = (e.clientY / innerHeight) * 2 - 1;
    setMousePos({ x, y });
  }, []);

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [handleMouseMove]);

  // Keyboard shortcut (Enter or Space to enter dashboard)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter') {
        handleEnter();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleEnter = (page?: PageId) => {
    setIsExiting(true);
    setTimeout(() => {
      onEnterDashboard(page || 'overview');
    }, 450);
  };

  return (
    <div
      className={`fixed inset-0 z-50 overflow-hidden bg-[#FFFBFD] flex flex-col justify-between selection:bg-rr-soft selection:text-rr-deep transition-all duration-500 ${
        isExiting ? 'opacity-0 scale-95 pointer-events-none' : 'opacity-100 scale-100'
      }`}
    >
      {/* Background Layer 1: Pink Grid Pattern */}
      <div className="absolute inset-0 bg-grid-pattern pointer-events-none opacity-80" />

      {/* Background Layer 2: Subtle Radiating Sunburst Lines (Inspired by Ruby reference) */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden">
        <svg
          viewBox="0 0 1000 1000"
          className="w-[140vw] max-w-[1500px] h-[140vw] max-h-[1500px] opacity-25 animate-ray-rotate"
          style={{ willChange: 'transform' }}
        >
          <g stroke="#E50057" strokeWidth="1" strokeDasharray="3 7">
            {Array.from({ length: 36 }).map((_, i) => (
              <line
                key={i}
                x1="500"
                y1="500"
                x2={500 + 500 * Math.cos((i * 10 * Math.PI) / 180)}
                y2={500 + 500 * Math.sin((i * 10 * Math.PI) / 180)}
              />
            ))}
          </g>
        </svg>
      </div>

      {/* Background Layer 3: Soft Central Glow / Aura */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[650px] rounded-full bg-gradient-to-r from-pink-300/20 via-rose-200/25 to-amber-200/15 blur-3xl pointer-events-none animate-pulse-glow" />

      {/* =========================================================================
          FLOATING VISUAL ASSETS (Rajasthan Royalty × Cricket Architecture)
          Arranged around perimeter with depth, scale, and subtle parallax
         ========================================================================= */}

      {/* 1. TOP-LEFT: Hawa Mahal (Illuminated in Pink) */}
      <div
        className="absolute top-12 sm:top-14 lg:top-16 left-2 sm:left-6 lg:left-12 pointer-events-none transition-transform duration-300 ease-out z-10"
        style={{
          transform: `translate3d(${mousePos.x * -16}px, ${mousePos.y * -12}px, 0)`,
        }}
      >
        <div className="animate-float-slow group cursor-default pointer-events-auto">
          <img
            src="/intro-assets/hawa-mahal.png"
            alt="Hawa Mahal illuminated in Royal Pink"
            className="w-36 sm:w-52 md:w-64 lg:w-72 xl:w-80 h-auto object-contain filter drop-shadow-[0_12px_24px_rgba(229,0,87,0.18)] opacity-90 hover:opacity-100 transition-opacity"
          />
          <div className="hidden xl:block absolute -bottom-3 left-6 px-2.5 py-0.5 rounded-full bg-white/90 backdrop-blur-xs border border-pink-200/80 text-[10px] font-bold text-rr-charcoal shadow-xs">
            Hawa Mahal • Jaipur
          </div>
        </div>
      </div>

      {/* 2. TOP-RIGHT: Amber Fort & Palace Architecture */}
      <div
        className="absolute top-10 sm:top-12 lg:top-14 right-2 sm:right-6 lg:right-12 pointer-events-none transition-transform duration-300 ease-out z-10"
        style={{
          transform: `translate3d(${mousePos.x * 18}px, ${mousePos.y * -14}px, 0)`,
        }}
      >
        <div className="animate-float-medium group cursor-default pointer-events-auto">
          <img
            src="/intro-assets/amber-fort.png"
            alt="Amber Fort Fortress & Hilltop Palace"
            className="w-44 sm:w-60 md:w-72 lg:w-84 xl:w-96 h-auto object-contain filter drop-shadow-[0_14px_28px_rgba(229,0,87,0.18)] opacity-90 hover:opacity-100 transition-opacity"
          />
          <div className="hidden xl:block absolute -bottom-3 right-8 px-2.5 py-0.5 rounded-full bg-white/90 backdrop-blur-xs border border-pink-200/80 text-[10px] font-bold text-rr-charcoal shadow-xs">
            Amber Fort Architecture
          </div>
        </div>
      </div>

      {/* 3. UPPER-MID LEFT: Chhatri Royal Pavilion */}
      <div
        className="hidden md:block absolute top-[36%] left-4 lg:left-14 pointer-events-none transition-transform duration-300 ease-out z-10"
        style={{
          transform: `translate3d(${mousePos.x * -24}px, ${mousePos.y * 10}px, 0)`,
        }}
      >
        <div className="animate-float-reverse">
          <img
            src="/intro-assets/chhatri-pavilion.png"
            alt="Rajasthan Chhatri Royal Pavilion"
            className="w-20 md:w-28 lg:w-36 h-auto object-contain filter drop-shadow-[0_8px_18px_rgba(229,0,87,0.16)] opacity-85"
          />
        </div>
      </div>

      {/* 4. MID-LEFT: Cricket Ball with Pink Motion Trails */}
      <div
        className="absolute top-[48%] sm:top-[44%] left-1 sm:left-4 lg:left-20 pointer-events-none transition-transform duration-300 ease-out z-20"
        style={{
          transform: `translate3d(${mousePos.x * -32}px, ${mousePos.y * 20}px, 0)`,
        }}
      >
        <div className="animate-float-fast">
          <img
            src="/intro-assets/cricket-ball-trail.png"
            alt="Cricket ball with neon pink motion trail"
            className="w-24 sm:w-32 md:w-40 lg:w-44 h-auto object-contain filter drop-shadow-[0_10px_20px_rgba(229,0,87,0.25)]"
          />
        </div>
      </div>

      {/* 5. UPPER-MID RIGHT: Desert Camel with Pink Sun */}
      <div
        className="hidden lg:block absolute top-[33%] right-8 xl:right-16 pointer-events-none transition-transform duration-300 ease-out z-10"
        style={{
          transform: `translate3d(${mousePos.x * 22}px, ${mousePos.y * 14}px, 0)`,
        }}
      >
        <div className="animate-float-slow">
          <img
            src="/intro-assets/desert-camel.png"
            alt="Desert Camel Rider against Royal Pink Sun"
            className="w-36 lg:w-48 xl:w-56 h-auto object-contain filter drop-shadow-[0_10px_22px_rgba(229,0,87,0.18)] opacity-90"
          />
        </div>
      </div>

      {/* 6. MID-RIGHT: Cricket Stadium with Floodlights */}
      <div
        className="hidden sm:block absolute top-[48%] right-2 sm:right-6 lg:right-20 pointer-events-none transition-transform duration-300 ease-out z-10"
        style={{
          transform: `translate3d(${mousePos.x * 28}px, ${mousePos.y * 18}px, 0)`,
        }}
      >
        <div className="animate-float-medium">
          <img
            src="/intro-assets/cricket-stadium.png"
            alt="Cricket stadium illuminated under floodlights"
            className="w-40 sm:w-52 md:w-64 lg:w-72 h-auto object-contain filter drop-shadow-[0_12px_24px_rgba(229,0,87,0.2)] opacity-85"
          />
        </div>
      </div>

      {/* 7. BOTTOM-LEFT: Batter Silhouette Playing Drive */}
      <div
        className="absolute bottom-8 sm:bottom-12 lg:bottom-16 left-2 sm:left-8 lg:left-16 pointer-events-none transition-transform duration-300 ease-out z-20"
        style={{
          transform: `translate3d(${mousePos.x * -20}px, ${mousePos.y * 24}px, 0)`,
        }}
      >
        <div className="animate-float-medium">
          <img
            src="/intro-assets/batter-drive.png"
            alt="Batter playing stroke with pink swoosh trail"
            className="w-24 sm:w-32 md:w-44 lg:w-52 h-auto object-contain filter drop-shadow-[0_14px_28px_rgba(229,0,87,0.25)]"
          />
        </div>
      </div>

      {/* 8. BOTTOM-LEFT-CENTER: Stumps & Bails with Pink Glow */}
      <div
        className="hidden md:block absolute bottom-12 lg:bottom-16 left-[22%] lg:left-[24%] pointer-events-none transition-transform duration-300 ease-out z-15"
        style={{
          transform: `translate3d(${mousePos.x * -12}px, ${mousePos.y * 16}px, 0)`,
        }}
      >
        <div className="animate-float-reverse">
          <img
            src="/intro-assets/cricket-stumps.png"
            alt="Cricket stumps and bails"
            className="w-16 md:w-20 lg:w-24 h-auto object-contain filter drop-shadow-[0_8px_18px_rgba(229,0,87,0.22)] opacity-85"
          />
        </div>
      </div>

      {/* 9. BOTTOM-RIGHT: Bowler Silhouette in Delivery */}
      <div
        className="absolute bottom-8 sm:bottom-12 lg:bottom-16 right-2 sm:right-8 lg:right-16 pointer-events-none transition-transform duration-300 ease-out z-20"
        style={{
          transform: `translate3d(${mousePos.x * 24}px, ${mousePos.y * 22}px, 0)`,
        }}
      >
        <div className="animate-float-fast">
          <img
            src="/intro-assets/bowler-delivery.png"
            alt="Bowler in delivery action with pink ball trail"
            className="w-22 sm:w-28 md:w-38 lg:w-46 h-auto object-contain filter drop-shadow-[0_14px_28px_rgba(229,0,87,0.25)]"
          />
        </div>
      </div>

      {/* 10. BOTTOM-RIGHT-CENTER: Cricket Helmet with RR Crest */}
      <div
        className="hidden sm:block absolute bottom-12 lg:bottom-16 right-[22%] lg:right-[24%] pointer-events-none transition-transform duration-300 ease-out z-15"
        style={{
          transform: `translate3d(${mousePos.x * 14}px, ${mousePos.y * 18}px, 0)`,
        }}
      >
        <div className="animate-float-slow">
          <img
            src="/intro-assets/cricket-helmet.png"
            alt="Cricket helmet with Rajasthan Royals crest"
            className="w-20 md:w-24 lg:w-28 h-auto object-contain filter drop-shadow-[0_8px_18px_rgba(229,0,87,0.2)] opacity-90"
          />
        </div>
      </div>

      {/* 11. TOP-RIGHT EMBLEM: Royal Rajasthan Flag */}
      <div
        className="hidden xl:block absolute top-[28%] right-2 pointer-events-none transition-transform duration-300 ease-out z-10"
        style={{
          transform: `translate3d(${mousePos.x * 30}px, ${mousePos.y * -8}px, 0)`,
        }}
      >
        <div className="animate-float-reverse">
          <img
            src="/intro-assets/rajasthan-flag.png"
            alt="Royal Rajasthan Flag"
            className="w-28 h-auto object-contain filter drop-shadow-[0_8px_16px_rgba(229,0,87,0.2)] opacity-80"
          />
        </div>
      </div>

      {/* 12. BOTTOM CENTER-BACKGROUND: Flowing Pink Ribbon Wave */}
      <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 w-full max-w-[1200px] pointer-events-none opacity-40 z-0">
        <img
          src="/intro-assets/pink-ribbon.png"
          alt="Flowing royal pink fabric"
          className="w-full h-auto object-contain filter blur-[1px]"
        />
      </div>

      {/* =========================================================================
          TOP NAVIGATION BAR
         ========================================================================= */}
      <header className="relative z-30 w-full px-4 sm:px-8 lg:px-14 py-4 sm:py-5 flex items-center justify-between">
        {/* Left: Brand Identity Mark */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-white border border-pink-100 shadow-xs flex items-center justify-center p-1.5">
            <img src="/rr_emblem.png" alt="RR Crest" className="w-full h-full object-contain" />
          </div>
          <div className="hidden xs:flex flex-col">
            <span className="text-xs sm:text-sm font-extrabold tracking-wider text-rr-navy leading-none">
              RR EDGE
            </span>
            <span className="text-[10px] font-semibold text-rr-deep tracking-wider uppercase mt-0.5">
              SupeRR Selector 2026
            </span>
          </div>
        </div>

        {/* Center: Competition Badge */}
        <div className="hidden md:inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/80 backdrop-blur-sm border border-pink-200/60 shadow-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
          <span className="text-[11px] font-bold text-rr-navy tracking-wide">
            AUDITED SUBMISSION • PRIMARY PRESSURE COHORT
          </span>
        </div>

        {/* Right: Category Label & Direct Enter Button */}
        <div className="flex items-center gap-2.5">
          <span className="hidden sm:inline-block px-3 py-1 rounded-full bg-pink-50 text-rr-deep text-xs font-bold tracking-wider border border-pink-100">
            CRICKET INTELLIGENCE PLATFORM
          </span>
          <button
            onClick={() => handleEnter()}
            className="inline-flex items-center gap-1.5 px-3 sm:px-4 py-1.5 rounded-xl bg-rr-navy hover:bg-rr-darkNavy text-white text-xs font-bold tracking-wide shadow-sm hover:shadow-md transition-all group"
          >
            <span>Enter</span>
            <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-1" />
          </button>
        </div>
      </header>

      {/* =========================================================================
          CENTRAL HERO COMPOSITION (The Heart of RR EDGE)
         ========================================================================= */}
      <main className="relative z-30 flex-1 flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 text-center max-w-4xl mx-auto my-auto py-2">
        {/* Eyebrow Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/95 backdrop-blur-md border border-pink-200/90 shadow-sm mb-4 sm:mb-5">
          <Sparkles className="w-3.5 h-3.5 text-rr-pink animate-pulse" />
          <span className="text-xs font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-rr-pink via-rose-600 to-rr-deep">
            FINDING THE COMPETITIVE EDGE
          </span>
          <span className="hidden sm:inline-block w-1 h-1 rounded-full bg-pink-300" />
          <span className="hidden sm:inline-block text-[11px] font-semibold text-slate-500">
            Season 2 Audited Engine
          </span>
        </div>

        {/* Central Logo Composition */}
        <div className="relative mb-3 sm:mb-4 group">
          {/* Subtle back-glow */}
          <div className="absolute inset-0 bg-pink-400/20 blur-2xl rounded-full scale-110 pointer-events-none" />

          {/* Real Supplied Logo */}
          <img
            src="/logo.png"
            alt="RR EDGE — Finding the Competitive Edge"
            className="relative w-auto max-h-20 sm:max-h-24 md:max-h-28 lg:max-h-32 object-contain drop-shadow-[0_8px_20px_rgba(229,0,87,0.15)] mx-auto transition-transform duration-300 group-hover:scale-[1.02]"
          />
        </div>

        {/* Hero Tagline / Pitch */}
        <h1 className="text-xl sm:text-2xl md:text-3xl font-extrabold text-rr-navy tracking-tight max-w-2xl mb-3 sm:mb-4">
          Uncovering Latent Match Leverage{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-rr-pink via-pink-600 to-rr-deep">
            Under Peak Pressure
          </span>
        </h1>

        {/* Editorial Description */}
        <p className="text-xs sm:text-sm md:text-base text-slate-600 max-w-xl leading-relaxed mb-6 sm:mb-7 font-normal">
          A data-driven approach to identifying players who deliver when the game gets difficult.
          Empirical Bayes shrinkage, Context RAE/RCAE, and match-cluster bootstrap uncertainty across 192,373 deliveries.
        </p>

        {/* Prominent Primary CTA Button */}
        <div className="relative group mb-5 sm:mb-6">
          {/* Button Outer Pulse Ring */}
          <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-rr-pink via-rose-500 to-rr-deep opacity-60 blur-md group-hover:opacity-100 group-hover:blur-lg transition-all duration-300" />

          <button
            onClick={() => handleEnter()}
            className="relative flex items-center justify-center gap-3 px-8 sm:px-10 py-3.5 sm:py-4 rounded-xl bg-gradient-to-r from-rr-pink via-[#E6007E] to-rr-deep text-white font-extrabold text-sm sm:text-base tracking-wide shadow-lg hover:shadow-pink-500/30 transition-all duration-300 active:scale-[0.98] overflow-hidden"
          >
            {/* Shimmer sweep effect */}
            <div className="absolute inset-0 w-1/2 h-full bg-white/20 skew-x-12 animate-shimmer pointer-events-none" />

            <span className="relative z-10">ENTER DASHBOARD</span>
            <ArrowRight className="relative z-10 w-5 h-5 transition-transform duration-300 group-hover:translate-x-2" />
          </button>
        </div>

        {/* Supporting Micro-Text Below Button */}
        <div className="flex items-center justify-center gap-2 text-[10px] sm:text-xs font-bold text-slate-500 tracking-wider uppercase mb-5 sm:mb-6">
          <span>PRESSURE PERFORMANCE</span>
          <span>•</span>
          <span>PLAYER RELIABILITY</span>
          <span>•</span>
          <span>IPL & T20I</span>
        </div>

        {/* Live Metrics Showcase Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3 w-full max-w-2xl bg-white/90 backdrop-blur-md rounded-2xl border border-pink-200/80 p-2.5 sm:p-3 shadow-xs">
          <div className="flex flex-col items-center justify-center py-1.5 px-2 rounded-xl bg-pink-50/60 border border-pink-100/60">
            <span className="text-sm sm:text-base font-extrabold text-rr-deep">192,373</span>
            <span className="text-[10px] font-semibold text-slate-500 tracking-tight">Pressure Deliveries</span>
          </div>
          <div className="flex flex-col items-center justify-center py-1.5 px-2 rounded-xl bg-pink-50/60 border border-pink-100/60">
            <span className="text-sm sm:text-base font-extrabold text-rr-navy">888</span>
            <span className="text-[10px] font-semibold text-slate-500 tracking-tight">Audited Players</span>
          </div>
          <div className="flex flex-col items-center justify-center py-1.5 px-2 rounded-xl bg-pink-50/60 border border-pink-100/60">
            <span className="text-sm sm:text-base font-extrabold text-rr-pink">M = 45</span>
            <span className="text-[10px] font-semibold text-slate-500 tracking-tight">Bayes Shrinkage</span>
          </div>
          <div className="flex flex-col items-center justify-center py-1.5 px-2 rounded-xl bg-pink-50/60 border border-pink-100/60">
            <span className="text-sm sm:text-base font-extrabold text-amber-600">10,000</span>
            <span className="text-[10px] font-semibold text-slate-500 tracking-tight">Bootstrap Runs</span>
          </div>
        </div>
      </main>

      {/* =========================================================================
          BOTTOM BAR: DIRECT EXPLORATION SHORTCUTS FOR JUDGES
         ========================================================================= */}
      <footer className="relative z-30 w-full px-4 sm:px-8 py-3 sm:py-4 bg-white/70 backdrop-blur-md border-t border-pink-100 flex flex-col sm:flex-row items-center justify-between gap-2.5">
        <div className="flex items-center gap-2 text-[11px] font-medium text-slate-500">
          <span className="w-1.5 h-1.5 rounded-full bg-rr-pink" />
          <span>Quick jump to core module:</span>
        </div>

        {/* One-Click Shortcut Pills */}
        <div className="flex flex-wrap items-center justify-center gap-1.5 sm:gap-2">
          <button
            onClick={() => handleEnter('overview')}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:border-pink-300 hover:bg-pink-50 text-[11px] font-semibold text-slate-700 hover:text-rr-deep transition-all shadow-2xs"
          >
            <Compass className="w-3 h-3 text-rr-pink" />
            <span>Overview</span>
          </button>
          <button
            onClick={() => handleEnter('batters')}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:border-pink-300 hover:bg-pink-50 text-[11px] font-semibold text-slate-700 hover:text-rr-deep transition-all shadow-2xs"
          >
            <Swords className="w-3 h-3 text-rr-pink" />
            <span>Top Batters</span>
          </button>
          <button
            onClick={() => handleEnter('bowlers')}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:border-pink-300 hover:bg-pink-50 text-[11px] font-semibold text-slate-700 hover:text-rr-deep transition-all shadow-2xs"
          >
            <Shield className="w-3 h-3 text-rr-pink" />
            <span>Top Bowlers</span>
          </button>
          <button
            onClick={() => handleEnter('simulator')}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-pink-300 bg-pink-50/50 hover:bg-pink-100/60 text-[11px] font-bold text-rr-deep transition-all shadow-2xs"
          >
            <Gamepad2 className="w-3 h-3 text-rr-pink" />
            <span>2D Simulator</span>
          </button>
          <button
            onClick={() => handleEnter('gallery')}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:border-pink-300 hover:bg-pink-50 text-[11px] font-semibold text-slate-700 hover:text-rr-deep transition-all shadow-2xs"
          >
            <Award className="w-3 h-3 text-rr-pink" />
            <span>888 Gallery</span>
          </button>
          <button
            onClick={() => handleEnter('explorer')}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:border-pink-300 hover:bg-pink-50 text-[11px] font-semibold text-slate-700 hover:text-rr-deep transition-all shadow-2xs"
          >
            <Database className="w-3 h-3 text-rr-pink" />
            <span>Data Explorer</span>
          </button>
        </div>

        {/* Confidential Scouting Platform Badge */}
        <div className="hidden lg:flex items-center gap-1.5 text-[10px] font-semibold text-slate-400">
          <span>RR EDGE v2.0 • Rajasthan Royals Selection Intelligence</span>
        </div>
      </footer>
    </div>
  );
};
