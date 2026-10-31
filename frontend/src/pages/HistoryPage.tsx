import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  History,
  MessageSquare,
  Sparkles,
  BookOpen,
  Filter,
  RefreshCw,
  Clock,
} from 'lucide-react';
import { getHistory } from '../services/api';
import { useOffline } from '../context/OfflineContext';
import { FeedbackButtons } from '../components/common/FeedbackButtons';
import type { HistoryItem } from '../types';

export const HistoryPage: React.FC = () => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';
  const { cacheData, getCachedData } = useOffline();

  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterIntent, setFilterIntent] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);

  const CACHE_KEY = 'kisansathi_cached_history';

  const loadHistory = async () => {
    setLoading(true);
    setError(null);

    // Load from cache first for immediate responsiveness
    const cached = getCachedData<HistoryItem[]>(CACHE_KEY);
    if (cached && cached.length > 0) {
      setItems(cached);
    }

    try {
      const data = await getHistory(50, 0);
      setItems(data);
      cacheData(CACHE_KEY, data);
    } catch (err) {
      console.warn('Failed to fetch remote history:', err);
      if (!cached || cached.length === 0) {
        setError(
          isHi
            ? 'इतिहास लोड नहीं हो सका। कृपया नेटवर्क जांचें।'
            : 'Could not load history. Please verify your connection.'
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const filteredItems = items.filter((item) => {
    if (filterIntent === 'all') return true;
    return item.intent === filterIntent;
  });

  const getIntentColor = (intent: string) => {
    switch (intent) {
      case 'disease':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'weather':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'price':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'yield':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-purple-100 text-purple-800 border-purple-200';
    }
  };

  const getIntentLabel = (intent: string) => {
    if (isHi) {
      switch (intent) {
        case 'disease':
          return 'रोग जांच';
        case 'weather':
          return 'मौसम सलाह';
        case 'price':
          return 'मंडी भाव';
        case 'yield':
          return 'उपज अनुमान';
        default:
          return 'कृषि परामर्श';
      }
    }
    return intent.toUpperCase();
  };

  return (
    <div className="max-w-3xl mx-auto my-6 px-4 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-primary-100 text-primary-800 flex items-center justify-center shadow-sm">
            <History className="w-6 h-6" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900">
              {isHi ? 'परामर्श इतिहास' : 'Advisory History'}
            </h1>
            <p className="text-xs text-slate-500">
              {isHi
                ? 'आपके पूछे गए प्रश्न, एआई उत्तर एवं वैज्ञानिक संदर्भ'
                : 'Timeline of your agricultural queries, AI advice & university citations'}
            </p>
          </div>
        </div>

        <button
          onClick={loadHistory}
          disabled={loading}
          aria-label={isHi ? 'इतिहास रीफ्रेश करें' : 'Refresh history'}
          className="self-start sm:self-auto flex items-center space-x-1.5 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-2 rounded-xl transition focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} aria-hidden="true" />
          <span>{isHi ? 'रीफ्रेश' : 'Refresh'}</span>
        </button>
      </div>

      {/* Filter Chips */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1" role="toolbar" aria-label="Filter queries by intent">
        <Filter className="w-4 h-4 text-slate-400 flex-shrink-0" aria-hidden="true" />
        {[
          { key: 'all', label: isHi ? 'सभी' : 'All' },
          { key: 'disease', label: isHi ? 'रोग' : 'Disease' },
          { key: 'weather', label: isHi ? 'मौसम' : 'Weather' },
          { key: 'price', label: isHi ? 'भाव' : 'Price' },
          { key: 'yield', label: isHi ? 'उपज' : 'Yield' },
          { key: 'general', label: isHi ? 'सामान्य' : 'General' },
        ].map((f) => (
          <button
            key={f.key}
            onClick={() => setFilterIntent(f.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition focus:outline-none focus:ring-2 focus:ring-primary-500 ${
              filterIntent === f.key
                ? 'bg-primary-600 text-white shadow-sm'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Timeline Items */}
      {loading && items.length === 0 ? (
        <div className="py-12 text-center text-xs text-slate-500 animate-pulse">
          {isHi ? 'इतिहास लोड हो रहा है...' : 'Loading history records...'}
        </div>
      ) : error && items.length === 0 ? (
        <div className="p-4 bg-amber-50 text-amber-800 rounded-xl border border-amber-200 text-xs">
          {error}
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="bg-white rounded-2xl p-10 text-center border border-slate-200 text-slate-500">
          <MessageSquare className="w-10 h-10 mx-auto text-slate-300 mb-2" aria-hidden="true" />
          <p className="text-sm font-medium text-slate-700">
            {isHi ? 'कोई इतिहास रिकॉर्ड नहीं मिला' : 'No queries found in this category'}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            {isHi
              ? 'सलाहकार चैट या रोग पहचान में प्रश्न पूछने पर रिकॉर्ड यहाँ जुड़ेंगे।'
              : 'Interact with Advisor Chat or Crop Diagnosis to see your queries here.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredItems.map((item) => (
            <article
              key={item.id}
              className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-3 transition hover:shadow-md"
            >
              {/* Intent & Timestamp Header */}
              <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2.5">
                <div className="flex items-center space-x-2">
                  <span
                    className={`text-[11px] font-bold px-2 py-0.5 rounded-md border ${getIntentColor(
                      item.intent
                    )}`}
                  >
                    {getIntentLabel(item.intent)}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">
                    {item.model_version}
                  </span>
                </div>
                <div className="flex items-center text-[11px] text-slate-400 space-x-1">
                  <Clock className="w-3.5 h-3.5" aria-hidden="true" />
                  <time dateTime={item.created_at}>
                    {new Date(item.created_at).toLocaleString(
                      isHi ? 'hi-IN' : 'en-IN',
                      { dateStyle: 'medium', timeStyle: 'short' }
                    )}
                  </time>
                </div>
              </div>

              {/* Question */}
              <div className="flex items-start gap-2 text-slate-900 font-semibold text-sm">
                <span className="text-primary-600 font-bold" aria-hidden="true">
                  Q:
                </span>
                <p>{item.question}</p>
              </div>

              {/* Answer */}
              <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100 text-xs text-slate-700 leading-relaxed space-y-2">
                <div className="flex items-center gap-1.5 text-primary-700 font-semibold text-[11px]">
                  <Sparkles className="w-3.5 h-3.5" aria-hidden="true" />
                  <span>{isHi ? 'सलाहकार का उत्तर:' : 'Advisor Guidance:'}</span>
                </div>
                <p className="whitespace-pre-line">{item.answer}</p>
              </div>

              {/* Verified Sources */}
              {item.sources && item.sources.length > 0 && (
                <div className="text-[11px] text-slate-600 pt-1">
                  <div className="flex items-center gap-1 font-semibold text-slate-700 mb-1">
                    <BookOpen className="w-3.5 h-3.5 text-primary-600" aria-hidden="true" />
                    <span>{isHi ? 'सत्यापित संदर्भ स्रोत:' : 'Grounded Sources:'}</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {item.sources.map((src, sIdx) => (
                      <span
                        key={sIdx}
                        className="bg-slate-100 border border-slate-200 text-slate-700 px-2 py-0.5 rounded text-[10px]"
                      >
                        {src.doc_title || src.source}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Feedback Form Component */}
              <FeedbackButtons
                messageId={item.id}
                initialRating={item.feedback_rating}
                initialOutcome={item.actual_outcome}
                onFeedbackSaved={(rating, outcome) => {
                  setItems((prev) =>
                    prev.map((i) =>
                      i.id === item.id
                        ? { ...i, feedback_rating: rating, actual_outcome: outcome }
                        : i
                    )
                  );
                }}
              />
            </article>
          ))}
        </div>
      )}
    </div>
  );
};
