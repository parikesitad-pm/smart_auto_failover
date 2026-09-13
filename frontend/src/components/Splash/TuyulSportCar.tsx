import React from 'react';

export interface TuyulSportCarProps {
  isReady: boolean;
  isDeparting: boolean;
}

export const TuyulSportCar: React.FC<TuyulSportCarProps> = ({
  isReady,
  isDeparting,
}) => {
  return (
    <div className="relative w-full h-36 flex items-center justify-center overflow-hidden mb-6 border border-slate-800/80 rounded-2xl bg-gradient-to-b from-[#0a0e17] to-[#06090e] shadow-2xl">
      {/* Background speed lines */}
      <div className="absolute inset-0 flex items-center justify-between px-6 opacity-15 pointer-events-none">
        <div className="h-[1px] w-12 bg-cyan-400"></div>
        <div className="h-[1px] w-24 bg-cyan-400"></div>
        <div className="h-[1px] w-8 bg-cyan-400"></div>
        <div className="h-[1px] w-20 bg-cyan-400"></div>
      </div>

      {/* Motion Streak Light-Trail */}
      <div
        className={`absolute h-1.5 bg-gradient-to-l from-cyan-400 via-cyan-500/80 to-transparent rounded-full pointer-events-none transition-all ${
          isDeparting ? 'streak-active' : 'opacity-0'
        }`}
        style={{ right: '50%', bottom: '42px' }}
      ></div>

      {/* Tuyul & Sport Car Animated Unit */}
      <div
        className={`relative flex items-center justify-center transition-all duration-300 ${
          isDeparting ? 'car-departing' : 'tuyul-idle'
        }`}
      >
        <svg
          className="w-64 h-28"
          viewBox="0 0 260 110"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Shadow below car */}
          <ellipse
            cx="130"
            cy="98"
            rx="100"
            ry="7"
            fill="black"
            fillOpacity="0.65"
          />

          {/* Exhaust Flame Pulse (Ignites on 100% Ready) */}
          <g
            className={`transition-opacity duration-300 ${isReady ? 'opacity-100' : 'opacity-0'}`}
          >
            <polygon
              points="26,78 6,80 26,82"
              fill="#38bdf8"
              className="exhaust-active"
            />
            <polygon
              points="26,79 12,80 26,81"
              fill="#ffffff"
              className="exhaust-active"
            />
          </g>

          {/* Mini Sleek Sport Car Body */}
          <path
            d="M 28 85 L 235 85 L 244 80 L 225 78 L 35 78 Z"
            fill="#0b0f19"
            stroke="#1e293b"
            strokeWidth="1.5"
          />
          <path
            d="M 32 78 Q 45 68 85 66 L 115 54 Q 145 42 178 54 L 210 68 Q 235 72 245 80 L 220 80 Q 210 74 195 74 Q 180 74 172 80 L 98 80 Q 90 74 75 74 Q 60 74 52 80 Z"
            fill="#0f172a"
            stroke="#334155"
            strokeWidth="1.5"
          />

          {/* Performance Side Skirt with AutoFailover 3.0 Signature Accent */}
          <path
            d="M 98 79 L 172 79"
            stroke="#002b7f"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
          <path
            d="M 98 79 L 125 79"
            stroke="#5bc0eb"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
          <path
            d="M 152 79 L 172 79"
            stroke="#e31b23"
            strokeWidth="2.5"
            strokeLinecap="round"
          />

          {/* Cockpit Glass Canopy (Cyan Tinted) */}
          <path
            d="M 118 53 Q 145 43 172 53 L 182 66 L 108 66 Z"
            fill="#0369a1"
            fillOpacity="0.25"
            stroke="#38bdf8"
            strokeWidth="1.2"
          />

          {/* Rear Wing / Spoiler */}
          <path
            d="M 28 66 L 46 66 L 40 76 L 30 76 Z"
            fill="#0f172a"
            stroke="#475569"
            strokeWidth="1.2"
          />
          <line
            x1="28"
            y1="68"
            x2="44"
            y2="68"
            stroke="#ef4444"
            strokeWidth="2"
            strokeLinecap="round"
          />

          {/* TUYUL MASCOT IN COCKPIT */}
          <g>
            {/* Pointed ears */}
            <polygon points="135,46 128,42 134,50" fill="#cbd5e1" />
            <polygon points="155,46 162,42 156,50" fill="#cbd5e1" />
            {/* Bald Head */}
            <circle cx="145" cy="46" r="10" fill="#e2e8f0" />
            {/* HUD Visor / Cockpit Goggles */}
            <rect
              x="139"
              y="44"
              width="13"
              height="5.5"
              rx="2.5"
              fill="#0c4a6e"
              stroke="#38bdf8"
              strokeWidth="1"
            />
            <circle cx="143" cy="46.7" r="1.2" fill="#38bdf8" />
            <circle cx="148" cy="46.7" r="1.2" fill="#38bdf8" />
            <path
              d="M 143 51 Q 146 53 148 51"
              stroke="#475569"
              strokeWidth="1"
              strokeLinecap="round"
            />
            <circle cx="152" cy="56" r="2.5" fill="#e2e8f0" />
          </g>

          {/* Sport Car Headlight Units */}
          <g className="transition-all duration-300">
            <path
              d="M 230 73 L 244 76"
              stroke="#38bdf8"
              strokeWidth="2"
              strokeLinecap="round"
              opacity={isReady ? 1 : 0.3}
            />
            <polygon
              points="244,76 290,65 290,88"
              fill="url(#lightBeamGrad)"
              className={`transition-opacity duration-300 ${isReady ? 'opacity-80 headlight-on' : 'opacity-0'}`}
            />
          </g>

          {/* Performance Wheels & Rims */}
          <g transform="translate(63, 80)">
            <circle
              cx="0"
              cy="0"
              r="14"
              fill="#090d16"
              stroke="#475569"
              strokeWidth="2"
            />
            <circle
              cx="0"
              cy="0"
              r="8"
              fill="#1e293b"
              stroke="#64748b"
              strokeWidth="1.2"
            />
            <circle cx="0" cy="0" r="3" fill="#38bdf8" />
            <line
              x1="-8"
              y1="0"
              x2="8"
              y2="0"
              stroke="#94a3b8"
              strokeWidth="1"
            />
            <line
              x1="0"
              y1="-8"
              x2="0"
              y2="8"
              stroke="#94a3b8"
              strokeWidth="1"
            />
          </g>
          <g transform="translate(186, 80)">
            <circle
              cx="0"
              cy="0"
              r="14"
              fill="#090d16"
              stroke="#475569"
              strokeWidth="2"
            />
            <circle
              cx="0"
              cy="0"
              r="8"
              fill="#1e293b"
              stroke="#64748b"
              strokeWidth="1.2"
            />
            <circle cx="0" cy="0" r="3" fill="#38bdf8" />
            <line
              x1="-8"
              y1="0"
              x2="8"
              y2="0"
              stroke="#94a3b8"
              strokeWidth="1"
            />
            <line
              x1="0"
              y1="-8"
              x2="0"
              y2="8"
              stroke="#94a3b8"
              strokeWidth="1"
            />
          </g>

          <defs>
            <linearGradient
              id="lightBeamGrad"
              x1="0%"
              y1="0%"
              x2="100%"
              y2="0%"
            >
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.75" />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>
      </div>
    </div>
  );
};
