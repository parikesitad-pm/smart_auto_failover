import { NetworkInterface } from '../../../types/cockpit.types';

export interface InterfaceDeckProps {
  adapters: NetworkInterface[];
  activePath: string;
  onToggleAdapter: (id: string) => void;
  runtimeMode?: 'native' | 'browser_preview';
  isCoreReachable?: boolean | null;
  isSimulationActive?: boolean;
  onEnableSimulation?: () => void;
  onDisableSimulation?: () => void;
}
