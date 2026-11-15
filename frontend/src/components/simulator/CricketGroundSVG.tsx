import React, { useState, useEffect, useRef } from 'react';
import { FielderPosition } from '../../services/simulatorApi';

interface DeliveryVisualData {
  pitch_landing: { x: number; y: number; length_label?: string; line_label?: string };
  shot_trajectory: {
    start_x: number;
    start_y: number;
    target_x: number;
    target_y: number;
    is_boundary: boolean;
    is_six: boolean;
    stroke_category?: string;
  };
  runs: number;
  is_wicket: boolean;
  dismissal_type?: string | null;
  stroke?: string;
  delivery_style?: string;
  speed_kph?: number;
  striker_name?: string;
  bowler_name?: string;
  is_simulation?: boolean;
}

interface CricketGroundSVGProps {
  fielders: FielderPosition[];
  onFielderChange?: (fielders: FielderPosition[]) => void;
  activeDelivery?: DeliveryVisualData | null;
  isPlaying?: boolean;
  playbackProgress?: number; // 0.0 to 1.0 within delivery animation
  strikerName?: string;
  bowlerName?: string;
  nonStrikerName?: string;
  isEditable?: boolean;
}

export const CricketGroundSVG: React.FC<CricketGroundSVGProps> = ({
  fielders,
  onFielderChange,
  activeDelivery,
  isPlaying = false,
  playbackProgress = 1.0,
  strikerName = 'Striker',
  bowlerName = 'Bowler',
  nonStrikerName = 'Non-Striker',
  isEditable = false,
}) => {
  const [selectedFielderId, setSelectedFielderId] = useState<number | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Ball interpolation coordinates
  // 0.0 to 0.4: Bowler release (300, 245) -> Pitch landing (px, py)
  // 0.4 to 0.5: Pitch landing -> Striker contact (300, 335)
  // 0.5 to 1.0: Striker contact -> Shot target (tx, ty)
  let ballX = 300;
  let ballY = 245;
  let ballVisible = false;
  let showPitchMark = false;
  let showShotVector = false;

  if (activeDelivery) {
    const p = Math.max(0, Math.min(1, playbackProgress));
    ballVisible = true;
    const px = activeDelivery.pitch_landing?.x ?? 300;
    const py = activeDelivery.pitch_landing?.y ?? 310;
    const tx = activeDelivery.shot_trajectory?.target_x ?? 300;
    const ty = activeDelivery.shot_trajectory?.target_y ?? 335;

    if (p <= 0.4) {
      const t = p / 0.4;
      ballX = 300 + (px - 300) * t;
      ballY = 245 + (py - 245) * t;
    } else if (p <= 0.5) {
      showPitchMark = true;
      const t = (p - 0.4) / 0.1;
      ballX = px + (300 - px) * t;
      ballY = py + (335 - py) * t;
    } else {
      showPitchMark = true;
      showShotVector = true;
      const t = (p - 0.5) / 0.5;
      ballX = 300 + (tx - 300) * t;
      ballY = 335 + (ty - 335) * t;
    }
  }

  // Handle Drag-and-Drop or Click-to-Move for fielders
  const handleFielderPointerDown = (e: React.PointerEvent, id: number) => {
    if (!isEditable) return;
    e.stopPropagation();
    setSelectedFielderId(id);
    (e.target as Element).setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isEditable || selectedFielderId === null || !svgRef.current || !onFielderChange) return;
    const rect = svgRef.current.getBoundingClientRect();
    const scaleX = 600 / rect.width;
    const scaleY = 600 / rect.height;
    let newX = Math.round((e.clientX - rect.left) * scaleX);
    let newY = Math.round((e.clientY - rect.top) * scaleY);

    // Constrain within boundary oval (radius 265 around 300, 300)
    const dx = newX - 300;
    const dy = newY - 300;
    const dist = Math.hypot(dx, dy);
    if (dist > 260) {
      newX = Math.round(300 + (dx / dist) * 260);
      newY = Math.round(300 + (dy / dist) * 260);
    }

    const updated = fielders.map((f) =>
      f.id === selectedFielderId ? { ...f, x: newX, y: newY } : f
    );
    onFielderChange(updated);
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    if (selectedFielderId !== null) {
      try {
        (e.target as Element).releasePointerCapture(e.pointerId);
      } catch {}
      setSelectedFielderId(null);
    }
  };

  return (
    <div className="relative w-full aspect-square max-w-[560px] mx-auto select-none rounded-2xl overflow-hidden shadow-card border border-slate-200 bg-[#17462C]">
      <svg
        ref={svgRef}
        viewBox="0 0 600 600"
        className="w-full h-full block"
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      >
        <defs>
          {/* Outfield Grass Gradient */}
          <radialGradient id="outfieldGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#1E5E3A" />
            <stop offset="70%" stopColor="#174A2E" />
            <stop offset="100%" stopColor="#113822" />
          </radialGradient>

          {/* Pitch Strip Gradient */}
          <linearGradient id="pitchGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#D9C7A1" />
            <stop offset="50%" stopColor="#E4D5B5" />
            <stop offset="100%" stopColor="#C9B68D" />
          </linearGradient>

          {/* Ball Glow Filter */}
          <filter id="ballGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#FF0055" />
          </filter>
        </defs>

        {/* 1. Outfield Oval */}
        <circle cx="300" cy="300" r="290" fill="url(#outfieldGrad)" />

        {/* Outfield Mowing Circles pattern */}
        <circle cx="300" cy="300" r="210" fill="none" stroke="#256E45" strokeWidth="16" opacity="0.4" />
        <circle cx="300" cy="300" r="160" fill="none" stroke="#256E45" strokeWidth="16" opacity="0.4" />

        {/* 2. Boundary Rope */}
        <circle
          cx="300"
          cy="300"
          r="265"
          fill="none"
          stroke="#FFFFFF"
          strokeWidth="3.5"
          strokeDasharray="14, 6"
          opacity="0.9"
        />

        {/* Boundary Markers */}
        {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => {
          const rad = (deg * Math.PI) / 180;
          const mx = 300 + Math.cos(rad) * 265;
          const my = 300 + Math.sin(rad) * 265;
          return <circle key={deg} cx={mx} cy={my} r="3" fill="#D4AF37" />;
        })}

        {/* 3. 30-Yard Infield Ring */}
        <circle
          cx="300"
          cy="300"
          r="135"
          fill="none"
          stroke="#FFFFFF"
          strokeWidth="1.8"
          strokeDasharray="6, 6"
          opacity="0.65"
        />
        <text
          x="300"
          y="155"
          textAnchor="middle"
          fill="#FFFFFF"
          fontSize="8"
          fontWeight="bold"
          letterSpacing="1"
          opacity="0.5"
        >
          30-YARD INNER RING
        </text>

        {/* 4. Central 22-Yard Pitch (Length: 120px, Width: 32px) */}
        <rect
          x="284"
          y="235"
          width="32"
          height="115"
          rx="2"
          fill="url(#pitchGrad)"
          stroke="#8C7355"
          strokeWidth="1"
        />

        {/* Bowling Crease & Stumps (Top End - Bowler) */}
        <line x1="280" y1="245" x2="320" y2="245" stroke="#FFFFFF" strokeWidth="1.5" opacity="0.85" />
        <circle cx="297" cy="245" r="1.5" fill="#4A3525" />
        <circle cx="300" cy="245" r="1.5" fill="#4A3525" />
        <circle cx="303" cy="245" r="1.5" fill="#4A3525" />

        {/* Batting Creases & Stumps (Bottom End - Striker) */}
        <line x1="275" y1="335" x2="325" y2="335" stroke="#FFFFFF" strokeWidth="1.8" opacity="0.9" />
        {/* Popping Crease Return Lines */}
        <line x1="280" y1="335" x2="280" y2="348" stroke="#FFFFFF" strokeWidth="1" opacity="0.7" />
        <line x1="320" y1="335" x2="320" y2="348" stroke="#FFFFFF" strokeWidth="1" opacity="0.7" />
        <circle cx="297" cy="346" r="1.5" fill="#4A3525" />
        <circle cx="300" cy="346" r="1.5" fill="#4A3525" />
        <circle cx="303" cy="346" r="1.5" fill="#4A3525" />

        {/* 5. Static Player Markers on Pitch */}
        {/* Bowler Release Position */}
        <g transform="translate(300, 230)">
          <circle cx="0" cy="0" r="7" fill="#0B192C" stroke="#D4AF37" strokeWidth="1.5" />
          <text x="0" y="2.5" textAnchor="middle" fill="#FFFFFF" fontSize="6.5" fontWeight="bold">
            B
          </text>
          <text x="0" y="-10" textAnchor="middle" fill="#FFFFFF" fontSize="7" fontWeight="bold">
            {bowlerName.split(' ').pop()}
          </text>
        </g>

        {/* Non-Striker */}
        <g transform="translate(268, 250)">
          <circle cx="0" cy="0" r="6" fill="#E6007E" stroke="#FFFFFF" strokeWidth="1" opacity="0.85" />
          <text x="0" y="2" textAnchor="middle" fill="#FFFFFF" fontSize="6" fontWeight="bold">
            NS
          </text>
          <text x="0" y="-8" textAnchor="middle" fill="#FFFFFF" fontSize="6.5" opacity="0.9">
            {nonStrikerName.split(' ').pop()}
          </text>
        </g>

        {/* Striker Batting Position */}
        <g transform="translate(300, 335)">
          <circle cx="0" cy="0" r="8" fill="#E6007E" stroke="#FFFFFF" strokeWidth="2" />
          <text x="0" y="3" textAnchor="middle" fill="#FFFFFF" fontSize="7.5" fontWeight="black">
            S
          </text>
          <text x="0" y="16" textAnchor="middle" fill="#FFFFFF" fontSize="7.5" fontWeight="bold">
            {strikerName.split(' ').pop()}
          </text>
        </g>

        {/* Wicketkeeper Behind Stumps */}
        <g transform="translate(300, 375)">
          <circle cx="0" cy="0" r="6.5" fill="#4776A8" stroke="#FFFFFF" strokeWidth="1.2" />
          <text x="0" y="2.5" textAnchor="middle" fill="#FFFFFF" fontSize="6" fontWeight="bold">
            WK
          </text>
          <text x="0" y="12" textAnchor="middle" fill="#E2E8F0" fontSize="6.5">
            Keeper
          </text>
        </g>

        {/* 6. Dynamic Fielders (9 Fielders) */}
        {fielders.map((f) => {
          const isSelected = selectedFielderId === f.id;
          const isBoundaryRider = f.role === 'boundary_rider';
          return (
            <g
              key={f.id}
              transform={`translate(${f.x}, ${f.y})`}
              className={isEditable ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer'}
              onPointerDown={(e) => handleFielderPointerDown(e, f.id)}
            >
              {isSelected && (
                <circle cx="0" cy="0" r="14" fill="none" stroke="#D4AF37" strokeWidth="2" strokeDasharray="3,3" />
              )}
              <circle
                cx="0"
                cy="0"
                r={isBoundaryRider ? 7 : 6}
                fill={isBoundaryRider ? '#D4AF37' : '#0B192C'}
                stroke="#FFFFFF"
                strokeWidth="1.5"
              />
              <text
                x="0"
                y="2.5"
                textAnchor="middle"
                fill={isBoundaryRider ? '#0B192C' : '#FFFFFF'}
                fontSize="6"
                fontWeight="black"
              >
                {f.id}
              </text>
              <text
                x="0"
                y="12"
                textAnchor="middle"
                fill="#FFFFFF"
                fontSize="6.5"
                fontWeight="semibold"
                className="pointer-events-none drop-shadow-sm"
              >
                {f.name}
              </text>
            </g>
          );
        })}

        {/* 7. Trajectory Vector Path */}
        {showShotVector && activeDelivery?.shot_trajectory && (
          <g>
            <line
              x1="300"
              y1="335"
              x2={activeDelivery.shot_trajectory.target_x}
              y2={activeDelivery.shot_trajectory.target_y}
              stroke={
                activeDelivery.is_wicket
                  ? '#EF4444'
                  : activeDelivery.shot_trajectory.is_boundary
                  ? '#D4AF37'
                  : '#FFFFFF'
              }
              strokeWidth={activeDelivery.shot_trajectory.is_boundary ? '2.5' : '1.8'}
              strokeDasharray={activeDelivery.shot_trajectory.is_six ? 'none' : '4, 4'}
              opacity="0.85"
            />
            {/* Target Landing Ring */}
            <circle
              cx={activeDelivery.shot_trajectory.target_x}
              cy={activeDelivery.shot_trajectory.target_y}
              r={activeDelivery.shot_trajectory.is_six ? 7 : 5}
              fill="none"
              stroke={activeDelivery.shot_trajectory.is_boundary ? '#D4AF37' : '#FFFFFF'}
              strokeWidth="2"
            />
          </g>
        )}

        {/* Pitch Landing Marker */}
        {showPitchMark && activeDelivery?.pitch_landing && (
          <g>
            <circle
              cx={activeDelivery.pitch_landing.x}
              cy={activeDelivery.pitch_landing.y}
              r="4.5"
              fill="#D4AF37"
              stroke="#0B192C"
              strokeWidth="1"
              opacity="0.9"
            />
            <circle
              cx={activeDelivery.pitch_landing.x}
              cy={activeDelivery.pitch_landing.y}
              r="8"
              fill="none"
              stroke="#D4AF37"
              strokeWidth="1.2"
              opacity="0.5"
            />
          </g>
        )}

        {/* 8. Animated Cricket Ball */}
        {ballVisible && (
          <g transform={`translate(${ballX}, ${ballY})`}>
            <circle cx="0" cy="0" r="4.5" fill="#E6007E" stroke="#FFFFFF" strokeWidth="1" />
            <circle cx="0" cy="0" r="1.8" fill="#FFFFFF" opacity="0.8" />
          </g>
        )}
      </svg>

      {/* Floating Tactical Overlay Pill */}
      {activeDelivery && (
        <div className="absolute top-3 left-3 right-3 flex items-center justify-between pointer-events-none">
          <div className="bg-slate-900/80 backdrop-blur-sm border border-white/20 text-white px-3 py-1.5 rounded-lg text-xs flex items-center gap-2">
            <span className="font-bold text-rr-pink">
              {activeDelivery.runs === 4
                ? 'FOUR!'
                : activeDelivery.runs === 6
                ? 'SIX!'
                : activeDelivery.is_wicket
                ? 'WICKET!'
                : `${activeDelivery.runs} RUNS`}
            </span>
            <span className="text-slate-400">•</span>
            <span className="text-slate-200">{activeDelivery.stroke || 'Shot'}</span>
            <span className="text-slate-400">•</span>
            <span className="text-rr-gold font-mono">{activeDelivery.speed_kph || 135} km/h</span>
          </div>

          {activeDelivery.is_simulation && (
            <div className="bg-rr-pink/90 backdrop-blur-sm text-white px-2.5 py-1 rounded text-[10px] font-extrabold uppercase tracking-wider shadow-sm">
              Illustrative Simulation
            </div>
          )}
        </div>
      )}
    </div>
  );
};

