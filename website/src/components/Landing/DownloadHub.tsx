import React, { useState } from 'react';
import {
  Download,
  Clock,
  ShieldCheck,
  ExternalLink,
  FileText,
  AlertCircle,
  Sparkles,
  RefreshCw,
  Archive,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useLatestRelease } from '../../hooks/useLatestRelease';
import { PlatformReleaseInfo, ResolvedRelease } from '../../types/releases';

export const DownloadHub: React.FC = () => {
  const { release: latestRelease, releasesHistory, loading, isRefreshing, refresh } = useLatestRelease();
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [showArchiveTable, setShowArchiveTable] = useState(false);

  // Active displayed release: either selected by user or latest release
  const activeRelease: ResolvedRelease | null = selectedTag
    ? releasesHistory.find((r) => r.tagName === selectedTag) || latestRelease
    : latestRelease;

  const platforms: PlatformReleaseInfo[] = activeRelease
    ? Object.values(activeRelease.platforms)
    : [];

  return (
    <section
      id="downloads"
      className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-slate-800/80"
    >
      <div className="text-center max-w-3xl mx-auto mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold tracking-wider uppercase mb-4">
          <Sparkles className="w-3.5 h-3.5" />
          {activeRelease?.channel === 'STABLE'
            ? 'Stable Production Release'
            : activeRelease?.channel === 'BETA'
              ? 'Official Beta Release'
              : 'Release Archive / Preview Channel'}
        </div>

        <h2 className="text-3xl sm:text-5xl font-extrabold text-white mb-4 tracking-tight">
          Download AutoFailover {activeRelease ? activeRelease.tagName.replace(/^v/, '') : '3.1.0'}
        </h2>
        <p className="text-slate-400 text-base sm:text-lg">
          Native standalone desktop packages for Windows, Linux, and macOS.
          Choose your target version or explore verified previous releases below.
        </p>

        {/* Release Meta Bar */}
        {activeRelease && (
          <div className="mt-4 flex flex-col items-center gap-3">
            <div className="flex flex-wrap items-center justify-center gap-3 text-xs font-mono text-slate-400">
              <a
                href={
                  activeRelease.htmlUrl ||
                  `https://github.com/parikesitad-pm/smart_auto_failover/releases/tag/${activeRelease.tagName}`
                }
                target="_blank"
                rel="noopener noreferrer"
                title={`View ${activeRelease.tagName} on GitHub Releases`}
                className="px-3 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 hover:border-emerald-500/50 text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1.5 transition-all cursor-pointer group"
              >
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                <span>
                  {activeRelease.channel === 'STABLE'
                    ? 'Stable'
                    : activeRelease.channel === 'BETA'
                      ? 'Beta'
                      : 'Preview'}{' '}
                  • {activeRelease.tagName}
                </span>
                <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-emerald-400 transition-colors" />
              </a>
              <button
                onClick={refresh}
                disabled={isRefreshing}
                title="Check for latest releases on GitHub"
                className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-400 hover:text-emerald-400 transition-all cursor-pointer flex items-center gap-1"
              >
                <RefreshCw
                  className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`}
                />
                <span className="text-[10px] hidden sm:inline">Refresh</span>
              </button>
              <span>•</span>
              <a
                href={
                  activeRelease.htmlUrl ||
                  `https://github.com/parikesitad-pm/smart_auto_failover/releases/tag/${activeRelease.tagName}`
                }
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-300 hover:text-white underline hover:no-underline flex items-center gap-1 cursor-pointer"
              >
                {activeRelease.releaseTitle}
                <ExternalLink className="w-3 h-3 text-slate-500" />
              </a>
              {activeRelease.checksumsUrl && (
                <>
                  <span>•</span>
                  <a
                    href={activeRelease.checksumsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 underline cursor-pointer"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    SHA256SUMS.txt
                  </a>
                </>
              )}
            </div>

            {/* Version switcher pills */}
            <div className="w-full max-w-2xl mt-4 p-1.5 rounded-2xl bg-[#090e17] border border-slate-800 flex flex-wrap items-center justify-center gap-1 sm:gap-2">
              <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 px-2 py-1 flex items-center gap-1.5">
                <Archive className="w-3.5 h-3.5 text-cyan-400" />
                Select Version:
              </span>
              {releasesHistory.slice(0, 5).map((r) => {
                const isSelected =
                  (selectedTag === null && r.tagName === latestRelease?.tagName) ||
                  selectedTag === r.tagName;
                const isBeta = r.channel === 'BETA' || r.tagName.includes('preview.26');
                const isLatest = r.tagName === latestRelease?.tagName;

                return (
                  <button
                    key={r.tagName}
                    onClick={() => setSelectedTag(r.tagName)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-mono font-medium transition-all cursor-pointer flex items-center gap-1.5 ${
                      isSelected
                        ? 'bg-emerald-500 text-slate-950 font-bold shadow-[0_0_12px_rgba(16,185,129,0.3)]'
                        : 'bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <span>{r.tagName}</span>
                    {isLatest && (
                      <span className={`text-[9px] px-1 py-0.2 rounded uppercase font-extrabold ${isSelected ? 'bg-slate-950 text-emerald-300' : 'bg-emerald-500/20 text-emerald-400'}`}>
                        Latest
                      </span>
                    )}
                    {isBeta && !isLatest && (
                      <span className={`text-[9px] px-1 py-0.2 rounded uppercase font-extrabold ${isSelected ? 'bg-slate-950 text-cyan-300' : 'bg-cyan-500/20 text-cyan-400'}`}>
                        Beta
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {loading ? (
        <div className="text-center py-16">
          <div className="inline-block w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-slate-400 text-sm">
            Discovering releases from GitHub...
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {platforms.map((p) => {
            const isRec = p.isRecommended;
            return (
              <div
                key={p.platformId}
                className={`flex flex-col justify-between p-6 rounded-2xl bg-gradient-to-b from-[#0e1626] to-[#080b10] border transition-all shadow-xl relative overflow-hidden group ${
                  isRec
                    ? 'border-emerald-500/50 shadow-[0_0_25px_rgba(16,185,129,0.15)] ring-1 ring-emerald-500/30'
                    : 'border-slate-800 hover:border-slate-700'
                }`}
              >
                {/* Recommended Badge */}
                {isRec && (
                  <div className="absolute top-0 right-0 bg-emerald-500 text-slate-950 text-[10px] font-extrabold uppercase px-3 py-1 rounded-bl-xl tracking-wider">
                    Detected OS
                  </div>
                )}

                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xl font-bold text-white group-hover:text-emerald-400 transition-colors">
                      {p.platformName}
                    </h3>
                  </div>

                  <div className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider bg-slate-900 border border-slate-800 text-slate-300 mb-3">
                    {p.validationStatus}
                  </div>

                  <div className="text-xs font-mono text-cyan-400 mb-2">
                    {p.arch}
                  </div>

                  <p className="text-xs text-slate-400 mb-4 leading-relaxed">
                    {p.description}
                  </p>

                  <div className="p-2.5 rounded-lg bg-black/40 border border-slate-800/80 mb-6">
                    <span className="text-[10px] text-slate-500 font-mono block truncate">
                      {p.assetName}
                    </span>
                    {p.sizeFormatted && (
                      <span className="text-[10px] text-emerald-400 font-mono block mt-1">
                        Size: {p.sizeFormatted}
                      </span>
                    )}
                  </div>
                </div>

                {/* Bottom Button */}
                <div>
                  {p.available && p.downloadUrl ? (
                    <a
                      href={p.downloadUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full py-3 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-[0_0_18px_rgba(16,185,129,0.25)] transition-all flex items-center justify-center gap-2 cursor-pointer"
                    >
                      <Download className="w-3.5 h-3.5" />
                      Download {activeRelease?.tagName} ({p.platformName.split(' ')[0]})
                      <ExternalLink className="w-3 h-3 opacity-70" />
                    </a>
                  ) : (
                    <button
                      disabled
                      className="w-full py-3 px-4 rounded-xl bg-slate-800/50 border border-slate-700 text-slate-500 font-medium text-xs flex items-center justify-center gap-2 cursor-not-allowed"
                    >
                      <Clock className="w-3.5 h-3.5" />
                      Build Unavailable
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Multi-Version Archive Matrix Accordion */}
      <div className="mb-12 p-6 rounded-2xl bg-[#090d15] border border-slate-800/90 shadow-xl">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Archive className="w-5 h-5 text-emerald-400" />
              Download Another Version (Last 5 Releases)
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Direct access from latest release down to Build 3.0.0 Preview 24.
              All artifacts are multi-platform verified.
            </p>
          </div>
          <button
            onClick={() => setShowArchiveTable((prev) => !prev)}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 hover:text-white flex items-center gap-2 transition-all cursor-pointer"
          >
            {showArchiveTable ? (
              <>
                <span>Hide Archive Table</span>
                <ChevronUp className="w-4 h-4 text-emerald-400" />
              </>
            ) : (
              <>
                <span>View Full Matrix (5 Releases)</span>
                <ChevronDown className="w-4 h-4 text-cyan-400" />
              </>
            )}
          </button>
        </div>

        {showArchiveTable && (
          <div className="mt-6 overflow-x-auto">
            <table className="w-full text-left text-xs font-mono border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                  <th className="py-3 px-4">Release / Tag</th>
                  <th className="py-3 px-4">Channel</th>
                  <th className="py-3 px-4">Windows (x64)</th>
                  <th className="py-3 px-4">Linux (x86_64)</th>
                  <th className="py-3 px-4">macOS (Apple Silicon)</th>
                  <th className="py-3 px-4">macOS (Intel)</th>
                  <th className="py-3 px-4">Verification</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {releasesHistory.slice(0, 5).map((r) => {
                  const isCur = r.tagName === latestRelease?.tagName;
                  return (
                    <tr
                      key={r.tagName}
                      className={`hover:bg-slate-900/40 transition-colors ${
                        selectedTag === r.tagName ? 'bg-emerald-500/5' : ''
                      }`}
                    >
                      <td className="py-3 px-4 font-bold text-white flex items-center gap-2">
                        <span>{r.tagName}</span>
                        {isCur && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-sans font-bold">
                            Current
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                            r.channel === 'STABLE'
                              ? 'bg-emerald-500/20 text-emerald-400'
                              : r.channel === 'BETA'
                                ? 'bg-cyan-500/20 text-cyan-400'
                                : 'bg-slate-800 text-slate-300'
                          }`}
                        >
                          {r.channel}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <a
                          href={r.platforms.windows.downloadUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-emerald-400 hover:text-emerald-300 underline inline-flex items-center gap-1"
                        >
                          <Download className="w-3 h-3" />
                          .zip
                        </a>
                      </td>
                      <td className="py-3 px-4">
                        <a
                          href={r.platforms.linux.downloadUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-cyan-400 hover:text-cyan-300 underline inline-flex items-center gap-1"
                        >
                          <Download className="w-3 h-3" />
                          .tar.gz
                        </a>
                      </td>
                      <td className="py-3 px-4">
                        <a
                          href={r.platforms['macos-arm64'].downloadUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-emerald-400 hover:text-emerald-300 underline inline-flex items-center gap-1"
                        >
                          <Download className="w-3 h-3" />
                          arm64 .dmg
                        </a>
                      </td>
                      <td className="py-3 px-4">
                        <a
                          href={r.platforms['macos-x64'].downloadUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-slate-300 hover:text-white underline inline-flex items-center gap-1"
                        >
                          <Download className="w-3 h-3" />
                          x64 .dmg
                        </a>
                      </td>
                      <td className="py-3 px-4">
                        {r.checksumsUrl ? (
                          <a
                            href={r.checksumsUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-slate-400 hover:text-cyan-400 flex items-center gap-1 underline text-[11px]"
                          >
                            <FileText className="w-3 h-3" />
                            SHA-256
                          </a>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Security & Integrity Disclosure */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-400">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-slate-200 block mb-1">
              Authoritative SHA-256 Checksum Verification
            </strong>
            Every build produces an authoritative checksum file
            (`SHA256SUMS.txt`). Verify downloaded packages against the published
            cryptographic hash before deployment.
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-slate-200 block mb-1">
              Kernel Safety & Architecture Notice
            </strong>
            AutoFailover operates via standard Layer-3 routing metrics. It requires
            no proprietary network filter drivers, ensuring zero kernel instability
            or BSOD risk on Windows, macOS, and Linux.
          </div>
        </div>
      </div>

      <div className="text-center mt-8">
        <a
          href="https://github.com/parikesitad-pm/smart_auto_failover/releases"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs font-mono text-cyan-400 hover:text-cyan-300 underline inline-flex items-center gap-1.5"
        >
          View all releases and build logs on GitHub
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </section>
  );
};

