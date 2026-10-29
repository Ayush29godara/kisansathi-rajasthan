"""Unit tests for rule-based intent classification."""

import pytest
from services.intent import classify_intent


@pytest.mark.parametrize(
    "query, expected_intent",
    [
        ("कोटा मंडी में सरसों का क्या भाव चल रहा है?", "price"),
        ("What is the mandi price of mustard in Alwar?", "price"),
        ("जयपुर जिले में बाजरे की पैदावार कितनी हो सकती है?", "yield"),
        ("Estimate wheat production and yield per hectare", "yield"),
        ("अगले 3 दिनों में बारिश होगी क्या?", "weather"),
        ("When is the next irrigation schedule for wheat?", "weather"),
        ("सरसों के पत्तों पर सफेद धब्बे (सफेद रोली) का उपचार क्या है?", "disease"),
        ("What pesticide or spray should I use for fungal blight?", "disease"),
        ("नमस्ते, आप क्या-क्या जानकारी दे सकते हैं?", "general"),
        ("", "general"),
    ],
)
def test_classify_intent(query: str, expected_intent: str):
    """Ensure bilingual queries are correctly mapped to their respective intents."""
    assert classify_intent(query) == expected_intent
