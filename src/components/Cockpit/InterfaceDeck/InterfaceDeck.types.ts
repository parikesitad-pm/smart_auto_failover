import { NetworkInterface } from '../../../types/cockpit.types';

export interface InterfaceDeckProps {
  adapters: NetworkInterface[];
  activePath: string;
  onToggleAdapter: (id: string) => void;
}
