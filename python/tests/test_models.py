"""
SentinAL: Pydantic Models Tests
================================
Unit tests for request/response validation models.

Author: SentinAL Testing Team
Date: 2026-01-23
"""

import pytest
from pydantic import ValidationError
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import AnalyzeRequest, AnalyzeResponse, ErrorResponse, HealthResponse


class TestAnalyzeRequest:
    """Test suite for AnalyzeRequest model"""
    
    def test_valid_request(self):
        """Test valid request creation"""
        request = AnalyzeRequest(user_id=50)
        assert request.user_id == 50
    
    def test_boundary_values(self):
        """Test boundary values (0 and 99)"""
        request_min = AnalyzeRequest(user_id=0)
        request_max = AnalyzeRequest(user_id=99)
        
        assert request_min.user_id == 0
        assert request_max.user_id == 99
    
    def test_invalid_negative(self):
        """Test that negative user_id is rejected"""
        with pytest.raises(ValidationError):
            AnalyzeRequest(user_id=-1)
    
    def test_invalid_too_large(self):
        """Test that user_id > 99 is rejected"""
        with pytest.raises(ValidationError):
            AnalyzeRequest(user_id=100)
    
    def test_invalid_type(self):
        """Test that non-integer user_id is rejected"""
        with pytest.raises(ValidationError):
            AnalyzeRequest(user_id="invalid")


class TestAnalyzeResponse:
    """Test suite for AnalyzeResponse model"""
    
    def test_valid_response(self):
        """Test valid response creation"""
        response = AnalyzeResponse(
            error=False,
            user_id=77,
            score="0.923",
            is_fraud=True,
            reason="Suspicious patterns",
            agent_report="Detailed analysis..."
        )
        
        assert response.error is False
        assert response.user_id == 77
        assert response.score == "0.923"
        assert response.is_fraud is True
    
    def test_optional_reason(self):
        """Test that reason is optional"""
        response = AnalyzeResponse(
            user_id=50,
            score="0.123",
            is_fraud=False,
            agent_report="Normal behavior"
        )
        
        assert response.reason is None


class TestErrorResponse:
    """Test suite for ErrorResponse model"""
    
    def test_error_response(self):
        """Test error response creation"""
        error = ErrorResponse(
            detail="User not found",
            status_code=404
        )
        
        assert error.error is True
        assert error.detail == "User not found"
        assert error.status_code == 404


class TestHealthResponse:
    """Test suite for HealthResponse model"""
    
    def test_health_response(self):
        """Test health response creation"""
        health = HealthResponse(
            status="healthy",
            ai_connected=True,
            data_loaded=True
        )
        
        assert health.status == "healthy"
        assert health.ai_connected is True
        assert health.data_loaded is True
