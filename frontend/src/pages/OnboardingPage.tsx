import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { MapPin, Save, Sprout, Info, CheckCircle2, AlertCircle, ArrowLeft } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../services/api';
import { offlineStorage } from '../services/offlineStorage';
import type { FarmProfile } from '../types';

// 41 Official Districts of Rajasthan as configured in backend/reference/districts.json
const RAJASTHAN_41_DISTRICTS = [
  { id: 'ajmer', en: 'Ajmer', hi: 'अजमेर', zone: 'III-A' },
  { id: 'alwar', en: 'Alwar', hi: 'अलवर', zone: 'III-B' },
  { id: 'anupgarh', en: 'Anupgarh', hi: 'अनूपगढ़', zone: 'I-B' },
  { id: 'balotra', en: 'Balotra', hi: 'बालोतरा', zone: 'II-B' },
  { id: 'banswara', en: 'Banswara', hi: 'बांसवाड़ा', zone: 'IV-B' },
  { id: 'baran', en: 'Baran', hi: 'बारां', zone: 'V' },
  { id: 'barmer', en: 'Barmer', hi: 'बाड़मेर', zone: 'II-B' },
  { id: 'beawar', en: 'Beawar', hi: 'ब्यावर', zone: 'III-A' },
  { id: 'bharatpur', en: 'Bharatpur', hi: 'भरतपुर', zone: 'III-B' },
  { id: 'bhilwara', en: 'Bhilwara', hi: 'भीलवाड़ा', zone: 'IV-A' },
  { id: 'bikaner', en: 'Bikaner', hi: 'बीकानेर', zone: 'I-C' },
  { id: 'bundi', en: 'Bundi', hi: 'बूंदी', zone: 'V' },
  { id: 'chittorgarh', en: 'Chittorgarh', hi: 'चित्तौड़गढ़', zone: 'IV-B' },
  { id: 'churu', en: 'Churu', hi: 'चूरू', zone: 'I-C' },
  { id: 'dausa', en: 'Dausa', hi: 'दौसा', zone: 'III-A' },
  { id: 'deeg', en: 'Deeg', hi: 'डीग', zone: 'III-B' },
  { id: 'didwana_kuchaman', en: 'Didwana-Kuchaman', hi: 'डीडवाना-कुचामन', zone: 'II-A' },
  { id: 'dholpur', en: 'Dholpur', hi: 'धौलपुर', zone: 'III-B' },
  { id: 'dungarpur', en: 'Dungarpur', hi: 'डूंगरपुर', zone: 'IV-B' },
  { id: 'hanumangarh', en: 'Hanumangarh', hi: 'हनुमानगढ़', zone: 'I-B' },
  { id: 'jaipur', en: 'Jaipur (Urban)', hi: 'जयपुर (शहरी)', zone: 'III-A' },
  { id: 'jaipur_rural', en: 'Jaipur (Rural)', hi: 'जयपुर (ग्रामीण)', zone: 'III-A' },
  { id: 'jaisalmer', en: 'Jaisalmer', hi: 'जैसलमेर', zone: 'I-A' },
  { id: 'jalore', en: 'Jalore', hi: 'जालोर', zone: 'II-B' },
  { id: 'jhalawar', en: 'Jhalawar', hi: 'झालावाड़', zone: 'V' },
  { id: 'jhunjhunu', en: 'Jhunjhunu', hi: 'झुंझुनू', zone: 'II-A' },
  { id: 'jodhpur', en: 'Jodhpur (Urban)', hi: 'जोधपुर (शहरी)', zone: 'I-A' },
  { id: 'jodhpur_rural', en: 'Jodhpur (Rural)', hi: 'जोधपुर (ग्रामीण)', zone: 'I-A' },
  { id: 'karauli', en: 'Karauli', hi: 'करौली', zone: 'III-B' },
  { id: 'kekri', en: 'Kekri', hi: 'केकड़ी', zone: 'III-A' },
  { id: 'khairthal_tijara', en: 'Khairthal-Tijara', hi: 'खैरथल-तिजारा', zone: 'III-B' },
  { id: 'kota', en: 'Kota', hi: 'कोटा', zone: 'V' },
  { id: 'kotputli_behror', en: 'Kotputli-Behror', hi: 'कोटपूतली-बहरोड़', zone: 'III-A' },
  { id: 'nagaur', en: 'Nagaur', hi: 'नागौर', zone: 'II-A' },
  { id: 'pali', en: 'Pali', hi: 'पाली', zone: 'II-B' },
  { id: 'phalodi', en: 'Phalodi', hi: 'फलौदी', zone: 'I-A' },
  { id: 'pratapgarh', en: 'Pratapgarh', hi: 'प्रतापगढ़', zone: 'IV-B' },
  { id: 'rajsamand', en: 'Rajsamand', hi: 'राजसमंद', zone: 'IV-A' },
  { id: 'salumbar', en: 'Salumbar', hi: 'सलूंबर', zone: 'IV-B' },
  { id: 'sanchore', en: 'Sanchore', hi: 'सांचौर', zone: 'II-B' },
  { id: 'sawai_madhopur', en: 'Sawai Madhopur', hi: 'सवाई माधोपुर', zone: 'III-B' }
];

const CROPS_LIST = [
  { id: 'Mustard', en: 'Mustard / Raya', hi: 'सरसों / राया', season: 'Rabi' },
  { id: 'Bajra', en: 'Bajra (Pearl Millet)', hi: 'बाजरा', season: 'Kharif' },
  { id: 'Wheat', en: 'Wheat', hi: 'गेहूं', season: 'Rabi' },
  { id: 'Gram', en: 'Gram (Chickpea)', hi: 'चना', season: 'Rabi' },
  { id: 'Guar', en: 'Guar (Cluster Bean)', hi: 'ग्वार', season: 'Kharif' },
  { id: 'Moong', en: 'Moong (Green Gram)', hi: 'मूंग', season: 'Kharif' },
  { id: 'Soybean', en: 'Soybean', hi: 'सोयाबीन', season: 'Kharif' },
  { id: 'Cotton', en: 'Cotton', hi: 'कपास', season: 'Kharif' },
  { id: 'Cumin', en: 'Cumin (Jeera)', hi: 'जीरा', season: 'Rabi' },
  { id: 'Isabgol', en: 'Isabgol (Psyllium Husk)', hi: 'ईसबगोल', season: 'Rabi' },
  { id: 'Coriander', en: 'Coriander (Dhaniya)', hi: 'धनिया', season: 'Rabi' },
  { id: 'Barley', en: 'Barley (Jau)', hi: 'जौ', season: 'Rabi' }
];

const IRRIGATION_OPTIONS = [
  { id: 'tubewell', en: 'Tubewell (Borewell)', hi: 'नलकूप (बोरवेल)' },
  { id: 'canal', en: 'Canal (Nehar)', hi: 'नहरी सिंचाई' },
  { id: 'well', en: 'Open Well (Kuan)', hi: 'खुला कुआं' },
  { id: 'rainfed', en: 'Rainfed (Barani)', hi: 'वर्षा आधारित (बारानी)' }
];

// Conversion standard for Rajasthan:
// 1 Pucca Bigha = 2,529.28 sq.m ≈ 0.2529 Hectares
// 1 Hectare ≈ 3.95368 Pucca Bighas
const HECTARE_TO_BIGHA = 3.9537;
const BIGHA_TO_HECTARE = 0.2529;

export const OnboardingPage: React.FC = () => {
  const { i18n } = useTranslation();
  const navigate = useNavigate();
  const { farm, refreshProfile, setFarmLocally, user } = useAuth();

  const isHindi = i18n.language === 'hi';

  const [district, setDistrict] = useState(farm?.district || 'Jaipur (Rural)');
  const [tehsil, setTehsil] = useState(farm?.tehsil || '');
  const [crop, setCrop] = useState(farm?.crop || 'Mustard');
  const [landUnit, setLandUnit] = useState<'bigha' | 'hectare'>('bigha');
  const [landValue, setLandValue] = useState<number>(
    farm?.land_hectare ? (farm.land_hectare * HECTARE_TO_BIGHA) : 8
  );
  const [irrigation, setIrrigation] = useState<any>(farm?.irrigation || 'tubewell');
  const [sowingDate, setSowingDate] = useState(
    farm?.sowing_date || new Date().toISOString().split('T')[0]
  );

  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // The farm profile may load after this page mounts (direct navigation / refresh):
  // populate the form once with the saved details so they can be edited.
  const populatedFor = useRef<string | null>(null);
  useEffect(() => {
    if (!farm) return;
    const signature = `${farm.farm_id}|${farm.updated_at ?? ''}`;
    if (populatedFor.current === signature) return;
    populatedFor.current = signature;
    // Map backend district (e.g. "Jaipur") onto the form option value when only the base name matches
    const match =
      RAJASTHAN_41_DISTRICTS.find((d) => d.en === farm.district) ||
      RAJASTHAN_41_DISTRICTS.find((d) => d.en.toLowerCase().startsWith(farm.district.toLowerCase()));
    setDistrict(match ? match.en : farm.district);
    setTehsil(farm.tehsil === 'Headquarters' ? '' : farm.tehsil);
    setCrop(farm.crop);
    setLandUnit('bigha');
    setLandValue(parseFloat((farm.land_hectare * HECTARE_TO_BIGHA).toFixed(2)));
    setIrrigation(farm.irrigation);
    setSowingDate(farm.sowing_date);
  }, [farm]);

  // Live conversion calculations
  const landInHectares = landUnit === 'bigha' ? (landValue * BIGHA_TO_HECTARE) : landValue;
  const landInBighas = landUnit === 'bigha' ? landValue : (landValue * HECTARE_TO_BIGHA);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    const farmPayload = {
      district,
      tehsil: tehsil.trim() || 'Headquarters',
      crop,
      land_hectare: parseFloat(landInHectares.toFixed(2)),
      irrigation,
      sowing_date: sowingDate,
    };

    try {
      // Send to FastAPI /profile endpoint
      await apiClient.put('/profile', { farm: farmPayload });
      await refreshProfile();
      offlineStorage.saveProfile(farmPayload);

      setSuccessMsg(isHindi ? 'खेत प्रोफाइल सफलतापूर्वक सहेजी गई!' : 'Farm profile saved successfully!');
      setTimeout(() => navigate('/'), 800);
    } catch (err: unknown) {
      console.warn('API error saving profile, saving locally:', err);
      const reason = err instanceof Error ? err.message : '';
      // Keep the app usable: apply the change on this device, but tell the user honestly
      setFarmLocally({
        farm_id: farm?.farm_id || 'local-farm',
        user_id: farm?.user_id || user?.id || 'local',
        ...farmPayload,
      } as FarmProfile);
      setErrorMsg(
        isHindi
          ? `सर्वर पर सहेजने में विफल${reason ? ` (${reason})` : ''}। बदलाव केवल इस डिवाइस पर सहेजे गए हैं।`
          : `Could not save to the server${reason ? ` (${reason})` : ''}. Changes were applied on this device only.`
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto my-6 p-6 sm:p-8 bg-white rounded-2xl border border-slate-200 shadow-sm">
      <button
        onClick={() => navigate('/')}
        className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 mb-4 transition-colors font-medium"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>{isHindi ? 'मुख्य पृष्ठ पर वापस जाएं' : 'Back to Home'}</span>
      </button>

      <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-100">
        <div className="w-11 h-11 rounded-xl bg-brand-100 text-brand-700 flex items-center justify-center shadow-inner">
          <Sprout className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-slate-900">
            {isHindi ? 'खेत प्रोफाइल पंजीकरण एवं विवरण' : 'Farm Profile Setup'}
          </h1>
          <p className="text-xs text-slate-500">
            {isHindi
              ? 'राजस्थान के 41 जिलों और कृषि जलवायु क्षेत्रों के अनुसार निजीकृत सलाह'
              : 'Personalized according to Rajasthan’s 41 districts and agro-climatic zones'}
          </p>
        </div>
      </div>

      {errorMsg && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* District & Tehsil */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {isHindi ? 'जिला (District - 41 जिले)' : 'District (Rajasthan 41 Districts)'} <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <select
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                required
                className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white"
              >
                {RAJASTHAN_41_DISTRICTS.map((d) => (
                  <option key={d.id} value={d.en}>
                    {isHindi ? `${d.hi} (${d.en}) — Zone ${d.zone}` : `${d.en} (${d.hi}) — Zone ${d.zone}`}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {isHindi ? 'तहसील / उप-खंड (Tehsil)' : 'Tehsil / Sub-district'} <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={tehsil}
              onChange={(e) => setTehsil(e.target.value)}
              required
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
              placeholder={isHindi ? 'उदा. आमेर, बस्सी, सांगानेर' : 'e.g. Amber, Bassi, Sanganer'}
            />
          </div>
        </div>

        {/* Primary Crop */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            {isHindi ? 'मुख्य फसल (Primary Crop)' : 'Primary Cultivated Crop'} <span className="text-red-500">*</span>
          </label>
          <select
            value={crop}
            onChange={(e) => setCrop(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white"
          >
            {CROPS_LIST.map((c) => (
              <option key={c.id} value={c.id}>
                {isHindi ? `${c.hi} (${c.en}) — ${c.season}` : `${c.en} (${c.hi}) — ${c.season}`}
              </option>
            ))}
          </select>
        </div>

        {/* Land Size Input with Bigha / Hectare Conversion */}
        <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-slate-800">
              {isHindi ? 'जमीन का रकबा (Land Area)' : 'Farm Land Area'} <span className="text-red-500">*</span>
            </label>
            <div className="inline-flex rounded-lg border border-slate-300 p-0.5 bg-white text-xs">
              <button
                type="button"
                onClick={() => setLandUnit('bigha')}
                className={`px-3 py-1 rounded-md font-semibold transition-colors ${
                  landUnit === 'bigha' ? 'bg-brand-700 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {isHindi ? 'बीघा (Bigha)' : 'Bigha'}
              </button>
              <button
                type="button"
                onClick={() => setLandUnit('hectare')}
                className={`px-3 py-1 rounded-md font-semibold transition-colors ${
                  landUnit === 'hectare' ? 'bg-brand-700 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {isHindi ? 'हेक्टेयर (Hectare)' : 'Hectare'}
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="number"
              step="0.1"
              min="0.1"
              value={landValue}
              onChange={(e) => setLandValue(Math.max(parseFloat(e.target.value) || 0, 0))}
              required
              className="w-full px-3 py-2 text-sm font-semibold border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white"
            />
            <span className="text-sm font-medium text-slate-600 whitespace-nowrap">
              {landUnit === 'bigha' ? (isHindi ? 'पक्का बीघा' : 'Pucca Bigha') : (isHindi ? 'हेक्टेयर' : 'Hectares')}
            </span>
          </div>

          {/* Conversion explanation pill */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs text-brand-900 bg-brand-50 p-2.5 rounded-lg border border-brand-200">
            <div>
              <span className="font-semibold">{isHindi ? 'रूपांतरित माप:' : 'Converted equivalent:'} </span>
              <strong>{landInHectares.toFixed(2)} {isHindi ? 'हेक्टेयर' : 'Hectares'}</strong> ({landInBighas.toFixed(1)} {isHindi ? 'बीघा' : 'Bigha'})
            </div>
            <div className="text-[11px] text-brand-700 mt-1 sm:mt-0">
              1 Hectare ≈ 3.95 Pucca Bigha (राजस्थान मानक)
            </div>
          </div>
        </div>

        {/* Irrigation & Sowing Date */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {isHindi ? 'सिंचाई साधन (Irrigation Type)' : 'Irrigation Source'} <span className="text-red-500">*</span>
            </label>
            <select
              value={irrigation}
              onChange={(e) => setIrrigation(e.target.value as any)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white"
            >
              {IRRIGATION_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {isHindi ? opt.hi : opt.en}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {isHindi ? 'बुवाई की तारीख (Sowing Date)' : 'Sowing Date'} <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              value={sowingDate}
              onChange={(e) => setSowingDate(e.target.value)}
              required
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white"
            />
          </div>
        </div>

        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600 flex items-start gap-2">
          <Info className="w-4 h-4 text-brand-700 flex-shrink-0 mt-0.5" />
          <span>
            {isHindi
              ? 'यह विवरण आपके खेत की FAO-56 जल मांग, सिंचाई समय-सारणी, मौसम चेतावनी और मंडी भावों को व्यक्तिगत बनाने में उपयोग होगा।'
              : 'This profile calibrates your FAO-56 crop water demand, irrigation scheduling, weather alerts, and localized mandi insights.'}
          </span>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="w-full py-2.5 px-4 bg-brand-700 hover:bg-brand-800 text-white font-semibold rounded-lg text-sm transition-colors flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          <span>
            {saving
              ? (isHindi ? 'सहेजा जा रहा है...' : 'Saving...')
              : (isHindi ? 'प्रोफाइल सहेजें और मुख्य पृष्ठ पर जाएं' : 'Save Profile & Proceed')}
          </span>
        </button>
      </form>
    </div>
  );
};
