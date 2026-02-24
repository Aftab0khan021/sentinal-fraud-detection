#!/bin/bash
set -e

echo "🚀 Setting up SentinAL development environment..."

# Update package lists
echo "📦 Updating package lists..."
sudo apt-get update

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt-get install -y \
    build-essential \
    curl \
    git \
    vim \
    jq \
    htop \
    postgresql-client \
    redis-tools

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
cd /workspace
pip install --upgrade pip
pip install -r python/requirements.txt
pip install -r python/requirements-dev.txt || true

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
pip install pre-commit
pre-commit install || true

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p python/logs
mkdir -p python/data
mkdir -p python/models
mkdir -p torchserve/model-store

# Copy environment file if not exists
if [ ! -f python/.env ]; then
    echo "📝 Creating .env file from template..."
    cp python/.env.example python/.env
    echo "⚠️  Please update python/.env with your configuration"
fi

# Set up git config
echo "🔧 Configuring git..."
git config --global core.autocrlf input
git config --global pull.rebase false

# Install development tools
echo "🛠️  Installing development tools..."
pip install ipython jupyter black flake8 mypy pytest-watch

# Build frontend
echo "🏗️  Building frontend..."
npm run build || echo "⚠️  Frontend build failed, will retry later"

# Print success message
echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📚 Quick Start:"
echo "  1. Update python/.env with your configuration"
echo "  2. Start services: docker-compose up -d"
echo "  3. Start API: cd python && python api.py"
echo "  4. Start frontend: npm run dev"
echo ""
echo "🔗 Useful URLs:"
echo "  - Frontend: http://localhost:3000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Grafana: http://localhost:3001"
echo "  - Jaeger: http://localhost:16686"
echo ""
echo "Happy coding! 🎉"
