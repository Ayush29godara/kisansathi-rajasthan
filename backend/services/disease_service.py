"""Crop disease advice and high-accuracy vision diagnosis service.

Grounded in official Package of Practices (POP) from:
- Agriculture University Kota
- Sri Karan Narendra Agriculture University (SKNAU), Jobner
- Swami Keshwanand Rajasthan Agricultural University (SKRAU), Bikaner
- ICAR - Central Arid Zone Research Institute (CAZRI), Jodhpur
- ICAR - Directorate of Rapeseed-Mustard Research (DRMR), Bharatpur
- ICAR - Indian Institute of Wheat and Barley Research (IIWBR), Karnal
"""

import os
import io
import base64
import json
import uuid
import logging
from typing import Dict, Any, Tuple, Optional, List
from PIL import Image
from sqlalchemy.orm import Session
import httpx

from app.config import get_settings
from app.schemas import DiseaseDiagnosisResponse, SourceCitation

logger = logging.getLogger("kisansathi.disease_service")
settings = get_settings()

CONFIDENCE_THRESHOLD = 0.70


def get_gemini_endpoint() -> str:
    model = getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite") or "gemini-3.5-flash-lite"
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


GEMINI_GENERATE_ENDPOINT = get_gemini_endpoint()

# Curated reference treatments from Rajasthan Agriculture Universities & ICAR institutes
VERIFIED_DISEASE_KB: Dict[str, Dict[str, Any]] = {
    # ---------------- Mustard Diseases ----------------
    "mustard_white_rust": {
        "disease_name": "Mustard White Rust (सरसों सफेद रोली)",
        "crop": "Mustard",
        "treatment": "मैनकोजेब (Mancozeb 75% WP) 2 ग्राम प्रति लीटर पानी या रिडोमिल एम.जेड. (Metalaxyl + Mancozeb) 1.5 ग्राम प्रति लीटर पानी की दर से छिड़काव करें। पहला लक्षण दिखते ही 15 दिन के अंतर पर दूसरा छिड़काव करें।",
        "prevention": [
            "प्रमाणित एवं थीरम/कार्बेन्डाजिम से उपचारित बीज ही बोएं।",
            "फसल चक्र अपनाएं एवं खेत की ग्रीष्मकालीन गहरी जुताई करें।",
            "खेत में अतिरिक्त जलभराव न होने दें।"
        ],
        "source": "Package of Practices for Rabi Crops, Agriculture University Kota",
    },
    "mustard_alternaria_blight": {
        "disease_name": "Mustard Alternaria Blight (सरसों झुलसा रोग)",
        "crop": "Mustard",
        "treatment": "मैनकोजेब (Mancozeb 75% WP) 2 ग्राम प्रति लीटर अथवा कॉपर ऑक्सीक्लोराइड 2.5 ग्राम प्रति लीटर पानी का छिड़काव 15 दिन के अंतराल पर 2 बार करें।",
        "prevention": [
            "समय पर बुवाई (15 से 25 अक्टूबर) करें ताकि फूल आने के समय अधिक आर्द्रता से बचाव हो सके।",
            "प्रमाणित रोगरोधी किस्मों (जैसे गिरराज, आर.एच.-725) का चयन करें।"
        ],
        "source": "Directorate of Rapeseed-Mustard Research (DRMR), Bharatpur",
    },
    "mustard_aphids": {
        "disease_name": "Mustard Aphids / Chepa (सरसों मोयला / चेपा कीट)",
        "crop": "Mustard",
        "treatment": "आर्थिक क्षति स्तर (ETL: 20-25% पौधों पर चेपा) होने पर डाईमेथोएट (30 EC) 1 मिली प्रति लीटर अथवा इमिडाक्लोप्रिड (17.8 SL) 1 मिली प्रति 3 लीटर पानी का छिड़काव करें।",
        "prevention": [
            "खेत में पीले चिपचिपे ट्रेप (Yellow Sticky Traps) लगाएं।",
            "मित्र कीटों (लेडीबर्ड बीटल) के संरक्षण हेतु आवश्यकतानुसार ही छिड़काव करें।"
        ],
        "source": "ICAR-DRMR Technical Bulletin, Bharatpur",
    },
    "mustard_armyworm": {
        "disease_name": "Mustard Armyworm (सरसों सैनिक कीट / सूंडी)",
        "crop": "Mustard",
        "treatment": "क्विनालफॉस (25% EC) 1.5 मिली/लीटर या क्लोरपायरीफॉस (20% EC) 2 मिली/लीटर पानी का छिड़काव शाम के समय करें जब सूंडी सक्रिय होती है।",
        "prevention": [
            "खेत के चारों ओर गहरी खाई खोदें ताकि सूंडी का प्रसार रुके।",
            "प्रारंभिक अवस्था में कीटों के अंडे व सुंडियों को इकट्ठा कर नष्ट करें।"
        ],
        "source": "ICAR-DRMR Advisory, Bharatpur",
    },
    "mustard_leaf_miner": {
        "disease_name": "Mustard Leaf Miner (सरसों पत्ती सुरंगक कीट)",
        "crop": "Mustard",
        "treatment": "नीम का तेल (5 मिली/लीटर) या डाईमेथोएट (30 EC) 1 मिली प्रति लीटर पानी का छिड़काव करें।",
        "prevention": [
            "संक्रमित पत्तियों को तोड़कर नष्ट करें।",
            "संतुलित उर्वरक का प्रयोग करें।"
        ],
        "source": "Package of Practices, Agriculture University Kota",
    },
    "mustard_healthy": {
        "disease_name": "Healthy Mustard (सरसों स्वस्थ पत्ती)",
        "crop": "Mustard",
        "treatment": "पत्ती पूर्णतः स्वस्थ है। किसी रासायनिक कीटनाशक अथवा फफूंदनाशी के प्रयोग की आवश्यकता नहीं है।",
        "prevention": [
            "संतुलित उर्वरक (NPK + गंधक) का प्रयोग जारी रखें।",
            "नियमित रूप से फसल का निरीक्षण करते रहें।"
        ],
        "source": "KisanSathi Agronomy Reference, AU Kota",
    },

    # ---------------- Tomato Diseases ----------------
    "tomato_early_blight": {
        "disease_name": "Tomato Early Blight (टमाटर अगेती झुलसा)",
        "crop": "Tomato",
        "treatment": "मैनकोजेब (Mancozeb 75% WP) 2.5 ग्राम/लीटर या क्लोरोथैलोनिल (Chlorothalonil 75% WP) 2 ग्राम/लीटर पानी का छिड़काव 10-12 दिन के अंतराल पर करें।",
        "prevention": [
            "पत्तियों पर संकेंद्रित छल्लेदार (target-like) भूरे धब्बे दिखने पर तुरंत निचली संक्रमित पत्तियों को हटाएं।",
            "ड्रिप सिंचाई का उपयोग करें ताकि पत्तियां गीली न रहें।",
            "टमाटर के बाद टमाटर न लगाएं; 2 वर्ष का फसल चक्र अपनाएं।"
        ],
        "source": "Package of Practices for Vegetable Crops, Agriculture University Kota",
    },
    "tomato_late_blight": {
        "disease_name": "Tomato Late Blight (टमाटर पछेती झुलसा)",
        "crop": "Tomato",
        "treatment": "रिडोमिल एम.जेड. (Metalaxyl 8% + Mancozeb 64% WP) 2.5 ग्राम प्रति लीटर या साइमोक्सानिल + मैनकोजेब 2 ग्राम प्रति लीटर पानी का छिड़काव करें।",
        "prevention": [
            "बादल छाए रहने एवं 80% से अधिक आर्द्रता में सुरक्षात्मक छिड़काव करें।",
            "रोगग्रस्त पौधों को उखाड़कर नष्ट करें।"
        ],
        "source": "SKNAU Jobner Horticulture Advisory",
    },
    "tomato_bacterial_spot": {
        "disease_name": "Tomato Bacterial Spot (टमाटर जीवाणु धब्बा रोग)",
        "crop": "Tomato",
        "treatment": "स्ट्रेप्टोसाइक्लिन 1 ग्राम + कॉपर ऑक्सीक्लोराइड 50% WP (25 ग्राम) प्रति 10 लीटर पानी में घोलकर 12-15 दिन के अंतर पर छिड़काव करें।",
        "prevention": [
            "गर्म पानी (50°C पर 25 मिनट) से बीज उपचार करें।",
            "संक्रमित फसल अवशेषों को खेत से बाहर निकालकर जला दें।"
        ],
        "source": "Package of Practices, SKNAU Jobner",
    },
    "tomato_leaf_mold": {
        "disease_name": "Tomato Leaf Mold (टमाटर पत्ती फफूंद)",
        "crop": "Tomato",
        "treatment": "कार्बेन्डाजिम 12% + मैनकोजेब 63% WP (साफ) 2 ग्राम/लीटर पानी का छिड़काव करें।",
        "prevention": [
            "पौधों के बीच हवा का आवागमन सुनिश्चित करने हेतु उचित दूरी रखें।",
            "ग्रीनहाउस/पॉलीहाउस में वेंटिलेशन बेहतर रखें।"
        ],
        "source": "Agriculture University Kota",
    },
    "tomato_spider_mites": {
        "disease_name": "Tomato Spider Mites (टमाटर लाल मकड़ी / माइट्स)",
        "crop": "Tomato",
        "treatment": "प्रोपारगाइट (57% EC) 2 मिली/लीटर या फेनाजाक्विन (10% EC) 1.5 मिली/लीटर पानी का छिड़काव पत्तियों की निचली सतह पर अच्छी तरह करें।",
        "prevention": [
            "खेत में नमी बनाए रखें; शुष्क व गर्म मौसम में माइट्स तेजी से फैलते हैं।",
            "नीम का तेल 5 मिली/लीटर का छिड़काव प्रारंभिक अवस्था में करें।"
        ],
        "source": "ICAR-CAZRI Vegetable Advisory, Jodhpur",
    },
    "tomato_mosaic_virus": {
        "disease_name": "Tomato Mosaic Virus - ToMV (टमाटर मोजेक वायरस)",
        "crop": "Tomato",
        "treatment": "वायरस का कोई सीधा रासायनिक उपचार नहीं है। संवाहक कीटों (माहू/थ्रिप्स) के नियंत्रण हेतु इमिडाक्लोप्रिड 1 मिली/3 लीटर पानी का छिड़काव करें।",
        "prevention": [
            "संक्रमित मोजेक पत्ती वाले पौधों को तुरंत उखाड़कर गहरे गड्ढे में दबाएं।",
            "रोगमुक्त प्रमाणित नर्सरी से ही पौधे लगाएं।",
            "हाथों और कृषि औजारों को साबुन या ट्राइसोडियम फॉस्फेट से साफ करें।"
        ],
        "source": "SKNAU Jobner Advisory Bulletin",
    },
    "tomato_septoria_leaf_spot": {
        "disease_name": "Tomato Septoria Leaf Spot (टमाटर सेप्टोरिया पत्ती धब्बा)",
        "crop": "Tomato",
        "treatment": "मैनकोजेब 2.5 ग्राम प्रति लीटर या कॉपर हाइड्रॉक्साइड 2 ग्राम प्रति लीटर पानी का छिड़काव करें।",
        "prevention": [
            "निचली पुरानी पत्तियों को जो जमीन को छू रही हों, हटा दें।",
            "मल्चिंग का उपयोग करें ताकि मिट्टी से फफूंद के बीजाणु पत्तियों पर न उछलें।"
        ],
        "source": "Agriculture University Kota",
    },
    "tomato_yellow_leaf_curl": {
        "disease_name": "Tomato Leaf Curl Virus (टमाटर पर्ण कुंचन वायरस / माथा बंधना)",
        "crop": "Tomato",
        "treatment": "संवाहक सफेद मक्खी (Whitefly) के नियंत्रण हेतु डायफेंथियूरॉन (50% WP) 1.25 ग्राम/लीटर या थायोमेथोक्सम (25% WG) 0.5 ग्राम/लीटर पानी का छिड़काव करें।",
        "prevention": [
            "नर्सरी को 40-मेष कीट-रोधी जाली में उगाएं।",
            "खेत में प्रति बीघा 8-10 पीले चिपचिपे ट्रेप (Yellow Sticky Traps) लगाएं।",
            "संक्रमित बौने व मुड़े हुए पौधों को तुरंत नष्ट करें।"
        ],
        "source": "ICAR-CAZRI & AU Kota Vegetable Guidelines",
    },
    "tomato_target_spot": {
        "disease_name": "Tomato Target Spot (टमाटर टारगेट स्पॉट)",
        "crop": "Tomato",
        "treatment": "एजोक्सीस्ट्रोबिन (23% SC) 1 मिली प्रति लीटर या मैनकोजेब 2.5 ग्राम प्रति लीटर पानी का छिड़काव करें।",
        "prevention": [
            "फसल को अधिक घना न लगाएं।",
            "अतिरिक्त नाइट्रोजन देने से बचें।"
        ],
        "source": "Agriculture University Kota",
    },
    "tomato_healthy": {
        "disease_name": "Healthy Tomato (स्वस्थ टमाटर)",
        "crop": "Tomato",
        "treatment": "पौधा एवं पत्ती पूर्णतः स्वस्थ है। किसी रासायनिक दवा की आवश्यकता नहीं है।",
        "prevention": [
            "संतुलित पोषण (NPK + सूक्ष्म पोषक तत्व) देते रहें।",
            "नियमित सिंचाई बनाए रखें।"
        ],
        "source": "KisanSathi Agronomy Reference",
    },

    # ---------------- Bajra (Pearl Millet) Diseases ----------------
    "bajra_blast": {
        "disease_name": "Bajra Blast / Pyricularia Leaf Spot (बाजरा पत्ती धब्बा रोग)",
        "crop": "Bajra",
        "treatment": "जैनेब (Zineb 75% WP) अथवा मैनकोजेब 2 ग्राम प्रति लीटर पानी का छिड़काव लक्षण दिखते ही करें।",
        "prevention": [
            "रोगरोधी संकर किस्में (जैसे MPMH-17, HHB-67 सुधरी) लगाएं।",
            "नाइट्रोजन का अत्यधिक असंतुलित प्रयोग न करें; पोटाश का अनुशंसित प्रयोग करें।"
        ],
        "source": "ICAR-CAZRI Technical Bulletin, Jodhpur",
    },
    "bajra_downy_mildew": {
        "disease_name": "Bajra Downy Mildew / Green Ear (बाजरा जोगिया / हरित बाली)",
        "crop": "Bajra",
        "treatment": "रोगग्रस्त पौधों को उखाड़कर तुरंत नष्ट करें। रिडोमिल 2 ग्राम/लीटर का सुरक्षात्मक छिड़काव बुवाई के 20-25 दिन बाद करें।",
        "prevention": [
            "बीज को मेटालैक्सिल (एप्रन 35 एसडी) 6 ग्राम प्रति किग्रा बीज से उपचारित करें।",
            "रोगरोधी संकर किस्मों का ही चयन करें।"
        ],
        "source": "ICAR-CAZRI Technical Advisory, Jodhpur",
    },
    "bajra_smut": {
        "disease_name": "Bajra Smut / Ergot (बाजरा अरगट / कंडवा)",
        "crop": "Bajra",
        "treatment": "फूल आने के समय कार्बेन्डाजिम (50% WP) 1 ग्राम प्रति लीटर पानी का छिड़काव करें।",
        "prevention": [
            "20% नमक के घोल में बीज डालकर तैरते हुए हल्के रोगग्रस्त बीज अलग कर नष्ट करें।",
            "गहरी ग्रीष्मकालीन जुताई करें ताकि बीजाणु मिट्टी में दब जाएं।"
        ],
        "source": "Rajasthan Agriculture University, Bikaner",
    },
    "bajra_rust": {
        "disease_name": "Bajra Rust (बाजरा रतुआ रोग)",
        "crop": "Bajra",
        "treatment": "मैनकोजेब 2 ग्राम प्रति लीटर अथवा प्रोपिकोनाजोल 1 मिली प्रति लीटर पानी का छिड़काव करें।",
        "prevention": [
            "समय पर बुवाई करें।",
            "फसल अवशेषों को नष्ट करें।"
        ],
        "source": "ICAR-CAZRI Jodhpur",
    },
    "bajra_healthy": {
        "disease_name": "Healthy Bajra (बाजरा स्वस्थ पत्ती)",
        "crop": "Bajra",
        "treatment": "बाजरे की पत्ती स्वस्थ है। किसी रासायनिक छिड़काव की आवश्यकता नहीं है।",
        "prevention": [
            "समय पर निराई-गुड़ाई कर खरपतवार नियंत्रित रखें।"
        ],
        "source": "KisanSathi Agronomy Reference",
    },

    # ---------------- Wheat Diseases ----------------
    "wheat_yellow_rust": {
        "disease_name": "Wheat Yellow / Stripe Rust (गेहूं पीला रतुआ)",
        "crop": "Wheat",
        "treatment": "प्रोपिकोनाजोल (Propiconazole 25% EC) 1 मिली प्रति लीटर पानी की दर से 500 लीटर पानी प्रति हेक्टेयर में घोल बनाकर छिड़कें। दूसरा छिड़काव 15 दिन बाद आवश्यकतानुसार करें।",
        "prevention": [
            "राजस्थान के सिंचित क्षेत्रों में पीला रतुआ रोधी किस्में (जैसे डीबीडब्ल्यू-187, डीबीडब्ल्यू-303, राज-4037) बोएं।",
            "पत्तियों पर पीले पाउडर की धारियां दिखते ही तुरंत कृषि पर्यवेक्षक को सूचित करें।"
        ],
        "source": "ICAR-IIWBR Technical Guidelines, Karnal",
    },
    "wheat_brown_rust": {
        "disease_name": "Wheat Brown / Leaf Rust (गेहूं भूरा रतुआ)",
        "crop": "Wheat",
        "treatment": "मैनकोजेब 2 ग्राम प्रति लीटर अथवा प्रोपिकोनाजोल 1 मिली प्रति लीटर पानी का छिड़काव करें।",
        "prevention": [
            "समय पर बुवाई (नवंबर प्रथम पखवाड़ा) करें; अत्यधिक देर से बुवाई से बचें।"
        ],
        "source": "ICAR-IIWBR Technical Guidelines, Karnal",
    },
    "wheat_septoria": {
        "disease_name": "Wheat Septoria Leaf Blotch (गेहूं सेप्टोरिया पर्ण झुलसा)",
        "crop": "Wheat",
        "treatment": "प्रोपिकोनाजोल 25 EC 1 मिली/लीटर या टेबुकोनाजोल 1 मिली/लीटर पानी का छिड़काव करें।",
        "prevention": [
            "प्रमाणित बीज का प्रयोग करें एवं फसल चक्र अपनाएं।"
        ],
        "source": "ICAR-IIWBR Guidelines",
    },
    "wheat_loose_smut": {
        "disease_name": "Wheat Loose Smut (गेहूं अनावृत कंडवा / कांगियारी)",
        "crop": "Wheat",
        "treatment": "खड़ी फसल में बाली काली होने पर रासायनिक दवा काम नहीं करती। रोगग्रस्त काली बालियों को पन्नी से ढककर सावधानीपूर्वक उखाड़ें और जला दें।",
        "prevention": [
            "बुवाई से पूर्व बीज को कार्बोक्सिन 37.5% + थीरम 37.5% (विटावैक्स) 2.5 ग्राम/किग्रा बीज से उपचारित करें।",
            "मई-जून में सोलर हीट ट्रीटमेंट (बीज को धूप में सुखाना) अपनाएं।"
        ],
        "source": "ICAR-IIWBR Karnal",
    },
    "wheat_karnal_bunt": {
        "disease_name": "Wheat Karnal Bunt (गेहूं करनाल बंट)",
        "crop": "Wheat",
        "treatment": "बाली निकलने के समय प्रोपिकोनाजोल 25 EC 1 मिली/लीटर पानी का सुरक्षात्मक छिड़काव करें।",
        "prevention": [
            "प्रमाणित निरोगी बीज का ही प्रयोग करें।",
            "सड़ी गोबर की खाद एवं ट्राइकोडर्मा का प्रयोग करें।"
        ],
        "source": "ICAR-IIWBR Technical Guidelines, Karnal",
    },
    "wheat_healthy": {
        "disease_name": "Healthy Wheat (गेहूं स्वस्थ पत्ती)",
        "crop": "Wheat",
        "treatment": "पत्ती स्वस्थ है। किसी कीटनाशक की आवश्यकता नहीं है।",
        "prevention": [
            "सी.आर.आई. और कल्ले फूटने की अवस्था में क्रांतिक सिंचाई सुनिश्चित करें।"
        ],
        "source": "KisanSathi Agronomy Reference",
    },

    # ---------------- Soybean & Guar & Gram ----------------
    "soybean_yellow_mosaic": {
        "disease_name": "Soybean Yellow Mosaic Virus (सोयाबीन पीला मोजेक)",
        "crop": "Soybean",
        "treatment": "वाहक सफेद मक्खी (Whitefly) के नियंत्रण हेतु थायोमेथोक्सम (25% WG) 0.5 ग्राम/लीटर या इमिडाक्लोप्रिड 1 मिली/3 लीटर पानी का छिड़काव करें।",
        "prevention": [
            "रोगग्रस्त पौधों को शुरुआत में ही उखाड़कर नष्ट करें।",
            "सफेद मक्खी की रोकथाम हेतु पीले चिपचिपे ट्रेप लगाएं।"
        ],
        "source": "ICAR-IISR Indore & Agriculture University Kota",
    },
    "soybean_leaf_spot": {
        "disease_name": "Soybean Leaf Spot (सोयाबीन पर्ण चित्ती)",
        "crop": "Soybean",
        "treatment": "टेबुकोनाजोल + ट्राइफ्लॉक्सीस्ट्रोबिन 0.75 ग्राम प्रति लीटर पानी का छिड़काव करें।",
        "prevention": [
            "फसल चक्र अपनाएं एवं पोटाश का अनुशंसित प्रयोग करें।"
        ],
        "source": "Agriculture University Kota",
    },
    "soybean_healthy": {
        "disease_name": "Healthy Soybean (सोयाबीन स्वस्थ पत्ती)",
        "crop": "Soybean",
        "treatment": "पौधा पूर्णतः स्वस्थ है। किसी रासायनिक दवा की आवश्यकता नहीं है।",
        "prevention": [
            "जल निकासी की उचित व्यवस्था रखें।"
        ],
        "source": "KisanSathi Agronomy Reference",
    },
    "guar_bacterial_blight": {
        "disease_name": "Guar Bacterial Blight (ग्वार जीवाणु झुलसा)",
        "crop": "Guar",
        "treatment": "स्ट्रेप्टोसाइक्लिन 1 ग्राम + कॉपर ऑक्सीक्लोराइड 20 ग्राम प्रति 10 लीटर पानी में मिलाकर छिड़काव करें।",
        "prevention": [
            "बीज को स्ट्रेप्टोसाइक्लिन 500 पीपीएम घोल में 2 घंटे भिगोकर उपचारित करें।",
            "रोगरोधी किस्में (जैसे आर.जी.सी.-936, आर.जी.सी.-1003) लगाएं।"
        ],
        "source": "SKNAU Jobner / ICAR-CAZRI Jodhpur",
    },
    "guar_healthy": {
        "disease_name": "Healthy Guar (ग्वार स्वस्थ पत्ती)",
        "crop": "Guar",
        "treatment": "पत्ती स्वस्थ है। किसी दवा की आवश्यकता नहीं है।",
        "prevention": [
            "सामान्य खरपतवार नियंत्रण बनाए रखें।"
        ],
        "source": "KisanSathi Agronomy Reference",
    },
    "gram_wilt": {
        "disease_name": "Gram / Chickpea Fusarium Wilt (चना उकठा / विल्ट रोग)",
        "crop": "Gram",
        "treatment": "खड़ी फसल में विल्ट आने पर रासायनिक नियंत्रण प्रभावी नहीं होता। रोगग्रस्त पौधों को उखाड़कर जलाएं।",
        "prevention": [
            "ट्राइकोडर्मा विरिडी 5-6 ग्राम प्रति किग्रा बीज से बीज उपचार करें।",
            "गहरी बुवाई से बचें तथा रोगरोधी किस्में (जैसे जीएनजी-1581, जीएनजी-1958) अपनाएं।"
        ],
        "source": "SKNAU Jobner Pulse Advisory",
    },
    "gram_pod_borer": {
        "disease_name": "Gram Pod Borer (चना फली छेदक / इल्ली)",
        "crop": "Gram",
        "treatment": "इमामेक्टिन बेंजोएट (5% SG) 0.4 ग्राम/लीटर या क्लोरएंट्रानिलिप्रोल (18.5% SC) 0.3 मिली/लीटर पानी का छिड़काव करें।",
        "prevention": [
            "खेत में 'टी' (T) आकार की खूंटियां पक्षियों के बैठने हेतु लगाएं।",
            "फेरोमोन ट्रेप 4-5 प्रति बीघा लगाएं।"
        ],
        "source": "Package of Practices, SKNAU Jobner",
    },
    "gram_healthy": {
        "disease_name": "Healthy Gram (स्वस्थ चना)",
        "crop": "Gram",
        "treatment": "पत्ती व पौधा स्वस्थ है। किसी कीटनाशक की आवश्यकता नहीं है।",
        "prevention": [
            "उचित जल प्रबंधन बनाए रखें।"
        ],
        "source": "KisanSathi Agronomy Reference",
    },
}

# Fuzzy synonym normalization mapping
DISEASE_KEY_SYNONYMS: Dict[str, str] = {
    # Mustard
    "white_rust": "mustard_white_rust",
    "mustard_white_rust": "mustard_white_rust",
    "albugo_candida": "mustard_white_rust",
    "white_pustules": "mustard_white_rust",
    "alternaria_blight": "mustard_alternaria_blight",
    "mustard_blight": "mustard_alternaria_blight",
    "mustard_alternaria_blight": "mustard_alternaria_blight",
    "blight": "mustard_alternaria_blight",
    "aphid": "mustard_aphids",
    "aphids": "mustard_aphids",
    "mustard_aphid": "mustard_aphids",
    "mustard_aphids": "mustard_aphids",
    "chepa": "mustard_aphids",
    "moyla": "mustard_aphids",
    "armyworm": "mustard_armyworm",
    "mustard_armyworm": "mustard_armyworm",
    "leaf_miner": "mustard_leaf_miner",
    "mustard_leaf_miner": "mustard_leaf_miner",
    "mustard_healthy": "mustard_healthy",
    # Tomato
    "early_blight": "tomato_early_blight",
    "tomato_early_blight": "tomato_early_blight",
    "late_blight": "tomato_late_blight",
    "tomato_late_blight": "tomato_late_blight",
    "bacterial_spot": "tomato_bacterial_spot",
    "tomato_bacterial_spot": "tomato_bacterial_spot",
    "leaf_mold": "tomato_leaf_mold",
    "tomato_leaf_mold": "tomato_leaf_mold",
    "spider_mites": "tomato_spider_mites",
    "two_spotted_spider_mite": "tomato_spider_mites",
    "tomato_spider_mites": "tomato_spider_mites",
    "mosaic_virus": "tomato_mosaic_virus",
    "tomato_mosaic_virus": "tomato_mosaic_virus",
    "septoria": "tomato_septoria_leaf_spot",
    "septoria_leaf_spot": "tomato_septoria_leaf_spot",
    "tomato_septoria": "tomato_septoria_leaf_spot",
    "tomato_septoria_leaf_spot": "tomato_septoria_leaf_spot",
    "yellow_leaf_curl": "tomato_yellow_leaf_curl",
    "leaf_curl": "tomato_yellow_leaf_curl",
    "tomato_yellow_leaf_curl": "tomato_yellow_leaf_curl",
    "target_spot": "tomato_target_spot",
    "tomato_target_spot": "tomato_target_spot",
    "tomato_healthy": "tomato_healthy",
    # Wheat
    "yellow_rust": "wheat_yellow_rust",
    "stripe_rust": "wheat_yellow_rust",
    "wheat_yellow_rust": "wheat_yellow_rust",
    "brown_rust": "wheat_brown_rust",
    "leaf_rust": "wheat_brown_rust",
    "wheat_brown_rust": "wheat_brown_rust",
    "karnal_bunt": "wheat_karnal_bunt",
    "wheat_karnal_bunt": "wheat_karnal_bunt",
    "loose_smut": "wheat_loose_smut",
    "wheat_loose_smut": "wheat_loose_smut",
    "wheat_septoria": "wheat_septoria",
    "wheat_healthy": "wheat_healthy",
    # Bajra
    "blast": "bajra_blast",
    "bajra_blast": "bajra_blast",
    "downy_mildew": "bajra_downy_mildew",
    "green_ear": "bajra_downy_mildew",
    "jogiya": "bajra_downy_mildew",
    "bajra_downy_mildew": "bajra_downy_mildew",
    "smut": "bajra_smut",
    "ergot": "bajra_smut",
    "bajra_smut": "bajra_smut",
    "bajra_rust": "bajra_rust",
    "bajra_healthy": "bajra_healthy",
    # Soybean
    "yellow_mosaic": "soybean_yellow_mosaic",
    "soybean_yellow_mosaic": "soybean_yellow_mosaic",
    "soybean_leaf_spot": "soybean_leaf_spot",
    "soybean_healthy": "soybean_healthy",
    # Guar
    "bacterial_blight": "guar_bacterial_blight",
    "guar_bacterial_blight": "guar_bacterial_blight",
    "guar_healthy": "guar_healthy",
    # Gram
    "wilt": "gram_wilt",
    "fusarium_wilt": "gram_wilt",
    "gram_wilt": "gram_wilt",
    "pod_borer": "gram_pod_borer",
    "gram_pod_borer": "gram_pod_borer",
    "gram_healthy": "gram_healthy",
}


def normalize_disease_label(label: str, crop: str = "") -> str:
    """Normalize raw or shortened model labels into verified KB keys."""
    raw = label.lower().strip().replace("-", "_").replace(" ", "_")

    # Direct synonym match
    if raw in DISEASE_KEY_SYNONYMS:
        return DISEASE_KEY_SYNONYMS[raw]

    # Crop prefix check
    crop_prefix = crop.lower().strip()
    if crop_prefix:
        combined = f"{crop_prefix}_{raw}"
        if combined in DISEASE_KEY_SYNONYMS:
            return DISEASE_KEY_SYNONYMS[combined]
        if combined in VERIFIED_DISEASE_KB:
            return combined

    if raw in VERIFIED_DISEASE_KB:
        return raw

    # Substring search in KB
    for k in VERIFIED_DISEASE_KB.keys():
        if raw in k or k in raw:
            return k

    return raw


def sanitize_and_strip_exif(image_bytes: bytes) -> bytes:
    """Validate JPEG/PNG image, strip EXIF metadata, and return sanitized image bytes."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as exc:
        raise ValueError(f"Corrupt or invalid image file: {str(exc)}")

    if image.format not in ("JPEG", "PNG"):
        raise ValueError(f"Invalid image format '{image.format}'. Only JPEG and PNG are permitted.")

    clean_buffer = io.BytesIO()
    clean_image = Image.new(image.mode, image.size)
    clean_image.paste(image)
    clean_image.save(clean_buffer, format="JPEG" if image.format == "JPEG" else "PNG", quality=90)
    return clean_buffer.getvalue()


async def classify_image_with_vision(
    image_bytes: bytes,
    crop: str,
) -> Tuple[str, float, str]:
    """
    High-accuracy server-side plant pathology vision analysis using Gemini Vision.
    
    Returns: (predicted_label, confidence, symptom_notes)
    """
    clean_bytes = sanitize_and_strip_exif(image_bytes)
    crop_clean = crop.strip()
    crop_lower = crop_clean.lower()

    # In test environment with mock keys
    if (
        settings.ENVIRONMENT in ("test", "development")
        and (not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.startswith("mock_"))
    ):
        if "mustard" in crop_lower:
            return "mustard_white_rust", 0.85, "Visual symptoms consistent with White Rust pustules."
        elif "bajra" in crop_lower:
            return "bajra_blast", 0.82, "Spindle-shaped brown lesions observed."
        elif "wheat" in crop_lower:
            return "wheat_yellow_rust", 0.78, "Linear yellow pustule streaks noted."
        elif "tomato" in crop_lower:
            return "tomato_early_blight", 0.88, "Concentric target-like rings with chlorotic halo observed."
        else:
            return "uncertain_or_unrecognized", 0.52, "Low visual distinctiveness, recommend KVK expert."

    # Production Gemini Vision API Call
    b64_img = base64.b64encode(clean_bytes).decode("utf-8")
    mime_type = "image/png" if clean_bytes.startswith(b"\x89PNG") else "image/jpeg"

    # Provide all verified keys, prioritizing the selected crop first
    all_keys = list(VERIFIED_DISEASE_KB.keys())
    if crop_lower and crop_lower not in ("auto-detect", "all", "", "any"):
        crop_keys = [k for k in all_keys if crop_lower in k]
        other_keys = [k for k in all_keys if crop_lower not in k]
        relevant_keys = crop_keys + other_keys
        crop_hint = f"The farmer selected crop '{crop_clean}' (prefer {crop_clean} keys if the leaf matches {crop_clean}, or identify the true crop if clearly different)."
    else:
        relevant_keys = all_keys
        crop_hint = "Automatically detect the crop and its exact foliar condition."

    candidate_str = ", ".join(relevant_keys)

    system_instruction = (
        "You are a senior agricultural plant pathologist and entomologist specializing in crops grown in Rajasthan, India. "
        f"{crop_hint} "
        "Carefully examine the leaf or plant photo for exact foliar symptoms (white rust pustules, yellow stripe rust, brown rust, concentric early blight rings, water-soaked late blight lesions, bacterial spots, septoria spots, leaf curl, spider mites, powdery/downy mildew, smut, armyworm/leaf miner damage, or healthy green tissue). "
        f"Select the single best matching disease_key from these verified keys: [{candidate_str}]. "
        "If the leaf is healthy and free of disease, choose the '<crop>_healthy' key with confidence >= 0.85. "
        "If the image is clearly a diseased crop leaf, set confidence between 0.78 and 0.96 based on symptom clarity. "
        "If the image is blurry, irrelevant, or not a plant/crop, set disease_key to 'uncertain_or_unrecognized' and confidence < 0.55. "
        "Return STRICT JSON only with this schema:\n"
        "{\n"
        '  "disease_key": string,\n'
        '  "confidence": float between 0.0 and 1.0,\n'
        '  "detected_crop": string,\n'
        '  "notes": string describing visible symptoms\n'
        "}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": system_instruction},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_img,
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }

    url = get_gemini_endpoint()
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={"x-goog-api-key": settings.GEMINI_API_KEY},
            )
            if resp.status_code == 200:
                data = resp.json()
                text_out = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if text_out.startswith("```"):
                    text_out = text_out.strip("`").removeprefix("json").strip()
                parsed = json.loads(text_out)

                raw_key = str(parsed.get("disease_key", "uncertain_or_unrecognized"))
                conf = float(parsed.get("confidence", 0.55))
                notes = str(parsed.get("notes", ""))
                detected_crop = str(parsed.get("detected_crop", crop_clean))

                # Normalize through dictionary mapping
                normalized_key = normalize_disease_label(raw_key, crop=detected_crop or crop_clean)
                return normalized_key, conf, notes
            else:
                logger.warning("Gemini Vision HTTP %d: %s", resp.status_code, resp.text)
    except Exception as exc:
        logger.error("Gemini Vision classification failed: %s", exc)

    return "uncertain_or_unrecognized", 0.50, "Server vision analysis inconclusive."


def get_disease_advice_from_kb(
    crop: str,
    predicted_label: str,
    confidence: float,
    db: Optional[Session] = None,
) -> DiseaseDiagnosisResponse:
    """
    Produce treatment advice strictly grounded in verified KB / ICAR sources.
    
    Rule: If confidence < 0.70 or disease unrecognized, strictly returns:
    'Not sure, please contact your nearest KVK'.
    """
    norm_label = normalize_disease_label(predicted_label, crop=crop)
    is_fallback = confidence < CONFIDENCE_THRESHOLD or norm_label not in VERIFIED_DISEASE_KB

    if is_fallback:
        return DiseaseDiagnosisResponse(
            crop=crop,
            predicted_label="अस्पष्ट लक्षण (Low Confidence)",
            confidence=round(confidence, 2),
            model_version="gemini-vision" if confidence < CONFIDENCE_THRESHOLD else "baseline",
            is_fallback=True,
            treatment_advice=(
                "सटीक पहचान नहीं हो सकी (विश्वास स्तर 70% से कम है)। "
                "गलत कीटनाशक अथवा फफूंदनाशी के अनावश्यक प्रयोग से बचें। "
                "कृपया पौधे का ताजा पत्ता लेकर अपने निकटतम कृषि विज्ञान केंद्र (KVK) अथवा कृषि पर्यवेक्षक से संपर्क करें।"
            ),
            prevention_steps=[
                "पत्ती का ताजा नमूना प्लास्टिक थैली में रखकर निकटतम KVK वैज्ञानिक को दिखाएं।",
                "बिना आधिकारिक सलाह के कोई रासायनिक छिड़काव न करें।"
            ],
            sources=[],
            disclaimer="सलाह केवल मार्गदर्शन हेतु है। विशिष्ट रासायनिक उपचार हेतु कृषि विज्ञान केंद्र (KVK) से परामर्श अनिवार्य है।",
        )

    info = VERIFIED_DISEASE_KB[norm_label]
    effective_crop = info.get("crop") or (crop if crop not in ("Auto-Detect", "All", "") else "Crop")
    citation = SourceCitation(
        doc_title=f"{effective_crop} रोग प्रबंधन संदर्शिका",
        source=info["source"],
        chunk_text=info["treatment"],
        relevance_score=round(confidence, 2),
    )

    return DiseaseDiagnosisResponse(
        crop=effective_crop,
        predicted_label=info["disease_name"],
        confidence=round(confidence, 2),
        model_version="gemini-vision",
        is_fallback=False,
        treatment_advice=info["treatment"],
        prevention_steps=info["prevention"],
        sources=[citation],
        disclaimer="सलाह केवल मार्गदर्शन हेतु है। रासायनिक छिड़काव करते समय सुरक्षा निर्देशों का पालन करें।",
    )


async def store_photo_if_opted_in(
    image_bytes: bytes,
    user_id: str,
    crop: str,
    opt_in: bool,
) -> Optional[str]:
    """
    Opt-in photo storage in private Supabase bucket 'disease-photos'.
    
    1. EXIF is strictly stripped.
    2. Bucket is private.
    3. Stored only when opt_in=True; returns signed URL or private object key.
    """
    if not opt_in:
        return None

    clean_bytes = sanitize_and_strip_exif(image_bytes)
    file_id = f"{uuid.uuid4().hex[:12]}.jpg"
    storage_path = f"{user_id}/{crop.lower()}_{file_id}"

    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
        try:
            upload_url = f"{settings.SUPABASE_URL}/storage/v1/object/disease-photos/{storage_path}"
            headers = {
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "image/jpeg",
                "x-upsert": "true",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(upload_url, content=clean_bytes, headers=headers)
                if res.status_code in (200, 201):
                    sign_url = f"{settings.SUPABASE_URL}/storage/v1/object/sign/disease-photos/{storage_path}"
                    sign_res = await client.post(sign_url, json={"expiresIn": 3600}, headers=headers)
                    if sign_res.status_code == 200:
                        signed_data = sign_res.json()
                        return f"{settings.SUPABASE_URL}/storage/v1{signed_data.get('signedURL')}"
                    return f"disease-photos/{storage_path}"
        except Exception as exc:
            logger.warning("Supabase storage upload failed: %s", exc)

    return f"disease-photos/{storage_path}"
