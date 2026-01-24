# ============================================
# SentinAL Automated Setup Script
# ============================================
# This script automates the entire setup process after Python 3.11 is installed
# 
# Prerequisites: Python 3.11 must be installed with "Add to PATH" checked
#
# Usage: .\automated_setup.ps1
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SentinAL Automated Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python 3.11
Write-Host "[1/7] Checking for Python 3.11..." -ForegroundColor Yellow
try {
    $pythonVersion = py -3.11 --version 2>&1
    if ($pythonVersion -match "Python 3\.11") {
        Write-Host "      ✓ Python 3.11 found: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "      ✗ Python 3.11 not found!" -ForegroundColor Red
        Write-Host "      Please install Python 3.11 first:" -ForegroundColor Yellow
        Write-Host "      https://www.python.org/ftp/python/3.11.10/python-3.11.10-amd64.exe" -ForegroundColor White
        exit 1
    }
} catch {
    Write-Host "      ✗ Python 3.11 not found!" -ForegroundColor Red
    Write-Host "      Please install Python 3.11 first" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Step 2: Remove old venv if exists
Write-Host "[2/7] Cleaning up old virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Remove-Item -Recurse -Force "venv"
    Write-Host "      ✓ Removed old venv" -ForegroundColor Green
} else {
    Write-Host "      ✓ No old venv found" -ForegroundColor Green
}

Write-Host ""

# Step 3: Create new virtual environment
Write-Host "[3/7] Creating Python 3.11 virtual environment..." -ForegroundColor Yellow
py -3.11 -m venv venv
if ($LASTEXITCODE -eq 0) {
    Write-Host "      ✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "      ✗ Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 4: Activate virtual environment
Write-Host "[4/7] Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
Write-Host "      ✓ Virtual environment activated" -ForegroundColor Green

Write-Host ""

# Step 5: Upgrade pip
Write-Host "[5/7] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "      ✓ pip upgraded" -ForegroundColor Green
} else {
    Write-Host "      ⚠ pip upgrade had issues (continuing anyway)" -ForegroundColor Yellow
}

Write-Host ""

# Step 6: Install production dependencies
Write-Host "[6/7] Installing production dependencies..." -ForegroundColor Yellow
Write-Host "      This may take 5-10 minutes..." -ForegroundColor Gray
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "      ✓ Production dependencies installed" -ForegroundColor Green
} else {
    Write-Host "      ✗ Failed to install production dependencies" -ForegroundColor Red
    Write-Host "      Check the error messages above" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Step 7: Install development dependencies
Write-Host "[7/7] Installing development dependencies..." -ForegroundColor Yellow
pip install -r requirements-dev.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "      ✓ Development dependencies installed" -ForegroundColor Green
} else {
    Write-Host "      ⚠ Some dev dependencies failed (continuing)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete! ✓" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verify installation
Write-Host "Verification:" -ForegroundColor Yellow
Write-Host "  Python version: " -NoNewline
python --version
Write-Host "  Pip version: " -NoNewline
pip --version
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Run tests:           pytest tests/ -v" -ForegroundColor White
Write-Host "  2. Check coverage:      pytest --cov=. --cov-report=html" -ForegroundColor White
Write-Host "  3. Install pre-commit:  pre-commit install" -ForegroundColor White
Write-Host "  4. Start API:           python api.py" -ForegroundColor White
Write-Host ""

Write-Host "To activate venv in future sessions:" -ForegroundColor Yellow
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""

# Optional: Run a quick test
Write-Host "Would you like to run a quick test now? (Y/N): " -ForegroundColor Yellow -NoNewline
$response = Read-Host
if ($response -eq "Y" -or $response -eq "y") {
    Write-Host ""
    Write-Host "Running quick test..." -ForegroundColor Yellow
    pytest tests/test_auth.py -v
}

Write-Host ""
Write-Host "Setup script completed successfully!" -ForegroundColor Green
Write-Host ""
