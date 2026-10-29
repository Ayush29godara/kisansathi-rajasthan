"""Profile and farm management endpoints scoped strictly to the authenticated user."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.auth import get_current_user
from app.schemas import ProfileResponse, ProfileUpdate, FarmResponse, FarmCreate, FarmUpdate

router = APIRouter(prefix="", tags=["Profile & Farm"])


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieve profile for the authenticated farmer.
    Every query is scoped strictly to user['id'].
    """
    return ProfileResponse(
        user_id=user["id"],
        language="hi",
    )


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Update profile preferences (language, etc.) for the authenticated user."""
    return ProfileResponse(
        user_id=user["id"],
        language=profile_data.language or "hi",
    )


@router.get("/farms", response_model=Optional[FarmResponse])
async def get_farm(user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve farm details for the authenticated user."""
    # Scaffold baseline farm profile
    return FarmResponse(
        farm_id="mock-farm-id",
        user_id=user["id"],
        district="Jaipur",
        tehsil="Amber",
        crop="Mustard",
        land_hectare=2.5,
        irrigation="tubewell",
        sowing_date="2026-10-15",
    )


@router.post("/farms", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(
    farm_data: FarmCreate,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new farm profile linked to the authenticated user."""
    return FarmResponse(
        farm_id="farm-" + user["id"][:8],
        user_id=user["id"],
        **farm_data.model_dump(),
    )
