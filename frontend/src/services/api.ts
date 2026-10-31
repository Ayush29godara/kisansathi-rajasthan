/**
 * Centralized HTTP Client with synchronous JWT Bearer Token Injection
 * Avoids calling `await supabase.auth.getSession()` inside Axios interceptors,
 * which causes Web Lock (`navigator.locks`) deadlocks when triggered from `onAuthStateChange`.
 */

import axios from 'axios';
import type { HistoryItem, FeedbackPayload, SystemMetadata } from '../types';

const isLocalhost =
  typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

const envBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
const isEnvLocalhost =
  envBaseUrl.includes('localhost') || envBaseUrl.includes('127.0.0.1');

const API_BASE_URL = isLocalhost
  ? envBaseUrl || 'http://localhost:8000'
  : isEnvLocalhost
    ? ''
    : envBaseUrl;

let currentAccessToken: string | null = null;

export function setApiAccessToken(token: string | null): void {
  currentAccessToken = token;
}

function getStoredTokenSync(): string {
  if (currentAccessToken) {
    return currentAccessToken;
  }
  try {
    const demoToken = localStorage.getItem('kisansathi_demo_token');
    if (demoToken) {
      return demoToken;
    }
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('sb-') && key.endsWith('-auth-token')) {
        const raw = localStorage.getItem(key);
        if (raw) {
          const parsed = JSON.parse(raw);
          if (parsed?.access_token) {
            return parsed.access_token as string;
          }
        }
      }
    }
  } catch {
    // Ignore storage read errors
  }
  return 'mock_token_demo-farmer-jaipur';
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Synchronous request interceptor to attach JWT without navigator.locks deadlock
apiClient.interceptors.request.use(
  (config) => {
    if (!config.headers.Authorization) {
      const token = getStoredTokenSync();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for unified error formatting
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail;
    const detailText = Array.isArray(detail)
      ? detail.map((d: { msg?: string }) => d?.msg ?? '').filter(Boolean).join('; ')
      : detail;
    const message = detailText || error.message || 'Network error';
    return Promise.reject(new Error(message));
  }
);

export async function getHistory(limit = 50, offset = 0): Promise<HistoryItem[]> {
  const res = await apiClient.get<HistoryItem[]>('/history', {
    params: { limit, offset },
  });
  return res.data;
}

export async function submitFeedback(payload: FeedbackPayload): Promise<{ id: string; status: string }> {
  const res = await apiClient.post<{ id: string; status: string }>('/feedback', payload);
  return res.data;
}

export async function getSystemMetadata(): Promise<SystemMetadata> {
  try {
    const res = await apiClient.get<SystemMetadata>('/system/metadata');
    return res.data;
  } catch (err) {
    // If backend is unreachable or offline, load static bundled model_metadata.json
    const res = await fetch('/models/model_metadata.json');
    if (res.ok) {
      return (await res.json()) as SystemMetadata;
    }
    throw err;
  }
}
