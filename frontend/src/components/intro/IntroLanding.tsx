import React, { useState, useEffect, useCallback } from 'react';
import { ArrowRight, Sparkles } from 'lucide-react';
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
      className={`fixed inset-0 z-50 overflow-hidden bg-[#FFFBFD] flex flex-col items-center justify-center selection:bg-rr-soft selection:text-rr-deep transition-all duration-500 ${
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

      {/* Fullscreen Royal Frame Asset (bg.png) */}
      <img
        src="/intro-assets/bg.png"
        alt="Royal Rajasthan Frame"
        className="absolute inset-0 w-full h-full object-fill pointer-events-none z-0 select-none opacity-95"
      />

      {/* =========================================================================
          FLOATING VISUAL ASSETS (Rajasthan Royalty × Cricket Architecture)
          Arranged around perimeter with depth, scale, and subtle parallax
         ========================================================================= */}

      {/* 1. TOP-LEFT: Hawa Mahal (Illuminated in Pink) */}
      <div
        className="absolute top-4 sm:top-6 lg:top-8 left-2 sm:left-6 lg:left-10 pointer-events-none transition-transform duration-300 ease-out z-10"
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
        className="absolute top-4 sm:top-6 lg:top-8 right-2 sm:right-6 lg:right-10 pointer-events-none transition-transform duration-300 ease-out z-10"
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

      {/* 3. UPPER-MID LEFT: Stadium Floodlight Tower Casting Pink Beams */}
      <div
        className="hidden md:block absolute top-[30%] sm:top-[32%] left-3 lg:left-10 pointer-events-none transition-transform duration-300 ease-out z-10"
        style={{
          transform: `translate3d(${mousePos.x * -24}px, ${mousePos.y * 10}px, 0)`,
        }}
      >
        <div className="animate-float-reverse">
          <img
            src="/intro-assets/floodlight-tower.png"
            alt="Stadium Floodlight Tower emitting pink light"
            className="w-24 md:w-32 lg:w-40 h-auto object-contain filter drop-shadow-[0_8px_18px_rgba(229,0,87,0.22)] opacity-90"
          />
        </div>
      </div>

      {/* 4. MID-LEFT: Cricket Ball with Pink Motion Trails */}
      <div
        className="absolute top-[50%] sm:top-[46%] left-1 sm:left-4 lg:left-16 pointer-events-none transition-transform duration-300 ease-out z-20"
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

      {/* 5. UPPER-MID RIGHT: Jal Mahal (Illuminated Water Palace) */}
      <div
        className="hidden lg:block absolute top-[28%] sm:top-[30%] right-4 xl:right-12 pointer-events-none transition-transform duration-300 ease-out z-10"
        style={{
          transform: `translate3d(${mousePos.x * 22}px, ${mousePos.y * 14}px, 0)`,
        }}
      >
        <div className="animate-float-slow group cursor-default pointer-events-auto">
          <img
            src="/intro-assets/jal-mahal.png"
            alt="Jal Mahal illuminated over the water in Jaipur"
            className="w-44 lg:w-56 xl:w-68 h-auto object-contain filter drop-shadow-[0_10px_22px_rgba(229,0,87,0.2)] opacity-90 hover:opacity-100 transition-opacity"
          />
          <div className="hidden xl:block absolute -bottom-2 right-6 px-2 py-0.5 rounded-full bg-white/90 backdrop-blur-xs border border-pink-200/80 text-[10px] font-bold text-rr-charcoal shadow-xs">
            Jal Mahal • Jaipur
          </div>
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
          CENTRAL HERO COMPOSITION (The Heart of RR EDGE)
         ========================================================================= */}
      <main className="relative z-30 flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 text-center max-w-4xl mx-auto py-2">
        {/* Eyebrow Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/95 backdrop-blur-md border border-pink-200/90 shadow-sm mb-3 sm:mb-4">
          <Sparkles className="w-3.5 h-3.5 text-rr-pink animate-pulse" />
          <span className="text-xs font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-rr-pink via-rose-600 to-rr-deep">
            FINDING THE COMPETITIVE EDGE
          </span>
          <span className="hidden sm:inline-block w-1 h-1 rounded-full bg-pink-300" />
          <span className="hidden sm:inline-block text-[11px] font-semibold text-slate-500">
            Season 2 Audited Engine
          </span>
        </div>

        {/* Hero Tagline / Pitch (Moved Up Above Logo) */}
        <h1 className="text-lg sm:text-2xl md:text-3xl font-extrabold text-rr-navy tracking-tight max-w-2xl mb-4 sm:mb-6">
          Uncovering Latent Match Leverage{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-rr-pink via-pink-600 to-rr-deep">
            Under Peak Pressure
          </span>
        </h1>

        {/* Central Logo Composition - in exact center */}
        <div className="relative mb-5 sm:mb-7 group">
          {/* Subtle back-glow */}
          <div className="absolute inset-0 bg-pink-400/20 blur-2xl rounded-full scale-125 pointer-events-none" />

          {/* Real Supplied Logo */}
          <img
            src="/logo.png"
            alt="RR EDGE — Finding the Competitive Edge"
            className="relative w-auto max-h-24 sm:max-h-28 md:max-h-36 lg:max-h-40 object-contain drop-shadow-[0_10px_25px_rgba(229,0,87,0.18)] mx-auto transition-transform duration-300 group-hover:scale-[1.03]"
          />
        </div>

        {/* Prominent Primary CTA Button */}
        <div className="relative group mb-4 sm:mb-5">
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
    </div>
  );
};
