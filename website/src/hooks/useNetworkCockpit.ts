import { useState, useEffect, useRef, useCallback } from 'react';
import {
  NetworkInterface,
  TelemetryState,
  WorkloadProfile,
  FailoverEvent,
  DeviceHealth,
} from '../types/cockpit.types';

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
  platform:
    typeof navigator !== 'undefined' && navigator.userAgent.includes('Mac')
      ? 'macOS'
      : typeof navigator !== 'undefined' && navigator.userAgent.includes('Win')
        ? 'Windows'
        : 'Linux',
};

const NOMINAL_INTERFACES: NetworkInterface[] = [
  {
    id: 'eth0',
    name: 'Ethernet 1',
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
    id: 'wifi0',
    name: 'Wi-Fi 6',
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

export function useNetworkCockpit() {
  const [adapters, setAdapters] = useState<NetworkInterface[]>(NOMINAL_INTERFACES);
  const [activePath, setActivePath] = useState<string>('eth0');
  const [workloadProfile, setWorkloadProfile] = useState<WorkloadProfile>('conference');
  const [smartBubbleTarget, setSmartBubbleTarget] = useState<string | null>(null);
  const [newDeviceAlert, setNewDeviceAlert] = useState<{ id: string; name: string } | null>(null);
  const [recentToast, setRecentToast] = useState<FailoverEvent | null>(null);
  const [deviceHealth, setDeviceHealth] = useState<DeviceHealth>(DEFAULT_DEVICE_HEALTH);

  const [telemetry, setTelemetry] = useState<TelemetryState>({
    downloadSpeed: 187.6,
    uploadSpeed: 48.2,
    targetDownload: 187.6,
    targetUpload: 48.2,
    latency: 8.2,
    jitter: 1.1,
    healthScore: 98,
    activePath: 'eth0',
  });

  const toastTimerRef = useRef<number | null>(null);

  const showToast = useCallback(
    (icon: string, message: string, type: 'info' | 'alert' | 'success' = 'info') => {
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

  // 60 FPS Client-Side Lerping loop for smooth gauge animations
  useEffect(() => {
    let animId: number;
    const lerp = (start: number, end: number, amt: number) => (1 - amt) * start + amt * end;

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

  // Low-frequency passive simulated device telemetry (~1 Hz)
  useEffect(() => {
    const interval = setInterval(() => {
      setDeviceHealth((prev) => {
        const cpuNoise = (Math.random() - 0.5) * 2;
        const newCpu = Math.max(8, Math.min(32, +(prev.cpuUsagePercent + cpuNoise).toFixed(1)));
        return {
          ...prev,
          cpuUsagePercent: newCpu,
          timestampMs: Date.now(),
        };
      });
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // ----------------------------------------------------
  // Interactive Simulator Controls
  // ----------------------------------------------------

  // 1. Disconnect Ethernet
  const disconnectEthernet = useCallback(() => {
    setAdapters((prev) =>
      prev.map((a) => {
        if (a.id === 'eth0') {
          return {
            ...a,
            state: 'OFFLINE',
            carrier: 'Disconnected',
            linkState: 'disconnected',
            latency: 0,
            jitter: 0,
            score: 0,
          };
        }
        if (a.id === 'wifi0' && a.enabled) {
          return { ...a, state: 'ONLINE' };
        }
        return a;
      })
    );
    setActivePath('wifi0');
    setTelemetry((prev) => ({
      ...prev,
      targetDownload: 142.5,
      targetUpload: 38.0,
      latency: 18.5,
      jitter: 3.4,
      healthScore: 86,
      activePath: 'wifi0',
    }));
    showToast(
      '⚡',
      'HARD CUT: Ethernet 1 physical link down. Sub-second failover promoted Wi-Fi 6 to ONLINE.',
      'alert'
    );
  }, [showToast]);

  // 2. Reconnect Ethernet
  const reconnectEthernet = useCallback(() => {
    setAdapters((prev) =>
      prev.map((a) => {
        if (a.id === 'eth0') {
          return {
            ...a,
            enabled: true,
            adminState: 'enabled',
            state: 'ONLINE',
            carrier: 'Connected',
            linkState: 'connected',
            latency: 8.2,
            jitter: 1.1,
            score: 98.4,
            bgProbingScore: 98.4,
          };
        }
        if (a.id === 'wifi0' && a.enabled) {
          return { ...a, state: 'READY' };
        }
        return a;
      })
    );
    setActivePath('eth0');
    setTelemetry((prev) => ({
      ...prev,
      targetDownload: 187.6,
      targetUpload: 48.2,
      latency: 8.2,
      jitter: 1.1,
      healthScore: 98,
      activePath: 'eth0',
    }));
    showToast(
      '🔄',
      'RECOVERY: Ethernet 1 link restored. Anti-flap arbiter verified stability — promoted to primary active path.',
      'success'
    );
  }, [showToast]);

  // 3. Disable Wi-Fi
  const disableWifi = useCallback(() => {
    setAdapters((prev) => {
      const next = prev.map((a) =>
        a.id === 'wifi0'
          ? {
              ...a,
              enabled: false,
              adminState: 'disabled' as const,
              state: 'DISABLED' as const,
              carrier: 'Disabled',
              score: 0,
            }
          : a
      );
      return next;
    });

    // If Wi-Fi was active, failover to Ethernet if healthy
    setActivePath((prevActive) => {
      if (prevActive === 'wifi0') {
        const eth = adapters.find((a) => a.id === 'eth0');
        if (eth && eth.enabled && eth.linkState === 'connected') {
          setAdapters((list) =>
            list.map((a) => (a.id === 'eth0' ? { ...a, state: 'ONLINE' } : a))
          );
          setTelemetry((t) => ({
            ...t,
            targetDownload: 187.6,
            targetUpload: 48.2,
            latency: 8.2,
            jitter: 1.1,
            healthScore: 98,
            activePath: 'eth0',
          }));
          return 'eth0';
        }
        setTelemetry((t) => ({
          ...t,
          targetDownload: 0,
          targetUpload: 0,
          latency: 0,
          jitter: 0,
          healthScore: 0,
          activePath: '',
        }));
        return '';
      }
      return prevActive;
    });

    showToast('🛡️', 'ADAPTER: Wi-Fi 6 administratively disabled.', 'info');
  }, [adapters, showToast]);

  // 4. Enable Wi-Fi
  const enableWifi = useCallback(() => {
    setAdapters((prev) =>
      prev.map((a) => {
        if (a.id === 'wifi0') {
          const isEthOnline = prev.some((x) => x.id === 'eth0' && x.state === 'ONLINE');
          return {
            ...a,
            enabled: true,
            adminState: 'enabled',
            state: isEthOnline ? 'READY' : 'ONLINE',
            carrier: 'SSID: Studio-5G',
            linkState: 'connected',
            latency: 18.5,
            jitter: 3.4,
            score: 86.2,
            bgProbingScore: 86.2,
          };
        }
        return a;
      })
    );

    setActivePath((prevActive) => {
      if (!prevActive) {
        setTelemetry({
          downloadSpeed: 0,
          uploadSpeed: 0,
          targetDownload: 142.5,
          targetUpload: 38.0,
          latency: 18.5,
          jitter: 3.4,
          healthScore: 86,
          activePath: 'wifi0',
        });
        return 'wifi0';
      }
      return prevActive;
    });

    showToast(
      '✅',
      'ADAPTER: Wi-Fi 6 administratively enabled — ready as standby failover path.',
      'success'
    );
  }, [showToast]);

  // 5. Degrade Connection (Jitter Spike / Packet Loss)
  const degradeConnection = useCallback(() => {
    setAdapters((prev) =>
      prev.map((a) => {
        if (a.id === 'eth0') {
          return {
            ...a,
            state: 'ALERT',
            latency: 48.5,
            jitter: 18.2,
            score: 41.0,
          };
        }
        if (a.id === 'wifi0' && a.enabled && a.linkState === 'connected') {
          return { ...a, state: 'ONLINE' };
        }
        return a;
      })
    );
    setActivePath('wifi0');
    setTelemetry((prev) => ({
      ...prev,
      targetDownload: 142.5,
      targetUpload: 38.0,
      latency: 18.5,
      jitter: 3.4,
      healthScore: 86,
      activePath: 'wifi0',
    }));
    showToast(
      '⚠️',
      'DEGRADATION DETECTED: Jitter spiked to 18.2ms on ETH 1. Policy Engine promoted Wi-Fi 6 before stream stalled.',
      'alert'
    );
  }, [showToast]);

  // 6. Recover Connection
  const recoverConnection = useCallback(() => {
    setAdapters((prev) =>
      prev.map((a) => {
        if (a.id === 'eth0') {
          return {
            ...a,
            state: 'ONLINE',
            carrier: 'Connected',
            linkState: 'connected',
            latency: 8.2,
            jitter: 1.1,
            score: 98.4,
            bgProbingScore: 98.4,
          };
        }
        if (a.id === 'wifi0' && a.enabled) {
          return { ...a, state: 'READY' };
        }
        return a;
      })
    );
    setActivePath('eth0');
    setTelemetry((prev) => ({
      ...prev,
      targetDownload: 187.6,
      targetUpload: 48.2,
      latency: 8.2,
      jitter: 1.1,
      healthScore: 98,
      activePath: 'eth0',
    }));
    showToast(
      '🟢',
      'RESTORED: Ethernet 1 path stability confirmed. Clean failback executed.',
      'success'
    );
  }, [showToast]);

  // 7. Reset Demo (Nominal State)
  const resetDemo = useCallback(() => {
    setAdapters(NOMINAL_INTERFACES);
    setActivePath('eth0');
    setSmartBubbleTarget(null);
    setNewDeviceAlert(null);
    setTelemetry({
      downloadSpeed: 187.6,
      uploadSpeed: 48.2,
      targetDownload: 187.6,
      targetUpload: 48.2,
      latency: 8.2,
      jitter: 1.1,
      healthScore: 98,
      activePath: 'eth0',
    });
    showToast('✨', 'DEMO RESET: Restored nominal dual-homed network cockpit topology.', 'success');
  }, [showToast]);

  // Interface Deck toggle handler
  const toggleInterface = useCallback(
    (id: string) => {
      const target = adapters.find((a) => a.id === id);
      if (!target) return;

      if (target.enabled) {
        if (id === 'eth0') {
          disconnectEthernet();
        } else if (id === 'wifi0') {
          disableWifi();
        }
      } else {
        if (id === 'eth0') {
          reconnectEthernet();
        } else if (id === 'wifi0') {
          enableWifi();
        }
      }
    },
    [adapters, disconnectEthernet, disableWifi, reconnectEthernet, enableWifi]
  );

  // Admin confirmation bubble action
  const handleAdminAction = useCallback(
    (accept: boolean) => {
      if (accept && smartBubbleTarget) {
        if (smartBubbleTarget === 'eth0') reconnectEthernet();
        if (smartBubbleTarget === 'wifi0') enableWifi();
      }
      setSmartBubbleTarget(null);
    },
    [smartBubbleTarget, reconnectEthernet, enableWifi]
  );

  // Dynamic device alert handlers
  const handleRefreshTopology = useCallback(() => {
    setAdapters((prev) => {
      if (prev.some((a) => a.id === 'eth2')) return prev;
      return [
        ...prev,
        {
          id: 'eth2',
          name: 'Ethernet 2 (USB-C Dock)',
          carrier: 'Connected',
          mediaType: 'ethernet',
          enabled: true,
          state: 'READY',
          latency: 9.4,
          jitter: 1.4,
          score: 95.1,
          bgProbingScore: 95.1,
          ipAddress: '192.168.2.10',
          netmask: '255.255.255.0',
          gateway: '192.168.2.1',
          linkSpeed: '1 Gbps',
          adminState: 'enabled',
          linkState: 'connected',
        },
      ];
    });
    setNewDeviceAlert(null);
    showToast('🔄', 'Topology refreshed: USB-C Dock synchronized into interface deck.', 'success');
  }, [showToast]);

  const handleDismissNewDevice = useCallback(() => {
    setNewDeviceAlert(null);
  }, []);

  const simulateHotplugDocking = useCallback(() => {
    setNewDeviceAlert({
      id: 'eth2',
      name: 'Ethernet 2 (USB-C Docking Station)',
    });
    showToast('🔌', 'Dynamic detection: USB-C Docking Station attached.', 'info');
  }, [showToast]);

  const forceManualCoreReinit = useCallback(() => {
    showToast('🔄', 'Policy Engine re-evaluating physical link quality scores...', 'info');
    setTimeout(() => {
      showToast('✅', 'Kernel route metrics verified nominal.', 'success');
    }, 600);
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
    simulateNominal: resetDemo,
    simulateAdminPrompt: useCallback(() => {
      setSmartBubbleTarget('eth0');
      showToast('🛡️', 'Background socket probe detected Ethernet 1 healthy while disabled.', 'alert');
    }, [showToast]),
    simulateJitterDegradation: degradeConnection,
    simulateInterfaceDisconnect: disconnectEthernet,
    simulateHotplugDocking,
    runtimeMode: 'browser_preview' as const,
    isCoreReachable: true,
    isSimulationActive: true,
    enableSimulation: resetDemo,
    disableSimulation: useCallback(() => {
      showToast('ℹ️', 'Deterministic simulation active.', 'info');
    }, [showToast]),

    // Explicit 7 Demo Controls
    disconnectEthernet,
    reconnectEthernet,
    disableWifi,
    enableWifi,
    degradeConnection,
    recoverConnection,
    resetDemo,
  };
}
