"""
SentinAL: Request/Response Models
==================================
Pydantic models for API request validation and response formatting.

Author: SentinAL Security Team
Date: 2026-01-23
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class AnalyzeRequest(BaseModel):
    """
    Request model for user fraud analysis.
    
    Validates that user_id is within acceptable range.
    """
    user_id: int = Field(
        ...,
        ge=0,
        le=99,
        description="User ID to analyze (must be between 0 and 99)"
    )
    
    @validator('user_id')
    def validate_user_id(cls, v):
        """Additional validation for user_id"""
        if v < 0 or v > 99:
            raise ValueError(f"User ID must be between 0 and 99, got {v}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 77
            }
        }


class AnalyzeResponse(BaseModel):
    """
    Response model for fraud analysis results.
    """
    error: bool = Field(
        default=False,
        description="Whether an error occurred"
    )
    user_id: int = Field(
        ...,
        description="User ID that was analyzed"
    )
    score: str = Field(
        ...,
        description="Fraud probability score (0.000 to 1.000)"
    )
    is_fraud: bool = Field(
        ...,
        description="Whether user is flagged as fraudulent"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Brief reason for the classification"
    )
    agent_report: str = Field(
        ...,
        description="Detailed AI-generated explanation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": False,
                "user_id": 77,
                "score": "0.923",
                "is_fraud": True,
                "reason": "Suspicious cyclic topology detected",
                "agent_report": "User 77 exhibits high-risk behavior consistent with money laundering..."
            }
        }


class GraphNode(BaseModel):
    """Node in the transaction graph"""
    id: str = Field(..., description="Unique node identifier")
    is_fraud: bool = Field(..., description="Ground truth fraud status")
    risk_score: float = Field(..., description="Initial risk score")
    fraud_probability: float = Field(..., description="Predicted fraud probability from GNN")

class GraphLink(BaseModel):
    """Edge/Transaction in the graph"""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    amount: float = Field(..., description="Transaction amount")
    is_laundering: bool = Field(..., description="Whether transaction is part of laundering pattern")

class GraphResponse(BaseModel):
    """Full graph data for visualization"""
    nodes: List[GraphNode]
    links: List[GraphLink]


class ErrorResponse(BaseModel):
    """
    Standard error response model.
    """
    error: bool = Field(
        default=True,
        description="Always true for error responses"
    )
    detail: str = Field(
        ...,
        description="Error message"
    )
    status_code: int = Field(
        ...,
        description="HTTP status code"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": True,
                "detail": "User ID 999 does not exist",
                "status_code": 400
            }
        }


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(
        ...,
        description="Service health status"
    )
    timestamp: str = Field(
        ...,
        description="Current timestamp"
    )
    version: str = Field(
        ...,
        description="API version"
    )
    cache: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Cache health and statistics"
    )
    instance_id: Optional[str] = Field(
        default="unknown",
        description="Instance identifier for load balancing"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "ai_connected": True,
                "data_loaded": True
            }
        }
