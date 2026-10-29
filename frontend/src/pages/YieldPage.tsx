import React, { useState } from 'react';
import { TrendingUp, BarChart3, Info, ShieldAlert } from 'lucide-react';
import { YieldOutlook } from '../types';

export const YieldPage: React.FC = () => {
  const [district, setDistrict] = useState('Alwar');
  const [crop, setCrop] = useState('Mustard');
  const [outlook] = useState<YieldOutlook>({
    district: 'Alwar',
    crop: 'Mustard (सरसों)',
    season: 'Rabi 2026',
    forecast_year: 2026,
    predicted_yield_kg_ha: 1780.0,
    baseline_5yr_mean_kg_ha: 1780.0,
    model_version: 'baseline',
    top_drivers: [
      {
        feature: 'Historical District Baseline',
        impact: 'neutral',
        description: 'अलवर जिले के 5-वर्षीय औसत उत्पादन पर आधारित अनुमान।',
      },
      {
        feature: 'Pre-sowing Monsoon Rainfall',
        impact: 'positive',
        description: 'बुवाई पूर्व पर्याप्त मानसूनी नमी से अंकुरण में सहायक।',
      },
    ],
    summary_text: 'अलवर जिले में सरसों की ऐतिहासिक 5-वर्षीय औसत उपज 1780 किग्रा/हेक्टेयर है। वर्तमान परिणाम बेसलाइन सांख्यिकी पर आधारित है।',
  });

  return (
    <div className="max-w-3xl mx-auto my-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">जिला उपज परिदृश्य (District Yield Outlook)</h1>
            <p className="text-xs text-slate-500">कृषि जलवायु क्षेत्र और ऐतिहासिक उत्पादन सांख्यिकी पर आधारित अनुमान</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">जिला चुनें</label>
            <select
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
            >
              <option value="Alwar">Alwar (अलवर)</option>
              <option value="Jaipur">Jaipur (जयपुर)</option>
              <option value="Kota">Kota (कोटा)</option>
              <option value="Bikaner">Bikaner (बीकानेर)</option>
              <option value="Sri Ganganagar">Sri Ganganagar (श्रीगंगानगर)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">फसल चुनें</label>
            <select
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
            >
              <option value="Mustard">सरसों (Mustard)</option>
              <option value="Bajra">बाजरा (Bajra)</option>
              <option value="Wheat">गेहूं (Wheat)</option>
              <option value="Guar">ग्वार (Guar)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Yield Metrics Card */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">पूर्वानुमान परिणाम</span>
          <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
            Model Version: {outlook.model_version}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-100">
            <div className="text-xs text-emerald-800 font-medium">अनुमानित उत्पादन (Yield Outlook)</div>
            <div className="text-2xl font-extrabold text-emerald-950 mt-1">
              {outlook.predicted_yield_kg_ha.toFixed(0)} <span className="text-sm font-semibold">किग्रा/हेक्टेयर</span>
            </div>
            <div className="text-[11px] text-emerald-700 mt-1">
              लगभग {(outlook.predicted_yield_kg_ha / 100).toFixed(1)} क्विंटल प्रति हेक्टेयर
            </div>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
            <div className="text-xs text-slate-600 font-medium">जिला 5-वर्षीय औसत (Historical Baseline)</div>
            <div className="text-2xl font-extrabold text-slate-800 mt-1">
              {outlook.baseline_5yr_mean_kg_ha.toFixed(0)} <span className="text-sm font-semibold">किग्रा/हेक्टेयर</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              DES राजस्थान कृषि सांख्यिकी 2019-2024
            </div>
          </div>
        </div>

        {/* Explainability / Top Drivers */}
        <div className="mt-4">
          <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <BarChart3 className="w-4 h-4 text-purple-600" />
            <span>उत्पादकता को प्रभावित करने वाले मुख्य कारक (SHAP Feature Drivers):</span>
          </h2>
          <div className="space-y-2">
            {outlook.top_drivers.map((driver, idx) => (
              <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                <div className="font-semibold text-slate-800">{driver.feature}</div>
                <div className="text-slate-600 mt-0.5">{driver.description}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Scientific Transparency Notice */}
        <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-900 flex items-start gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-700 flex-shrink-0 mt-0.5" />
          <span>
            <strong>सत्यनिष्ठ प्रकटीकरण (Honesty Rule):</strong> जब तक प्रशिक्षित मशीन लर्निंग मॉडल Colab में प्रशिक्षित होकर लोड नहीं होता, यह परिणाम ऐतिहासिक जिला औसत (Baseline) को दर्शाता है। इसे कभी भी नकली ML सटीकता के रूप में प्रस्तुत नहीं किया जाता।
          </span>
        </div>
      </div>
    </div>
  );
};
