import React, { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Camera,
  Upload,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  ShieldCheck,
  Loader2,
  Eye,
  EyeOff,
  Cpu,
  BookOpen,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../services/api';
import { offlineStorage } from '../services/offlineStorage';
import { FeedbackButtons } from '../components/common/FeedbackButtons';
import {
  resizeImageTo512Canvas,
  runInBrowserDiagnosis,
  CONFIDENCE_THRESHOLD,
} from '../services/onnx';
import { DiseaseDiagnosis } from '../types';

interface CropOption {
  id: string;
  name: string;
  hi: string;
}

const CROPS: CropOption[] = [
  { id: 'Auto-Detect', name: 'Auto-Detect (Any Crop)', hi: 'स्वतः पहचानें (Auto-Detect Crop)' },
  { id: 'Mustard', name: 'Mustard', hi: 'सरसों / राया (Mustard)' },
  { id: 'Tomato', name: 'Tomato', hi: 'टमाटर (Tomato)' },
  { id: 'Wheat', name: 'Wheat', hi: 'गेहूं (Wheat)' },
  { id: 'Bajra', name: 'Bajra', hi: 'बाजरा (Bajra)' },
  { id: 'Soybean', name: 'Soybean', hi: 'सोयाबीन (Soybean)' },
  { id: 'Guar', name: 'Guar', hi: 'ग्वार (Guar)' },
  { id: 'Gram', name: 'Gram', hi: 'चना (Gram)' },
];

export const DiagnosePage: React.FC = () => {
  const { i18n } = useTranslation();
  const isHindi = i18n.language?.startsWith('hi');
  useAuth();

  const [selectedCrop, setSelectedCrop] = useState<string>('Auto-Detect');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [optInStore, setOptInStore] = useState<boolean>(false);
  const [diagnosis, setDiagnosis] = useState<DiseaseDiagnosis | null>(null);
  const [topProbs, setTopProbs] = useState<{ label: string; hindiLabel?: string; prob: number }[]>([]);
  const [heatmapUrl, setHeatmapUrl] = useState<string | null>(null);
  const [showHeatmap, setShowHeatmap] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const imageElementRef = useRef<HTMLImageElement>(null);

  const handleImageFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError(isHindi ? 'कृपया केवल JPEG या PNG फोटो चुनें' : 'Please select a valid JPEG or PNG image');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError(isHindi ? 'फोटो का आकार 5 MB से कम होना चाहिए' : 'Image size must be less than 5 MB');
      return;
    }

    setError(null);
    setDiagnosis(null);
    setHeatmapUrl(null);
    setShowHeatmap(false);

    const reader = new FileReader();
    reader.onload = () => {
      setSelectedImage(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleImageFile(e.target.files[0]);
    }
  };

  // High-accuracy Unified Diagnosis
  const runDiagnosis = async () => {
    if (!selectedImage || !imageElementRef.current) return;
    setAnalyzing(true);
    setError(null);

    try {
      // 1. Client-side canvas resize to 512px max dimension & EXIF stripping for privacy
      const canvas512 = resizeImageTo512Canvas(imageElementRef.current);

      // 2. Check if in-browser ONNX model is available locally
      let inBrowserResult = null;
      try {
        inBrowserResult = await runInBrowserDiagnosis(canvas512, selectedCrop);
      } catch (err) {
        console.info('In-browser model bypassed, falling back to server vision:', err);
      }

      // If in-browser model gave high confidence (>= 0.70)
      if (
        inBrowserResult &&
        inBrowserResult.label !== 'unloaded' &&
        inBrowserResult.confidence >= CONFIDENCE_THRESHOLD
      ) {
        if (inBrowserResult.heatmapDataUrl) {
          setHeatmapUrl(inBrowserResult.heatmapDataUrl);
        }
        setTopProbs(inBrowserResult.allProbabilities || []);
        const effectiveCrop =
          selectedCrop === 'Auto-Detect'
            ? inBrowserResult.detectedCrop || 'Auto-Detect'
            : selectedCrop;
        const adviceRes = await apiClient.post<DiseaseDiagnosis>('/advice/disease', {
          crop: effectiveCrop,
          predicted_label: inBrowserResult.label,
          confidence: inBrowserResult.confidence,
          model_version: 'onnx-mobilenet-v3-small',
        });
        const finalDiag = {
          ...adviceRes.data,
          confidence: inBrowserResult.confidence,
          model_version: 'onnx-mobilenet-v3-small',
          is_fallback: false,
          heatmap_url: inBrowserResult.heatmapDataUrl,
        };
        setDiagnosis(finalDiag);
        offlineStorage.saveDiseaseAdvice(finalDiag);
        return;
      }

      setTopProbs(inBrowserResult?.allProbabilities || []);

      // 3. High-Accuracy Server Vision Fallback (Gemini Vision with Rajasthan POP Grounding)
      const blob = await new Promise<Blob | null>((resolve) =>
        canvas512.toBlob((b) => resolve(b), 'image/jpeg', 0.92)
      );
      if (!blob) throw new Error('Could not convert canvas to image blob');

      const formData = new FormData();
      formData.append('crop', selectedCrop);
      formData.append('opt_in_store', optInStore ? 'true' : 'false');
      formData.append('file', blob, 'leaf_sample.jpg');

      const res = await apiClient.post<DiseaseDiagnosis>('/diagnose', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const serverDiag = {
        ...res.data,
        is_fallback: res.data.confidence < CONFIDENCE_THRESHOLD,
      };
      setDiagnosis(serverDiag);
      offlineStorage.saveDiseaseAdvice(serverDiag);
    } catch (err: any) {
      console.error('Diagnosis failed:', err);
      const cached = offlineStorage.getDiseaseAdvice<DiseaseDiagnosis>();
      if (cached) {
        setDiagnosis(cached);
        setError(
          isHindi
            ? 'ऑफ़लाइन मोड: पिछली जांची गई बीमारी की सलाह दिखाई जा रही है।'
            : 'Offline mode: Showing cached diagnostic advice.'
        );
      } else {
        setError(
          err?.response?.data?.detail ||
            (isHindi
              ? 'रोग विश्लेषण में त्रुटि आई। कृपया इंटरनेट कनेक्शन जांचें।'
              : 'Disease diagnosis failed. Please check your network.')
        );
      }
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto my-6 px-4 space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center shadow-inner">
            <Camera className="w-6 h-6" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">
              {isHindi ? 'फसल रोग पहचान एवं वैज्ञानिक उपचार' : 'Crop Disease Diagnosis & Treatment'}
            </h1>
            <p className="text-xs text-slate-500">
              {isHindi
                ? 'AI विज़न मॉडल द्वारा पत्ती के रोग लक्षणों की सटीक पहचान एवं विश्वविद्यालय-अनुशंसित दवा छिड़काव सलाह'
                : 'High-accuracy AI vision pathology grounded in official Rajasthan Agriculture University Package of Practices'}
            </p>
          </div>
        </div>

        {/* Crop Selection */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="crop-select" className="block text-xs font-semibold text-slate-700 mb-1">
              {isHindi ? 'फसल चुनें (Select Crop)' : 'Select Crop'}
            </label>
            <select
              id="crop-select"
              value={selectedCrop}
              onChange={(e) => {
                setSelectedCrop(e.target.value);
                setDiagnosis(null);
                setTopProbs([]);
              }}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none bg-white font-medium text-slate-800"
            >
              {CROPS.map((c) => (
                <option key={c.id} value={c.id}>
                  {isHindi ? c.hi : c.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <div className="flex items-center gap-1.5 text-xs text-emerald-700 bg-emerald-50 px-3 py-2 rounded-lg border border-emerald-200 w-full">
              <Cpu className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
              <span>
                {isHindi
                  ? '512px ऑटो रिसाइज एवं EXIF गोपनीयता सुरक्षा'
                  : '512px in-memory resize with EXIF location stripping'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Upload and Capture Section */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png"
          onChange={handleInputChange}
          className="hidden"
          aria-label="Upload leaf image"
        />
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/jpeg,image/png"
          capture="environment"
          onChange={handleInputChange}
          className="hidden"
          aria-label="Capture leaf photo"
        />

        {selectedImage ? (
          <div className="space-y-4">
            <div className="relative rounded-xl overflow-hidden border border-slate-200 bg-black/5 max-h-96 flex items-center justify-center">
              <img
                ref={imageElementRef}
                src={selectedImage}
                alt="Selected Leaf Sample"
                className="max-h-96 w-auto object-contain rounded-xl"
              />

              {showHeatmap && heatmapUrl && (
                <img
                  src={heatmapUrl}
                  alt="Lesion Activation Heatmap"
                  className="absolute inset-0 w-full h-full object-contain rounded-xl opacity-60 mix-blend-screen pointer-events-none"
                />
              )}

              {heatmapUrl && (
                <button
                  type="button"
                  onClick={() => setShowHeatmap(!showHeatmap)}
                  className="absolute bottom-3 right-3 bg-slate-900/80 hover:bg-slate-900 text-white text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1.5 backdrop-blur-sm transition"
                  aria-pressed={showHeatmap}
                >
                  {showHeatmap ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  <span>{showHeatmap ? (isHindi ? 'हीटमैप छुपाएं' : 'Hide Lesions') : (isHindi ? 'रोग क्षेत्र देखें' : 'View Lesions')}</span>
                </button>
              )}
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => {
                  setSelectedImage(null);
                  setDiagnosis(null);
                }}
                className="flex-1 py-2 text-xs font-bold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-xl transition flex items-center justify-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>{isHindi ? 'अन्य फोटो चुनें' : 'Choose Different Photo'}</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div
              onClick={() => cameraInputRef.current?.click()}
              className="border-2 border-dashed border-emerald-300 hover:border-emerald-500 rounded-xl p-8 text-center cursor-pointer bg-emerald-50/30 hover:bg-emerald-50/60 transition-all flex flex-col items-center justify-center"
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && cameraInputRef.current?.click()}
              aria-label={isHindi ? 'कैमरा से फोटो खींचें' : 'Take Leaf Photo'}
            >
              <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center mb-3">
                <Camera className="w-6 h-6" aria-hidden="true" />
              </div>
              <div className="text-sm font-semibold text-slate-800">{isHindi ? 'कैमरा से फोटो खींचें' : 'Take Leaf Photo'}</div>
              <p className="text-[11px] text-slate-500 mt-1">{isHindi ? 'पत्ती के रोगग्रस्त भाग पर फोकस करें' : 'Focus closely on diseased leaf lesion'}</p>
            </div>

            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-300 hover:border-brand-500 rounded-xl p-8 text-center cursor-pointer bg-slate-50 hover:bg-brand-50/20 transition-all flex flex-col items-center justify-center"
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
              aria-label={isHindi ? 'गैलरी से फोटो अपलोड करें' : 'Upload from Device'}
            >
              <div className="w-12 h-12 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center mb-3">
                <Upload className="w-6 h-6" aria-hidden="true" />
              </div>
              <div className="text-sm font-semibold text-slate-800">{isHindi ? 'गैलरी से फोटो अपलोड करें' : 'Upload from Device'}</div>
              <p className="text-[11px] text-slate-500 mt-1">{isHindi ? 'JPEG या PNG (अधिकतम 5 MB)' : 'JPEG or PNG (Max 5 MB)'}</p>
            </div>
          </div>
        )}

        {/* Opt-in Privacy Checkbox */}
        <div className="mt-5 p-3.5 bg-slate-50 rounded-xl border border-slate-200">
          <label className="flex items-start gap-2.5 text-xs text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={optInStore}
              onChange={(e) => setOptInStore(e.target.checked)}
              className="mt-0.5 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
            />
            <div>
              <span className="font-semibold text-slate-900">
                {isHindi ? 'मॉडल सुधार योगदान विकल्प (Opt-in Photo Contribution):' : 'Opt-in Model Improvement:'}
              </span>{' '}
              {isHindi
                ? 'राजस्थान के अन्य किसानों की मदद हेतु फोटो को सुरक्षित सुपाबेस बकेट में बिना स्थान व EXIF डेटा के सहेजने की अनुमति दें।'
                : 'Allow storing photo in a private Supabase bucket without EXIF/location metadata to help improve Rajasthan crop models.'}
            </div>
          </label>
        </div>

        {/* Main Diagnose Button */}
        <div className="mt-4">
          <button
            onClick={runDiagnosis}
            disabled={!selectedImage || analyzing}
            className="w-full py-3.5 px-4 bg-primary-600 hover:bg-primary-700 text-white rounded-xl text-sm font-bold shadow-md transition disabled:opacity-50 flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {analyzing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" aria-hidden="true" />
                <span>{isHindi ? 'रोग विश्लेषण जारी है...' : 'Analyzing Leaf Pathology...'}</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" aria-hidden="true" />
                <span>{isHindi ? 'पत्ती रोग की सटीक पहचान करें' : 'Diagnose Crop Disease'}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Notice */}
      {error && (
        <div role="alert" className="bg-rose-50 border border-rose-200 rounded-2xl p-4 text-rose-800 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div className="text-xs">{error}</div>
        </div>
      )}

      {/* Diagnosis Results Card */}
      {diagnosis && (
        <div
          className={`rounded-2xl p-6 border shadow-sm space-y-4 ${
            diagnosis.confidence < CONFIDENCE_THRESHOLD || diagnosis.is_fallback
              ? 'bg-gradient-to-br from-amber-50 to-orange-50/50 border-amber-300'
              : 'bg-white border-slate-200'
          }`}
        >
          {/* Top Result Banner */}
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 border-b border-slate-100 pb-3">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                {isHindi ? 'पहचाना गया रोग' : 'Identified Condition'}
              </span>
              <h2 className="text-xl font-bold text-slate-900 mt-0.5">{diagnosis.predicted_label}</h2>
              <div className="text-xs text-slate-500 mt-0.5">
                {diagnosis.crop} • {isHindi ? 'सत्यापित मॉडल:' : 'Model:'}{' '}
                <span className="font-mono text-slate-700 font-semibold">{diagnosis.model_version}</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div
                className={`px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 ${
                  diagnosis.confidence >= CONFIDENCE_THRESHOLD
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                    : 'bg-amber-100 text-amber-900 border border-amber-300'
                }`}
              >
                <span>{isHindi ? 'सटीकता' : 'Confidence'}:</span>
                <span className="text-sm font-mono font-extrabold">{(diagnosis.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>

          {/* Top-3 Differential Probabilities */}
          {topProbs.length > 1 && (
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/70 space-y-1.5">
              <div className="text-[11px] font-semibold text-slate-600">
                {isHindi ? 'शीर्ष संभावित रोग वर्गीकरण (Top Differential Matches):' : 'Top Differential Matches:'}
              </div>
              {topProbs.map((item, idx) => (
                <div key={idx} className="flex items-center gap-2 text-xs">
                  <span className="w-48 truncate text-slate-700 font-medium">
                    {item.hindiLabel || item.label}
                  </span>
                  <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${idx === 0 ? 'bg-emerald-600' : 'bg-slate-400'}`}
                      style={{ width: `${Math.max(2, Math.round(item.prob * 100))}%` }}
                    />
                  </div>
                  <span className="w-10 text-right font-mono text-[11px] text-slate-600">
                    {(item.prob * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Low Confidence (< 0.70) KVK Fallback Card */}
          {diagnosis.confidence < CONFIDENCE_THRESHOLD && (
            <div className="p-4 bg-amber-100/80 rounded-xl border border-amber-300 text-amber-950 space-y-3">
              <div className="flex items-start gap-2.5">
                <HelpCircle className="w-5 h-5 text-amber-800 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <div className="font-bold text-sm">
                    {isHindi ? 'लक्षण अस्पष्ट — कृपया निकटतम KVK से संपर्क करें' : 'Uncertain Symptoms — Consult Nearest KVK'}
                  </div>
                  <p className="text-xs text-amber-900 mt-1 leading-relaxed">
                    {isHindi
                      ? 'फोटो में लक्षण पूर्णतः स्पष्ट नहीं हैं (विश्वास स्तर 70% से कम है)। गलत कीटनाशक के छिड़काव से फसल को नुकसान हो सकता है। कृपया किसी भी रसायन का प्रयोग करने से पहले निकटतम कृषि विज्ञान केंद्र (KVK) के वैज्ञानिक से सलाह लें।'
                      : 'The leaf symptoms are not distinct enough (confidence is below the 70% safety threshold). Avoid guessing pesticides; consult your local Krishi Vigyan Kendra (KVK) expert.'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Scientific Treatment Guidance */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 shadow-sm space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-800 uppercase tracking-wide">
              <BookOpen className="w-4 h-4 text-primary-700" aria-hidden="true" />
              <span>{isHindi ? 'वैज्ञानिक रोग उपचार एवं अनुशंसित दवा' : 'Scientific Treatment & Spray Advisory'}</span>
            </div>
            <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-medium">
              {diagnosis.treatment_advice}
            </p>
          </div>

          {/* Prevention Cultural Practices */}
          {diagnosis.prevention_steps && diagnosis.prevention_steps.length > 0 && (
            <div className="p-4 bg-white rounded-xl border border-slate-200 text-xs text-slate-700 space-y-2">
              <div className="font-bold text-slate-800">
                {isHindi ? 'रोकथाम एवं कृषि कार्य (Prevention Measures):' : 'Prevention & Cultural Practices:'}
              </div>
              <ul className="list-disc list-inside space-y-1 text-slate-600 pl-1">
                {diagnosis.prevention_steps.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Verified Source Citations */}
          {diagnosis.sources && diagnosis.sources.length > 0 && (
            <div className="p-3 bg-primary-50/60 rounded-xl border border-primary-100 text-[11px] text-primary-900 space-y-1">
              <div className="font-semibold flex items-center gap-1.5 text-primary-800">
                <CheckCircle2 className="w-3.5 h-3.5 text-primary-700" aria-hidden="true" />
                <span>{isHindi ? 'सत्यापित स्रोत (Verified Source):' : 'Verified Source Citation:'}</span>
              </div>
              {diagnosis.sources.map((s, idx) => (
                <div key={idx} className="text-slate-700">
                  <span className="font-semibold">{s.doc_title}</span> — {s.source}
                </div>
              ))}
            </div>
          )}

          {/* Mandatory Chemical Advisory Disclaimer */}
          <div className="pt-2 border-t border-slate-200/80 flex items-start gap-2 text-[11px] text-slate-500">
            <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <span>{diagnosis.disclaimer}</span>
          </div>

          {/* Feedback on Diagnosis */}
          <FeedbackButtons />
        </div>
      )}
    </div>
  );
};

export default DiagnosePage;
