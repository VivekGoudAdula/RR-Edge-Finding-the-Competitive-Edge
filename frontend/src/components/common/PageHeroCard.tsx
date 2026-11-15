import React from 'react';

export interface PageHeroCardProps {
  /** Uppercase category or status pill badge text */
  badge?: string;
  /** Optional icon rendered inside or next to the badge */
  badgeIcon?: React.ReactNode;
  /** Secondary context or subtitle text shown next to the badge */
  badgeContext?: string;
  /** Page or section title */
  title: string | React.ReactNode;
  /** 1-2 sentence description explaining the analytical purpose */
  description?: string | React.ReactNode;
  /** Optional right-aligned action buttons, tabs, or toggles */
  actions?: React.ReactNode;
  /** Extra container class names */
  className?: string;
}

/**
 * Standardized Page Hero Card Component for RR EDGE.
 * Adopts the sleek Behavioral Dynamics dark gradient styling across all sections
 * while maintaining a unified, compact vertical height to preserve screen real estate.
 */
export const PageHeroCard: React.FC<PageHeroCardProps> = ({
  badge,
  badgeIcon,
  badgeContext,
  title,
  description,
  actions,
  className = '',
}) => {
  return (
    <div
      style={{ background: 'linear-gradient(to right, #B90063, #25212A)' }}
      className={`rounded-2xl px-5 py-4 sm:px-6 sm:py-4 text-white shadow-card relative overflow-hidden border border-white/10 ${className}`}
    >
      {/* Ambient background glow matching Behavioral Dynamics */}
      <div className="absolute right-0 top-0 bottom-0 w-80 bg-rr-pink/15 blur-3xl pointer-events-none" />

      <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Left Column: Badge, Title & Description */}
        <div className="max-w-3xl space-y-1 min-w-0">
          {(badge || badgeContext) && (
            <div className="flex flex-wrap items-center gap-2">
              {badge && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-white/10 text-white text-[11px] font-semibold backdrop-blur-md border border-white/15 tracking-wide uppercase">
                  {badgeIcon}
                  <span>{badge}</span>
                </span>
              )}
              {badgeContext && (
                <span className="text-[11px] text-slate-200/80 font-medium">
                  {badgeContext}
                </span>
              )}
            </div>
          )}

          <h1 className="text-xl sm:text-2xl font-display font-extrabold tracking-tight text-white leading-tight">
            {title}
          </h1>

          {description && (
            <p className="text-xs sm:text-sm text-slate-200/90 leading-snug line-clamp-2">
              {description}
            </p>
          )}
        </div>

        {/* Right Column: Actions / Toggles / Controls */}
        {actions && (
          <div className="flex-shrink-0 flex flex-wrap items-center gap-2 self-start md:self-center">
            {actions}
          </div>
        )}
      </div>
    </div>
  );
};

