"""Crop disease advice and server-side fallback diagnosis service."""

import io
from typing import Dict, Any, Tuple, Optional
from PIL import Image
from app.config import get_settings
from app.schemas import DiseaseDiagnosisResponse, SourceCitation

settings = get_settings()

CONFIDENCE_THRESHOLD = 0.70

# Curated reference treatments from Rajasthan Agriculture University / ICAR guidelines
VERIFIED_DISEASE_KB: Dict[str, Dict[str, Any]] = {
    "mustard_white_rust": {
        "disease_name": "White Rust (सफेद रोली)",
        "crop": "Mustard",
        "treatment": "मैनकोजेब (Mancozeb 75% WP) 2 ग्राम प्रति लीटर पानी की दर से छिड़काव करें। पहला लक्षण दिखते ही उपचार प्रारंभ करें।",
        "prevention": [
            "प्रमाणित एवं उपचारित बीज ही बोएं।",
            "फसल चक्र अपनाएं एवं खेत की गहरी जुताई करें।",
            "खेत में जलभराव न होने दें।"
        ],
        "source": "Package of Practices for Rabi Crops, Agriculture University Kota",
    },
    "bajra_blast": {
        "disease_name": "Blast / Leaf Spot (पत्ती धब्बा रोग)",
        "crop": "Bajra",
        "treatment": "जैनेब (Zineb) या मैनकोजेब 2 ग्राम प्रति लीटर पानी का छिड़काव करें।",
        "prevention": [
            "रोग-रोधी किस्में लगाएं।",
            "नाइट्रोजन का अत्यधिक प्रयोग न करें।"
        ],
        "source": "ICAR-CAZRI Technical Bulletin, Jodhpur",
    },
}


def sanitize_and_strip_exif(image_bytes: bytes) -> bytes:
    """
    Validate JPEG/PNG image, strip EXIF metadata, and return sanitized image bytes.
    Ensures user privacy and eliminates malicious payload injection in metadata.
    """
    image = Image.open(io.BytesIO(image_bytes))
    if image.format not in ("JPEG", "PNG"):
        raise ValueError("Invalid image format. Only JPEG and PNG are permitted.")

    # Re-save without EXIF metadata
    clean_buffer = io.BytesIO()
    image_data = list(image.getdata())
    clean_image = Image.new(image.mode, image.size)
    clean_image.putdata(image_data)
    clean_image.save(clean_buffer, format="JPEG" if image.format == "JPEG" else "PNG")
    return clean_buffer.getvalue()


def get_disease_advice(
    crop: str,
    predicted_label: str,
    confidence: float,
) -> DiseaseDiagnosisResponse:
    """
    Produce treatment advice for a detected disease.
    
    If confidence < 0.70 or label is unrecognized, strictly falls back to:
    'Not sure, please contact your nearest KVK'.
    """
    is_fallback = confidence < CONFIDENCE_THRESHOLD or predicted_label not in VERIFIED_DISEASE_KB

    if is_fallback:
        return DiseaseDiagnosisResponse(
            crop=crop,
            predicted_label="uncertain_or_unrecognized",
            confidence=confidence,
            model_version="baseline",
            is_fallback=True,
            treatment_advice=(
                "सटीक पहचान नहीं हो सकी (विश्वास स्तर 70% से कम है)। "
                "गलत कीटनाशक के प्रयोग से बचें और कृपया अपने निकटतम कृषि विज्ञान केंद्र (KVK) से संपर्क करें।"
            ),
            prevention_steps=["निकटतम KVK विशेषज्ञ को पौधे का ताजा नमूना दिखाएं।"],
            sources=[],
            disclaimer="सलाह केवल मार्गदर्शन हेतु है। विशिष्ट रासायनिक उपचार हेतु विशेषज्ञ परामर्श अनिवार्य है।",
        )

    info = VERIFIED_DISEASE_KB[predicted_label]
    citation = SourceCitation(
        doc_title=f"{crop} रोग प्रबंधन मार्गदर्शिका",
        source=info["source"],
        chunk_text=info["treatment"],
        relevance_score=confidence,
    )

    return DiseaseDiagnosisResponse(
        crop=crop,
        predicted_label=info["disease_name"],
        confidence=confidence,
        model_version="baseline",
        is_fallback=False,
        treatment_advice=info["treatment"],
        prevention_steps=info["prevention"],
        sources=[citation],
        disclaimer="सलाह केवल मार्गदर्शन हेतु है। छिड़काव करते समय सुरक्षा निर्देशों का पालन करें।",
    )
