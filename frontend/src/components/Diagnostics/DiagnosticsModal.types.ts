export interface DiagnosticsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSimulateNominal: () => void;
  onSimulateAdminPrompt: () => void;
  onSimulateJitterDegradation: () => void;
  onSimulateInterfaceDisconnect: () => void;
  onSimulateHotplugDocking?: () => void;
}
