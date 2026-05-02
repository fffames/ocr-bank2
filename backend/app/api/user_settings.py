"""User settings API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
import json

from app.database.connection import get_db
from app.models.user_settings import UserSettings

router = APIRouter()


class UserSettingsUpdate(BaseModel):
    user_name: Optional[str] = None
    name_variations: Optional[List[str]] = None
    auto_classify: Optional[bool] = None


@router.get("/settings")
async def get_user_settings(db: Session = Depends(get_db)):
    """
    Get user settings (creates default if not exists).

    Returns:
        User settings with user_name, name_variations, auto_classify
    """
    settings = db.query(UserSettings).first()

    if not settings:
        # Create default settings
        settings = UserSettings(
            user_name="",
            user_name_variations="[]",
            auto_classify=True
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return {
        "user_name": settings.user_name or "",
        "name_variations": json.loads(settings.user_name_variations) if settings.user_name_variations else [],
        "auto_classify": settings.auto_classify
    }


@router.put("/settings")
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    db: Session = Depends(get_db)
):
    """
    Update user settings.

    Args:
        settings_update: User settings to update

    Returns:
        Updated user settings
    """
    settings = db.query(UserSettings).first()

    if not settings:
        # Create if doesn't exist
        settings = UserSettings()
        db.add(settings)

    if settings_update.user_name is not None:
        settings.user_name = settings_update.user_name

    if settings_update.name_variations is not None:
        settings.user_name_variations = json.dumps(settings_update.name_variations, ensure_ascii=False)

    if settings_update.auto_classify is not None:
        settings.auto_classify = settings_update.auto_classify

    db.commit()
    db.refresh(settings)

    return {
        "user_name": settings.user_name or "",
        "name_variations": json.loads(settings.user_name_variations) if settings.user_name_variations else [],
        "auto_classify": settings.auto_classify
    }
