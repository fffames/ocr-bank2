"""Authentication service for user management and JWT tokens.

Updated: 2026-05-06 - Fixed bcrypt password length limit (72 bytes) and bcrypt 4.x compatibility
"""
from datetime import datetime, timedelta
from typing import Optional
import bcrypt  # Import bcrypt directly for version 4.x compatibility
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database.connection import get_db
from app.models.user import User
from app.schemas.user import TokenData

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _truncate_password(password: str) -> str:
    """Truncate password to 72 bytes (bcrypt limit) BEFORE hashing."""
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        return password_bytes[:72].decode('utf-8', errors='ignore')
    return password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    # Truncate BEFORE any bcrypt operations (required for bcrypt 4.x)
    truncated_password = _truncate_password(plain_password)

    # Use bcrypt directly for 4.x compatibility
    try:
        return bcrypt.checkpw(
            truncated_password.encode('utf-8'),
            hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
        )
    except Exception:
        # Fallback to string comparison if there are encoding issues
        return bcrypt.checkpw(truncated_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    # Truncate BEFORE any bcrypt operations (required for bcrypt 4.x)
    truncated_password = _truncate_password(password)

    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(truncated_password.encode('utf-8'), salt)

    # Return as string
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})

    # Encode JWT
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        token_data = TokenData(user_id=user_id)

    except JWTError:
        raise credentials_exception

    # Get user from database
    user = get_user_by_id(db, user_id=token_data.user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


def create_user(db: Session, email: str, password: str, name: Optional[str] = None, is_admin: bool = False) -> User:
    """Create a new user."""
    # Check if user already exists
    existing_user = get_user_by_email(db, email)
    if existing_user:
        raise ValueError(f"User with email {email} already exists")

    # Create new user
    hashed_password = get_password_hash(password)
    db_user = User(
        email=email,
        password_hash=hashed_password,
        name=name,
        is_admin=is_admin,
        is_active=True
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create default user settings
    from app.models.user_settings import UserSettings
    user_settings = UserSettings(
        user_id=db_user.id,
        user_name=name or email.split("@")[0],
        auto_classify=True,
        salary_day_of_month=1,
        salary_category="Salary"
    )
    db.add(user_settings)
    db.commit()

    return db_user