import React, { useMemo } from 'react';
import { PerformanceGaugesProps } from './PerformanceGauges.types';
import { calculateGaugeGeometry } from '../../../lib/gaugeMath';

export const PerformanceGauges: React.FC<PerformanceGaugesProps> = ({
  telemetry,
}) => {
  const dlGeom = useMemo(
    () => calculateGaugeGeometry(telemetry.downloadSpeed, 'download'),
    [telemetry.downloadSpeed]
  );

  const ulGeom = useMemo(
    () => calculateGaugeGeometry(telemetry.uploadSpeed, 'upload'),
    [telemetry.uploadSpeed]
  );

  return (
    <section
      aria-label="Network Performance Gauges"
      className="my-3 grid grid-cols-1 md:grid-cols-3 gap-4 items-center"
    >
      {/* Left Gauge: Download Speed */}
      <div className="cockpit-panel rounded-xl p-4 border border-cyan-900/30 flex flex-col items-center relative group">
        <div className="w-full flex justify-between items-center text-[11px] font-mono text-cyan-400 uppercase tracking-wider mb-1">
          <span className="flex items-center gap-1">
            <svg
              className="w-3.5 h-3.5 text-cyan-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2.5"
                d="M19 14l-7 7m0 0l-7-7m7 7V3"
              />
            </svg>
            Download
          </span>
          <span className="text-slate-400">Peak 212 Mbps</span>
        </div>

        <div className="relative w-44 h-44 flex items-center justify-center">
          <svg className="w-full h-full" viewBox="0 0 200 200">
            {/* Background Scale Track Arc (-120 deg to +120 deg) */}
            <path
              d="M 37.65 136.00 A 72 72 0 1 1 162.35 136.00"
              stroke="#1e293b"
              strokeWidth="10"
              strokeLinecap="round"
              fill="none"
            />
            {/* Reference scale markers */}
            <text
              x="32"
              y="154"
              fill="#475569"
              fontFamily="monospace"
              fontSize="8"
              textAnchor="middle"
            >
              0
            </text>
            <text
              x="100"
              y="18"
              fill="#475569"
              fontFamily="monospace"
              fontSize="8"
              textAnchor="middle"
            >
              150
            </text>
            <text
              x="168"
              y="154"
              fill="#475569"
              fontFamily="monospace"
              fontSize="8"
              textAnchor="middle"
            >
              300
            </text>

            {/* Active Progress Arc */}
            {dlGeom.arcPath && (
              <path
                d={dlGeom.arcPath}
                stroke="#06b6d4"
                strokeWidth="10"
                strokeLinecap="round"
                fill="none"
                style={{
                  filter: 'drop-shadow(0 0 8px rgba(6, 182, 212, 0.75))',
                }}
              />
            )}

            {/* Needle (Collinear with arc endpoint, exact center pivot 100, 100) */}
            <line
              x1="100"
              y1="100"
              x2="100"
              y2="38"
              stroke="#38bdf8"
              strokeWidth="2.5"
              strokeLinecap="round"
              transform={dlGeom.needleTransform}
            />
            <circle
              cx="100"
              cy="100"
              r="6"
              fill="#080b11"
              stroke="#38bdf8"
              strokeWidth="2"
            />
            <circle cx="100" cy="100" r="2" fill="#38bdf8" />
          </svg>

          <div className="absolute flex flex-col items-center pointer-events-none">
            <span className="text-2xl font-black font-mono tracking-tight text-white">
              {telemetry.downloadSpeed.toFixed(1)}
            </span>
            <span className="text-[10px] font-mono text-cyan-400 uppercase">
              Mbps
            </span>
          </div>
        </div>
      </div>

      {/* Center Dial: Net Health & RFC 3550 Telemetry */}
      <div className="cockpit-panel rounded-2xl p-4 border border-slate-700/60 shadow-xl flex flex-col items-center justify-center relative">
        <span className="text-[10px] font-mono tracking-widest text-slate-400 uppercase mb-1">
          Network Health Index
        </span>

        <div className="relative w-36 h-36 flex items-center justify-center my-1">
          <svg
            className="w-full h-full transform -rotate-90"
            viewBox="0 0 100 100"
          >
            <circle
              cx="50"
              cy="50"
              r="42"
              stroke="#1e293b"
              strokeWidth="6"
              fill="none"
            />
            <circle
              cx="50"
              cy="50"
              r="42"
              stroke="#10b981"
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray="264"
              strokeDashoffset={264 - (telemetry.healthScore / 100) * 264}
              fill="none"
              style={{ filter: 'drop-shadow(0 0 8px rgba(16, 185, 129, 0.6))' }}
            />
          </svg>
          <div className="absolute flex flex-col items-center">
            <span className="text-3xl font-black font-mono text-emerald-400">
              {telemetry.healthScore}
            </span>
            <span className="text-[9px] font-mono text-emerald-300 uppercase tracking-widest font-bold">
              /100 HEALTHY
            </span>
          </div>
        </div>

        {/* RFC 3550 Jitter & Latency */}
        <div className="w-full grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80 text-center font-mono">
          <div className="bg-slate-900/60 rounded-lg p-1.5 border border-slate-800">
            <span className="text-[9px] text-slate-400 uppercase block">
              Latency
            </span>
            <span className="text-xs font-bold text-white">
              {telemetry.latency} ms
            </span>
          </div>
          <div className="bg-slate-900/60 rounded-lg p-1.5 border border-slate-800">
            <span className="text-[9px] text-slate-400 uppercase block">
              RFC 3550 Jitter
            </span>
            <span className="text-xs font-bold text-cyan-300">
              {telemetry.jitter} ms
            </span>
          </div>
        </div>
      </div>

      {/* Right Gauge: Upload Speed */}
      <div className="cockpit-panel rounded-xl p-4 border border-fuchsia-900/30 flex flex-col items-center relative group">
        <div className="w-full flex justify-between items-center text-[11px] font-mono text-fuchsia-400 uppercase tracking-wider mb-1">
          <span className="flex items-center gap-1">
            <svg
              className="w-3.5 h-3.5 text-fuchsia-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2.5"
                d="M5 10l7-7m0 0l7 7m-7-7v18"
              />
            </svg>
            Upload
          </span>
          <span className="text-slate-400">Peak 58 Mbps</span>
        </div>

        <div className="relative w-44 h-44 flex items-center justify-center">
          <svg className="w-full h-full" viewBox="0 0 200 200">
            {/* Background Scale Track Arc (-120 deg to +120 deg) */}
            <path
              d="M 37.65 136.00 A 72 72 0 1 1 162.35 136.00"
              stroke="#1e293b"
              strokeWidth="10"
              strokeLinecap="round"
              fill="none"
            />
            {/* Reference scale markers */}
            <text
              x="32"
              y="154"
              fill="#475569"
              fontFamily="monospace"
              fontSize="8"
              textAnchor="middle"
            >
              0
            </text>
            <text
              x="100"
              y="18"
              fill="#475569"
              fontFamily="monospace"
              fontSize="8"
              textAnchor="middle"
            >
              50
            </text>
            <text
              x="168"
              y="154"
              fill="#475569"
              fontFamily="monospace"
              fontSize="8"
              textAnchor="middle"
            >
              100
            </text>

            {/* Active Progress Arc */}
            {ulGeom.arcPath && (
              <path
                d={ulGeom.arcPath}
                stroke="#d946ef"
                strokeWidth="10"
                strokeLinecap="round"
                fill="none"
                style={{
                  filter: 'drop-shadow(0 0 8px rgba(217, 70, 239, 0.75))',
                }}
              />
            )}

            {/* Needle (Collinear with arc endpoint, exact center pivot 100, 100) */}
            <line
              x1="100"
              y1="100"
              x2="100"
              y2="38"
              stroke="#f472b6"
              strokeWidth="2.5"
              strokeLinecap="round"
              transform={ulGeom.needleTransform}
            />
            <circle
              cx="100"
              cy="100"
              r="6"
              fill="#080b11"
              stroke="#f472b6"
              strokeWidth="2"
            />
            <circle cx="100" cy="100" r="2" fill="#f472b6" />
          </svg>

          <div className="absolute flex flex-col items-center pointer-events-none">
            <span className="text-2xl font-black font-mono tracking-tight text-white">
              {telemetry.uploadSpeed.toFixed(1)}
            </span>
            <span className="text-[10px] font-mono text-fuchsia-400 uppercase">
              Mbps
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};
