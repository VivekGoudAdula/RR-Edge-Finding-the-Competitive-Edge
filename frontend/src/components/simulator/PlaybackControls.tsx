import React from 'react';
import { Play, Pause, SkipBack, SkipForward, RotateCcw, FastForward } from 'lucide-react';
import { DeliveryRecord } from '../../services/simulatorApi';

interface PlaybackControlsProps {
  isPlaying: boolean;
  onPlayToggle: () => void;
  onStepPrev: () => void;
  onStepNext: () => void;
  onReplayBall: () => void;
  speed: number;
  onSpeedChange: (speed: number) => void;
  currentIndex: number;
  totalDeliveries: number;
  onSelectDeliveryIndex: (index: number) => void;
  deliveries?: DeliveryRecord[];
}

export const PlaybackControls: React.FC<PlaybackControlsProps> = ({
  isPlaying,
  onPlayToggle,
  onStepPrev,
  onStepNext,
  onReplayBall,
  speed,
  onSpeedChange,
  currentIndex,
  totalDeliveries,
  onSelectDeliveryIndex,
  deliveries = [],
}) => {
  return (
    <div className="bg-white rounded-xl shadow-card border border-rr-navy/10 p-4 space-y-3">
      {/* Sequence Scrubber Dots */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-thin">
        {deliveries.length > 0 ? (
          deliveries.map((d, idx) => {
            const isSelected = idx === currentIndex;
            const runs = d.runs;
            const isWkt = d.is_wicket;

            let badgeBg = 'bg-slate-100 text-slate-700 hover:bg-slate-200';
            if (isWkt) {
              badgeBg = isSelected
                ? 'bg-red-600 text-white ring-2 ring-red-400 font-bold'
                : 'bg-red-100 text-red-700';
            } else if (runs === 4 || runs === 6) {
              badgeBg = isSelected
                ? 'bg-amber-500 text-white ring-2 ring-amber-300 font-bold'
                : 'bg-amber-100 text-amber-800';
            } else if (runs > 0) {
              badgeBg = isSelected
                ? 'bg-blue-600 text-white ring-2 ring-blue-400 font-bold'
                : 'bg-blue-50 text-blue-700';
            } else {
              badgeBg = isSelected
                ? 'bg-[#0B192C] text-white ring-2 ring-slate-400 font-bold'
                : 'bg-slate-100 text-slate-600';
            }

            return (
              <button
                type="button"
                key={idx}
                onClick={() => onSelectDeliveryIndex(idx)}
                className={`flex-shrink-0 px-2 py-1 rounded text-[11px] font-mono transition-all ${badgeBg}`}
                title={`Ball ${d.over_ball} - ${isWkt ? 'Wicket' : `${runs} runs`}`}
              >
                <span>{d.over_ball}</span>
                <span className="ml-1 opacity-80">{isWkt ? 'W' : runs}</span>
              </button>
            );
          })
        ) : (
          <div className="text-xs text-rr-muted py-1">No deliveries loaded</div>
        )}
      </div>

      {/* Main Transport Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-slate-100">
        <div className="flex items-center space-x-2">
          {/* Step Back */}
          <button
            type="button"
            onClick={onStepPrev}
            disabled={currentIndex <= 0}
            className="p-2 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-40 transition"
            title="Previous Delivery"
          >
            <SkipBack className="w-4 h-4" />
          </button>

          {/* Play / Pause Primary Button */}
          <button
            type="button"
            onClick={onPlayToggle}
            style={{ backgroundColor: '#0B192C', color: '#FFFFFF' }}
            className="px-4 py-2 rounded-lg bg-rr-navy text-white text-xs font-bold flex items-center gap-1.5 shadow-sm hover:opacity-95 transition"
          >
            {isPlaying ? (
              <>
                <Pause className="w-4 h-4 fill-white" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Play Replay</span>
              </>
            )}
          </button>

          {/* Step Next */}
          <button
            type="button"
            onClick={onStepNext}
            disabled={currentIndex >= totalDeliveries - 1}
            className="p-2 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-40 transition"
            title="Next Delivery"
          >
            <SkipForward className="w-4 h-4" />
          </button>

          {/* Replay Current Ball */}
          <button
            type="button"
            onClick={onReplayBall}
            className="p-2 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 transition"
            title="Replay Current Delivery"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>

        {/* Counter and Speed Selector */}
        <div className="flex items-center space-x-3">
          <div className="text-xs text-slate-600 font-mono">
            Ball <span className="font-bold text-rr-navy">{currentIndex + 1}</span> of{' '}
            <span className="font-bold text-rr-navy">{Math.max(1, totalDeliveries)}</span>
          </div>

          <div className="flex items-center bg-slate-100 rounded-lg p-0.5 border border-slate-200">
            {[0.5, 1.0, 2.0].map((s) => (
              <button
                type="button"
                key={s}
                onClick={() => onSpeedChange(s)}
                className={`px-2 py-1 text-[11px] font-bold rounded transition ${
                  speed === s
                    ? 'bg-white text-rr-pink shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

