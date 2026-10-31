import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ShieldCheck,
  Database,
  AlertCircle,
  Cpu,
  BarChart3,
  CheckCircle2,
} from 'lucide-react';
import { getSystemMetadata } from '../services/api';
import type { SystemMetadata } from '../types';

export const AboutPage: React.FC = () => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  const [metadata, setMetadata] = useState<SystemMetadata | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    getSystemMetadata()
      .then((data) => {
        if (isMounted) {
          setMetadata(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.warn('Could not fetch dynamic system metadata:', err);
          setError(
            isHi
              ? 'सिस्टम मेटाडेटा लोड करने में असमर्थ'
              : 'Failed to load system metadata'
          );
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [isHi]);

  return (
    <div className="max-w-4xl mx-auto my-6 px-4 space-y-6">
      {/* Title & Mission Card */}
      <section
        aria-labelledby="about-title"
        className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 rounded-2xl bg-green-100 text-green-800 flex items-center justify-center shadow-sm">
            <ShieldCheck className="w-7 h-7" aria-hidden="true" />
          </div>
          <div>
            <h1 id="about-title" className="text-xl sm:text-2xl font-bold text-slate-900">
              {isHi ? 'किसान साथी राजस्थान (KisanSathi Rajasthan)' : 'KisanSathi Rajasthan'}
            </h1>
            <p className="text-xs font-semibold text-green-700">
              {isHi
                ? 'विश्वविद्यालय अंतिम वर्ष कैप्सटन प्रोजेक्ट • वैज्ञानिक सत्यनिष्ठा एवं पूर्ण पारदर्शिता'
                : 'University Final-Year Capstone Project • Scientific Rigor & Transparency'}
            </p>
          </div>
        </div>
        <p className="text-xs sm:text-sm text-slate-600 mt-3 leading-relaxed">
          {isHi
            ? 'यह प्लेटफॉर्म राजस्थान के 33 जिलों के छोटे और सीमांत किसानों को द्विभाषी (हिन्दी एवं English) में विश्वसनीय, कृषि-विश्वविद्यालय प्रमाणित और डेटा-संचालित निर्णय-सहायता प्रदान करता है। हम किसी भी काल्पनिक या मनगढ़ंत मॉडल दावों के बिना प्रामाणिक आंकड़े प्रदर्शित करते हैं।'
            : 'A full-stack, AI-assisted decision-support platform engineered for Rajasthan smallholder farmers across 33 districts. We strictly uphold scientific integrity: deterministic baselines are explicitly reported, and all advice is grounded in verified state agricultural university publications.'}
        </p>
      </section>

      {/* Model Metadata & Real Evaluation Metrics */}
      <section
        aria-labelledby="metrics-title"
        className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4"
      >
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h2 id="metrics-title" className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-purple-700" aria-hidden="true" />
            <span>
              {isHi
                ? 'सत्यापित मॉडल मेट्रिक्स एवं आर्किटेक्चर (Live Model Metadata)'
                : 'Verified Model Metrics & Architectures'}
            </span>
          </h2>
          {metadata && (
            <span className="text-[11px] font-mono bg-purple-50 text-purple-800 px-2.5 py-1 rounded-full border border-purple-200">
              v{metadata.version} ({metadata.environment})
            </span>
          )}
        </div>

        {loading ? (
          <div className="py-8 text-center text-xs text-slate-500 animate-pulse">
            {isHi ? 'मॉडल मेटाडेटा फ़ाइलें पढ़ी जा रही हैं...' : 'Loading model metadata from disk...'}
          </div>
        ) : error ? (
          <div className="text-xs text-amber-700 bg-amber-50 p-3 rounded-lg border border-amber-200">
            {error}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {metadata?.modules.map((m, idx) => (
              <div
                key={idx}
                className="bg-slate-50 rounded-xl p-4 border border-slate-200 flex flex-col justify-between hover:shadow-sm transition"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="text-xs font-bold text-slate-900 leading-snug">
                      {m.module}
                    </h3>
                    <span className="text-[10px] font-mono bg-slate-200 text-slate-800 px-1.5 py-0.5 rounded flex-shrink-0">
                      {m.version}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-600 mb-2">
                    <strong className="text-slate-800">
                      {isHi ? 'मॉडल प्रकार: ' : 'Model: '}
                    </strong>
                    {m.model_type}
                  </p>

                  <div className="bg-white p-2.5 rounded-lg border border-slate-200 mb-2.5">
                    <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                      <BarChart3 className="w-3 h-3 text-primary-600" aria-hidden="true" />
                      <span>{m.accuracy_metric}</span>
                    </div>
                    <div className="text-xs font-mono font-bold text-slate-900">
                      {m.metric_value}
                    </div>
                  </div>

                  <div className="text-[11px] text-slate-600 mb-2">
                    <strong className="text-slate-800">
                      {isHi ? 'डेटा स्रोत: ' : 'Data Source: '}
                    </strong>
                    {m.data_source}
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-200">
                  <div className="text-[10px] font-bold text-amber-800 flex items-center gap-1 mb-1">
                    <AlertCircle className="w-3 h-3" aria-hidden="true" />
                    <span>{isHi ? 'प्रलेखित सीमाएं:' : 'Documented Limitations:'}</span>
                  </div>
                  <ul className="list-disc list-inside space-y-0.5 text-[10px] text-slate-600">
                    {m.limitations.map((lim, lIdx) => (
                      <li key={lIdx} className="leading-tight">
                        {lim}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Official Data Sources */}
      <section
        aria-labelledby="sources-title"
        className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-3"
      >
        <h2 id="sources-title" className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Database className="w-5 h-5 text-green-700" aria-hidden="true" />
          <span>{isHi ? 'प्रामाणिक डेटा प्रदाता एवं संदर्भ' : 'Authentic Data Providers & Grounding'}</span>
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-slate-700">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <span className="font-semibold text-slate-900">
                DES, राजस्थान सरकार (Government of Rajasthan):
              </span>
              <p className="text-[11px] text-slate-600 mt-0.5">
                जिलावार 6 प्रमुख फसलों के वास्तविक ऐतिहासिक उपज और क्षेत्रफल आंकड़े (2018–2024)।
              </p>
            </div>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <span className="font-semibold text-slate-900">Agmarknet & Data.gov.in:</span>
              <p className="text-[11px] text-slate-600 mt-0.5">
                दैनिक राष्ट्रीय कृषि उपज मंडी भाव, न्यूनतम-अधिकतम व मोडल दरें और आवक रिकॉर्ड।
              </p>
            </div>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <span className="font-semibold text-slate-900">ICAR, AU Kota, SKNAU, SKRAU:</span>
              <p className="text-[11px] text-slate-600 mt-0.5">
                सत्यापित कृषि पैकेज ऑफ प्रैक्टिसेज (POP), रोग लक्षण व विश्वविद्यालय कृषि सलाह।
              </p>
            </div>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <span className="font-semibold text-slate-900">FAO-56 & Open-Meteo API:</span>
              <p className="text-[11px] text-slate-600 mt-0.5">
                पेनमैन-मोंटीथ वाष्पोत्सर्जन भौतिकी एवं उच्च-सटीक 72-घंटे वर्षा व तापमान पूर्वानुमान।
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Explicit Capstone Boundaries & Out-of-Scope Notice */}
      <section
        aria-labelledby="boundaries-title"
        className="bg-amber-50 rounded-2xl p-6 border border-amber-200 text-xs text-amber-900 space-y-2"
      >
        <div className="flex items-center gap-2 font-bold text-sm text-amber-900">
          <AlertCircle className="w-4 h-4 text-amber-700" aria-hidden="true" />
          <h2 id="boundaries-title">{isHi ? 'परियोजना सीमाएं एवं पारदर्शी घोषणा' : 'Capstone Limitations & Disclosure'}</h2>
        </div>
        <p className="leading-relaxed">
          {isHi
            ? '1. सर्वर संसाधन: Render के 512MB RAM फ्री-टियर पर सिस्टम को सुरक्षित रखने के लिए भारी पायटॉर्च मॉडल सर्वर पर नहीं चलाए जाते; ऑन-डिवाइस ONNX Web का उपयोग होता है।'
            : '1. Server Resources: To strictly adhere to Render free-tier 512MB RAM constraints, heavy neural network models do not run server-side; client-side ONNX Web runtime is leveraged.'}
        </p>
        <p className="leading-relaxed">
          {isHi
            ? '2. कानूनी अस्वीकरण: यह सेवा केवल निर्णय-सहायता मार्गदर्शन है। किसी भी रासायनिक छिड़काव से पहले अपने नजदीकी कृषि पर्यवेक्षक या KVK वैज्ञानिक से संपर्क करें।'
            : '2. Legal Advisory: The outputs provided are decision-support guidance only and should not replace certified on-site agricultural officer inspections.'}
        </p>
      </section>
    </div>
  );
};
