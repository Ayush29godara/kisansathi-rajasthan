import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import hiTranslation from './locales/hi.json';
import enTranslation from './locales/en.json';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      hi: { translation: hiTranslation },
      en: { translation: enTranslation }
    },
    lng: 'hi', // Hindi is default as requested
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
