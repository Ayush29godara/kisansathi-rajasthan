/**
 * Client-Side ONNX Runtime Web Model Execution Pipeline
 * Runs lightweight MobileNetV3-Small vision model inside the farmer's browser.
 */

import * as ort from 'onnxruntime-web/wasm';

const MODEL_PATH = '/models/crop_disease.onnx';
const LABELS_PATH = '/models/crop_disease_labels.json';
export const CONFIDENCE_THRESHOLD = 0.70;

const ONNX_SUPPORTED_CROPS = new Set(['bajra', 'mustard', 'tomato', 'wheat']);

let session: ort.InferenceSession | null = null;
let labelsMetadata: {
  classes: string[];
  class_labels_hi: Record<string, string>;
  confidence_threshold: number;
} | null = null;

export interface InBrowserPrediction {
  label: string;
  hindiLabel: string;
  detectedCrop?: string;
  confidence: number;
  isFallback: boolean;
  heatmapDataUrl?: string;
  allProbabilities?: { label: string; hindiLabel?: string; prob: number }[];
}

/**
 * Resize image onto canvas with max dimension of 512px, stripping EXIF and optimizing for client inference.
 */
export function resizeImageTo512Canvas(
  imgElement: HTMLImageElement
): HTMLCanvasElement {
  const maxDim = 512;
  let width = imgElement.naturalWidth || imgElement.width || 224;
  let height = imgElement.naturalHeight || imgElement.height || 224;

  if (width > maxDim || height > maxDim) {
    if (width > height) {
      height = Math.round((height * maxDim) / width);
      width = maxDim;
    } else {
      width = Math.round((width * maxDim) / height);
      height = maxDim;
    }
  }

  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.drawImage(imgElement, 0, 0, width, height);
  }
  return canvas;
}

/**
 * Load metadata labels JSON.
 */
export async function loadLabelsMetadata(): Promise<boolean> {
  if (labelsMetadata) return true;
  try {
    const res = await fetch(LABELS_PATH);
    if (res.ok) {
      labelsMetadata = await res.json();
      return true;
    }
  } catch (err) {
    console.warn('Could not load local crop_disease_labels.json:', err);
  }
  return false;
}

/**
 * Initialize ONNX Runtime Web session.
 */
export async function loadDiseaseModel(): Promise<boolean> {
  if (session) return true;
  try {
    const headRes = await fetch(MODEL_PATH, { method: 'HEAD' });
    const contentType = headRes.headers.get('content-type') || '';
    if (!headRes.ok || contentType.includes('text/html')) {
      return false;
    }
    await loadLabelsMetadata();
    ort.env.wasm.numThreads = 1;
    ort.env.wasm.wasmPaths = {
      wasm: '/ort/ort-wasm-simd-threaded.wasm',
    };
    session = await ort.InferenceSession.create(MODEL_PATH, {
      executionProviders: ['wasm'],
      graphOptimizationLevel: 'all',
    });
    return true;
  } catch (err) {
    console.info('Local ONNX model not yet downloaded or unsupported, will use server fallback:', err);
    return false;
  }
}

/**
 * Generate 2D lesion salience heatmap highlighting chlorotic/necrotic/pustule pixels on the leaf.
 */
export function generateActivationHeatmap(
  canvas: HTMLCanvasElement,
  confidence: number
): string {
  const heatmapCanvas = document.createElement('canvas');
  heatmapCanvas.width = canvas.width;
  heatmapCanvas.height = canvas.height;
  const ctx = heatmapCanvas.getContext('2d');
  if (!ctx) return '';

  ctx.drawImage(canvas, 0, 0);
  const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const { data, width, height } = imgData;

  let weightedX = 0;
  let weightedY = 0;
  let totalWeight = 0;

  for (let y = 0; y < height; y += 2) {
    for (let x = 0; x < width; x += 2) {
      const idx = (y * width + x) * 4;
      const r = data[idx];
      const g = data[idx + 1];
      const b = data[idx + 2];
      // Highlight yellow/brown chlorotic or white pustule anomalies relative to healthy green
      const lesionScore = Math.max(0, (r - g * 0.85) + Math.abs(r - b) * 0.3);
      if (lesionScore > 25) {
        weightedX += x * lesionScore;
        weightedY += y * lesionScore;
        totalWeight += lesionScore;
      }
    }
  }

  const centerX = totalWeight > 0 ? weightedX / totalWeight : canvas.width * 0.5;
  const centerY = totalWeight > 0 ? weightedY / totalWeight : canvas.height * 0.5;
  const radius = Math.min(canvas.width, canvas.height) * 0.4;

  const gradient = ctx.createRadialGradient(centerX, centerY, 8, centerX, centerY, radius);
  gradient.addColorStop(0, `rgba(239, 68, 68, ${Math.min(confidence * 0.72, 0.68)})`);
  gradient.addColorStop(0.45, `rgba(245, 158, 11, ${Math.min(confidence * 0.5, 0.48)})`);
  gradient.addColorStop(0.75, 'rgba(59, 130, 246, 0.22)');
  gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

  ctx.globalCompositeOperation = 'screen';
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  return heatmapCanvas.toDataURL('image/jpeg', 0.85);
}

function inferCropFromLabel(label: string): string {
  const prefix = label.split('_')[0]?.toLowerCase();
  if (prefix === 'bajra') return 'Bajra';
  if (prefix === 'mustard') return 'Mustard';
  if (prefix === 'tomato') return 'Tomato';
  if (prefix === 'wheat') return 'Wheat';
  return 'Auto-Detect';
}

/**
 * Run client-side inference on a 512px canvas with crop-aware probability filtering.
 */
export async function runInBrowserDiagnosis(
  canvas: HTMLCanvasElement,
  selectedCrop: string = 'Auto-Detect'
): Promise<InBrowserPrediction> {
  const cropKey = selectedCrop.trim().toLowerCase();
  const isAuto = cropKey === 'auto-detect' || cropKey === 'all' || cropKey === '';

  // If user explicitly chose a crop not in the 24-class local ONNX model (e.g., Soybean, Guar, Gram),
  // bypass local ONNX so the server Gemini Vision classifier handles it.
  if (!isAuto && !ONNX_SUPPORTED_CROPS.has(cropKey)) {
    return {
      label: 'unloaded',
      hindiLabel: 'सर्वर विज़न विश्लेषण',
      confidence: 0,
      isFallback: true,
    };
  }

  const isLoaded = await loadDiseaseModel();

  if (!isLoaded || !session) {
    return {
      label: 'unloaded',
      hindiLabel: 'लोकल मॉडल अनुपलब्ध',
      confidence: 0,
      isFallback: true,
    };
  }

  try {
    // 1. Prepare 224x224 input canvas
    const tensorCanvas = document.createElement('canvas');
    tensorCanvas.width = 224;
    tensorCanvas.height = 224;
    const ctx = tensorCanvas.getContext('2d');
    if (!ctx) throw new Error('Could not get 2d context');
    ctx.drawImage(canvas, 0, 0, 224, 224);

    const imgData = ctx.getImageData(0, 0, 224, 224);
    const { data } = imgData;

    // 2. Preprocess into planar [1, 3, 224, 224] Float32Array with ImageNet normalization
    const mean = [0.485, 0.456, 0.406];
    const std = [0.229, 0.224, 0.225];
    const float32Data = new Float32Array(3 * 224 * 224);

    const channelSize = 224 * 224;
    for (let i = 0; i < channelSize; i++) {
      const r = data[i * 4] / 255.0;
      const g = data[i * 4 + 1] / 255.0;
      const b = data[i * 4 + 2] / 255.0;

      float32Data[i] = (r - mean[0]) / std[0];
      float32Data[channelSize + i] = (g - mean[1]) / std[1];
      float32Data[2 * channelSize + i] = (b - mean[2]) / std[2];
    }

    const inputTensor = new ort.Tensor('float32', float32Data, [1, 3, 224, 224]);

    // 3. Run session
    const inputName = session.inputNames[0] || 'input';
    const feeds: Record<string, ort.Tensor> = { [inputName]: inputTensor };

    const results = await session.run(feeds);
    const outputName = session.outputNames[0] || 'output';
    const outputTensor = results[outputName];
    const logits = outputTensor.data as Float32Array;

    const classList = labelsMetadata?.classes || [];

    // 4. Compute global Softmax probabilities
    let maxLogit = -Infinity;
    for (let i = 0; i < logits.length; i++) {
      if (logits[i] > maxLogit) maxLogit = logits[i];
    }
    const expVals = new Float32Array(logits.length);
    let sumExp = 0.0;
    for (let i = 0; i < logits.length; i++) {
      expVals[i] = Math.exp(logits[i] - maxLogit);
      sumExp += expVals[i];
    }

    const globalProbs: { idx: number; label: string; prob: number }[] = [];
    for (let i = 0; i < logits.length; i++) {
      globalProbs.push({
        idx: i,
        label: classList[i] || `class_${i}`,
        prob: expVals[i] / sumExp,
      });
    }

    // 5. If user selected a specific crop (Mustard, Tomato, Wheat, Bajra), check crop probability mass
    let activeProbs = [...globalProbs];
    if (!isAuto && ONNX_SUPPORTED_CROPS.has(cropKey)) {
      const cropPrefix = `${cropKey}_`;
      const matching = globalProbs.filter((p) => p.label.startsWith(cropPrefix));
      const cropMass = matching.reduce((acc, p) => acc + p.prob, 0);

      // If leaf plausibly matches selected crop (cropMass >= 0.12), re-normalize over that crop's classes
      if (cropMass >= 0.12 && matching.length > 0) {
        activeProbs = matching.map((p) => ({
          ...p,
          prob: p.prob / cropMass,
        }));
      }
    }

    activeProbs.sort((a, b) => b.prob - a.prob);
    const top1 = activeProbs[0];
    const topLabel = top1.label || 'uncertain_or_unrecognized';
    const hindiLabel = labelsMetadata?.class_labels_hi?.[topLabel] || topLabel;
    const detectedCrop = inferCropFromLabel(topLabel);
    const heatmap = generateActivationHeatmap(canvas, top1.prob);

    return {
      label: topLabel,
      hindiLabel,
      detectedCrop,
      confidence: top1.prob,
      isFallback: top1.prob < CONFIDENCE_THRESHOLD,
      heatmapDataUrl: heatmap,
      allProbabilities: activeProbs.slice(0, 3).map((p) => ({
        label: p.label,
        hindiLabel: labelsMetadata?.class_labels_hi?.[p.label] || p.label,
        prob: p.prob,
      })),
    };
  } catch (err) {
    console.error('In-browser ONNX inference failed:', err);
    return {
      label: 'unloaded',
      hindiLabel: 'पहचान अस्पष्ट',
      confidence: 0,
      isFallback: true,
    };
  }
}
