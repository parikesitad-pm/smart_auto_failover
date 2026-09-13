import React from 'react';
import { Activity, Cpu, Sliders, Shield, Zap } from 'lucide-react';

export const FeaturePillars: React.FC = () => {
  const pillars = [
    {
      icon: Activity,
      title: 'RFC 3550 Jitter Smoothing',
      formula: 'J = J + (|D| - J) / 16',
      description:
        'Eliminates knee-jerk switching on isolated ping spikes. Continuous statistical inter-arrival variance estimation tracks true path stability.',
      accent: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10',
    },
    {
      icon: Sliders,
      title: '0–100 Multi-Factor Health Index',
      formula: 'H = 0.35(L) + 0.35(J) + 0.30(P)',
      description:
        'Composite scoring weighted for interactive real-time streams: 35% Latency, 35% RFC 3550 Jitter, 30% Packet Loss.',
      accent: 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10',
    },
    {
      icon: Shield,
      title: 'Takeover Margin & Anti-Flap Arbiter',
      formula: 'Candidate >= Active + Margin (15 pts)',
      description:
        'Prevents destructive oscillation between interfaces. A recovering path enters READY first, absorbing transient noise before any switch is permitted.',
      accent: 'text-amber-400 border-amber-500/30 bg-amber-500/10',
    },
    {
      icon: Zap,
      title: 'Workload-Aware Protection',
      formula: 'Passive Process Detection',
      description:
        'Dynamically adapts health thresholds when Zoom, OBS Studio, vMix, Microsoft Teams, or Google Meet are actively transmitting.',
      accent: 'text-teal-400 border-teal-500/30 bg-teal-500/10',
    },
    {
      icon: Cpu,
      title: 'Decoupled Hardware Telemetry',
      formula: 'Passive 1 Hz Host Sampling',
      description:
        'Device telemetry (CPU/RAM) is strictly decoupled from network routing. Host resource load never corrupts network failover policy decisions.',
      accent: 'text-indigo-400 border-indigo-500/30 bg-indigo-500/10',
    },
  ];

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-slate-800/80">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
          Engineered for Zero Disruption
        </h2>
        <p className="text-slate-400 text-base sm:text-lg">
          Five core algorithmic innovations ensuring seamless internet pipeline failover.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {pillars.map((pillar, idx) => {
          const IconComponent = pillar.icon;
          return (
            <div
              key={idx}
              className="p-6 rounded-2xl bg-gradient-to-b from-[#0d131f] to-[#080b10] border border-slate-800 hover:border-slate-700 transition-all shadow-lg flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-3 rounded-xl border ${pillar.accent}`}>
                    <IconComponent className="w-6 h-6" />
                  </div>
                  <span className="text-xs font-mono text-slate-500">0{idx + 1}</span>
                </div>

                <h3 className="text-xl font-bold text-white mb-2">{pillar.title}</h3>
                <div className="inline-block px-2.5 py-1 rounded bg-black/40 text-[11px] font-mono text-emerald-400 border border-slate-800 mb-4">
                  {pillar.formula}
                </div>
                <p className="text-sm text-slate-400 leading-relaxed">{pillar.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
