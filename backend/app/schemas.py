"""Pydantic schemas for data validation and API request/response contracts."""

from datetime import date, datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Common / System Schemas
# -----------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = "ok"
    version: str = "0.1.0"
    environment: str = "development"
    database: str = "connected"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SourceCitation(BaseModel):
    """Knowledge base source citation for RAG answers."""
    doc_title: str
    source: str
    chunk_text: str
    relevance_score: Optional[float] = None


# -----------------------------------------------------------------------------
# User & Farm Profile Schemas
# -----------------------------------------------------------------------------

class FarmBase(BaseModel):
    """Farm profile capturing local agro-parameters."""
    district: str = Field(..., description="Rajasthan district name")
    tehsil: str = Field(..., description="Sub-district / Tehsil")
    crop: str = Field(..., description="Primary cultivated crop")
    land_hectare: float = Field(..., gt=0, description="Farm land size in hectares")
    irrigation: Literal["canal", "tubewell", "well", "rainfed"] = Field(
        ..., description="Primary irrigation water source"
    )
    sowing_date: date = Field(..., description="Date of sowing for the current crop season")


class FarmCreate(FarmBase):
    pass


class FarmUpdate(BaseModel):
    district: Optional[str] = None
    tehsil: Optional[str] = None
    crop: Optional[str] = None
    land_hectare: Optional[float] = Field(None, gt=0)
    irrigation: Optional[Literal["canal", "tubewell", "well", "rainfed"]] = None
    sowing_date: Optional[date] = None


class FarmResponse(FarmBase):
    farm_id: str
    user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProfileBase(BaseModel):
    """User profile base schema."""
    language: Literal["hi", "en"] = "hi"


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    language: Optional[Literal["hi", "en"]] = None
    farm: Optional[FarmUpdate] = None


class ProfileResponse(ProfileBase):
    user_id: str
    farm: Optional[FarmResponse] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# -----------------------------------------------------------------------------
# Advisor Chat Schemas
# -----------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Advisor chat request query."""
    question: str = Field(..., min_length=1, description="Farmer query in Hindi or English")
    language: Optional[Literal["hi", "en"]] = None


class ChatResponse(BaseModel):
    """Grounded advisor chat answer with source citations."""
    id: Optional[str] = None
    question: str
    intent: str = Field(..., description="Classified intent: price/yield/weather/disease/general")
    answer: str = Field(..., description="Answer text phrased in the user's preferred language")
    sources: List[SourceCitation] = Field(default_factory=list, description="Grounding document sources")
    model_version: str = "gemini-1.5-flash"
    disclaimer: str = "यह सलाह केवल मार्गदर्शन हेतु है। विशिष्ट समस्याओं के लिए निकटतम कृषि विज्ञान केंद्र (KVK) से संपर्क करें।"
    created_at: datetime = Field(default_factory=datetime.utcnow)


# -----------------------------------------------------------------------------
# Crop Disease Detection Schemas
# -----------------------------------------------------------------------------

class DiseaseDiagnosisResponse(BaseModel):
    """Disease detection response either from browser ONNX sync or server fallback."""
    crop: str
    predicted_label: str
    confidence: float
    model_version: str
    is_fallback: bool = False
    treatment_advice: str
    prevention_steps: List[str] = Field(default_factory=list)
    sources: List[SourceCitation] = Field(default_factory=list)
    disclaimer: str = "सलाह केवल मार्गदर्शन हेतु है। गंभीर संक्रमण में तुरंत KVK विशेषज्ञ से परामर्श लें।"
    image_path: Optional[str] = None
    heatmap_url: Optional[str] = None


class DiseaseRecordCreate(BaseModel):
    """Schema to record client-side ONNX prediction to history (opt-in image path)."""
    crop: str
    predicted_label: str
    confidence: float
    model_version: str = "onnx-mobilenet-v3"
    image_path: Optional[str] = None


# -----------------------------------------------------------------------------
# District Yield Outlook Schemas
# -----------------------------------------------------------------------------

class YieldDriver(BaseModel):
    """Feature attribution explanation driver."""
    feature: str
    impact: Literal["positive", "negative", "neutral"]
    description: str


class YieldOutlookResponse(BaseModel):
    """District yield forecast and drivers."""
    district: str
    crop: str
    season: str
    forecast_year: int
    predicted_yield_kg_ha: float
    baseline_5yr_mean_kg_ha: float
    model_version: str
    top_drivers: List[YieldDriver] = Field(default_factory=list)
    summary_text: str


# -----------------------------------------------------------------------------
# Mandi Price Trend & Forecast Schemas
# -----------------------------------------------------------------------------

class PriceForecastRange(BaseModel):
    min_expected: float
    max_expected: float
    expected_modal: float


class MandiPriceRecord(BaseModel):
    price_date: date
    modal_price: float
    min_price: float
    max_price: float
    arrivals: Optional[float] = None


class MandiPriceForecastResponse(BaseModel):
    """Mandi price trend and 2-4 week forecast."""
    mandi: str
    commodity: str
    latest_date: date
    latest_modal_price: float
    trend: Literal["bullish", "bearish", "stable"]
    forecast_2_weeks: PriceForecastRange
    forecast_4_weeks: PriceForecastRange
    model_version: str
    recommendation: Literal["sell_now", "wait", "hold"] = "hold"
    recommendation_text: str = Field(
        default="",
        description="Actionable decision hint (e.g. Wait / Sell now) based on trend and price projections"
    )
    disclaimer: str = Field(
        default="यह भाव पूर्वानुमान और सलाह केवल मार्गदर्शन हेतु है। वास्तविक बाजार भाव स्थानीय मांग, गुणवत्ता और सरकारी नीतियों पर निर्भर करते हैं।",
        description="Clear guidance disclaimer reminding farmers of market risk"
    )
    history: List[MandiPriceRecord] = Field(default_factory=list)
    explanation: str


# -----------------------------------------------------------------------------
# Weather Alert & FAO-56 Irrigation Schemas
# -----------------------------------------------------------------------------

class WeatherAlertItem(BaseModel):
    alert_type: str
    severity: Literal["info", "warning", "critical"]
    message: str
    source: Optional[str] = Field(
        default="Package of Practices, Agriculture University Kota / SKNAU Jobner / ICAR-CAZRI",
        description="University advisory reference source for this agronomic rule"
    )


class IrrigationScheduleResponse(BaseModel):
    """FAO-56 evapotranspiration based irrigation schedule."""
    district: str
    crop: str
    et0_mm_day: float
    kc_factor: float
    crop_etc_mm_day: float
    days_since_sowing: int
    current_growth_stage: str
    next_irrigation_due_days: int
    water_depth_mm: float
    irrigation_urgency: Literal["normal", "due_soon", "immediate", "withhold_due_to_rain"]
    advisory_text: str
    alerts: List[WeatherAlertItem] = Field(default_factory=list)
    weather_summary: Optional[Dict[str, Any]] = None
    methodology: str = "FAO-56 Penman-Monteith (Physics-based deterministic model, zero ML)"


# -----------------------------------------------------------------------------
# User Feedback Schemas
# -----------------------------------------------------------------------------

class FeedbackCreate(BaseModel):
    message_id: Optional[str] = None
    rating: int = Field(..., ge=-1, le=5, description="Thumbs up/down or 1-5 scale")
    actual_outcome: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: str
    status: str = "recorded"


# -----------------------------------------------------------------------------
# History & Metadata Schemas (Phase 7)
# -----------------------------------------------------------------------------

class HistoryItemResponse(BaseModel):
    id: str
    question: str
    intent: str
    answer: str
    sources: List[Dict[str, Any]] = []
    model_version: str
    created_at: datetime
    feedback_rating: Optional[int] = None
    actual_outcome: Optional[str] = None


class ModuleMetadata(BaseModel):
    module: str
    model_type: str
    version: str
    accuracy_metric: str
    metric_value: str
    training_date: Optional[str] = None
    data_source: str
    limitations: List[str]


class SystemMetadataResponse(BaseModel):
    project: str
    version: str
    environment: str
    modules: List[ModuleMetadata]
