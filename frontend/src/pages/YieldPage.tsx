import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  TrendingUp,
  BarChart3,
  ShieldAlert,
  Loader2,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  MinusCircle,
  Sparkles,
  Lock,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../services/api';
import { YieldOutlook } from '../types';

const CROPS = [
  { id: 'Mustard', hi: 'सरसों (Mustard)', en: 'Mustard', defaultSeason: 'Rabi' },
  { id: 'Bajra', hi: 'बाजरा (Bajra)', en: 'Bajra (Pearl Millet)', defaultSeason: 'Kharif' },
  { id: 'Wheat', hi: 'गेहूं (Wheat)', en: 'Wheat', defaultSeason: 'Rabi' },
  { id: 'Soybean', hi: 'सोयाबीन (Soybean)', en: 'Soybean', defaultSeason: 'Kharif' },
  { id: 'Guar', hi: 'ग्वार (Guar)', en: 'Guar (Cluster Bean)', defaultSeason: 'Kharif' },
  { id: 'Gram', hi: 'चना (Gram)', en: 'Gram (Chickpea)', defaultSeason: 'Rabi' },
];

const SEASONS = [
  { id: 'Rabi', hi: 'रबी (Rabi)', en: 'Rabi' },
  { id: 'Kharif', hi: 'खरीफ (Kharif)', en: 'Kharif' },
];

const RAJASTHAN_DISTRICTS = [
  'Ajmer', 'Alwar', 'Anupgarh', 'Balotra', 'Banswara', 'Baran', 'Barmer', 'Beawar',
  'Bharatpur', 'Bhilwara', 'Bikaner', 'Bundi', 'Chittorgarh', 'Churu', 'Dausa', 'Deeg',
  'Didwana-Kuchaman', 'Dholpur', 'Dungarpur', 'Hanumangarh', 'Jaipur', 'Jaisalmer',
  'Jalore', 'Jhalawar', 'Jhunjhunu', 'Jodhpur', 'Karauli', 'Kekri', 'Khairthal-Tijara',
  'Kota', 'Kotputli-Behror', 'Nagaur', 'Pali', 'Phalodi', 'Pratapgarh', 'Rajsamand',
  'Salumber', 'Sanchore', 'Sawai Madhopur', 'Sikar', 'Sirohi', 'Sri Ganganagar', 'Tonk', 'Udaipur'
];

export const YieldPage: React.FC = () => {
  const { i18n } = useTranslation();
  const isHindi = i18n.language?.startsWith('hi');
  const { user, farm, signInAsDemoFarmer } = useAuth();

  const [district, setDistrict] = useState(farm?.district || 'Jaipur');
  const [crop, setCrop] = useState(farm?.crop || 'Mustard');
  const [season, setSeason] = useState('Rabi');
  const [year] = useState(2026);

  const [outlook, setOutlook] = useState<YieldOutlook | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync with user's farm profile when available
  useEffect(() => {
    if (farm?.district) setDistrict(farm.district);
    if (farm?.crop) setCrop(farm.crop);
  }, [farm]);

  const fetchYieldOutlook = useCallback(async () => {
    if (!user) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { data } = await apiClient.get<YieldOutlook>('/predict/yield', {
        params: { district, crop, season, year, language: isHindi ? 'hi' : 'en' },
      });
      setOutlook(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'उपज अनुमान लोड करने में विफल।';
      setError(msg);
      setOutlook(null);
    } finally {
      setLoading(false);
    }
  }, [user, district, crop, season, year, isHindi]);

  useEffect(() => {
    fetchYieldOutlook();
  }, [fetchYieldOutlook]);

  // Conversions: 1 Hectare ≈ 3.95 Pucca Bigha (Rajasthan standard), 1 Quintal = 100 kg
  const quintalPerHectare = outlook ? (outlook.predicted_yield_kg_ha / 100).toFixed(1) : '0';
  const quintalPerBigha = outlook ? ((outlook.predicted_yield_kg_ha / 100) / 3.95).toFixed(2) : '0';
  const baselineQuintalHa = outlook ? (outlook.baseline_5yr_mean_kg_ha / 100).toFixed(1) : '0';

  const pctDiff = outlook && outlook.baseline_5yr_mean_kg_ha > 0
    ? ((outlook.predicted_yield_kg_ha - outlook.baseline_5yr_mean_kg_ha) / outlook.baseline_5yr_mean_kg_ha) * 100
    : 0;

  const isBaseline = outlook?.model_version === 'baseline';
  const isTrend = outlook?.model_version?.startsWith('district-trend') ?? false;

  return (
    <div className="max-w-4xl mx-auto my-6 space-y-6">
      {/* Title & Parameter Selection Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
              <TrendingUp className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">
                {isHindi ? 'जिला फसल उपज परिदृश्य' : 'District Crop Yield Outlook'}
              </h1>
              <p className="text-xs text-slate-500">
                {isHindi
                  ? 'मौसम विज्ञान, सिंचाई व 33-जिला ऐतिहासिक सांख्यिकी पर आधारित वैज्ञानिक अनुमान'
                  : 'Agro-climatic features, weather indicators, and historical 33-district benchmark'}
              </p>
            </div>
          </div>

          <button
            onClick={fetchYieldOutlook}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors disabled:opacity-50"
            title="पुनः गणना करें"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin text-brand-600" /> : <RefreshCw className="w-4 h-4" />}
            <span>{isHindi ? 'ताज़ा करें' : 'Refresh'}</span>
          </button>
        </div>

        {/* Input Selectors */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {isHindi ? 'जिला (District)' : 'District'}
            </label>
            <select
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white"
            >
              {(RAJASTHAN_DISTRICTS.includes(district) ? RAJASTHAN_DISTRICTS : [district, ...RAJASTHAN_DISTRICTS]).map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {isHindi ? 'फसल (Crop)' : 'Crop'}
            </label>
            <select
              value={crop}
              onChange={(e) => {
                const selected = e.target.value;
                setCrop(selected);
                const found = CROPS.find((c) => c.id === selected);
                if (found) setSeason(found.defaultSeason);
              }}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white"
            >
              {CROPS.map((c) => (
                <option key={c.id} value={c.id}>{isHindi ? c.hi : c.en}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {isHindi ? 'मौसम (Season)' : 'Season'}
            </label>
            <select
              value={season}
              onChange={(e) => setSeason(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white"
            >
              {SEASONS.map((s) => (
                <option key={s.id} value={s.id}>{isHindi ? s.hi : s.en}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Error Notice */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={fetchYieldOutlook} className="font-semibold underline ml-2">पुनः प्रयास करें</button>
        </div>
      )}

      {/* Unauthenticated Login Callout */}
      {!user && (
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-brand-100 text-brand-800 flex items-center justify-center mx-auto">
            <Lock className="w-6 h-6" />
          </div>
          <h2 className="text-base font-bold text-slate-800">
            {isHindi ? 'उपज पूर्वानुमान देखने के लिए लॉगिन आवश्यक है' : 'Login Required to Access Yield Forecasts'}
          </h2>
          <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            {isHindi
              ? 'प्रमाणित सुरक्षा नियमों के अनुसार कृषि निर्णय सहायक मॉडल देखने के लिए किसान खाते से लॉगिन करें। परीक्षण हेतु 1-क्लिक त्वरित डेमो लॉगिन उपलब्ध है।'
              : 'Per security guidelines, accessing agricultural decision models requires an authenticated session. Quick 1-click demo access is available for instant testing.'}
          </p>
          <div className="flex items-center justify-center gap-3 pt-2">
            <button
              onClick={signInAsDemoFarmer}
              className="px-5 py-2.5 bg-brand-700 hover:bg-brand-800 text-white rounded-xl text-xs font-semibold shadow-xs transition-colors cursor-pointer"
            >
              {isHindi ? '⚡ 1-क्लिक त्वरित डेमो लॉगिन' : '⚡ 1-Click Quick Demo Login'}
            </button>
            <Link
              to="/login"
              className="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors"
            >
              {isHindi ? 'लॉगिन पेज पर जाएं' : 'Go to Login'}
            </Link>
          </div>
        </div>
      )}

      {/* Yield Metrics Card */}
      {outlook && (
        <div
          key={`${outlook.district}-${outlook.crop}-${outlook.season}-${outlook.forecast_year}-${outlook.predicted_yield_kg_ha}`}
          className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-6"
        >
          {/* Status Header */}
          <div className="flex items-center justify-between border-b border-slate-100 pb-3 flex-wrap gap-2">
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              {`${outlook.district} — ${outlook.crop} (${outlook.season} ${outlook.forecast_year})`}
            </span>

            {/* Model Badge */}
            {isTrend ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-800 border border-blue-200">
                <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
                <span>{isHindi ? 'जिला रुझान अनुमान (सांख्यिकीय)' : 'District Trend Estimate (statistical)'}</span>
              </span>
            ) : isBaseline ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                <span>{isHindi ? 'सांख्यिकीय बेसलाइन (5-Year Rolling Mean)' : 'Statistical Baseline (5-Year Mean)'}</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                <span>{isHindi ? `ML मॉडल (${outlook.model_version})` : `ML Model (${outlook.model_version})`}</span>
              </span>
            )}
          </div>

          {/* Metric Comparison Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Predicted Outlook Card */}
            <div className="p-5 bg-gradient-to-br from-emerald-50 to-emerald-100/40 rounded-2xl border border-emerald-200">
              <div className="text-xs text-emerald-800 font-semibold uppercase tracking-wider">
                {isHindi ? 'अनुमानित पैदावार (Expected Yield)' : 'Expected Yield Outlook'}
              </div>
              <div className="text-3xl font-extrabold text-emerald-950 mt-2" translate="no">
                <span>{outlook.predicted_yield_kg_ha.toFixed(0)}</span>{' '}
                <span className="text-sm font-semibold text-emerald-800">kg/ha</span>
              </div>
              <div className="mt-3 pt-3 border-t border-emerald-200/60 flex items-center justify-between text-xs text-emerald-900 font-medium">
                <span>
                  {isHindi ? (
                    <>लगभग <strong translate="no">{quintalPerHectare}</strong> क्विंटल/हेक्टेयर</>
                  ) : (
                    <>About <strong translate="no">{quintalPerHectare}</strong> quintals/hectare</>
                  )}
                </span>
                <span>
                  {isHindi ? (
                    <>(≈ <strong translate="no">{quintalPerBigha}</strong> क्विंटल/बीघा)</>
                  ) : (
                    <>(≈ <strong translate="no">{quintalPerBigha}</strong> quintals/bigha)</>
                  )}
                </span>
              </div>
            </div>

            {/* Historical District 5-Yr Baseline Card */}
            <div className="p-5 bg-slate-50 rounded-2xl border border-slate-200">
              <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
                {isHindi ? 'जिला 5-वर्षीय औसत (Historical Baseline)' : 'District 5-Year Average'}
              </div>
              <div className="text-3xl font-extrabold text-slate-800 mt-2" translate="no">
                <span>{outlook.baseline_5yr_mean_kg_ha.toFixed(0)}</span>{' '}
                <span className="text-sm font-semibold text-slate-500">kg/ha</span>
              </div>
              <div className="mt-3 pt-3 border-t border-slate-200/60 flex items-center justify-between text-xs text-slate-600 font-medium">
                <span>
                  {isHindi ? (
                    <>लगभग <strong translate="no">{baselineQuintalHa}</strong> क्विंटल/हेक्टेयर</>
                  ) : (
                    <>About <strong translate="no">{baselineQuintalHa}</strong> quintals/hectare</>
                  )}
                </span>
                {pctDiff !== 0 && (
                  <span className={`px-2 py-0.5 rounded font-bold ${pctDiff > 0 ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
                    {isHindi
                      ? `${pctDiff > 0 ? `+${pctDiff.toFixed(1)}%` : `${pctDiff.toFixed(1)}%`} औसत से`
                      : `${pctDiff > 0 ? `+${pctDiff.toFixed(1)}%` : `${pctDiff.toFixed(1)}%`} from average`}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Plain Language Summary */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 leading-relaxed">
            {outlook.summary_text}
          </div>

          {/* Top Drivers Attribution (SHAP Explanations) */}
          <div>
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <BarChart3 className="w-4 h-4 text-purple-600" />
              <span>
                {isHindi
                  ? 'उत्पादन को प्रभावित करने वाले मुख्य कारक (Key Feature Drivers):'
                  : 'Key Feature Drivers (TreeSHAP Attributions):'}
              </span>
            </h2>

            <div className="space-y-2.5">
              {outlook.top_drivers.map((driver, idx) => {
                const isPos = driver.impact === 'positive';
                const isNeg = driver.impact === 'negative';

                return (
                  <div
                    key={idx}
                    className="p-3.5 bg-white rounded-xl border border-slate-200 flex items-start gap-3 shadow-xs"
                  >
                    <div className="mt-0.5 flex-shrink-0">
                      {isPos && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                      {isNeg && <AlertTriangle className="w-4 h-4 text-red-600" />}
                      {!isPos && !isNeg && <MinusCircle className="w-4 h-4 text-slate-400" />}
                    </div>
                    <div className="flex-1 text-xs">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="font-bold text-slate-800">{driver.feature}</span>
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                            isPos
                              ? 'bg-emerald-100 text-emerald-800'
                              : isNeg
                              ? 'bg-red-100 text-red-800'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          {isPos ? (isHindi ? 'सकारात्मक प्रभाव' : 'Positive Impact')
                            : isNeg ? (isHindi ? 'नकारात्मक प्रभाव' : 'Negative Impact')
                            : (isHindi ? 'तटस्थ' : 'Neutral')}
                        </span>
                      </div>
                      <p className="text-slate-600 leading-normal">{driver.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Scientific Honesty Notice */}
          <div className="p-4 bg-amber-50/70 rounded-xl border border-amber-200 text-xs text-amber-900 flex items-start gap-2.5">
            <ShieldAlert className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
            <div className="leading-relaxed">
              <strong>{isHindi ? 'सत्यनिष्ठ प्रकटीकरण (Honesty Rule):' : 'Scientific Transparency Policy:'} </strong>
              {isHindi
                ? 'यदि वास्तविक प्रशिक्षित ML मॉडल उपलब्ध न हो तो किसान साथी 5-वर्षीय ऐतिहासिक जिला औसत (Baseline) प्रस्तुत करता है और इसे मॉडल संस्करण "baseline" के रूप में स्पष्ट दिखाता है। हम कभी भी सांख्यिकीय बेसलाइन को झूठे ML के रूप में प्रस्तुत नहीं करते।'
                : 'Whenever a trained model is not present, KisanSathi displays the 5-year historical district average and clearly flags model_version="baseline". We never present baseline statistical outputs as machine learning predictions.'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
