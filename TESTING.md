# Testing Guide - SentinAL Fraud Detection

## 📋 Overview

This document describes the testing infrastructure for the SentinAL fraud detection system, including unit tests, integration tests, E2E tests, and code quality tools.

---

## 🧪 Test Suite

### Test Coverage

- **Unit Tests:** 40+ test cases covering all core modules
- **Integration Tests:** End-to-end pipeline testing
- **E2E Tests:** Complete user workflow testing
- **Target Coverage:** 80%+

### Test Files

```
python/tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── test_auth.py             # Authentication tests (7 tests)
├── test_api.py              # API integration tests (13 tests)
├── test_data_gen.py         # Data generation tests (14 tests)
├── test_gnn_train.py        # GNN training tests (9 tests)
├── test_agent_explainer.py  # Agent explainer tests (6 tests)
├── test_models.py           # Pydantic model tests (10 tests)
└── test_logging.py          # Logging tests (5 tests)
```

---

## 🚀 Running Tests

### Run All Tests

```bash
cd python
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_auth.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=. --cov-report=html --cov-report=term
```

### Run Specific Test Class

```bash
pytest tests/test_data_gen.py::TestFinancialGraphGenerator -v
```

### Run Specific Test

```bash
pytest tests/test_auth.py::test_create_access_token -v
```

### Run Tests by Marker

```bash
# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

---

## 📊 Coverage Reports

### Generate HTML Coverage Report

```bash
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

### Generate Terminal Coverage Report

```bash
pytest --cov=. --cov-report=term-missing
```

### Coverage Configuration

Coverage settings are in `pyproject.toml`:
- **Target:** 80% coverage
- **Excludes:** Test files, venv, __pycache__
- **Reports:** HTML, XML, Terminal

---

## 🔧 Code Quality Tools

### Black (Code Formatting)

```bash
# Check formatting
black python/ --check

# Auto-format code
black python/

# Format specific file
black python/api.py
```

### isort (Import Sorting)

```bash
# Check imports
isort python/ --check-only

# Auto-sort imports
isort python/

# Sort specific file
isort python/api.py
```

### Flake8 (Linting)

```bash
# Run flake8
flake8 python/

# Check specific file
flake8 python/api.py
```

### Pylint (Advanced Linting)

```bash
# Run pylint
pylint python/*.py

# Check specific file
pylint python/api.py

# Disable specific warnings
pylint python/api.py --disable=C0111
```

### MyPy (Type Checking)

```bash
# Run mypy
mypy python/

# Check specific file
mypy python/api.py
```

---

## 🎨 Frontend Code Quality

### ESLint

```bash
# Run ESLint
npm run lint

# Auto-fix issues
npm run lint -- --fix
```

### Prettier

```bash
# Check formatting
npx prettier --check "src/**/*.{ts,tsx}"

# Auto-format
npx prettier --write "src/**/*.{ts,tsx}"
```

---

## 🔄 Pre-commit Hooks

### Install Pre-commit

```bash
pip install pre-commit
pre-commit install
```

### Run Pre-commit Manually

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files
pre-commit run
```

### Skip Pre-commit (Not Recommended)

```bash
git commit --no-verify -m "message"
```

---

## 🤖 CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline runs automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

### Pipeline Jobs

1. **test-python:** Run tests on Python 3.9, 3.10, 3.11
2. **lint-python:** Check code formatting and linting
3. **security-scan:** Run safety and bandit scans
4. **test-frontend:** Build and lint frontend
5. **integration-tests:** Run integration tests

### View Pipeline Status

- Check GitHub Actions tab in repository
- Status badges in README.md

---

## 📝 Writing Tests

### Unit Test Template

```python
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from module_name import FunctionToTest


class TestClassName:
    """Test suite for ClassName"""
    
    def test_function_name(self):
        """Test description"""
        # Arrange
        input_data = "test"
        
        # Act
        result = FunctionToTest(input_data)
        
        # Assert
        assert result == expected_output
```

### Using Fixtures

```python
@pytest.fixture
def sample_data():
    """Create sample data for testing"""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Test using fixture"""
    assert sample_data["key"] == "value"
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch

def test_with_mock():
    """Test with mocked dependency"""
    with patch('module.external_function') as mock_func:
        mock_func.return_value = "mocked"
        result = function_that_calls_external()
        assert result == "mocked"
```

---

## 🐛 Debugging Tests

### Run Tests in Verbose Mode

```bash
pytest tests/ -vv
```

### Show Print Statements

```bash
pytest tests/ -s
```

### Stop on First Failure

```bash
pytest tests/ -x
```

### Run Last Failed Tests

```bash
pytest tests/ --lf
```

### Drop into Debugger on Failure

```bash
pytest tests/ --pdb
```

---

## 📈 Performance Testing

### Benchmark Tests

```python
import pytest

@pytest.mark.benchmark
def test_performance(benchmark):
    """Benchmark test"""
    result = benchmark(function_to_test, arg1, arg2)
    assert result is not None
```

### Run Benchmarks

```bash
pytest tests/ --benchmark-only
```

---

## 🔒 Security Testing

### Run Safety Check

```bash
cd python
safety check --file requirements.txt
```

### Run Bandit Scan

```bash
bandit -r python/ -f screen
```

### Generate Security Report

```bash
bandit -r python/ -f json -o security-report.json
```

---

## ✅ Test Checklist

Before committing code:

- [ ] All tests pass locally
- [ ] Coverage is above 80%
- [ ] Code formatted with Black
- [ ] Imports sorted with isort
- [ ] No Flake8 errors
- [ ] No Pylint critical errors
- [ ] Type hints added (where applicable)
- [ ] Pre-commit hooks pass
- [ ] Documentation updated

---

## 🆘 Troubleshooting

### Tests Failing

**Issue:** Import errors
```bash
# Solution: Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

**Issue:** Module not found
```bash
# Solution: Install in development mode
pip install -e .
```

### Coverage Not Updating

```bash
# Clear coverage cache
rm -rf .coverage htmlcov/

# Run tests again
pytest --cov=. --cov-report=html
```

### Pre-commit Hooks Failing

```bash
# Update hooks
pre-commit autoupdate

# Clear cache
pre-commit clean

# Reinstall
pre-commit install --install-hooks
```

---

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Black Documentation](https://black.readthedocs.io/)
- [Pylint Documentation](https://pylint.readthedocs.io/)
- [Pre-commit Documentation](https://pre-commit.com/)

---

**Happy Testing!** 🎉
