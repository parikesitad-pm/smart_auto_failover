import React from 'react';
import { AdminConfirmationBubbleProps } from './AdminConfirmationBubble.types';

export const AdminConfirmationBubble: React.FC<
  AdminConfirmationBubbleProps
> = ({ targetInterfaceId, onAction }) => {
  if (!targetInterfaceId) return null;

  return (
    <div
      role="alert"
      className="my-2.5 p-3.5 rounded-xl border border-cyan-500/80 bg-gradient-to-r from-cyan-950/95 via-slate-900/95 to-blue-950/95 shadow-2xl shadow-cyan-950/60 flex flex-wrap items-center justify-between gap-3 text-xs font-mono bubble-anim"
    >
      <div className="flex items-start space-x-3">
        <div className="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300 text-base shrink-0 mt-0.5">
          🛡️
        </div>
        <div>
          <div className="font-bold text-cyan-200 flex items-center gap-2">
            <span>
              Ethernet 1 is disabled but appears healthy. Enable it for
              automatic failover?
            </span>
          </div>
          <div className="text-[11px] text-slate-300 mt-1 leading-relaxed">
            Background socket probe confirms healthy carrier:{' '}
            <strong>8.2ms latency, 1.2ms jitter, score 98.4</strong>. Enabling
            allows the Policy Engine to evaluate it as an eligible standby
            candidate.
          </div>
        </div>
      </div>
      <div className="flex items-center space-x-2 shrink-0">
        <button
          type="button"
          onClick={() => onAction(true)}
          className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-md shadow-cyan-500/30 flex items-center gap-1.5 transition-all"
        >
          <span>Enable</span>
        </button>
        <button
          type="button"
          onClick={() => onAction(false)}
          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition-colors"
        >
          Keep Disabled
        </button>
      </div>
    </div>
  );
};
