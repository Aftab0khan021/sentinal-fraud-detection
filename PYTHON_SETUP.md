# Python 3.11 Installation & Setup Guide

## Step 1: Download Python 3.11

1. Go to: https://www.python.org/downloads/release/python-31110/
2. Scroll down to "Files" section
3. Download: **Windows installer (64-bit)** - `python-3.11.10-amd64.exe`

## Step 2: Install Python 3.11

1. Run the downloaded installer
2. ⚠️ **IMPORTANT:** Check ✅ "Add python.exe to PATH"
3. Click "Install Now"
4. Wait for installation to complete
5. Click "Close"

## Step 3: Verify Installation

Open a NEW PowerShell window and run:

```powershell
py -3.11 --version
```

Expected output: `Python 3.11.10`

## Step 4: Create Virtual Environment

```powershell
# Navigate to project directory
cd C:\Users\HP-PC\project\sentinal-fraud-detection\python

# Create virtual environment with Python 3.11
py -3.11 -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

You should see `(venv)` in your prompt.

## Step 5: Install Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

## Step 6: Verify Installation

```powershell
# Check Python version in venv
python --version
# Should show: Python 3.11.x

# Run tests
pytest tests/ -v

# Check coverage
pytest --cov=. --cov-report=term
```

## Step 7: Install Pre-commit Hooks

```powershell
pre-commit install
```

## Troubleshooting

### If "py -3.11" doesn't work:
- Close and reopen PowerShell
- Make sure you checked "Add to PATH" during installation
- Try: `python3.11 --version` or `python --version`

### If activation fails:
```powershell
# Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### If pip install fails:
```powershell
# Try with --user flag
pip install --user -r requirements.txt
```

## Quick Setup Script

Alternatively, run the automated setup script:

```powershell
cd C:\Users\HP-PC\project\sentinal-fraud-detection\python
.\setup.ps1
```

---

**After setup, you can:**
- Run tests: `pytest tests/ -v`
- Check coverage: `pytest --cov=. --cov-report=html`
- Format code: `black python/`
- Run linters: `flake8 python/`
- Start API: `python api.py`
