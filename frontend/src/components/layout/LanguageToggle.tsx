import React from 'react';
import { useTranslation } from 'react-i18next';
import { Languages } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiClient } from '../../services/api';

export const LanguageToggle: React.FC = () => {
  const { i18n } = useTranslation();
  const { user } = useAuth();

  const toggleLanguage = async () => {
    const nextLang = i18n.language === 'hi' ? 'en' : 'hi';
    await i18n.changeLanguage(nextLang);
    localStorage.setItem('i18nextLng', nextLang);

    // Sync preference to Supabase profile if user is authenticated
    if (user) {
      try {
        await apiClient.put('/profile', { language: nextLang });
      } catch (err) {
        console.warn('Could not sync language preference to profile:', err);
      }
    }
  };

  return (
    <button
      onClick={toggleLanguage}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-white/10 hover:bg-white/20 text-white border border-white/20 transition-colors"
      aria-label="Toggle language between Hindi and English"
    >
      <Languages className="w-3.5 h-3.5" />
      <span>{i18n.language === 'hi' ? 'English' : 'हिन्दी'}</span>
    </button>
  );
};
