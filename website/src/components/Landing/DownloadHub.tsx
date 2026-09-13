import React from 'react';
import {
  Download,
  Clock,
  ShieldCheck,
  ExternalLink,
  FileText,
  AlertCircle,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import { useLatestRelease } from '../../hooks/useLatestRelease';
import { PlatformReleaseInfo } from '../../types/releases';

export const DownloadHub: React.FC = () => {
  const { release, loading, isRefreshing, refresh } = useLatestRelease();

  const platforms: PlatformReleaseInfo[] = release
    ? Object.values(release.platforms)
    : [];

  return (
    <section
      id="downloads"
      className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-slate-800/80"
    >
      <div className="text-center max-w-3xl mx-auto mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold tracking-wider uppercase mb-4">
          <Sparkles className="w-3.5 h-3.5" />
          {release?.channel === 'STABLE'
            ? 'Stable Production Release'
            : release?.channel === 'BETA'
              ? 'Official Beta Release'
              : 'Live Preview Channel'}
        </div>

        <h2 className="text-3xl sm:text-5xl font-extrabold text-white mb-4 tracking-tight">
          Download AutoFailover 3.0 Beta
        </h2>
        <p className="text-slate-400 text-base sm:text-lg">
          Native desktop packages built independently on native runners.
          Real-time dynamic discovery via GitHub Releases.
        </p>

        {release && (
          <div className="mt-4 flex flex-col items-center gap-3">
            <div className="flex flex-wrap items-center justify-center gap-3 text-xs font-mono text-slate-400">
              <a
                href={
                  release.htmlUrl ||
                  `https://github.com/parikesitad-pm/smart_auto_failover/releases/tag/${release.tagName}`
                }
                target="_blank"
                rel="noopener noreferrer"
                title={`View ${release.tagName} on GitHub Releases`}
                className="px-3 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 hover:border-emerald-500/50 text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1.5 transition-all cursor-pointer group"
              >
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                <span>Beta • {release.tagName}</span>
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
                  release.htmlUrl ||
                  `https://github.com/parikesitad-pm/smart_auto_failover/releases/tag/${release.tagName}`
                }
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-300 hover:text-white underline hover:no-underline flex items-center gap-1 cursor-pointer"
              >
                {release.releaseTitle}
                <ExternalLink className="w-3 h-3 text-slate-500" />
              </a>
              {release.checksumsUrl && (
                <>
                  <span>•</span>
                  <a
                    href={release.checksumsUrl}
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

            <a
              href={
                release.htmlUrl ||
                `https://github.com/parikesitad-pm/smart_auto_failover/releases/tag/${release.tagName}`
              }
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-700 hover:border-emerald-500/50 text-slate-300 hover:text-white text-xs font-medium transition-all shadow-sm group cursor-pointer"
            >
              <span>
                GitHub Beta Release: <strong>{release.tagName}</strong>
              </span>
              <ExternalLink className="w-3.5 h-3.5 text-cyan-400 group-hover:translate-x-0.5 transition-transform" />
            </a>
          </div>
        )}
      </div>

      {loading ? (
        <div className="text-center py-16">
          <div className="inline-block w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-slate-400 text-sm">
            Discovering latest builds from GitHub...
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
                      Download Beta ({p.platformName.split(' ')[0]})
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

      {/* Security & Integrity Disclosure */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-400">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-slate-200 block mb-1">
              SHA-256 Checksum Verification
            </strong>
            Every build produces an authoritative checksum file
            (`SHA256SUMS.txt`). Verify downloaded packages against the published
            cryptographic hash before installation.
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-slate-200 block mb-1">
              Unsigned Beta Notice
            </strong>
            Beta builds are not yet Authenticode or Apple Notarized. Operating
            systems may prompt standard unknown publisher alerts. Full code
            signing will accompany the stable release.
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
