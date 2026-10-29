/**
 * Offline Storage Utility using browser localStorage / IndexedDB
 * Ensures smallholder farmers retain access to vital data in low-connectivity areas.
 */

const STORAGE_KEYS = {
  PROFILE: 'kisansathi_offline_profile',
  MANDI_CACHE: 'kisansathi_offline_mandi',
  ADVICE_CACHE: 'kisansathi_offline_advice',
};

export const offlineStorage = {
  saveProfile(profile: unknown): void {
    try {
      localStorage.setItem(STORAGE_KEYS.PROFILE, JSON.stringify(profile));
    } catch (e) {
      console.warn('Could not cache profile offline', e);
    }
  },

  getProfile<T>(): T | null {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.PROFILE);
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  },

  saveMandiPrices(prices: unknown): void {
    try {
      localStorage.setItem(STORAGE_KEYS.MANDI_CACHE, JSON.stringify(prices));
    } catch (e) {
      console.warn('Could not cache mandi prices offline', e);
    }
  },

  getMandiPrices<T>(): T | null {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.MANDI_CACHE);
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  },
};
