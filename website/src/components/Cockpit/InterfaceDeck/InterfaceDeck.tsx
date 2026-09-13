import React from 'react';
import { InterfaceDeckProps } from './InterfaceDeck.types';

export const InterfaceDeck: React.FC<InterfaceDeckProps> = ({
  adapters,
  activePath,
  onToggleAdapter,
  runtimeMode = 'native',
  isCoreReachable,
  isSimulationActive = false,
  onEnableSimulation,
  onDisableSimulation,
}) => {
  return (
    <section aria-label="Physical Network Interfaces" className="mt-2 mb-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-slate-400">
        <span className="font-bold text-slate-300 flex items-center gap-1.5">
          <span>Physical Interface Matrix</span>
          <span className="text-[10px] font-normal text-slate-500">
            {runtimeMode === 'browser_preview' && !isSimulationActive
              ? '(Native Core Required)'
              : isSimulationActive
                ? '(Deterministic Simulation)'
                : '(Dynamic Hotplug Detection)'}
          </span>
        </span>
        <span className="text-[10px] text-slate-500">
          {runtimeMode === 'browser_preview'
            ? 'Browser Environment'
            : 'Autonomous Carrier Scoring Engine'}
        </span>
      </div>

      {isSimulationActive && (
        <div className="mb-2.5 py-1.5 px-3 rounded-lg border border-amber-700/60 bg-amber-950/40 flex items-center justify-between text-xs font-mono text-amber-300">
          <div className="flex items-center gap-2">
            <span>⚠️</span>
            <span className="font-semibold">
              BROWSER SIMULATION ACTIVE — NOT REAL HARDWARE
            </span>
          </div>
          {onDisableSimulation && (
            <button
              type="button"
              onClick={onDisableSimulation}
              className="text-[11px] underline text-amber-200 hover:text-white transition-colors"
            >
              Exit Simulation
            </button>
          )}
        </div>
      )}

      {adapters.length === 0 ? (
        runtimeMode === 'browser_preview' || isCoreReachable === false ? (
          <div className="py-8 px-6 rounded-xl border border-amber-800/60 bg-amber-950/20 text-center font-mono shadow-inner">
            <div className="text-3xl mb-2">🌐</div>
            <p className="text-sm text-amber-300 font-bold tracking-wider uppercase">
              NATIVE CORE UNAVAILABLE
            </p>
            <p className="text-xs text-slate-200 mt-1 font-semibold">
              Browser Preview Mode
            </p>
            <p className="text-[11px] text-slate-400 mt-2 max-w-md mx-auto leading-relaxed">
              Real network interface discovery and kernel route manipulation
              require the AutoFailover desktop runtime (Tauri + Rust Core).
            </p>
            {onEnableSimulation && (
              <div className="mt-4 flex items-center justify-center gap-3">
                <button
                  type="button"
                  onClick={onEnableSimulation}
                  className="px-3.5 py-1.5 rounded-lg bg-amber-900/50 hover:bg-amber-800/80 text-amber-200 border border-amber-700/80 text-xs transition-colors shadow flex items-center gap-1.5"
                >
                  <span>🧪</span>
                  <span>Enable Deterministic Simulation</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="py-8 px-4 rounded-xl border border-slate-800/80 bg-slate-950/40 text-center font-mono">
            <div className="inline-block animate-spin text-cyan-400 mb-2">
              🔄
            </div>
            <p className="text-xs text-slate-300 font-bold">
              Scanning hardware topology...
            </p>
            <p className="text-[10px] text-slate-500 mt-0.5">
              Physical network interface detection in progress
            </p>
          </div>
        )
      ) : (
        <div
          className={`grid grid-cols-1 sm:grid-cols-2 ${
            adapters.length > 2 ? 'lg:grid-cols-4' : 'lg:grid-cols-2'
          } gap-2.5`}
        >
          {adapters.map((adapter) => {
            const isDisabled =
              !adapter.enabled ||
              adapter.state === 'DISABLED' ||
              adapter.adminState === 'disabled';
            const isOnline =
              !isDisabled &&
              adapter.id === activePath &&
              adapter.state === 'ONLINE';
            const isAlert = !isDisabled && adapter.state === 'ALERT';
            const isOffline =
              !isDisabled &&
              (adapter.state === 'OFFLINE' ||
                adapter.carrier === 'Disconnected' ||
                adapter.linkState === 'disconnected');

            let borderClass = 'border-slate-800 bg-slate-900/40';
            let statusBadgeClass =
              'bg-cyan-950 text-cyan-400 border border-cyan-800';
            let statusLabel: string = adapter.state;

            if (isDisabled) {
              borderClass = 'border-slate-800/60 bg-slate-950/40 opacity-70';
              statusBadgeClass =
                'bg-slate-900 text-slate-500 border border-slate-700';
              statusLabel = 'DISABLED';
            } else if (isOnline) {
              borderClass =
                'border-cyan-500/70 bg-cyan-950/20 shadow-lg shadow-cyan-950/40';
              statusBadgeClass =
                'bg-emerald-950 text-emerald-300 border border-emerald-500';
              statusLabel = 'ONLINE';
            } else if (isAlert) {
              borderClass = 'border-amber-500/70 bg-amber-950/20';
              statusBadgeClass =
                'bg-amber-950 text-amber-300 border border-amber-500';
              statusLabel = 'ALERT';
            } else if (isOffline) {
              borderClass = 'border-rose-900/60 bg-rose-950/30';
              statusBadgeClass =
                'bg-rose-950 text-rose-300 border border-rose-800';
              statusLabel = 'OFFLINE';
            } else {
              borderClass = 'border-slate-800 bg-slate-900/40';
              statusBadgeClass =
                'bg-cyan-950 text-cyan-400 border border-cyan-800';
              statusLabel = 'READY';
            }

            const isUsable = !isDisabled && !isOffline;
            const displayIp =
              isUsable && adapter.ipAddress && adapter.ipAddress !== 'N/A'
                ? adapter.ipAddress
                : '—';
            const displayGateway =
              isUsable && adapter.gateway && adapter.gateway !== 'N/A'
                ? adapter.gateway
                : '—';
            const displayNetmask =
              isUsable && adapter.netmask ? adapter.netmask : '—';
            const displayLinkSpeed =
              isUsable && adapter.linkSpeed && adapter.linkSpeed !== 'N/A'
                ? adapter.linkSpeed
                : '—';
            const displayLatency =
              isUsable && adapter.latency > 0
                ? `${adapter.latency.toFixed(1)} ms`
                : '—';
            const displayJitter =
              isUsable && adapter.jitter > 0
                ? `${adapter.jitter.toFixed(1)} ms`
                : '—';
            const displayScore = isUsable ? adapter.score.toFixed(1) : '—';
            const displaySsid =
              isUsable && adapter.mediaType === 'wifi'
                ? (adapter.ssid ?? '—')
                : null;

            return (
              <div
                key={adapter.id}
                className={`p-3 rounded-xl border transition-all flex flex-col justify-between ${borderClass}`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex flex-col">
                      <span className="text-xs font-bold font-mono text-slate-200">
                        {adapter.name}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">
                        ID: {adapter.id} • {adapter.mediaType.toUpperCase()}
                      </span>
                    </div>
                    <span
                      className={`text-[9px] font-bold px-2 py-0.5 rounded ${statusBadgeClass}`}
                    >
                      {statusLabel}
                    </span>
                  </div>

                  {/* Compact 2-column Network Parameter Grid */}
                  <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[10px] font-mono py-1.5 border-t border-slate-800/60 text-slate-400">
                    <div>
                      <span className="text-slate-500 block text-[9px] uppercase">
                        IPv4 Address
                      </span>
                      <span className="text-slate-300 font-semibold truncate block">
                        {displayIp}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[9px] uppercase">
                        Gateway
                      </span>
                      <span className="text-slate-300 truncate block">
                        {displayGateway}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[9px] uppercase">
                        Netmask
                      </span>
                      <span className="text-slate-300 truncate block">
                        {displayNetmask}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[9px] uppercase">
                        Link Speed
                      </span>
                      <span className="text-slate-300 truncate block">
                        {displayLinkSpeed}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[9px] uppercase">
                        Latency / Jitter
                      </span>
                      <span className="text-slate-300 truncate block">
                        {displayLatency} / {displayJitter}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[9px] uppercase">
                        {displaySsid !== null ? 'SSID / Score' : 'Health Score'}
                      </span>
                      <span className="text-cyan-400 font-bold truncate block">
                        {displaySsid !== null
                          ? `${displaySsid} (${displayScore})`
                          : displayScore}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Administrative hardware toggle */}
                <div className="pt-2 mt-2 border-t border-slate-800/80 flex items-center justify-between">
                  <span className="text-[10px] text-slate-500 font-mono">
                    Admin State:
                  </span>
                  <button
                    type="button"
                    onClick={() => onToggleAdapter(adapter.id)}
                    className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-bold transition-colors border ${
                      !isDisabled
                        ? 'bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 border-emerald-700/60'
                        : 'bg-slate-900 hover:bg-slate-800 text-slate-400 border-slate-700'
                    }`}
                  >
                    {!isDisabled ? 'ENABLED' : 'DISABLED'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
};
