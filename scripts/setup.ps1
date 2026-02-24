# SentinAL Automated Setup Script for Windows
# This script automates the entire development environment setup

$ErrorActionPreference = "Stop"

# Colors
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Cyan "╔════════════════════════════════════════════════════════╗"
Write-ColorOutput Cyan "║     SentinAL Fraud Detection - Automated Setup        ║"
Write-ColorOutput Cyan "╚════════════════════════════════════════════════════════╝"
Write-Host ""

# Function to check if command exists
function Test-CommandExists {
    param($command)
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

# Step 1: Check prerequisites
Write-ColorOutput Yellow "`n📋 Step 1/8: Checking prerequisites..."

if (-not (Test-CommandExists git)) {
    Write-ColorOutput Red "❌ Git is not installed. Please install Git first."
    Write-ColorOutput Yellow "   Download from: https://git-scm.com/download/win"
    exit 1
}
Write-ColorOutput Green "✅ Git is installed"

if (-not (Test-CommandExists docker)) {
    Write-ColorOutput Red "❌ Docker is not installed. Please install Docker Desktop first."
    Write-ColorOutput Yellow "   Download from: https://www.docker.com/products/docker-desktop"
    exit 1
}
Write-ColorOutput Green "✅ Docker is installed"

if (-not (Test-CommandExists docker-compose)) {
    Write-ColorOutput Red "❌ Docker Compose is not installed."
    exit 1
}
Write-ColorOutput Green "✅ Docker Compose is installed"

# Step 2: Install Python
Write-ColorOutput Yellow "`n📋 Step 2/8: Setting up Python..."

if (-not (Test-CommandExists python)) {
    Write-ColorOutput Yellow "Python not found. Please install Python 3.11 from:"
    Write-ColorOutput Yellow "https://www.python.org/downloads/"
    Write-ColorOutput Yellow "Make sure to check 'Add Python to PATH' during installation"
    exit 1
}

$pythonVersion = python --version
Write-ColorOutput Green "✅ Python is ready: $pythonVersion"

# Step 3: Install Node.js
Write-ColorOutput Yellow "`n📋 Step 3/8: Setting up Node.js..."

if (-not (Test-CommandExists node)) {
    Write-ColorOutput Yellow "Node.js not found. Please install Node.js 20 from:"
    Write-ColorOutput Yellow "https://nodejs.org/"
    exit 1
}

$nodeVersion = node --version
Write-ColorOutput Green "✅ Node.js is ready: $nodeVersion"

# Step 4: Create Python virtual environment
Write-ColorOutput Yellow "`n📋 Step 4/8: Creating Python virtual environment..."

if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-ColorOutput Green "✅ Virtual environment created"
} else {
    Write-ColorOutput Green "✅ Virtual environment already exists"
}

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Step 5: Install Python dependencies
Write-ColorOutput Yellow "`n📋 Step 5/8: Installing Python dependencies..."

python -m pip install --upgrade pip
pip install -r python\requirements.txt
Write-ColorOutput Green "✅ Python dependencies installed"

# Step 6: Install Node.js dependencies
Write-ColorOutput Yellow "`n📋 Step 6/8: Installing Node.js dependencies..."

npm install
Write-ColorOutput Green "✅ Node.js dependencies installed"

# Step 7: Setup environment files
Write-ColorOutput Yellow "`n📋 Step 7/8: Setting up environment files..."

if (-not (Test-Path "python\.env")) {
    Copy-Item "python\.env.example" "python\.env"
    Write-ColorOutput Green "✅ Created python\.env from template"
    Write-ColorOutput Yellow "⚠️  Please update python\.env with your configuration"
} else {
    Write-ColorOutput Green "✅ python\.env already exists"
}

# Create necessary directories
New-Item -ItemType Directory -Force -Path "python\logs" | Out-Null
New-Item -ItemType Directory -Force -Path "python\data" | Out-Null
New-Item -ItemType Directory -Force -Path "python\models" | Out-Null
New-Item -ItemType Directory -Force -Path "torchserve\model-store" | Out-Null

# Step 8: Start Docker services
Write-ColorOutput Yellow "`n📋 Step 8/8: Starting Docker services..."

docker-compose up -d redis-master prometheus grafana

Write-ColorOutput Green "✅ Docker services started"

# Wait for services to be ready
Write-ColorOutput Cyan "`n⏳ Waiting for services to be ready..."
Start-Sleep -Seconds 5

# Check service health
Write-ColorOutput Cyan "`n🔍 Checking service health..."

try {
    $null = Invoke-WebRequest -Uri "http://localhost:9090/-/healthy" -UseBasicParsing -TimeoutSec 2
    Write-ColorOutput Green "✅ Prometheus is running"
} catch {
    Write-ColorOutput Yellow "⚠️  Prometheus may not be ready yet"
}

try {
    $null = Invoke-WebRequest -Uri "http://localhost:3001" -UseBasicParsing -TimeoutSec 2
    Write-ColorOutput Green "✅ Grafana is running"
} catch {
    Write-ColorOutput Yellow "⚠️  Grafana may not be ready yet"
}

# Print success message
Write-Host ""
Write-ColorOutput Green "╔════════════════════════════════════════════════════════╗"
Write-ColorOutput Green "║           ✅ Setup Complete! ✅                         ║"
Write-ColorOutput Green "╚════════════════════════════════════════════════════════╝"
Write-Host ""

Write-ColorOutput Cyan "📚 Next Steps:"
Write-Host ""
Write-Host "  1. Update configuration:"
Write-ColorOutput Yellow "     notepad python\.env"
Write-Host ""
Write-Host "  2. Start the API:"
Write-ColorOutput Yellow "     .\venv\Scripts\Activate.ps1"
Write-ColorOutput Yellow "     cd python"
Write-ColorOutput Yellow "     python api.py"
Write-Host ""
Write-Host "  3. Start the frontend (in a new terminal):"
Write-ColorOutput Yellow "     npm run dev"
Write-Host ""
Write-Host "  4. Access the application:"
Write-ColorOutput Green "     Frontend:    http://localhost:5173"
Write-ColorOutput Green "     API Docs:    http://localhost:8000/docs"
Write-ColorOutput Green "     Grafana:     http://localhost:3001 (admin/SentinAL_Grafana_2024!)"
Write-ColorOutput Green "     Prometheus:  http://localhost:9090"
Write-ColorOutput Green "     Jaeger:      http://localhost:16686"
Write-Host ""
Write-ColorOutput Cyan "For more information, see README.md"
Write-ColorOutput Cyan "Report issues: https://github.com/Aftab0khan021/sentinal-fraud-detection/issues"
Write-Host ""
Write-ColorOutput Green "Happy coding!"
