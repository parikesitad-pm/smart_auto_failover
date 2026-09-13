import React from 'react';
import { Search, BarChart3, Shuffle, ArrowRightLeft } from 'lucide-react';

export const HowItWorks: React.FC = () => {
  const steps = [
    {
      icon: Search,
      num: '01',
      title: 'Continuous Interface Discovery',
      description: 'AutoFailover constantly polls network interfaces and OS carrier signals via native Netlink / sysfs.',
    },
    {
      icon: BarChart3,
      num: '02',
      title: 'High-Precision RFC 3550 Probing',
      description: 'Every 50ms–200ms, each eligible path is probed to compute moving statistical jitter and round-trip latency.',
    },
    {
      icon: Shuffle,
      num: '03',
      title: 'Anti-Flap Policy Scoring',
      description: 'The Policy Engine awards candidate scores. Promotion requires exceeding the active score by the 15-point takeover margin.',
    },
    {
      icon: ArrowRightLeft,
      num: '04',
      title: 'Atomic Route Switching',
      description: 'When failover triggers, the OS default routing metric is swapped in under 10ms with zero desktop UI stalling.',
    },
  ];

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-slate-800/80">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
          How It Works Under the Hood
        </h2>
        <p className="text-slate-400 text-base sm:text-lg">
          A 4-step real-time control loop running independently in the Python core.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          return (
            <div
              key={idx}
              className="p-6 rounded-2xl bg-gradient-to-b from-[#0e1626] to-[#080b10] border border-slate-800 relative group hover:border-slate-700 transition-all"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-2xl font-black font-mono text-emerald-400/40 group-hover:text-emerald-400 transition-colors">
                  {step.num}
                </span>
                <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-cyan-400">
                  <Icon className="w-5 h-5" />
                </div>
              </div>
              <h3 className="text-lg font-bold text-white mb-2">{step.title}</h3>
              <p className="text-xs text-slate-400 leading-relaxed">{step.description}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
};
