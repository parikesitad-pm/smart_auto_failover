import React, { useState } from 'react';
import { useStartupSequence } from './hooks/useStartupSequence';
import { SplashScreen, SplashSettingsModal } from './components/Splash';
import { Cockpit } from './components/Cockpit';

export const App: React.FC = () => {
  const {
    state,
    config,
    runStartup,
    setPreset,
    setCustomDuration,
    setEngineSpeed,
    setSkipEnabled,
  } = useStartupSequence();

  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#05070a] text-slate-100 antialiased p-3 font-sans selection:bg-cyan-500 selection:text-black flex flex-col justify-center">
      {/* Intentional Startup Splash Presentation (Decoupled Engine) */}
      <SplashScreen state={state} />

      {/* Main Digital Network Cockpit */}
      <Cockpit onOpenStartupModal={() => setIsModalOpen(true)} />

      {/* Presentation Delay & Settings Modal */}
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
  );
};

export default App;
