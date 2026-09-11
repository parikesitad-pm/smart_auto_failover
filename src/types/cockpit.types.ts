export type InterfaceState = 'ONLINE' | 'READY' | 'ALERT' | 'OFFLINE';

export type InterfaceMediaType = 'ethernet' | 'wifi' | 'cellular';

export interface NetworkInterface {
  id: string;
  name: string;
  carrier: string;
  mediaType: InterfaceMediaType;
  enabled: boolean;
  state: InterfaceState;
  latency: number;
  jitter: number;
  score: number;
  bgProbingScore: number;
}

export type WorkloadProfile = 'conference' | 'broadcast' | 'balanced';

export interface TelemetryState {
  downloadSpeed: number;
  uploadSpeed: number;
  targetDownload: number;
  targetUpload: number;
  latency: number;
  jitter: number;
  healthScore: number;
  activePath: string;
}

export type StartupPreset = 'fast' | 'normal' | 'cinematic' | 'custom';

export interface StartupConfig {
  splashMinDurationMs: number;
  preset: StartupPreset;
  simulatedEngineInitMs: number;
  skipEnabled: boolean;
}

export interface FailoverEvent {
  id: string;
  icon: string;
  message: string;
  timestamp: string;
  type: 'info' | 'alert' | 'success';
}

export interface PolicyConfig {
  takeoverMargin: number;
  rfc3550Weight: number;
  latencyWeight: number;
  workloadProfile: WorkloadProfile;
}
