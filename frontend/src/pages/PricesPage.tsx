import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  IndianRupee,
  Calendar,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Minus,
  Clock,
  ShoppingCart,
  Scale,
  RefreshCw,
  Loader2,
  Info,
  ShieldAlert,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../services/api';
import { offlineStorage } from '../services/offlineStorage';
import { MandiPriceForecast, MandiPriceRecord } from '../types';

interface MandiOption {
  id: string;
  name: string;
  hi: string;
  district: string;
}

interface CommodityOption {
  id: string;
  name: string;
  hi: string;
  en: string;
}

const RAJASTHAN_MANDIS: MandiOption[] = [
  { id: 'Alwar', name: 'Alwar', hi: 'अलवर (Alwar)', district: 'Alwar' },
  { id: 'Kota', name: 'Kota', hi: 'भामाशाह मंडी कोटा (Kota)', district: 'Kota' },
  { id: 'Jaipur (Surajpole)', name: 'Jaipur (Surajpole)', hi: 'जयपुर सूरजपोल (Jaipur)', district: 'Jaipur' },
  { id: 'Bikaner', name: 'Bikaner', hi: 'बीकानेर अनाज मंडी (Bikaner)', district: 'Bikaner' },
  { id: 'Jodhpur', name: 'Jodhpur', hi: 'जोधपुर मंडोर (Jodhpur)', district: 'Jodhpur' },
  { id: 'Sri Ganganagar', name: 'Sri Ganganagar', hi: 'श्रीगंगानगर (Sri Ganganagar)', district: 'Sri Ganganagar' },
  { id: 'Baran', name: 'Baran', hi: 'बारां मंडी (Baran)', district: 'Baran' },
  { id: 'Bharatpur', name: 'Bharatpur', hi: 'भरतपुर (Bharatpur)', district: 'Bharatpur' },
  { id: 'Nagaur', name: 'Nagaur', hi: 'नागौर (Nagaur)', district: 'Nagaur' },
  { id: 'Hanumangarh', name: 'Hanumangarh', hi: 'हनुमानगढ़ (Hanumangarh)', district: 'Hanumangarh' },
];

const COMMODITIES: CommodityOption[] = [
  { id: 'Mustard', name: 'Mustard', hi: 'सरसों / राया (Mustard)', en: 'Mustard' },
  { id: 'Wheat', name: 'Wheat', hi: 'गेहूं (Wheat)', en: 'Wheat' },
  { id: 'Bajra', name: 'Bajra', hi: 'बाजरा (Bajra)', en: 'Bajra (Pearl Millet)' },
  { id: 'Soybean', name: 'Soybean', hi: 'सोयाबीन (Soybean)', en: 'Soybean' },
  { id: 'Guar', name: 'Guar', hi: 'ग्वार (Guar)', en: 'Guar (Cluster Bean)' },
  { id: 'Gram', name: 'Gram', hi: 'चना (Gram)', en: 'Gram (Chickpea)' },
  { id: 'Moong', name: 'Moong', hi: 'मूंग (Moong)', en: 'Moong (Green Gram)' },
  { id: 'Cumin', name: 'Cumin', hi: 'जीरा (Cumin)', en: 'Cumin' },
];

export const PricesPage: React.FC = () => {
  const { i18n } = useTranslation();
  const isHindi = i18n.language === 'hi';
  const { farm } = useAuth();

  const [mandi, setMandi] = useState<string>(farm?.district || 'Alwar');
  const [commodity, setCommodity] = useState<string>(farm?.crop || 'Mustard');
  const [days, setDays] = useState<number>(30);

  const [forecast, setForecast] = useState<MandiPriceForecast | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<{ label: string; price: number; type: string } | null>(null);

  // Sync with user's farm profile if available on initial load
  useEffect(() => {
    if (farm?.district) {
      const match = RAJASTHAN_MANDIS.find(
        (m) => m.name.toLowerCase() === farm.district.toLowerCase() || m.district.toLowerCase() === farm.district.toLowerCase()
      );
      if (match) setMandi(match.name);
    }
    if (farm?.crop) {
      const match = COMMODITIES.find((c) => c.id.toLowerCase() === farm.crop.toLowerCase());
      if (match) setCommodity(match.id);
    }
  }, [farm]);

  const fetchForecast = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<MandiPriceForecast>('/forecast/price', {
        params: {
          mandi,
          commodity,
          days,
        },
      });
      setForecast(response.data);
      offlineStorage.saveMandiPrices(response.data);
    } catch (err: any) {
      console.warn('Failed to load mandi price forecast, trying offline cache:', err);
      const cached = offlineStorage.getMandiPrices<MandiPriceForecast>();
      if (cached) {
        setForecast(cached);
      } else {
        setError(
          err?.response?.data?.detail ||
            (isHindi
              ? 'मंडी भाव लोड करने में समस्या आई। कृपया नेटवर्क जांचें।'
              : 'Could not load mandi price forecast. Please check your network.')
        );
      }
    } finally {
      setLoading(false);
    }
  }, [mandi, commodity, days, isHindi]);

  useEffect(() => {
    fetchForecast();
  }, [fetchForecast]);

  // Derived calculations for the SVG Forecast Chart
  const chartData = useMemo(() => {
    if (!forecast || !forecast.history || forecast.history.length === 0) return null;

    const history = forecast.history;
    const latestModal = forecast.latest_modal_price;

    // Combine history with 2-week and 4-week forecast projections
    const histPoints = history.map((h) => ({
      date: h.price_date,
      modal: h.modal_price,
      min: h.min_price,
      max: h.max_price,
      isForecast: false,
    }));

    // Add forecast milestones (+14 days and +28 days)
    const f2w = {
      date: isHindi ? '+2 सप्ताह (अनुमान)' : '+2 Wks (Forecast)',
      modal: forecast.forecast_2_weeks.expected_modal,
      min: forecast.forecast_2_weeks.min_expected,
      max: forecast.forecast_2_weeks.max_expected,
      isForecast: true,
    };

    const f4w = {
      date: isHindi ? '+4 सप्ताह (अनुमान)' : '+4 Wks (Forecast)',
      modal: forecast.forecast_4_weeks.expected_modal,
      min: forecast.forecast_4_weeks.min_expected,
      max: forecast.forecast_4_weeks.max_expected,
      isForecast: true,
    };

    const allPrices = [
      ...histPoints.map((p) => p.modal),
      ...histPoints.map((p) => p.min),
      ...histPoints.map((p) => p.max),
      f2w.min,
      f2w.max,
      f4w.min,
      f4w.max,
    ];

    const minPrice = Math.min(...allPrices);
    const maxPrice = Math.max(...allPrices);
    const padding = (maxPrice - minPrice) * 0.15 || 100;
    const yMin = Math.max(0, Math.floor((minPrice - padding) / 50) * 50);
    const yMax = Math.ceil((maxPrice + padding) / 50) * 50;

    return {
      history: histPoints,
      forecast2w: f2w,
      forecast4w: f4w,
      yMin,
      yMax,
      latestModal,
    };
  }, [forecast, isHindi]);

  // SVG dimensions
  const svgWidth = 720;
  const svgHeight = 280;
  const margin = { top: 20, right: 30, bottom: 40, left: 60 };
  const innerWidth = svgWidth - margin.left - margin.right;
  const innerHeight = svgHeight - margin.top - margin.bottom;

  return (
    <div className="max-w-4xl mx-auto my-6 px-4 space-y-6">
      {/* Page Title & Controls */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-5">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center shadow-inner">
              <IndianRupee className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">
                {isHindi ? 'मंडी भाव एवं 2-4 सप्ताह का पूर्वानुमान' : 'Mandi Prices & 2-4 Week Price Forecast'}
              </h1>
              <p className="text-xs text-slate-500">
                {isHindi
                  ? 'राजस्थान APMC मंडियों के वास्तविक भाव, क्वांटाइल रुझान व विक्रय सलाह'
                  : 'Rajasthan APMC daily prices, quantile forecast bands & sell/wait advisory'}
              </p>
            </div>
          </div>

          <button
            onClick={fetchForecast}
            disabled={loading}
            className="self-start sm:self-center inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-xs font-medium text-slate-700 hover:bg-slate-100 transition disabled:opacity-50"
            title={isHindi ? 'ताज़ा भाव प्राप्त करें' : 'Refresh prices'}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-brand-600' : ''}`} />
            <span>{loading ? (isHindi ? 'अपडेट हो रहा है...' : 'Refreshing...') : isHindi ? 'ताज़ा करें' : 'Refresh'}</span>
          </button>
        </div>

        {/* Selection Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {isHindi ? 'मंडी चुनें (APMC Mandi)' : 'Select APMC Mandi'}
            </label>
            <select
              value={mandi}
              onChange={(e) => setMandi(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white font-medium text-slate-800"
            >
              {RAJASTHAN_MANDIS.map((m) => (
                <option key={m.id} value={m.name}>
                  {isHindi ? m.hi : `${m.name} (${m.district})`}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {isHindi ? 'जिंस चुनें (Commodity)' : 'Select Commodity'}
            </label>
            <select
              value={commodity}
              onChange={(e) => setCommodity(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white font-medium text-slate-800"
            >
              {COMMODITIES.map((c) => (
                <option key={c.id} value={c.id}>
                  {isHindi ? c.hi : c.en}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {isHindi ? 'इतिहास अवधि (Days of History)' : 'History Window'}
            </label>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white text-slate-800"
            >
              <option value={15}>{isHindi ? 'पिछले 15 दिन (15 Days)' : 'Past 15 Days'}</option>
              <option value={30}>{isHindi ? 'पिछले 30 दिन (30 Days)' : 'Past 30 Days'}</option>
              <option value={60}>{isHindi ? 'पिछले 60 दिन (60 Days)' : 'Past 60 Days'}</option>
            </select>
          </div>
        </div>

        {farm?.crop && (
          <div className="mt-3 flex items-center gap-1.5 text-xs text-brand-700 bg-brand-50 px-3 py-1.5 rounded-lg border border-brand-100">
            <Info className="w-3.5 h-3.5 flex-shrink-0" />
            <span>
              {isHindi
                ? `आपके खेत प्रोफ़ाइल (${farm.district} • ${farm.crop}) के अनुसार स्वतः चयनित`
                : `Auto-selected from your farm profile (${farm.district} • ${farm.crop})`}
            </span>
          </div>
        )}
      </div>

      {/* Loading & Error States */}
      {loading && !forecast && (
        <div className="bg-white rounded-2xl p-12 border border-slate-200 text-center">
          <Loader2 className="w-8 h-8 text-brand-600 animate-spin mx-auto mb-2" />
          <p className="text-sm text-slate-600 font-medium">
            {isHindi ? 'मंडी भाव व सांख्यिकीय मॉडल का विश्लेषण जारी है...' : 'Fetching mandi rates and running forecast models...'}
          </p>
        </div>
      )}

      {error && (
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-5 text-rose-800 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
          <div>
            <div className="text-sm font-bold">{isHindi ? 'डेटा प्राप्त करने में त्रुटि' : 'Error fetching data'}</div>
            <div className="text-xs mt-0.5">{error}</div>
          </div>
        </div>
      )}

      {forecast && (
        <div
          key={`${forecast.mandi}-${forecast.commodity}-${forecast.latest_modal_price}-${days}`}
          className="space-y-6"
        >
          {/* Key Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 1. Latest Modal */}
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <div className="text-xs text-slate-500 font-medium">
                  {isHindi ? 'वर्तमान मॉडल भाव' : 'Latest Modal Price'}
                </div>
                <div className="text-2xl font-bold text-slate-900 mt-1">
                  ₹{forecast.latest_modal_price.toFixed(0)}{' '}
                  <span className="text-xs font-normal text-slate-500">/क्विंटल</span>
                </div>
              </div>
              <div className="text-[11px] text-slate-400 mt-2 flex items-center gap-1 border-t border-slate-100 pt-2">
                <Calendar className="w-3 h-3" />
                <span>{forecast.latest_date}</span>
              </div>
            </div>

            {/* 2. 2-Week Forecast */}
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <div className="text-xs text-slate-500 font-medium">
                  {isHindi ? '2 सप्ताह का दायरा (q10 - q90)' : '2-Week Expected Band'}
                </div>
                <div className="text-lg font-bold text-brand-700 mt-1">
                  ₹{forecast.forecast_2_weeks.min_expected.toFixed(0)} - ₹
                  {forecast.forecast_2_weeks.max_expected.toFixed(0)}
                </div>
              </div>
              <div className="text-[11px] text-slate-600 mt-2 border-t border-slate-100 pt-2">
                {isHindi ? 'अनुमानित मध्य:' : 'Expected Mid:'}{' '}
                <span className="font-semibold text-slate-800">
                  ₹{forecast.forecast_2_weeks.expected_modal.toFixed(0)}
                </span>
              </div>
            </div>

            {/* 3. 4-Week Forecast */}
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <div className="text-xs text-slate-500 font-medium">
                  {isHindi ? '4 सप्ताह का दायरा (q10 - q90)' : '4-Week Expected Band'}
                </div>
                <div className="text-lg font-bold text-indigo-700 mt-1">
                  ₹{forecast.forecast_4_weeks.min_expected.toFixed(0)} - ₹
                  {forecast.forecast_4_weeks.max_expected.toFixed(0)}
                </div>
              </div>
              <div className="text-[11px] text-slate-600 mt-2 border-t border-slate-100 pt-2">
                {isHindi ? 'अनुमानित मध्य:' : 'Expected Mid:'}{' '}
                <span className="font-semibold text-slate-800">
                  ₹{forecast.forecast_4_weeks.expected_modal.toFixed(0)}
                </span>
              </div>
            </div>

            {/* 4. Market Trend Badge */}
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <div className="text-xs text-slate-500 font-medium">
                  {isHindi ? 'बाजार का संभावित रुख' : 'Projected Market Trend'}
                </div>
                <div className="mt-1.5 flex items-center gap-2">
                  {forecast.trend === 'bullish' ? (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-700" />
                      <span>{isHindi ? 'तेजी (बढ़त)' : 'Bullish (Rising)'}</span>
                    </span>
                  ) : forecast.trend === 'bearish' ? (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200">
                      <TrendingDown className="w-3.5 h-3.5 text-rose-700" />
                      <span>{isHindi ? 'मंदी (गिरावट)' : 'Bearish (Softening)'}</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-200">
                      <Minus className="w-3.5 h-3.5 text-blue-700" />
                      <span>{isHindi ? 'स्थिर (समान)' : 'Stable / Flat'}</span>
                    </span>
                  )}
                </div>
              </div>
              <div className="text-[11px] text-slate-400 mt-2 border-t border-slate-100 pt-2 font-mono">
                Model: {forecast.model_version}
              </div>
            </div>
          </div>

          {/* Sell Now vs Wait Advisory Card */}
          <div
            className={`rounded-2xl p-5 border shadow-sm ${
              forecast.recommendation === 'wait'
                ? 'bg-gradient-to-br from-emerald-50 to-teal-50/50 border-emerald-200'
                : forecast.recommendation === 'sell_now'
                ? 'bg-gradient-to-br from-amber-50 to-orange-50/50 border-amber-200'
                : 'bg-gradient-to-br from-blue-50 to-sky-50/50 border-blue-200'
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm ${
                    forecast.recommendation === 'wait'
                      ? 'bg-emerald-600 text-white'
                      : forecast.recommendation === 'sell_now'
                      ? 'bg-amber-600 text-white'
                      : 'bg-blue-600 text-white'
                  }`}
                >
                  {forecast.recommendation === 'wait' ? (
                    <Clock className="w-5 h-5" />
                  ) : forecast.recommendation === 'sell_now' ? (
                    <ShoppingCart className="w-5 h-5" />
                  ) : (
                    <Scale className="w-5 h-5" />
                  )}
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      {isHindi ? 'निर्णय सहयोग सलाह (Decision Support Hint)' : 'Farmer Decision Support Hint'}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-bold uppercase ${
                        forecast.recommendation === 'wait'
                          ? 'bg-emerald-200 text-emerald-900'
                          : forecast.recommendation === 'sell_now'
                          ? 'bg-amber-200 text-amber-900'
                          : 'bg-blue-200 text-blue-900'
                      }`}
                    >
                      {forecast.recommendation === 'wait'
                        ? isHindi
                          ? 'रुकें (Wait)'
                          : 'Wait'
                        : forecast.recommendation === 'sell_now'
                        ? isHindi
                          ? 'तुरंत बेचें (Sell Now)'
                          : 'Sell Now'
                        : isHindi
                        ? 'सामान्य (Hold)'
                        : 'Hold'}
                    </span>
                  </div>

                  <p className="text-sm font-semibold text-slate-900 mt-1">
                    {forecast.recommendation_text || forecast.explanation}
                  </p>
                  <p className="text-xs text-slate-600 mt-1">{forecast.explanation}</p>
                </div>
              </div>
            </div>

            {/* Mandatory Market Risk Guidance Notice */}
            <div className="mt-4 pt-3 border-t border-slate-200/60 flex items-start gap-2 text-[11px] text-slate-600">
              <ShieldAlert className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <span>{forecast.disclaimer}</span>
            </div>
          </div>

          {/* Forecast & Uncertainty Band Chart (Clean Interactive SVG) */}
          {chartData && (
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
                <div>
                  <h2 className="text-base font-bold text-slate-900">
                    {isHindi ? 'मूल्य प्रवृत्ति एवं अनिश्चितता दायरा (Price Trajectory & Forecast Band)' : 'Price Trajectory & Forecast Band'}
                  </h2>
                  <p className="text-xs text-slate-500">
                    {isHindi
                      ? 'नीली रेखा: ऐतिहासिक दैनिक भाव • बैंगनी क्षेत्र: 80% क्वांटाइल संभावित दायरा'
                      : 'Blue line: Historical modal rates • Shaded band: 80% Quantile uncertainty interval (q10 to q90)'}
                  </p>
                </div>

                {/* Legend */}
                <div className="flex items-center gap-4 text-xs text-slate-600">
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-blue-600 inline-block rounded" />
                    <span>{isHindi ? 'दैनिक भाव' : 'Historical Modal'}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 border-t-2 border-dashed border-indigo-600 inline-block" />
                    <span>{isHindi ? 'पूर्वानुमान' : 'Forecast Modal'}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-3 bg-indigo-100 border border-indigo-300 rounded inline-block" />
                    <span>{isHindi ? 'संभावित दायरा' : 'Forecast Band'}</span>
                  </div>
                </div>
              </div>

              {/* Responsive SVG Chart */}
              <div className="relative overflow-x-auto">
                <svg
                  viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                  className="w-full h-auto min-w-[600px] select-none"
                >
                  <defs>
                    <linearGradient id="bandGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor="#818cf8" stopOpacity="0.35" />
                      <stop offset="100%" stopColor="#c7d2fe" stopOpacity="0.10" />
                    </linearGradient>
                  </defs>

                  {/* Background grid lines */}
                  {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
                    const priceVal = chartData.yMin + pct * (chartData.yMax - chartData.yMin);
                    const yPos = margin.top + innerHeight - pct * innerHeight;
                    return (
                      <g key={i}>
                        <line
                          x1={margin.left}
                          y1={yPos}
                          x2={svgWidth - margin.right}
                          y2={yPos}
                          stroke="#e2e8f0"
                          strokeDasharray="3 3"
                        />
                        <text
                          x={margin.left - 8}
                          y={yPos + 4}
                          textAnchor="end"
                          className="text-[10px] fill-slate-400 font-mono"
                        >
                          ₹{priceVal.toFixed(0)}
                        </text>
                      </g>
                    );
                  })}

                  {/* Calculations for points */}
                  {(() => {
                    const totalPoints = chartData.history.length + 2; // history + 2 forecast milestones
                    const stepX = innerWidth / (totalPoints - 1);

                    const getY = (price: number) => {
                      const ratio = (price - chartData.yMin) / (chartData.yMax - chartData.yMin);
                      return margin.top + innerHeight - ratio * innerHeight;
                    };

                    const getX = (idx: number) => margin.left + idx * stepX;

                    // Historical points
                    const histCoords = chartData.history.map((h, idx) => ({
                      x: getX(idx),
                      y: getY(h.modal),
                      label: h.date,
                      price: h.modal,
                    }));

                    // Transition from last historical point to +2wk and +4wk
                    const lastHistIdx = chartData.history.length - 1;
                    const lastHistCoord = histCoords[lastHistIdx];
                    const idx2w = lastHistIdx + 1;
                    const idx4w = lastHistIdx + 2;

                    const coord2wModal = { x: getX(idx2w), y: getY(chartData.forecast2w.modal) };
                    const coord4wModal = { x: getX(idx4w), y: getY(chartData.forecast4w.modal) };

                    const coord2wMin = { x: getX(idx2w), y: getY(chartData.forecast2w.min) };
                    const coord2wMax = { x: getX(idx2w), y: getY(chartData.forecast2w.max) };

                    const coord4wMin = { x: getX(idx4w), y: getY(chartData.forecast4w.min) };
                    const coord4wMax = { x: getX(idx4w), y: getY(chartData.forecast4w.max) };

                    // Polygon path for shaded forecast band
                    const bandPath = `
                      M ${lastHistCoord.x} ${lastHistCoord.y}
                      L ${coord2wMax.x} ${coord2wMax.y}
                      L ${coord4wMax.x} ${coord4wMax.y}
                      L ${coord4wMin.x} ${coord4wMin.y}
                      L ${coord2wMin.x} ${coord2wMin.y}
                      Z
                    `;

                    // Historical path string
                    const histPathStr = histCoords.reduce(
                      (acc, p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`),
                      ''
                    );

                    // Forecast dashed path string
                    const forecastPathStr = `
                      M ${lastHistCoord.x} ${lastHistCoord.y}
                      L ${coord2wModal.x} ${coord2wModal.y}
                      L ${coord4wModal.x} ${coord4wModal.y}
                    `;

                    return (
                      <g>
                        {/* Shaded Forecast Band */}
                        <path d={bandPath} fill="url(#bandGradient)" stroke="#818cf8" strokeWidth="1" strokeDasharray="2 2" />

                        {/* Forecast Center Line (Dashed) */}
                        <path
                          d={forecastPathStr}
                          fill="none"
                          stroke="#4f46e5"
                          strokeWidth="2.5"
                          strokeDasharray="5 5"
                        />

                        {/* Historical Line (Solid) */}
                        <path d={histPathStr} fill="none" stroke="#2563eb" strokeWidth="2.5" />

                        {/* Historical Dots */}
                        {histCoords.map((p, idx) => (
                          <circle
                            key={`hist-${idx}`}
                            cx={p.x}
                            cy={p.y}
                            r={3}
                            className="fill-blue-600 hover:fill-blue-800 transition cursor-pointer"
                            onMouseEnter={() =>
                              setHoveredPoint({
                                label: p.label,
                                price: p.price,
                                type: isHindi ? 'वास्तविक मॉडल भाव' : 'Actual Modal Price',
                              })
                            }
                            onMouseLeave={() => setHoveredPoint(null)}
                          />
                        ))}

                        {/* Forecast Dots */}
                        {/* +2 Wks Point */}
                        <circle
                          cx={coord2wModal.x}
                          cy={coord2wModal.y}
                          r={5}
                          className="fill-indigo-600 stroke-2 stroke-white cursor-pointer"
                          onMouseEnter={() =>
                            setHoveredPoint({
                              label: chartData.forecast2w.date,
                              price: chartData.forecast2w.modal,
                              type: isHindi
                                ? `2-सप्ताह मध्य (दायरा ₹${chartData.forecast2w.min.toFixed(0)} - ₹${chartData.forecast2w.max.toFixed(0)})`
                                : `2-Week Mid (Band ₹${chartData.forecast2w.min.toFixed(0)} - ₹${chartData.forecast2w.max.toFixed(0)})`,
                            })
                          }
                          onMouseLeave={() => setHoveredPoint(null)}
                        />
                        {/* +4 Wks Point */}
                        <circle
                          cx={coord4wModal.x}
                          cy={coord4wModal.y}
                          r={5}
                          className="fill-indigo-600 stroke-2 stroke-white cursor-pointer"
                          onMouseEnter={() =>
                            setHoveredPoint({
                              label: chartData.forecast4w.date,
                              price: chartData.forecast4w.modal,
                              type: isHindi
                                ? `4-सप्ताह मध्य (दायरा ₹${chartData.forecast4w.min.toFixed(0)} - ₹${chartData.forecast4w.max.toFixed(0)})`
                                : `4-Week Mid (Band ₹${chartData.forecast4w.min.toFixed(0)} - ₹${chartData.forecast4w.max.toFixed(0)})`,
                            })
                          }
                          onMouseLeave={() => setHoveredPoint(null)}
                        />

                        {/* X-Axis Labels */}
                        <text
                          x={lastHistCoord.x}
                          y={svgHeight - margin.bottom + 16}
                          textAnchor="middle"
                          className="text-[10px] fill-slate-500 font-medium"
                        >
                          {chartData.history[chartData.history.length - 1].date}
                        </text>
                        <text
                          x={coord2wModal.x}
                          y={svgHeight - margin.bottom + 16}
                          textAnchor="middle"
                          className="text-[10px] fill-indigo-700 font-bold"
                        >
                          +14D (2 Wk)
                        </text>
                        <text
                          x={coord4wModal.x}
                          y={svgHeight - margin.bottom + 16}
                          textAnchor="middle"
                          className="text-[10px] fill-indigo-700 font-bold"
                        >
                          +28D (4 Wk)
                        </text>
                      </g>
                    );
                  })()}
                </svg>

                {/* Hover Tooltip Overlay */}
                {hoveredPoint && (
                  <div className="absolute top-2 right-4 bg-slate-900/90 backdrop-blur-sm text-white px-3 py-1.5 rounded-lg text-xs shadow-lg pointer-events-none border border-slate-700">
                    <div className="font-semibold">{hoveredPoint.label}</div>
                    <div className="text-amber-300 font-mono text-sm">₹{hoveredPoint.price.toFixed(0)} / Qtl</div>
                    <div className="text-[10px] text-slate-300">{hoveredPoint.type}</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Recent APMC Daily Price Table */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-bold text-slate-800">
                  {isHindi ? 'हालिया दैनिक मंडी भाव (APMC Daily Records)' : 'Recent APMC Mandi Records'}
                </h2>
                <p className="text-xs text-slate-500">
                  {isHindi
                    ? `${mandi} मंडी में ${commodity} के सत्यापित दैनिक लेन-देन भाव`
                    : `Verified daily transaction prices for ${commodity} in ${mandi}`}
                </p>
              </div>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                Model: {forecast.model_version}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-3">{isHindi ? 'दिनांक' : 'Date'}</th>
                    <th className="py-2.5 px-3">{isHindi ? 'न्यूनतम भाव (₹)' : 'Min Price (₹)'}</th>
                    <th className="py-2.5 px-3">{isHindi ? 'अधिकतम भाव (₹)' : 'Max Price (₹)'}</th>
                    <th className="py-2.5 px-3 font-bold text-slate-900">{isHindi ? 'मॉडल भाव (₹)' : 'Modal Price (₹)'}</th>
                    <th className="py-2.5 px-3">{isHindi ? 'आवक (क्विंटल)' : 'Arrivals (Qtl)'}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {forecast.history
                    .slice()
                    .reverse()
                    .slice(0, 10)
                    .map((row: MandiPriceRecord, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-50/60 transition">
                        <td className="py-2.5 px-3 font-medium text-slate-800">{row.price_date}</td>
                        <td className="py-2.5 px-3 text-slate-600">₹{row.min_price.toFixed(0)}</td>
                        <td className="py-2.5 px-3 text-slate-600">₹{row.max_price.toFixed(0)}</td>
                        <td className="py-2.5 px-3 font-bold text-brand-700">₹{row.modal_price.toFixed(0)}</td>
                        <td className="py-2.5 px-3 text-slate-600">{row.arrivals ?? '-'}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>

            <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600 flex items-center justify-between">
              <span>
                {isHindi
                  ? 'स्रोत: Agmarknet / राजस्थान कृषि विपणन बोर्ड (RSAMB)'
                  : 'Source: Agmarknet / Rajasthan State Agricultural Marketing Board (RSAMB)'}
              </span>
              <span className="font-mono text-[10px] text-slate-400">
                KisanSathi Price Engine v1.0
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default PricesPage;
