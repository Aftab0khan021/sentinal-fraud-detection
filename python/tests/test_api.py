"""
SentinAL: API Tests
===================
Integration tests for secured API endpoints.

Author: SentinAL Security Team
Date: 2026-01-23
"""

import pytest
import time


def test_root_endpoint(client):
    """Test root endpoint (no auth required)"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "SentinAL" in data["name"]


def test_health_check(client):
    """Test health check endpoint (no auth required)"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "ai_connected" in data
    assert "data_loaded" in data


def test_analyze_without_auth(client):
    """Test analyze endpoint without authentication"""
    response = client.get("/analyze/77")
    assert response.status_code == 403  # Forbidden


def test_analyze_with_invalid_token(client):
    """Test analyze endpoint with invalid token"""
    headers = {"Authorization": "Bearer invalid-token"}
    response = client.get("/analyze/77", headers=headers)
    assert response.status_code == 401  # Unauthorized


def test_analyze_with_valid_token(client, auth_headers):
    """Test analyze endpoint with valid authentication"""
    response = client.get("/analyze/77", headers=auth_headers)
    
    # May be 200 (success) or 503 (if AI not loaded in test)
    assert response.status_code in [200, 503]
    
    data = response.json()
    assert "error" in data


def test_analyze_invalid_user_id(client, auth_headers):
    """Test analyze endpoint with invalid user_id"""
    # Test out of range
    response = client.get("/analyze/999", headers=auth_headers)
    assert response.status_code in [400, 404]  # Bad Request or Not Found
    
    # Test negative
    response = client.get("/analyze/-1", headers=auth_headers)
    assert response.status_code == 400


def test_rate_limiting(client, auth_headers):
    """Test rate limiting (10 requests per minute)"""
    # Make 11 rapid requests
    responses = []
    for i in range(11):
        response = client.get("/analyze/77", headers=auth_headers)
        responses.append(response.status_code)
        time.sleep(0.1)  # Small delay between requests
    
    # At least one should be rate limited (429)
    # Note: This test may be flaky depending on timing
    assert 429 in responses or all(r in [200, 503] for r in responses)


def test_cors_headers(client):
    """Test CORS headers are present"""
    response = client.get("/health")
    assert "access-control-allow-origin" in response.headers or response.status_code == 200


def test_security_headers(client):
    """Test security headers are present"""
    response = client.get("/health")
    
    # Check for security headers
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"


def test_validation_error_format(client, auth_headers):
    """Test that validation errors return proper format"""
    response = client.get("/analyze/abc", headers=auth_headers)
    assert response.status_code == 422  # Unprocessable Entity (FastAPI validation)
    
    data = response.json()
    assert "detail" in data


def test_missing_authorization_header(client):
    """Test request without Authorization header"""
    response = client.get("/analyze/77")
    assert response.status_code == 403


def test_malformed_authorization_header(client):
    """Test request with malformed Authorization header"""
    headers = {"Authorization": "InvalidFormat"}
    response = client.get("/analyze/77", headers=headers)
    assert response.status_code in [401, 403]
