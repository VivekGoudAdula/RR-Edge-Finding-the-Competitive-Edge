import React, { useState, useEffect, useRef } from 'react';
import {
  Gamepad2,
  History,
  Sliders,
  Play,
  RotateCcw,
  Shield,
  Swords,
  Sparkles,
  Info,
  CheckCircle2,
  AlertCircle,
  Layers,
  Search,
} from 'lucide-react';
import {
  SimulatorPlayer,
  PresetScenario,
  HistoricalSequenceMeta,
  HistoricalSequenceData,
  DeliveryRecord,
  FielderPosition,
  FieldingPresets,
  HeadToHeadAnalytics,
  fetchSimulatorPlayers,
  fetchSimulatorScenarios,
  fetchSimulatorHistoricalSequences,
  fetchSimulatorSequenceDeliveries,
  simulateWhatIfDelivery,
  fetchSimulatorHeadToHead,
  fetchSimulatorFieldingPresets,
} from '../services/simulatorApi';
import canonicalSimulatorPlayers from '../data/canonicalSimulatorPlayers.json';
import canonicalSimulatorScenarios from '../data/canonicalSimulatorScenarios.json';
import canonicalSimulatorPresets from '../data/canonicalSimulatorPresets.json';
import canonicalSimulatorSequences from '../data/canonicalSimulatorSequences.json';
import { CricketGroundSVG } from '../components/simulator/CricketGroundSVG';
import { PlaybackControls } from '../components/simulator/PlaybackControls';
import { AnalyticsPanel } from '../components/simulator/AnalyticsPanel';
import { PageHeroCard } from '../components/common/PageHeroCard';

export const CricketSimulator: React.FC = () => {
  // Modes: 'replay' or 'whatif'
  const [mode, setMode] = useState<'replay' | 'whatif'>('replay');

  // Shared Data
  const [players, setPlayers] = useState<SimulatorPlayer[]>(canonicalSimulatorPlayers as unknown as SimulatorPlayer[]);
  const [presetScenarios, setPresetScenarios] = useState<PresetScenario[]>(canonicalSimulatorScenarios as unknown as PresetScenario[]);
  const [fieldingPresets, setFieldingPresets] = useState<FieldingPresets | null>(canonicalSimulatorPresets as unknown as FieldingPresets);
  const [activeFielders, setActiveFielders] = useState<FielderPosition[]>(
    ((canonicalSimulatorPresets as any)?.death_protection || []) as FielderPosition[]
  );
  const [selectedFieldingPreset, setSelectedFieldingPreset] = useState<string>('death_protection');

  // Historical Replay State
  const [sequences, setSequences] = useState<HistoricalSequenceMeta[]>(canonicalSimulatorSequences as unknown as HistoricalSequenceMeta[]);
  const [selectedSequenceId, setSelectedSequenceId] = useState<string>(
    (canonicalSimulatorSequences as any[])?.[0]?.sequence_id || 'seq_13512_inn2'
  );
  const [sequenceData, setSequenceData] = useState<HistoricalSequenceData | null>(null);
  const [currentDeliveryIndex, setCurrentDeliveryIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playSpeed, setPlaySpeed] = useState<number>(1.0);
  const [playbackProgress, setPlaybackProgress] = useState<number>(1.0);

  // What-if Simulation State
  const [formatFilter, setFormatFilter] = useState<string>('IPL');
  const [selectedBatterId, setSelectedBatterId] = useState<number>(6396); // Tim David
  const [selectedNonStrikerId, setSelectedNonStrikerId] = useState<number>(1699); // Suryakumar Yadav
  const [selectedBowlerId, setSelectedBowlerId] = useState<number>(2933); // Jasprit Bumrah
  const [simInnings, setSimInnings] = useState<number>(2);
  const [simBallsRemaining, setSimBallsRemaining] = useState<number>(6);
  const [simRunsToDefend, setSimRunsToDefend] = useState<number>(18);
  const [simWicketsRemaining, setSimWicketsRemaining] = useState<number>(4);
  const [simCurrentScore, setSimCurrentScore] = useState<number>(170);
  const [simPreviousContext, setSimPreviousContext] = useState<string>('dot');
  const [simHistory, setSimHistory] = useState<any[]>([]);
  const [activeSimDelivery, setActiveSimDelivery] = useState<any | null>(null);
  const [simLoading, setSimLoading] = useState<boolean>(false);
  const [lastSimResult, setLastSimResult] = useState<any | null>(null);

  // Analytics & ML Baseline State
  const [analytics, setAnalytics] = useState<HeadToHeadAnalytics | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState<boolean>(false);

  // Animation Frame Reference
  const animFrameRef = useRef<number | null>(null);

  // Load initial simulator catalogs
  useEffect(() => {
    async function initSimulator() {
      try {
        const [pList, sList, fPresets, seqList] = await Promise.all([
          fetchSimulatorPlayers({ limit: 100 }),
          fetchSimulatorScenarios(),
          fetchSimulatorFieldingPresets(),
          fetchSimulatorHistoricalSequences({ limit: 25 }),
        ]);

        setPlayers(pList);
        setPresetScenarios(sList);
        setFieldingPresets(fPresets);
        if (fPresets?.death_protection) {
          setActiveFielders(fPresets.death_protection);
        }

        setSequences(seqList);
        if (seqList.length > 0) {
          setSelectedSequenceId(seqList[0].sequence_id);
        }
      } catch (e) {
        console.error('Failed to initialize simulator catalogs:', e);
      }
    }
    initSimulator();
  }, []);

  // Fetch sequence deliveries when selected sequence changes
  useEffect(() => {
    if (mode !== 'replay' || !selectedSequenceId || sequences.length === 0) return;
    const seqMeta = sequences.find((s) => s.sequence_id === selectedSequenceId);
    if (!seqMeta) return;
    const targetMeta = seqMeta;

    async function loadSeq() {
      try {
        setIsPlaying(false);
        const data = await fetchSimulatorSequenceDeliveries(targetMeta.match_id, {
          innings: targetMeta.innings,
          over_start: targetMeta.over_start,
          over_end: targetMeta.over_end,
        });
        setSequenceData(data);
        setCurrentDeliveryIndex(0);
        setPlaybackProgress(1.0);
      } catch (err) {
        console.error('Failed to load sequence deliveries:', err);
      }
    }
    loadSeq();
  }, [mode, selectedSequenceId, sequences]);

  // Fetch dual player analytics when players or format change
  useEffect(() => {
    async function loadAnalytics() {
      const bId = mode === 'replay' ? activeDeliveryRecord?.striker?.id : selectedBatterId;
      const bwId = mode === 'replay' ? activeDeliveryRecord?.bowler?.id : selectedBowlerId;
      if (!bId || !bwId) return;

      setAnalyticsLoading(true);
      try {
        const res = await fetchSimulatorHeadToHead(bId, bwId, formatFilter);
        setAnalytics(res);
      } catch (err) {
        console.error('Failed to fetch head-to-head analytics:', err);
      } finally {
        setAnalyticsLoading(false);
      }
    }
    loadAnalytics();
  }, [mode, selectedBatterId, selectedBowlerId, formatFilter, currentDeliveryIndex]);

  // Handle Fielding Preset Change
  const handlePresetSelect = (presetKey: string) => {
    setSelectedFieldingPreset(presetKey);
    if (fieldingPresets && (fieldingPresets as any)[presetKey]) {
      setActiveFielders((fieldingPresets as any)[presetKey]);
    }
  };

  // Replay Animation Loop
  useEffect(() => {
    if (!isPlaying) {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      return;
    }

    let startTime = performance.now();
    const duration = 2400 / playSpeed;

    const animate = (time: number) => {
      const elapsed = time - startTime;
      const progress = Math.min(1.0, elapsed / duration);
      setPlaybackProgress(progress);

      if (progress < 1.0) {
        animFrameRef.current = requestAnimationFrame(animate);
      } else {
        // Step to next delivery or pause
        if (sequenceData && currentDeliveryIndex < sequenceData.deliveries.length - 1) {
          setTimeout(() => {
            setCurrentDeliveryIndex((prev) => prev + 1);
            startTime = performance.now();
            animFrameRef.current = requestAnimationFrame(animate);
          }, 600 / playSpeed);
        } else {
          setIsPlaying(false);
        }
      }
    };

    animFrameRef.current = requestAnimationFrame(animate);
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isPlaying, currentDeliveryIndex, playSpeed, sequenceData]);

  // Active delivery record in replay mode
  const activeDeliveryRecord: DeliveryRecord | null =
    sequenceData && sequenceData.deliveries.length > 0
      ? sequenceData.deliveries[currentDeliveryIndex]
      : null;

  // Active delivery data formatted for SVG
  const activeVisualDelivery =
    mode === 'replay'
      ? activeDeliveryRecord
        ? {
            pitch_landing: activeDeliveryRecord.pitch_landing,
            shot_trajectory: activeDeliveryRecord.shot_trajectory,
            runs: activeDeliveryRecord.runs,
            is_wicket: activeDeliveryRecord.is_wicket,
            dismissal_type: activeDeliveryRecord.dismissal_type,
            stroke: activeDeliveryRecord.stroke,
            delivery_style: activeDeliveryRecord.delivery_style,
            speed_kph: activeDeliveryRecord.speed_kph,
            striker_name: activeDeliveryRecord.striker?.name,
            bowler_name: activeDeliveryRecord.bowler?.name,
            is_simulation: false,
          }
        : null
      : activeSimDelivery;

  // Execute What-if single delivery simulation
  const handleSimulateNextDelivery = async () => {
    if (simLoading) return;
    setSimLoading(true);

    try {
      const payload = {
        format: formatFilter,
        innings: simInnings,
        batter_id: selectedBatterId,
        bowler_id: selectedBowlerId,
        balls_remaining: simBallsRemaining,
        runs_to_defend: simRunsToDefend,
        wickets_remaining: simWicketsRemaining,
        current_score: simCurrentScore,
        target_runs: simCurrentScore + simRunsToDefend,
        previous_context: simPreviousContext,
        fielding_preset: selectedFieldingPreset,
        fielders: activeFielders,
      };

      const res = await simulateWhatIfDelivery(payload);
      setLastSimResult(res);

      const dRes = res.delivery_result;
      const uState = res.updated_state;

      const batName = players.find((p) => p.player_id === selectedBatterId)?.player_name || 'Batter';
      const bowlName = players.find((p) => p.player_id === selectedBowlerId)?.player_name || 'Bowler';

      const simDelivVisual = {
        pitch_landing: dRes.pitch_landing,
        shot_trajectory: dRes.shot_trajectory,
        runs: dRes.runs,
        is_wicket: dRes.is_wicket,
        dismissal_type: dRes.dismissal_type,
        stroke: dRes.stroke,
        delivery_style: dRes.delivery_style,
        speed_kph: dRes.speed_kph,
        striker_name: batName,
        bowler_name: bowlName,
        is_simulation: true,
      };

      setActiveSimDelivery(simDelivVisual);
      setPlaybackProgress(0.0);

      // Animate the simulated ball
      let startTime = performance.now();
      const duration = 2000;
      const animateSim = (t: number) => {
        const p = Math.min(1.0, (t - startTime) / duration);
        setPlaybackProgress(p);
        if (p < 1.0) {
          requestAnimationFrame(animateSim);
        }
      };
      requestAnimationFrame(animateSim);

      // Update state for next delivery
      setSimCurrentScore(uState.current_score);
      setSimWicketsRemaining(uState.wickets_remaining);
      setSimBallsRemaining(uState.balls_remaining);
      setSimRunsToDefend(uState.runs_needed);
      setSimPreviousContext(dRes.is_wicket ? 'wicket' : dRes.runs === 0 ? 'dot' : dRes.runs >= 4 ? 'boundary' : 'single');

      // Handle Strike Rotation or Wicket Replacement
      if (dRes.is_wicket) {
        // Find next eligible batter not currently at crease
        const nextBatter = players.find(
          (p) =>
            (p.discipline === 'BATTER' || p.discipline === 'ALL_ROUNDER') &&
            p.player_id !== selectedBatterId &&
            p.player_id !== selectedNonStrikerId
        );
        if (nextBatter) {
          setSelectedBatterId(nextBatter.player_id);
        }
      } else if (uState.strike_rotated) {
        // Odd runs scored or over completed: swap striker and non-striker
        const temp = selectedBatterId;
        setSelectedBatterId(selectedNonStrikerId);
        setSelectedNonStrikerId(temp);
      }

      // Append to history
      setSimHistory((prev) => [
        ...prev,
        {
          ball_num: prev.length + 1,
          runs: dRes.runs,
          is_wicket: dRes.is_wicket,
          stroke: dRes.stroke,
          score: `${uState.current_score}/${10 - uState.wickets_remaining}`,
          runs_needed: uState.runs_needed,
          balls_left: uState.balls_remaining,
          strike_rotated: Boolean(uState.strike_rotated),
        },
      ]);
    } catch (err: any) {
      alert('Failed to simulate delivery: ' + err.message);
    } finally {
      setSimLoading(false);
    }
  };

  const selectedBatterObj = players.find((p) => p.player_id === selectedBatterId);
  const selectedNonStrikerObj = players.find((p) => p.player_id === selectedNonStrikerId);
  const selectedBowlerObj = players.find((p) => p.player_id === selectedBowlerId);

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Standardized Compact Hero Section */}
      <PageHeroCard
        badge="Interactive 2D Simulation"
        badgeIcon={<Gamepad2 className="w-3.5 h-3.5 text-rr-pink" />}
        badgeContext="Historical Replay • What-if Tactical Crucible"
        title="Cricket Simulator"
        description="Replay real historical IPL & T20I sequences delivery-by-delivery, or configure hypothetical crucibles with custom field placements and empirical delivery-outcome simulations."
        actions={
          <div className="flex items-center bg-white/10 p-1 rounded-xl border border-white/20">
            <button
              type="button"
              onClick={() => {
                setMode('replay');
                setIsPlaying(false);
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                mode === 'replay' ? 'bg-rr-navy text-white shadow-sm' : 'text-white/70 hover:text-white'
              }`}
            >
              <History className="w-3.5 h-3.5 text-rr-gold" />
              <span>Historical Replay</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setMode('whatif');
                setIsPlaying(false);
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                mode === 'whatif' ? 'bg-rr-pink text-white shadow-sm' : 'text-white/70 hover:text-white'
              }`}
            >
              <Gamepad2 className="w-3.5 h-3.5 text-white" />
              <span>What-if Sim</span>
            </button>
          </div>
        }
      />

      {/* Tactical Disclosure Note */}
      <div className="p-3 bg-white border border-slate-200 rounded-xl flex items-center justify-between text-xs text-slate-600 shadow-sm">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-rr-pink flex-shrink-0" />
          <span>
            {mode === 'replay'
              ? 'Historical replay uses actual recorded ball-by-ball telemetry (speed, stroke, style, outcome). Pitch landing and trajectory vectors are illustrative visual paths between recorded coordinates.'
              : 'What-if mode delivers illustrative delivery simulations based on player-specific empirical match states and contextual ML baselines.'}
          </span>
        </div>
        <span className="font-mono text-[10px] text-slate-400 uppercase hidden sm:inline">Audit Verified</span>
      </div>

      {/* Main Simulator Workspace (Grid: Ground & Controls on Left, Configuration & Analytics on Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: 2D Pitch SVG & Playback Transport */}
        <div className="lg:col-span-7 space-y-4">
          {/* Ground Viewport */}
          <CricketGroundSVG
            fielders={activeFielders}
            onFielderChange={setActiveFielders}
            activeDelivery={activeVisualDelivery}
            isPlaying={isPlaying}
            playbackProgress={playbackProgress}
            strikerName={
              mode === 'replay'
                ? activeDeliveryRecord?.striker?.name || 'Striker'
                : selectedBatterObj?.player_name || 'Striker'
            }
            bowlerName={
              mode === 'replay'
                ? activeDeliveryRecord?.bowler?.name || 'Bowler'
                : selectedBowlerObj?.player_name || 'Bowler'
            }
            nonStrikerName={
              mode === 'replay'
                ? activeDeliveryRecord?.non_striker?.name || 'Non-Striker'
                : selectedNonStrikerObj?.player_name || 'Non-Striker'
            }
            isEditable={mode === 'whatif'}
          />

          {/* Transport Controls (Replay Mode) */}
          {mode === 'replay' && sequenceData && (
            <PlaybackControls
              isPlaying={isPlaying}
              onPlayToggle={() => setIsPlaying(!isPlaying)}
              onStepPrev={() => {
                setIsPlaying(false);
                setCurrentDeliveryIndex((prev) => Math.max(0, prev - 1));
                setPlaybackProgress(1.0);
              }}
              onStepNext={() => {
                setIsPlaying(false);
                setCurrentDeliveryIndex((prev) =>
                  Math.min(sequenceData.deliveries.length - 1, prev + 1)
                );
                setPlaybackProgress(1.0);
              }}
              onReplayBall={() => {
                setIsPlaying(false);
                setPlaybackProgress(0.0);
                setTimeout(() => setPlaybackProgress(1.0), 300);
              }}
              speed={playSpeed}
              onSpeedChange={setPlaySpeed}
              currentIndex={currentDeliveryIndex}
              totalDeliveries={sequenceData.deliveries.length}
              onSelectDeliveryIndex={(idx) => {
                setIsPlaying(false);
                setCurrentDeliveryIndex(idx);
                setPlaybackProgress(1.0);
              }}
              deliveries={sequenceData.deliveries}
            />
          )}

          {/* What-if Action Button & Current State Strip */}
          {mode === 'whatif' && (
            <div className="bg-white rounded-xl shadow-card border border-rr-navy/10 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-bold text-slate-500 uppercase">Match State</span>
                  <div className="text-lg font-black text-rr-navy">
                    {simCurrentScore}/{10 - simWicketsRemaining} &bull; Need{' '}
                    <span className="text-rr-pink">{simRunsToDefend}</span> off{' '}
                    <span className="text-rr-pink">{simBallsRemaining}</span> balls
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleSimulateNextDelivery}
                  disabled={simLoading || simBallsRemaining <= 0 || simRunsToDefend <= 0 || simWicketsRemaining <= 0}
                  style={{ backgroundColor: '#E6007E', color: '#FFFFFF' }}
                  className="px-5 py-2.5 rounded-lg bg-rr-pink text-white text-xs font-black shadow-sm hover:opacity-95 transition disabled:opacity-40 flex items-center gap-2"
                >
                  <Sparkles className="w-4 h-4 text-white" />
                  <span>{simLoading ? 'Simulating...' : 'Simulate Next Delivery'}</span>
                </button>
              </div>

              {/* Simulation Sequence Log */}
              {simHistory.length > 0 && (
                <div className="pt-2 border-t border-slate-100 flex items-center gap-1.5 overflow-x-auto pb-1">
                  {simHistory.map((h, i) => (
                    <span
                      key={i}
                      className={`px-2 py-0.5 rounded text-[11px] font-mono ${
                        h.is_wicket
                          ? 'bg-red-100 text-red-700 font-bold'
                          : h.runs >= 4
                          ? 'bg-amber-100 text-amber-800 font-bold'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      B{h.ball_num}: {h.is_wicket ? 'W' : `${h.runs}r`}
                    </span>
                  ))}
                  <button
                    type="button"
                    onClick={() => {
                      setSimHistory([]);
                      setSimCurrentScore(170);
                      setSimRunsToDefend(18);
                      setSimBallsRemaining(6);
                      setSimWicketsRemaining(4);
                      setActiveSimDelivery(null);
                    }}
                    className="text-[11px] text-slate-400 hover:text-slate-600 underline ml-2"
                  >
                    Reset Over
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Configuration & Dual Analytics */}
        <div className="lg:col-span-5 space-y-4">
          {/* Historical Sequence Selector (Replay Mode) */}
          {mode === 'replay' && (
            <div className="bg-white rounded-xl shadow-card border border-rr-navy/10 p-4 space-y-3">
              <label className="text-xs font-bold uppercase tracking-wider text-rr-navy block">
                Select Historical Death Sequence
              </label>
              <select
                value={selectedSequenceId}
                onChange={(e) => setSelectedSequenceId(e.target.value)}
                className="w-full p-2.5 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-800 font-medium focus:outline-none focus:border-rr-pink"
              >
                {sequences.map((s) => (
                  <option key={s.sequence_id} value={s.sequence_id}>
                    [{s.format}] {s.comp_name} &bull; {s.situation_title} ({s.key_bowler_name} to {s.key_striker_name})
                  </option>
                ))}
              </select>

              {/* Sequence Details Badge */}
              {sequenceData && (
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1">
                  <div className="font-bold text-rr-navy">{sequenceData.comp_name}</div>
                  <div className="text-slate-500 text-[11px]">
                    Match Date: {sequenceData.match_date} &bull; Innings {sequenceData.innings} &bull; Final Result: {sequenceData.final_runs}/{sequenceData.final_wickets}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* What-if Match Setup Panel */}
          {mode === 'whatif' && (
            <div className="bg-white rounded-xl shadow-card border border-rr-navy/10 p-4 space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <h3 className="text-xs font-bold uppercase tracking-wider text-rr-navy">
                  What-if Crucible Setup
                </h3>
                <span className="text-[10px] text-rr-pink font-semibold">Custom Situational State</span>
              </div>

              {/* Format Filter */}
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-600">Format:</span>
                {['IPL', 'T20I', 'ALL'].map((f) => (
                  <button
                    type="button"
                    key={f}
                    onClick={() => setFormatFilter(f)}
                    style={
                      formatFilter === f
                        ? { backgroundColor: '#0B192C', color: '#FFFFFF' }
                        : { backgroundColor: '#FFFFFF', color: '#64748B' }
                    }
                    className={`px-3 py-1 text-xs font-bold rounded-lg border border-slate-200 transition ${
                      formatFilter === f ? 'bg-rr-navy text-white shadow-xs' : 'hover:bg-slate-50'
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>

              {/* Player Selection Dropdowns */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {/* Striker Dropdown */}
                <div>
                  <label className="text-[11px] font-bold text-slate-700 block mb-1">
                    Striker
                  </label>
                  <select
                    value={selectedBatterId}
                    onChange={(e) => setSelectedBatterId(Number(e.target.value))}
                    className="w-full p-2 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-800 font-semibold truncate"
                  >
                    {players
                      .filter((p) => p.discipline === 'BATTER' || p.discipline === 'ALL_ROUNDER')
                      .map((p) => (
                        <option key={p.player_id} value={p.player_id}>
                          {p.player_name} {p.is_top_10 ? `★ Top 10` : ''}
                        </option>
                      ))}
                  </select>
                </div>

                {/* Non-Striker Dropdown */}
                <div>
                  <label className="text-[11px] font-bold text-slate-700 block mb-1">
                    Non-Striker
                  </label>
                  <select
                    value={selectedNonStrikerId}
                    onChange={(e) => setSelectedNonStrikerId(Number(e.target.value))}
                    className="w-full p-2 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-800 font-semibold truncate"
                  >
                    {players
                      .filter((p) => (p.discipline === 'BATTER' || p.discipline === 'ALL_ROUNDER') && p.player_id !== selectedBatterId)
                      .map((p) => (
                        <option key={p.player_id} value={p.player_id}>
                          {p.player_name} {p.is_top_10 ? `★ Top 10` : ''}
                        </option>
                      ))}
                  </select>
                </div>

                {/* Bowler Dropdown */}
                <div>
                  <label className="text-[11px] font-bold text-slate-700 block mb-1">
                    Bowler
                  </label>
                  <select
                    value={selectedBowlerId}
                    onChange={(e) => setSelectedBowlerId(Number(e.target.value))}
                    className="w-full p-2 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-800 font-semibold truncate"
                  >
                    {players
                      .filter((p) => p.discipline === 'BOWLER' || p.discipline === 'ALL_ROUNDER')
                      .map((p) => (
                        <option key={p.player_id} value={p.player_id}>
                          {p.player_name} {p.is_top_10 ? `★ Top 10` : ''}
                        </option>
                      ))}
                  </select>
                </div>
              </div>

              {/* Fielding Presets */}
              <div>
                <label className="text-[11px] font-bold text-slate-700 block mb-1">
                  Tactical Fielding Arrangement
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
                  {[
                    { id: 'death_protection', name: 'Death Guard' },
                    { id: 'defensive_spread', name: 'Boundary Spread' },
                    { id: 'powerplay', name: 'Powerplay Ring' },
                    { id: 'attacking', name: 'Attack & Slips' },
                  ].map((preset) => (
                    <button
                      type="button"
                      key={preset.id}
                      onClick={() => handlePresetSelect(preset.id)}
                      style={
                        selectedFieldingPreset === preset.id
                          ? { backgroundColor: '#0B192C', color: '#FFFFFF', borderColor: '#D4AF37' }
                          : { backgroundColor: '#FFFFFF', color: '#475569', borderColor: '#E2E8F0' }
                      }
                      className="px-2 py-1.5 rounded-lg text-[10px] font-bold border transition text-center truncate"
                    >
                      {preset.name}
                    </button>
                  ))}
                </div>
                <p className="text-[10px] text-slate-400 mt-1">
                  Tip: Fielders can be dragged freely across the ground to evaluate specific gaps.
                </p>
              </div>

              {/* Situation Presets */}
              <div>
                <label className="text-[11px] font-bold text-slate-700 block mb-1">
                  Crucible Situational Presets
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {presetScenarios.slice(0, 4).map((ps) => (
                    <button
                      type="button"
                      key={ps.id}
                      onClick={() => {
                        setSimBallsRemaining(ps.balls_remaining);
                        setSimRunsToDefend(ps.runs_to_defend);
                        setSimWicketsRemaining(ps.wickets_remaining);
                        handlePresetSelect(ps.fielding_preset);
                      }}
                      className="p-2 rounded-lg border border-slate-200 text-left hover:border-rr-pink/50 hover:bg-slate-50 transition text-xs"
                    >
                      <div className="font-bold text-rr-navy truncate">{ps.name}</div>
                      <div className="text-[10px] text-slate-500 uppercase mt-0.5">{ps.category}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Live Analytics & Head-to-Head Panel */}
          <AnalyticsPanel
            analytics={analytics}
            loading={analyticsLoading}
            mlBaseline={lastSimResult?.contextual_ml_baseline}
          />
        </div>
      </div>
    </div>
  );
};
