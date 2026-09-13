import React, { useState } from 'react';
import { CockpitHeaderProps } from './CockpitHeader.types';
import { DeviceHealthBar } from '../DeviceHealthBar';

export const CockpitHeader: React.FC<CockpitHeaderProps> = ({
  activePathName,
  workloadProfile,
  deviceHealth,
  onWorkloadChange,
  onForceReinit,
  onOpenStartupModal,
  onOpenDiagnostics,
}) => {
  const [isReinitSpinning, setIsReinitSpinning] = useState(false);

  const handleReinitClick = () => {
    setIsReinitSpinning(true);
    onForceReinit();
    setTimeout(() => setIsReinitSpinning(false), 500);
  };

  return (
    <header className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800/60">
      {/* Brand & Subtitle */}
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-lg bg-slate-900 border border-slate-700/80 p-1 flex items-center justify-center shadow-lg">
          <img
            src="/modula_3.0.png"
            alt="Modula 3.0 Logo"
            className="w-full h-full object-contain drop-shadow-[0_0_8px_rgba(16,185,129,0.35)]"
          />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-base font-bold tracking-tight text-white font-mono">
              AutoFailover 3.0{' '}
              <span className="text-xs font-normal text-slate-400">
                by Modula
              </span>
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <p className="text-[11px] text-slate-300 font-sans tracking-tight">
              Navigate Your Internet Pipeline to Keep You Online
            </p>
            <span className="text-slate-600 text-[10px]">•</span>
            <p className="text-[10px] text-cyan-400/90 font-mono italic">
              "light seamless and usefull"
            </p>
          </div>
        </div>
      </div>

      {/* Center Zone: Workload Profile & Compact Device Health Strip */}
      <div className="flex flex-wrap items-center gap-2.5">
        <div className="flex items-center space-x-1.5 bg-slate-900/90 border border-slate-800 px-2 py-1 rounded-xl text-xs font-mono">
          <span className="text-[10px] text-slate-500 uppercase tracking-wider pr-1">
            Workload:
          </span>
          <button
            type="button"
            onClick={() => onWorkloadChange('conference')}
            className={`px-2 py-0.5 rounded text-[11px] transition-colors ${
              workloadProfile === 'conference'
                ? 'bg-cyan-950 text-cyan-300 border border-cyan-700/80 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            📹 Conferencing
          </button>
          <button
            type="button"
            onClick={() => onWorkloadChange('broadcast')}
            className={`px-2 py-0.5 rounded text-[11px] transition-colors ${
              workloadProfile === 'broadcast'
                ? 'bg-cyan-950 text-cyan-300 border border-cyan-700/80 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            🎙️ Live Production
          </button>
        </div>

        {/* Compact Device Health (CPU, RAM, GPU) */}
        <DeviceHealthBar deviceHealth={deviceHealth} />
      </div>

      {/* Action Buttons & Master Status Pill */}
      <div className="flex items-center space-x-2">
        {/* Manual Force Re-initialization Button */}
        <button
          type="button"
          onClick={handleReinitClick}
          className="px-3 py-1.5 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-emerald-300 text-xs font-mono border border-slate-700/80 flex items-center gap-1.5 transition-all shadow-sm group cursor-pointer"
          title="Force manual probe cycle and re-evaluate link quality scores"
        >
          <span
            className={`inline-block transition-transform duration-300 ${isReinitSpinning ? 'animate-spin' : ''}`}
          >
            🔄
          </span>
          <span>Re-evaluate Links</span>
        </button>

        {/* Startup Presentation Modal Trigger */}
        <button
          type="button"
          onClick={onOpenStartupModal}
          className="px-3 py-1.5 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 text-xs font-mono border border-slate-700/80 flex items-center gap-1.5 transition-all shadow-sm cursor-pointer"
          title="Configure minimum presentation duration and replay startup"
        >
          <span>⏱️</span>
          <span>Startup Presentation</span>
        </button>

        {/* Diagnostics & Simulation Trigger */}
        <button
          type="button"
          onClick={onOpenDiagnostics}
          className="px-3 py-1.5 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-amber-300 text-xs font-mono border border-slate-700/80 flex items-center gap-1.5 transition-all shadow-sm cursor-pointer"
          title="Open Policy Engine Diagnostics & Simulation modal (Shift+D)"
        >
          <span>🧪</span>
          <span>Diagnostics</span>
        </button>

        {/* Interactive Demo Mode Badge */}
        <div
          className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono border bg-cyan-950/40 border-cyan-700/60 text-cyan-300"
          title="Interactive Deterministic Simulator"
        >
          <span>🧪</span>
          <span className="font-semibold uppercase tracking-wider">
            INTERACTIVE DEMO
          </span>
        </div>

        {/* Master Status Pill */}
        {activePathName &&
        activePathName !== 'NONE' &&
        activePathName !== 'none' ? (
          <div className="flex items-center space-x-2 bg-emerald-950/60 border border-emerald-700/50 px-3 py-1.5 rounded-full transition-all duration-300">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 pulse-glow-emerald"></span>
            <span className="text-xs font-semibold tracking-wider font-mono text-emerald-300">
              ONLINE • {activePathName.toUpperCase()}
            </span>
          </div>
        ) : (
          <div className="flex items-center space-x-2 bg-rose-950/60 border border-rose-700/50 px-3 py-1.5 rounded-full transition-all duration-300">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></span>
            <span className="text-xs font-semibold tracking-wider font-mono text-rose-300">
              OFFLINE • NO ACTIVE PATH
            </span>
          </div>
        )}
      </div>
    </header>
  );
};
