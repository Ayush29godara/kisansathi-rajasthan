import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import {
  MessageSquare,
  Stethoscope,
  TrendingUp,
  IndianRupee,
  CloudSun,
  MapPin,
  ArrowRight,
  ShieldCheck,
  Cpu,
  AlertCircle
} from 'lucide-react';

export const HomePage: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { user, farm } = useAuth();

  const isHindi = i18n.language === 'hi';

  const featureCards = [
    {
      title: t('home.feature_chat'),
      desc: t('home.feature_chat_desc'),
      icon: MessageSquare,
      path: '/chat',
      badge: 'RAG + Voice',
      badgeColor: 'bg-emerald-100 text-emerald-800',
      color: 'border-l-4 border-l-emerald-600',
    },
    {
      title: t('home.feature_diagnose'),
      desc: t('home.feature_diagnose_desc'),
      icon: Stethoscope,
      path: '/diagnose',
      badge: 'ONNX Web Browser',
      badgeColor: 'bg-blue-100 text-blue-800',
      color: 'border-l-4 border-l-blue-600',
    },
    {
      title: t('home.feature_yield'),
      desc: t('home.feature_yield_desc'),
      icon: TrendingUp,
      path: '/yield',
      badge: 'Tabular ML',
      badgeColor: 'bg-purple-100 text-purple-800',
      color: 'border-l-4 border-l-purple-600',
    },
    {
      title: t('home.feature_prices'),
      desc: t('home.feature_prices_desc'),
      icon: IndianRupee,
      path: '/prices',
      badge: 'Agmarknet Forecast',
      badgeColor: 'bg-amber-100 text-amber-800',
      color: 'border-l-4 border-l-amber-600',
    },
    {
      title: t('home.feature_weather'),
      desc: t('home.feature_weather_desc'),
      icon: CloudSun,
      path: '/weather',
      badge: 'FAO-56 ET0 Model',
      badgeColor: 'bg-teal-100 text-teal-800',
      color: 'border-l-4 border-l-teal-600',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner / Hero Greeting */}
      <section className="bg-gradient-to-r from-brand-800 to-brand-900 text-white rounded-2xl p-6 sm:p-8 shadow-sm relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-white/10 text-brand-100 mb-3">
            <Cpu className="w-3.5 h-3.5 text-rajasthan-amber" />
            <span>{isHindi ? 'राजस्थान राज्य कृषि AI निर्णय प्रणाली' : 'Rajasthan State Agriculture AI System'}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-2">
            {t('home.welcome')} {user?.email ? `(${user.email.split('@')[0]})` : ''}
          </h1>
          <p className="text-brand-100 text-sm sm:text-base leading-relaxed">
            {t('app_tagline')} — {isHindi ? 'सत्यापित कृषि वैज्ञानिकों के शोध और पारदर्शी निर्णय मॉडल्स पर आधारित।' : 'Powered by verified agricultural research and transparent baseline models.'}
          </p>

          <div className="mt-5 flex flex-wrap gap-3">
            <Link
              to="/onboarding"
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-rajasthan-amber hover:bg-amber-600 text-slate-900 font-semibold rounded-xl text-sm transition-all shadow-sm"
            >
              <MapPin className="w-4 h-4" />
              <span>{farm ? (isHindi ? 'खेत विवरण बदलें' : 'Update Farm Profile') : (isHindi ? 'खेत प्रोफाइल जोड़ें' : 'Set Up Farm Profile')}</span>
            </Link>
            <Link
              to="/chat"
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white font-medium rounded-xl text-sm transition-all border border-white/15"
            >
              <MessageSquare className="w-4 h-4" />
              <span>{isHindi ? 'सलाहकार से पूछें' : 'Ask Advisor'}</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Active Farm Profile Context Card */}
      {farm ? (
        <section className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-sm">
                राज
              </div>
              <div>
                <span className="text-[11px] font-semibold text-emerald-800 uppercase tracking-wider block">
                  {isHindi ? 'सक्रिय खेत संदर्भ (Active Farm Context)' : 'Active Farm Context'}
                </span>
                <h2 className="text-base font-bold text-slate-900">
                  {farm.district} • {farm.crop}
                </h2>
              </div>
            </div>
            <Link
              to="/onboarding"
              className="text-xs font-semibold text-brand-700 hover:text-brand-900 inline-flex items-center gap-1 self-start sm:self-auto"
            >
              <span>{isHindi ? 'संशोधन करें' : 'Edit Profile'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 text-xs">
            <div>
              <span className="text-slate-400 block">{isHindi ? 'तहसील' : 'Tehsil'}</span>
              <strong className="text-slate-800 text-sm">{farm.tehsil || '-'}</strong>
            </div>
            <div>
              <span className="text-slate-400 block">{isHindi ? 'क्षेत्रफल (Area)' : 'Land Area'}</span>
              <strong className="text-slate-800 text-sm">
                {farm.land_hectare} ha ({(farm.land_hectare * 3.95).toFixed(1)} {isHindi ? 'बीघा' : 'bigha'})
              </strong>
            </div>
            <div>
              <span className="text-slate-400 block">{isHindi ? 'सिंचाई साधन' : 'Irrigation'}</span>
              <strong className="text-slate-800 text-sm capitalize">{farm.irrigation}</strong>
            </div>
            <div>
              <span className="text-slate-400 block">{isHindi ? 'बुवाई तिथि' : 'Sowing Date'}</span>
              <strong className="text-slate-800 text-sm">{farm.sowing_date}</strong>
            </div>
          </div>
        </section>
      ) : (
        <section className="bg-amber-50/80 border border-amber-300 rounded-xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold text-amber-950">
                {isHindi ? 'खेत प्रोफाइल अधूरी है' : 'Farm Profile Not Set'}
              </h3>
              <p className="text-xs text-amber-800 mt-0.5 leading-relaxed">
                {isHindi
                  ? 'कृपया अपना जिला, मुख्य फसल और सिंचाई का साधन दर्ज करें ताकि सभी पूर्वानुमान और FAO-56 सिंचाई अनुसूची आपके खेत के अनुसार अनुकूलित हो सकें।'
                  : 'Please set your district, crop, and irrigation source to personalize all forecasts, weather alerts, and irrigation schedules.'}
              </p>
            </div>
          </div>
          <Link
            to="/onboarding"
            className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white font-semibold rounded-lg text-xs transition-colors whitespace-nowrap shadow-sm"
          >
            {isHindi ? 'खेत जोड़ें (Set Up)' : 'Set Up Farm'}
          </Link>
        </section>
      )}

      {/* Feature Grid */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {featureCards.map((card) => {
          const Icon = card.icon;
          return (
            <Link
              key={card.path}
              to={card.path}
              className={`bg-white rounded-xl p-5 border border-slate-200 shadow-sm card-hover flex flex-col justify-between ${card.color}`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center">
                    <Icon className="w-5 h-5 text-brand-700" />
                  </div>
                  <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full ${card.badgeColor}`}>
                    {card.badge}
                  </span>
                </div>
                <h2 className="text-base font-bold text-slate-900 mb-1">{card.title}</h2>
                <p className="text-xs text-slate-600 leading-relaxed">{card.desc}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-brand-700">
                <span>{isHindi ? 'आगे बढ़ें' : 'Open Tool'}</span>
                <ArrowRight className="w-4 h-4" />
              </div>
            </Link>
          );
        })}
      </section>

      {/* Scientific Honesty Disclaimer Card */}
      <section className="bg-slate-100/70 border border-slate-200 rounded-xl p-4 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-brand-700 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-slate-700 leading-relaxed">
          <span className="font-bold text-slate-900">
            {isHindi ? 'विश्वविद्यालय अनुसंधान मानक (Academic Integrity): ' : 'Academic Integrity Standard: '}
          </span>
          {isHindi
            ? 'KisanSathi में कोई भी काल्पनिक डेटा या कृत्रिम आंकड़े सम्मिलित नहीं हैं। अप्रशिक्षित मॉडल्स की स्थिति में यह सिस्टम पारदर्शी रूप से ऐतिहासिक सांख्यिकी (Baseline) प्रदर्शित करता है।'
            : 'KisanSathi strictly prohibits fabricated datasets or dummy accuracy numbers. Uncalibrated modules transparently display verified historical baselines.'}
        </div>
      </section>
    </div>
  );
};
