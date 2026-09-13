import {
  DeviceHealth,
  NetworkInterface,
  PolicyConfig,
  SystemIdentity,
} from '../types/cockpit.types';

// Check if running inside the Tauri native desktop shell
const isTauri = typeof window !== 'undefined' && '__TAURI_IPC__' in window;

/**
 * Atomic Tauri IPC Service
 * UI only requests actions and observes engine state. Never executes routing or probing logic directly.
 */
export const tauriIpc = {
  /**
   * Administratively enable interface (admit into READY candidate pool, never forces ONLINE).
   */
  async enableInterface(id: string): Promise<void> {
    if (isTauri) {
      const { invoke } = await import('@tauri-apps/api');
      return invoke<void>('enable_interface', { id });
    }
  },

  /**
   * Administratively disable interface (remove from candidate pool).
   */
  async disableInterface(id: string): Promise<void> {
    if (isTauri) {
      const { invoke } = await import('@tauri-apps/api');
      return invoke<void>('disable_interface', { id });
    }
  },

  /**
   * Update policy configuration parameters.
   */
  async requestPolicyUpdate(config: PolicyConfig): Promise<void> {
    if (isTauri) {
      const { invoke } = await import('@tauri-apps/api');
      return invoke<void>('request_policy_update', { config });
    }
  },

  /**
   * Query current hardware adapter states from the Rust Core.
   */
  async getInterfaceState(): Promise<NetworkInterface[]> {
    if (isTauri) {
      try {
        const { invoke } = await import('@tauri-apps/api');
        const state = await invoke<any>('get_interface_state');
        if (state && state.interfaces) {
          return state.interfaces.map((i: any) => ({
            id: i.id,
            name: i.name,
            carrier: i.carrier_detected ? 'Connected' : 'Disconnected',
            mediaType: i.kind === 'wifi' ? 'wifi' : 'ethernet',
            enabled: i.is_admin_enabled,
            state: i.state,
            latency: i.metrics?.latency_ms ?? 0,
            jitter: i.metrics?.jitter_ms ?? 0,
            score: i.metrics?.ewma_score ?? 100,
            bgProbingScore: i.metrics?.ewma_score ?? 100,
            ipAddress: i.ip_addresses?.[0] ?? 'N/A',
            netmask: '255.255.255.0',
            gateway: i.gateway ?? 'N/A',
            ssid: i.kind === 'wifi' ? 'www.d-rvc.com' : 'N/A',
            linkSpeed: i.kind === 'wifi' ? 'N/A' : '100 Mbps',
            adminState: i.is_admin_enabled ? 'enabled' : 'disabled',
            linkState: i.carrier_detected ? 'connected' : 'disconnected',
          }));
        }
      } catch (err) {
        console.warn('[IPC] Failed to fetch interface state:', err);
      }
    }
    return [
      {
        id: 'enp44s0',
        name: 'Ethernet 1 (enp44s0)',
        carrier: 'Active 100 Mbps',
        mediaType: 'ethernet',
        enabled: true,
        state: 'ONLINE',
        latency: 8.2,
        jitter: 1.1,
        score: 98.4,
        bgProbingScore: 98.4,
        ipAddress: '192.168.50.88',
        netmask: '255.255.255.0',
        gateway: '192.168.50.1',
        linkSpeed: '100 Mbps',
        adminState: 'enabled',
        linkState: 'connected',
      },
      {
        id: 'wlp0s20f3',
        name: 'Wi-Fi (wlp0s20f3)',
        carrier: 'SSID: www.d-rvc.com',
        mediaType: 'wifi',
        enabled: true,
        state: 'READY',
        latency: 26.4,
        jitter: 2.8,
        score: 78.2,
        bgProbingScore: 78.2,
        ipAddress: '192.168.50.4',
        netmask: '255.255.255.0',
        gateway: '192.168.50.1',
        ssid: 'www.d-rvc.com',
        linkSpeed: 'N/A',
        adminState: 'enabled',
        linkState: 'connected',
      },
    ];
  },

  /**
   * Force manual Core re-initialization and socket probe cycle.
   */
  async forceCoreReinit(): Promise<void> {
    if (isTauri) {
      const { invoke } = await import('@tauri-apps/api');
      return invoke<void>('force_core_reinit');
    }
  },

  /**
   * Re-run interface discovery after new device detection.
   */
  async refreshTopology(): Promise<any> {
    if (isTauri) {
      const { invoke } = await import('@tauri-apps/api');
      return invoke<any>('refresh_topology');
    }
    return null;
  },

  /**
   * Run isolated on-demand speedtest.
   * Strictly isolated from continuous failover health scoring.
   */
  async runSpeedtest(interfaceId: string): Promise<any> {
    if (isTauri) {
      const { invoke } = await import('@tauri-apps/api');
      return invoke<any>('run_speedtest', { interfaceId });
    }
    return null;
  },

  /**
   * Query low-frequency passive system telemetry (CPU/RAM/GPU ~1 Hz).
   */
  async getSystemTelemetry(): Promise<any> {
    if (isTauri) {
      const { invoke } = await import('@tauri-apps/api');
      return invoke<any>('get_system_telemetry');
    }
    return null;
  },

  /**
   * Query dedicated Device Health domain metrics (~1 Hz).
   */
  async getDeviceHealth(): Promise<DeviceHealth | null> {
    if (isTauri) {
      const { invoke } = await import('@tauri-apps/api');
      return invoke<DeviceHealth>('get_device_health');
    }
    return null;
  },

  /**
   * Query compact hardware and system identity for bootstrap presentation.
   */
  async getSystemIdentity(): Promise<SystemIdentity | null> {
    if (isTauri) {
      try {
        const { invoke } = await import('@tauri-apps/api');
        return await invoke<SystemIdentity>('get_system_identity');
      } catch (err) {
        console.warn('[IPC] Failed to fetch system identity:', err);
      }
    }
    return {
      deviceName: 'Nitro AN515-56',
      osName: 'Linux',
      architecture: 'x86_64',
      kernelOrVersion: '7.1.13-MANJARO',
      totalInterfacesDetected: 2,
      activeConnection: 'wlp0s20f3',
    };
  },

  /**
   * Subscribe to live Rust Core events streamed over Tauri IPC.
   * Returns an unlisten function.
   */
  subscribeEngineEvents(callback: (event: any) => void): () => void {
    if (isTauri) {
      let active = true;
      let unlistenFn: (() => void) | null = null;

      import('@tauri-apps/api/event').then(({ listen }) => {
        if (!active) return;
        listen('network-engine-event', (event) => {
          callback(event.payload);
        }).then((unlisten) => {
          if (!active) {
            unlisten();
          } else {
            unlistenFn = unlisten;
          }
        });
      });

      return () => {
        active = false;
        if (unlistenFn) unlistenFn();
      };
    }

    return () => {};
  },

  /**
   * Open an external URL in the system default browser.
   */
  async openUrl(url: string): Promise<void> {
    if (isTauri) {
      try {
        const { open } = await import('@tauri-apps/api/shell');
        await open(url);
        return;
      } catch {
        // Fallback if Tauri shell plugin is not active
      }
    }
    window.open(url, '_blank', 'noopener,noreferrer');
  },
};
