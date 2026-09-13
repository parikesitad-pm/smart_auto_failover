import {
  DeviceHealth,
  NetworkInterface,
  PolicyConfig,
  SystemIdentity,
} from '../types/cockpit.types';

// Check if running inside the Tauri native desktop shell
export const isTauri =
  typeof window !== 'undefined' &&
  Boolean(
    (window as any).isTauri ||
    (window as any).__TAURI_INTERNALS__ ||
    (window as any).__TAURI__ ||
    (window as any).__TAURI_IPC__
  );

export interface CoreHandshakeResult {
  isTauriRuntime: boolean;
  isCoreAvailable: boolean;
  platform?: string;
  coreVersion?: string;
  error?: string;
}

/**
 * Atomic Tauri IPC Service
 * UI only requests actions and observes engine state. Never executes routing or probing logic directly.
 */
export const tauriIpc = {
  /**
   * Verify whether Rust Core backend is actively reachable within a bounded window.
   */
  async checkCoreHandshake(timeoutMs = 2500): Promise<CoreHandshakeResult> {
    if (!isTauri) {
      return {
        isTauriRuntime: false,
        isCoreAvailable: false,
        error: 'NATIVE_CORE_UNAVAILABLE',
      };
    }
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const response = await Promise.race([
        invoke<{ core_version: string; status: string; platform: string }>(
          'core_handshake'
        ),
        new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error('HANDSHAKE_TIMEOUT')), timeoutMs)
        ),
      ]);
      return {
        isTauriRuntime: true,
        isCoreAvailable: true,
        platform: response.platform,
        coreVersion: response.core_version,
      };
    } catch (err: any) {
      return {
        isTauriRuntime: true,
        isCoreAvailable: false,
        error: err?.message || 'CORE_UNAVAILABLE',
      };
    }
  },

  /**
   * Administratively enable interface (admit into READY candidate pool, never forces ONLINE).
   */
  async enableInterface(id: string): Promise<void> {
    if (isTauri) {
      const { invoke } = await import('@tauri-apps/api/core');
      return invoke<void>('enable_interface', { id });
    }
  },

  /**
   * Administratively disable interface (remove from candidate pool).
   */
  async disableInterface(id: string): Promise<void> {
    if (isTauri) {
      const { invoke } = await import('@tauri-apps/api/core');
      return invoke<void>('disable_interface', { id });
    }
  },

  /**
   * Update policy configuration parameters.
   */
  async requestPolicyUpdate(config: PolicyConfig): Promise<void> {
    if (isTauri) {
      const { invoke } = await import('@tauri-apps/api/core');
      return invoke<void>('request_policy_update', { config });
    }
  },

  /**
   * Query current hardware adapter states from the Rust Core.
   */
  async getInterfaceState(): Promise<NetworkInterface[]> {
    if (isTauri) {
      try {
        const { invoke } = await import('@tauri-apps/api/core');
        const state = await invoke<any>('get_interface_state');
        if (state && state.interfaces) {
          return state.interfaces.map((i: any) => {
            const isDisabled =
              i.state === 'DISABLED' || i.is_admin_enabled === false;
            const isCarrier =
              !isDisabled &&
              (i.carrier_detected === true ||
                i.state === 'ONLINE' ||
                i.state === 'READY');
            return {
              id: i.id,
              name: i.name,
              carrier: isDisabled
                ? 'Disabled'
                : isCarrier
                  ? i.ssid
                    ? `SSID: ${i.ssid}`
                    : 'Connected'
                  : 'Disconnected',
              mediaType: i.kind === 'wifi' ? 'wifi' : 'ethernet',
              enabled: !isDisabled,
              state: i.state,
              latency:
                isDisabled || !isCarrier ? 0 : (i.metrics?.latency_ms ?? 0),
              jitter:
                isDisabled || !isCarrier ? 0 : (i.metrics?.jitter_ms ?? 0),
              score:
                isDisabled || !isCarrier ? 0 : (i.metrics?.ewma_score ?? 0),
              bgProbingScore:
                isDisabled || !isCarrier ? 0 : (i.metrics?.ewma_score ?? 0),
              ipAddress:
                isDisabled || !isCarrier ? '—' : (i.ip_addresses?.[0] ?? '—'),
              netmask:
                isDisabled || !isCarrier ? '—' : (i.netmask ?? '255.255.255.0'),
              gateway: isDisabled || !isCarrier ? '—' : (i.gateway ?? '—'),
              ssid:
                isDisabled || !isCarrier ? undefined : (i.ssid ?? undefined),
              linkSpeed:
                isDisabled || !isCarrier
                  ? '—'
                  : (i.link_speed ?? (i.kind === 'wifi' ? '—' : '1 Gbps')),
              adminState: isDisabled ? 'disabled' : 'enabled',
              linkState: isCarrier ? 'connected' : 'disconnected',
            };
          });
        }
      } catch (err) {
        console.warn('[IPC] Failed to fetch interface state:', err);
      }
    }
    return [];
  },

  /**
   * Force manual Core re-initialization and socket probe cycle.
   */
  async forceCoreReinit(): Promise<void> {
    if (isTauri) {
      const { invoke } = await import('@tauri-apps/api/core');
      return invoke<void>('force_core_reinit');
    }
  },

  /**
   * Re-run interface discovery after new device detection.
   */
  async refreshTopology(): Promise<any> {
    if (isTauri) {
      const { invoke } = await import('@tauri-apps/api/core');
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
      const { invoke } = await import('@tauri-apps/api/core');
      return invoke<any>('run_speedtest', { interfaceId });
    }
    return null;
  },

  /**
   * Query low-frequency passive system telemetry (CPU/RAM/GPU ~1 Hz).
   */
  async getSystemTelemetry(): Promise<any> {
    if (isTauri) {
      const { invoke } = await import('@tauri-apps/api/core');
      return invoke<any>('get_system_telemetry');
    }
    return null;
  },

  /**
   * Query dedicated Device Health domain metrics (~1 Hz).
   */
  async getDeviceHealth(): Promise<DeviceHealth | null> {
    if (isTauri) {
      const { invoke } = await import('@tauri-apps/api/core');
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
        const { invoke } = await import('@tauri-apps/api/core');
        return await invoke<SystemIdentity>('get_system_identity');
      } catch (err) {
        console.warn('[IPC] Failed to fetch system identity:', err);
      }
    }
    return null;
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
    window.open(url, '_blank', 'noopener,noreferrer');
  },
};
