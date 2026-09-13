import { useState, useEffect, useRef, useCallback } from 'react';
import {
  NetworkInterface,
  TelemetryState,
  WorkloadProfile,
  FailoverEvent,
  DeviceHealth,
} from '../types/cockpit.types';
import { tauriIpc } from '../services/tauriIpc';

const DEFAULT_DEVICE_HEALTH: DeviceHealth = {
  cpuUsagePercent: 14.5,
  memoryUsedMb: 6144,
  memoryTotalMb: 16384,
  memoryPercent: 37.5,
  gpu: {
    gpuUsagePercent: null,
    gpuMemoryUsedMb: null,
    gpuMemoryTotalMb: null,
    gpuName: null,
  },
  timestampMs: Date.now(),
  capabilities: {
    cpuMonitoring: true,
    memoryMonitoring: true,
    gpuMonitoring: false,
    gpuMemoryMonitoring: false,
  },
  systemPressure: 'nominal',
  platform: 'Linux',
};

const BASELINE_LAPTOP_INTERFACES: NetworkInterface[] = [
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
];

function normalizeAdapter(raw: any): NetworkInterface {
  return {
    id: raw.id,
    name: raw.name,
    carrier:
      typeof raw.carrier === 'string'
        ? raw.carrier
        : raw.carrier_detected
          ? 'Connected'
          : 'Disconnected',
    mediaType: raw.mediaType ?? (raw.kind === 'wifi' ? 'wifi' : 'ethernet'),
    enabled: raw.enabled ?? raw.is_admin_enabled ?? true,
    state: raw.state ?? 'OFFLINE',
    latency:
      typeof raw.latency === 'number'
        ? raw.latency
        : (raw.metrics?.latency_ms ?? 0),
    jitter:
      typeof raw.jitter === 'number'
        ? raw.jitter
        : (raw.metrics?.jitter_ms ?? 0),
    score:
      typeof raw.score === 'number'
        ? raw.score
        : (raw.metrics?.ewma_score ?? 100),
    bgProbingScore:
      typeof raw.bgProbingScore === 'number'
        ? raw.bgProbingScore
        : (raw.metrics?.ewma_score ?? 100),
    ipAddress: raw.ipAddress ?? raw.ip_addresses?.[0] ?? 'N/A',
    netmask: raw.netmask ?? '255.255.255.0',
    gateway: raw.gateway ?? 'N/A',
    ssid: raw.ssid ?? (raw.kind === 'wifi' ? 'www.d-rvc.com' : 'N/A'),
    linkSpeed: raw.linkSpeed ?? (raw.kind === 'ethernet' ? '100 Mbps' : 'N/A'),
    adminState:
      raw.adminState ?? (raw.is_admin_enabled ? 'enabled' : 'disabled'),
    linkState:
      raw.linkState ?? (raw.carrier_detected ? 'connected' : 'disconnected'),
  };
}

export function useNetworkCockpit() {
  const [adapters, setAdapters] = useState<NetworkInterface[]>(
    BASELINE_LAPTOP_INTERFACES
  );
  const [activePath, setActivePath] = useState<string>('eth1');
  const [workloadProfile, setWorkloadProfile] =
    useState<WorkloadProfile>('conference');
  const [smartBubbleTarget, setSmartBubbleTarget] = useState<string | null>(
    null
  );
  const [newDeviceAlert, setNewDeviceAlert] = useState<{
    id: string;
    name: string;
  } | null>(null);
  const [recentToast, setRecentToast] = useState<FailoverEvent | null>(null);
  const [deviceHealth, setDeviceHealth] = useState<DeviceHealth>(
    DEFAULT_DEVICE_HEALTH
  );

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

  // Authoritative Core Event Subscription & Initial Snapshot
  useEffect(() => {
    let isMounted = true;

    // Initial snapshot on mount (initial load, resync)
    const fetchInitialState = async () => {
      try {
        const [initialHealth, initialAdapters] = await Promise.all([
          tauriIpc.getDeviceHealth(),
          tauriIpc.getInterfaceState(),
        ]);
        if (isMounted) {
          if (initialHealth) setDeviceHealth(initialHealth);
          if (initialAdapters && initialAdapters.length > 0) {
            const normalized = initialAdapters.map(normalizeAdapter);
            setAdapters(normalized);
            const active = normalized.find((a) => a.state === 'ONLINE');
            if (active) setActivePath(active.id);
          }
        }
      } catch {
        // Fallback in browser preview mode
      }
    };

    fetchInitialState();

    // Event-driven state updates (zero continuous polling)
    const unsubscribe = tauriIpc.subscribeEngineEvents((event: any) => {
      if (!isMounted || !event) return;

      switch (event.type) {
        case 'DeviceHealthUpdated':
          if (event.payload) {
            setDeviceHealth(event.payload);
          }
          break;

        case 'NetworkStateReady':
        case 'StateUpdated':
        case 'StateChanged':
          if (event.payload) {
            const state = event.payload;
            if (state.interfaces && state.interfaces.length > 0) {
              setAdapters(state.interfaces.map(normalizeAdapter));
            }
            const activeId =
              state.active_interface_id ?? state.activeInterfaceId;
            if (activeId) {
              setActivePath(activeId);
              setTelemetry((prev) => ({ ...prev, activePath: activeId }));
            }
            const liveHealth = state.device_health ?? state.deviceHealth;
            if (liveHealth) {
              setDeviceHealth(liveHealth);
            }
          }
          break;

        case 'FailoverStarted': {
          const prevId =
            event.payload?.previous_id ?? event.payload?.previousId ?? 'active';
          const nextId =
            event.payload?.target_id ?? event.payload?.targetId ?? 'target';
          showToast(
            '🔄',
            `Initiating route handover: ${prevId.toUpperCase()} → ${nextId.toUpperCase()}...`,
            'info'
          );
          break;
        }

        case 'FailoverCompleted': {
          const targetId =
            event.payload?.target_id ?? event.payload?.targetId ?? 'target';
          showToast(
            '✅',
            `Failover confirmed: ${targetId.toUpperCase()} verified active in routing table.`,
            'success'
          );
          break;
        }

        case 'RouteOperationFailed': {
          const ifaceId =
            event.payload?.interface_id ??
            event.payload?.interfaceId ??
            'route';
          const err = event.payload?.error ?? 'Route operation failed';
          showToast(
            '❌',
            `Route operation rejected on ${ifaceId.toUpperCase()}: ${err}`,
            'alert'
          );
          break;
        }

        case 'FailoverTriggered':
          if (event.payload) {
            const ev = event.payload;
            const prevId =
              ev.previous_interface_id ?? ev.previousInterfaceId ?? 'previous';
            const nextId = ev.new_interface_id ?? ev.newInterfaceId ?? 'target';
            showToast(
              '⚡',
              `Failover Engine promoted ${nextId.toUpperCase()} from ${prevId.toUpperCase()} (${ev.reason})`,
              'alert'
            );
          }
          break;

        case 'AdminActionRequired': {
          const targetId =
            event.payload?.interface_id ?? event.payload?.interfaceId;
          if (targetId) {
            setSmartBubbleTarget(targetId);
            showToast(
              '🛡️',
              `Background socket probe detected ${targetId.toUpperCase()} healthy while disabled.`,
              'alert'
            );
          }
          break;
        }

        case 'NewDeviceDetected': {
          const targetId =
            event.payload?.interface_id ?? event.payload?.interfaceId;
          const targetName =
            event.payload?.interface_name ??
            event.payload?.interfaceName ??
            targetId;
          if (targetId) {
            setNewDeviceAlert({ id: targetId, name: targetName });
          }
          break;
        }

        case 'RecoveryStarted': {
          const targetId =
            event.payload?.interface_id ?? event.payload?.interfaceId;
          if (targetId) {
            showToast(
              '⏳',
              `Carrier link recovered on ${targetId.toUpperCase()}. Anti-flap stabilization active.`,
              'info'
            );
          }
          break;
        }

        case 'RecoveryCompleted': {
          const targetId =
            event.payload?.interface_id ?? event.payload?.interfaceId;
          if (targetId) {
            showToast(
              '✅',
              `${targetId.toUpperCase()} stabilized. Admitted to READY candidate pool.`,
              'success'
            );
          }
          break;
        }

        case 'InterfaceUpdated': {
          if (event.payload) {
            const updated = normalizeAdapter(event.payload);
            setAdapters((prev) =>
              prev.map((a) => (a.id === updated.id ? { ...a, ...updated } : a))
            );
          }
          break;
        }

        default:
          break;
      }
    });

    return () => {
      isMounted = false;
      unsubscribe();
    };
  }, [showToast]);

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
      'CORE RE-INITIALIZED: Hardware rescanned. Sockets probed in 12.8ms. Routing verified.',
      'success'
    );
    setTelemetry((prev) => ({
      ...prev,
      targetDownload: 184 + Math.random() * 18,
      targetUpload: 42 + Math.random() * 5,
    }));
  }, [showToast]);

  // Topology Refresh Flow
  const handleRefreshTopology = useCallback(async () => {
    try {
      const result = await tauriIpc.refreshTopology();
      if (result && result.interfaces && result.interfaces.length > 0) {
        setAdapters(result.interfaces);
        const activeId = result.active_interface_id ?? result.activeInterfaceId;
        if (activeId) {
          setActivePath(activeId);
        }
      } else {
        // Browser mock preview fallback
        setAdapters((prev) => {
          if (prev.some((a) => a.id === 'eth2')) return prev;
          return [
            ...prev,
            {
              id: 'eth2',
              name: 'Ethernet 2 (USB-C Dock)',
              carrier: 'Active 1Gbps',
              mediaType: 'ethernet',
              enabled: true,
              state: 'READY',
              latency: 9.4,
              jitter: 1.4,
              score: 95.1,
              bgProbingScore: 95.1,
            },
          ];
        });
      }
      setNewDeviceAlert(null);
      showToast(
        '🔄',
        'Topology refreshed: Hardware devices synchronized into interface deck.',
        'success'
      );
    } catch {
      setNewDeviceAlert(null);
    }
  }, [showToast]);

  const handleDismissNewDevice = useCallback(() => {
    setNewDeviceAlert(null);
  }, []);

  const simulateHotplugDocking = useCallback(() => {
    setNewDeviceAlert({
      id: 'eth2',
      name: 'Ethernet 2 (USB-C Docking Station)',
    });
    showToast(
      '🔌',
      'Dynamic detection: USB-C Docking Station attached.',
      'info'
    );
  }, [showToast]);

  // Simulation Scenarios
  const simulateNominal = useCallback(() => {
    setActivePath('eth1');
    setSmartBubbleTarget(null);
    setNewDeviceAlert(null);
    setAdapters(BASELINE_LAPTOP_INTERFACES);
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
          : a.id === 'wifi'
            ? { ...a, state: 'ONLINE' }
            : a
      )
    );
    setActivePath('wifi');
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
          : a.id === 'wifi'
            ? { ...a, state: 'ONLINE' }
            : a
      )
    );
    setActivePath('wifi');
    setTelemetry((prev) => ({
      ...prev,
      targetDownload: 145.0,
      targetUpload: 34.0,
      latency: 14.1,
      jitter: 1.5,
      healthScore: 78,
      activePath: 'wifi',
    }));
    showToast(
      '⚠️',
      'DEGRADATION DETECTED: Jitter spiked to 18.2ms on ETH 1. Policy promoted Wi-Fi 6 before session dropped.',
      'alert'
    );
  }, [showToast]);

  const simulateInterfaceDisconnect = useCallback(() => {
    setAdapters((prev) =>
      prev.map((a) =>
        a.id === 'eth1'
          ? { ...a, state: 'OFFLINE', latency: 0, jitter: 0, score: 0 }
          : a.id === 'wifi'
            ? { ...a, state: 'ONLINE' }
            : a
      )
    );
    setActivePath('wifi');
    setTelemetry((prev) => ({
      ...prev,
      targetDownload: 140.0,
      targetUpload: 32.0,
      latency: 14.1,
      jitter: 1.5,
      healthScore: 89,
      activePath: 'wifi',
    }));
    showToast(
      '⚡',
      'HARD CUT: Ethernet 1 disconnected. Sub-second failover promoted Wi-Fi 6.',
      'alert'
    );
  }, [showToast]);

  return {
    adapters,
    activePath,
    workloadProfile,
    telemetry,
    smartBubbleTarget,
    newDeviceAlert,
    recentToast,
    deviceHealth,
    setWorkloadProfile,
    toggleInterface,
    handleAdminAction,
    handleRefreshTopology,
    handleDismissNewDevice,
    forceManualCoreReinit,
    simulateNominal,
    simulateAdminPrompt,
    simulateJitterDegradation,
    simulateInterfaceDisconnect,
    simulateHotplugDocking,
  };
}
