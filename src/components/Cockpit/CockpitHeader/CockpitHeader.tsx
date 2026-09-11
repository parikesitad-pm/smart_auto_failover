import React, { useState } from 'react';
import { CockpitHeaderProps } from './CockpitHeader.types';

export const CockpitHeader: React.FC<CockpitHeaderProps> = ({
  activePathName,
  workloadProfile,
  onWorkloadChange,
  onForceReinit,
  onOpenStartupModal,
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
        <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center text-cyan-400 shadow-lg">
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-base font-bold tracking-tight text-white font-mono">
              AutoFailover 3.0{' '}
              <span className="text-xs font-normal text-slate-400">
                by Modula
              </span>
            </h1>
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-cyan-950 text-cyan-400 border border-cyan-800/50">
              React + TS • Rust Engine
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans tracking-wide italic">
            "light seamless and usefull"
          </p>
        </div>
      </div>

      {/* Workload Profile Selector */}
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

      {/* Action Buttons & Master Status Pill */}
      <div className="flex items-center space-x-2">
        {/* Manual Force Re-initialization Button */}
        <button
          type="button"
          onClick={handleReinitClick}
          className="px-3 py-1.5 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-emerald-300 text-xs font-mono border border-slate-700/80 flex items-center gap-1.5 transition-all shadow-sm group"
          title="Force manual Core re-initialization and hardware probe cycle (without startup presentation)"
        >
          <span
            className={`inline-block transition-transform duration-300 ${isReinitSpinning ? 'animate-spin' : ''}`}
          >
            🔄
          </span>
          <span>Re-initialize Core</span>
        </button>

        {/* Startup Presentation Modal Trigger */}
        <button
          type="button"
          onClick={onOpenStartupModal}
          className="px-3 py-1.5 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 text-xs font-mono border border-slate-700/80 flex items-center gap-1.5 transition-all shadow-sm"
          title="Configure minimum presentation duration and replay startup"
        >
          <span>⏱️</span>
          <span>Startup Presentation</span>
        </button>

        {/* Master Status Pill */}
        <div className="flex items-center space-x-2 bg-emerald-950/60 border border-emerald-700/50 px-3 py-1.5 rounded-full transition-all duration-300">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 pulse-glow-emerald"></span>
          <span className="text-xs font-semibold tracking-wider font-mono text-emerald-300">
            ONLINE • {activePathName.toUpperCase()} PRIMARY
          </span>
        </div>
      </div>
    </header>
  );
};
