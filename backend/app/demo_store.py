"""In-memory profile store for demo farmer sessions.

Demo users (ids starting with ``demo-``) do not exist in Supabase ``auth.users`` so they
cannot be persisted to the database (foreign-key constraints). Their farm profile is kept
here so that edits made on the Farm Details page are honoured consistently by the
advisor chat, yield outlook and every other endpoint.
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, Optional

DEMO_PREFIX = "demo-"


def is_demo_user(user_id: str) -> bool:
    return str(user_id).startswith(DEMO_PREFIX)


def _default_farm(user_id: str) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "farm_id": "farm-demo-jaipur",
        "user_id": user_id,
        "district": "Jaipur",
        "tehsil": "Amber",
        "crop": "Mustard",
        "land_hectare": 2.5,
        "irrigation": "tubewell",
        "sowing_date": date(2026, 10, 15),
        "created_at": now,
        "updated_at": now,
    }


_demo_farms: Dict[str, Dict[str, Any]] = {}
_demo_languages: Dict[str, str] = {}


def get_demo_farm(user_id: str) -> Dict[str, Any]:
    if user_id not in _demo_farms:
        _demo_farms[user_id] = _default_farm(user_id)
    return _demo_farms[user_id]


def update_demo_farm(user_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
    farm = get_demo_farm(user_id)
    for key, value in changes.items():
        if value is not None and key in farm:
            farm[key] = value
    farm["updated_at"] = datetime.now(timezone.utc)
    return farm


def get_demo_language(user_id: str) -> str:
    return _demo_languages.get(user_id, "hi")


def set_demo_language(user_id: str, language: Optional[str]) -> None:
    if language:
        _demo_languages[user_id] = language


def reset_demo_store() -> None:
    """Clear all demo state (used by tests)."""
    _demo_farms.clear()
    _demo_languages.clear()
