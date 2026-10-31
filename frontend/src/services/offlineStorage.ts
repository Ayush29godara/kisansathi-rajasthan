/**
 * Offline Storage Utility using browser localStorage
 * Ensures smallholder farmers retain access to vital farm profile, mandi prices,
 * weather schedules, and disease advice in low-connectivity rural environments.
 */

const STORAGE_KEYS = {
  PROFILE: 'kisansathi_offline_profile',
  MANDI_CACHE: 'kisansathi_offline_mandi',
  ADVICE_CACHE: 'kisansathi_offline_advice',
  WEATHER_CACHE: 'kisansathi_offline_weather',
  DISEASE_CACHE: 'kisansathi_offline_disease',
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

  saveWeatherAdvice(weather: unknown): void {
    try {
      localStorage.setItem(STORAGE_KEYS.WEATHER_CACHE, JSON.stringify(weather));
    } catch (e) {
      console.warn('Could not cache weather advice offline', e);
    }
  },

  getWeatherAdvice<T>(): T | null {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.WEATHER_CACHE);
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  },

  saveDiseaseAdvice(advice: unknown): void {
    try {
      localStorage.setItem(STORAGE_KEYS.DISEASE_CACHE, JSON.stringify(advice));
    } catch (e) {
      console.warn('Could not cache disease advice offline', e);
    }
  },

  getDiseaseAdvice<T>(): T | null {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.DISEASE_CACHE);
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  },
};
