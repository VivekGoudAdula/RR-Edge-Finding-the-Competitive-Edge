import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'pink' | 'neutral' | 'outline' | 'blue' | 'discovery';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'pink',
  size = 'md',
}) => {
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-semibold';

  let variantClasses = 'bg-rr-softPink text-rr-deepPink border border-pink-200/60';

  if (variant === 'neutral') {
    variantClasses = 'bg-gray-100 text-rr-charcoal border border-gray-200';
  } else if (variant === 'outline') {
    variantClasses = 'bg-white text-rr-charcoal border border-rr-border';
  } else if (variant === 'blue') {
    variantClasses = 'bg-blue-50 text-rr-blue border border-blue-200/60';
  } else if (variant === 'discovery') {
    variantClasses = 'bg-pink-50 text-rr-pink border border-pink-300 font-bold tracking-wide uppercase';
  }

  return (
    <span className={`inline-flex items-center rounded-full tracking-tight transition-colors ${sizeClasses} ${variantClasses}`}>
      {children}
    </span>
  );
};

export const TierBadge: React.FC<{ tier: string; title?: string }> = ({ tier, title }) => {
  const t = (tier || '').toUpperCase();
  let content = <Badge variant="neutral" size="sm">{t.replace(/_/g, ' ')}</Badge>;

  if (t.includes('CONFIDENT')) {
    content = <Badge variant="pink" size="sm">CONFIDENT</Badge>;
  } else if (t.includes('MODERATE')) {
    content = <Badge variant="neutral" size="sm">MODERATE</Badge>;
  } else if (t.includes('PROVISIONAL')) {
    content = <Badge variant="outline" size="sm">PROVISIONAL</Badge>;
  } else if (t.includes('INSUFFICIENT')) {
    content = <Badge variant="neutral" size="sm">INSUFFICIENT</Badge>;
  }

  return title ? (
    <span title={title} className="cursor-help">
      {content}
    </span>
  ) : (
    content
  );
};

export const ArchetypeBadge: React.FC<{ archetype: string }> = ({ archetype }) => {
  if (archetype === 'ROBUST_ANCHOR') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200 whitespace-nowrap">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
        ROBUST ANCHOR
      </span>
    );
  }
  if (archetype === 'DISCOVERY_UPSIDE' || archetype === 'SHRINKAGE_SENSITIVE') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rr-softPink text-rr-deepPink border border-pink-300 whitespace-nowrap">
        <span className="w-1.5 h-1.5 rounded-full bg-rr-pink animate-pulse"></span>
        DISCOVERY UPSIDE
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200 whitespace-nowrap">
      <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
      CONTEXT DEPENDENT
    </span>
  );
};

