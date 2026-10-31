"""Profile and farm management endpoints scoped strictly to the authenticated user."""

import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.demo_store import (
    is_demo_user,
    get_demo_farm,
    update_demo_farm,
    get_demo_language,
    set_demo_language,
)
from app.models import ProfileModel, FarmModel
from app.schemas import (
    ProfileResponse,
    ProfileUpdate,
    FarmResponse,
    FarmCreate,
    FarmUpdate,
)

logger = logging.getLogger("kisansathi.profile")
router = APIRouter(prefix="", tags=["Profile & Farm"])


def _demo_profile_response(user_id: str) -> ProfileResponse:
    farm = get_demo_farm(user_id)
    return ProfileResponse(
        user_id=user_id,
        language=get_demo_language(user_id),
        farm=FarmResponse(**farm),
        created_at=farm["created_at"],
        updated_at=farm["updated_at"],
    )


def _farm_model_to_response(farm: Optional[FarmModel]) -> Optional[FarmResponse]:
    """Convert SQLAlchemy FarmModel instance to Pydantic FarmResponse schema."""
    if not farm:
        return None
    return FarmResponse(
        farm_id=str(farm.farm_id),
        user_id=str(farm.user_id),
        district=farm.district,
        tehsil=farm.tehsil,
        crop=farm.crop,
        land_hectare=float(farm.land_hectare),
        irrigation=farm.irrigation,
        sowing_date=farm.sowing_date,
        created_at=farm.created_at,
        updated_at=farm.updated_at,
    )


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    user: Dict[str, Any] = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """
    Retrieve user preferences and current farm profile for the authenticated user.
    Scoped strictly to auth.uid() = user['id'].
    """
    user_id = user["id"]

    # Demo farmers or serverless fallback without live Postgres use in-memory store
    if is_demo_user(user_id) or db is None:
        return _demo_profile_response(str(user_id))

    user_uuid = str(user_id)

    # Find or initialize user profile
    profile = db.query(ProfileModel).filter(ProfileModel.user_id == user_uuid).first()
    if not profile:
        profile = ProfileModel(user_id=user_uuid, language="hi")
        db.add(profile)
        db.commit()
        db.refresh(profile)

    # Find active farm profile
    farm = (
        db.query(FarmModel)
        .filter(FarmModel.user_id == user_uuid)
        .order_by(FarmModel.updated_at.desc())
        .first()
    )

    return ProfileResponse(
        user_id=str(profile.user_id),
        language=profile.language,
        farm=_farm_model_to_response(farm),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    payload: ProfileUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """
    Update profile preferences and/or farm attributes for the authenticated user.
    """
    user_id = user["id"]

    if is_demo_user(user_id) or db is None:
        set_demo_language(str(user_id), payload.language)
        if payload.farm is not None:
            update_demo_farm(str(user_id), payload.farm.model_dump(exclude_none=True))
        return _demo_profile_response(str(user_id))

    user_uuid = str(user_id)

    # 1. Update Profile
    profile = db.query(ProfileModel).filter(ProfileModel.user_id == user_uuid).first()
    if not profile:
        profile = ProfileModel(user_id=user_uuid, language=payload.language or "hi")
        db.add(profile)
    else:
        if payload.language is not None:
            profile.language = payload.language

    # 2. Update or create Farm if provided
    farm = (
        db.query(FarmModel)
        .filter(FarmModel.user_id == user_uuid)
        .order_by(FarmModel.updated_at.desc())
        .first()
    )

    if payload.farm is not None:
        f_data = payload.farm
        if farm:
            if f_data.district is not None:
                farm.district = f_data.district
            if f_data.tehsil is not None:
                farm.tehsil = f_data.tehsil
            if f_data.crop is not None:
                farm.crop = f_data.crop
            if f_data.land_hectare is not None:
                farm.land_hectare = f_data.land_hectare
            if f_data.irrigation is not None:
                farm.irrigation = f_data.irrigation
            if f_data.sowing_date is not None:
                farm.sowing_date = f_data.sowing_date
        else:
            # All fields must be present if creating new farm
            if not (f_data.district and f_data.tehsil and f_data.crop and f_data.land_hectare and f_data.irrigation and f_data.sowing_date):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="All farm fields are required when creating a farm profile",
                )
            farm = FarmModel(
                user_id=user_uuid,
                district=f_data.district,
                tehsil=f_data.tehsil,
                crop=f_data.crop,
                land_hectare=f_data.land_hectare,
                irrigation=f_data.irrigation,
                sowing_date=f_data.sowing_date,
            )
            db.add(farm)

    try:
        db.commit()
        db.refresh(profile)
        if farm:
            db.refresh(farm)
    except Exception as exc:
        db.rollback()
        logger.error("Failed to save profile for user %s: %s", user_uuid, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save farm details. Please try again.",
        )

    return ProfileResponse(
        user_id=str(profile.user_id),
        language=profile.language,
        farm=_farm_model_to_response(farm),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("/farms", response_model=Optional[FarmResponse])
async def get_farm(
    user: Dict[str, Any] = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """Retrieve active farm details for the authenticated user."""
    user_id = user["id"]

    if is_demo_user(user_id) or db is None:
        return FarmResponse(**get_demo_farm(str(user_id)))

    user_uuid = str(user_id)

    farm = (
        db.query(FarmModel)
        .filter(FarmModel.user_id == user_uuid)
        .order_by(FarmModel.updated_at.desc())
        .first()
    )
    if not farm:
        return None

    return _farm_model_to_response(farm)


@router.post("/farms", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(
    farm_data: FarmCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """Create a new farm profile linked to the authenticated user."""
    user_id = user["id"]

    if is_demo_user(user_id) or db is None:
        return FarmResponse(**update_demo_farm(str(user_id), farm_data.model_dump()))

    user_uuid = str(user_id)

    new_farm = FarmModel(
        user_id=user_uuid,
        district=farm_data.district,
        tehsil=farm_data.tehsil,
        crop=farm_data.crop,
        land_hectare=farm_data.land_hectare,
        irrigation=farm_data.irrigation,
        sowing_date=farm_data.sowing_date,
    )
    db.add(new_farm)
    db.commit()
    db.refresh(new_farm)

    return _farm_model_to_response(new_farm)
