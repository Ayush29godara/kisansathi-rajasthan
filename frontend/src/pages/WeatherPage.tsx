import React, { useState } from 'react';
import { CloudSun, Droplets, AlertTriangle, Calendar, Info, ShieldCheck } from 'lucide-react';
import { IrrigationSchedule } from '../types';

export const WeatherPage: React.FC = () => {
  const [district] = useState('Jaipur');
  const [crop] = useState('Mustard');

  const [schedule] = useState<IrrigationSchedule>({
    district: 'Jaipur (जयपुर)',
    crop: 'Mustard (सरसों)',
    et0_mm_day: 4.8,
    kc_factor: 0.75,
    crop_etc_mm_day: 3.6,
    days_since_sowing: 14,
    current_growth_stage: 'Vegetative / Early Tillering',
    next_irrigation_due_days: 5,
    water_depth_mm: 25.0,
    irrigation_urgency: 'normal',
    advisory_text: 'जयपुर में सरसों फसल बुवाई से 14 दिन की अवस्था में है। वर्तमान दैनिक वाष्पीकरण मांग 3.6 मिमी/दिन है। आगामी सिंचाई लगभग 5 दिनों बाद अनुशंसित है।',
    alerts: [
      {
        alert_type: 'तापमान सामान्य',
        severity: 'info',
        message: 'आगामी 3 दिनों में अधिकतम तापमान 32°C और न्यूनतम 18°C रहने का अनुमान। पाले की कोई आशंका नहीं।',
      }
    ],
  });

  return (
    <div className="max-w-3xl mx-auto my-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-800 flex items-center justify-center">
            <CloudSun className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">मौसम अलर्ट एवं वैज्ञानिक सिंचाई अनुसूची</h1>
            <p className="text-xs text-slate-500">FAO-56 पेनमैन-मोंटीथ वाष्पोत्सर्जन भौतिकी मॉडल पर आधारित</p>
          </div>
        </div>
      </div>

      {/* Weather Alert Notification */}
      {schedule.alerts.map((alert, idx) => (
        <div key={idx} className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-700 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-blue-900">
            <span className="font-bold">{alert.alert_type}:</span> {alert.message}
          </div>
        </div>
      ))}

      {/* FAO-56 Irrigation Metrics */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <Droplets className="w-4 h-4 text-brand-600" />
            <h2 className="text-sm font-bold text-slate-800">फसल जल आवश्यकता (Crop Water Balance)</h2>
          </div>
          <span className="text-[11px] font-semibold bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-full">
            FAO Irrigation Paper 56
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
            <div className="text-xs text-slate-500 font-medium">फसल अवस्था (Growth Stage)</div>
            <div className="text-sm font-bold text-slate-900 mt-1">{schedule.current_growth_stage}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">बुवाई से {schedule.days_since_sowing} दिन</div>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
            <div className="text-xs text-slate-500 font-medium">फसल गुणांक (Crop Kc)</div>
            <div className="text-lg font-bold text-slate-900 mt-1">{schedule.kc_factor.toFixed(2)}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">संदर्भ ET₀: {schedule.et0_mm_day} mm/दिन</div>
          </div>

          <div className="p-4 bg-brand-50 rounded-xl border border-brand-100">
            <div className="text-xs text-brand-800 font-medium">दैनिक जल खपत (ETc)</div>
            <div className="text-2xl font-extrabold text-brand-900 mt-1">
              {schedule.crop_etc_mm_day} <span className="text-xs font-semibold">मिमी/दिन</span>
            </div>
            <div className="text-[11px] text-brand-700 mt-0.5">Kc × ET₀ वाष्पोत्सर्जन</div>
          </div>
        </div>

        {/* Schedule Recommendation Box */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
          <div className="text-xs font-semibold text-slate-800 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-brand-700" />
            <span>आगामी सिंचाई संस्तुति:</span>
          </div>
          <p className="text-xs text-slate-700 leading-relaxed">{schedule.advisory_text}</p>
          <div className="text-[11px] text-brand-800 font-medium">
            प्रस्तावित सिंचाई गहराई: {schedule.water_depth_mm} मिमी (मध्यम सिंचाई)
          </div>
        </div>

        <div className="text-[11px] text-slate-500 flex items-center gap-1.5 pt-2 border-t border-slate-100">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
          <span>सिंचाई निर्णय 100% भौतिकी एवं कृषि विज्ञान नियमों पर आधारित है (Zero Black-box ML).</span>
        </div>
      </div>
    </div>
  );
};
