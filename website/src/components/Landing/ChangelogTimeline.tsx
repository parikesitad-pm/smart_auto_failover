import React, { useState } from 'react';
import {
  GitCommit,
  ExternalLink,
  Tag,
  Wrench,
  ShieldCheck,
  PlusCircle,
} from 'lucide-react';


interface ChangelogRelease {
  version: string;
  tag: string;
  date: string;
  channel: 'STABLE' | 'BETA' | 'LEGACY';
  highlights: string;
  added?: string[];
  changed?: string[];
  fixed?: string[];
}

export const ChangelogTimeline: React.FC = () => {
  const [filterChannel, setFilterChannel] = useState<'ALL' | 'STABLE' | 'BETA' | 'LEGACY'>('ALL');

  const releases: ChangelogRelease[] = [
    {
      version: '3.1.0',
      tag: 'v3.1.0',
      date: 'September 14, 2026',
      channel: 'STABLE',
      highlights:
        'Audited Network Interface Deck with 4-stage presentation pipeline, dynamic card order retention, Zoom/vMix stability guarantee, multi-version download hub, and enterprise developer documentation.',
      added: [
        'Strict 4-stage interface presentation pipeline (Core Registry → Visibility Filter → Sort Visible Only → Dynamic Render) ensuring disconnected Ethernet cables never reappear from sorting.',
        'Multi-version download selector and historical releases matrix (v3.1.0 down to v3.0.0-preview.24) with multi-platform packages.',
        'Comprehensive Enterprise Developer Guide (CONTRIBUTING.md) with decoupled architecture, MIT License 2026 attribution, and code ethics.',
        'Desktop Advantages & Native Systems Tech Stack showcase on the public web surface.',
      ],
      changed: [
        'Upgraded core version baseline across all system manifests to 3.1.0.',
        'Synchronized visual card order dynamically in Tkinter pack sequence on every UI tick without visual tearing.',
      ],
      fixed: [
        'Detail Modal crash in Cockpit GUI: corrected PolicyEngine.compute_score() 4-parameter call contract and iface.state.is_eligible_candidate() method resolution.',
        'Interface deck dynamic click and detail handler re-binding to prevent stale runtime snapshot references.',
      ],
    },
    {
      version: '3.0.1',
      tag: 'v3.0.1',
      date: 'September 14, 2026',
      channel: 'STABLE',
      highlights:
        '5-Case deterministic interface priority hierarchy and active live workload continuity protection for Zoom, Microsoft Teams, vMix, and OBS Studio.',
      added: [
        '5-Case interface priority hierarchy: Ethernet prioritized over Wi-Fi, eth0 baseline primary, instant eth1 failover upon eth0 degradation, and emergency Wi-Fi failover.',
        'Workload continuity shield forbidding impulsive switching between healthy Ethernet paths during active live streaming.',
      ],
      changed: [
        'Refined route takeover arbiter to prioritize session stability over microscopic latency fluctuations.',
      ],
      fixed: [
        'Prevented unnecessary route oscillations when secondary Ethernet adapters recover.',
      ],
    },
    {
      version: '3.0.0 (Beta)',
      tag: 'v3.0.0-preview.26',
      date: 'September 13, 2026',
      channel: 'BETA',
      highlights:
        'Authoritative multi-platform Beta Release with Full HD desktop cockpit showcase, 4-provider speedtest architecture, and windowed GUI desktop application.',
      added: [
        'Modular 4-Provider Speedtest Architecture (Cloudflare, Fast.com, Ookla, nPerf) with sequential non-contention benchmark runner.',
        'Desktop sub-navigation tabs (Overview, Interfaces, Speed Test, Events) with clean state isolation.',
        'Dynamic GitHub Releases discovery service with Stale-While-Revalidate caching.',
      ],
      changed: [
        'Designated Release 26 as the official multi-platform Beta Release with Full HD cockpit showcase.',
        'Cleaned application teardown with automatic route metric restoration upon exit.',
      ],
      fixed: [
        'Eliminated Windows kernel socket accumulation via zero-linger SO_LINGER(1, 0) and SO_REUSEADDR.',
        'Prevented psutil process iteration lock contention with media capture drivers.',
      ],
    },
    {
      version: '2.6.0',
      tag: 'v2.6.0',
      date: 'September 2026',
      channel: 'LEGACY',
      highlights:
        'Dual supercar cockpit tachometers (RPM Download & MPH Upload) with dynamic auto-scaling (Kbps/Mbps/Gbps) and RFC 3550 Jitter HUD readout.',
      added: [
        'Automotive digital cluster dials with 60 FPS client-side needle lerping.',
        'Center HUD readout for RFC 3550 transit jitter calculation.',
        'Circular ICMP multi-target backbone indicators (1.1.1.1, 8.8.8.8, 9.9.9.9).',
      ],
    },
    {
      version: '2.5.0',
      tag: 'v2.5.0',
      date: 'September 2026',
      channel: 'LEGACY',
      highlights:
        'SportsCarSpeedGauge speedtest gauge with 250° arc and peak hold indicators.',
      added: [
        'Staged tactile refresh feedback sequence for adapter scanning.',
        'Canvas idle sleep optimization reducing CPU usage during constant network throughput.',
      ],
    },
    {
      version: '2.4.0',
      tag: 'v2.4.0',
      date: 'September 2026',
      channel: 'LEGACY',
      highlights:
        'Inline QoS monitor for one-click meeting and broadcast bandwidth reservation.',
      added: [
        'Adaptive 1-to-8 port layout engine supporting single-NIC laptops through multi-port workstations.',
        'Searchable log viewer with level filtering and export capability.',
      ],
    },
    {
      version: '2.0.0',
      tag: 'v2.0.0',
      date: 'September 2026',
      channel: 'LEGACY',
      highlights:
        'Multi-port failover engine supporting simultaneous routing metric management across up to 3 physical adapters.',
      added: [
        'Real-time Jitter calculation implemented using standard IETF RFC 3550 formula.',
        'Rebranding to MODULA with dual dark/light theme foundation.',
      ],
    },
    {
      version: '1.0.0',
      tag: 'v1.0.0',
      date: 'September 2026',
      channel: 'LEGACY',
      highlights:
        'Initial release of software Layer-3 metric manipulation for zero-drop network failover without socket teardown.',
      added: [
        'Native routing table metric manipulation for uninterrupted network path failover.',
      ],
    },
  ];

  const filtered = releases.filter((r) => {
    if (filterChannel === 'ALL') return true;
    return r.channel === filterChannel;
  });

  return (
    <section
      id="changelog"
      className="py-20 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto border-t border-slate-800/80"
    >
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold tracking-wider uppercase mb-4">
          <GitCommit className="w-3.5 h-3.5" />
          Version Evolution
        </div>
        <h2 className="text-3xl sm:text-5xl font-extrabold text-white mb-4 tracking-tight">
          Release Changelog
        </h2>
        <p className="text-slate-400 text-base">
          Authoritative history of all notable changes to AutoFailover by Modula,
          from initial prototype to the current 3.1.0 release.
        </p>

        {/* Channel Filter Pills */}
        <div className="mt-6 inline-flex p-1 rounded-xl bg-slate-900 border border-slate-800 gap-1">
          {(['ALL', 'STABLE', 'BETA', 'LEGACY'] as const).map((channel) => (
            <button
              key={channel}
              onClick={() => setFilterChannel(channel)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                filterChannel === channel
                  ? 'bg-emerald-500 text-slate-950 shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {channel === 'ALL' ? 'All Releases' : channel}
            </button>
          ))}
        </div>
      </div>

      {/* Timeline */}
      <div className="relative border-l border-slate-800 ml-4 sm:ml-8 pl-6 sm:pl-8 space-y-12">
        {filtered.map((r, idx) => {
          const isLatest = idx === 0 && filterChannel === 'ALL';
          return (
            <div key={r.tag} className="relative group">
              {/* Timeline Dot */}
              <div
                className={`absolute -left-[31px] sm:-left-[39px] top-1.5 w-4 h-4 rounded-full border-2 flex items-center justify-center transition-all ${
                  isLatest
                    ? 'bg-emerald-500 border-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.8)]'
                    : r.channel === 'BETA'
                      ? 'bg-cyan-500 border-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.6)]'
                      : 'bg-slate-900 border-slate-700 group-hover:border-slate-500'
                }`}
              />

              {/* Version Header Box */}
              <div className="p-6 rounded-2xl bg-[#0a0f19] border border-slate-800 hover:border-slate-700 transition-all shadow-lg">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xl font-bold text-white font-mono">
                      v{r.version}
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                        r.channel === 'STABLE'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : r.channel === 'BETA'
                            ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                            : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {r.channel}
                    </span>
                    {isLatest && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500 text-slate-950 font-extrabold uppercase">
                        Current Latest
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
                    <span>{r.date}</span>
                    <a
                      href={`https://github.com/parikesitad-pm/smart_auto_failover/releases/tag/${r.tag}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-400 hover:text-cyan-300 inline-flex items-center gap-1 underline"
                    >
                      <Tag className="w-3 h-3" />
                      {r.tag}
                      <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  </div>
                </div>

                {/* Highlights */}
                <p className="text-sm text-slate-300 mb-4 leading-relaxed">
                  {r.highlights}
                </p>

                {/* Detailed Categorized Lists */}
                <div className="space-y-3 pt-2 border-t border-slate-800/80">
                  {r.added && r.added.length > 0 && (
                    <div>
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-400 uppercase tracking-wider mb-1.5">
                        <PlusCircle className="w-3 h-3" /> Added
                      </span>
                      <ul className="space-y-1 pl-1">
                        {r.added.map((item, i) => (
                          <li
                            key={i}
                            className="text-xs text-slate-400 flex items-start gap-2 leading-relaxed"
                          >
                            <span className="text-emerald-500 shrink-0">•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {r.changed && r.changed.length > 0 && (
                    <div>
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold text-cyan-400 uppercase tracking-wider mb-1.5">
                        <Wrench className="w-3 h-3" /> Changed
                      </span>
                      <ul className="space-y-1 pl-1">
                        {r.changed.map((item, i) => (
                          <li
                            key={i}
                            className="text-xs text-slate-400 flex items-start gap-2 leading-relaxed"
                          >
                            <span className="text-cyan-500 shrink-0">•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {r.fixed && r.fixed.length > 0 && (
                    <div>
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-400 uppercase tracking-wider mb-1.5">
                        <ShieldCheck className="w-3 h-3" /> Fixed & Hardened
                      </span>
                      <ul className="space-y-1 pl-1">
                        {r.fixed.map((item, i) => (
                          <li
                            key={i}
                            className="text-xs text-slate-400 flex items-start gap-2 leading-relaxed"
                          >
                            <span className="text-amber-400 shrink-0">•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer link to GitHub */}
      <div className="text-center mt-12">
        <a
          href="https://github.com/parikesitad-pm/smart_auto_failover/blob/main/CHANGELOG.md"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs font-mono text-cyan-400 hover:text-cyan-300 inline-flex items-center gap-1.5 underline"
        >
          View complete raw CHANGELOG.md on GitHub
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </section>
  );
};
