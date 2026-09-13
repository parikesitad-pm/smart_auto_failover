import React from 'react';
import {
  Unplug,
  Plug,
  WifiOff,
  Wifi,
  Activity,
  CheckCircle2,
  RotateCcw,
} from 'lucide-react';

export interface DemoToolbarProps {
  onDisconnectEthernet: () => void;
  onReconnectEthernet: () => void;
  onDisableWifi: () => void;
  onEnableWifi: () => void;
  onDegradeConnection: () => void;
  onRecoverConnection: () => void;
  onResetDemo: () => void;
}

export const DemoToolbar: React.FC<DemoToolbarProps> = ({
  onDisconnectEthernet,
  onReconnectEthernet,
  onDisableWifi,
  onEnableWifi,
  onDegradeConnection,
  onRecoverConnection,
  onResetDemo,
}) => {
  return (
    <div className="my-3 p-3 rounded-xl border border-slate-800 bg-slate-950/70 font-mono shadow-lg">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2.5 pb-2 border-b border-slate-800/60 text-xs">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span className="font-bold text-slate-200 uppercase tracking-wider">
            Interactive Scenario Controller
          </span>
          <span className="text-[10px] text-slate-500 hidden sm:inline">
            • Test sub-second failover in real-time
          </span>
        </div>
        <button
          type="button"
          onClick={onResetDemo}
          className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 text-[11px] font-semibold transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer"
          title="Reset cockpit state to nominal dual-homed baseline"
        >
          <RotateCcw className="w-3 h-3 text-cyan-400" />
          <span>Reset Demo</span>
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
        {/* Disconnect Ethernet */}
        <button
          type="button"
          onClick={onDisconnectEthernet}
          className="px-2.5 py-2 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 border border-rose-800/60 hover:border-rose-600 text-rose-300 text-[11px] font-medium transition-all flex flex-col items-center justify-center gap-1 text-center shadow-sm cursor-pointer"
          title="Simulate sudden physical cable disconnect on primary Ethernet"
        >
          <Unplug className="w-4 h-4 text-rose-400 shrink-0" />
          <span className="leading-tight">Disconnect Ethernet</span>
        </button>

        {/* Reconnect Ethernet */}
        <button
          type="button"
          onClick={onReconnectEthernet}
          className="px-2.5 py-2 rounded-lg bg-emerald-950/40 hover:bg-emerald-900/60 border border-emerald-800/60 hover:border-emerald-600 text-emerald-300 text-[11px] font-medium transition-all flex flex-col items-center justify-center gap-1 text-center shadow-sm cursor-pointer"
          title="Restore physical cable link and verify anti-flap recovery"
        >
          <Plug className="w-4 h-4 text-emerald-400 shrink-0" />
          <span className="leading-tight">Reconnect Ethernet</span>
        </button>

        {/* Disable Wi-Fi */}
        <button
          type="button"
          onClick={onDisableWifi}
          className="px-2.5 py-2 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-700 hover:border-slate-600 text-slate-300 text-[11px] font-medium transition-all flex flex-col items-center justify-center gap-1 text-center shadow-sm cursor-pointer"
          title="Administratively disable Wi-Fi adapter"
        >
          <WifiOff className="w-4 h-4 text-slate-400 shrink-0" />
          <span className="leading-tight">Disable Wi-Fi</span>
        </button>

        {/* Enable Wi-Fi */}
        <button
          type="button"
          onClick={onEnableWifi}
          className="px-2.5 py-2 rounded-lg bg-cyan-950/40 hover:bg-cyan-900/60 border border-cyan-800/60 hover:border-cyan-600 text-cyan-300 text-[11px] font-medium transition-all flex flex-col items-center justify-center gap-1 text-center shadow-sm cursor-pointer"
          title="Administratively re-enable Wi-Fi standby path"
        >
          <Wifi className="w-4 h-4 text-cyan-400 shrink-0" />
          <span className="leading-tight">Enable Wi-Fi</span>
        </button>

        {/* Degrade Connection */}
        <button
          type="button"
          onClick={onDegradeConnection}
          className="px-2.5 py-2 rounded-lg bg-amber-950/40 hover:bg-amber-900/60 border border-amber-800/60 hover:border-amber-600 text-amber-300 text-[11px] font-medium transition-all flex flex-col items-center justify-center gap-1 text-center shadow-sm cursor-pointer"
          title="Simulate jitter spike (RFC 3550) triggering pre-emptive failover"
        >
          <Activity className="w-4 h-4 text-amber-400 shrink-0" />
          <span className="leading-tight">Degrade Connection</span>
        </button>

        {/* Recover Connection */}
        <button
          type="button"
          onClick={onRecoverConnection}
          className="px-2.5 py-2 rounded-lg bg-emerald-950/40 hover:bg-emerald-900/60 border border-emerald-800/60 hover:border-emerald-600 text-emerald-300 text-[11px] font-medium transition-all flex flex-col items-center justify-center gap-1 text-center shadow-sm cursor-pointer"
          title="Clear packet loss and restore pristine gigabit metrics"
        >
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span className="leading-tight">Recover Connection</span>
        </button>
      </div>
    </div>
  );
};
