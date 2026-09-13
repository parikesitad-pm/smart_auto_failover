import React, { useRef, useState } from 'react';
import { Shield, ArrowRight, Activity, Terminal, Download } from 'lucide-react';

import { ResolvedRelease } from '../../types/releases';

interface HeroSectionProps {
  onScrollToDownloads: () => void;
  onScrollToShowcase: () => void;
  release?: ResolvedRelease | null;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  onScrollToDownloads,
  onScrollToShowcase,
  release,
}) => {
  const logoCardRef = useRef<HTMLDivElement>(null);
  const [rotateX, setRotateX] = useState(0);
  const [rotateY, setRotateY] = useState(0);
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!logoCardRef.current) return;
    const rect = logoCardRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const deltaX = (e.clientX - centerX) / (rect.width / 2);
    const deltaY = (e.clientY - centerY) / (rect.height / 2);

    setRotateX(-deltaY * 16);
    setRotateY(deltaX * 16);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    setRotateX(0);
    setRotateY(0);
  };

  return (
    <section className="relative pt-24 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto overflow-hidden">
      {/* Background radial glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[680px] h-[680px] bg-emerald-500/10 rounded-full blur-[140px] pointer-events-none -z-10" />
      <div className="absolute top-1/3 left-1/3 -translate-x-1/2 -translate-y-1/2 w-[420px] h-[420px] bg-cyan-500/10 rounded-full blur-[100px] pointer-events-none -z-10" />

      <div className="text-center max-w-4xl mx-auto">
        {/* Top release badge */}
        <a
          href={
            release?.htmlUrl ||
            `https://github.com/parikesitad-pm/smart_auto_failover/releases/tag/${release?.tagName || 'v3.0.0-preview.25'}`
          }
          target="_blank"
          rel="noopener noreferrer"
          title={`View ${release ? release.tagName : 'v3.0.0-preview.25'} on GitHub Releases`}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 hover:border-emerald-500/60 text-emerald-400 text-xs font-semibold tracking-wider uppercase mb-8 backdrop-blur-md transition-all group cursor-pointer"
        >
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span>
            AutoFailover 3.0 by Modula •{' '}
            <span className="text-cyan-300 font-semibold">Beta Release</span> •{' '}
            <strong className="underline decoration-emerald-500/50 underline-offset-2">
              {release ? release.tagName : 'v3.0.0-preview.25'}
            </strong>
          </span>
          <ArrowRight className="w-3 h-3 text-emerald-400 group-hover:translate-x-1 transition-transform" />
        </a>

        {/* Alive Breathing 3D Interactive Logo */}
        <div
          className="relative w-48 h-48 sm:w-56 sm:h-56 mx-auto mb-10 flex items-center justify-center cursor-pointer select-none"
          style={{ perspective: '1000px' }}
          onMouseMove={handleMouseMove}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={handleMouseLeave}
        >
          {/* Orbital Tech Reticles */}
          <div className="absolute inset-0 rounded-full border border-emerald-500/20 border-dashed animate-[spin_24s_linear_infinite] pointer-events-none" />
          <div className="absolute -inset-4 rounded-full border border-cyan-500/15 border-t-transparent border-b-transparent animate-[spin_16s_linear_infinite_reverse] pointer-events-none" />

          {/* Interactive 3D Tilt Card */}
          <div
            ref={logoCardRef}
            style={{
              transform: `rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(${isHovered ? 1.05 : 1})`,
              transition: isHovered
                ? 'transform 0.08s ease-out'
                : 'transform 0.5s ease-out',
              transformStyle: 'preserve-3d',
            }}
            className="relative w-40 h-40 sm:w-48 sm:h-48 rounded-3xl p-6 bg-gradient-to-b from-[#121c2d]/80 to-[#080b10]/90 border border-emerald-500/30 shadow-[0_0_50px_rgba(16,185,129,0.25)] flex items-center justify-center backdrop-blur-xl group"
          >
            {/* Pulsing Emerald Halo */}
            <div className="absolute inset-0 rounded-3xl bg-emerald-500/10 blur-xl opacity-75 group-hover:opacity-100 transition-opacity animate-pulse" />

            <img
              src="/modula_3.0.png"
              alt="Modula 3.0 Official Identity"
              className="w-full h-full object-contain relative z-10 drop-shadow-[0_0_24px_rgba(16,185,129,0.6)]"
            />
          </div>
        </div>

        {/* Primary Statement */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white mb-6 leading-[1.1]">
          Navigate Your Internet Pipeline <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
            to Keep You Online
          </span>
        </h1>

        {/* Supporting Statement */}
        <p className="text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto mb-10 leading-relaxed font-normal">
          Engineered for{' '}
          <strong className="text-white font-semibold">
            Video Conference & Livestreaming Production
          </strong>
          . Real-time RFC 3550 jitter evaluation, multi-factor scoring, and
          anti-flap arbitrated failover.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
          <button
            onClick={onScrollToDownloads}
            className="w-full sm:w-auto px-7 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm shadow-[0_0_25px_rgba(16,185,129,0.35)] transition-all flex items-center justify-center gap-2 group cursor-pointer"
          >
            <Download className="w-4 h-4 group-hover:-translate-y-0.5 transition-transform" />
            Download AutoFailover 3.0 Beta{' '}
            {release ? `(${release.tagName})` : ''}
          </button>

          <button
            onClick={onScrollToShowcase}
            className="w-full sm:w-auto px-7 py-3.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-700 hover:border-cyan-500/50 text-white font-semibold text-sm transition-all flex items-center justify-center gap-2 shadow-lg backdrop-blur-md group cursor-pointer"
          >
            <Activity className="w-4 h-4 text-cyan-400 group-hover:rotate-12 transition-transform" />
            Desktop Cockpit
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 transition-transform" />
          </button>

          <a
            href={
              release?.htmlUrl ||
              `https://github.com/parikesitad-pm/smart_auto_failover/releases/tag/${release?.tagName || 'v3.0.0-preview.25'}`
            }
            target="_blank"
            rel="noopener noreferrer"
            className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-slate-950/60 hover:bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white font-semibold text-sm transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            GitHub Beta Release (
            {release ? release.tagName : 'v3.0.0-preview.25'})
            <ArrowRight className="w-4 h-4 text-cyan-400" />
          </a>
        </div>

        {/* Micro Tagline & Guiding Principle */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-400 border-t border-slate-800/80 pt-6">
          <span className="flex items-center gap-1.5">
            <Shield className="w-4 h-4 text-emerald-400" />
            Switch when necessary, not because you can
          </span>
          <span className="w-1 h-1 rounded-full bg-slate-700" />
          <span className="flex items-center gap-1.5">
            <Terminal className="w-4 h-4 text-cyan-400" />
            Kelihatan kompleks di dalam, terasa sederhana di luar
          </span>
        </div>
      </div>
    </section>
  );
};
