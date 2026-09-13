import { useState, useEffect, useRef, useCallback } from 'react';
import {
  StartupConfig,
  StartupPreset,
  SystemIdentity,
} from '../types/cockpit.types';
import { tauriIpc } from '../services/tauriIpc';

export interface DiscoveredInterfaceDetail {
  id: string;
  name: string;
  mediaType: string;
  adminState: string;
  linkState: string;
  ipAddress: string;
  netmask: string;
  gateway: string;
  ssid: string;
  linkSpeed: string;
  state: string;
}

export type StartupSequenceStep =
  | 'starting_core' // 0% - 10%
  | 'reading_system_info' // 10% - 20%
  | 'discovering_interfaces' // 20% - 40%
  | 'reading_ip_config' // 40% - 55%
  | 'validating_interface_state' // 55% - 70%
  | 'initializing_probes' // 70% - 85%
  | 'evaluating_network_health' // 85% - 95%
  | 'preparing_runtime_state' // 95% - 100%
  | 'app_ready'; // 100%

export interface StartupSequenceState {
  isActive: boolean;
  progress: number;
  statusText: string;
  currentStep: StartupSequenceStep;
  isReady: boolean;
  isFadingOut: boolean;
  isFailed: boolean;
  errorMessage: string | null;
  actualInitMs: number | null;
  minDurationMs: number;
  remainingMs: number;
  systemIdentity: SystemIdentity | null;
  discoveredInterfaces: DiscoveredInterfaceDetail[];
  activePath: string | null;
  defaultGateway: string | null;
  isCoreAvailable: boolean | null;
  isTauriRuntime: boolean;
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
    statusText: 'Starting Core',
    currentStep: 'starting_core',
    isReady: false,
    isFadingOut: false,
    isFailed: false,
    errorMessage: null,
    actualInitMs: null,
    minDurationMs: config.splashMinDurationMs,
    remainingMs: config.splashMinDurationMs,
    systemIdentity: null,
    discoveredInterfaces: [],
    activePath: null,
    defaultGateway: null,
    isCoreAvailable: null,
    isTauriRuntime: true,
  });

  const timerRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);
  const fadeTimerRef = useRef<number | null>(null);
  const exitTimerRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(0);
  const isCancelledRef = useRef<boolean>(false);

  const clearAllTimers = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    if (fadeTimerRef.current) clearTimeout(fadeTimerRef.current);
    if (exitTimerRef.current) clearTimeout(exitTimerRef.current);
  }, []);

  const skipStartup = useCallback(() => {
    clearAllTimers();
    setState((prev) => ({
      ...prev,
      isActive: false,
      isReady: true,
      isFadingOut: false,
      isFailed: false,
      progress: 100,
      currentStep: 'app_ready',
      statusText: 'APP READY',
    }));
  }, [clearAllTimers]);

  const runStartup = useCallback(async () => {
    clearAllTimers();
    isCancelledRef.current = false;

    if (config.skipEnabled) {
      setState((prev) => ({
        ...prev,
        isActive: false,
        isReady: true,
        isFadingOut: false,
        isFailed: false,
        progress: 100,
        currentStep: 'app_ready',
        statusText: 'APP READY',
      }));
      return;
    }

    const minSplashMs = config.splashMinDurationMs;
    startTimeRef.current = performance.now();
    const startTime = startTimeRef.current;

    setState((prev) => ({
      ...prev,
      isActive: true,
      progress: 0,
      statusText: 'Starting Core',
      currentStep: 'starting_core',
      isReady: false,
      isFadingOut: false,
      isFailed: false,
      errorMessage: null,
      actualInitMs: null,
      minDurationMs: minSplashMs,
      remainingMs: minSplashMs,
    }));

    // Real Core initialization starts immediately at maximum speed
    let coreReady = false;
    let coreFailed = false;

    // Check Core Handshake
    try {
      const handshake = await tauriIpc.checkCoreHandshake(2500);
      if (isCancelledRef.current) return;

      if (!handshake.isTauriRuntime) {
        // Standard Web Browser Mode (Preview / Vercel)
        setState((prev) => ({
          ...prev,
          isTauriRuntime: false,
          isCoreAvailable: false,
        }));
        coreReady = true; // Browser preview is self-contained
      } else if (!handshake.isCoreAvailable) {
        // Tauri Desktop Shell, but Rust Core failed to respond
        coreFailed = true;
        setState((prev) => ({
          ...prev,
          isActive: true,
          progress: 8,
          currentStep: 'starting_core',
          statusText: 'INITIALIZATION INCOMPLETE',
          isFailed: true,
          errorMessage:
            'Rust Core unresponsive. Verify native daemon or restart application.',
          isReady: false,
          isCoreAvailable: false,
          isTauriRuntime: true,
        }));
        return;
      } else {
        // Core is available and verified
        setState((prev) => ({
          ...prev,
          isCoreAvailable: true,
          isTauriRuntime: true,
        }));

        // Parallel hardware query 1: System Hardware Identity
        tauriIpc
          .getSystemIdentity()
          .then((sysId) => {
            if (sysId && !isCancelledRef.current) {
              setState((prev) => ({ ...prev, systemIdentity: sysId }));
            }
          })
          .catch(() => {});

        // Parallel hardware query 2: Network Topology & Interfaces
        try {
          const ifaces = await tauriIpc.getInterfaceState();
          if (!isCancelledRef.current && ifaces && ifaces.length > 0) {
            const details: DiscoveredInterfaceDetail[] = ifaces.map((i) => {
              const isDisabled =
                i.state === 'DISABLED' ||
                i.adminState === 'disabled' ||
                !i.enabled;
              return {
                id: i.id,
                name: i.name,
                mediaType: i.mediaType,
                adminState: isDisabled ? 'Disabled' : 'Enabled',
                linkState: isDisabled
                  ? 'Disabled'
                  : i.linkState ||
                    (i.carrier === 'Connected' ||
                    i.state === 'ONLINE' ||
                    i.state === 'READY'
                      ? 'Connected'
                      : 'Disconnected'),
                ipAddress: isDisabled ? 'N/A' : i.ipAddress || 'N/A',
                netmask: isDisabled ? 'N/A' : i.netmask || '255.255.255.0',
                gateway: isDisabled ? 'N/A' : i.gateway || 'N/A',
                ssid: isDisabled ? 'N/A' : i.ssid || 'N/A',
                linkSpeed: isDisabled
                  ? 'N/A'
                  : i.linkSpeed ||
                    (i.mediaType === 'ethernet' ? '1000 Mbps' : 'N/A'),
                state: i.state,
              };
            });

            const onlineIface = ifaces.find((i) => i.state === 'ONLINE');
            const primaryGateway =
              details.find((d) => d.gateway && d.gateway !== 'N/A')?.gateway ||
              '192.168.1.1';

            setState((prev) => ({
              ...prev,
              discoveredInterfaces: details,
              activePath:
                onlineIface?.name ||
                details.find((d) => d.linkState === 'Connected')?.name ||
                details[0]?.name ||
                null,
              defaultGateway: primaryGateway,
            }));
          }
        } catch {
          // If query fails, fall back gracefully
        }

        const coreReadyAt = performance.now();
        const actualDuration = Math.round(coreReadyAt - startTime);
        coreReady = true;
        setState((prev) => ({ ...prev, actualInitMs: actualDuration }));
      }
    } catch {
      coreFailed = true;
      setState((prev) => ({
        ...prev,
        isActive: true,
        progress: 8,
        currentStep: 'starting_core',
        statusText: 'INITIALIZATION INCOMPLETE',
        isFailed: true,
        errorMessage: 'Fatal bootstrap error during Core initialization.',
        isReady: false,
      }));
      return;
    }

    // Progressive visual progression loop
    const updateLoop = () => {
      if (isCancelledRef.current || coreFailed) return;

      const elapsed = performance.now() - startTime;
      const presentationRatio = Math.min(1, elapsed / minSplashMs);
      const remaining = Math.max(0, minSplashMs - elapsed);

      // Exact Stage Mapping:
      // 0% - 10%: Starting Core
      // 10% - 20%: Reading System Information
      // 20% - 40%: Discovering Network Interfaces
      // 40% - 55%: Reading IP Configuration
      // 55% - 70%: Validating Interface State
      // 70% - 85%: Initializing Network Probes
      // 85% - 95%: Evaluating Network Health
      // 95% - 100%: Preparing Runtime State
      // 100%: APP READY

      let currentStep: StartupSequenceStep = 'starting_core';
      let currentStatus = 'Starting Core';
      let currentPct = Math.min(99, Math.floor(presentationRatio * 100));

      if (currentPct >= 95) {
        currentStep = 'preparing_runtime_state';
        currentStatus = 'Preparing Runtime State';
      } else if (currentPct >= 85) {
        currentStep = 'evaluating_network_health';
        currentStatus = 'Evaluating Network Health';
      } else if (currentPct >= 70) {
        currentStep = 'initializing_probes';
        currentStatus = 'Initializing Network Probes';
      } else if (currentPct >= 55) {
        currentStep = 'validating_interface_state';
        currentStatus = 'Validating Interface State';
      } else if (currentPct >= 40) {
        currentStep = 'reading_ip_config';
        currentStatus = 'Reading IP Configuration';
      } else if (currentPct >= 20) {
        currentStep = 'discovering_interfaces';
        currentStatus = 'Discovering Network Interfaces';
      } else if (currentPct >= 10) {
        currentStep = 'reading_system_info';
        currentStatus = 'Reading System Information';
      } else {
        currentStep = 'starting_core';
        currentStatus = 'Starting Core';
      }

      // Check if both presentation time and real core readiness are satisfied
      if (elapsed >= minSplashMs) {
        if (!coreReady) {
          // Hold at 95% preparing runtime state until native core is genuinely ready
          setState((prev) => ({
            ...prev,
            progress: 95,
            currentStep: 'preparing_runtime_state',
            statusText: 'Preparing Runtime State',
            remainingMs: 0,
          }));
          rafRef.current = requestAnimationFrame(updateLoop);
          return;
        }

        // Both requirements met: Reach 100% APP READY
        setState((prev) => ({
          ...prev,
          progress: 100,
          currentStep: 'app_ready',
          statusText: 'APP READY',
          isReady: true,
          remainingMs: 0,
        }));

        // Restrained completion transition: hold at 100% for 450ms then calm fade-out
        fadeTimerRef.current = window.setTimeout(() => {
          if (isCancelledRef.current) return;
          setState((prev) => ({ ...prev, isFadingOut: true }));

          exitTimerRef.current = window.setTimeout(() => {
            if (isCancelledRef.current) return;
            setState((prev) => ({ ...prev, isActive: false }));
          }, 350);
        }, 450);

        return;
      }

      setState((prev) => ({
        ...prev,
        progress: currentPct,
        currentStep,
        statusText: currentStatus,
        remainingMs: Math.round(remaining),
      }));

      rafRef.current = requestAnimationFrame(updateLoop);
    };

    rafRef.current = requestAnimationFrame(updateLoop);
  }, [config, clearAllTimers]);

  // Keyboard shortcut: Hold Shift to skip startup presentation
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
      isCancelledRef.current = true;
      clearAllTimers();
    };
  }, [runStartup, clearAllTimers]);

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
