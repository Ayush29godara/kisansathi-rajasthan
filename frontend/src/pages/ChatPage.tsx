import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Mic, BookOpen, AlertTriangle, User, Bot, Languages, ChevronDown, ChevronUp } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../services/api';
import { useOffline } from '../context/OfflineContext';
import { FeedbackButtons } from '../components/common/FeedbackButtons';
import { RichText } from '../components/common/RichText';
import { ChatMessage, SourceCitation } from '../types';

/* ------------------------------------------------------------------ */
/*  Web Speech API – browser‑safe type shims                          */
/* ------------------------------------------------------------------ */
interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent {
  error: string;
  message?: string;
}

type SpeechRecognitionInstance = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((e: SpeechRecognitionEvent) => void) | null;
  onerror: ((e: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};

function getSpeechRecognition(): (new () => SpeechRecognitionInstance) | null {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const w = window as any;
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

/* ------------------------------------------------------------------ */
/*  Internal UI message type (wraps the API ChatMessage)              */
/* ------------------------------------------------------------------ */
interface UIMessage {
  id?: string;
  role: 'user' | 'bot';
  text: string;
  sources?: SourceCitation[];
  model_version?: string;
  disclaimer?: string;
  intent?: ChatMessage['intent'];
  isError?: boolean;
  isOfflineQueued?: boolean;
}

/* ------------------------------------------------------------------ */
/*  Source Citation Chip                                               */
/* ------------------------------------------------------------------ */
const SourceChip: React.FC<{ source: SourceCitation; index: number }> = ({ source, index }) => {
  const [expanded, setExpanded] = useState(false);
  const colors = [
    'bg-blue-100 text-blue-800 border-blue-200',
    'bg-emerald-100 text-emerald-800 border-emerald-200',
    'bg-amber-100 text-amber-800 border-amber-200',
    'bg-purple-100 text-purple-800 border-purple-200',
    'bg-rose-100 text-rose-800 border-rose-200',
  ];
  const colorClass = colors[index % colors.length];

  return (
    <div className="inline-block mr-1.5 mb-1.5">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium border cursor-pointer transition-colors hover:opacity-80 ${colorClass}`}
        aria-expanded={expanded}
        aria-label={`Source: ${source.doc_title}`}
      >
        <BookOpen className="w-3 h-3 flex-shrink-0" />
        <span className="truncate max-w-[180px]">{source.doc_title}</span>
        {source.relevance_score != null && (
          <span className="ml-1 bg-white/60 px-1.5 py-0.5 rounded-full text-[10px] font-semibold">
            {Math.round(source.relevance_score * 100)}%
          </span>
        )}
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>

      {expanded && (
        <div className="mt-1.5 p-2.5 bg-white border border-slate-200 rounded-lg text-xs text-slate-600 leading-relaxed shadow-sm">
          <p className="font-medium text-slate-700 mb-1">{source.source}</p>
          <p className="italic text-slate-500">"{source.chunk_text}"</p>
        </div>
      )}
    </div>
  );
};

/* ------------------------------------------------------------------ */
/*  Animated Loading Dots                                             */
/* ------------------------------------------------------------------ */
const LoadingIndicator: React.FC<{ text: string }> = ({ text }) => (
  <div className="flex items-start gap-2.5 justify-start">
    <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center flex-shrink-0">
      <Bot className="w-4 h-4" />
    </div>
    <div className="bg-slate-50 border border-slate-200 rounded-2xl rounded-tl-none px-4 py-3 max-w-[90%] text-sm shadow-sm">
      <div className="flex items-center gap-2 text-slate-500">
        <span className="flex gap-1">
          <span className="w-2 h-2 bg-brand-600 rounded-full animate-bounce [animation-delay:0ms]" />
          <span className="w-2 h-2 bg-brand-600 rounded-full animate-bounce [animation-delay:150ms]" />
          <span className="w-2 h-2 bg-brand-600 rounded-full animate-bounce [animation-delay:300ms]" />
        </span>
        <span className="text-xs italic">{text}</span>
      </div>
    </div>
  </div>
);

/* ================================================================== */
/*  ChatPage – main component                                        */
/* ================================================================== */
export const ChatPage: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { isOnline, queueChatMessage } = useOffline();

  /* ---- state ---- */
  const [messages, setMessages] = useState<UIMessage[]>([
    {
      role: 'bot',
      text: t('chat.welcome_message'),
      model_version: 'system',
    },
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [loading, setLoading] = useState(false);

  /* ---- refs ---- */
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);

  /* ---- Speech API availability ---- */
  const speechAvailable = Boolean(getSpeechRecognition());

  /* ---- auto-scroll ---- */
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, scrollToBottom]);

  /* ---- send handler ---- */
  const handleSend = useCallback(
    async (text?: string) => {
      const query = (text ?? inputQuery).trim();
      if (!query || loading) return;

      setInputQuery('');
      setMessages((prev) => [...prev, { role: 'user', text: query }]);

      // If offline, queue immediately and show notification bubble
      if (!isOnline) {
        queueChatMessage(query, (i18n.language as any) || 'hi');
        setMessages((prev) => [
          ...prev,
          {
            role: 'bot',
            text:
              i18n.language === 'hi'
                ? 'आप ऑफ़लाइन हैं। आपका संदेश सुरक्षित कर लिया गया है। इंटरनेट कनेक्ट होते ही उत्तर स्वतः प्राप्त होगा।'
                : 'You are offline. Your query has been queued and will be sent automatically once reconnected.',
            model_version: 'offline-queue',
            isOfflineQueued: true,
          },
        ]);
        return;
      }

      setLoading(true);

      try {
        const { data } = await apiClient.post<ChatMessage>(
          '/chat',
          {
            question: query,
            language: i18n.language?.startsWith('en') ? 'en' : 'hi',
          },
          { timeout: 90000 },
        );

        setMessages((prev) => [
          ...prev,
          {
            id: data.id,
            role: 'bot',
            text: data.answer,
            sources: data.sources,
            model_version: data.model_version,
            disclaimer: data.disclaimer,
            intent: data.intent,
          },
        ]);
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : t('chat.error');
        setMessages((prev) => [
          ...prev,
          {
            role: 'bot',
            text: errMsg,
            isError: true,
          },
        ]);
      } finally {
        setLoading(false);
        inputRef.current?.focus();
      }
    },
    [inputQuery, loading, i18n.language, isOnline, queueChatMessage, t],
  );

  const onFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSend();
  };

  /* ---- voice input ---- */
  const startRecording = useCallback(() => {
    const SpeechRecognitionCtor = getSpeechRecognition();
    if (!SpeechRecognitionCtor) return;

    const recognition = new SpeechRecognitionCtor();
    recognition.lang = i18n.language === 'en' ? 'en-IN' : 'hi-IN';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = event.results[0]?.[0]?.transcript;
      if (transcript) {
        setInputQuery(transcript);
        // Auto-submit after a short delay so user can see the text
        setTimeout(() => {
          handleSend(transcript);
        }, 300);
      }
    };

    recognition.onerror = () => {
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsRecording(true);
  }, [i18n.language, handleSend]);

  const stopRecording = useCallback(() => {
    recognitionRef.current?.stop();
    setIsRecording(false);
  }, []);

  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  /* ---- language toggle (inline in header) ---- */
  const toggleLanguage = async () => {
    const nextLang = i18n.language === 'hi' ? 'en' : 'hi';
    await i18n.changeLanguage(nextLang);
    localStorage.setItem('i18nextLng', nextLang);
  };

  /* ================================================================ */
  /*  RENDER                                                          */
  /* ================================================================ */
  return (
    <div className="max-w-3xl mx-auto flex flex-col h-[calc(100vh-8rem)] bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* ---- HEADER ---- */}
      <header className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between gap-2 flex-wrap">
        <div className="min-w-0">
          <h1 className="text-base font-bold text-slate-800 truncate">
            {t('chat.title')}
          </h1>
          <p className="text-xs text-slate-500 truncate">{t('chat.subtitle')}</p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="text-[11px] font-semibold bg-emerald-100 text-emerald-800 px-2.5 py-1 rounded-full whitespace-nowrap">
            {t('chat.model_badge')}
          </span>
          <button
            type="button"
            onClick={toggleLanguage}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-brand-700 hover:bg-brand-800 text-white transition-colors min-h-[2.75rem] min-w-[2.75rem] justify-center"
            aria-label="Toggle language between Hindi and English"
          >
            <Languages className="w-3.5 h-3.5" />
            <span>{i18n.language === 'hi' ? 'English' : 'हिन्दी'}</span>
          </button>
        </div>
      </header>

      {/* ---- MESSAGE LIST ---- */}
      <div
        className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth"
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
      >
        {messages.map((msg, idx) => {
          if (msg.role === 'user') {
            /* ---------- User bubble ---------- */
            return (
              <div key={idx} className="flex items-start gap-2.5 justify-end">
                <div className="bg-brand-700 text-white rounded-2xl rounded-tr-none px-4 py-2.5 max-w-[85%] text-sm shadow-sm">
                  {msg.text}
                </div>
                <div className="w-8 h-8 rounded-full bg-brand-800 text-white flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4" />
                </div>
              </div>
            );
          }

          /* ---------- Bot bubble ---------- */
          return (
            <div key={idx} className="flex items-start gap-2.5 justify-start">
              <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div
                className={`rounded-2xl rounded-tl-none p-4 max-w-[90%] text-sm space-y-3 shadow-sm ${
                  msg.isError
                    ? 'bg-red-50 border border-red-200'
                    : 'bg-slate-50 border border-slate-200'
                }`}
              >
                {/* Answer text */}
                <div
                  className={`leading-relaxed ${
                    msg.isError ? 'text-red-700' : 'text-slate-800'
                  }`}
                >
                  {!msg.isError ? <RichText text={msg.text} /> : msg.text}
                </div>

                {/* Source citation chips */}
                {msg.sources && msg.sources.length > 0 && (
                  <div>
                    <p className="text-[11px] font-semibold text-slate-600 mb-1.5 flex items-center gap-1">
                      <BookOpen className="w-3.5 h-3.5 text-brand-700" />
                      {t('chat.sources_label')}
                    </p>
                    <div className="flex flex-wrap">
                      {msg.sources.map((src, sIdx) => (
                        <SourceChip key={sIdx} source={src} index={sIdx} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Disclaimer */}
                {msg.disclaimer && (
                  <div className="text-[10px] text-slate-400 flex items-center gap-1 pt-1 border-t border-slate-200/60">
                    <AlertTriangle className="w-3 h-3 text-amber-500 flex-shrink-0" />
                    <span>{msg.disclaimer || t('chat.disclaimer')}</span>
                  </div>
                )}

                {/* Model badge */}
                {msg.model_version && msg.model_version !== 'system' && (
                  <div className="flex">
                    <span className="text-[10px] bg-slate-200 text-slate-600 px-2 py-0.5 rounded-full">
                      {msg.model_version}
                    </span>
                  </div>
                )}

                {/* Farmer Feedback */}
                {!msg.isError && msg.model_version !== 'system' && !msg.isOfflineQueued && (
                  <FeedbackButtons messageId={msg.id} />
                )}
              </div>
            </div>
          );
        })}

        {/* Loading state */}
        {loading && <LoadingIndicator text={t('chat.searching')} />}

        {/* Invisible scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* ---- INPUT BAR ---- */}
      <form
        onSubmit={onFormSubmit}
        className="p-3 bg-slate-50 border-t border-slate-200 flex items-center gap-2"
      >
        {/* Mic button (only if Speech API available) */}
        {speechAvailable ? (
          <div className="relative">
            <button
              type="button"
              onClick={toggleRecording}
              className={`p-2.5 rounded-full transition-colors min-h-[2.75rem] min-w-[2.75rem] flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-brand-500 ${
                isRecording
                  ? 'bg-red-600 text-white animate-pulse shadow-lg shadow-red-300'
                  : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
              }`}
              aria-label={isRecording ? t('chat.voice_listening') : t('chat.voice_start')}
              title={isRecording ? t('chat.voice_listening') : t('chat.voice_start')}
            >
              <Mic className="w-5 h-5" />
            </button>
            {isRecording && (
              <span className="absolute -top-6 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] font-medium text-red-600 bg-red-50 px-2 py-0.5 rounded-full border border-red-200 shadow-sm">
                {t('chat.voice_listening')}
              </span>
            )}
          </div>
        ) : (
          <button
            type="button"
            disabled
            className="p-2.5 rounded-full bg-slate-100 text-slate-400 cursor-not-allowed min-h-[2.75rem] min-w-[2.75rem] flex items-center justify-center"
            aria-label={t('chat.voice_unsupported')}
            title={t('chat.voice_unsupported')}
          >
            <Mic className="w-5 h-5" />
          </button>
        )}

        {/* Text input */}
        <input
          ref={inputRef}
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder={t('chat.placeholder')}
          disabled={loading}
          className="flex-1 px-4 py-2.5 text-sm border border-slate-300 rounded-full focus:ring-2 focus:ring-brand-500 focus:outline-none disabled:opacity-60 min-h-[2.75rem]"
          aria-label={t('chat.placeholder')}
        />

        {/* Send button */}
        <button
          type="submit"
          disabled={!inputQuery.trim() || loading}
          className="p-2.5 bg-brand-700 hover:bg-brand-800 disabled:bg-brand-400 disabled:cursor-not-allowed text-white rounded-full transition-colors min-h-[2.75rem] min-w-[2.75rem] flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-brand-500"
          aria-label={t('chat.send')}
          title={t('chat.send')}
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  );
};
