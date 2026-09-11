import React from 'react';
import { StartupSequenceState } from '../../hooks/useStartupSequence';
import { TuyulSportCar } from './TuyulSportCar';

export interface SplashScreenProps {
  state: StartupSequenceState;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ state }) => {
  if (!state.isActive) return null;

  return (
    <div
      id="splash-overlay"
      className="fixed inset-0 z-50 bg-[#05070a] flex flex-col items-center justify-center p-4 select-none transition-all duration-300"
    >
      {/* Carbon mesh background */}
      <div className="absolute inset-0 carbon-mesh opacity-40 pointer-events-none"></div>

      {/* Center Stage Card */}
      <div className="relative z-10 max-w-xl w-full flex flex-col items-center text-center">
        {/* Header Branding */}
        <div className="flex items-center space-x-2 mb-2">
          <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center text-cyan-400 shadow-md">
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
          <span className="font-mono text-xl font-bold tracking-tight text-white">
            AutoFailover 3.0{' '}
            <span className="text-xs font-normal text-slate-400">
              by Modula
            </span>
          </span>
        </div>
        <p className="text-[12px] font-mono text-cyan-400 tracking-wider mb-6 uppercase">
          "light seamless and usefull"
        </p>

        {/* TUYUL SPORT CAR ANIMATED STAGE */}
        <TuyulSportCar
          isReady={state.isReady}
          isDeparting={state.isDeparting}
        />

        {/* HONEST COMPLETION & TELEMETRY PROGRESS */}
        <div className="w-full bg-[#080c14] border border-slate-800 rounded-xl p-4 shadow-xl mb-4 text-left font-mono">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  state.isReady
                    ? 'bg-emerald-400 pulse-glow-emerald'
                    : 'bg-amber-400 animate-pulse'
                }`}
              ></span>
              <span
                className={`text-xs font-bold ${state.isReady ? 'text-emerald-400' : 'text-slate-200'}`}
              >
                {state.statusText}
              </span>
            </div>
            <span
              className={`text-xs font-bold ${state.isReady ? 'text-emerald-400' : 'text-cyan-400'}`}
            >
              {state.progress}%
            </span>
          </div>

          {/* Progress Bar Track */}
          <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden p-0.5 border border-slate-800">
            <div
              className={`h-full rounded-full transition-all duration-150 ${
                state.isReady
                  ? 'bg-emerald-500 shadow-[0_0_16px_rgba(16,185,129,0.9)]'
                  : 'bg-cyan-500 shadow-[0_0_12px_rgba(6,182,212,0.8)]'
              }`}
              style={{ width: `${state.progress}%` }}
            ></div>
          </div>

          {/* Decoupled Telemetry Readout */}
          <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-400">
            <div>
              Actual Core Init:{' '}
              <span className="text-white font-bold">
                {state.actualInitMs !== null
                  ? `${state.actualInitMs}ms ✓ Complete`
                  : 'Measuring...'}
              </span>
            </div>
            <div>
              Splash Min Duration:{' '}
              <span className="text-cyan-300 font-bold">
                {state.minDurationMs}ms
              </span>
            </div>
            <div>
              Remaining Window:{' '}
              <span className="text-slate-300 font-bold">
                {state.remainingMs}ms{' '}
                {state.isReady ? '(Playing Departure)' : ''}
              </span>
            </div>
          </div>
        </div>

        {/* Explanatory Note & Skip Tip */}
        <div className="flex flex-col items-center gap-1.5 text-[11px] text-slate-400 font-mono">
          <p className="text-slate-400">
            Controls minimum presentation duration. Does not affect network
            initialization.
          </p>
          <div className="flex items-center gap-2 mt-1 px-3 py-1 rounded-full bg-slate-900/80 border border-slate-800 text-[10px] text-slate-400">
            <kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700 text-slate-200 font-semibold shadow">
              Shift
            </kbd>
            <span>Hold Shift to skip startup presentation</span>
          </div>
        </div>
      </div>
    </div>
  );
};
