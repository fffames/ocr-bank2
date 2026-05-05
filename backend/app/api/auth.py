"""Authentication API endpoints for user registration, login, and user management."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database.connection import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserResponse, Token, PasswordChange
from app.services.auth_service import (
    authenticate_user,
    create_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    verify_password
)
from app.config import settings

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user.

    - **email**: User email address (must be unique)
    - **password**: User password (min 6 characters)
    - **name**: User's display name (optional)
    """
    try:
        # Create user
        user = create_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
            name=user_data.name,
            is_admin=False  # Regular users are not admins
        )
        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email and password.

    Returns:
        - **access_token**: JWT token for authenticated requests
        - **token_type**: Type of token (bearer)
        - **user**: User information

    Use the access_token in the Authorization header:
    `Authorization: Bearer <access_token>`
    """
    # Authenticate user
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information.

    Requires authentication token in Authorization header.
    """
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.

    - **old_password**: Current password
    - **new_password**: New password (min 6 characters)
    """
    # Verify old password
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout_user():
    """
    Logout user.

    Note: In JWT-based auth, logout is handled client-side by deleting the token.
    This endpoint is provided for future token blacklisting functionality.
    """
    return {"message": "Logout successful. Please delete your token on the client side."}