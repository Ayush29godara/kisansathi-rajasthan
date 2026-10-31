import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { apiClient } from '../services/api';
import type { ChatMessage, LanguageCode, OfflineQueuedMessage } from '../types';

interface OfflineContextType {
  isOnline: boolean;
  pendingQueue: OfflineQueuedMessage[];
  queueChatMessage: (question: string, language: LanguageCode) => OfflineQueuedMessage;
  flushQueue: (onMessageSynced?: (synced: ChatMessage) => void) => Promise<number>;
  cacheData: <T>(key: string, data: T) => void;
  getCachedData: <T>(key: string) => T | null;
}

const OfflineContext = createContext<OfflineContextType | undefined>(undefined);

const QUEUE_KEY = 'kisansathi_offline_chat_queue';

export const OfflineProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine);
  const [pendingQueue, setPendingQueue] = useState<OfflineQueuedMessage[]>(() => {
    try {
      const stored = localStorage.getItem(QUEUE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  // Sync state to localStorage whenever pendingQueue changes
  useEffect(() => {
    try {
      localStorage.setItem(QUEUE_KEY, JSON.stringify(pendingQueue));
    } catch (err) {
      console.warn('Failed to save offline queue to localStorage', err);
    }
  }, [pendingQueue]);

  const queueChatMessage = useCallback((question: string, language: LanguageCode): OfflineQueuedMessage => {
    const item: OfflineQueuedMessage = {
      tempId: `offline-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      question,
      language,
      timestamp: Date.now(),
    };
    setPendingQueue((prev) => [...prev, item]);
    return item;
  }, []);

  const flushQueue = useCallback(
    async (onMessageSynced?: (synced: ChatMessage) => void): Promise<number> => {
      if (!navigator.onLine || pendingQueue.length === 0) {
        return 0;
      }

      let successCount = 0;
      const remaining: OfflineQueuedMessage[] = [];

      for (const item of pendingQueue) {
        try {
          const { data } = await apiClient.post<ChatMessage>('/chat', {
            question: item.question,
            language: item.language,
          });
          successCount++;
          if (onMessageSynced) {
            onMessageSynced(data);
          }
        } catch (err) {
          console.error('Failed to flush offline message:', item.question, err);
          // If delivery fails, keep in queue
          remaining.push(item);
        }
      }

      setPendingQueue(remaining);
      return successCount;
    },
    [pendingQueue]
  );

  // Auto flush when coming back online
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      flushQueue();
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [flushQueue]);

  const cacheData = useCallback(<T,>(key: string, data: T): void => {
    try {
      localStorage.setItem(key, JSON.stringify({ data, timestamp: Date.now() }));
    } catch (err) {
      console.warn(`Failed to cache data for key: ${key}`, err);
    }
  }, []);

  const getCachedData = useCallback(<T,>(key: string): T | null => {
    try {
      const stored = localStorage.getItem(key);
      if (!stored) return null;
      const parsed = JSON.parse(stored);
      return parsed.data as T;
    } catch {
      return null;
    }
  }, []);

  return (
    <OfflineContext.Provider
      value={{
        isOnline,
        pendingQueue,
        queueChatMessage,
        flushQueue,
        cacheData,
        getCachedData,
      }}
    >
      {children}
    </OfflineContext.Provider>
  );
};

export const useOffline = () => {
  const context = useContext(OfflineContext);
  if (!context) {
    throw new Error('useOffline must be used within an OfflineProvider');
  }
  return context;
};
