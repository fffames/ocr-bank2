"""Admin API endpoints for user management.
Only accessible by users with is_admin=True.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database.connection import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserRegister, AdminStatusUpdate, PasswordReset
from app.services.auth_service import (
    get_current_active_user,
    get_password_hash,
    authenticate_user,
    create_user
)

router = APIRouter()


async def get_current_admin(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> User:
    """Verify current user is an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only).

    Returns:
        List of all users with their details
    """
    users = db.query(User).all()
    return users


@router.post("/users", response_model=UserResponse)
async def create_new_user(
    user_data: UserRegister,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new user (admin only).

    Args:
        user_data: User registration data
        admin: Current admin user

    Returns:
        Created user details
    """
    try:
        # Check if email already exists
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

        # Create user (can be admin or regular user)
        user = create_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
            name=user_data.name,
            is_admin=False  # New users are regular users by default
        )

        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a user (admin only).

    Args:
        user_id: ID of user to delete
        admin: Current admin user

    Returns:
        Success message
    """
    # Prevent deleting yourself
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Delete related records manually (in case cascade isn't set up)
    try:
        from app.models.user_settings import UserSettings
        from app.models.receipt import Receipt

        # Delete user settings
        db.query(UserSettings).filter(UserSettings.user_id == user_id).delete()

        # Delete receipts
        db.query(Receipt).filter(Receipt.user_id == user_id).delete()

        # Finally delete the user
        db.delete(user)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )

    return {"message": f"User {user.email} deleted successfully"}


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password_data: PasswordReset,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Reset a user's password (admin only).

    Args:
        user_id: ID of user
        password_data: New password data
        admin: Current admin user

    Returns:
        Success message
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update password
    user.password_hash = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": f"Password reset for user {user.email}"}


@router.put("/users/{user_id}/admin")
async def toggle_admin_status(
    user_id: int,
    status_data: AdminStatusUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Toggle admin status of a user (admin only).

    Args:
        user_id: ID of user
        status_data: New admin status data
        admin: Current admin user

    Returns:
        Success message
    """
    # Prevent removing your own admin status
    if user_id == admin.id and not status_data.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin status"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update admin status
    user.is_admin = status_data.is_admin
    db.commit()

    status_text = "admin" if status_data.is_admin else "regular user"
    return {"message": f"User {user.email} is now a {status_text}"}
