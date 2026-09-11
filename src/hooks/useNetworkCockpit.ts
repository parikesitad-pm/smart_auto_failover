import { useState, useEffect, useRef, useCallback } from 'react';
import {
  NetworkInterface,
  TelemetryState,
  WorkloadProfile,
  FailoverEvent,
} from '../types/cockpit.types';
import { tauriIpc } from '../services/tauriIpc';

const DEFAULT_INTERFACES: NetworkInterface[] = [
  {
    id: 'eth1',
    name: 'Ethernet 1',
    carrier: 'Active 1Gbps',
    mediaType: 'ethernet',
    enabled: true,
    state: 'ONLINE',
    latency: 8.2,
    jitter: 1.2,
    score: 98.4,
    bgProbingScore: 98.4,
  },
  {
    id: 'eth2',
    name: 'ETH 2 (Docking)',
    carrier: 'Active 1Gbps',
    mediaType: 'ethernet',
    enabled: true,
    state: 'READY',
    latency: 14.1,
    jitter: 1.5,
    score: 89.2,
    bgProbingScore: 89.2,
  },
  {
    id: 'wifi',
    name: 'Wi-Fi 6',
    carrier: 'SSID: Studio_5G',
    mediaType: 'wifi',
    enabled: true,
    state: 'READY',
    latency: 26.8,
    jitter: 3.4,
    score: 76.5,
    bgProbingScore: 76.5,
  },
  {
    id: 'usb',
    name: 'USB 5G Modem',
    carrier: 'Modem: LTE/5G High',
    mediaType: 'cellular',
    enabled: true,
    state: 'READY',
    latency: 61.4,
    jitter: 8.9,
    score: 54.0,
    bgProbingScore: 54.0,
  },
];

export function useNetworkCockpit() {
  const [adapters, setAdapters] =
    useState<NetworkInterface[]>(DEFAULT_INTERFACES);
  const [activePath, setActivePath] = useState<string>('eth1');
  const [workloadProfile, setWorkloadProfile] =
    useState<WorkloadProfile>('conference');
  const [smartBubbleTarget, setSmartBubbleTarget] = useState<string | null>(
    null
  );
  const [recentToast, setRecentToast] = useState<FailoverEvent | null>(null);

  const [telemetry, setTelemetry] = useState<TelemetryState>({
    downloadSpeed: 187.6,
    uploadSpeed: 43.2,
    targetDownload: 187.6,
    targetUpload: 43.2,
    latency: 8.2,
    jitter: 1.2,
    healthScore: 98,
    activePath: 'eth1',
  });

  const toastTimerRef = useRef<number | null>(null);

  const showToast = useCallback(
    (
      icon: string,
      message: string,
      type: 'info' | 'alert' | 'success' = 'info'
    ) => {
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
      const event: FailoverEvent = {
        id: String(Date.now()),
        icon,
        message,
        timestamp: new Date().toLocaleTimeString(),
        type,
      };
      setRecentToast(event);
      toastTimerRef.current = window.setTimeout(() => {
        setRecentToast(null);
      }, 6000);
    },
    []
  );

  // 60 FPS Client-Side Lerping loop
  useEffect(() => {
    let animId: number;
    const lerp = (start: number, end: number, amt: number) =>
      (1 - amt) * start + amt * end;

    const loop = () => {
      setTelemetry((prev) => {
        const nextDl = lerp(prev.downloadSpeed, prev.targetDownload, 0.08);
        const nextUl = lerp(prev.uploadSpeed, prev.targetUpload, 0.08);
        if (
          Math.abs(nextDl - prev.downloadSpeed) < 0.01 &&
          Math.abs(nextUl - prev.uploadSpeed) < 0.01
        ) {
          return prev;
        }
        return {
          ...prev,
          downloadSpeed: nextDl,
          uploadSpeed: nextUl,
        };
      });
      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, []);

  // Dynamic telemetry cadence simulation (5-10 Hz)
  useEffect(() => {
    const interval = setInterval(() => {
      setTelemetry((prev) => {
        const currentActive = adapters.find((a) => a.id === activePath);
        if (
          !currentActive ||
          !currentActive.enabled ||
          currentActive.state === 'OFFLINE'
        ) {
          return prev;
        }
        const dlJitter = (Math.random() - 0.5) * 6;
        const ulJitter = (Math.random() - 0.5) * 2;
        return {
          ...prev,
          targetDownload: Math.max(
            10,
            Math.min(290, prev.targetDownload + dlJitter)
          ),
          targetUpload: Math.max(5, Math.min(95, prev.targetUpload + ulJitter)),
          latency: Number(
            (currentActive.latency + (Math.random() - 0.5) * 0.4).toFixed(1)
          ),
          jitter: Number(
            (currentActive.jitter + (Math.random() - 0.5) * 0.2).toFixed(1)
          ),
        };
      });
    }, 900);
    return () => clearInterval(interval);
  }, [adapters, activePath]);

  // Administrative interface toggle
  const toggleInterface = useCallback(
    async (id: string) => {
      const adapter = adapters.find((a) => a.id === id);
      if (!adapter) return;

      if (adapter.enabled) {
        await tauriIpc.disableInterface(id);
        setAdapters((prev) =>
          prev.map((a) =>
            a.id === id ? { ...a, enabled: false, state: 'OFFLINE' } : a
          )
        );
        showToast(
          '🔒',
          `IPC: disable_interface('${id}'). Adapter administratively disabled.`,
          'info'
        );

        // Failover if active path was disabled
        if (activePath === id) {
          const eligible = adapters.filter(
            (a) => a.id !== id && a.enabled && a.state !== 'OFFLINE'
          );
          if (eligible.length > 0) {
            const nextBest = eligible.reduce((prev, curr) =>
              curr.score > prev.score ? curr : prev
            );
            setActivePath(nextBest.id);
            setAdapters((prev) =>
              prev.map((a) => {
                if (a.id === nextBest.id) return { ...a, state: 'ONLINE' };
                if (a.id === id)
                  return { ...a, enabled: false, state: 'OFFLINE' };
                return a;
              })
            );
            showToast(
              '⚡',
              `Failover Engine promoted ${nextBest.name} to active path.`,
              'success'
            );
          }
        }
      } else {
        await tauriIpc.enableInterface(id);
        setAdapters((prev) =>
          prev.map((a) =>
            a.id === id ? { ...a, enabled: true, state: 'READY' } : a
          )
        );
        showToast(
          '🔌',
          `IPC: enable_interface('${id}'). Admitted as READY candidate.`,
          'success'
        );
      }
    },
    [adapters, activePath, showToast]
  );

  // Administrative confirmation bubble action
  const handleAdminAction = useCallback(
    async (approve: boolean) => {
      if (!smartBubbleTarget) return;
      const targetId = smartBubbleTarget;
      setSmartBubbleTarget(null);

      if (approve) {
        await tauriIpc.enableInterface(targetId);
        setAdapters((prev) =>
          prev.map((a) =>
            a.id === targetId ? { ...a, enabled: true, state: 'READY' } : a
          )
        );
        showToast(
          '✅',
          `ADMIN ACTION: User enabled ${targetId.toUpperCase()}. Admitted to candidate pool.`,
          'success'
        );
      } else {
        showToast(
          '🔒',
          `ADMIN ACTION: ${targetId.toUpperCase()} kept disabled by user choice.`,
          'info'
        );
      }
    },
    [smartBubbleTarget, showToast]
  );

  // Force manual core re-initialization
  const forceManualCoreReinit = useCallback(async () => {
    await tauriIpc.forceCoreReinit();
    showToast(
      '🔄',
      'CORE RE-INITIALIZED: Hardware rescanned (4 adapters). Sockets probed in 12.8ms. Routing verified.',
      'success'
    );
    setTelemetry((prev) => ({
      ...prev,
      targetDownload: 184 + Math.random() * 18,
      targetUpload: 42 + Math.random() * 5,
    }));
  }, [showToast]);

  // Simulation Scenarios
  const simulateNominal = useCallback(() => {
    setActivePath('eth1');
    setSmartBubbleTarget(null);
    setAdapters(DEFAULT_INTERFACES);
    setTelemetry((prev) => ({
      ...prev,
      targetDownload: 187.6,
      targetUpload: 43.2,
      latency: 8.2,
      jitter: 1.2,
      healthScore: 98,
      activePath: 'eth1',
    }));
    showToast(
      '🟢',
      'Simulation: Nominal state active. Ethernet 1 Primary Online.',
      'success'
    );
  }, [showToast]);

  const simulateAdminPrompt = useCallback(() => {
    setAdapters((prev) =>
      prev.map((a) =>
        a.id === 'eth1'
          ? { ...a, enabled: false, state: 'OFFLINE' }
          : a.id === 'eth2'
            ? { ...a, state: 'ONLINE' }
            : a
      )
    );
    setActivePath('eth2');
    setSmartBubbleTarget('eth1');
    showToast(
      '🛡️',
      'Background socket probe detected Ethernet 1 healthy while disabled.',
      'alert'
    );
  }, [showToast]);

  const simulateJitterDegradation = useCallback(() => {
    setAdapters((prev) =>
      prev.map((a) =>
        a.id === 'eth1'
          ? { ...a, latency: 48.5, jitter: 18.2, score: 41.0, state: 'ALERT' }
          : a.id === 'eth2'
            ? { ...a, state: 'ONLINE' }
            : a
      )
    );
    setActivePath('eth2');
    setTelemetry((prev) => ({
      ...prev,
      targetDownload: 145.0,
      targetUpload: 34.0,
      latency: 14.1,
      jitter: 1.5,
      healthScore: 78,
      activePath: 'eth2',
    }));
    showToast(
      '⚠️',
      'DEGRADATION DETECTED: Jitter spiked to 18.2ms on ETH 1. Policy promoted ETH 2 before session dropped.',
      'alert'
    );
  }, [showToast]);

  const simulateInterfaceDisconnect = useCallback(() => {
    setAdapters((prev) =>
      prev.map((a) =>
        a.id === 'eth1'
          ? { ...a, state: 'OFFLINE', latency: 0, jitter: 0, score: 0 }
          : a.id === 'eth2'
            ? { ...a, state: 'ONLINE' }
            : a
      )
    );
    setActivePath('eth2');
    setTelemetry((prev) => ({
      ...prev,
      targetDownload: 140.0,
      targetUpload: 32.0,
      latency: 14.1,
      jitter: 1.5,
      healthScore: 89,
      activePath: 'eth2',
    }));
    showToast(
      '⚡',
      'HARD CUT: Ethernet 1 disconnected. Sub-second failover promoted ETH 2.',
      'alert'
    );
  }, [showToast]);

  return {
    adapters,
    activePath,
    workloadProfile,
    telemetry,
    smartBubbleTarget,
    recentToast,
    setWorkloadProfile,
    toggleInterface,
    handleAdminAction,
    forceManualCoreReinit,
    simulateNominal,
    simulateAdminPrompt,
    simulateJitterDegradation,
    simulateInterfaceDisconnect,
  };
}
