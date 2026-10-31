import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Home, Compass } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  return (
    <div
      role="main"
      className="min-h-[70vh] flex flex-col items-center justify-center px-4 text-center"
    >
      <div className="w-20 h-20 bg-green-50 text-green-700 rounded-3xl flex items-center justify-center mb-6 shadow-sm border border-green-100">
        <Compass className="w-10 h-10 animate-pulse" aria-hidden="true" />
      </div>

      <span className="text-sm font-semibold tracking-wider text-green-700 uppercase mb-2">
        404 Error
      </span>
      <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 mb-3">
        {isHi ? 'यह पृष्ठ उपलब्ध नहीं है' : 'Page Not Found'}
      </h1>
      <p className="max-w-md text-sm text-gray-600 mb-8 leading-relaxed">
        {isHi
          ? 'आप जिस पते पर जाने की कोशिश कर रहे हैं वह मौजूद नहीं है या बदल दिया गया है।'
          : "The page you are looking for doesn't exist or has been moved."}
      </p>

      <Link
        to="/"
        className="inline-flex items-center space-x-2 bg-primary-600 text-white font-medium px-6 py-3 rounded-xl hover:bg-primary-700 active:scale-95 transition shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
      >
        <Home className="w-4 h-4" aria-hidden="true" />
        <span>{isHi ? 'मुख्य पृष्ठ पर जाएं' : 'Return to Home'}</span>
      </Link>
    </div>
  );
};
