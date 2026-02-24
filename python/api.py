"""
SentinAL: Secured FastAPI Backend
==================================
Production-ready API with authentication, rate limiting, and comprehensive error handling.

Security Features:
- JWT authentication on all endpoints
- Rate limiting (10 requests/minute per IP)
- Input validation with Pydantic
- Structured logging with sensitive data protection
- CORS whitelist (no wildcards)
- Security headers

Author: SentinAL Security Team
Date: 2026-01-23
"""

import logging
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
from datetime import datetime
from datetime import timezone
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import ValidationError
from prometheus_fastapi_instrumentator import Instrumentator
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Import local modules
from agent_explainer import load_data, FraudExplainerAgent
from explainability import init_explainer_module, get_advanced_explanation
from auth import (
    get_current_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    blacklist_token,
    authenticate_user,
)
import auth_models
from models import (
    AnalyzeRequest,
    AnalyzeResponse,
    ErrorResponse,
    HealthResponse,
    GraphResponse,
    GraphNode,
    GraphLink,
)
from logging_config import get_logger, hash_sensitive_data
from audit_logger import log_audit_event
from cache_manager import get_cache_manager
from tracing import init_tracing, create_span, set_span_attribute, set_span_error, get_trace_id

# Load environment variables
load_dotenv()

# Configuration
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

VERSION = "2.0.0"  # Single source of truth for API version
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8080").split(",")
RATE_LIMIT = os.getenv("RATE_LIMIT_PER_MINUTE", "10")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Fail fast if default JWT secrets are used in production (Bug #1)
if ENVIRONMENT == "production":
    _jwt_secret = os.getenv("JWT_SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION")
    if _jwt_secret == "CHANGE_THIS_IN_PRODUCTION":
        raise RuntimeError(
            "FATAL: JWT_SECRET_KEY must be set in production! "
            "Set it via environment variable before starting the server."
        )

# Initialize logger
logger = get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="SentinAL Fraud Detection API (Secured)",
    description="AI-powered fraud detection with Graph Neural Networks and GraphRAG",
    version=VERSION,  # Bug #10: use VERSION constant
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None,
)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Prometheus Monitoring
Instrumentator().instrument(app).expose(app)

# CORS Middleware (Whitelist only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# Request Size Limit Middleware
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Limit request body size to prevent DoS attacks"""
    MAX_REQUEST_SIZE = 1024 * 1024  # 1MB

    if request.method in ["POST", "PUT", "PATCH"]:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"error": True, "detail": "Request body too large"},
            )

    response = await call_next(request)
    return response


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # HSTS only in production
    if ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip_hash": hash_sensitive_data(request.client.host)
            if request.client
            else "unknown",
        },
    )
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}", extra={"status_code": response.status_code})
    return response


# Global State  (Bug #5: removed duplicate `agent = None`)
agent = None
fraud_scores = None
graph = None

# Shared thread pool executor for async LLM calls (Bug #21: avoids per-request executor)
_executor = ThreadPoolExecutor(max_workers=4)


# Custom Exception Handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": True, "detail": "Invalid request data", "errors": exc.errors()},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "detail": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "detail": "Internal server error" if ENVIRONMENT == "production" else str(exc),
            "status_code": 500,
        },
    )


# Startup Event
@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    logger.info("=" * 50)
    logger.info("Starting SentinAL Fraud Detection API")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Allowed Origins: {ALLOWED_ORIGINS}")
    logger.info(f"Instance ID: {os.getenv('INSTANCE_ID', 'unknown')}")
    logger.info("=" * 50)

    # Initialize distributed tracing
    try:
        logger.info("Initializing distributed tracing...")
        init_tracing(
            app, service_name="sentinal-api", service_version=VERSION
        )  # was hardcoded "2.0.0"
    except Exception as e:
        logger.warning(f"Failed to initialize tracing: {e}")

    # Load graph data
    global graph, fraud_scores, agent  # Bug #8: `agent` must be declared global here
    try:
        logger.info("Loading transaction graph data...")
        import pickle

        with open("data/graph_enhanced.pkl", "rb") as f:
            data = pickle.load(f)

        graph = data["graph"]
        fraud_scores = data["fraud_scores"]

        logger.info(
            f"✓ Loaded graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges"
        )
        logger.info(f"✓ Loaded fraud scores for {len(fraud_scores)} users")
    except Exception as e:
        logger.error(f"❌ Failed to load graph data: {e}")
        graph = None
        fraud_scores = None

    # Initialize AI Agent (requires graph data to be loaded first)
    if graph is not None and fraud_scores is not None:
        try:
            logger.info("Initializing GraphRAG Fraud Explainer Agent...")
            agent = FraudExplainerAgent(graph=graph, fraud_scores=fraud_scores)
            app.state.fraud_agent = agent
            logger.info("✓ AI Agent ready with Ollama")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI agent: {e}")
            logger.warning("API will run without AI explanations")
            agent = None
    else:
        logger.warning("Skipping AI agent initialization (graph data not loaded)")
        agent = None

    # Initialize Explainer Module
    try:
        logger.info("Initializing Advanced Explainer Module...")
        init_explainer_module()
        logger.info("✓ Explainer module ready")
    except Exception as e:
        logger.error(f"❌ Failed to init explainer: {e}")

    logger.info("=" * 50)
    logger.info("✓ SentinAL API Ready")
    logger.info("=" * 50)

    # Track startup time for uptime calculation
    app.state.start_time = time.time()


# Endpoints


@app.get("/", response_model=dict)
async def root():
    """Root endpoint - API information"""
    return {
        "name": "SentinAL Fraud Detection API",
        "version": VERSION,  # was hardcoded "2.0.0"
        "status": "operational",
        "documentation": "/docs" if ENVIRONMENT == "development" else "Contact administrator",
        "security": "JWT authentication required",
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint for monitoring.
    Returns system status and cache information.
    """
    cache_manager = get_cache_manager()
    cache_health = cache_manager.health_check()

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=VERSION,  # Bug #10: use VERSION constant (was hardcoded "1.0.0")
        cache=cache_health,
        instance_id=os.getenv("INSTANCE_ID", "unknown"),
    )


@app.get("/health/ready", response_model=dict, tags=["System"])
async def readiness_check():
    """
    Readiness probe for load balancer.
    Checks if instance can serve traffic (dependencies available).
    """
    checks = {"redis": False, "model": False, "cache": False}

    try:
        # Check Redis connection
        cache_manager = get_cache_manager()
        cache_health = cache_manager.health_check()
        checks["redis"] = cache_health.get("status") in ["connected", "fallback"]
        checks["cache"] = True

        # Check if model data is loaded (Bug #6: was app.state.graph_data which never exists)
        checks["model"] = graph is not None and fraud_scores is not None

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")

    all_ready = all(checks.values())

    if all_ready:
        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),  # was naive datetime
            "checks": checks,
            "instance_id": os.getenv("INSTANCE_ID", "unknown"),
        }
    else:
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})


@app.get("/health/live", response_model=dict, tags=["System"])
async def liveness_check():
    """
    Liveness probe for load balancer.
    Checks if instance is alive (can respond to requests).
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),  # was naive datetime
        "instance_id": os.getenv("INSTANCE_ID", "unknown"),
        "uptime_seconds": time.time() - app.state.start_time
        if hasattr(app.state, "start_time")
        else 0,
    }


# Authentication Endpoints


@app.post("/api/auth/login", tags=["Authentication"])
@limiter.limit(f"{RATE_LIMIT}/minute")
async def login(request: Request, credentials: auth_models.LoginRequest):
    """
    Authenticate user and return access and refresh tokens.

    Args:
        email: User email
        password: User password

    Returns:
        Access token, refresh token, and user info
    """
    # Authenticate user
    user = authenticate_user(credentials.email, credentials.password)

    if not user:
        logger.warning(f"Failed login attempt for email: {hash_sensitive_data(credentials.email)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )

    # Create tokens
    access_token = create_access_token(
        data={"sub": user["id"], "email": user["email"], "username": user["username"]}
    )
    refresh_token = create_refresh_token(data={"sub": user["id"]})

    # Log successful login
    logger.info(f"Successful login for user: {user['id']}")
    log_audit_event(
        event_type="USER_LOGIN",
        user_id=user["id"],
        action="login",
        details={"email": user["email"]},
        status="SUCCESS",
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {"id": user["id"], "email": user["email"], "username": user["username"]},
    }


@app.post("/api/auth/refresh", tags=["Authentication"])
@limiter.limit(f"{RATE_LIMIT}/minute")
async def refresh_token_endpoint(request: Request, body: auth_models.RefreshRequest):
    """
    Refresh access token using refresh token.

    Accepts a JSON body: {"refresh_token": "<token>"}

    Returns:
        New access token and refresh token
    """
    try:
        # Verify refresh token (body.refresh_token from JSON body)
        user_id = verify_refresh_token(body.refresh_token)

        # Create new tokens
        access_token = create_access_token(data={"sub": user_id})
        new_refresh_token = create_refresh_token(data={"sub": user_id})

        logger.info(f"Token refreshed for user: {user_id}")

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not refresh token"
        )


@app.post("/api/auth/logout", tags=["Authentication"])
@limiter.limit(f"{RATE_LIMIT}/minute")
async def logout(request: Request, current_user: str = Depends(get_current_user)):
    """
    Logout user and invalidate tokens.

    Requires:
        Valid JWT token in Authorization header
    """
    try:
        # Get token from request
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            blacklist_token(token)

        logger.info(f"User logged out: {current_user}")
        log_audit_event(
            event_type="USER_LOGOUT",
            user_id=current_user,
            action="logout",
            details={},
            status="SUCCESS",
        )

        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )


# Bug #2: Public endpoint is now gated to development environment only
@app.get("/analyze/{user_id}", response_model=AnalyzeResponse)
@limiter.limit(f"{RATE_LIMIT}/minute")
async def analyze_user_public(request: Request, user_id: int):
    """
    Analyze a user for fraud patterns (PUBLIC ENDPOINT FOR DEMO).

    Note: This is a public endpoint for demo purposes.
    In production, use the authenticated endpoint below.

    Args:
        user_id: User ID to analyze (0-99)

    Returns:
        Fraud analysis with score and AI explanation

    Rate Limit: 10 requests per minute per IP
    """
    # Bug #2: Block public endpoint in production
    if ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This demo endpoint is not available in production. Use /api/analyze/{user_id} with authentication.",
        )

    # Check if services are available
    if fraud_scores is None:
        logger.error("Service unavailable: data not loaded")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Graph data not loaded.",
        )

    # Validate user_id
    try:
        validated_request = AnalyzeRequest(user_id=user_id)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user_id: {e.errors()[0]['msg']}",
        )

    # Log request (with hashed user_id for privacy)
    logger.info(
        f"Public analysis requested",
        extra={"user_id_hash": hash_sensitive_data(user_id), "requester": "public"},
    )

    # Perform analysis
    try:
        # Bug #7: Standardize fraud_scores access — always use dict form
        fraud_probs = (
            fraud_scores.get("fraud_probability", fraud_scores)
            if isinstance(fraud_scores, dict)
            else fraud_scores
        )
        if user_id >= len(fraud_probs):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User ID {user_id} not found in dataset",
            )

        score = float(fraud_probs[user_id])

        # Get AI explanation (synchronous call - simpler and more reliable)
        if agent is not None:
            try:
                explanation = agent.explain(user_id)
                logger.info(f"AI explanation generated for user {user_id}")
            except Exception as e:
                logger.error(f"AI explanation failed for user {user_id}: {e}", exc_info=True)
                explanation = f"AI explanation unavailable. Fraud score: {score:.3f}"
        else:
            explanation = f"AI explanation unavailable. Fraud score: {score:.3f}"

        # Determine fraud status and risk level
        if score > 0.8:
            is_fraud = True
            risk_level = "high"
            reason = "High fraud probability - Suspicious patterns detected"
        elif score > 0.5:
            is_fraud = True  # Medium suspicious
            risk_level = "medium"
            reason = "Medium fraud probability - Some suspicious patterns"
        else:
            is_fraud = False
            risk_level = "low"
            reason = "Normal transaction patterns"

        # Build response
        response = AnalyzeResponse(
            error=False,
            user_id=user_id,
            score=f"{score:.3f}",
            is_fraud=is_fraud,
            reason=reason,
            agent_report=explanation,
        )

        logger.info(
            f"Analysis complete: user_hash={hash_sensitive_data(user_id)}, "
            f"fraud={is_fraud}, score={score:.3f}"
        )

        # AUDIT LOG
        log_audit_event(
            event_type="FRAUD_ANALYSIS",
            user_id="public_demo",
            action="analyze_user_public",
            details={
                "target_user_id": user_id,
                "score": f"{score:.3f}",
                "is_fraud": is_fraud,
                "reason": response.reason,
            },
            status="SUCCESS",
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed. Please try again later.",
        )


# Authenticated endpoint (for production use)
@app.get("/api/analyze/{user_id}", response_model=AnalyzeResponse)
@limiter.limit(f"{RATE_LIMIT}/minute")
async def analyze_user_authenticated(
    request: Request, user_id: int, current_user: str = Depends(get_current_user)
):
    """
    Analyze a user for fraud patterns (AUTHENTICATED ENDPOINT).
    
    Requires:
    - Valid JWT token in Authorization header
    - User ID between 0 and 99
    
    Returns:
    - Fraud probability score
    - Classification (fraud/normal)
    - AI-generated explanation
    
    Rate Limit: 10 requests per minute per IP
    
    Example:
        curl -H "Authorization: Bearer YOUR_TOKEN" \\
             http://localhost:8000/api/analyze/77
    """
    # Bug #11: Only block if fraud_scores itself isn't loaded; degrade gracefully without agent
    if fraud_scores is None:
        logger.error("Service unavailable: data not loaded")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Data not loaded.",
        )

    # Validate user_id
    try:
        validated_request = AnalyzeRequest(user_id=user_id)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user_id: {e.errors()[0]['msg']}",
        )

    # Log request (with hashed user_id for privacy)
    logger.info(
        f"Analysis requested by {current_user}",
        extra={"user_id_hash": hash_sensitive_data(user_id), "requester": current_user},
    )

    # Perform analysis
    try:
        # Bug #7: Standardize fraud_scores access
        fraud_probs = (
            fraud_scores.get("fraud_probability", fraud_scores)
            if isinstance(fraud_scores, dict)
            else fraud_scores
        )
        if user_id >= len(fraud_probs):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User ID {user_id} not found in dataset",
            )

        score = float(fraud_probs[user_id])

        # Get AI explanation (Bug #21: use get_running_loop + shared executor)
        if agent is not None:
            try:
                loop = asyncio.get_running_loop()  # Bug #21: was get_event_loop() (deprecated)
                explanation = await loop.run_in_executor(
                    _executor,  # Bug #21: shared executor, not new per-request
                    agent.explain,
                    user_id,
                )
            except Exception as e:
                logger.warning(f"AI explanation failed: {e}")
                explanation = f"AI explanation unavailable. Fraud score: {score:.3f}"
        else:
            explanation = f"AI agent not available. Fraud score: {score:.3f}"

        # Determine fraud status
        is_fraud = score > 0.8

        # Build response
        response = AnalyzeResponse(
            error=False,
            user_id=user_id,
            score=f"{score:.3f}",
            is_fraud=is_fraud,
            reason="Suspicious cyclic topology detected"
            if is_fraud
            else "Normal transaction patterns",
            agent_report=explanation,
        )

        logger.info(
            f"Analysis complete: user_hash={hash_sensitive_data(user_id)}, "
            f"fraud={is_fraud}, score={score:.3f}"
        )

        # AUDIT LOG
        log_audit_event(
            event_type="FRAUD_ANALYSIS",
            user_id=current_user,
            action="analyze_user_authenticated",
            details={
                "target_user_id": user_id,
                "score": f"{score:.3f}",
                "is_fraud": is_fraud,
                "reason": response.reason,
            },
            status="SUCCESS",
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed. Please try again later.",
        )


@app.get("/api/graph", response_model=GraphResponse)
@limiter.limit(f"{RATE_LIMIT}/minute")
async def get_graph_data(request: Request, current_user: str = Depends(get_current_user)):
    """
    Get full graph data for visualization (AUTHENTICATED).

    Returns:
    - Nodes with fraud probabilities
    - Links with transaction amounts
    """
    if graph is None or fraud_scores is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Graph data not loaded"
        )

    try:
        nodes = []
        for node_id in graph.nodes():
            node_data = graph.nodes[node_id]
            # Safely get fraud probability
            try:
                fraud_prob = fraud_scores["fraud_probability"][node_id]
            except (IndexError, KeyError, TypeError):
                fraud_prob = 0.0

            nodes.append(
                GraphNode(
                    id=str(node_id),
                    is_fraud=bool(node_data.get("is_fraud", False)),
                    risk_score=float(node_data.get("risk_score_initial", 0.0)),
                    fraud_probability=float(fraud_prob),
                )
            )

        links = []
        for u, v, data in graph.edges(data=True):
            links.append(
                GraphLink(
                    source=str(u),
                    target=str(v),
                    amount=float(data.get("amount", 0.0)),
                    is_laundering=bool(data.get("is_laundering", False)),
                )
            )

        return GraphResponse(nodes=nodes, links=links)

    except Exception as e:
        logger.error(f"Failed to retrieve graph data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve graph data",
        )


@app.get("/api/explain/advanced/{user_id}")
@limiter.limit(f"{RATE_LIMIT}/minute")
async def advanced_explanation(
    request: Request, user_id: int, current_user: str = Depends(get_current_user)
):
    """
    Get deep learning explanation (GNNExplainer/SHAP).
    """
    try:
        explanation = get_advanced_explanation(user_id)
        if "error" in explanation:
            raise HTTPException(status_code=400, detail=explanation["error"])
        return explanation
    except Exception as e:
        logger.error(f"Explanation failed: {e}")
        raise HTTPException(status_code=500, detail="Explanation extraction failed")


# Run server
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(app, host=host, port=port, log_level="info")
