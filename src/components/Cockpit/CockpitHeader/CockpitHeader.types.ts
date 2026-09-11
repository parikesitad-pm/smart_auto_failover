import { WorkloadProfile } from '../../../types/cockpit.types';

export interface CockpitHeaderProps {
  activePathName: string;
  workloadProfile: WorkloadProfile;
  onWorkloadChange: (profile: WorkloadProfile) => void;
  onForceReinit: () => void;
  onOpenStartupModal: () => void;
}
