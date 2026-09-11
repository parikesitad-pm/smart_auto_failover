import { NetworkInterface, PolicyConfig } from '../types/cockpit.types';

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
      const { invoke } = await import('@tauri-apps/api');
      return invoke<NetworkInterface[]>('get_interface_state');
    }
    return [];
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
};
