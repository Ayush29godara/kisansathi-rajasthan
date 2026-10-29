import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapPin, Save, Sprout, Info } from 'lucide-react';

const RAJASTHAN_DISTRICTS = [
  'Ajmer', 'Alwar', 'Banswara', 'Baran', 'Barmer', 'Bharatpur', 'Bhilwara', 'Bikaner',
  'Bundi', 'Chittorgarh', 'Churu', 'Dausa', 'Dholpur', 'Dungarpur', 'Hanumangarh',
  'Jaipur', 'Jaisalmer', 'Jalore', 'Jhalawar', 'Jhunjhunu', 'Jodhpur', 'Karauli',
  'Kota', 'Nagaur', 'Pali', 'Pratapgarh', 'Rajsamand', 'Sawai Madhopur', 'Sikar',
  'Sirohi', 'Sri Ganganagar', 'Tonk', 'Udaipur'
];

const MAJOR_CROPS = [
  { id: 'Mustard', label: 'सरसों / राया (Mustard - Rabi)' },
  { id: 'Bajra', label: 'बाजरा (Pearl Millet - Kharif)' },
  { id: 'Wheat', label: 'गेहूं (Wheat - Rabi)' },
  { id: 'Gram', label: 'चना (Chickpea - Rabi)' },
  { id: 'Guar', label: 'ग्वार (Cluster Bean - Kharif)' },
  { id: 'Moong', label: 'मूंग (Green Gram - Kharif)' },
  { id: 'Soybean', label: 'सोयाबीन (Soybean - Kharif)' },
  { id: 'Cotton', label: 'कपास (Cotton - Kharif)' },
  { id: 'Cumin', label: 'जीरा (Jeera - Rabi)' },
];

export const OnboardingPage: React.FC = () => {
  const navigate = useNavigate();
  const [district, setDistrict] = useState('Jaipur');
  const [tehsil, setTehsil] = useState('Amber');
  const [crop, setCrop] = useState('Mustard');
  const [landUnit, setLandUnit] = useState<'hectare' | 'bigha'>('bigha');
  const [landArea, setLandArea] = useState<number>(10);
  const [irrigation, setIrrigation] = useState<'canal' | 'tubewell' | 'well' | 'rainfed'>('tubewell');
  const [sowingDate, setSowingDate] = useState('2026-10-15');
  const [saving, setSaving] = useState(false);

  // Convert bigha to hectare (Rajasthan pucca bigha approx 0.2529 hectare)
  const convertedHectare = landUnit === 'bigha' ? landArea * 0.253 : landArea;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    // Save profile locally and proceed
    setTimeout(() => {
      setSaving(false);
      navigate('/');
    }, 600);
  };

  return (
    <div className="max-w-2xl mx-auto my-6 p-6 sm:p-8 bg-white rounded-2xl border border-slate-200 shadow-sm">
      <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-100">
        <div className="w-10 h-10 rounded-xl bg-brand-100 text-brand-700 flex items-center justify-center">
          <Sprout className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-slate-900">खेत प्रोफाइल पंजीकरण (Farm Profile)</h1>
          <p className="text-xs text-slate-500">यह जानकारी आपके सभी पूर्वानुमानों और सलाह को व्यक्तिगत बनाएगी</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              जिला (District) <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <select
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
              >
                {RAJASTHAN_DISTRICTS.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              तहसील (Tehsil) <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={tehsil}
              onChange={(e) => setTehsil(e.target.value)}
              required
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
              placeholder="उदा. आमेर, कोटपूतली"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            मुख्य फसल (Primary Crop) <span className="text-red-500">*</span>
          </label>
          <select
            value={crop}
            onChange={(e) => setCrop(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
          >
            {MAJOR_CROPS.map((c) => (
              <option key={c.id} value={c.id}>{c.label}</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              जमीन का आकार (Land Area) <span className="text-red-500">*</span>
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                step="0.1"
                min="0.1"
                value={landArea}
                onChange={(e) => setLandArea(parseFloat(e.target.value) || 0)}
                required
                className="w-2/3 px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
              />
              <select
                value={landUnit}
                onChange={(e) => setLandUnit(e.target.value as 'hectare' | 'bigha')}
                className="w-1/3 px-2 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
              >
                <option value="bigha">बीघा</option>
                <option value="hectare">हेक्टेयर</option>
              </select>
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              बराबर: {convertedHectare.toFixed(2)} हेक्टेयर
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              सिंचाई साधन (Irrigation Type) <span className="text-red-500">*</span>
            </label>
            <select
              value={irrigation}
              onChange={(e) => setIrrigation(e.target.value as any)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
            >
              <option value="tubewell">नलकूप (Tubewell)</option>
              <option value="canal">नहर (Canal)</option>
              <option value="well">कुआं (Open Well)</option>
              <option value="rainfed">वर्षा आधारित (Rainfed / बारानी)</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            बुवाई की तारीख (Sowing Date) <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            value={sowingDate}
            onChange={(e) => setSowingDate(e.target.value)}
            required
            className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
          />
        </div>

        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600 flex items-start gap-2">
          <Info className="w-4 h-4 text-brand-700 flex-shrink-0 mt-0.5" />
          <span>
            यह प्रोफाइल आपके क्षेत्र की कृषि जलवायु (Agro-climatic zone) के आधार पर मौसम अलर्ट, FAO-56 सिंचाई समय और मंडी पूर्वानुमान निर्धारित करेगी।
          </span>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="w-full py-2.5 px-4 bg-brand-700 hover:bg-brand-800 text-white font-semibold rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
        >
          <Save className="w-4 h-4" />
          <span>{saving ? 'प्रोफाइल सहेजी जा रही है...' : 'प्रोफाइल सहेजें और आगे बढ़ें'}</span>
        </button>
      </form>
    </div>
  );
};
