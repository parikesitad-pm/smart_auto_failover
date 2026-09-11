import React from 'react';
import { SimulationScenariosProps } from './SimulationScenarios.types';

export const SimulationScenarios: React.FC<SimulationScenariosProps> = ({
  onSimulateNominal,
  onSimulateAdminPrompt,
  onSimulateJitterDegradation,
  onSimulateInterfaceDisconnect,
}) => {
  return (
    <section
      aria-label="Policy Engine Simulation Controls"
      className="mt-4 pt-3 border-t border-slate-800"
    >
      <div className="text-[11px] font-mono text-slate-400 mb-2 flex items-center justify-between">
        <span className="font-bold text-slate-300">
          🎮 Policy Engine Simulation & Evaluation:
        </span>
        <span className="text-[10px] text-slate-500">
          Decoupled UI & Native Core IPC Execution
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
        {/* 1. Nominal State */}
        <button
          type="button"
          onClick={onSimulateNominal}
          className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 text-left transition-all"
        >
          <div className="font-bold text-emerald-400 text-[11px]">
            🟢 1. Nominal State
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">
            Primary Active (ETH 1)
          </div>
        </button>

        {/* 2. Admin Probe Prompt */}
        <button
          type="button"
          onClick={onSimulateAdminPrompt}
          className="p-2 rounded-lg bg-cyan-950/40 hover:bg-cyan-950/70 text-cyan-200 border border-cyan-700/70 text-left transition-all"
        >
          <div className="font-bold text-cyan-300 text-[11px]">
            🛡️ 2. Admin Evaluation
          </div>
          <div className="text-[10px] text-cyan-300/70 mt-0.5">
            Request Candidate Admission
          </div>
        </button>

        {/* 3. Jitter Degradation */}
        <button
          type="button"
          onClick={onSimulateJitterDegradation}
          className="p-2 rounded-lg bg-amber-950/40 hover:bg-amber-950/70 text-amber-200 border border-amber-700/70 text-left transition-all"
        >
          <div className="font-bold text-amber-400 text-[11px]">
            ⚠️ 3. Jitter Degradation
          </div>
          <div className="text-[10px] text-amber-300/70 mt-0.5">
            Anti-Flap Takeover Handover
          </div>
        </button>

        {/* 4. Hard Interface Disconnect */}
        <button
          type="button"
          onClick={onSimulateInterfaceDisconnect}
          className="p-2 rounded-lg bg-rose-950/40 hover:bg-rose-950/70 text-rose-200 border border-rose-700/70 text-left transition-all"
        >
          <div className="font-bold text-rose-400 text-[11px]">
            ⚡ 4. Interface Disconnect
          </div>
          <div className="text-[10px] text-rose-300/70 mt-0.5">
            Sub-Second Failover (RTO)
          </div>
        </button>
      </div>
    </section>
  );
};
