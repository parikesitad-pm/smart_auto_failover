import { Github } from 'lucide-react';

export const LandingFooter: React.FC = () => {
  return (
    <footer className="py-12 px-4 sm:px-6 lg:px-8 border-t border-slate-800/80 bg-[#05070a] text-slate-500 text-xs">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-3">
          <img src="/modula_3.0.png" alt="Modula 3.0" className="w-6 h-6 object-contain" />
          <span className="font-bold text-slate-300">AutoFailover 3.0 by Modula</span>
          <span className="text-slate-600">|</span>
          <span>light seamless and usefull</span>
        </div>

        <div className="flex items-center gap-6">
          <span className="text-slate-400">
            Crafted by <strong className="text-slate-300">parikesitad-pm</strong>
          </span>
          <span className="text-slate-600">|</span>
          <span>MIT License © 2026</span>
          <span className="text-slate-600">|</span>
          <a
            href="https://github.com/parikesitad-pm/smart_auto_failover"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-slate-400 hover:text-emerald-400 transition-colors"
          >
            <Github className="w-4 h-4" />
            GitHub
          </a>
        </div>
      </div>
    </footer>
  );
};
