import React from 'react';
import { StartupSequenceState } from '../../hooks/useStartupSequence';
import { TuyulSportCar } from './TuyulSportCar';

export interface SplashScreenProps {
  state: StartupSequenceState;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ state }) => {
  if (!state.isActive) return null;

  const showDevice = state.progress >= 5;
  const showOs = state.progress >= 14;
  const showArch = state.progress >= 26;
  const showInterfaces = state.progress >= 38;
  const showNetworkInfo = state.progress >= 50;
  const showProbe = state.progress >= 65;
  const showHealth = state.progress >= 78;
  const showActivePath = state.progress >= 90;

  return (
    <div
      id="splash-overlay"
      className="fixed inset-0 z-50 bg-[#05070a] flex flex-col items-center justify-center p-4 select-none transition-all duration-300"
    >
      {/* Carbon mesh background */}
      <div className="absolute inset-0 carbon-mesh opacity-40 pointer-events-none"></div>

      {/* Center Stage Card */}
      <div className="relative z-10 max-w-2xl w-full flex flex-col items-center text-center">
        {/* Brand & Product Positioning Hierarchy */}
        <div className="flex flex-col items-center mb-5">
          <div className="flex items-center space-x-2.5 mb-1.5">
            <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center text-cyan-400 shadow-lg">
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <div className="text-left font-mono">
              <span className="text-lg font-black tracking-tight text-white uppercase">
                AUTOFAILOVER 3.0
              </span>
              <span className="block text-[10px] font-semibold text-cyan-400 tracking-widest uppercase -mt-1">
                BY MODULA
              </span>
            </div>
          </div>

          {/* Primary User-Facing Positioning */}
          <h2 className="text-base sm:text-lg font-bold text-slate-100 tracking-tight leading-snug mt-1 font-sans">
            Navigate Your Internet Pipeline to Keep You Online
          </h2>

          {/* Supporting Line */}
          <p className="text-xs text-slate-400 font-sans tracking-normal mt-0.5">
            Through Video Conference &amp; Livestreaming Production
          </p>

          {/* Tagline */}
          <p className="text-[11px] font-mono text-cyan-400/90 tracking-wider mt-1 italic">
            "light seamless and usefull"
          </p>
        </div>

        {/* TUYUL SPORT CAR ANIMATED STAGE */}
        <TuyulSportCar
          isReady={state.isReady}
          isDeparting={state.isDeparting}
        />

        {/* INITIAL SYSTEM INFORMATION CARD */}
        <div className="w-full bg-[#080c14] border border-slate-800/80 rounded-xl p-3.5 shadow-xl mb-3 text-left font-mono">
          <div className="flex items-center justify-between border-b border-slate-800/70 pb-2 mb-2.5">
            <span className="text-[11px] font-bold tracking-wider text-slate-300 uppercase flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
              System Information
            </span>
            <span className="text-[10px] text-slate-500 font-normal">
              Native Hardware Discovery
            </span>
          </div>

          {/* 3-Item Compact System Summary */}
          <div className="grid grid-cols-3 gap-2 text-[11px] mb-3">
            {/* Device */}
            <div className="bg-slate-900/50 p-2 rounded-lg border border-slate-800/40">
              <div className="text-[9px] text-slate-500 uppercase font-semibold">
                Device
              </div>
              {showDevice ? (
                <div className="text-slate-200 font-bold truncate">
                  {state.systemIdentity?.deviceName || 'Nitro AN515-56'}
                </div>
              ) : (
                <div className="h-4 w-20 bg-slate-800/80 rounded animate-pulse mt-0.5"></div>
              )}
            </div>

            {/* Operating System */}
            <div className="bg-slate-900/50 p-2 rounded-lg border border-slate-800/40">
              <div className="text-[9px] text-slate-500 uppercase font-semibold">
                Operating System
              </div>
              {showOs ? (
                <div className="text-slate-200 font-bold truncate">
                  {state.systemIdentity?.osName || 'Linux'}
                </div>
              ) : (
                <div className="h-4 w-16 bg-slate-800/80 rounded animate-pulse mt-0.5"></div>
              )}
            </div>

            {/* Architecture */}
            <div className="bg-slate-900/50 p-2 rounded-lg border border-slate-800/40">
              <div className="text-[9px] text-slate-500 uppercase font-semibold">
                Architecture
              </div>
              {showArch ? (
                <div className="text-slate-200 font-bold truncate">
                  {state.systemIdentity?.architecture || 'x86_64'}
                </div>
              ) : (
                <div className="h-4 w-16 bg-slate-800/80 rounded animate-pulse mt-0.5"></div>
              )}
            </div>
          </div>

          {/* NETWORK DISCOVERY SECTION */}
          <div className="bg-slate-950/70 rounded-lg p-2.5 border border-slate-800/60 text-[10px] space-y-2">
            <div className="flex items-center justify-between text-slate-400 font-semibold border-b border-slate-800/50 pb-1">
              <span className="uppercase tracking-wider text-[10px] text-slate-300 flex items-center gap-1.5">
                <span
                  className={`w-1.5 h-1.5 rounded-full ${showInterfaces ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'}`}
                ></span>
                Network Discovery
              </span>
              <span
                className={
                  state.isReady ? 'text-emerald-400 font-bold' : 'text-cyan-400'
                }
              >
                {state.isReady ? 'TOPOLOGY VALIDATED ✓' : state.statusText}
              </span>
            </div>

            {/* Interface Discovery Rows */}
            {!showInterfaces ? (
              <div className="space-y-1.5 py-1">
                <div className="h-8 bg-slate-900/60 rounded border border-slate-800/50 animate-pulse flex items-center px-2.5">
                  <span className="text-slate-500 text-[9px]">
                    Scanning network interfaces...
                  </span>
                </div>
                <div className="h-8 bg-slate-900/60 rounded border border-slate-800/50 animate-pulse flex items-center px-2.5">
                  <span className="text-slate-500 text-[9px]">
                    Awaiting carrier state...
                  </span>
                </div>
              </div>
            ) : (
              <div className="space-y-1.5 pt-0.5">
                {state.discoveredInterfaces.map((iface) => {
                  const isOnline =
                    showActivePath &&
                    (iface.state === 'ONLINE' ||
                      state.activePath === iface.name);
                  return (
                    <div
                      key={iface.id}
                      className={`p-2 rounded border transition-all duration-200 ${
                        isOnline
                          ? 'bg-emerald-950/20 border-emerald-800/60'
                          : 'bg-slate-900/70 border-slate-800/70'
                      }`}
                    >
                      {/* Top Row: Name, Type, Carrier & State */}
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              iface.linkState === 'Connected'
                                ? 'bg-emerald-400'
                                : 'bg-slate-600'
                            }`}
                          ></span>
                          <span className="font-bold text-slate-200">
                            {iface.name}
                          </span>
                          <span className="px-1.5 py-0.2 bg-slate-800 rounded text-[9px] text-slate-400 uppercase">
                            {iface.mediaType}
                          </span>
                          <span className="text-slate-500 text-[9px]">
                            ({iface.adminState} · {iface.linkState})
                          </span>
                        </div>

                        <div>
                          {showActivePath ? (
                            <span
                              className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                                isOnline
                                  ? 'bg-emerald-900/80 text-emerald-300 border border-emerald-700/80'
                                  : 'bg-slate-800 text-cyan-300 border border-slate-700'
                              }`}
                            >
                              {isOnline ? 'ONLINE (ACTIVE)' : 'READY (STANDBY)'}
                            </span>
                          ) : showHealth ? (
                            <span className="text-cyan-400 text-[9px]">
                              Scoring...
                            </span>
                          ) : showProbe ? (
                            <span className="text-amber-400 text-[9px]">
                              Probing RFC 3550...
                            </span>
                          ) : (
                            <span className="text-slate-500 text-[9px]">
                              Detected
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Bottom Row: Detailed Network Properties (IPv4, Gateway, SSID, Speed) */}
                      {showNetworkInfo && (
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-1 text-[9px] text-slate-400 pt-1 border-t border-slate-800/50">
                          <div>
                            <span className="text-slate-500">IPv4: </span>
                            <span className="text-slate-300 font-mono">
                              {iface.ipAddress}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500">Netmask: </span>
                            <span className="text-slate-300 font-mono">
                              {iface.netmask}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500">Gateway: </span>
                            <span className="text-slate-300 font-mono">
                              {iface.gateway}
                            </span>
                          </div>
                          <div>
                            {iface.mediaType === 'wifi' ? (
                              <>
                                <span className="text-slate-500">SSID: </span>
                                <span className="text-cyan-300 font-mono">
                                  {iface.ssid}
                                </span>
                              </>
                            ) : (
                              <>
                                <span className="text-slate-500">Speed: </span>
                                <span className="text-slate-300 font-mono">
                                  {iface.linkSpeed}
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Authoritative Policy Engine Output */}
            {showActivePath && state.activePath && (
              <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1.5 border-t border-slate-800/80">
                <div className="flex items-center gap-1.5">
                  <span className="text-slate-500">
                    Designated Outbound Path:
                  </span>
                  <span className="text-emerald-400 font-bold">
                    {state.activePath}
                  </span>
                </div>
                <span className="text-slate-500 text-[9px]">
                  (Authoritative Policy Engine gate verified)
                </span>
              </div>
            )}
          </div>
        </div>

        {/* HONEST COMPLETION & TELEMETRY PROGRESS */}
        <div className="w-full bg-[#080c14] border border-slate-800 rounded-xl p-4 shadow-xl mb-4 text-left font-mono">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  state.isReady
                    ? 'bg-emerald-400 pulse-glow-emerald'
                    : 'bg-amber-400 animate-pulse'
                }`}
              ></span>
              <span
                className={`text-xs font-bold ${state.isReady ? 'text-emerald-400' : 'text-slate-200'}`}
              >
                {state.statusText}
              </span>
            </div>
            <span
              className={`text-xs font-bold ${state.isReady ? 'text-emerald-400' : 'text-cyan-400'}`}
            >
              {state.progress}%
            </span>
          </div>

          {/* Progress Bar Track */}
          <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden p-0.5 border border-slate-800">
            <div
              className={`h-full rounded-full transition-all duration-150 ${
                state.isReady
                  ? 'bg-emerald-500 shadow-[0_0_16px_rgba(16,185,129,0.9)]'
                  : 'bg-cyan-500 shadow-[0_0_12px_rgba(6,182,212,0.8)]'
              }`}
              style={{ width: `${state.progress}%` }}
            ></div>
          </div>

          {/* Decoupled Telemetry Readout */}
          <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-400">
            <div>
              Actual Core Init:{' '}
              <span className="text-white font-bold">
                {state.actualInitMs !== null
                  ? `${state.actualInitMs}ms ✓ Complete`
                  : 'Measuring...'}
              </span>
            </div>
            <div>
              Splash Min Duration:{' '}
              <span className="text-cyan-300 font-bold">
                {state.minDurationMs}ms
              </span>
            </div>
            <div>
              Remaining Window:{' '}
              <span className="text-slate-300 font-bold">
                {state.remainingMs}ms{' '}
                {state.isReady ? '(Playing Departure)' : ''}
              </span>
            </div>
          </div>
        </div>

        {/* Explanatory Note & Skip Tip */}
        <div className="flex flex-col items-center gap-1.5 text-[11px] text-slate-400 font-mono">
          <p className="text-slate-400">
            Controls minimum presentation duration. Does not affect network
            initialization.
          </p>
          <div className="flex items-center gap-2 mt-1 px-3 py-1 rounded-full bg-slate-900/80 border border-slate-800 text-[10px] text-slate-400">
            <kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700 text-slate-200 font-semibold shadow">
              Shift
            </kbd>
            <span>Hold Shift to skip startup presentation</span>
          </div>
        </div>
      </div>
    </div>
  );
};
