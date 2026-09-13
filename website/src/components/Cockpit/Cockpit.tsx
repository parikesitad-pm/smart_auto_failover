import React, { useState, useEffect } from 'react';
import { VerticalAccentRail } from './VerticalAccentRail';
import { CockpitHeader } from './CockpitHeader';
import { PerformanceGauges } from './PerformanceGauges';
import { InterfaceDeck } from './InterfaceDeck';
import { AdminConfirmationBubble } from './AdminConfirmationBubble';
import { CockpitFooter } from './CockpitFooter';
import { DemoToolbar } from './DemoToolbar';
import { DiagnosticsModal } from '../Diagnostics';
import { useNetworkCockpit } from '../../hooks/useNetworkCockpit';

export interface CockpitProps {
  onOpenStartupModal: () => void;
}

export const Cockpit: React.FC<CockpitProps> = ({ onOpenStartupModal }) => {
  const [isDiagnosticsOpen, setIsDiagnosticsOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        (e.shiftKey && e.key === 'D') ||
        (e.ctrlKey && e.shiftKey && e.key === 'D')
      ) {
        setIsDiagnosticsOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const {
    adapters,
    activePath,
    workloadProfile,
    telemetry,
    smartBubbleTarget,
    newDeviceAlert,
    recentToast,
    deviceHealth,
    setWorkloadProfile,
    toggleInterface,
    handleAdminAction,
    handleRefreshTopology,
    handleDismissNewDevice,
    forceManualCoreReinit,
    simulateNominal,
    simulateAdminPrompt,
    simulateJitterDegradation,
    simulateInterfaceDisconnect,
    simulateHotplugDocking,
    runtimeMode,
    isCoreReachable,
    isSimulationActive,
    enableSimulation,
    disableSimulation,
    disconnectEthernet,
    reconnectEthernet,
    disableWifi,
    enableWifi,
    degradeConnection,
    recoverConnection,
    resetDemo,
  } = useNetworkCockpit();

  const activeAdapter = adapters.find(
    (a) => a.id === activePath && a.state === 'ONLINE'
  );
  const activePathName = activeAdapter?.name || '';

  return (
    <main className="relative max-w-5xl mx-auto rounded-2xl overflow-hidden border border-slate-800 bg-[#080b10] shadow-2xl flex flex-row">
      {/* AutoFailover 3.0 Signature Vertical Accent Rail */}
      <VerticalAccentRail />

      {/* Main Cockpit Content Area */}
      <div className="flex-1 p-5 carbon-mesh">
        {/* Cockpit Header with manual re-init, diagnostics, and settings */}
        <CockpitHeader
          activePathName={activePathName}
          workloadProfile={workloadProfile}
          deviceHealth={deviceHealth}
          onWorkloadChange={setWorkloadProfile}
          onForceReinit={forceManualCoreReinit}
          onOpenStartupModal={onOpenStartupModal}
          onOpenDiagnostics={() => setIsDiagnosticsOpen(true)}
          isBrowserPreview={runtimeMode === 'browser_preview'}
          isSimulationActive={isSimulationActive}
        />

        {/* Administrative Confirmation Bubble */}
        <AdminConfirmationBubble
          targetInterfaceId={smartBubbleTarget}
          onAction={handleAdminAction}
        />

        {/* Dynamic Hardware Detection Notification (Non-blocking) */}
        {newDeviceAlert && (
          <div
            role="status"
            className="my-2.5 px-4 py-2.5 rounded-xl border border-sky-500/50 bg-sky-950/70 shadow-lg flex items-center justify-between text-xs font-mono text-sky-200"
          >
            <div className="flex items-center space-x-2.5">
              <span className="text-base">🔌</span>
              <div>
                <p className="font-semibold text-white">
                  New network device detected.
                </p>
                <p className="text-sky-300 text-[11px]">
                  Refresh to add it to the interface list.
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2 shrink-0">
              <button
                type="button"
                onClick={handleRefreshTopology}
                className="px-3.5 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs transition-colors shadow"
              >
                Refresh
              </button>
              <button
                type="button"
                onClick={handleDismissNewDevice}
                className="px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs transition-colors"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Failover Engine Event Toast */}
        {recentToast && (
          <div
            role="status"
            className={`my-2 px-3.5 py-2 rounded-xl border flex items-center justify-between text-xs font-mono toast-anim ${
              recentToast.type === 'alert'
                ? 'border-amber-600 bg-amber-950/80 text-amber-200'
                : recentToast.type === 'success'
                  ? 'border-cyan-500 bg-cyan-950/80 text-cyan-200'
                  : 'border-slate-700 bg-slate-900 text-slate-300'
            }`}
          >
            <div className="flex items-center space-x-2">
              <span>{recentToast.icon}</span>
              <span className="font-bold">{recentToast.message}</span>
            </div>
            <span className="text-[10px] text-slate-400">
              {recentToast.timestamp}
            </span>
          </div>
        )}

        {/* Mathematical Performance Gauges */}
        <PerformanceGauges telemetry={telemetry} />

        {/* Interactive Scenario Controls (7 Core Demo Actions) */}
        <DemoToolbar
          onDisconnectEthernet={disconnectEthernet}
          onReconnectEthernet={reconnectEthernet}
          onDisableWifi={disableWifi}
          onEnableWifi={enableWifi}
          onDegradeConnection={degradeConnection}
          onRecoverConnection={recoverConnection}
          onResetDemo={resetDemo}
        />

        {/* Physical Interface Matrix */}
        <InterfaceDeck
          adapters={adapters}
          activePath={activePath}
          onToggleAdapter={toggleInterface}
          runtimeMode={runtimeMode}
          isCoreReachable={isCoreReachable}
          isSimulationActive={isSimulationActive}
          onEnableSimulation={enableSimulation}
          onDisableSimulation={disableSimulation}
        />

        {/* Cockpit Footer Attribution */}
        <CockpitFooter />

        {/* Diagnostics & Simulation Modal (Out of normal Home view) */}
        <DiagnosticsModal
          isOpen={isDiagnosticsOpen}
          onClose={() => setIsDiagnosticsOpen(false)}
          onSimulateNominal={simulateNominal}
          onSimulateAdminPrompt={simulateAdminPrompt}
          onSimulateJitterDegradation={simulateJitterDegradation}
          onSimulateInterfaceDisconnect={simulateInterfaceDisconnect}
          onSimulateHotplugDocking={simulateHotplugDocking}
        />
      </div>
    </main>
  );
};
