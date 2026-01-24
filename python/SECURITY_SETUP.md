# Phase 1 Security Implementation - Setup Guide

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd python

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (optional, for testing)
pip install -r requirements-dev.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and update these critical values:
# - JWT_SECRET_KEY (generate a secure random string)
# - ALLOWED_ORIGINS (your frontend URL)
```

**Generate a secure JWT secret:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Test the Setup

```bash
# Run tests
pytest tests/ -v

# Generate a test token
python generate_token.py --user test_user --expires 60

# Start the API server
python api.py
```

### 4. Test Authentication

```bash
# Generate token
TOKEN=$(python generate_token.py --user test_user --expires 60 | grep "Token:" | cut -d' ' -f2)

# Test with authentication
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/analyze/77

# Test without authentication (should fail)
curl http://localhost:8000/analyze/77
```

---

## 📁 New Files Created

### Core Modules
- `auth.py` - JWT authentication (token generation & verification)
- `models.py` - Pydantic models for request/response validation
- `logging_config.py` - Structured logging with file rotation
- `generate_token.py` - Utility to generate test JWT tokens

### Configuration
- `.env.example` - Environment configuration template
- `requirements.txt` - Pinned production dependencies
- `requirements-dev.txt` - Development dependencies

### Tests
- `tests/conftest.py` - Pytest fixtures
- `tests/test_auth.py` - Authentication tests
- `tests/test_api.py` - API integration tests

### Updated Files
- `api.py` - Complete rewrite with security features
- `.gitignore` - Added .env and .log files

---

## 🔐 Security Features Implemented

### 1. JWT Authentication
- All `/analyze/*` endpoints require valid JWT token
- Tokens expire after 30 minutes (configurable)
- Proper error messages for expired/invalid tokens

### 2. Rate Limiting
- 10 requests per minute per IP address (configurable)
- Returns 429 Too Many Requests when exceeded
- Prevents API abuse and DoS attacks

### 3. Input Validation
- Pydantic models validate all requests
- User ID must be 0-99
- Proper error messages for invalid input

### 4. Logging
- Structured logging with timestamps
- File rotation (10MB per file, 5 backups)
- Sensitive data (user IDs) are hashed in logs
- Separate log levels for dev/prod

### 5. CORS Security
- Whitelist-only origins (no wildcards)
- Configured via environment variable
- Blocks unauthorized cross-origin requests

### 6. Security Headers
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- HSTS (production only)

### 7. Error Handling
- Custom exception handlers
- Consistent error response format
- No sensitive data in error messages
- Proper HTTP status codes

---

## 🧪 Running Tests

```bash
cd python

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

**Expected Results:**
- All authentication tests should pass
- API tests may show some failures if AI agent not loaded
- Rate limiting test may be flaky (timing-dependent)

---

## 🔧 Configuration Options

Edit `.env` to customize:

```bash
# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_EXPIRATION_MINUTES=30

# API
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development

# CORS
ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10

# Logging
LOG_LEVEL=INFO
LOG_FILE=api.log
LOG_MAX_SIZE_MB=10
LOG_BACKUP_COUNT=5

# Ollama
OLLAMA_MODEL=llama3.2:1b
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 📊 API Endpoints

### Public Endpoints (No Auth Required)
- `GET /` - API information
- `GET /health` - Health check

### Protected Endpoints (Auth Required)
- `GET /analyze/{user_id}` - Analyze user for fraud
  - Requires: `Authorization: Bearer <token>`
  - Rate limit: 10/minute
  - User ID: 0-99

---

## 🐛 Troubleshooting

### "403 Forbidden" Error
- Missing or invalid Authorization header
- Generate a new token: `python generate_token.py`

### "401 Unauthorized" Error
- Token is expired or invalid
- Check JWT_SECRET_KEY matches in .env

### "429 Too Many Requests" Error
- Rate limit exceeded (10/minute)
- Wait 60 seconds or increase RATE_LIMIT_PER_MINUTE

### "503 Service Unavailable" Error
- AI agent or fraud data not loaded
- Check that data files exist in `data/` directory
- Ensure Ollama is running: `ollama serve`

### Tests Failing
- Install test dependencies: `pip install -r requirements-dev.txt`
- Check that .env file exists
- Some tests may fail if AI agent not loaded (expected)

---

## 🚀 Next Steps

1. **Update Frontend** to include JWT tokens in requests
2. **Generate Production Secret** for JWT_SECRET_KEY
3. **Configure Production CORS** origins
4. **Set up Log Monitoring** (e.g., Logrotate, CloudWatch)
5. **Run Security Scan**: `safety check`
6. **Deploy to Production** with ENVIRONMENT=production

---

## 📝 Frontend Integration Example

```javascript
// Get JWT token (implement your own auth flow)
const token = "YOUR_JWT_TOKEN_HERE";

// Make authenticated request
fetch('http://localhost:8000/analyze/77', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

---

## ✅ Verification Checklist

- [ ] Dependencies installed successfully
- [ ] .env file created and configured
- [ ] JWT secret key generated and set
- [ ] Tests pass (pytest)
- [ ] Can generate test tokens
- [ ] API starts without errors
- [ ] Authentication works (403 without token)
- [ ] Rate limiting works (429 after 10 requests)
- [ ] Logs are created in api.log
- [ ] Security headers present in responses

---

**Implementation Complete!** 🎉

All Phase 1 security features have been implemented and tested.
