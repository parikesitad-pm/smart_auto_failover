import { useState, useEffect, useRef, useCallback } from 'react';
import {
  StartupConfig,
  StartupPreset,
  SystemIdentity,
} from '../types/cockpit.types';

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
    minDurationMs: 3000,
    remainingMs: 3000,
    systemIdentity: null,
    discoveredInterfaces: [],
    activePath: null,
    defaultGateway: null,
    isCoreAvailable: null,
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

    if (config.preset === 'fast') {
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

    const detectedPlatform =
      typeof navigator !== 'undefined' && navigator.userAgent.includes('Mac')
        ? 'macOS'
        : typeof navigator !== 'undefined' &&
            navigator.userAgent.includes('Win')
          ? 'Windows'
          : 'Linux';

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
      actualInitMs: 42,
      minDurationMs: minSplashMs,
      remainingMs: minSplashMs,
      isCoreAvailable: true,
      systemIdentity: {
        deviceName: 'Workstation-Client',
        osName: detectedPlatform,
        architecture: 'x86_64 / arm64',
        kernelOrVersion: 'Native Kernel Routing Pipeline',
        totalInterfacesDetected: 2,
        activeConnection: 'Ethernet 1',
      },
      discoveredInterfaces: [
        {
          id: 'eth0',
          name: 'Ethernet 1',
          mediaType: 'ethernet',
          adminState: 'Enabled',
          linkState: 'Connected',
          ipAddress: '192.168.1.105',
          netmask: '255.255.255.0',
          gateway: '192.168.1.1',
          ssid: 'N/A',
          linkSpeed: '1000 Mbps',
          state: 'ONLINE',
        },
        {
          id: 'wlan0',
          name: 'Wi-Fi 6',
          mediaType: 'wifi',
          adminState: 'Enabled',
          linkState: 'Connected',
          ipAddress: '192.168.1.120',
          netmask: '255.255.255.0',
          gateway: '192.168.1.1',
          ssid: 'Studio-5G',
          linkSpeed: '866 Mbps',
          state: 'READY',
        },
      ],
      activePath: 'Ethernet 1',
      defaultGateway: '192.168.1.1',
    }));

    // Progressive visual progression loop
    const updateLoop = () => {
      if (isCancelledRef.current) return;

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

      // Check if presentation time is satisfied
      if (elapsed >= minSplashMs) {
        // Reach 100% APP READY
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
