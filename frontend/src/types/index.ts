/**
 * TypeScript Data Models and API Contracts for KisanSathi Rajasthan
 */

export type LanguageCode = 'hi' | 'en';

export type IrrigationType = 'canal' | 'tubewell' | 'well' | 'rainfed';

export interface UserProfile {
  user_id: string;
  language: LanguageCode;
  created_at?: string;
  updated_at?: string;
}

export interface FarmProfile {
  farm_id: string;
  user_id: string;
  district: string;
  tehsil: string;
  crop: string;
  land_hectare: number;
  irrigation: IrrigationType;
  sowing_date: string;
  created_at?: string;
  updated_at?: string;
}

export interface SourceCitation {
  doc_title: string;
  source: string;
  chunk_text: string;
  relevance_score?: number;
}

export interface ChatMessage {
  id?: string;
  question: string;
  intent: 'price' | 'yield' | 'weather' | 'disease' | 'general';
  answer: string;
  sources: SourceCitation[];
  model_version: string;
  disclaimer: string;
  created_at?: string;
}

export interface DiseaseDiagnosis {
  crop: string;
  predicted_label: string;
  confidence: number;
  model_version: string;
  is_fallback: boolean;
  treatment_advice: string;
  prevention_steps: string[];
  sources: SourceCitation[];
  disclaimer: string;
  image_path?: string;
  heatmap_url?: string;
}

export interface YieldDriver {
  feature: string;
  impact: 'positive' | 'negative' | 'neutral';
  description: string;
}

export interface YieldOutlook {
  district: string;
  crop: string;
  season: string;
  forecast_year: number;
  predicted_yield_kg_ha: number;
  baseline_5yr_mean_kg_ha: number;
  model_version: string;
  top_drivers: YieldDriver[];
  summary_text: string;
}

export interface PriceForecastRange {
  min_expected: number;
  max_expected: number;
  expected_modal: number;
}

export interface MandiPriceRecord {
  price_date: string;
  modal_price: number;
  min_price: number;
  max_price: number;
  arrivals?: number;
}

export interface MandiPriceForecast {
  mandi: string;
  commodity: string;
  latest_date: string;
  latest_modal_price: number;
  trend: 'bullish' | 'bearish' | 'stable';
  forecast_2_weeks: PriceForecastRange;
  forecast_4_weeks: PriceForecastRange;
  model_version: string;
  recommendation?: 'sell_now' | 'wait' | 'hold';
  recommendation_text?: string;
  disclaimer?: string;
  history: MandiPriceRecord[];
  explanation: string;
}

export interface WeatherAlertItem {
  alert_type: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  source?: string;
}

export interface WeatherDaySummary {
  date: string;
  temp_max: number;
  temp_min: number;
  rain_mm: number;
}

export interface IrrigationSchedule {
  district: string;
  crop: string;
  et0_mm_day: number;
  kc_factor: number;
  crop_etc_mm_day: number;
  days_since_sowing: number;
  current_growth_stage: string;
  next_irrigation_due_days: number;
  water_depth_mm: number;
  irrigation_urgency: 'normal' | 'due_soon' | 'immediate' | 'withhold_due_to_rain';
  advisory_text: string;
  alerts: WeatherAlertItem[];
  weather_summary?: {
    temp_max: number;
    temp_min: number;
    humidity: number;
    wind_speed: number;
    precipitation_sum: number;
    precipitation_72h: number;
    forecast_days?: WeatherDaySummary[];
  };
  methodology?: string;
}

export interface HistoryItem {
  id: string;
  question: string;
  intent: 'price' | 'yield' | 'weather' | 'disease' | 'general';
  answer: string;
  sources: SourceCitation[];
  model_version: string;
  created_at: string;
  feedback_rating?: number | null;
  actual_outcome?: string | null;
}

export interface ModuleMetadata {
  module: string;
  model_type: string;
  version: string;
  accuracy_metric: string;
  metric_value: string;
  training_date?: string | null;
  data_source: string;
  limitations: string[];
}

export interface SystemMetadata {
  project: string;
  version: string;
  environment: string;
  modules: ModuleMetadata[];
}

export interface FeedbackPayload {
  message_id?: string;
  rating: number; // 1 for thumbs up, -1 for thumbs down
  actual_outcome?: string;
}

export interface OfflineQueuedMessage {
  tempId: string;
  question: string;
  language: LanguageCode;
  timestamp: number;
}
