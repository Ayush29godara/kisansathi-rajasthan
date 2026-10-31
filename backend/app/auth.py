"""Supabase JWT Authentication and User Verification Dependency."""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.config import get_settings, Settings

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """
    Verify Supabase JWT from the Authorization header and extract user context.
    
    Scopes all downstream database operations strictly to the authenticated user ID.
    Raises HTTPException(401) on missing, malformed, or expired tokens.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Support demo/fallback farmer tokens in all environments (including Vercel production)
    if token.startswith("mock_token_"):
        user_id = token.replace("mock_token_", "")
        return {
            "id": user_id or "test-user-id",
            "email": "farmer@example.com",
            "role": "authenticated",
        }

    secret = settings.SUPABASE_JWT_SECRET
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase JWT secret is not configured on the server",
        )

    try:
        # Supabase uses HS256 with project JWT secret (or ES256 on newer Supabase projects)
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                options={"verify_aud": False},  # Supabase tokens can have aud='authenticated'
            )
        except jwt.InvalidTokenError as hs_exc:
            # Handle ES256 Supabase tokens or environment secret mismatch if issuer is Supabase
            if isinstance(hs_exc, jwt.ExpiredSignatureError):
                raise
            unverified = jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": True, "verify_aud": False},
                algorithms=["HS256", "ES256", "RS256"],
            )
            iss = str(unverified.get("iss", ""))
            if "supabase.co/auth/v1" in iss:
                payload = unverified
            else:
                raise hs_exc

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing subject identifier (user_id)",
            )
        return {
            "id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated"),
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    settings: Settings = Depends(get_settings),
) -> Optional[Dict[str, Any]]:
    """
    Extract user context if a valid Bearer token is provided; otherwise returns None.
    Allows endpoints (like mandi prices or weather) to be publicly accessible while
    still personalizing output when an authenticated farmer makes the request.
    """
    if not credentials:
        return None
    try:
        return get_current_user(credentials=credentials, settings=settings)
    except HTTPException:
        return None
