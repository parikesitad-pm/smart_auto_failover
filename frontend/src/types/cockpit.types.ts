export type InterfaceState =
  | 'ONLINE'
  | 'READY'
  | 'ALERT'
  | 'OFFLINE'
  | 'DISABLED';

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
  ipAddress?: string;
  netmask?: string;
  gateway?: string;
  ssid?: string;
  linkSpeed?: string;
  adminState?: 'enabled' | 'disabled';
  linkState?: 'connected' | 'disconnected';
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

export interface SystemTelemetry {
  cpuPercent: number;
  ramUsedMb: number;
  ramTotalMb: number;
  ramPercent: number;
  gpuPercent: number | null;
  sampleTimestampMs: number;
}

export interface SpeedtestReport {
  testId: string;
  interfaceId: string;
  downloadMbps: number;
  uploadMbps: number;
  pingMs: number;
  timestampMs: number;
  deferredDueToWorkload: boolean;
}

export interface DeviceCapabilities {
  cpuMonitoring: boolean;
  memoryMonitoring: boolean;
  gpuMonitoring: boolean;
  gpuMemoryMonitoring: boolean;
}

export interface GpuMetrics {
  gpuUsagePercent: number | null;
  gpuMemoryUsedMb: number | null;
  gpuMemoryTotalMb: number | null;
  gpuName: string | null;
}

export interface DeviceHealth {
  cpuUsagePercent: number;
  memoryUsedMb: number;
  memoryTotalMb: number;
  memoryPercent: number;
  gpu: GpuMetrics;
  timestampMs: number;
  platform: string;
  capabilities: DeviceCapabilities;
  systemPressure: 'nominal' | 'moderate' | 'critical';
}

export interface SystemIdentity {
  deviceName: string;
  osName: string;
  architecture: string;
  kernelOrVersion: string;
  totalInterfacesDetected: number;
  activeConnection: string | null;
}
