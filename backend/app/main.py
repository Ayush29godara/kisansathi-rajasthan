"""FastAPI main application entrypoint for KisanSathi Rajasthan."""

import json
import logging
import os
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.db import check_db_health
from app.schemas import HealthResponse
from routers import (
    profile,
    chat,
    diagnose,
    yield_router,
    price,
    weather,
    feedback,
    system,
)

# Configure structured logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("kisansathi")

app = FastAPI(
    title="KisanSathi Rajasthan API",
    description="AI-assisted decision-support platform for smallholder farmers in Rajasthan, India.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Strict CORS Middleware - NEVER allow wildcard '*' in production
logger.info("Configuring CORS with allowed origins: %s", settings.allowed_origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    """Structured request logging capturing request_id, client_ip, method, path, and latency_ms."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()

    response = await call_next(request)

    latency_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id

    log_entry = {
        "event": "http_request",
        "request_id": request_id,
        "client_ip": client_ip,
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "latency_ms": latency_ms,
    }
    logger.info("HTTP %s %s -> %s (%sms) [%s]", request.method, request.url.path, response.status_code, latency_ms, request_id, extra=log_entry)
    return response


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Public healthcheck probe for monitoring and Render zero-downtime deploys.
    Checks live database connectivity and reports server state.
    """
    db_connected = check_db_health()
    return HealthResponse(
        status="ok",
        version="0.1.0",
        environment=settings.ENVIRONMENT,
        database="connected" if db_connected else "disconnected",
    )


@app.get("/reference/districts", tags=["Reference"])
async def get_districts():
    """Return the official list of Rajasthan districts with agro-climatic zones."""
    ref_path = os.path.join(os.path.dirname(__file__), "..", "reference", "districts.json")
    with open(ref_path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/reference/crops", tags=["Reference"])
async def get_crops():
    """Return the list of major Rajasthan crops with Hindi and English names."""
    ref_path = os.path.join(os.path.dirname(__file__), "..", "reference", "crops.json")
    with open(ref_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Mount application routers
app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(diagnose.router)
app.include_router(yield_router.router)
app.include_router(price.router)
app.include_router(weather.router)
app.include_router(feedback.router)
app.include_router(system.router)
