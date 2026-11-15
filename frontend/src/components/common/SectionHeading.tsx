import React from 'react';

interface SectionHeadingProps {
  badge?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export const SectionHeading: React.FC<SectionHeadingProps> = ({
  badge,
  title,
  description,
  action,
}) => {
  return (
    <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-6">
      <div>
        {badge && (
          <div className="inline-flex items-center gap-2 mb-2">
            <span className="w-2 h-2 rounded-full bg-rr-pink"></span>
            <span className="text-xs font-bold uppercase tracking-widest text-rr-deepPink">
              {badge}
            </span>
          </div>
        )}
        <h2 className="text-xl md:text-2xl font-extrabold text-rr-charcoal tracking-tight font-heading">
          {title}
        </h2>
        {description && (
          <p className="mt-1 text-sm text-rr-muted max-w-2xl leading-relaxed">
            {description}
          </p>
        )}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
};

export const LoadingSkeleton: React.FC<{ rows?: number }> = ({ rows = 4 }) => {
  return (
    <div className="space-y-3 animate-pulse">
      <div className="h-8 bg-pink-100/50 rounded-lg w-1/3 mb-4"></div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-14 bg-gray-100 rounded-xl w-full"></div>
      ))}
    </div>
  );
};

