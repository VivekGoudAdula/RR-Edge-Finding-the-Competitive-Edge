import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  delta?: string;
  deltaType?: 'positive' | 'negative' | 'neutral';
  accentEdge?: boolean;
  icon?: React.ReactNode;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  delta,
  deltaType = 'positive',
  accentEdge = false,
  icon,
}) => {
  return (
    <div
      className={`relative bg-white rounded-xl border border-rr-border p-5 shadow-rr-card transition-all duration-200 hover:shadow-rr-hover ${
        accentEdge ? 'overflow-hidden' : ''
      }`}
    >
      {accentEdge && (
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-rr-pink to-rr-deepPink" />
      )}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold text-rr-muted uppercase tracking-wider">{title}</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl lg:text-3xl font-extrabold text-rr-charcoal tracking-tight font-heading">
              {value}
            </span>
            {delta && (
              <span
                className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                  deltaType === 'positive'
                    ? 'bg-rr-softPink text-rr-deepPink'
                    : deltaType === 'negative'
                    ? 'bg-gray-100 text-rr-charcoal'
                    : 'bg-blue-50 text-rr-blue'
                }`}
              >
                {delta}
              </span>
            )}
          </div>
          {subtitle && <p className="mt-1.5 text-xs text-rr-muted leading-relaxed">{subtitle}</p>}
        </div>
        {icon && (
          <div className="p-2.5 rounded-lg bg-rr-palePink text-rr-pink border border-pink-100/80">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
};

