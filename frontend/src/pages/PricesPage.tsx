import React, { useState } from 'react';
import { IndianRupee, TrendingUp, Calendar, AlertCircle } from 'lucide-react';
import { MandiPriceForecast } from '../types';

export const PricesPage: React.FC = () => {
  const [mandi, setMandi] = useState('Alwar');
  const [commodity, setCommodity] = useState('Mustard');

  const [forecast] = useState<MandiPriceForecast>({
    mandi: 'Alwar (अलवर)',
    commodity: 'Mustard (सरसों)',
    latest_date: '2026-10-28',
    latest_modal_price: 5450.0,
    trend: 'stable',
    forecast_2_weeks: {
      min_expected: 5200.0,
      max_expected: 5700.0,
      expected_modal: 5450.0,
    },
    forecast_4_weeks: {
      min_expected: 5050.0,
      max_expected: 5850.0,
      expected_modal: 5450.0,
    },
    model_version: 'baseline',
    history: [
      { price_date: '2026-10-27', modal_price: 5420, min_price: 5150, max_price: 5600, arrivals: 140 },
      { price_date: '2026-10-26', modal_price: 5460, min_price: 5200, max_price: 5650, arrivals: 120 },
      { price_date: '2026-10-25', modal_price: 5440, min_price: 5180, max_price: 5620, arrivals: 155 },
    ],
    explanation: 'अलवर मंडी में सरसों का वर्तमान भाव ₹5,450/क्विंटल है। 2 से 4 सप्ताह का पूर्वानुमान "Same as last week" बेसलाइन मॉडल पर आधारित है।',
  });

  return (
    <div className="max-w-3xl mx-auto my-6 space-y-6">
      {/* Selection Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center">
            <IndianRupee className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">मंडी भाव एवं पूर्वानुमान (Mandi Price Outlook)</h1>
            <p className="text-xs text-slate-500">राजस्थान APMC मंडियों के दैनिक भाव और 2-4 सप्ताह का संभावित रुझान</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">मंडी चुनें</label>
            <select
              value={mandi}
              onChange={(e) => setMandi(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
            >
              <option value="Alwar">Alwar (अलवर)</option>
              <option value="Kota">Kota (भामाशाह मंडी कोटा)</option>
              <option value="Jaipur">Jaipur (सूरजपोल / मुहाना)</option>
              <option value="Bikaner">Bikaner (बीकानेर अनाज मंडी)</option>
              <option value="Sri Ganganagar">Sri Ganganagar (श्रीगंगानगर)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">जिंस (Commodity)</label>
            <select
              value={commodity}
              onChange={(e) => setCommodity(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
            >
              <option value="Mustard">सरसों (Mustard)</option>
              <option value="Wheat">गेहूं (Wheat)</option>
              <option value="Bajra">बाजरा (Bajra)</option>
              <option value="Soybean">सोयाबीन (Soybean)</option>
              <option value="Guar">ग्वार (Guar)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Price Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
          <div className="text-xs text-slate-500 font-medium">वर्तमान मॉडल भाव (Current Modal)</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            ₹{forecast.latest_modal_price.toFixed(0)} <span className="text-xs font-normal text-slate-500">/क्विंटल</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            <span>दिनांक: {forecast.latest_date}</span>
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
          <div className="text-xs text-slate-500 font-medium">2 सप्ताह का संभावित दायरा</div>
          <div className="text-lg font-bold text-brand-700 mt-1">
            ₹{forecast.forecast_2_weeks.min_expected.toFixed(0)} - ₹{forecast.forecast_2_weeks.max_expected.toFixed(0)}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            मध्य बिंदु: ₹{forecast.forecast_2_weeks.expected_modal.toFixed(0)}
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
          <div className="text-xs text-slate-500 font-medium">4 सप्ताह का संभावित दायरा</div>
          <div className="text-lg font-bold text-amber-700 mt-1">
            ₹{forecast.forecast_4_weeks.min_expected.toFixed(0)} - ₹{forecast.forecast_4_weeks.max_expected.toFixed(0)}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            मध्य बिंदु: ₹{forecast.forecast_4_weeks.expected_modal.toFixed(0)}
          </div>
        </div>
      </div>

      {/* Recent History Table */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold text-slate-800">हालिया दैनिक भाव इतिहास (Recent APMC Records)</h2>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600">
            Model: {forecast.model_version}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-3">दिनांक</th>
                <th className="py-2.5 px-3">न्यूनतम भाव (₹)</th>
                <th className="py-2.5 px-3">अधिकतम भाव (₹)</th>
                <th className="py-2.5 px-3">मॉडल भाव (₹)</th>
                <th className="py-2.5 px-3">आवक (क्विंटल)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {forecast.history.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50">
                  <td className="py-2.5 px-3 font-medium text-slate-800">{row.price_date}</td>
                  <td className="py-2.5 px-3 text-slate-600">₹{row.min_price}</td>
                  <td className="py-2.5 px-3 text-slate-600">₹{row.max_price}</td>
                  <td className="py-2.5 px-3 font-bold text-slate-900">₹{row.modal_price}</td>
                  <td className="py-2.5 px-3 text-slate-600">{row.arrivals}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-900 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-amber-700 flex-shrink-0 mt-0.5" />
          <span>{forecast.explanation}</span>
        </div>
      </div>
    </div>
  );
};
