import React from 'react';
import { useTranslation } from 'react-i18next';
import { useOffline } from '../../context/OfflineContext';
import { WifiOff, RefreshCw } from 'lucide-react';

export const OfflineBanner: React.FC = () => {
  const { isOnline, pendingQueue, flushQueue } = useOffline();
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  if (isOnline && pendingQueue.length === 0) {
    return null;
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className="bg-amber-600 text-white px-4 py-2.5 text-sm font-medium flex items-center justify-between shadow-md"
    >
      <div className="flex items-center space-x-2">
        <WifiOff className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
        <span>
          {!isOnline
            ? isHi
              ? 'आप ऑफलाइन हैं। सुरक्षित पुराना डेटा दिखाया जा रहा है।'
              : 'You are offline. Showing cached agricultural advisory.'
            : isHi
            ? 'नेटवर्क वापस आ गया है!'
            : 'Back online!'}
          {pendingQueue.length > 0 && (
            <span className="ml-2 font-bold bg-amber-800 px-2 py-0.5 rounded text-xs">
              {isHi
                ? `${pendingQueue.length} संदेश कतार में हैं`
                : `${pendingQueue.length} message(s) queued`}
            </span>
          )}
        </span>
      </div>

      {isOnline && pendingQueue.length > 0 && (
        <button
          onClick={() => flushQueue()}
          aria-label={isHi ? 'कतारबद्ध संदेश भेजें' : 'Send queued messages'}
          className="flex items-center space-x-1 bg-white text-amber-900 px-3 py-1 rounded text-xs font-bold hover:bg-amber-50 active:scale-95 transition focus:outline-none focus:ring-2 focus:ring-white"
        >
          <RefreshCw className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
          <span>{isHi ? 'अभी भेजें' : 'Sync Now'}</span>
        </button>
      )}
    </div>
  );
};
