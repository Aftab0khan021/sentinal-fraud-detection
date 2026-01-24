# Contributing to SentinAL

Thank you for your interest in contributing to SentinAL! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/sentinal-fraud-detection.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Submit a pull request

## 📋 Code Style

### Python

- **Formatting:** Use Black with 100 character line length
- **Import Sorting:** Use isort with Black profile
- **Linting:** Code must pass Flake8 and Pylint checks
- **Type Hints:** Add type hints to function signatures where applicable

```python
def function_name(param: str) -> int:
    """Function description."""
    return len(param)
```

### TypeScript/React

- **Formatting:** Use Prettier with 2-space indentation
- **Linting:** Code must pass ESLint checks
- **Components:** Use functional components with hooks

## 🧪 Testing Requirements

### All Code Changes Must Include Tests

- **Unit Tests:** For new functions/classes
- **Integration Tests:** For new features
- **Coverage:** Maintain 80%+ code coverage

### Running Tests

```bash
# Python tests
cd python
pytest tests/ -v --cov=.

# Frontend tests
npm test
```

## 📝 Commit Messages

Use conventional commit format:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): add JWT authentication
fix(gnn): correct class weight calculation
docs(readme): update installation instructions
```

## 🔍 Pull Request Process

1. **Update Documentation:** Update README.md, TESTING.md, or other docs if needed
2. **Add Tests:** Ensure all new code has tests
3. **Run Tests:** All tests must pass
4. **Run Linters:** Code must pass all quality checks
5. **Update Changelog:** Add entry to CHANGELOG.md (if exists)
6. **Request Review:** Tag maintainers for review

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No merge conflicts
- [ ] CI/CD pipeline passes

## 🐛 Reporting Bugs

### Bug Report Template

```markdown
**Describe the bug**
A clear description of the bug.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g., Windows 11]
 - Python Version: [e.g., 3.11]
 - Browser: [e.g., Chrome 120]
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Any alternative solutions or features.

**Additional context**
Any other context or screenshots.
```

## 🔐 Security

**Do not** open public issues for security vulnerabilities. Instead, email security@sentinal.ai (or contact maintainers privately).

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Your contributions make SentinAL better for everyone!
