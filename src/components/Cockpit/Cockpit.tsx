import React from 'react';
import { VerticalAccentRail } from './VerticalAccentRail';
import { CockpitHeader } from './CockpitHeader';
import { PerformanceGauges } from './PerformanceGauges';
import { InterfaceDeck } from './InterfaceDeck';
import { AdminConfirmationBubble } from './AdminConfirmationBubble';
import { SimulationScenarios } from './SimulationScenarios';
import { useNetworkCockpit } from '../../hooks/useNetworkCockpit';

export interface CockpitProps {
  onOpenStartupModal: () => void;
}

export const Cockpit: React.FC<CockpitProps> = ({ onOpenStartupModal }) => {
  const {
    adapters,
    activePath,
    workloadProfile,
    telemetry,
    smartBubbleTarget,
    recentToast,
    setWorkloadProfile,
    toggleInterface,
    handleAdminAction,
    forceManualCoreReinit,
    simulateNominal,
    simulateAdminPrompt,
    simulateJitterDegradation,
    simulateInterfaceDisconnect,
  } = useNetworkCockpit();

  const activeAdapter = adapters.find((a) => a.id === activePath);
  const activePathName = activeAdapter?.name || 'Primary';

  return (
    <main className="relative max-w-5xl mx-auto rounded-2xl overflow-hidden border border-slate-800 bg-[#080b10] shadow-2xl flex flex-row">
      {/* AutoFailover 3.0 Signature Vertical Accent Rail */}
      <VerticalAccentRail />

      {/* Main Cockpit Content Area */}
      <div className="flex-1 p-5 carbon-mesh">
        {/* Cockpit Header with manual re-init and settings */}
        <CockpitHeader
          activePathName={activePathName}
          workloadProfile={workloadProfile}
          onWorkloadChange={setWorkloadProfile}
          onForceReinit={forceManualCoreReinit}
          onOpenStartupModal={onOpenStartupModal}
        />

        {/* Administrative Confirmation Bubble */}
        <AdminConfirmationBubble
          targetInterfaceId={smartBubbleTarget}
          onAction={handleAdminAction}
        />

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

        {/* Physical Interface Matrix */}
        <InterfaceDeck
          adapters={adapters}
          activePath={activePath}
          onToggleAdapter={toggleInterface}
        />

        {/* Simulation Controls */}
        <SimulationScenarios
          onSimulateNominal={simulateNominal}
          onSimulateAdminPrompt={simulateAdminPrompt}
          onSimulateJitterDegradation={simulateJitterDegradation}
          onSimulateInterfaceDisconnect={simulateInterfaceDisconnect}
        />
      </div>
    </main>
  );
};
