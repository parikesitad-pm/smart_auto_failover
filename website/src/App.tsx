import React, { useState } from 'react';
import { useStartupSequence } from './hooks/useStartupSequence';
import { SplashScreen, SplashSettingsModal } from './components/Splash';
import { Cockpit } from './components/Cockpit';
import {
  HeroSection,
  DownloadHub,
  FeaturePillars,
  WhyAutoFailover,
  HowItWorks,
  FaqAccordion,
  LandingFooter,
} from './components/Landing';
import { Globe, MonitorPlay, Download } from 'lucide-react';

type ViewMode = 'landing' | 'cockpit';

export const App: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('landing');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const {
    state,
    config,
    skipStartup,
    runStartup,
    setPreset,
    setCustomDuration,
    setEngineSpeed,
    setSkipEnabled,
  } = useStartupSequence();

  const handleLaunchSimulator = () => {
    setViewMode('cockpit');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleScrollToDownloads = () => {
    if (viewMode !== 'landing') {
      setViewMode('landing');
      setTimeout(() => {
        document
          .getElementById('downloads')
          ?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } else {
      document
        .getElementById('downloads')
        ?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-[#05070a] text-slate-100 antialiased font-sans selection:bg-cyan-500 selection:text-black flex flex-col">
      {/* Top Universal Navbar */}
      <header className="sticky top-0 z-50 bg-[#080b10]/90 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-8 py-3 flex items-center justify-between">
        <div
          className="flex items-center gap-3 cursor-pointer select-none"
          onClick={() => setViewMode('landing')}
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
              3.0.0
            </span>
          </div>
        </div>

        {/* View Surface Switcher */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-900/80 rounded-xl border border-slate-800">
          <button
            onClick={() => setViewMode('landing')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
              viewMode === 'landing'
                ? 'bg-emerald-500 text-slate-950 shadow-[0_0_15px_rgba(16,185,129,0.3)]'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            Landing Page
          </button>

          <button
            onClick={() => setViewMode('cockpit')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
              viewMode === 'cockpit'
                ? 'bg-cyan-500 text-slate-950 shadow-[0_0_15px_rgba(6,182,212,0.3)]'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <MonitorPlay className="w-3.5 h-3.5" />
            Live Preview
          </button>
        </div>

        {/* Quick CTA */}
        <div className="hidden sm:flex items-center gap-3">
          <button
            onClick={handleScrollToDownloads}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-bold transition-all flex items-center gap-1.5 border border-slate-700 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-emerald-400" />
            Download v3.0.0
          </button>
        </div>
      </header>

      {/* Main Surface Content */}
      <main className="flex-1">
        {viewMode === 'landing' ? (
          <div>
            <HeroSection
              onLaunchSimulator={handleLaunchSimulator}
              onScrollToDownloads={handleScrollToDownloads}
            />
            <FeaturePillars />
            <WhyAutoFailover />
            <HowItWorks />
            <DownloadHub />
            <FaqAccordion />
            <LandingFooter />
          </div>
        ) : (
          <div className="p-3 sm:p-6 flex flex-col justify-center max-w-7xl mx-auto">
            {/* Startup Splash Gate */}
            <SplashScreen
              state={state}
              onRetry={runStartup}
              onSkip={skipStartup}
            />

            {/* Digital Network Cockpit */}
            {!state.isActive && (
              <Cockpit onOpenStartupModal={() => setIsModalOpen(true)} />
            )}

            {/* Settings & Presentation Modal */}
            <SplashSettingsModal
              isOpen={isModalOpen}
              onClose={() => setIsModalOpen(false)}
              config={config}
              onSetPreset={setPreset}
              onSetCustomDuration={setCustomDuration}
              onSetEngineSpeed={setEngineSpeed}
              onSetSkipEnabled={setSkipEnabled}
              onReplay={runStartup}
            />
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
