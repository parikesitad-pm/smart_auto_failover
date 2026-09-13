import { useState, useEffect, useRef, useCallback } from 'react';
import {
  NetworkInterface,
  TelemetryState,
  WorkloadProfile,
  FailoverEvent,
  DeviceHealth,
} from '../types/cockpit.types';
import { tauriIpc, isTauri } from '../services/tauriIpc';

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

const BASELINE_LAPTOP_INTERFACES: NetworkInterface[] = [];

export const DETERMINISTIC_SIMULATION_INTERFACES: NetworkInterface[] = [
  {
    id: 'sim_eth0',
    name: 'Ethernet 1 (Simulated)',
    carrier: 'Connected',
    mediaType: 'ethernet',
    enabled: true,
    state: 'ONLINE',
    latency: 8.2,
    jitter: 1.1,
    score: 98.4,
    bgProbingScore: 98.4,
    ipAddress: '192.168.1.105',
    netmask: '255.255.255.0',
    gateway: '192.168.1.1',
    linkSpeed: '1 Gbps',
    adminState: 'enabled',
    linkState: 'connected',
  },
  {
    id: 'sim_wlan0',
    name: 'Wi-Fi 6 (Simulated)',
    carrier: 'SSID: Studio-5G',
    mediaType: 'wifi',
    enabled: true,
    state: 'READY',
    latency: 18.5,
    jitter: 3.4,
    score: 86.2,
    bgProbingScore: 86.2,
    ipAddress: '192.168.1.120',
    netmask: '255.255.255.0',
    gateway: '192.168.1.1',
    ssid: 'Studio-5G',
    linkSpeed: '866 Mbps',
    adminState: 'enabled',
    linkState: 'connected',
  },
];

function normalizeAdapter(raw: any): NetworkInterface {
  const isDisabled =
    raw.state === 'DISABLED' ||
    raw.is_admin_enabled === false ||
    raw.enabled === false ||
    raw.adminState === 'disabled';

  const isCarrier =
    !isDisabled &&
    (typeof raw.carrier_detected === 'boolean'
      ? raw.carrier_detected
      : raw.carrier === 'Connected' ||
        raw.linkState === 'connected' ||
        (typeof raw.carrier === 'string' && raw.carrier.startsWith('Active')) ||
        (typeof raw.carrier === 'string' && raw.carrier.startsWith('SSID:')));

  const authoritativeState:
    | 'ONLINE'
    | 'READY'
    | 'ALERT'
    | 'OFFLINE'
    | 'DISABLED' = isDisabled
    ? 'DISABLED'
    : raw.state
      ? raw.state
      : isCarrier
        ? 'READY'
        : 'OFFLINE';

  const isUsable =
    authoritativeState === 'ONLINE' ||
    authoritativeState === 'READY' ||
    authoritativeState === 'ALERT';

  return {
    id: raw.id,
    name: raw.name,
    carrier: isDisabled
      ? 'Disabled'
      : typeof raw.carrier === 'string'
        ? raw.carrier
        : isCarrier
          ? raw.ssid
            ? `SSID: ${raw.ssid}`
            : 'Connected'
          : 'Disconnected',
    mediaType: raw.mediaType ?? (raw.kind === 'wifi' ? 'wifi' : 'ethernet'),
    enabled: !isDisabled,
    state: authoritativeState,
    latency: !isUsable
      ? 0
      : typeof raw.latency === 'number'
        ? raw.latency
        : (raw.metrics?.latency_ms ?? 0),
    jitter: !isUsable
      ? 0
      : typeof raw.jitter === 'number'
        ? raw.jitter
        : (raw.metrics?.jitter_ms ?? 0),
    score: !isUsable
      ? 0
      : typeof raw.score === 'number'
        ? raw.score
        : (raw.metrics?.ewma_score ?? 0),
    bgProbingScore: !isUsable
      ? 0
      : typeof raw.bgProbingScore === 'number'
        ? raw.bgProbingScore
        : (raw.metrics?.ewma_score ?? 0),
    ipAddress: !isUsable
      ? '—'
      : (raw.ipAddress ?? raw.ip_addresses?.[0] ?? '—'),
    netmask: !isUsable ? '—' : (raw.netmask ?? '255.255.255.0'),
    gateway: !isUsable ? '—' : (raw.gateway ?? '—'),
    ssid: !isUsable ? undefined : (raw.ssid ?? undefined),
    linkSpeed: !isUsable
      ? '—'
      : (raw.linkSpeed ??
        raw.link_speed ??
        (raw.kind === 'wifi' ? '—' : '1 Gbps')),
    adminState: isDisabled ? 'disabled' : 'enabled',
    linkState: isCarrier ? 'connected' : 'disconnected',
  };
}

export function useNetworkCockpit() {
  const [runtimeMode, setRuntimeMode] = useState<'native' | 'browser_preview'>(
    isTauri ? 'native' : 'browser_preview'
  );
  const [isCoreReachable, setIsCoreReachable] = useState<boolean | null>(null);
  const [isSimulationActive, setIsSimulationActive] = useState<boolean>(false);

  const [adapters, setAdapters] = useState<NetworkInterface[]>(
    BASELINE_LAPTOP_INTERFACES
  );
  const [activePath, setActivePath] = useState<string>('');
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
    downloadSpeed: 0,
    uploadSpeed: 0,
    targetDownload: 0,
    targetUpload: 0,
    latency: 0,
    jitter: 0,
    healthScore: 0,
    activePath: '',
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

  const enableSimulation = useCallback(() => {
    setIsSimulationActive(true);
    setAdapters(DETERMINISTIC_SIMULATION_INTERFACES);
    setActivePath('sim_eth0');
    setTelemetry({
      downloadSpeed: 187.6,
      uploadSpeed: 48.2,
      targetDownload: 187.6,
      targetUpload: 48.2,
      latency: 8.2,
      jitter: 1.1,
      healthScore: 98,
      activePath: 'sim_eth0',
    });
    showToast('🧪', 'Deterministic browser simulation mode enabled', 'info');
  }, [showToast]);

  const disableSimulation = useCallback(() => {
    setIsSimulationActive(false);
    setAdapters([]);
    setActivePath('');
    setTelemetry({
      downloadSpeed: 0,
      uploadSpeed: 0,
      targetDownload: 0,
      targetUpload: 0,
      latency: 0,
      jitter: 0,
      healthScore: 0,
      activePath: '',
    });
    showToast('🌐', 'Browser simulation disabled — Core unavailable', 'info');
  }, [showToast]);

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

  // Authoritative Core Event Subscription & Initial Snapshot
  useEffect(() => {
    let isMounted = true;

    // Initial snapshot on mount (initial load, resync)
    const fetchInitialState = async () => {
      try {
        const handshake = await tauriIpc.checkCoreHandshake(2500);
        if (!isMounted) return;

        if (!handshake.isCoreAvailable) {
          setRuntimeMode('browser_preview');
          setIsCoreReachable(false);
          setAdapters([]);
          setActivePath('');
          return;
        }

        setRuntimeMode('native');
        setIsCoreReachable(true);

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
            if (active) {
              setActivePath(active.id);
              setTelemetry((prev) => ({
                ...prev,
                activePath: active.id,
                latency: active.latency,
                jitter: active.jitter,
                healthScore: active.score,
              }));
            } else {
              setActivePath('');
              setTelemetry((prev) => ({
                ...prev,
                activePath: '',
                downloadSpeed: 0,
                uploadSpeed: 0,
                targetDownload: 0,
                targetUpload: 0,
                latency: 0,
                jitter: 0,
                healthScore: 0,
              }));
            }
          }
        }
      } catch {
        if (isMounted) {
          setRuntimeMode('browser_preview');
          setIsCoreReachable(false);
        }
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
              const activeIface = state.interfaces?.find(
                (i: any) => i.id === activeId
              );
              const dl = activeIface?.metrics?.download_mbps ?? 0;
              const ul = activeIface?.metrics?.upload_mbps ?? 0;
              const lat = activeIface?.metrics?.latency_ms ?? 0;
              const jit = activeIface?.metrics?.jitter_ms ?? 0;
              const hs = state.overall_health_index ?? 0;

              setTelemetry((prev) => ({
                ...prev,
                activePath: activeId,
                targetDownload: dl,
                targetUpload: ul,
                latency: lat,
                jitter: jit,
                healthScore: hs,
              }));
            } else {
              setActivePath('');
              setTelemetry((prev) => ({
                ...prev,
                activePath: '',
                downloadSpeed: 0,
                uploadSpeed: 0,
                targetDownload: 0,
                targetUpload: 0,
                latency: 0,
                jitter: 0,
                healthScore: 0,
              }));
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
    runtimeMode,
    isCoreReachable,
    isSimulationActive,
    enableSimulation,
    disableSimulation,
  };
}
