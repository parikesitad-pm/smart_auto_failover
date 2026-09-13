import React from 'react';
import {
  HeroSection,
  DesktopShowcase,
  DownloadHub,
  FeaturePillars,
  WhyAutoFailover,
  HowItWorks,
  FaqAccordion,
  LandingFooter,
} from './components/Landing';
import { Download, ExternalLink } from 'lucide-react';
import { useLatestRelease } from './hooks/useLatestRelease';

export const App: React.FC = () => {
  const { release } = useLatestRelease();

  const handleScrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-[#05070a] text-slate-100 antialiased font-sans selection:bg-cyan-500 selection:text-black flex flex-col">
      {/* Top Universal Navbar */}
      <header className="sticky top-0 z-50 bg-[#080b10]/90 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-8 py-3 flex items-center justify-between">
        <div
          className="flex items-center gap-3 cursor-pointer select-none"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        >
          <img
            src="/modula_3.0.png"
            alt="Modula 3.0"
            className="w-8 h-8 object-contain"
          />
          <div>
            <span className="font-extrabold tracking-tight text-white text-base">
              AUTO FAILOVER
            </span>
            <span className="ml-1.5 text-xs font-mono text-emerald-400 font-semibold">
              3.0
            </span>
            <span className="hidden sm:inline-block ml-2 text-xs text-slate-400 font-medium">
              by Modula
            </span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-300">
          <button
            onClick={() => handleScrollTo('showcase')}
            className="hover:text-emerald-400 transition-colors cursor-pointer"
          >
            Cockpit
          </button>
          <button
            onClick={() => handleScrollTo('features')}
            className="hover:text-emerald-400 transition-colors cursor-pointer"
          >
            Features
          </button>
          <button
            onClick={() => handleScrollTo('how-it-works')}
            className="hover:text-emerald-400 transition-colors cursor-pointer"
          >
            How It Works
          </button>
          <button
            onClick={() => handleScrollTo('downloads')}
            className="hover:text-emerald-400 transition-colors cursor-pointer"
          >
            Downloads
          </button>
          <a
            href={
              release?.htmlUrl ||
              'https://github.com/parikesitad-pm/smart_auto_failover/releases'
            }
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-emerald-400 transition-colors flex items-center gap-1 cursor-pointer"
          >
            Releases (
            {release ? `Beta: ${release.tagName}` : 'v3.0.0-preview.26'}
            )
            <ExternalLink className="w-3 h-3 text-slate-400" />
          </a>
        </nav>

        {/* Quick CTA */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => handleScrollTo('downloads')}
            className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold transition-all flex items-center gap-1.5 shadow-[0_0_15px_rgba(16,185,129,0.3)] cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            Download Beta {release ? `(${release.tagName})` : ''}
          </button>
        </div>
      </header>

      {/* Main Landing Surface */}
      <main className="flex-1">
        <HeroSection
          onScrollToDownloads={() => handleScrollTo('downloads')}
          onScrollToShowcase={() => handleScrollTo('showcase')}
          release={release}
        />
        <div id="showcase">
          <DesktopShowcase
            onScrollToDownloads={() => handleScrollTo('downloads')}
            release={release}
          />
        </div>
        <div id="features">
          <FeaturePillars />
        </div>
        <WhyAutoFailover />
        <div id="how-it-works">
          <HowItWorks />
        </div>
        <div id="downloads">
          <DownloadHub />
        </div>
        <FaqAccordion />
        <LandingFooter />
      </main>
    </div>
  );
};

export default App;
