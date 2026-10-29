"""Rule-based user intent classifier supporting Hindi and English agriculture queries."""

import re
from typing import Literal

IntentType = Literal["price", "yield", "weather", "disease", "general"]

# Hindi and English keywords for intent routing
INTENT_PATTERNS = {
    "price": re.compile(
        r"(भाव|मंडी|रेट|दाम|कीमत|बाजार|बिक्री|price|mandi|rate|cost|market|forecast|trend)",
        re.IGNORECASE,
    ),
    "yield": re.compile(
        r"(उपज|पैदावार|उत्पादन|अनुमान|क्विंटल|yield|production|productivity|harvest|output)",
        re.IGNORECASE,
    ),
    "weather": re.compile(
        r"(मौसम|बारिश|वर्षा|तापमान|आंधी|हवा|लू|पाला|सिंचाई|पानी|weather|rain|temperature|heatwave|frost|irrigation|wind)",
        re.IGNORECASE,
    ),
    "disease": re.compile(
        r"(रोग|बीमारी|कीट|कीड़ा|पत्ती|धब्बा|इल्ली|सुंडी|दवा|छिड़काव|स्प्रे|फंगस|सड़न|disease|pest|insect|fungus|blight|rot|caterpillar|spray|pesticide)",
        re.IGNORECASE,
    ),
}


def classify_intent(query: str) -> IntentType:
    """
    Classify query intent using lightweight, deterministic keyword rules.
    
    Returns one of: 'price', 'yield', 'weather', 'disease', 'general'.
    Fast, zero external model inference cost, 100% testable.
    """
    clean_query = query.strip()
    if not clean_query:
        return "general"

    # Prioritize specific technical domains before general queries
    for intent, pattern in INTENT_PATTERNS.items():
        if pattern.search(clean_query):
            return intent

    return "general"
