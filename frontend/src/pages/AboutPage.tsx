import React from 'react';
import { ShieldCheck, BookOpen, Database, AlertCircle, Cpu, ExternalLink } from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="max-w-3xl mx-auto my-6 space-y-6">
      {/* Title */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-brand-100 text-brand-800 flex items-center justify-center">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">किसान साथी राजस्थान (KisanSathi Rajasthan)</h1>
            <p className="text-xs text-slate-500">अंतिम वर्ष विश्वविद्यालय परियोजना • वैज्ञानिक सत्यनिष्ठा एवं पारदर्शिता</p>
          </div>
        </div>
        <p className="text-xs text-slate-600 mt-2 leading-relaxed">
          यह वेब एप्लिकेशन राजस्थान के छोटे एवं सीमांत किसानों को उनकी भाषा (हिन्दी/English) में सटीक, वैज्ञानिक और जोखिम-रहित कृषि निर्णय सहायता उपलब्ध कराने हेतु विकसित किया गया है।
        </p>
      </div>

      {/* Real Data Sources */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-3">
        <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Database className="w-4 h-4 text-brand-700" />
          <span>प्रामाणिक डेटा स्रोत (Authentic Data Sources)</span>
        </h2>
        <div className="space-y-2 text-xs text-slate-700">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <span className="font-semibold text-slate-900">जिलावार फसल उत्पादन एवं उपज इतिहास:</span> आर्थिक एवं सांख्यिकी निदेशालय (DES), कृषि विभाग, राजस्थान सरकार।
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <span className="font-semibold text-slate-900">दैनिक कृषि उपज मंडी भाव एवं आवक:</span> Agmarknet (कृषि विपणन सूचना नेटवर्क) एवं Open Government Data Platform India (data.gov.in)।
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <span className="font-semibold text-slate-900">कृषि परामर्श एवं कीट/रोग प्रबंधन:</span> ICAR - केंद्रीय शुष्क क्षेत्र अनुसंधान संस्थान (CAZRI) जोधपुर, स्वामी केशवानंद राजस्थान कृषि विश्वविद्यालय बीकानेर, एवं कृषि विश्वविद्यालय कोटा।
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <span className="font-semibold text-slate-900">मौसम एवं वाष्पोत्सर्जन भौतिकी:</span> FAO Irrigation and Drainage Paper 56 (पेनमैन-मोंटीथ विधि) एवं Open-Meteo मौसम पूर्वानुमान।
          </div>
        </div>
      </div>

      {/* Model Transparency & Baselines */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-3">
        <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-purple-700" />
          <span>मशीन लर्निंग मॉडल व बेसलाइन नीतियां (Model Transparency)</span>
        </h2>
        <div className="text-xs text-slate-600 space-y-2 leading-relaxed">
          <p>
            परियोजना के वैज्ञानिक मानकों के अनुसार, किसी भी मॉडल की सटीकता को बढ़ा-चढ़ाकर या मनगढ़ंत आंकड़ों के साथ प्रस्तुत नहीं किया जाता:
          </p>
          <ul className="list-disc list-inside space-y-1.5 pl-2 text-slate-700">
            <li>
              <strong>उपज पूर्वानुमान:</strong> वास्तविक ऐतिहासिक डेटा पर प्रशिक्षित मॉडल की अनुपस्थिति में यह प्रणाली स्पष्ट रूप से 5-वर्षीय जिला औसत (<code className="bg-slate-100 px-1 py-0.5 rounded text-slate-800">model_version = "baseline"</code>) प्रदान करती है।
            </li>
            <li>
              <strong>मंडी भाव:</strong> समय-श्रृंखला मॉडल के स्थान पर 'स्थिरता बेसलाइन' (Persistence: Same as last week) प्रदर्शित होती है।
            </li>
            <li>
              <strong>रोग पहचान:</strong> जब पहचान का विश्वास स्तर 70% से कम होता है, तो मॉडल मनगढ़ंत कीटनाशक बताने के बजाय सुरक्षित रूप से नजदीकी KVK विशेषज्ञ से संपर्क करने का निर्देश देता है।
            </li>
          </ul>
        </div>
      </div>

      {/* Limitations & Scope */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-3">
        <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-600" />
          <span>सिस्टम सीमाएं (Scope & System Boundaries)</span>
        </h2>
        <div className="text-xs text-slate-600 space-y-1.5 leading-relaxed">
          <p>• <strong>उपग्रह इमेजरी, SMS/IVR एवं भुगतान:</strong> इस संस्करण के दायरे से बाहर (Out of Scope) रखे गए हैं।</p>
          <p>• <strong>सर्वर संसाधन:</strong> रेंडर फ्री-टियर (512 MB RAM) सीमाओं का पालन करते हुए सर्वर पर कोई भारी डीप लर्निंग मॉडल लोड नहीं होता; दृष्टि मॉडल सीधे ब्राउज़र (ONNX Web) में निष्पादित होते हैं।</p>
          <p>• <strong>कानूनी अस्वीकरण:</strong> पोर्टल की सलाह केवल निर्णय-सहायता मार्गदर्शन है, किसी प्रमाणित कृषि वैज्ञानिक का पूर्ण विकल्प नहीं।</p>
        </div>
      </div>
    </div>
  );
};
