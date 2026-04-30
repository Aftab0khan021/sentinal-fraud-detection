"""
SentinAL: Test Configuration
=============================
Pytest fixtures and configuration for API testing.

Author: SentinAL Security Team
Date: 2026-01-23
"""

import os
import pytest
from fastapi.testclient import TestClient
from datetime import timedelta
import sys
from pathlib import Path

# ── Set required env vars BEFORE importing any app modules ─────────────────
# api.py raises RuntimeError in production if JWT_SECRET_KEY is the default,
# and auth.py / audit_logger.py emit warnings. Set test values here so the
# entire test suite works without a real .env file.
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("JWT_REFRESH_SECRET_KEY", "test-refresh-key-for-pytest-only")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("REDIS_ENABLED", "false")   # no Redis needed during tests
os.environ.setdefault("DEMO_USER_HASH", "")        # triggers fallback hash — acceptable in tests
os.environ.setdefault("ADMIN_USER_HASH", "")
# ───────────────────────────────────────────────────────────────────────────

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api import app
from auth import create_access_token


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Generate a valid JWT token for testing"""
    return create_access_token(
        data={"sub": "test_user", "email": "test@sentinal.ai", "username": "Test User"},
        expires_delta=timedelta(minutes=30),
    )


@pytest.fixture
def expired_token():
    """Generate an expired JWT token for testing"""
    return create_access_token(
        data={"sub": "test_user"}, expires_delta=timedelta(minutes=-1)  # Already expired
    )


@pytest.fixture
def auth_headers(valid_token):
    """Authorization headers with valid token"""
    return {"Authorization": f"Bearer {valid_token}"}


@pytest.fixture
def mock_fraud_scores():
    """Mock fraud scores data"""
    return {
        "fraud_probability": [0.1] * 50 + [0.9] * 50,  # 50 normal, 50 fraud
        "true_label": [0] * 50 + [1] * 50,
        "predicted_label": [0] * 50 + [1] * 50,
    }
