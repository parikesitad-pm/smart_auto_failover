import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';

export const FaqAccordion: React.FC = () => {
  const faqs = [
    {
      q: 'Does AutoFailover require root or administrator privileges?',
      a: 'Interface monitoring, RFC 3550 jitter probing, and health calculations run with regular user privileges. Only Layer-3 default route switching and administrative interface toggles require standard OS network elevation (sudo on Linux, UAC on Windows).',
    },
    {
      q: 'Does AutoFailover bond multiple internet connections?',
      a: 'No. AutoFailover is an intelligent, low-latency automatic failover router, not a channel bonding solution. Channel bonding requires external VPS aggregation and introduces higher base latency and packet reordering overhead.',
    },
    {
      q: 'How does it protect Zoom and OBS Studio specifically?',
      a: 'AutoFailover runs a passive workload detector. When interactive meeting or streaming applications are running, failover arbitration enters high-continuity mode: micro-jitter thresholds are monitored aggressively to fail over before the application buffer runs dry.',
    },
    {
      q: 'Why not switch immediately when another interface has 2ms lower ping?',
      a: 'Switching paths forces connection re-establishment and momentary jitter. Under the AutoFailover Takeover Margin rule, a candidate interface must outperform the active interface by at least 15 health points to justify a transition.',
    },
    {
      q: 'Is the desktop application dependent on web technologies?',
      a: 'The desktop application is built purely in Python with CustomTkinter and native OS networking APIs. The web surface is for marketing, documentation, and the live interactive browser simulator.',
    },
  ];

  const [openIdx, setOpenIdx] = useState<number | null>(null);

  const toggle = (idx: number) => {
    setOpenIdx(openIdx === idx ? null : idx);
  };

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto border-t border-slate-800/80">
      <div className="text-center mb-16">
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
          Frequently Asked Questions
        </h2>
        <p className="text-slate-400 text-base sm:text-lg">
          Answers to common questions about routing, continuity, and system architecture.
        </p>
      </div>

      <div className="space-y-4">
        {faqs.map((faq, idx) => {
          const isOpen = openIdx === idx;
          return (
            <div
              key={idx}
              className="rounded-2xl bg-[#0c1320] border border-slate-800 overflow-hidden transition-colors"
            >
              <button
                onClick={() => toggle(idx)}
                className="w-full py-5 px-6 text-left flex items-center justify-between gap-4 cursor-pointer hover:text-emerald-400 transition-colors"
              >
                <span className="font-semibold text-white text-base sm:text-lg">
                  {faq.q}
                </span>
                <ChevronDown
                  className={`w-5 h-5 text-slate-400 shrink-0 transition-transform duration-200 ${
                    isOpen ? 'rotate-180 text-emerald-400' : ''
                  }`}
                />
              </button>
              {isOpen && (
                <div className="px-6 pb-5 pt-0 text-sm text-slate-400 leading-relaxed border-t border-slate-800/60 mt-1">
                  <div className="pt-3">{faq.a}</div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
};
