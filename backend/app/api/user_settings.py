"""User settings API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
import json

from app.database.connection import get_db
from app.models.user_settings import UserSettings
from app.models.user import User
from app.services.auth_service import get_current_active_user

router = APIRouter()


class UserSettingsUpdate(BaseModel):
    user_name: Optional[str] = None
    name_variations: Optional[List[str]] = None
    auto_classify: Optional[bool] = None


@router.get("/settings")
async def get_user_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user settings for the current user (creates default if not exists).

    Returns:
        User settings with user_name, name_variations, auto_classify
    """
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()

    if not settings:
        # Create default settings for current user
        settings = UserSettings(
            user_id=current_user.id,
            user_name=current_user.name or current_user.email.split("@")[0],
            user_name_variations="[]",
            auto_classify=True,
            salary_day_of_month=1,
            salary_category="Salary"
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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user settings for the current user.

    Args:
        settings_update: User settings to update
        current_user: Authenticated user

    Returns:
        Updated user settings
    """
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()

    if not settings:
        # Create if doesn't exist
        settings = UserSettings(
            user_id=current_user.id,
            user_name=current_user.name or current_user.email.split("@")[0],
            user_name_variations="[]",
            auto_classify=True
        )
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
