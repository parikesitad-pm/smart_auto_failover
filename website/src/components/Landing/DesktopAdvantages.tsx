import React from 'react';
import {
  ShieldAlert,
  Cpu,
  Zap,
  Lock,
  Layers,
  Activity,
  Terminal,
  Server,
  Code2,
  GitBranch,
} from 'lucide-react';

export const DesktopAdvantages: React.FC = () => {
  const advantages = [
    {
      icon: Activity,
      title: 'Active Workload Continuity',
      badge: 'Zoom • vMix • OBS',
      description:
        'Engineered specifically to shield real-time streams and conferences. Avoids impulsive route changes between healthy Ethernet links to guarantee uninterrupted broadcast sessions.',
      accent: 'emerald',
    },
    {
      icon: Layers,
      title: '5-Case Deterministic Arbitration',
      badge: 'Deterministic HAL',
      description:
        'Rigorous priority rules: physical Ethernet is prioritized over Wi-Fi, secondary cables are held during active sessions, and emergency Wi-Fi failover triggers instantly when all wires fail.',
      accent: 'cyan',
    },
    {
      icon: Zap,
      title: 'Mathematical Anti-Flap Margin',
      badge: 'Score-Based Arbiter',
      description:
        'Takeover equation (candidate_score >= active_score + takeover_margin) dampens momentary noise and jitter spikes without artificial failover delay.',
      accent: 'teal',
    },
    {
      icon: Cpu,
      title: 'Ultra-Light Engine (<0.5% CPU)',
      badge: 'Near-Zero Footprint',
      description:
        'Completely decoupled background thread architecture. Thread-safe snapshot broadcasting ensures the automotive cockpit never causes GUI stutter or CPU spikes.',
      accent: 'emerald',
    },
    {
      icon: ShieldAlert,
      title: 'Kernel TCP/IP Safety & Zero BSOD',
      badge: 'Native Socket Safety',
      description:
        'Probing sockets are armed with SO_REUSEADDR and zero-linger SO_LINGER(1, 0) abortive RSTs, eliminating kernel TIME_WAIT socket accumulation in tcpip.sys.',
      accent: 'cyan',
    },
    {
      icon: Lock,
      title: '100% Local & Privacy-First',
      badge: 'Zero Cloud Dependency',
      description:
        'All routing decisions, socket probes, and health evaluations execute entirely on your physical workstation. No telemetry data ever leaves your device.',
      accent: 'teal',
    },
  ];

  const techStackLayers = [
    {
      layer: 'Desktop Engine & Architecture',
      tech: 'Python 3.10+ Standalone Bundle • CustomTkinter Automotive GUI',
      details:
        'Packaged into a single native windowed binary via PyInstaller. Decoupled UI and background orchestrator via thread-safe RuntimeSnapshot queue.',
      icon: Code2,
    },
    {
      layer: 'Cross-Platform Hardware HAL',
      tech: 'Windows NetTCPIP • Linux Netlink & sysfs • macOS BSD route & networksetup',
      details:
        'Direct Layer-3 interface metric manipulation. Zero custom kernel filter drivers required, guaranteeing 100% operating system stability.',
      icon: Server,
    },
    {
      layer: 'RFC 3550 Statistical Probing',
      tech: 'IETF RFC 3550 Variance Estimator • Raw Non-Blocking Sockets',
      details:
        'Calculates real-time packet transit jitter (J = J + (|D| - J)/16) against multi-target backbones (Cloudflare, Google DNS, Quad9).',
      icon: Terminal,
    },
    {
      layer: 'Web Surface & Ecosystem',
      tech: 'React 18 • TypeScript • TailwindCSS • Vite',
      details:
        'Dynamic GitHub Releases API client with Stale-While-Revalidate caching, multi-version downloads, and automotive cockpit simulation.',
      icon: GitBranch,
    },
  ];

  return (
    <section
      id="advantages"
      className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-slate-800/80"
    >
      {/* Section Header */}
      <div className="text-center max-w-3xl mx-auto mb-16">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold tracking-wider uppercase mb-4">
          <Zap className="w-3.5 h-3.5" />
          Enterprise Engine Architecture
        </div>
        <h2 className="text-3xl sm:text-5xl font-extrabold text-white mb-4 tracking-tight">
          Engineered for Broadcast-Grade Stability
        </h2>
        <p className="text-slate-400 text-base sm:text-lg">
          AutoFailover Desktop is not a simple pinger. It is an autonomous,
          fault-tolerant Layer-3 route orchestrator built for zero session disruption.
        </p>
      </div>

      {/* 6 Advantages Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-20">
        {advantages.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div
              key={idx}
              className="p-6 rounded-2xl bg-gradient-to-b from-[#0e1626]/90 to-[#080b10] border border-slate-800 hover:border-emerald-500/40 transition-all shadow-xl group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-700 flex items-center justify-center text-emerald-400 group-hover:text-emerald-300 group-hover:border-emerald-500/50 transition-colors">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono font-semibold px-2.5 py-1 rounded-lg bg-slate-900 text-cyan-400 border border-slate-800">
                    {item.badge}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-white mb-2 group-hover:text-emerald-400 transition-colors">
                  {item.title}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {item.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Technical Stack Architecture Breakdown */}
      <div className="rounded-3xl bg-[#090d16] border border-slate-800/90 p-8 sm:p-10 shadow-2xl relative overflow-hidden">
        <div className="max-w-2xl mb-8">
          <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider font-semibold">
            Under The Hood
          </span>
          <h3 className="text-2xl sm:text-3xl font-bold text-white mt-1 mb-2">
            AutoFailover 3.1.0 Desktop Tech Stack
          </h3>
          <p className="text-xs sm:text-sm text-slate-400">
            A pure native systems architecture designed with zero bloat and absolute execution safety.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {techStackLayers.map((layer, idx) => {
            const Icon = layer.icon;
            return (
              <div
                key={idx}
                className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors flex gap-4 items-start"
              >
                <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-700/80 flex items-center justify-center text-emerald-400 shrink-0 mt-0.5">
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wide">
                    {layer.layer}
                  </div>
                  <div className="text-sm font-bold text-white mt-0.5 mb-1.5">
                    {layer.tech}
                  </div>
                  <div className="text-xs text-slate-400 leading-relaxed">
                    {layer.details}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
