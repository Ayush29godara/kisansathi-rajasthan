"""FastAPI main application entrypoint for KisanSathi Rajasthan."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.schemas import HealthResponse
from routers import (
    profile,
    chat,
    diagnose,
    yield_router,
    price,
    weather,
    feedback,
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


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Public healthcheck probe for monitoring and Render zero-downtime deploys."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        environment=settings.ENVIRONMENT,
    )


# Mount application routers
app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(diagnose.router)
app.include_router(yield_router.router)
app.include_router(price.router)
app.include_router(weather.router)
app.include_router(feedback.router)
