"""Rule-based user intent classifier supporting Hindi and English agriculture queries."""

import re
from typing import Literal

IntentType = Literal["price", "yield", "weather", "disease", "general"]

# Hindi and English keywords for intent routing.
# Order matters: specific technical domains are checked first, then fallback to 'general'.
INTENT_PATTERNS = {
    "disease": re.compile(
        r"(रोग|बीमारी|कीट|कीड़ा|कीड़े|पत्त|धब्ब|रोली|उपचार|रोकथाम|नियंत्रण|लक्षण"
        r"|इल्ली|सुंडी|दवा|दवाई|छिड़काव|स्प्रे|फंगस|सड़न"
        r"|disease|pest|insect|fungus|blight|rot|rust|treatment|caterpillar|spray|pesticide)",
        re.IGNORECASE,
    ),
    "price": re.compile(
        r"(भाव|मंडी|रेट|दाम|कीमत|बाजार|बिक्री|price|mandi|cost|market|forecast|trend|\bmarket\s+rate|\bmandi\s+rate)",
        re.IGNORECASE,
    ),
    "yield": re.compile(
        r"(उपज|पैदावार|उत्पादन|अनुमान|क्विंटल|yield|production|productivity|harvest|output)",
        re.IGNORECASE,
    ),
    "weather": re.compile(
        r"(मौसम|बारिश|वर्षा|तापमान|आंधी|हवा|लू|पाला|सिंचाई|पानी"
        r"|weather|rain|temperature|heatwave|frost|irrigation|wind)",
        re.IGNORECASE,
    ),
}


def classify_intent(query: str) -> IntentType:
    """
    Classify query intent using lightweight, deterministic keyword rules.

    Priority order: disease > price > yield > weather > general.
    Fast, zero external model inference cost, 100% testable.

    Args:
        query: The user's question string.

    Returns:
        One of: 'disease', 'price', 'yield', 'weather', 'general'.
    """
    clean_query = query.strip()
    if not clean_query:
        return "general"

    # Prioritize specific technical domains before conversational / general
    for intent, pattern in INTENT_PATTERNS.items():
        if pattern.search(clean_query):
            return intent

    return "general"
