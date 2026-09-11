import React from 'react';
import { StartupConfig, StartupPreset } from '../../types/cockpit.types';

export interface SplashSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: StartupConfig;
  onSetPreset: (preset: StartupPreset, ms: number) => void;
  onSetCustomDuration: (ms: number) => void;
  onSetEngineSpeed: (ms: number) => void;
  onSetSkipEnabled: (skip: boolean) => void;
  onReplay: () => void;
}

export const SplashSettingsModal: React.FC<SplashSettingsModalProps> = ({
  isOpen,
  onClose,
  config,
  onSetPreset,
  onSetCustomDuration,
  onSetEngineSpeed,
  onSetSkipEnabled,
  onReplay,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#080c14] border border-slate-800 rounded-2xl max-w-md w-full p-5 shadow-2xl font-mono text-left relative">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <span className="text-base">⏱️</span>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Startup Presentation & Delay Engine
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-base"
          >
            ✕
          </button>
        </div>

        <div className="py-4 space-y-4 text-xs">
          {/* Presets */}
          <div>
            <label className="text-slate-400 block mb-2 text-[11px] font-bold uppercase tracking-wider">
              Presentation Presets
            </label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => onSetPreset('fast', 1500)}
                className={`px-3 py-1.5 rounded-lg border text-xs font-mono transition-all ${
                  config.preset === 'fast'
                    ? 'bg-cyan-950 border-cyan-500 text-cyan-300 shadow-md font-bold'
                    : 'bg-slate-900 border-slate-700 text-slate-300'
                }`}
              >
                Fast
                <br />
                <span className="text-[10px] text-slate-400">1500 ms</span>
              </button>
              <button
                type="button"
                onClick={() => onSetPreset('normal', 3000)}
                className={`px-3 py-1.5 rounded-lg border text-xs font-mono transition-all ${
                  config.preset === 'normal'
                    ? 'bg-cyan-950 border-cyan-500 text-cyan-300 shadow-md font-bold'
                    : 'bg-slate-900 border-slate-700 text-slate-300'
                }`}
              >
                Normal
                <br />
                <span className="text-[10px] text-cyan-400">3000 ms</span>
              </button>
              <button
                type="button"
                onClick={() => onSetPreset('cinematic', 5000)}
                className={`px-3 py-1.5 rounded-lg border text-xs font-mono transition-all ${
                  config.preset === 'cinematic'
                    ? 'bg-cyan-950 border-cyan-500 text-cyan-300 shadow-md font-bold'
                    : 'bg-slate-900 border-slate-700 text-slate-300'
                }`}
              >
                Cinematic
                <br />
                <span className="text-[10px] text-slate-400">5000 ms</span>
              </button>
            </div>
          </div>

          {/* Custom Slider */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-slate-400 text-[11px] font-bold uppercase tracking-wider">
                Custom Delay Window
              </label>
              <span className="text-cyan-300 font-bold">
                {config.splashMinDurationMs} ms
              </span>
            </div>
            <input
              type="range"
              min="1000"
              max="10000"
              step="250"
              value={config.splashMinDurationMs}
              onChange={(e) =>
                onSetCustomDuration(parseInt(e.target.value, 10))
              }
              className="w-full accent-cyan-400 bg-slate-900 rounded-lg cursor-pointer"
            />
            <div className="flex justify-between text-[9px] text-slate-400 mt-1">
              <span>1000 ms (1s)</span>
              <span>10000 ms (10s)</span>
            </div>
          </div>

          {/* Simulated Engine Speed */}
          <div>
            <label className="text-slate-400 block mb-2 text-[11px] font-bold uppercase tracking-wider">
              Simulated Network Engine Speed
            </label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => onSetEngineSpeed(280)}
                className={`px-2.5 py-1 rounded border text-[11px] font-mono transition-all ${
                  config.simulatedEngineInitMs === 280
                    ? 'bg-cyan-950 border-cyan-500 text-cyan-300 font-bold'
                    : 'bg-slate-900 border-slate-700 text-slate-400'
                }`}
              >
                100 Gbps
                <br />
                <span className="text-[9px] text-slate-400">280 ms init</span>
              </button>
              <button
                type="button"
                onClick={() => onSetEngineSpeed(450)}
                className={`px-2.5 py-1 rounded border text-[11px] font-mono transition-all ${
                  config.simulatedEngineInitMs === 450
                    ? 'bg-cyan-950 border-cyan-500 text-cyan-300 font-bold'
                    : 'bg-slate-900 border-slate-700 text-slate-400'
                }`}
              >
                Fast Fiber
                <br />
                <span className="text-[9px] text-cyan-400">450 ms init</span>
              </button>
              <button
                type="button"
                onClick={() => onSetEngineSpeed(1400)}
                className={`px-2.5 py-1 rounded border text-[11px] font-mono transition-all ${
                  config.simulatedEngineInitMs === 1400
                    ? 'bg-cyan-950 border-cyan-500 text-cyan-300 font-bold'
                    : 'bg-slate-900 border-slate-700 text-slate-400'
                }`}
              >
                High Latency
                <br />
                <span className="text-[9px] text-slate-400">1400 ms init</span>
              </button>
            </div>
          </div>

          {/* Skip Setting */}
          <div className="flex items-center space-x-2 pt-2 border-t border-slate-800">
            <input
              type="checkbox"
              id="skip-checkbox-modal"
              checked={config.skipEnabled}
              onChange={(e) => onSetSkipEnabled(e.target.checked)}
              className="accent-cyan-400 rounded"
            />
            <label
              htmlFor="skip-checkbox-modal"
              className="text-slate-300 cursor-pointer select-none"
            >
              Skip startup presentation (Default: OFF)
            </label>
          </div>

          {/* Clarification Note */}
          <div className="p-2.5 rounded-lg bg-cyan-950/30 border border-cyan-800/40 text-[10px] text-cyan-200/80 leading-relaxed">
            💡 <strong>Note:</strong> Controls minimum presentation display
            time. Does not affect network initialization. Engine always
            initializes at maximum hardware speed.
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-800">
          <button
            type="button"
            onClick={onClose}
            className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono transition-colors"
          >
            Close
          </button>
          <button
            type="button"
            onClick={() => {
              onClose();
              onReplay();
            }}
            className="px-4 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/30 flex items-center gap-1.5 font-mono transition-all"
          >
            <span>🚀</span>
            <span>Launch Presentation</span>
          </button>
        </div>
      </div>
    </div>
  );
};
