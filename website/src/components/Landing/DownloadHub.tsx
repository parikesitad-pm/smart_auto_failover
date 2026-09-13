import { Download, Clock, ShieldCheck, ExternalLink } from 'lucide-react';

export const DownloadHub: React.FC = () => {
  const platforms = [
    {
      id: 'linux',
      name: 'Linux',
      arch: 'x86_64 / glibc 2.31+',
      version: 'Auto Failover 3.0.0',
      artifactName: 'Auto Failover 3.0.0-linux-x86_64.tar.gz',
      status: 'REAL-HOST VALIDATED',
      statusType: 'validated',
      badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      downloadUrl: 'https://github.com/parikesitad-pm/smart_auto_failover/releases',
      enabled: true,
      description: 'Tested on physical hardware (Manjaro / Arch / Ubuntu). Uses native Netlink & sysfs.',
    },
    {
      id: 'windows',
      name: 'Windows',
      arch: 'x64 (Windows 10 / 11)',
      version: 'Auto Failover 3.0.0',
      artifactName: 'Auto-Failover-3.0.0-Setup.exe',
      status: 'VALIDATION PENDING',
      statusType: 'pending',
      badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      downloadUrl: 'https://github.com/parikesitad-pm/smart_auto_failover/releases',
      enabled: true,
      description: 'Native PowerShell NetTCPIP & netsh HAL implementation. Real-host physical verification pending.',
    },
    {
      id: 'macos',
      name: 'macOS',
      arch: 'Universal (Apple Silicon & Intel)',
      version: 'Auto Failover 3.0.0',
      artifactName: 'Auto-Failover-3.0.0-macOS.dmg',
      status: 'COMING SOON',
      statusType: 'soon',
      badgeColor: 'bg-slate-700/30 text-slate-400 border-slate-700',
      downloadUrl: '#',
      enabled: false,
      description: 'Native networksetup & BSD route HAL. Target packaging in progress.',
    },
  ];

  return (
    <section id="downloads" className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-slate-800/80">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
          Download AutoFailover 3.0
        </h2>
        <p className="text-slate-400 text-base sm:text-lg">
          Native binaries built directly on native runners. Honest platform statuses with no fake verification badges.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
        {platforms.map((p) => (
          <div
            key={p.id}
            className="flex flex-col justify-between p-6 rounded-2xl bg-gradient-to-b from-[#0e1626] to-[#080b10] border border-slate-800 hover:border-slate-700 transition-all shadow-xl relative overflow-hidden group"
          >
            {/* Top Bar */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-2xl font-bold text-white group-hover:text-emerald-400 transition-colors">
                  {p.name}
                </h3>
                <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wider border ${p.badgeColor}`}>
                  {p.status}
                </span>
              </div>

              <div className="text-xs font-mono text-cyan-400 mb-2">
                {p.version} • {p.arch}
              </div>

              <p className="text-sm text-slate-400 mb-6 leading-relaxed">
                {p.description}
              </p>

              <div className="p-3 rounded-lg bg-black/40 border border-slate-800/80 mb-6">
                <span className="text-[11px] text-slate-500 font-mono block truncate">
                  Artifact: {p.artifactName}
                </span>
              </div>
            </div>

            {/* Bottom Button */}
            <div>
              {p.enabled ? (
                <a
                  href={p.downloadUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full py-3.5 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm shadow-[0_0_20px_rgba(16,185,129,0.25)] transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  <Download className="w-4 h-4" />
                  Download for {p.name}
                  <ExternalLink className="w-3.5 h-3.5 opacity-70" />
                </a>
              ) : (
                <button
                  disabled
                  className="w-full py-3.5 px-4 rounded-xl bg-slate-800/50 border border-slate-700 text-slate-500 font-medium text-sm flex items-center justify-center gap-2 cursor-not-allowed"
                >
                  <Clock className="w-4 h-4" />
                  Coming Soon
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Verification Notice */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start sm:items-center gap-3 text-xs text-slate-400">
        <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5 sm:mt-0" />
        <p>
          <strong className="text-slate-200">Strict Traceability Policy:</strong> All release artifacts are signed and accompanied by SHA-256 checksums in the GitHub Release ledger. Builds are never labeled as PRODUCTION READY without physical hardware host validation.
        </p>
      </div>
    </section>
  );
};
