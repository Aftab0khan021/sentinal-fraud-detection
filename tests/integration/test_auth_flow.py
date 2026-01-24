"""
Integration tests for authentication flow.
Tests the complete authentication workflow from login to logout.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from api import app
from auth import create_access_token, create_refresh_token


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestAuthenticationFlow:
    """Test complete authentication workflow"""

    def test_login_success(self, client):
        """Test successful login"""
        response = client.post(
            "/api/auth/login",
            params={"email": "demo@sentinal.ai", "password": "demo123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["email"] == "demo@sentinal.ai"

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/auth/login",
            params={"email": "demo@sentinal.ai", "password": "wrongpassword"}
        )
        
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post(
            "/api/auth/login",
            params={"email": "nonexistent@example.com", "password": "password"}
        )
        
        assert response.status_code == 401

    def test_refresh_token_success(self, client):
        """Test successful token refresh"""
        # First login
        login_response = client.post(
            "/api/auth/login",
            params={"email": "demo@sentinal.ai", "password": "demo123"}
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = client.post(
            "/api/auth/refresh",
            params={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self, client):
        """Test token refresh with invalid token"""
        response = client.post(
            "/api/auth/refresh",
            params={"refresh_token": "invalid-token"}
        )
        
        assert response.status_code == 401

    def test_logout_success(self, client):
        """Test successful logout"""
        # First login
        login_response = client.post(
            "/api/auth/login",
            params={"email": "demo@sentinal.ai", "password": "demo123"}
        )
        access_token = login_response.json()["access_token"]
        
        # Logout
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        assert "message" in response.json()

    def test_logout_without_token(self, client):
        """Test logout without authentication"""
        response = client.post("/api/auth/logout")
        
        assert response.status_code == 403  # Forbidden

    def test_protected_endpoint_with_valid_token(self, client):
        """Test accessing protected endpoint with valid token"""
        # Login
        login_response = client.post(
            "/api/auth/login",
            params={"email": "demo@sentinal.ai", "password": "demo123"}
        )
        access_token = login_response.json()["access_token"]
        
        # Access protected endpoint
        response = client.get(
            "/api/graph",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Should succeed (or fail with 503 if data not loaded, but not 401)
        assert response.status_code in [200, 503]

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/graph")
        
        assert response.status_code == 403

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token"""
        response = client.get(
            "/api/graph",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401

    def test_rate_limiting(self, client):
        """Test rate limiting on login endpoint"""
        # Make multiple rapid requests
        for i in range(12):  # Exceeds 10/minute limit
            response = client.post(
                "/api/auth/login",
                params={"email": "demo@sentinal.ai", "password": "demo123"}
            )
            
            if i >= 10:
                # Should be rate limited
                assert response.status_code == 429
                break

    def test_complete_auth_flow(self, client):
        """Test complete authentication flow: login -> access -> refresh -> logout"""
        # 1. Login
        login_response = client.post(
            "/api/auth/login",
            params={"email": "demo@sentinal.ai", "password": "demo123"}
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]
        
        # 2. Access protected resource
        graph_response = client.get(
            "/api/graph",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert graph_response.status_code in [200, 503]
        
        # 3. Refresh token
        refresh_response = client.post(
            "/api/auth/refresh",
            params={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()["access_token"]
        
        # 4. Access with new token
        graph_response2 = client.get(
            "/api/graph",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert graph_response2.status_code in [200, 503]
        
        # 5. Logout
        logout_response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert logout_response.status_code == 200
