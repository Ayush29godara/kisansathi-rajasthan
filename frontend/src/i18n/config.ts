import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import hiTranslation from './locales/hi.json';
import enTranslation from './locales/en.json';

const savedLang =
  typeof window !== 'undefined' ? localStorage.getItem('i18nextLng') : null;

i18n
  .use(initReactI18next)
  .init({
    resources: {
      hi: { translation: hiTranslation },
      en: { translation: enTranslation }
    },
    lng: savedLang === 'en' || savedLang === 'hi' ? savedLang : 'hi',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
