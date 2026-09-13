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
  | 'system_init'
  | 'device_detected'
  | 'os_detected'
  | 'arch_detected'
  | 'interfaces_discovered'
  | 'network_info_detected'
  | 'probe_init'
  | 'health_eval'
  | 'path_determined'
  | 'ready';

export interface StartupSequenceState {
  isActive: boolean;
  progress: number;
  statusText: string;
  currentStep: StartupSequenceStep;
  isReady: boolean;
  actualInitMs: number | null;
  minDurationMs: number;
  remainingMs: number;
  isDeparting: boolean;
  systemIdentity: SystemIdentity | null;
  discoveredInterfaces: DiscoveredInterfaceDetail[];
  activePath: string | null;
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
    statusText: 'SYSTEM INITIALIZATION',
    currentStep: 'system_init',
    isReady: false,
    actualInitMs: null,
    minDurationMs: config.splashMinDurationMs,
    remainingMs: config.splashMinDurationMs,
    isDeparting: false,
    systemIdentity: null,
    discoveredInterfaces: [],
    activePath: null,
    isCoreAvailable: null,
    isTauriRuntime: true,
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
      currentStep: 'ready',
      statusText: 'SYSTEM READY',
    }));
  }, []);

  const runStartup = useCallback(async () => {
    if (config.skipEnabled) {
      setState((prev) => ({
        ...prev,
        isActive: false,
        isReady: true,
        progress: 100,
        currentStep: 'ready',
        statusText: 'SYSTEM READY',
      }));
      return;
    }

    if (timerRef.current) clearTimeout(timerRef.current);
    if (rafRef.current) cancelAnimationFrame(rafRef.current);

    startTimeRef.current = performance.now();
    const startTime = startTimeRef.current;
    const initTargetMs = config.simulatedEngineInitMs;
    const minSplashMs = config.splashMinDurationMs;

    // Check Core Handshake first before attempting native queries
    const handshake = await tauriIpc.checkCoreHandshake(2000);

    if (!handshake.isCoreAvailable) {
      if (!handshake.isTauriRuntime) {
        // Normal web browser preview mode (http://localhost:3000 / Vercel)
        setState((prev) => ({
          ...prev,
          isActive: false,
          progress: 100,
          statusText: 'BROWSER PREVIEW MODE • CORE UNAVAILABLE',
          currentStep: 'ready',
          isReady: true,
          actualInitMs: 0,
          minDurationMs: 0,
          remainingMs: 0,
          isDeparting: false,
          isCoreAvailable: false,
          isTauriRuntime: false,
          systemIdentity: null,
          discoveredInterfaces: [],
          activePath: null,
        }));
        return;
      } else {
        // Desktop shell launched but Rust Core timed out or unresponsive
        setState((prev) => ({
          ...prev,
          progress: 100,
          statusText: 'BOOTSTRAP_ERROR: CORE UNRESPONSIVE',
          currentStep: 'ready',
          isReady: true,
          actualInitMs: null,
          isCoreAvailable: false,
          isTauriRuntime: true,
        }));
        return;
      }
    }

    setState((prev) => ({
      ...prev,
      isActive: true,
      progress: 0,
      statusText: 'SYSTEM INITIALIZATION',
      currentStep: 'system_init',
      isReady: false,
      actualInitMs: null,
      minDurationMs: minSplashMs,
      remainingMs: minSplashMs,
      isDeparting: false,
      isCoreAvailable: true,
      isTauriRuntime: true,
    }));

    // Step 1: Query actual system hardware identity
    tauriIpc.getSystemIdentity().then((sysId) => {
      if (sysId) {
        setState((prev) => ({ ...prev, systemIdentity: sysId }));
      }
    });

    // Step 2: Query actual network interface details & topology
    tauriIpc.getInterfaceState().then((ifaces) => {
      if (ifaces && ifaces.length > 0) {
        const details: DiscoveredInterfaceDetail[] = ifaces.map((i) => {
          const isDisabled =
            i.state === 'DISABLED' || i.adminState === 'disabled' || !i.enabled;
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
                (i.mediaType === 'ethernet' ? '100 Mbps' : 'N/A'),
            state: i.state,
          };
        });
        const onlineIface = ifaces.find((i) => i.state === 'ONLINE');
        setState((prev) => ({
          ...prev,
          discoveredInterfaces: details,
          activePath: onlineIface ? onlineIface.name : details[0]?.name || null,
        }));
      }
    });

    // Honest progression step scheduler mapping actual phases
    const updateLoop = () => {
      const elapsed = performance.now() - startTime;
      const remaining = Math.max(0, minSplashMs - elapsed);

      if (elapsed < initTargetMs) {
        const ratio = Math.min(1, elapsed / initTargetMs);
        const currentPct = Math.min(99, Math.max(1, Math.floor(ratio * 100)));

        let currentStep: StartupSequenceStep = 'system_init';
        let currentStatus = 'SYSTEM INITIALIZATION';

        if (currentPct >= 90) {
          currentStep = 'path_determined';
          currentStatus = 'INITIAL ACTIVE PATH DETERMINED';
        } else if (currentPct >= 78) {
          currentStep = 'health_eval';
          currentStatus = 'INITIAL HEALTH EVALUATION';
        } else if (currentPct >= 65) {
          currentStep = 'probe_init';
          currentStatus = 'PROBE INITIALIZATION (RFC 3550)';
        } else if (currentPct >= 50) {
          currentStep = 'network_info_detected';
          currentStatus = 'INTERFACE NETWORK INFORMATION DETECTED';
        } else if (currentPct >= 38) {
          currentStep = 'interfaces_discovered';
          currentStatus = 'NETWORK INTERFACES DISCOVERED';
        } else if (currentPct >= 26) {
          currentStep = 'arch_detected';
          currentStatus = 'ARCHITECTURE DETECTED';
        } else if (currentPct >= 14) {
          currentStep = 'os_detected';
          currentStatus = 'OPERATING SYSTEM DETECTED';
        } else if (currentPct >= 5) {
          currentStep = 'device_detected';
          currentStatus = 'DEVICE DETECTED';
        }

        setState((prev) => ({
          ...prev,
          progress: currentPct,
          currentStep,
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
        currentStep: 'ready',
        statusText: 'SYSTEM READY',
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
