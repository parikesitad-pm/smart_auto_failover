import { useState, useEffect, useRef, useCallback } from 'react';
import { StartupConfig, StartupPreset } from '../types/cockpit.types';

export interface StartupSequenceState {
  isActive: boolean;
  progress: number;
  statusText: string;
  isReady: boolean;
  actualInitMs: number | null;
  minDurationMs: number;
  remainingMs: number;
  isDeparting: boolean;
}

export function useStartupSequence(initialConfig?: Partial<StartupConfig>) {
  const [config, setConfig] = useState<StartupConfig>({
    splashMinDurationMs: 3000,
    preset: 'normal',
    simulatedEngineInitMs: 450,
    skipEnabled: false,
    ...initialConfig,
  });

  const [state, setState] = useState<StartupSequenceState>({
    isActive: true,
    progress: 0,
    statusText: 'INITIALIZING ENGINE...',
    isReady: false,
    actualInitMs: null,
    minDurationMs: config.splashMinDurationMs,
    remainingMs: config.splashMinDurationMs,
    isDeparting: false,
  });

  const timerRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(0);

  const skipStartup = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    setState((prev) => ({
      ...prev,
      isActive: false,
      isReady: true,
      progress: 100,
    }));
  }, []);

  const runStartup = useCallback(() => {
    if (config.skipEnabled) {
      setState((prev) => ({
        ...prev,
        isActive: false,
        isReady: true,
        progress: 100,
      }));
      return;
    }

    if (timerRef.current) clearTimeout(timerRef.current);
    if (rafRef.current) cancelAnimationFrame(rafRef.current);

    startTimeRef.current = performance.now();
    const startTime = startTimeRef.current;
    const initTargetMs = config.simulatedEngineInitMs;
    const minSplashMs = config.splashMinDurationMs;

    setState({
      isActive: true,
      progress: 0,
      statusText: 'INITIALIZING ENGINE...',
      isReady: false,
      actualInitMs: null,
      minDurationMs: minSplashMs,
      remainingMs: minSplashMs,
      isDeparting: false,
    });

    // Natural 1 -> 100% progress counter loop
    const updateLoop = () => {
      const elapsed = performance.now() - startTime;
      const remaining = Math.max(0, minSplashMs - elapsed);

      if (elapsed < initTargetMs) {
        const ratio = Math.min(1, elapsed / initTargetMs);
        const currentPct = Math.min(99, Math.max(1, Math.floor(ratio * 100)));

        let currentStatus = 'DISCOVERING ADAPTERS (ETH / WLAN)...';
        if (currentPct >= 80) currentStatus = 'ENGAGING WORKLOAD PROTECTION...';
        else if (currentPct >= 55)
          currentStatus = 'EVALUATING ROUTE METRICS & SCORES...';
        else if (currentPct >= 25)
          currentStatus = 'PROBING CARRIER & RFC 3550 JITTER...';

        setState((prev) => ({
          ...prev,
          progress: currentPct,
          statusText: currentStatus,
          remainingMs: Math.round(remaining),
        }));

        rafRef.current = requestAnimationFrame(updateLoop);
      }
    };
    rafRef.current = requestAnimationFrame(updateLoop);

    // Core Engine reaches 100% (Honest completion at actual initialization time)
    timerRef.current = window.setTimeout(() => {
      const coreReadyAt = performance.now();
      const actualDuration = Math.round(coreReadyAt - startTime);
      const remainingPresentationMs = Math.max(0, minSplashMs - actualDuration);

      setState((prev) => ({
        ...prev,
        isReady: true,
        progress: 100,
        statusText: 'NETWORK READY',
        actualInitMs: actualDuration,
        remainingMs: Math.round(remainingPresentationMs),
      }));

      // Tuyul Sport Car Departure initiates during remaining delay window
      const departureDelay = Math.min(400, remainingPresentationMs * 0.25);
      window.setTimeout(() => {
        setState((prev) => ({ ...prev, isDeparting: true }));
      }, departureDelay);

      // Transition to Cockpit at max(actualDuration, minSplashMs)
      window.setTimeout(() => {
        setState((prev) => ({ ...prev, isActive: false }));
      }, remainingPresentationMs);
    }, initTargetMs);
  }, [config]);

  // Keyboard shortcut: Hold Shift to skip
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Shift' && state.isActive) {
        skipStartup();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [state.isActive, skipStartup]);

  // Run on mount
  useEffect(() => {
    runStartup();
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [runStartup]);

  const setPreset = useCallback((preset: StartupPreset, durationMs: number) => {
    setConfig((prev) => ({
      ...prev,
      preset,
      splashMinDurationMs: durationMs,
    }));
  }, []);

  const setCustomDuration = useCallback((durationMs: number) => {
    setConfig((prev) => ({
      ...prev,
      preset: 'custom',
      splashMinDurationMs: durationMs,
    }));
  }, []);

  const setEngineSpeed = useCallback((speedMs: number) => {
    setConfig((prev) => ({ ...prev, simulatedEngineInitMs: speedMs }));
  }, []);

  const setSkipEnabled = useCallback((skip: boolean) => {
    setConfig((prev) => ({ ...prev, skipEnabled: skip }));
  }, []);

  return {
    state,
    config,
    skipStartup,
    runStartup,
    setPreset,
    setCustomDuration,
    setEngineSpeed,
    setSkipEnabled,
  };
}
