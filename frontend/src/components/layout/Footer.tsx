import React from 'react';
import { useTranslation } from 'react-i18next';
import { ExternalLink, ShieldCheck } from 'lucide-react';

export const Footer: React.FC = () => {
  const { t } = useTranslation();

  return (
    <footer className="bg-slate-900 text-slate-400 text-xs py-8 border-t border-slate-800 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>KisanSathi Rajasthan • Final-Year Academic Capstone Project</span>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-4 text-slate-300">
            <a
              href="https://krishi.rajasthan.gov.in"
              target="_blank"
              rel="noreferrer"
              className="hover:text-white inline-flex items-center gap-1 transition-colors"
            >
              <span>कृषि विभाग राजस्थान</span>
              <ExternalLink className="w-3 h-3" />
            </a>
            <span>•</span>
            <a
              href="https://agmarknet.gov.in"
              target="_blank"
              rel="noreferrer"
              className="hover:text-white inline-flex items-center gap-1 transition-colors"
            >
              <span>Agmarknet Mandi Portal</span>
              <ExternalLink className="w-3 h-3" />
            </a>
            <span>•</span>
            <span className="text-emerald-400 font-mono">v0.1.0-scaffold</span>
          </div>
        </div>

        <div className="text-center mt-4 text-[11px] text-slate-500">
          {t('disclaimer')}
        </div>
      </div>
    </footer>
  );
};
