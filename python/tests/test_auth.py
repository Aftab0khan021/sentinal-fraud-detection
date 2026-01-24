"""
SentinAL: Authentication Tests
===============================
Test JWT token generation and verification.

Author: SentinAL Security Team
Date: 2026-01-23
"""

import pytest
from datetime import timedelta
import jwt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import create_access_token, verify_token, SECRET_KEY, ALGORITHM
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


def test_create_access_token():
    """Test JWT token creation"""
    token = create_access_token(data={"sub": "test_user"})
    assert token is not None
    assert isinstance(token, str)
    
    # Decode and verify
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "test_user"
    assert "exp" in payload


def test_create_token_with_custom_expiration():
    """Test token creation with custom expiration"""
    token = create_access_token(
        data={"sub": "test_user"},
        expires_delta=timedelta(minutes=60)
    )
    
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "test_user"


def test_verify_valid_token():
    """Test verification of valid token"""
    token = create_access_token(data={"sub": "test_user"})
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token
    )
    
    user_id = verify_token(credentials)
    assert user_id == "test_user"


def test_verify_expired_token():
    """Test verification of expired token"""
    token = create_access_token(
        data={"sub": "test_user"},
        expires_delta=timedelta(minutes=-1)  # Already expired
    )
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token
    )
    
    with pytest.raises(HTTPException) as exc_info:
        verify_token(credentials)
    
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_verify_invalid_token():
    """Test verification of invalid token"""
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid.token.here"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        verify_token(credentials)
    
    assert exc_info.value.status_code == 401


def test_verify_token_without_subject():
    """Test token without 'sub' claim"""
    token = jwt.encode({"data": "no_subject"}, SECRET_KEY, algorithm=ALGORITHM)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token
    )
    
    with pytest.raises(HTTPException) as exc_info:
        verify_token(credentials)
    
    assert exc_info.value.status_code == 401
