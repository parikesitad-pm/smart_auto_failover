import React from 'react';
import {
  Monitor,
  Cpu,
  Activity,
  ShieldCheck,
  Download,
  ExternalLink,
} from 'lucide-react';

import { ResolvedRelease } from '../../types/releases';

interface DesktopShowcaseProps {
  onScrollToDownloads: () => void;
  release?: ResolvedRelease | null;
}

export const DesktopShowcase: React.FC<DesktopShowcaseProps> = ({
  onScrollToDownloads,
  release,
}) => {
  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-slate-800/80">
      <div className="text-center max-w-3xl mx-auto mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold tracking-wider uppercase mb-4">
          <Monitor className="w-3.5 h-3.5" />
          Native Desktop Application
        </div>
        <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white mb-4">
          AutoFailover 3.0 Desktop: <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
            Real-Time Network Visibility
          </span>
        </h2>
        <p className="text-slate-400 text-base sm:text-lg leading-relaxed">
          Inspired by automotive digital instrument clusters. Real-time RFC 3550
          jitter readouts, dynamic multi-factor network health scoring, and
          failover arbitration without dashboard clutter.
        </p>
      </div>

      {/* Desktop Screenshot Presentation Frame */}
      <div className="relative rounded-2xl p-2 sm:p-4 bg-gradient-to-b from-[#121c2d] to-[#080b10] border border-slate-700/80 shadow-[0_0_60px_rgba(16,185,129,0.15)] mb-12 overflow-hidden group">
        {/* Ambient Top Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-24 bg-emerald-500/15 blur-3xl pointer-events-none" />

        {/* Mockup Window Title Bar */}
        <div className="flex items-center justify-between px-4 py-2.5 bg-[#05070a]/80 border-b border-slate-800 rounded-t-xl select-none">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-rose-500/80" />
            <span className="w-3 h-3 rounded-full bg-amber-500/80" />
            <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
            <span className="ml-3 text-xs font-mono text-slate-400">
              AutoFailover 3.0 by Modula
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            ONLINE • 5Hz TELEMETRY
          </div>
        </div>

        {/* Real App Screenshot */}
        <div className="relative overflow-hidden rounded-b-xl bg-[#080b10]">
          <img
            src="/dashboard_app.png"
            alt="AutoFailover 3.0 Desktop Digital Network Cockpit"
            className="w-full h-auto object-cover rounded-b-xl shadow-2xl transition-transform duration-700 group-hover:scale-[1.01]"
          />
        </div>
      </div>

      {/* Feature Highlights Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-4">
            <Activity className="w-5 h-5" />
          </div>
          <h3 className="text-white font-bold text-base mb-2">
            RFC 3550 Real-Time Jitter
          </h3>
          <p className="text-slate-400 text-sm leading-relaxed">
            Continuous packet inter-arrival jitter evaluation calculated
            directly according to RFC 3550, detecting subtle connection
            degradation before total packet drop.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mb-4">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="text-white font-bold text-base mb-2">
            Anti-Flap Policy Engine
          </h3>
          <p className="text-slate-400 text-sm leading-relaxed">
            Hysteresis scoring margin prevents erratic flip-flopping between
            Ethernet and Wi-Fi, keeping critical Zoom, Teams, and OBS sessions
            steady.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all">
          <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400 mb-4">
            <Cpu className="w-5 h-5" />
          </div>
          <h3 className="text-white font-bold text-base mb-2">
            Decoupled Architecture
          </h3>
          <p className="text-slate-400 text-sm leading-relaxed">
            Core network failover engine runs independently in background
            threads. Device CPU/RAM telemetry is strictly separated from network
            path decisions.
          </p>
        </div>
      </div>

      {/* CTA Row */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
        <button
          onClick={onScrollToDownloads}
          className="w-full sm:w-auto px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm shadow-[0_0_25px_rgba(16,185,129,0.35)] transition-all flex items-center justify-center gap-2 cursor-pointer"
        >
          <Download className="w-4 h-4" />
          Download AutoFailover Desktop App{' '}
          {release ? `(${release.tagName})` : ''}
        </button>

        <a
          href="https://github.com/parikesitad-pm/smart_auto_failover"
          target="_blank"
          rel="noopener noreferrer"
          className="w-full sm:w-auto px-6 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 hover:text-white font-semibold text-sm transition-all flex items-center justify-center gap-2 cursor-pointer"
        >
          <ExternalLink className="w-4 h-4 text-cyan-400" />
          View Source on GitHub
        </a>
      </div>
    </section>
  );
};
