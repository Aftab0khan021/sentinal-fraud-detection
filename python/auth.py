"""
SentinAL: Authentication Module
================================
JWT-based authentication for API endpoints.

Author: SentinAL Security Team
Date: 2026-01-23
"""

import os
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import secrets

import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from dotenv import load_dotenv
from passlib.context import CryptContext

# Load environment variables
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION")
REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", "CHANGE_THIS_REFRESH_KEY_IN_PRODUCTION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))

# Security scheme
security = HTTPBearer()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token blacklist (in-memory for now, should use Redis in production)
token_blacklist = set()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing claims to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
        
    Example:
        >>> token = create_access_token({"sub": "user123"})
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials) -> str:
    """
    Verify JWT token from Authorization header.
    
    Args:
        credentials: HTTP Bearer credentials containing the token
        
    Returns:
        User ID (subject) from the token
        
    Raises:
        HTTPException: If token is invalid, expired, or missing
        
    Example:
        Use as FastAPI dependency:
        >>> @app.get("/protected")
        >>> async def protected_route(user_id: str = Depends(verify_token)):
        >>>     return {"user": user_id}
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:  # Fixed exception class for pyjwt
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency to get current authenticated user.
    
    Args:
        credentials: Automatically injected by FastAPI from Authorization header
        
    Returns:
        User ID string
        
    Example:
        >>> from fastapi import Depends
        >>> @app.get("/me")
        >>> async def read_users_me(current_user: str = Depends(get_current_user)):
        >>>     return {"user_id": current_user}
    """
    return verify_token(credentials)


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with longer expiration.
    
    Args:
        data: Dictionary containing claims to encode in the token
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_refresh_token(token: str) -> str:
    """
    Verify a refresh token and return the user ID.
    
    Args:
        token: Refresh token string
        
    Returns:
        User ID from the token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if token is blacklisted
        if token in token_blacklist:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token"
        )


def blacklist_token(token: str):
    """
    Add a token to the blacklist (logout).
    In production, this should use Redis with TTL.
    
    Args:
        token: Token to blacklist
    """
    token_blacklist.add(token)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password for storing.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


# Demo user database (in production, use a real database)
DEMO_USERS = {
    "demo@sentinal.ai": {
        "id": "demo_user_001",
        "email": "demo@sentinal.ai",
        "username": "Demo Analyst",
        "hashed_password": get_password_hash("demo123"),
    },
    "admin@sentinal.ai": {
        "id": "admin_user_001",
        "email": "admin@sentinal.ai",
        "username": "Admin User",
        "hashed_password": get_password_hash("admin123"),
    },
}


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """
    Authenticate a user by email and password.
    
    Args:
        email: User email
        password: Plain text password
        
    Returns:
        User dict if authentication successful, None otherwise
    """
    user = DEMO_USERS.get(email)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


# Warn if using default secret keys
if SECRET_KEY == "CHANGE_THIS_IN_PRODUCTION":
    import warnings
    warnings.warn(
        "Using default JWT_SECRET_KEY! This is INSECURE. "
        "Set JWT_SECRET_KEY in your .env file before deploying to production.",
        UserWarning
    )

if REFRESH_SECRET_KEY == "CHANGE_THIS_REFRESH_KEY_IN_PRODUCTION":
    import warnings
    warnings.warn(
        "Using default JWT_REFRESH_SECRET_KEY! This is INSECURE. "
        "Set JWT_REFRESH_SECRET_KEY in your .env file before deploying to production.",
        UserWarning
    )
