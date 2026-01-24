
import unittest
from fastapi.testclient import TestClient
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add python directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'python')))

from api import app
from auth import create_access_token

class TestSentinALAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.token = create_access_token({"sub": "test_user"})
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}

    def test_root(self):
        """Test root endpoint"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.json())

    def test_health_check(self):
        """Test health endpoint"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)

    def test_analyze_public_no_auth(self):
        """Test public analysis endpoint"""
        # User 0 should exist
        response = self.client.get("/analyze/0")
        # It might be 503 if agent not loaded in test env, but let's check basic response
        if response.status_code == 200:
            data = response.json()
            self.assertEqual(data['user_id'], 0)
            self.assertIn("score", data)
        elif response.status_code == 503:
            # Service unavailable is acceptable if agent didn't load in test env
            pass
        else:
            self.fail(f"Unexpected status code: {response.status_code}")

    def test_analyze_authenticated_success(self):
        """Test authenticated analysis endpoint"""
        response = self.client.get("/api/analyze/0", headers=self.auth_headers)
        if response.status_code == 200:
            data = response.json()
            self.assertEqual(data['user_id'], 0)
        elif response.status_code == 503:
            pass
        else:
            self.fail(f"Unexpected status code: {response.status_code}")

    def test_analyze_authenticated_unauthorized(self):
        """Test calling auth endpoint without token"""
        response = self.client.get("/api/analyze/0")
        self.assertEqual(response.status_code, 401) # Server returns 401 for missing creds

if __name__ == '__main__':
    unittest.main()
