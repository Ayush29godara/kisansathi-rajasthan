"""Unit and integration tests for Advisor Chat endpoints."""

import io
from fastapi.testclient import TestClient
from app.db import SessionLocal
from app.models import MessageModel


def test_chat_unauthenticated_fails(client: TestClient):
    """POST /chat without bearer token must return 401 Unauthorized."""
    response = client.post("/chat", json={"question": "सरसों में सफेद रोली का इलाज क्या है?"})
    assert response.status_code == 401


def test_chat_empty_question_fails(client: TestClient, auth_headers: dict):
    """POST /chat with empty question must fail validation (HTTP 422)."""
    response = client.post(
        "/chat",
        json={"question": ""},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_chat_authenticated_succeeds(client: TestClient, auth_headers: dict):
    """POST /chat with valid token returns grounded ChatResponse with citations."""
    response = client.post(
        "/chat",
        json={
            "question": "सरसों में सफेद रोली रोग का क्या उपाय है?",
            "language": "hi",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["question"] == "सरसों में सफेद रोली रोग का क्या उपाय है?"
    assert data["intent"] == "disease"
    assert "answer" in data and len(data["answer"]) > 0
    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) > 0
    assert data["sources"][0]["doc_title"]
    assert "disclaimer" in data
    assert data["model_version"] == "gemini-1.5-flash"


def test_chat_english_language_query_succeeds(client: TestClient, auth_headers: dict):
    """POST /chat with English language query succeeds and preserves language preference."""
    response = client.post(
        "/chat",
        json={
            "question": "What is the recommended seed rate for mustard per hectare?",
            "language": "en",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "general"
    assert len(data["sources"]) > 0


def test_chat_message_saved_in_database(client: TestClient, auth_headers: dict):
    """Ensure completed chat exchanges are persisted to the messages table."""
    question = "गेहूं में पहली सिंचाई कब करें?"
    response = client.post(
        "/chat",
        json={"question": question, "language": "hi"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    msg_id = response.json()["id"]
    assert msg_id is not None

    # Query DB to ensure record was written
    if SessionLocal:
        db = SessionLocal()
        try:
            record = db.query(MessageModel).filter(MessageModel.id == msg_id).first()
            assert record is not None
            assert record.question == question
            assert record.intent == "weather"
        finally:
            db.close()


def test_chat_voice_invalid_mimetype_fails(client: TestClient, auth_headers: dict):
    """POST /chat/voice with non-audio file must return 400 Bad Request."""
    fake_txt_file = io.BytesIO(b"this is not audio")
    response = client.post(
        "/chat/voice",
        files={"audio": ("test.txt", fake_txt_file, "text/plain")},
        data={"language": "hi"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "valid audio recording" in response.json()["detail"]


def test_chat_voice_valid_audio_succeeds(client: TestClient, auth_headers: dict):
    """POST /chat/voice with valid audio file and transcript returns ChatResponse."""
    fake_wav_file = io.BytesIO(b"RIFF....WAVEfmt ....data....")
    response = client.post(
        "/chat/voice",
        files={"audio": ("speech.wav", fake_wav_file, "audio/wav")},
        data={
            "transcript": "कोटा मंडी में सरसों का भाव क्या है?",
            "language": "hi",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "price"
    assert data["question"] == "कोटा मंडी में सरसों का भाव क्या है?"
    assert len(data["sources"]) > 0


def test_chat_tomato_yellowing_query_succeeds(client: TestClient, auth_headers: dict):
    """Ensure specific tomato disease query returns grounded advice and citations."""
    response = client.post(
        "/chat",
        json={"question": "my tomato is turning yellow", "language": "en"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["sources"]) > 0
    assert "answer" in data and len(data["answer"]) > 0


def test_chat_wheat_yellow_spots_query_succeeds(client: TestClient, auth_headers: dict):
    """Ensure wheat yellow spots query returns grounded advice and citations."""
    response = client.post(
        "/chat",
        json={"question": "my wheat has some yellow spots on it", "language": "en"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["sources"]) > 0
    assert "answer" in data and len(data["answer"]) > 0


def test_chat_demo_farmer_history_succeeds(client: TestClient):
    """Ensure demo farmer can chat and retrieve history without database errors."""
    demo_headers = {"Authorization": "Bearer mock_token_demo-farmer-jaipur"}
    res1 = client.post(
        "/chat",
        json={"question": "टमाटर में पीले पत्ते की समस्या", "language": "hi"},
        headers=demo_headers,
    )
    assert res1.status_code == 200

    res2 = client.get("/history", headers=demo_headers)
    assert res2.status_code == 200
    history = res2.json()
    assert isinstance(history, list)
    assert len(history) > 0
    assert history[0]["question"] == "टमाटर में पीले पत्ते की समस्या"

