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
            (Dynamic Hotplug Detection)
          </span>
        </span>
        <span className="text-[10px] text-slate-500">
          Autonomous Carrier Scoring Engine
        </span>
      </div>

      {adapters.length === 0 ? (
        <div className="py-8 px-4 rounded-xl border border-slate-800/80 bg-slate-950/40 text-center font-mono">
          <div className="inline-block animate-spin text-cyan-400 mb-2">🔄</div>
          <p className="text-xs text-slate-300 font-bold">
            Scanning hardware topology...
          </p>
          <p className="text-[10px] text-slate-500 mt-0.5">
            Physical network interface detection in progress
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

            return (
              <div
                key={adapter.id}
                className={`p-3 rounded-xl border transition-all flex flex-col justify-between ${borderClass}`}
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold font-mono text-slate-300 flex items-center gap-1">
                      {adapter.name}
                    </span>
                    <span
                      className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${statusBadgeClass}`}
                    >
                      {statusLabel}
                    </span>
                  </div>

                  <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between mb-1">
                    <span>
                      {isDisabled || isOffline
                        ? '-- ms'
                        : `${adapter.latency} ms`}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      Score{' '}
                      {isDisabled || isOffline
                        ? '--'
                        : adapter.score.toFixed(1)}
                    </span>
                  </div>
                  <div className="text-[9px] text-slate-500 font-mono">
                    Carrier: {isDisabled ? 'Disabled' : adapter.carrier}
                  </div>
                </div>

                {/* Administrative hardware toggle */}
                <div className="pt-2 mt-2 border-t border-slate-800/80 flex items-center justify-between">
                  <span className="text-[10px] text-slate-400">
                    Administrative:
                  </span>
                  <button
                    type="button"
                    onClick={() => onToggleAdapter(adapter.id)}
                    className={`px-2 py-0.5 rounded text-[10px] font-mono transition-colors border ${
                      !isDisabled
                        ? 'bg-emerald-900/60 hover:bg-emerald-800 text-emerald-200 border-emerald-700/60'
                        : 'bg-slate-800 hover:bg-slate-700 text-slate-400 border-slate-700'
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
