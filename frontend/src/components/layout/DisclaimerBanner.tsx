import React from 'react';
import { useTranslation } from 'react-i18next';
import { AlertCircle } from 'lucide-react';

export const DisclaimerBanner: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="bg-emerald-50 border-y border-emerald-200 py-1.5 px-4 text-center text-xs text-emerald-800 flex items-center justify-center gap-1.5">
      <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 text-emerald-600" />
      <span>{t('disclaimer')}</span>
    </div>
  );
};
