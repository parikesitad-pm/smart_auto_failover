import { Video, Radio, Sparkles } from 'lucide-react';

export const WhyAutoFailover: React.FC = () => {
  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-slate-800/80">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold tracking-wider uppercase mb-6">
            Realistic Engineering Discipline
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-6 leading-tight">
            Why AutoFailover Exists: <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
              Protection Without False Guarantees
            </span>
          </h2>
          <p className="text-slate-300 text-base sm:text-lg mb-6 leading-relaxed">
            Many network tools promise "unconditional zero packet drop" across
            physical adapters. In reality, switching Layer-3 default routes
            changes the source IP address and NAT state—unpredictable for
            stateful TCP sessions.
          </p>
          <p className="text-slate-400 text-sm sm:text-base mb-8 leading-relaxed">
            AutoFailover is built on honesty: our mission is to{' '}
            <strong className="text-white">
              maximize the probability of uninterrupted continuity
            </strong>{' '}
            for UDP-based real-time video conference and livestreaming
            applications.
          </p>

          <div className="space-y-4">
            <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <Video className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-bold text-white mb-1">
                  Video Conference Defense
                </h4>
                <p className="text-xs text-slate-400">
                  Zoom, Microsoft Teams, and Google Meet use adaptive UDP. By
                  switching before the active connection completely drops, audio
                  and video buffers hold intact without meeting disconnection.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <Radio className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-bold text-white mb-1">
                  Live Broadcast Protection
                </h4>
                <p className="text-xs text-slate-400">
                  OBS Studio, vMix, and Streamlabs benefit from immediate path
                  promotion when primary WAN jitter exceeds safety bounds,
                  preventing stream bitrate crashes.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="p-8 rounded-3xl bg-gradient-to-br from-[#0c1422] to-[#06080d] border border-slate-800 shadow-2xl relative">
          <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-400" />
            The Failure Priority Hierarchy
          </h3>

          <ol className="space-y-4 font-mono text-xs">
            <li className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
                1
              </span>
              <span>Preserve a healthy active path above all else.</span>
            </li>
            <li className="p-3.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold">
                2
              </span>
              <span>Detect micro-degradations early via RFC 3550 jitter.</span>
            </li>
            <li className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold">
                3
              </span>
              <span>Avoid unnecessary switching for momentary noise.</span>
            </li>
            <li className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center font-bold">
                4
              </span>
              <span>If active path becomes unusable, fail over instantly.</span>
            </li>
            <li className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700 text-slate-300 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-slate-700 text-slate-300 flex items-center justify-center font-bold">
                5
              </span>
              <span>
                Recover and re-evaluate without preemption oscillation.
              </span>
            </li>
          </ol>
        </div>
      </div>
    </section>
  );
};
