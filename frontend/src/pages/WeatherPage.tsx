import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  CloudSun,
  Droplets,
  AlertTriangle,
  Info,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  Loader2,
  Wind,
  Thermometer,
  CloudRain,
  Flame,
  Snowflake,
  Clock,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../services/api';
import { offlineStorage } from '../services/offlineStorage';
import { IrrigationSchedule } from '../types';

const RAJASTHAN_DISTRICTS = [
  'Ajmer', 'Alwar', 'Anupgarh', 'Balotra', 'Banswara', 'Baran', 'Barmer', 'Beawar',
  'Bharatpur', 'Bhilwara', 'Bikaner', 'Bundi', 'Chittorgarh', 'Churu', 'Dausa', 'Deeg',
  'Didwana-Kuchaman', 'Dholpur', 'Dungarpur', 'Hanumangarh', 'Jaipur', 'Jaisalmer',
  'Jalore', 'Jhalawar', 'Jhunjhunu', 'Jodhpur', 'Karauli', 'Kekri', 'Khairthal-Tijara',
  'Kota', 'Kotputli-Behror', 'Nagaur', 'Pali', 'Phalodi', 'Pratapgarh', 'Rajsamand',
  'Salumbar', 'Sanchore', 'Sawai Madhopur', 'Sikar', 'Sirohi', 'Sri Ganganagar', 'Tonk', 'Udaipur'
];

const CROPS = [
  { id: 'Mustard', name: 'Mustard', hi: 'सरसों (Mustard)' },
  { id: 'Wheat', name: 'Wheat', hi: 'गेहूं (Wheat)' },
  { id: 'Bajra', name: 'Bajra', hi: 'बाजरा (Bajra)' },
  { id: 'Soybean', name: 'Soybean', hi: 'सोयाबीन (Soybean)' },
  { id: 'Gram', name: 'Gram', hi: 'चना (Gram)' },
  { id: 'Guar', name: 'Guar', hi: 'ग्वार (Guar)' },
];

const IRRIGATION_METHODS = [
  { id: 'tubewell', name: 'Tubewell (नलकूप - 75% efficiency)' },
  { id: 'canal', name: 'Canal (नहर - 60% efficiency)' },
  { id: 'well', name: 'Open Well (कुआं - 70% efficiency)' },
  { id: 'drip', name: 'Drip (ड्रिप / बूंद-बूंद - 90% efficiency)' },
  { id: 'sprinkler', name: 'Sprinkler (फव्वारा - 80% efficiency)' },
  { id: 'rainfed', name: 'Rainfed (वर्षा आधारित - 55% efficiency)' },
];

export const WeatherPage: React.FC = () => {
  const { i18n } = useTranslation();
  const isHindi = i18n.language === 'hi';
  const { farm } = useAuth();

  const [district, setDistrict] = useState<string>(farm?.district || 'Kota');
  const [crop, setCrop] = useState<string>(farm?.crop || 'Mustard');
  const [sowingDate, setSowingDate] = useState<string>(
    farm?.sowing_date ||
      new Date(Date.now() - 35 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [irrigationType, setIrrigationType] = useState<string>(farm?.irrigation || 'tubewell');

  const [schedule, setSchedule] = useState<IrrigationSchedule | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Sync with user's farm profile on initial load
  useEffect(() => {
    if (farm?.district) setDistrict(farm.district);
    if (farm?.crop) setCrop(farm.crop);
    if (farm?.sowing_date) setSowingDate(farm.sowing_date);
    if (farm?.irrigation) setIrrigationType(farm.irrigation);
  }, [farm]);

  const fetchSchedule = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<IrrigationSchedule>('/advice/weather', {
        params: {
          district,
          crop,
          sowing_date: sowingDate,
          irrigation_type: irrigationType,
        },
      });
      setSchedule(response.data);
      offlineStorage.saveWeatherAdvice(response.data);
    } catch (err: any) {
      console.warn('Weather advice fetch failed, attempting to read offline cache:', err);
      const cached = offlineStorage.getWeatherAdvice<IrrigationSchedule>();
      if (cached) {
        setSchedule(cached);
      } else {
        setError(
          err?.response?.data?.detail ||
            (isHindi
              ? 'मौसम व सिंचाई सलाह प्राप्त करने में त्रुटि आई। कृपया नेटवर्क जांचें।'
              : 'Could not fetch weather and irrigation schedule. Please check connection.')
        );
      }
    } finally {
      setLoading(false);
    }
  }, [district, crop, sowingDate, irrigationType, isHindi]);

  useEffect(() => {
    fetchSchedule();
  }, [fetchSchedule]);

  return (
    <div className="max-w-4xl mx-auto my-6 px-4 space-y-6">
      {/* Page Title & Context Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-teal-100 text-teal-800 flex items-center justify-center shadow-inner">
              <CloudSun className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">
                {isHindi ? 'मौसम अलर्ट एवं FAO-56 वैज्ञानिक सिंचाई अनुसूची' : 'Weather Alerts & FAO-56 Irrigation Advisory'}
              </h1>
              <p className="text-xs text-slate-500">
                {isHindi
                  ? 'Open-Meteo मौसम पूर्वानुमान, कृषि-मौसम चेतावनी नियम एवं FAO-56 वाष्पोत्सर्जन भौतिकी मॉडल'
                  : 'Open-Meteo real-time forecast, agro-met rules & FAO-56 Penman-Monteith physics'}
              </p>
            </div>
          </div>

          <button
            onClick={fetchSchedule}
            disabled={loading}
            className="self-start sm:self-center inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-xs font-medium text-slate-700 hover:bg-slate-100 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-brand-600' : ''}`} />
            <span>{loading ? (isHindi ? 'अपडेट हो रहा है...' : 'Updating...') : isHindi ? 'ताज़ा करें' : 'Refresh'}</span>
          </button>
        </div>

        {/* Input Parameters */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {isHindi ? 'जिला चुनें (District)' : 'District'}
            </label>
            <select
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white font-medium text-slate-800"
            >
              {RAJASTHAN_DISTRICTS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {isHindi ? 'फसल चुनें (Crop)' : 'Crop'}
            </label>
            <select
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white font-medium text-slate-800"
            >
              {CROPS.map((c) => (
                <option key={c.id} value={c.id}>
                  {isHindi ? c.hi : c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {isHindi ? 'बुवाई दिनांक (Sowing Date)' : 'Sowing Date'}
            </label>
            <input
              type="date"
              value={sowingDate}
              onChange={(e) => setSowingDate(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white text-slate-800"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {isHindi ? 'सिंचाई साधन (Method)' : 'Irrigation Method'}
            </label>
            <select
              value={irrigationType}
              onChange={(e) => setIrrigationType(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white text-slate-800 text-xs"
            >
              {IRRIGATION_METHODS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {farm?.district && (
          <div className="mt-3 flex items-center gap-1.5 text-xs text-brand-700 bg-brand-50 px-3 py-1.5 rounded-lg border border-brand-100">
            <Info className="w-3.5 h-3.5 flex-shrink-0" />
            <span>
              {isHindi
                ? `आपके खेत प्रोफ़ाइल (${farm.district} • ${farm.crop} • बुवाई ${farm.sowing_date}) से स्वतः चयनित`
                : `Auto-selected from your farm profile (${farm.district} • ${farm.crop} • sown ${farm.sowing_date})`}
            </span>
          </div>
        )}
      </div>

      {/* Explicit Scientific Disclaimer: Physics & Agronomic Rules (Zero Black-box ML) */}
      <div className="p-3.5 bg-slate-900 text-white rounded-xl text-xs flex items-center gap-2.5 shadow-sm">
        <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
        <div className="leading-relaxed">
          <span className="font-bold text-amber-300">
            {isHindi ? 'वैज्ञानिक कार्यप्रणाली (Methodology):' : 'Scientific Methodology:'}
          </span>{' '}
          {isHindi
            ? 'यह मॉड्यूल 100% भौतिकी एवं कृषि विज्ञान नियमों (FAO-56 Penman-Monteith वाष्पोत्सर्जन समीकरण व राजस्थान कृषि विश्वविद्यालय के नियमों) पर आधारित है। इसमें कोई अनपेक्षित ब्लैक-बॉक्स मशीन लर्निंग (ML) नहीं है।'
            : 'This module is 100% rule- and physics-based (FAO-56 Penman-Monteith ET0 equation & Rajasthan State Agricultural University packages of practices), completely free of unverified black-box ML.'}
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && !schedule && (
        <div className="bg-white rounded-2xl p-12 border border-slate-200 text-center">
          <Loader2 className="w-8 h-8 text-brand-600 animate-spin mx-auto mb-2" />
          <p className="text-sm text-slate-600 font-medium">
            {isHindi ? 'Open-Meteo मौसम डेटा व FAO-56 जल संतुलन की गणना जारी है...' : 'Calculating FAO-56 water balance and fetching Open-Meteo weather...'}
          </p>
        </div>
      )}

      {error && (
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-4 text-rose-800 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
          <div className="text-xs">{error}</div>
        </div>
      )}

      {schedule && (
        <div
          key={`${schedule.district}-${schedule.crop}-${sowingDate}-${irrigationType}`}
          className="space-y-6"
        >
          {/* Active Crop-Stage Weather Alerts */}
          {schedule.alerts && schedule.alerts.length > 0 ? (
            <div className="space-y-3">
              {schedule.alerts.map((alert, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border shadow-sm flex items-start gap-3 ${
                    alert.severity === 'critical'
                      ? 'bg-rose-50 border-rose-300 text-rose-950'
                      : alert.severity === 'warning'
                      ? 'bg-amber-50 border-amber-300 text-amber-950'
                      : 'bg-blue-50 border-blue-200 text-blue-950'
                  }`}
                >
                  <div className="mt-0.5 flex-shrink-0">
                    {alert.alert_type.includes('Frost') || alert.alert_type.includes('पाला') ? (
                      <Snowflake className="w-5 h-5 text-indigo-600" />
                    ) : alert.alert_type.includes('Heat') || alert.alert_type.includes('लू') ? (
                      <Flame className="w-5 h-5 text-rose-600" />
                    ) : alert.alert_type.includes('Rain') || alert.alert_type.includes('वर्षा') ? (
                      <CloudRain className="w-5 h-5 text-blue-600" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-amber-700" />
                    )}
                  </div>

                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm">{alert.alert_type}</span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                          alert.severity === 'critical'
                            ? 'bg-rose-200 text-rose-900'
                            : alert.severity === 'warning'
                            ? 'bg-amber-200 text-amber-900'
                            : 'bg-blue-200 text-blue-900'
                        }`}
                      >
                        {alert.severity}
                      </span>
                    </div>

                    <p className="text-xs leading-relaxed">{alert.message}</p>

                    {alert.source && (
                      <div className="text-[11px] text-slate-500 pt-1 border-t border-slate-200/60 font-medium">
                        {isHindi ? 'स्रोत:' : 'Source:'} {alert.source}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-900 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>
                {isHindi
                  ? 'मौसम अनुकूल है: वर्तमान में पाला, अति-ताप अथवा गंभीर फफूंद रोग का कोई तात्कालिक अलर्ट सक्रिय नहीं है।'
                  : 'Favourable weather: No frost, severe heat, or active disease-fostering conditions currently detected.'}
              </span>
            </div>
          )}

          {/* Today's Weather Snapshot KPIs */}
          {schedule.weather_summary && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-orange-100 text-orange-700 flex items-center justify-center flex-shrink-0">
                  <Thermometer className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-[11px] text-slate-500 font-medium">{isHindi ? 'तापमान (अधिकतम/न्यूनतम)' : 'Temp Max / Min'}</div>
                  <div className="text-base font-bold text-slate-900">
                    {schedule.weather_summary.temp_max.toFixed(1)}° / {schedule.weather_summary.temp_min.toFixed(1)}°C
                  </div>
                </div>
              </div>

              <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center flex-shrink-0">
                  <Droplets className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-[11px] text-slate-500 font-medium">{isHindi ? 'सापेक्ष आर्द्रता (Humidity)' : 'Relative Humidity'}</div>
                  <div className="text-base font-bold text-slate-900">
                    {schedule.weather_summary.humidity.toFixed(0)}%
                  </div>
                </div>
              </div>

              <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center flex-shrink-0">
                  <Wind className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-[11px] text-slate-500 font-medium">{isHindi ? 'हवा की गति (Wind)' : 'Wind Speed'}</div>
                  <div className="text-base font-bold text-slate-900">
                    {schedule.weather_summary.wind_speed.toFixed(1)} km/h
                  </div>
                </div>
              </div>

              <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center flex-shrink-0">
                  <CloudRain className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-[11px] text-slate-500 font-medium">{isHindi ? '72h संभावित वर्षा' : '72h Rain Forecast'}</div>
                  <div className="text-base font-bold text-slate-900">
                    {schedule.weather_summary.precipitation_72h.toFixed(1)} mm
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* FAO-56 Crop Water Balance Card */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Droplets className="w-5 h-5 text-brand-600" />
                <h2 className="text-base font-bold text-slate-800">
                  {isHindi ? 'फसल जल संतुलन एवं सिंचाई समय-सारणी' : 'FAO-56 Crop Water Balance & Schedule'}
                </h2>
              </div>
              <span className="text-[11px] font-semibold bg-emerald-100 text-emerald-800 px-3 py-1 rounded-full self-start sm:self-auto font-mono">
                FAO Irrigation Paper No. 56
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <div className="text-xs text-slate-500 font-medium">{isHindi ? 'फसल अवस्था (Growth Stage)' : 'Growth Stage'}</div>
                <div className="text-sm font-bold text-slate-900 mt-1">{schedule.current_growth_stage}</div>
                <div className="text-[11px] text-slate-400 mt-1">
                  {isHindi ? `बुवाई से ${schedule.days_since_sowing} दिन` : `${schedule.days_since_sowing} days since sowing`}
                </div>
              </div>

              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <div className="text-xs text-slate-500 font-medium">{isHindi ? 'फसल गुणांक (Crop Coefficient)' : 'Crop Kc Factor'}</div>
                <div className="text-xl font-bold text-slate-900 mt-1">{schedule.kc_factor.toFixed(2)}</div>
                <div className="text-[11px] text-slate-400 mt-1">
                  {isHindi ? `संदर्भ ET₀: ${schedule.et0_mm_day} मिमी/दिन` : `Ref ET0: ${schedule.et0_mm_day} mm/day`}
                </div>
              </div>

              <div className="p-4 bg-brand-50 rounded-xl border border-brand-100">
                <div className="text-xs text-brand-800 font-medium">{isHindi ? 'दैनिक फसल जल खपत (ETc)' : 'Daily Crop Water Use (ETc)'}</div>
                <div className="text-2xl font-extrabold text-brand-900 mt-1">
                  {schedule.crop_etc_mm_day.toFixed(2)} <span className="text-xs font-semibold">मिमी/दिन</span>
                </div>
                <div className="text-[11px] text-brand-700 mt-1">Kc × ET₀ वाष्पोत्सर्जन</div>
              </div>
            </div>

            {/* Actionable Irrigation Countdown Card */}
            <div
              className={`p-5 rounded-xl border ${
                schedule.irrigation_urgency === 'withhold_due_to_rain'
                  ? 'bg-purple-50 border-purple-200 text-purple-950'
                  : schedule.irrigation_urgency === 'immediate'
                  ? 'bg-rose-50 border-rose-200 text-rose-950'
                  : schedule.irrigation_urgency === 'due_soon'
                  ? 'bg-amber-50 border-amber-200 text-amber-950'
                  : 'bg-emerald-50 border-emerald-200 text-emerald-950'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-brand-700" />
                  <span className="font-bold text-sm">
                    {isHindi ? 'सिंचाई समय-सीमा (Irrigation Urgency):' : 'Irrigation Action Window:'}
                  </span>
                </div>

                <span
                  className={`text-xs px-3 py-1 rounded-full font-bold uppercase self-start sm:self-auto ${
                    schedule.irrigation_urgency === 'withhold_due_to_rain'
                      ? 'bg-purple-200 text-purple-900'
                      : schedule.irrigation_urgency === 'immediate'
                      ? 'bg-rose-200 text-rose-900'
                      : schedule.irrigation_urgency === 'due_soon'
                      ? 'bg-amber-200 text-amber-900'
                      : 'bg-emerald-200 text-emerald-900'
                  }`}
                >
                  {schedule.irrigation_urgency === 'withhold_due_to_rain'
                    ? isHindi ? 'सिंचाई स्थगित रखें' : 'Withhold (Rain Forecast)'
                    : schedule.irrigation_urgency === 'immediate'
                    ? isHindi ? 'तुरंत सिंचाई आवश्यक' : 'Immediate'
                    : schedule.irrigation_urgency === 'due_soon'
                    ? isHindi ? 'शीघ्र सिंचाई करें' : 'Due Soon'
                    : isHindi ? 'सामान्य' : 'Normal'}
                </span>
              </div>

              <p className="text-xs leading-relaxed font-medium mt-1">{schedule.advisory_text}</p>

              <div className="mt-3 pt-3 border-t border-slate-200/60 flex flex-wrap items-center justify-between text-xs font-semibold gap-2">
                <span>
                  {isHindi ? 'आगामी सिंचाई:' : 'Next Irrigation in:'}{' '}
                  <span className="text-brand-800 font-bold">{schedule.next_irrigation_due_days} {isHindi ? 'दिन' : 'days'}</span>
                </span>
                <span>
                  {isHindi ? 'अनुशंसित सिंचाई गहराई:' : 'Gross Application Depth:'}{' '}
                  <span className="text-brand-800 font-bold">{schedule.water_depth_mm} mm</span>
                </span>
              </div>
            </div>

            {/* 7-Day Mini Weather Forecast Strip */}
            {schedule.weather_summary?.forecast_days && schedule.weather_summary.forecast_days.length > 0 && (
              <div className="pt-2">
                <div className="text-xs font-bold text-slate-700 mb-2.5">
                  {isHindi ? 'आगामी 7 दिनों का मौसम पूर्वानुमान (Open-Meteo):' : '7-Day Weather Forecast (Open-Meteo):'}
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
                  {schedule.weather_summary.forecast_days.map((fd, i) => (
                    <div key={i} className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-center">
                      <div className="text-[11px] font-bold text-slate-700">{fd.date.slice(5)}</div>
                      <div className="text-xs font-bold text-slate-900 mt-1">{fd.temp_max.toFixed(0)}° / {fd.temp_min.toFixed(0)}°</div>
                      <div className="text-[10px] text-blue-600 mt-0.5">
                        {fd.rain_mm > 0 ? `🌧️ ${fd.rain_mm.toFixed(1)}mm` : '☀️ शुष्क'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default WeatherPage;
