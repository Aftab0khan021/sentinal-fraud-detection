#!/bin/bash
# SentinAL Automated Setup Script for macOS/Linux
# This script automates the entire development environment setup

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_message() {
    echo -e "${2}${1}${NC}"
}

print_message "╔════════════════════════════════════════════════════════╗" "$BLUE"
print_message "║     SentinAL Fraud Detection - Automated Setup        ║" "$BLUE"
print_message "╚════════════════════════════════════════════════════════╝" "$BLUE"
echo ""

# Check if running on macOS or Linux
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

print_message "🖥️  Detected OS: $MACHINE" "$BLUE"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check prerequisites
print_message "📋 Step 1/8: Checking prerequisites..." "$YELLOW"

if ! command_exists git; then
    print_message "❌ Git is not installed. Please install Git first." "$RED"
    exit 1
fi
print_message "✅ Git is installed" "$GREEN"

if ! command_exists docker; then
    print_message "❌ Docker is not installed. Please install Docker Desktop first." "$RED"
    print_message "   Download from: https://www.docker.com/products/docker-desktop" "$YELLOW"
    exit 1
fi
print_message "✅ Docker is installed" "$GREEN"

if ! command_exists docker-compose; then
    print_message "❌ Docker Compose is not installed." "$RED"
    exit 1
fi
print_message "✅ Docker Compose is installed" "$GREEN"

# Step 2: Install Python
print_message "\n📋 Step 2/8: Setting up Python..." "$YELLOW"

if ! command_exists python3; then
    print_message "Installing Python 3.11..." "$BLUE"
    if [ "$MACHINE" = "Mac" ]; then
        if ! command_exists brew; then
            print_message "Installing Homebrew..." "$BLUE"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python@3.11
    elif [ "$MACHINE" = "Linux" ]; then
        sudo apt-get update
        sudo apt-get install -y python3.11 python3.11-venv python3-pip
    fi
fi
print_message "✅ Python is ready" "$GREEN"

# Step 3: Install Node.js
print_message "\n📋 Step 3/8: Setting up Node.js..." "$YELLOW"

if ! command_exists node; then
    print_message "Installing Node.js 20..." "$BLUE"
    if [ "$MACHINE" = "Mac" ]; then
        brew install node@20
    elif [ "$MACHINE" = "Linux" ]; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
fi
print_message "✅ Node.js $(node --version) is ready" "$GREEN"

# Step 4: Create Python virtual environment
print_message "\n📋 Step 4/8: Creating Python virtual environment..." "$YELLOW"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_message "✅ Virtual environment created" "$GREEN"
else
    print_message "✅ Virtual environment already exists" "$GREEN"
fi

# Activate virtual environment
source venv/bin/activate

# Step 5: Install Python dependencies
print_message "\n📋 Step 5/8: Installing Python dependencies..." "$YELLOW"

pip install --upgrade pip
pip install -r python/requirements.txt
print_message "✅ Python dependencies installed" "$GREEN"

# Step 6: Install Node.js dependencies
print_message "\n📋 Step 6/8: Installing Node.js dependencies..." "$YELLOW"

npm install
print_message "✅ Node.js dependencies installed" "$GREEN"

# Step 7: Setup environment files
print_message "\n📋 Step 7/8: Setting up environment files..." "$YELLOW"

if [ ! -f "python/.env" ]; then
    cp python/.env.example python/.env
    print_message "✅ Created python/.env from template" "$GREEN"
    print_message "⚠️  Please update python/.env with your configuration" "$YELLOW"
else
    print_message "✅ python/.env already exists" "$GREEN"
fi

# Create necessary directories
mkdir -p python/logs
mkdir -p python/data
mkdir -p python/models
mkdir -p torchserve/model-store

# Step 8: Start Docker services
print_message "\n📋 Step 8/8: Starting Docker services..." "$YELLOW"

docker-compose up -d redis-master prometheus grafana

print_message "✅ Docker services started" "$GREEN"

# Wait for services to be ready
print_message "\n⏳ Waiting for services to be ready..." "$BLUE"
sleep 5

# Check service health
print_message "\n🔍 Checking service health..." "$BLUE"

if curl -f http://localhost:6379 > /dev/null 2>&1 || nc -z localhost 6379 2>/dev/null; then
    print_message "✅ Redis is running" "$GREEN"
else
    print_message "⚠️  Redis may not be ready yet" "$YELLOW"
fi

if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
    print_message "✅ Prometheus is running" "$GREEN"
else
    print_message "⚠️  Prometheus may not be ready yet" "$YELLOW"
fi

if curl -f http://localhost:3001 > /dev/null 2>&1; then
    print_message "✅ Grafana is running" "$GREEN"
else
    print_message "⚠️  Grafana may not be ready yet" "$YELLOW"
fi

# Print success message
echo ""
print_message "╔════════════════════════════════════════════════════════╗" "$GREEN"
print_message "║           ✅ Setup Complete! ✅                         ║" "$GREEN"
print_message "╚════════════════════════════════════════════════════════╝" "$GREEN"
echo ""

print_message "📚 Next Steps:" "$BLUE"
echo ""
echo "  1. Update configuration:"
echo "     ${YELLOW}nano python/.env${NC}"
echo ""
echo "  2. Start the API:"
echo "     ${YELLOW}source venv/bin/activate${NC}"
echo "     ${YELLOW}cd python && python api.py${NC}"
echo ""
echo "  3. Start the frontend (in a new terminal):"
echo "     ${YELLOW}npm run dev${NC}"
echo ""
echo "  4. Access the application:"
echo "     ${GREEN}Frontend:${NC}    http://localhost:5173"
echo "     ${GREEN}API Docs:${NC}    http://localhost:8000/docs"
echo "     ${GREEN}Grafana:${NC}     http://localhost:3001 (admin/SentinAL_Grafana_2024!)"
echo "     ${GREEN}Prometheus:${NC}  http://localhost:9090"
echo "     ${GREEN}Jaeger:${NC}      http://localhost:16686"
echo ""
print_message "📖 For more information, see README.md" "$BLUE"
print_message "🐛 Report issues: https://github.com/Aftab0khan021/sentinal-fraud-detection/issues" "$BLUE"
echo ""
print_message "Happy coding! 🎉" "$GREEN"
