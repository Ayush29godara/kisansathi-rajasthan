import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Sprout, Menu, X, MessageSquare, Stethoscope, TrendingUp, IndianRupee, CloudSun, History, Info } from 'lucide-react';
import { LanguageToggle } from './LanguageToggle';

export const Navbar: React.FC = () => {
  const { t } = useTranslation();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { path: '/', label: t('nav.home'), icon: Sprout },
    { path: '/chat', label: t('nav.chat'), icon: MessageSquare },
    { path: '/diagnose', label: t('nav.diagnose'), icon: Stethoscope },
    { path: '/yield', label: t('nav.yield'), icon: TrendingUp },
    { path: '/prices', label: t('nav.prices'), icon: IndianRupee },
    { path: '/weather', label: t('nav.weather'), icon: CloudSun },
    { path: '/history', label: t('nav.history'), icon: History },
    { path: '/about', label: t('nav.about'), icon: Info },
  ];

  return (
    <header className="bg-brand-800 text-white sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 hover:opacity-90 transition-opacity">
            <div className="w-9 h-9 rounded-full bg-rajasthan-amber flex items-center justify-center text-white shadow-sm">
              <Sprout className="w-5 h-5 text-emerald-900" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight block leading-none">किसान साथी</span>
              <span className="text-[10px] text-brand-100 uppercase tracking-wider">KisanSathi Rajasthan</span>
            </div>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden lg:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-brand-900 text-white font-semibold'
                      : 'text-brand-100 hover:bg-brand-700/60 hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Controls */}
          <div className="flex items-center gap-2">
            <LanguageToggle />
            <Link
              to="/login"
              className="hidden sm:inline-flex px-3 py-1.5 text-xs font-semibold bg-white text-brand-900 rounded-full hover:bg-brand-50 transition-colors"
            >
              {t('nav.login')}
            </Link>

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-md text-brand-100 hover:text-white hover:bg-brand-700"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Nav Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-brand-900 border-t border-brand-700 px-4 pt-2 pb-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-base font-medium ${
                  isActive ? 'bg-brand-800 text-white font-semibold' : 'text-brand-100 hover:bg-brand-800'
                }`}
              >
                <Icon className="w-5 h-5 text-rajasthan-sand" />
                <span>{item.label}</span>
              </Link>
            );
          })}
          <div className="pt-2 border-t border-brand-800">
            <Link
              to="/login"
              onClick={() => setMobileMenuOpen(false)}
              className="block w-full text-center py-2 px-4 rounded-md font-medium text-sm bg-brand-600 text-white"
            >
              {t('nav.login')}
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};
