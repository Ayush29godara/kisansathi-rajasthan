import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  MessageSquare,
  Stethoscope,
  TrendingUp,
  IndianRupee,
  CloudSun,
  MapPin,
  ArrowRight,
  ShieldCheck,
  Cpu
} from 'lucide-react';

export const HomePage: React.FC = () => {
  const { t } = useTranslation();

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
      {/* Top Banner / Welcome */}
      <section className="bg-gradient-to-r from-brand-800 to-brand-900 text-white rounded-2xl p-6 sm:p-8 shadow-sm relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-white/10 text-brand-100 mb-3">
            <Cpu className="w-3.5 h-3.5 text-rajasthan-amber" />
            <span>राजस्थान राज्य कृषि AI पोर्टल</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-2">
            {t('home.welcome')}
          </h1>
          <p className="text-brand-100 text-sm sm:text-base leading-relaxed">
            {t('app_tagline')} — सत्यापित कृषि वैज्ञानिकों के शोध और पारदर्शी निर्णय मॉडल्स पर आधारित।
          </p>

          <div className="mt-5 flex flex-wrap gap-3">
            <Link
              to="/onboarding"
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-rajasthan-amber hover:bg-amber-600 text-slate-900 font-semibold rounded-xl text-sm transition-all shadow-sm"
            >
              <MapPin className="w-4 h-4" />
              <span>खेत प्रोफाइल सेट करें (Onboarding)</span>
            </Link>
            <Link
              to="/chat"
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white font-medium rounded-xl text-sm transition-all border border-white/15"
            >
              <MessageSquare className="w-4 h-4" />
              <span>सलाहकार से पूछें</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Farm Profile Summary Pill */}
      <section className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
            राज
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium">सक्रिय खेत संदर्भ (Active Context)</div>
            <div className="text-sm font-semibold text-slate-800">
              जिला: जयपुर • फसल: सरसों (Mustard) • 2.5 हेक्टेयर
            </div>
          </div>
        </div>
        <Link
          to="/onboarding"
          className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 hover:underline inline-flex items-center gap-1"
        >
          <span>विवरण बदलें</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </section>

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
                <span>आगे बढ़ें</span>
                <ArrowRight className="w-4 h-4" />
              </div>
            </Link>
          );
        })}
      </section>

      {/* Honest Capstone Disclosure Card */}
      <section className="bg-amber-50/70 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-amber-900 leading-relaxed">
          <span className="font-bold">सत्यनिष्ठ अनुसंधान मानक (Scientific Honesty):</span> KisanSathi में कोई भी काल्पनिक डेटा या कृत्रिम आंकड़े सम्मिलित नहीं हैं। प्रशिक्षित मॉडल्स की अनुपस्थिति में यह सिस्टम स्पष्ट रूप से ऐतिहासिक जिला सांख्यिकी (Baseline) प्रदर्शित करता है।
        </div>
      </section>
    </div>
  );
};
