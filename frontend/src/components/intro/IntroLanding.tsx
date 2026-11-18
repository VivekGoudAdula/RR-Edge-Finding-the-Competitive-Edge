import React, { useState, useEffect, useCallback } from 'react';
import { ArrowRight } from 'lucide-react';
import { PageId } from '../layout/Sidebar';

interface IntroLandingProps {
  onEnterDashboard: (targetPage?: PageId) => void;
}

export const IntroLanding: React.FC<IntroLandingProps> = ({ onEnterDashboard }) => {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [isExiting, setIsExiting] = useState(false);

  // Suppress right-click context menu everywhere on the intro landing so images feel like native UI
  useEffect(() => {
    const handleContextMenu = (e: MouseEvent) => {
      e.preventDefault();
      return false;
    };
    window.addEventListener('contextmenu', handleContextMenu);
    return () => window.removeEventListener('contextmenu', handleContextMenu);
  }, []);

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
      onContextMenu={(e) => {
        e.preventDefault();
        return false;
      }}
      className={`fixed inset-0 z-50 overflow-hidden bg-[#FFFBFD] flex flex-col items-center justify-center select-none cursor-default transition-all duration-500 ${
        isExiting ? 'opacity-0 scale-95 pointer-events-none' : 'opacity-100 scale-100'
      }`}
    >
      {/* Background Layer 1: Pink Grid Pattern */}
      <div className="absolute inset-0 bg-grid-pattern pointer-events-none opacity-80" />

      {/* Background Layer 2: Subtle Radiating Sunburst Lines */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden">
        <svg
          viewBox="0 0 1000 1000"
          className="w-[140vw] max-w-[1500px] h-[140vw] max-h-[1500px] opacity-25 animate-ray-rotate select-none pointer-events-none"
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

      {/* Fullscreen Royal Frame Asset (bg.png) - 100% Protected, Non-Draggable Canvas-like UI */}
      <img
        src="/intro-assets/bg.png"
        alt=""
        draggable={false}
        onContextMenu={(e) => e.preventDefault()}
        className="absolute inset-0 w-full h-full object-fill pointer-events-none z-0 select-none opacity-95"
      />

      {/* =========================================================================
          FLOATING VISUAL ASSETS (Evenly Distributed Across Perimeter & Top Corners)
          All assets are pointer-events-none, non-draggable, and context-menu blocked
         ========================================================================= */}

      {/* 1. TOP-LEFT CORNER (Fills empty white space): Cricket Ball with Pink Motion Trails */}
      <div
        className="absolute top-8 sm:top-10 md:top-14 left-8 sm:left-14 md:left-20 lg:left-28 pointer-events-none transition-transform duration-300 ease-out z-20 select-none mix-blend-multiply"
        style={{
          transform: `translate3d(${mousePos.x * -22}px, ${mousePos.y * -14}px, 0)`,
        }}
      >
        <div className="animate-float-fast">
          <img
            src="/intro-assets/ball.png"
            alt=""
            draggable={false}
            onContextMenu={(e) => e.preventDefault()}
            className="w-28 sm:w-36 md:w-44 lg:w-52 h-auto object-contain filter drop-shadow-[0_8px_18px_rgba(229,0,87,0.18)] select-none pointer-events-none"
          />
        </div>
      </div>

      {/* 2. TOP-RIGHT CORNER (Fills empty white space): Royal Rajasthan Flag */}
      <div
        className="absolute top-8 sm:top-10 md:top-14 right-8 sm:right-14 md:right-20 lg:right-28 pointer-events-none transition-transform duration-300 ease-out z-10 select-none mix-blend-multiply"
        style={{
          transform: `translate3d(${mousePos.x * 22}px, ${mousePos.y * -14}px, 0)`,
        }}
      >
        <div className="animate-float-reverse">
          <img
            src="/intro-assets/flag.png"
            alt=""
            draggable={false}
            onContextMenu={(e) => e.preventDefault()}
            className="w-28 sm:w-36 md:w-44 lg:w-52 h-auto object-contain filter drop-shadow-[0_8px_16px_rgba(229,0,87,0.16)] opacity-95 select-none pointer-events-none"
          />
        </div>
      </div>

      {/* 3. MID-LEFT: Glowing Stumps & Bails (Neatly proportioned) */}
      <div
        className="hidden sm:block absolute top-[48%] -translate-y-1/2 left-6 sm:left-10 md:left-14 lg:left-18 pointer-events-none transition-transform duration-300 ease-out z-15 select-none mix-blend-multiply"
        style={{
          transform: `translate3d(${mousePos.x * -16}px, ${mousePos.y * 12}px, 0)`,
        }}
      >
        <div className="animate-float-medium">
          <img
            src="/intro-assets/wickets.png"
            alt=""
            draggable={false}
            onContextMenu={(e) => e.preventDefault()}
            className="w-14 sm:w-16 md:w-20 lg:w-24 h-auto object-contain filter drop-shadow-[0_6px_14px_rgba(229,0,87,0.18)] opacity-90 select-none pointer-events-none"
          />
        </div>
      </div>

      {/* 4. MID-RIGHT: Royal Cricket Helmet */}
      <div
        className="hidden sm:block absolute top-[48%] -translate-y-1/2 right-6 sm:right-10 md:right-14 lg:right-18 pointer-events-none transition-transform duration-300 ease-out z-15 select-none mix-blend-multiply"
        style={{
          transform: `translate3d(${mousePos.x * 16}px, ${mousePos.y * 12}px, 0)`,
        }}
      >
        <div className="animate-float-slow">
          <img
            src="/intro-assets/cap.png"
            alt=""
            draggable={false}
            onContextMenu={(e) => e.preventDefault()}
            className="w-20 sm:w-26 md:w-30 lg:w-36 h-auto object-contain filter drop-shadow-[0_6px_14px_rgba(229,0,87,0.16)] opacity-95 select-none pointer-events-none"
          />
        </div>
      </div>

      {/* 5. BOTTOM-LEFT: Batter Silhouette Playing Drive */}
      <div
        className="absolute bottom-6 sm:bottom-8 md:bottom-12 left-8 sm:left-14 md:left-20 lg:left-28 pointer-events-none transition-transform duration-300 ease-out z-20 select-none mix-blend-multiply"
        style={{
          transform: `translate3d(${mousePos.x * -20}px, ${mousePos.y * 20}px, 0)`,
        }}
      >
        <div className="animate-float-medium">
          <img
            src="/intro-assets/batter.png"
            alt=""
            draggable={false}
            onContextMenu={(e) => e.preventDefault()}
            className="w-24 sm:w-32 md:w-40 lg:w-48 h-auto object-contain filter drop-shadow-[0_10px_20px_rgba(229,0,87,0.18)] select-none pointer-events-none"
          />
        </div>
      </div>

      {/* 6. BOTTOM-RIGHT: Bowler Silhouette in Delivery */}
      <div
        className="absolute bottom-6 sm:bottom-8 md:bottom-12 right-8 sm:right-14 md:right-20 lg:right-28 pointer-events-none transition-transform duration-300 ease-out z-20 select-none mix-blend-multiply"
        style={{
          transform: `translate3d(${mousePos.x * 20}px, ${mousePos.y * 20}px, 0)`,
        }}
      >
        <div className="animate-float-fast">
          <img
            src="/intro-assets/bowler.png"
            alt=""
            draggable={false}
            onContextMenu={(e) => e.preventDefault()}
            className="w-24 sm:w-32 md:w-40 lg:w-48 h-auto object-contain filter drop-shadow-[0_10px_20px_rgba(229,0,87,0.18)] select-none pointer-events-none"
          />
        </div>
      </div>

      {/* =========================================================================
          CENTRAL HERO COMPOSITION (The Heart of RR EDGE)
         ========================================================================= */}
      <main className="relative z-30 flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 text-center max-w-5xl mx-auto py-2 select-none">
        {/* Royal Cursive Script Headline (Clean 2-Line Calligraphy) */}
        <h1 className="text-center w-full mx-auto mb-4 sm:mb-6 select-none">
          {/* Normal Font Tagline on Top */}
          <span className="block text-[11px] sm:text-xs md:text-sm font-extrabold uppercase tracking-[0.28em] text-slate-500 mb-2 sm:mb-3 font-heading">
            Finding the Competitive Edge
          </span>
          <span
            className="block text-2xl sm:text-3xl md:text-[36px] lg:text-[40px] xl:text-[44px] font-normal text-rr-navy tracking-wide leading-[1.4] drop-shadow-xs font-cursive-calligraphy whitespace-nowrap py-1"
            style={{ fontFamily: "'Great Vibes', 'Alex Brush', 'Allura', 'Parisienne', cursive" }}
          >
            Uncovering Latent Match Leverage
          </span>
          <span
            className="block text-2xl sm:text-3xl md:text-[38px] lg:text-[42px] xl:text-[46px] font-normal leading-[1.5] text-[#E50057] drop-shadow-[0_4px_16px_rgba(229,0,87,0.22)] font-cursive-calligraphy whitespace-nowrap mt-1 sm:mt-2 py-1"
            style={{ fontFamily: "'Great Vibes', 'Alex Brush', 'Allura', 'Parisienne', cursive" }}
          >
            Under Peak Pressure
          </span>
        </h1>

        {/* Central Logo Composition - Pure Native Feel */}
        <div className="relative mb-6 sm:mb-8 pointer-events-none select-none">
          {/* Subtle back-glow */}
          <div className="absolute inset-0 bg-pink-400/20 blur-2xl rounded-full scale-125 pointer-events-none" />

          {/* Official Supplied Logo */}
          <img
            src="/logo.png"
            alt=""
            draggable={false}
            onContextMenu={(e) => e.preventDefault()}
            className="relative w-auto max-h-24 sm:max-h-28 md:max-h-36 lg:max-h-40 object-contain drop-shadow-[0_12px_28px_rgba(229,0,87,0.2)] mx-auto pointer-events-none select-none"
          />
        </div>

        {/* Prominent Primary CTA Button with Shining 24K Gold Border */}
        <div className="relative group mb-5 sm:mb-6 cursor-pointer">
          {/* Luxury 24K Shining Gold Border Wrapper */}
          <div className="relative p-[2.5px] rounded-full bg-gradient-to-r from-[#BF953F] via-[#FCF6BA] via-[#B38728] via-[#FBF5B7] to-[#AA771C] animate-gold-beam shadow-md transition-all duration-300">
            <button
              onClick={() => handleEnter()}
              className="relative flex items-center justify-center gap-3.5 px-10 sm:px-14 py-3.5 sm:py-4 rounded-full bg-[#E50057] hover:bg-[#D0004F] text-white font-heading font-black text-xs sm:text-sm tracking-[0.25em] uppercase transition-all duration-300 group-hover:scale-[1.01] active:scale-[0.98] overflow-hidden cursor-pointer"
            >
              {/* Shimmer sweep effect */}
              <div className="absolute inset-0 w-1/2 h-full bg-gradient-to-r from-transparent via-white/30 to-transparent skew-x-12 animate-shimmer pointer-events-none" />

              {/* Text */}
              <span className="relative z-10 font-heading font-black tracking-[0.25em] drop-shadow-xs">
                ENTER DASHBOARD
              </span>

              {/* Circular arrow icon */}
              <div className="relative z-10 w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-white/20 flex items-center justify-center border border-white/40 shadow-xs group-hover:bg-white group-hover:text-[#E50057] transition-all duration-300">
                <ArrowRight className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-0.5" />
              </div>
            </button>
          </div>
        </div>

        {/* Supporting Micro-Text Below Button */}
        <div className="flex flex-wrap items-center justify-center gap-2.5 sm:gap-4 text-[10px] sm:text-[11px] font-heading font-bold text-slate-400 tracking-[0.25em] uppercase select-none">
          <span className="hover:text-rr-deepPink transition-colors">PRESSURE PERFORMANCE</span>
          <span className="w-1.5 h-1.5 rounded-full bg-[#E50057] inline-block opacity-70" />
          <span className="hover:text-rr-deepPink transition-colors">PLAYER RELIABILITY</span>
          <span className="w-1.5 h-1.5 rounded-full bg-[#E50057] inline-block opacity-70" />
          <span className="hover:text-rr-deepPink transition-colors">IPL & T20I AUDITED</span>
        </div>
      </main>
    </div>
  );
};
