import { DeviceHealth, WorkloadProfile } from '../../../types/cockpit.types';

export interface CockpitHeaderProps {
  activePathName: string;
  workloadProfile: WorkloadProfile;
  deviceHealth: DeviceHealth;
  onWorkloadChange: (profile: WorkloadProfile) => void;
  onForceReinit: () => void;
  onOpenStartupModal: () => void;
  onOpenDiagnostics: () => void;
}
