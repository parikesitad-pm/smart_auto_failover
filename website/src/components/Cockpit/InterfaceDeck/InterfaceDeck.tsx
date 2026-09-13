import React from 'react';
import { InterfaceDeckProps } from './InterfaceDeck.types';

export const InterfaceDeck: React.FC<InterfaceDeckProps> = ({
  adapters,
  activePath,
  onToggleAdapter,
}) => {
  return (
    <section aria-label="Physical Network Interfaces" className="mt-2 mb-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-slate-400">
        <span className="font-bold text-slate-300 flex items-center gap-1.5">
          <span>Physical Interface Matrix</span>
          <span className="text-[10px] font-normal text-slate-500">
            (Multi-Path Active / Standby Routing)
          </span>
        </span>
        <span className="text-[10px] text-cyan-400/80">
          Carrier Scoring Engine • Sub-second Failover
        </span>
      </div>

      {adapters.length === 0 ? (
        <div className="py-8 px-6 rounded-xl border border-slate-800 bg-slate-950/60 text-center font-mono">
          <p className="text-xs text-slate-300 font-bold">
            No active network interfaces
          </p>
          <p className="text-[11px] text-slate-500 mt-1">
            Click 'Reset Demo' or 'Reconnect Ethernet' above to restore adapter
            links.
          </p>
        </div>
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
