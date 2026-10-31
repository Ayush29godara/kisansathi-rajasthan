"""In-memory sliding window rate limiter for protecting free-tier Render services."""

import time
import logging
from collections import defaultdict
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status

from app.config import get_settings

logger = logging.getLogger("kisansathi.rate_limiter")
settings = get_settings()


class SlidingWindowRateLimiter:
    """
    Sliding window in-memory rate limiter per IP/User.
    
    Safe for single uvicorn worker on Render free tier (512 MB RAM).
    """

    def __init__(self, times: int = 20, seconds: int = 60):
        self.times = times
        self.seconds = seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(self, key: str) -> bool:
        """Check if request exceeds rate limit; record timestamp if permitted."""
        now = time.time()
        window_start = now - self.seconds

        # Clean timestamps older than window
        timestamps = self._requests[key]
        self._requests[key] = [t for t in timestamps if t > window_start]

        if len(self._requests[key]) >= self.times:
            return True

        self._requests[key].append(now)
        return False

    def clear(self) -> None:
        """Reset state (useful for test suites)."""
        self._requests.clear()


# Global limiter instances for specific endpoints
chat_limiter = SlidingWindowRateLimiter(times=20, seconds=60)
diagnose_limiter = SlidingWindowRateLimiter(times=10, seconds=60)


async def check_chat_rate_limit(request: Request) -> None:
    """FastAPI dependency for /chat and /chat/voice rate limiting."""
    if settings.ENVIRONMENT == "test":
        return

    client_ip = request.client.host if request.client else "127.0.0.1"
    auth_header = request.headers.get("Authorization", "")
    # Use client IP or token prefix as rate limit bucket key
    key = auth_header[:30] if auth_header else client_ip

    if chat_limiter.is_rate_limited(key):
        logger.warning("Rate limit exceeded for chat endpoint by %s", client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="बहुत अधिक अनुरोध। कृपया 1 मिनट बाद पुनः प्रयास करें। (Too many chat requests. Please try again in 1 minute.)",
            headers={"Retry-After": "60"},
        )


async def check_diagnose_rate_limit(request: Request) -> None:
    """FastAPI dependency for /diagnose vision rate limiting."""
    if settings.ENVIRONMENT == "test":
        return

    client_ip = request.client.host if request.client else "127.0.0.1"
    auth_header = request.headers.get("Authorization", "")
    key = auth_header[:30] if auth_header else client_ip

    if diagnose_limiter.is_rate_limited(key):
        logger.warning("Rate limit exceeded for diagnose endpoint by %s", client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="बहुत अधिक रोग पहचान अनुरोध। कृपया 1 मिनट बाद पुनः प्रयास करें। (Too many diagnosis requests. Please try again in 1 minute.)",
            headers={"Retry-After": "60"},
        )
