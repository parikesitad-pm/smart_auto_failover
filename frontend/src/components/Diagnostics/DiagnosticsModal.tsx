import React, { useEffect } from 'react';
import { DiagnosticsModalProps } from './DiagnosticsModal.types';

export const DiagnosticsModal: React.FC<DiagnosticsModalProps> = ({
  isOpen,
  onClose,
  onSimulateNominal,
  onSimulateAdminPrompt,
  onSimulateJitterDegradation,
  onSimulateInterfaceDisconnect,
  onSimulateHotplugDocking,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-2xl bg-[#090d16] border border-slate-800/90 rounded-2xl shadow-2xl p-6 relative overflow-hidden font-mono">
        {/* Top Bezel Accent */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-sky-400 via-blue-600 to-rose-500 opacity-80" />

        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800/60 pb-4 mb-4">
          <div className="flex items-center gap-3">
            <span className="text-xl">🧪</span>
            <div>
              <h2 className="text-xs font-bold tracking-[0.2em] text-slate-100 uppercase">
                Policy Engine Diagnostics & Simulation
              </h2>
              <p className="text-[10px] text-slate-400 mt-0.5">
                Isolated evaluation scenarios for failover and state machine
                verification
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 p-1.5 rounded-lg text-sm transition-colors"
            title="Close diagnostics (Esc)"
          >
            ✕
          </button>
        </div>

        {/* Scenario Buttons Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs mb-5">
          {/* 1. Nominal State */}
          <button
            type="button"
            onClick={() => {
              onSimulateNominal();
              onClose();
            }}
            className="p-3 rounded-xl bg-slate-900/80 hover:bg-slate-800/90 text-slate-200 border border-slate-700/80 text-left transition-all group shadow-sm"
          >
            <div className="font-bold text-emerald-400 text-xs flex items-center gap-2">
              <span>🟢</span> 1. Nominal State
            </div>
            <p className="text-[10px] text-slate-400 mt-1">
              Primary Active (ETH 1), all secondary links READY and healthy.
            </p>
          </button>

          {/* 2. Admin Probe Prompt */}
          <button
            type="button"
            onClick={() => {
              onSimulateAdminPrompt();
              onClose();
            }}
            className="p-3 rounded-xl bg-cyan-950/40 hover:bg-cyan-950/70 text-cyan-200 border border-cyan-700/70 text-left transition-all shadow-sm"
          >
            <div className="font-bold text-cyan-300 text-xs flex items-center gap-2">
              <span>🛡️</span> 2. Admin Evaluation
            </div>
            <p className="text-[10px] text-cyan-300/70 mt-1">
              Disabled link detected healthy. Triggers confirmation bubble.
            </p>
          </button>

          {/* 3. Jitter Degradation */}
          <button
            type="button"
            onClick={() => {
              onSimulateJitterDegradation();
              onClose();
            }}
            className="p-3 rounded-xl bg-amber-950/40 hover:bg-amber-950/70 text-amber-200 border border-amber-700/70 text-left transition-all shadow-sm"
          >
            <div className="font-bold text-amber-400 text-xs flex items-center gap-2">
              <span>⚠️</span> 3. Jitter Degradation
            </div>
            <p className="text-[10px] text-amber-300/70 mt-1">
              Active link jitter spikes. Anti-flap margin handover to candidate.
            </p>
          </button>

          {/* 4. Hard Interface Disconnect */}
          <button
            type="button"
            onClick={() => {
              onSimulateInterfaceDisconnect();
              onClose();
            }}
            className="p-3 rounded-xl bg-rose-950/40 hover:bg-rose-950/70 text-rose-200 border border-rose-700/70 text-left transition-all shadow-sm"
          >
            <div className="font-bold text-rose-400 text-xs flex items-center gap-2">
              <span>⚡</span> 4. Interface Disconnect
            </div>
            <p className="text-[10px] text-rose-300/70 mt-1">
              Hard carrier down / link cut. Immediate sub-second failover.
            </p>
          </button>

          {/* 5. Hotplug USB-C Docking Station */}
          {onSimulateHotplugDocking && (
            <button
              type="button"
              onClick={() => {
                onSimulateHotplugDocking();
                onClose();
              }}
              className="p-3 rounded-xl bg-sky-950/40 hover:bg-sky-950/70 text-sky-200 border border-sky-700/70 text-left transition-all shadow-sm sm:col-span-2"
            >
              <div className="font-bold text-sky-400 text-xs flex items-center gap-2">
                <span>🔌</span> 5. Hotplug USB-C Docking Station
              </div>
              <p className="text-[10px] text-sky-300/70 mt-1">
                Dynamic topology detection: triggers non-blocking new device
                notification banner.
              </p>
            </button>
          )}
        </div>

        {/* Footer info note */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-800/60 text-[10px] text-slate-500">
          <span>Decoupled UI & Native Core IPC Execution</span>
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
