import React from 'react';
import { StartupSequenceState } from '../../hooks/useStartupSequence';

export interface SplashScreenProps {
  state: StartupSequenceState;
  onRetry?: () => void;
  onSkip?: () => void;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({
  state,
  onRetry,
  onSkip,
}) => {
  if (!state.isActive) return null;

  // Progressive disclosure triggers mapped to exact stage thresholds:
  // 10% - 20%: Reading System Information
  const showSystem = state.progress >= 10;
  // 20% - 40%: Discovering Network Interfaces
  const showInterfaces = state.progress >= 20;
  // 40% - 55%: Reading IP Configuration
  const showIpConfig = state.progress >= 40;
  // 55% - 70%: Validating Interface State
  const showInterfaceValidation = state.progress >= 55;
  // 70% - 85%: Initializing Network Probes
  const showProbes = state.progress >= 70;
  // 85% - 95%: Evaluating Network Health
  const showHealth = state.progress >= 85;
  // 95% - 100%: Preparing Runtime State / Active Path
  const showActivePath = state.progress >= 95;

  // Interface grouping: separate Ethernet and Wi-Fi for clear enterprise hierarchy
  const ethernetInterfaces = state.discoveredInterfaces.filter(
    (i) => i.mediaType.toLowerCase() === 'ethernet'
  );
  const wifiInterfaces = state.discoveredInterfaces.filter(
    (i) => i.mediaType.toLowerCase() === 'wifi'
  );
  const otherInterfaces = state.discoveredInterfaces.filter(
    (i) =>
      i.mediaType.toLowerCase() !== 'ethernet' &&
      i.mediaType.toLowerCase() !== 'wifi'
  );

  return (
    <div
      id="splash-overlay"
      className={`fixed inset-0 z-50 bg-[#05070a] flex flex-col items-center justify-center p-4 select-none transition-opacity duration-350 ease-out ${
        state.isFadingOut ? 'opacity-0 pointer-events-none' : 'opacity-100'
      }`}
    >
      {/* Precision carbon mesh background */}
      <div className="absolute inset-0 carbon-mesh opacity-40 pointer-events-none" />

      {/* Subtle radial ambient emerald glow behind logo */}
      <div
        className={`absolute w-[480px] h-[480px] rounded-full blur-[120px] pointer-events-none transition-all duration-700 ${
          state.isFailed
            ? 'bg-rose-500/10'
            : state.isReady
              ? 'bg-emerald-500/20'
              : 'bg-emerald-500/12'
        }`}
      />

      {/* Main Container */}
      <div className="relative z-10 max-w-2xl w-full flex flex-col items-center text-center">
        {/* Modula 3.0 Official Brand Logo */}
        <div className="flex flex-col items-center mb-4">
          <div className="relative mb-3 flex items-center justify-center">
            <img
              src="/modula_3.0.png"
              alt="Modula 3.0 Official Logo"
              className={`w-28 h-28 object-contain transition-all duration-500 ${
                state.isFailed
                  ? 'drop-shadow-[0_0_24px_rgba(244,63,94,0.4)]'
                  : state.isReady
                    ? 'drop-shadow-[0_0_28px_rgba(16,185,129,0.45)]'
                    : 'drop-shadow-[0_0_20px_rgba(16,185,129,0.25)]'
              }`}
            />
          </div>

          <div className="font-mono">
            <h1 className="text-xl font-black tracking-tight text-white uppercase">
              AUTOFAILOVER 3.0
            </h1>
            <span className="block text-[10px] font-semibold text-emerald-400 tracking-[0.25em] uppercase -mt-0.5">
              BY MODULA
            </span>
          </div>

          {/* Positioning & Tagline */}
          <h2 className="text-sm font-medium text-slate-200 tracking-tight mt-1 font-sans">
            Navigate Your Internet Pipeline to Keep You Online
          </h2>
          <p className="text-[11px] font-mono text-emerald-400/80 tracking-wider mt-0.5 italic">
            "light seamless and usefull"
          </p>
        </div>

        {/* SYSTEM HARDWARE & SPECIFICATION CARD */}
        <div className="w-full bg-[#080c14] border border-slate-800/80 rounded-xl p-3.5 shadow-2xl mb-2.5 text-left font-mono">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2 mb-2.5">
            <span className="text-[11px] font-bold tracking-wider text-slate-300 uppercase flex items-center gap-1.5">
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  showSystem ? 'bg-emerald-400' : 'bg-slate-600'
                }`}
              />
              System Specification
            </span>
            <span className="text-[10px] text-slate-500 font-normal">
              {showSystem
                ? 'Authoritative Hardware Detection'
                : 'Awaiting Hardware Probe...'}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 text-[11px]">
            {/* Device / Hostname */}
            <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800/50">
              <div className="text-[9px] text-slate-500 uppercase font-semibold">
                Device / Host
              </div>
              {showSystem ? (
                <div
                  className="text-slate-200 font-bold truncate"
                  title={
                    state.systemIdentity?.deviceName || 'Local Workstation'
                  }
                >
                  {state.systemIdentity?.deviceName || 'Local Workstation'}
                </div>
              ) : (
                <div className="h-4 w-20 bg-slate-800/70 rounded animate-pulse mt-0.5" />
              )}
            </div>

            {/* Operating System */}
            <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800/50">
              <div className="text-[9px] text-slate-500 uppercase font-semibold">
                Operating System
              </div>
              {showSystem ? (
                <div
                  className="text-slate-200 font-bold truncate"
                  title={
                    state.systemIdentity?.kernelOrVersion
                      ? `${state.systemIdentity.osName} (${state.systemIdentity.kernelOrVersion})`
                      : state.systemIdentity?.osName || 'Linux / Native'
                  }
                >
                  {state.systemIdentity?.osName || 'Native OS'}
                </div>
              ) : (
                <div className="h-4 w-16 bg-slate-800/70 rounded animate-pulse mt-0.5" />
              )}
            </div>

            {/* Architecture */}
            <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800/50">
              <div className="text-[9px] text-slate-500 uppercase font-semibold">
                Architecture
              </div>
              {showSystem ? (
                <div className="text-slate-200 font-bold truncate">
                  {state.systemIdentity?.architecture || 'x86_64'}
                </div>
              ) : (
                <div className="h-4 w-16 bg-slate-800/70 rounded animate-pulse mt-0.5" />
              )}
            </div>
          </div>
        </div>

        {/* NETWORK TOPOLOGY & INTERFACES CARD */}
        <div className="w-full bg-[#080c14] border border-slate-800/80 rounded-xl p-3.5 shadow-2xl mb-3 text-left font-mono">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2 mb-2.5">
            <span className="text-[11px] font-bold tracking-wider text-slate-300 uppercase flex items-center gap-1.5">
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  state.isReady
                    ? 'bg-emerald-400'
                    : showInterfaces
                      ? 'bg-cyan-400'
                      : 'bg-amber-400 animate-pulse'
                }`}
              />
              Network Topology &amp; Pipelines
            </span>
            <span
              className={`text-[10px] font-semibold ${
                state.isReady
                  ? 'text-emerald-400'
                  : state.isFailed
                    ? 'text-rose-400'
                    : 'text-slate-400'
              }`}
            >
              {state.isReady
                ? 'TOPOLOGY VALIDATED ✓'
                : state.isFailed
                  ? 'DETECTION HALTED'
                  : state.statusText}
            </span>
          </div>

          {/* Interface Rows */}
          {!showInterfaces ? (
            <div className="space-y-1.5 py-1">
              <div className="h-8 bg-slate-900/50 rounded border border-slate-800/50 animate-pulse flex items-center px-2.5">
                <span className="text-slate-500 text-[10px]">
                  Discovering network interfaces via native OS APIs...
                </span>
              </div>
              <div className="h-8 bg-slate-900/50 rounded border border-slate-800/50 animate-pulse flex items-center px-2.5">
                <span className="text-slate-500 text-[10px]">
                  Querying adapter carrier states...
                </span>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              {/* Ethernet Section */}
              {ethernetInterfaces.length > 0 && (
                <div className="space-y-1">
                  {ethernetInterfaces.map((iface) => {
                    const isOnline =
                      showActivePath &&
                      (iface.state === 'ONLINE' ||
                        state.activePath === iface.name);
                    return (
                      <div
                        key={iface.id}
                        className={`p-2 rounded-lg border transition-all duration-200 text-[10px] ${
                          isOnline
                            ? 'bg-emerald-950/20 border-emerald-700/60'
                            : 'bg-slate-900/70 border-slate-800/70'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                iface.linkState === 'Connected'
                                  ? 'bg-emerald-400'
                                  : 'bg-slate-600'
                              }`}
                            />
                            <span className="font-bold text-slate-200">
                              {iface.name}
                            </span>
                            <span className="px-1.5 py-0.5 bg-slate-800 rounded text-[9px] text-slate-400 uppercase font-semibold">
                              Ethernet
                            </span>
                            {showInterfaceValidation && (
                              <span className="text-slate-500 text-[9px]">
                                {iface.linkState} · {iface.linkSpeed}
                              </span>
                            )}
                          </div>

                          <div>
                            {showActivePath ? (
                              <span
                                className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                                  isOnline
                                    ? 'bg-emerald-900/80 text-emerald-300 border border-emerald-600/80'
                                    : 'bg-slate-800 text-slate-300 border border-slate-700'
                                }`}
                              >
                                {isOnline ? 'ONLINE (ACTIVE)' : 'READY'}
                              </span>
                            ) : showHealth ? (
                              <span className="text-emerald-400 text-[9px]">
                                Health Evaluated ✓
                              </span>
                            ) : showProbes ? (
                              <span className="text-cyan-400 text-[9px]">
                                RFC 3550 Probing
                              </span>
                            ) : (
                              <span className="text-slate-500 text-[9px]">
                                Detected
                              </span>
                            )}
                          </div>
                        </div>

                        {/* IP & Gateway Row */}
                        {showIpConfig && (
                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-1 text-[9px] text-slate-400 pt-1.5 mt-1 border-t border-slate-800/60">
                            <div>
                              <span className="text-slate-500">IPv4: </span>
                              <span className="text-slate-200 font-mono">
                                {iface.ipAddress}
                              </span>
                            </div>
                            <div>
                              <span className="text-slate-500">Gateway: </span>
                              <span className="text-slate-200 font-mono">
                                {iface.gateway}
                              </span>
                            </div>
                            <div>
                              <span className="text-slate-500">Mask: </span>
                              <span className="text-slate-300 font-mono">
                                {iface.netmask}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Wi-Fi Section */}
              {wifiInterfaces.length > 0 && (
                <div className="space-y-1">
                  {wifiInterfaces.map((iface) => {
                    const isOnline =
                      showActivePath &&
                      (iface.state === 'ONLINE' ||
                        state.activePath === iface.name);
                    return (
                      <div
                        key={iface.id}
                        className={`p-2 rounded-lg border transition-all duration-200 text-[10px] ${
                          isOnline
                            ? 'bg-emerald-950/20 border-emerald-700/60'
                            : 'bg-slate-900/70 border-slate-800/70'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                iface.linkState === 'Connected'
                                  ? 'bg-emerald-400'
                                  : 'bg-slate-600'
                              }`}
                            />
                            <span className="font-bold text-slate-200">
                              {iface.name}
                            </span>
                            <span className="px-1.5 py-0.5 bg-slate-800 rounded text-[9px] text-slate-400 uppercase font-semibold">
                              Wi-Fi
                            </span>
                            {showInterfaceValidation && (
                              <span className="text-slate-500 text-[9px]">
                                {iface.ssid !== 'N/A'
                                  ? `SSID: ${iface.ssid}`
                                  : iface.linkState}
                              </span>
                            )}
                          </div>

                          <div>
                            {showActivePath ? (
                              <span
                                className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                                  isOnline
                                    ? 'bg-emerald-900/80 text-emerald-300 border border-emerald-600/80'
                                    : 'bg-slate-800 text-slate-300 border border-slate-700'
                                }`}
                              >
                                {isOnline ? 'ONLINE (ACTIVE)' : 'READY'}
                              </span>
                            ) : showHealth ? (
                              <span className="text-emerald-400 text-[9px]">
                                Health Evaluated ✓
                              </span>
                            ) : showProbes ? (
                              <span className="text-cyan-400 text-[9px]">
                                RFC 3550 Probing
                              </span>
                            ) : (
                              <span className="text-slate-500 text-[9px]">
                                Detected
                              </span>
                            )}
                          </div>
                        </div>

                        {/* IP & SSID Row */}
                        {showIpConfig && (
                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-1 text-[9px] text-slate-400 pt-1.5 mt-1 border-t border-slate-800/60">
                            <div>
                              <span className="text-slate-500">IPv4: </span>
                              <span className="text-slate-200 font-mono">
                                {iface.ipAddress}
                              </span>
                            </div>
                            <div>
                              <span className="text-slate-500">SSID: </span>
                              <span className="text-cyan-300 font-mono">
                                {iface.ssid}
                              </span>
                            </div>
                            <div>
                              <span className="text-slate-500">Gateway: </span>
                              <span className="text-slate-200 font-mono">
                                {iface.gateway}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Other interfaces if any */}
              {otherInterfaces.length > 0 && (
                <div className="space-y-1">
                  {otherInterfaces.map((iface) => (
                    <div
                      key={iface.id}
                      className="p-2 rounded-lg bg-slate-900/50 border border-slate-800/60 text-[10px] flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-300">
                          {iface.name}
                        </span>
                        <span className="text-slate-500 text-[9px]">
                          ({iface.mediaType})
                        </span>
                      </div>
                      <span className="text-slate-400 text-[9px]">
                        {iface.ipAddress}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Outbound Route Status Row */}
              {showActivePath && state.activePath && (
                <div className="flex items-center justify-between text-[10px] text-slate-400 pt-2 border-t border-slate-800/80">
                  <div className="flex items-center gap-1.5">
                    <span className="text-slate-500">
                      Designated Outbound Path:
                    </span>
                    <span className="text-emerald-400 font-bold">
                      {state.activePath}
                    </span>
                    {state.defaultGateway && (
                      <span className="text-slate-500 text-[9px]">
                        via {state.defaultGateway}
                      </span>
                    )}
                  </div>
                  <span className="text-emerald-500/90 text-[9px] font-semibold">
                    Policy Engine Verified ✓
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* PROGRESS TRACK & STATUS */}
        <div className="w-full bg-[#080c14] border border-slate-800 rounded-xl p-4 shadow-2xl mb-3 text-left font-mono">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  state.isFailed
                    ? 'bg-rose-500 animate-pulse'
                    : state.isReady
                      ? 'bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.8)]'
                      : 'bg-emerald-400/80 animate-pulse'
                }`}
              />
              <span
                className={`text-xs font-bold ${
                  state.isFailed
                    ? 'text-rose-400'
                    : state.isReady
                      ? 'text-emerald-400'
                      : 'text-slate-200'
                }`}
              >
                {state.isReady
                  ? 'APP READY'
                  : state.isFailed
                    ? 'INITIALIZATION INCOMPLETE'
                    : state.statusText}
              </span>
            </div>
            <span
              className={`text-xs font-bold ${
                state.isFailed
                  ? 'text-rose-400'
                  : state.isReady
                    ? 'text-emerald-400'
                    : 'text-slate-300'
              }`}
            >
              {state.progress}%
            </span>
          </div>

          {/* Precision Track */}
          <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden p-0.5 border border-slate-800/80">
            <div
              className={`h-full rounded-full transition-all duration-150 ${
                state.isFailed
                  ? 'bg-rose-500 shadow-[0_0_12px_rgba(244,63,94,0.8)]'
                  : state.isReady
                    ? 'bg-emerald-400 shadow-[0_0_14px_rgba(16,185,129,0.9)]'
                    : 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.7)]'
              }`}
              style={{ width: `${state.progress}%` }}
            />
          </div>

          {/* Telemetry Footnote */}
          <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-400">
            <div>
              Actual Core Init:{' '}
              <span className="text-white font-bold">
                {state.actualInitMs !== null
                  ? `${state.actualInitMs}ms ✓ Authoritative`
                  : 'Measuring...'}
              </span>
            </div>
            <div>
              Splash Minimum Gate:{' '}
              <span className="text-emerald-400 font-bold">
                {state.minDurationMs}ms
              </span>
            </div>
            <div>
              Remaining Window:{' '}
              <span className="text-slate-300 font-bold">
                {state.remainingMs}ms
              </span>
            </div>
          </div>
        </div>

        {/* INCOMPLETE / ERROR RECOVERY CARD */}
        {state.isFailed && (
          <div className="w-full bg-rose-950/40 border border-rose-800/70 rounded-xl p-3.5 shadow-xl mb-3 text-left font-mono">
            <div className="flex items-start justify-between gap-3">
              <div className="text-xs text-rose-200">
                <div className="font-bold flex items-center gap-1.5 text-rose-300">
                  <span>⚠️</span>
                  <span>INITIALIZATION INCOMPLETE</span>
                </div>
                <p className="text-[11px] text-rose-300/80 mt-1">
                  {state.errorMessage ||
                    'Rust Core could not be contacted. Native routing table and hardware sockets require desktop runtime.'}
                </p>
              </div>
              {onRetry && (
                <button
                  type="button"
                  onClick={onRetry}
                  className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow-lg transition-colors whitespace-nowrap cursor-pointer"
                >
                  Retry Initialization
                </button>
              )}
            </div>
          </div>
        )}

        {/* INTERACTIVE SIMULATOR MODE BANNER */}
        {!state.isFailed && (
          <div className="w-full bg-slate-900/80 border border-slate-800 rounded-xl p-2.5 mb-3 text-left font-mono text-[11px] flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-400">
              <span className="text-base">🌐</span>
              <span>
                <strong className="text-slate-300">
                  Interactive Simulator Mode
                </strong>{' '}
                · Simulating deterministic multi-path network engine.
              </span>
            </div>
            {onSkip && (
              <button
                type="button"
                onClick={onSkip}
                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 font-semibold text-[10px] transition-colors"
              >
                Enter Cockpit →
              </button>
            )}
          </div>
        )}

        {/* Explanatory Note & Skip Tip */}
        <div className="flex flex-col items-center gap-1 text-[11px] text-slate-400 font-mono">
          <p className="text-slate-400">
            Controls minimum presentation duration. Does not affect network
            initialization.
          </p>
          <div className="flex items-center gap-2 mt-0.5 px-3 py-1 rounded-full bg-slate-900/80 border border-slate-800 text-[10px] text-slate-400">
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
