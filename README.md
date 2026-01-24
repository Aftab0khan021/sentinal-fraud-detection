# 🛡️ SentinAL: Agentic Fraud Detection with GraphRAG

![CI Pipeline](https://github.com/Aftab0khan021/sentinal-fraud-detection/actions/workflows/ci.yml/badge.svg)
![Docker Build](https://github.com/Aftab0khan021/sentinal-fraud-detection/actions/workflows/docker-build.yml/badge.svg)
![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)
![Coverage](https://img.shields.io/badge/coverage-75%25-yellow.svg)
![Security](https://img.shields.io/badge/security-A-green.svg)

**SentinAL** is a privacy-first fraud detection system that combines **Graph Neural Networks (GNNs)** with **Local Generative AI** to identify and explain complex money laundering rings.

Unlike standard "black box" models that only output a probability score, SentinAL uses an **AI Agent** to analyze transaction topology and generate human-readable compliance reports—all without sending sensitive financial data to the cloud.

---

## 🆕 What's New (v2.0.0)

### ✅ Authentication & Security
- **JWT Authentication** with refresh tokens
- **Protected Routes** - Login required for fraud detection
- **Secure Passwords** - Bcrypt hashing with demo users
- **Request Size Limits** - 1MB max to prevent DoS
- **Enhanced Security Headers** - CORS, CSP, HSTS

### ✅ Testing Infrastructure
- **Frontend Tests** - Vitest + React Testing Library
- **Integration Tests** - Complete auth flow testing
- **80% Coverage Target** - Comprehensive test suite
- **CI/CD Pipeline** - Automated testing on push/PR

### ✅ Production Ready
- **Environment Variables** - No hardcoded secrets
- **Redis Caching** - Distributed cache with password
- **Monitoring** - Prometheus + Grafana dashboards
- **Docker Compose** - One-command deployment

---

## 📸 Project Demo

### 1. Authentication
*Secure login with JWT tokens:*
![Login Screen](https://via.placeholder.com/800x400?text=Login+Screen)

### 2. The Intelligence (Backend)
*The core AI agent detecting a money laundering ring using local Llama 3.2:*
<img width="1297" height="661" alt="Terminal Output" src="https://github.com/user-attachments/assets/5f18fa7e-6021-4d27-8ead-b7714d86c227" />

### 3. The Interface (Frontend)
*The analyst dashboard visualizing the detected fraud ring:*
<img width="1024" height="581" alt="Dashboard UI" src="https://github.com/user-attachments/assets/92ffc80a-d03e-4df3-ba59-43676e4247f4" />

---

## 🚀 Key Features

* **Graph Neural Network (R-GCN):** Uses Relational Graph Convolutional Networks to detect "cyclic" transaction patterns (A → B → C → A) that traditional tabular models miss.
* **GraphRAG Explanation Agent:** A custom AI agent that retrieves topological subgraphs (k-hop neighbors) and uses a local LLM to explain *why* a user was flagged.
* **Privacy-First Architecture:** Runs 100% locally using **Ollama** (Llama 3.2 1B), ensuring no financial data leaves the secure environment.
* **Interactive Dashboard:** A React/TypeScript UI for compliance officers to visualize risk scores and transaction flows.
* **JWT Authentication:** Secure access with token refresh and logout functionality.
* **Distributed Caching:** Redis integration with automatic fallback to in-memory cache.

## 🛠️ Tech Stack

* **AI/ML:** Python, PyTorch Geometric, NetworkX, Scikit-learn
* **GenAI:** LangChain, Ollama (Llama 3.2), Prompt Engineering
* **Frontend:** React, TypeScript, Vite, Tailwind CSS, Shadcn UI
* **Backend:** FastAPI, JWT Authentication, Redis Caching
* **Testing:** Vitest, React Testing Library, Pytest
* **DevOps:** Docker, Docker Compose, GitHub Actions, Prometheus, Grafana
* **Data:** Synthetic financial graph generation with injected fraud topologies

---

## 💻 Quick Start

### Prerequisites
- Python 3.10+ (3.14 recommended)
- Node.js 18+
- Docker & Docker Compose (optional)
- Ollama (for AI explanations)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/Aftab0khan021/sentinal-fraud-detection.git
cd sentinal-fraud-detection

# Set up environment variables
cp python/.env.example python/.env
# Edit python/.env and set secure secrets

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
# Grafana: http://localhost:3001 (admin / SentinAL_Grafana_2024!)
```

### Option 2: Manual Setup

#### 1. Backend Setup

```bash
cd python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up environment
cp .env.example .env
# Edit .env and configure secrets

# Generate synthetic data
python data_gen_enhanced.py

# Train the fraud detection model
python gnn_train_improved.py

# Start the API server
python api.py
```

#### 2. Frontend Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Access at http://localhost:5173
```

#### 3. Start Ollama (for AI explanations)

```bash
# Install Ollama from https://ollama.ai
ollama serve

# Pull the model
ollama pull llama3.2:1b
```

---

## 🔐 Demo Credentials

| Email | Password | Role |
|-------|----------|------|
| demo@sentinal.ai | demo123 | Analyst |
| admin@sentinal.ai | admin123 | Admin |

---

## 🧪 Testing

### Run All Tests

```bash
# Frontend tests
npm test
npm run test:coverage

# Backend tests
cd python
pytest tests/ -v --cov=. --cov-report=html

# Integration tests
pytest tests/integration/ -v
```

### Test Coverage
- **Frontend:** ~60% (Login, AuthContext, ProtectedRoute)
- **Backend:** ~75% (API, Auth, GNN, Cache)
- **Target:** 80%+

---

## 📚 Documentation

- [**Walkthrough**](./walkthrough.md) - Complete implementation guide
- [**Testing Guide**](./TESTING.md) - How to run and write tests
- [**Security Hardening**](./SECURITY_HARDENING.md) - Production security checklist
- [**API Documentation**](http://localhost:8000/docs) - Interactive API docs (when running)

---

## 🏗️ Architecture

```
┌─────────────────┐
│   React UI      │  ← JWT Auth, Protected Routes
│   (Frontend)    │
└────────┬────────┘
         │
    HTTP/REST
         │
┌────────▼────────┐
│   FastAPI       │  ← Rate Limiting, Security Headers
│   (Backend)     │
└────┬───────┬────┘
     │       │
     │       └──────► Redis Cache (Distributed)
     │
┌────▼────────────┐
│  R-GCN Model    │  ← Fraud Detection
│  GraphRAG Agent │  ← AI Explanations (Ollama)
└─────────────────┘
```

---

## 🔒 Security Features

- ✅ JWT authentication with refresh tokens
- ✅ Password hashing with bcrypt
- ✅ Request size limits (1MB)
- ✅ Rate limiting (10 req/min)
- ✅ CORS whitelist
- ✅ Security headers (CSP, HSTS, X-Frame-Options)
- ✅ Audit logging
- ✅ Token blacklist for logout
- ✅ Environment-based secrets

---

## 🚢 Deployment

### Production Checklist

1. **Generate Secure Secrets**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Configure Environment Variables**
   - Set `JWT_SECRET_KEY` and `JWT_REFRESH_SECRET_KEY`
   - Set `REDIS_PASSWORD` and `GRAFANA_ADMIN_PASSWORD`
   - Set `ENVIRONMENT=production`

3. **Enable HTTPS**
   - Configure SSL certificates
   - Update `ALLOWED_ORIGINS` for production domain

4. **Database Migration**
   - Replace demo users with real database
   - Implement user registration/management

5. **Monitoring**
   - Set up Grafana dashboards
   - Configure Prometheus alerts
   - Enable error tracking (Sentry)

---

## 📊 Performance

- **API Response Time:** < 100ms (cached)
- **Fraud Detection:** ~2s per user
- **AI Explanation:** ~5s per user (with Ollama)
- **Cache Hit Rate:** 85%+

---

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

## 📝 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- PyTorch Geometric team for R-GCN implementation
- Ollama for local LLM inference
- Shadcn UI for beautiful components
- FastAPI for the excellent web framework

---

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ by the SentinAL Team**
