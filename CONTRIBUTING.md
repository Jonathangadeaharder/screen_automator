# Contributing to Screen Automator

Thank you for your interest in contributing to Screen Automator! This guide will help you get started with development, testing, and submitting changes.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for everyone. We expect all contributors to:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, trolling, or insulting comments
- Personal or political attacks
- Publishing others' private information
- Any conduct inappropriate in a professional setting

### Reporting

If you experience or witness unacceptable behavior, please report it by opening an issue or contacting the project maintainers.

---

## Getting Started

### Prerequisites

- **Python**: 3.9 or higher
- **Git**: For version control
- **Poetry** (optional): For dependency management
- **IDE**: VSCode, PyCharm, or similar with Python support

### Installation

1. **Fork the repository**
   ```bash
   # On GitHub, click "Fork" button
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR-USERNAME/screen_automator.git
   cd screen_automator
   ```

3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/ORIGINAL-OWNER/screen_automator.git
   ```

4. **Install dependencies**

   **Option A: Using Poetry (Recommended)**
   ```bash
   # Install Poetry
   curl -sSL https://install.python-poetry.org | python3 -

   # Install all dependencies including dev tools
   poetry install --with dev

   # Activate virtual environment
   poetry shell
   ```

   **Option B: Using pip**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

5. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

6. **Verify installation**
   ```bash
   # Run tests
   pytest

   # Run type checking
   mypy src/

   # Run linter
   ruff check src/
   ```

---

## Development Setup

### IDE Configuration

#### VSCode

**Recommended Extensions:**
- Python (Microsoft)
- Pylance
- Python Test Explorer
- Ruff
- mypy

**.vscode/settings.json:**
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.linting.mypyEnabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "editor.formatOnSave": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

#### PyCharm

1. **Enable pytest**: Settings → Tools → Python Integrated Tools → Default test runner → pytest
2. **Enable mypy**: Settings → Tools → External Tools → Add mypy
3. **Enable Ruff**: Settings → Tools → External Tools → Add ruff

### Environment Variables

Create `.env` file for local development (not committed):

```bash
# Development mode
DEBUG=true

# Test configuration
PYTEST_TIMEOUT=30

# Logging
LOG_LEVEL=DEBUG
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

**Branch Naming Convention:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test improvements
- `chore/` - Maintenance tasks

### 2. Make Changes

- Write code following [Code Standards](#code-standards)
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### 3. Run Quality Checks

```bash
# Run all checks
./run_checks.sh

# Or run individually:
pytest                  # Tests
mypy src/              # Type checking
ruff check src/        # Linting
black src/             # Format code
bandit -r src/         # Security scan
```

### 4. Commit Changes

Follow [Commit Guidelines](#commit-guidelines):

```bash
git add .
git commit -m "feat: add auto-retry for image detection"
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

---

## Code Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

- **Line Length**: 100 characters (not 79)
- **Quotes**: Prefer double quotes `"` over single `'`
- **Imports**: Organized using isort
- **Formatting**: Automated with Black

### Type Hints

**All public functions must have type hints:**

```python
# ✅ Good
def wait_for_image(
    self,
    image_path: str,
    automator: Any,
    timeout: Optional[int] = None
) -> tuple[int, int, int, int]:
    """Wait for an image to appear on screen."""
    ...

# ❌ Bad
def wait_for_image(self, image_path, automator, timeout=None):
    ...
```

### Docstrings

Use **Google-style docstrings**:

```python
def complex_function(param1: int, param2: str) -> bool:
    """
    Brief one-line description.

    Longer description if needed. Explain the purpose, behavior,
    and any important details.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is negative
        TimeoutError: When operation times out

    Example:
        >>> result = complex_function(42, "test")
        >>> print(result)
        True
    """
    ...
```

### Code Organization

```python
# 1. Standard library imports
import os
import sys
from typing import Optional, Any

# 2. Third-party imports
import cv2
import numpy as np

# 3. Local imports
from src.image_detector import ImageDetector
from src.exceptions import TimeoutError

# 4. Constants
DEFAULT_TIMEOUT = 10000
POLL_INTERVAL = 50

# 5. Classes and functions
class MyClass:
    ...

def my_function():
    ...
```

### Error Handling

**Be specific with exceptions:**

```python
# ✅ Good
try:
    result = detector.find_image(path)
except FileNotFoundError as e:
    logger.error(f"Image file not found: {path}")
    raise ImageNotFoundError(f"Cannot find template: {path}") from e
except cv2.error as e:
    logger.error(f"OpenCV error: {e}")
    raise ImageDetectionError(f"Failed to process image: {path}") from e

# ❌ Bad
try:
    result = detector.find_image(path)
except Exception as e:
    print("Something went wrong")
    pass
```

### Logging

Use the logging module:

```python
import logging

logger = logging.getLogger(__name__)

# Log at appropriate levels
logger.debug("Searching for image: %s", image_path)
logger.info("Image found at (%d, %d)", x, y)
logger.warning("Image confidence low: %.2f", confidence)
logger.error("Failed to find image: %s", image_path)
logger.critical("System failure: %s", error)
```

---

## Testing Guidelines

### Test Requirements

**All contributions must include tests:**

- New features: Add tests demonstrating functionality
- Bug fixes: Add test reproducing the bug
- Refactoring: Ensure existing tests still pass
- Target: Maintain ≥70% code coverage

### Writing Tests

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for comprehensive testing documentation.

**Quick checklist:**

- [ ] Test file named `test_*.py`
- [ ] Test functions named `test_*`
- [ ] Descriptive test names
- [ ] Arrange-Act-Assert pattern
- [ ] Use fixtures for setup
- [ ] Mock external dependencies
- [ ] Test both success and failure cases
- [ ] Fast execution (<1s per test)

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_expectations.py

# With coverage
pytest --cov=src --cov-report=html

# Fast parallel execution
pytest -n auto

# Watch mode (requires pytest-watch)
pytest-watch
```

---

## Commit Guidelines

### Commit Message Format

We use **Conventional Commits**:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

**Examples:**

```
feat(expectations): add support for text-based expectations

Implement TextExpectation class for property-based automation.
Supports waiting for specific text to appear or disappear.

Closes #123
```

```
fix(actionability): resolve stability check timeout issue

Stability checks were timing out due to incorrect duration
calculation. Fixed by using milliseconds consistently.

Fixes #456
```

```
docs: update ARCHITECTURE.md with protocol pattern explanation

Added section explaining how Protocols are used to avoid
circular dependencies in GUI components.
```

### Commit Best Practices

1. **Atomic commits**: One logical change per commit
2. **Present tense**: "Add feature" not "Added feature"
3. **Imperative mood**: "Fix bug" not "Fixes bug"
4. **Reference issues**: Include issue numbers
5. **Explain why**: Not just what changed

```bash
# ✅ Good commit history
feat: add image caching for faster detection
fix: handle None return from find_image
docs: update API examples
test: add tests for edge cases

# ❌ Bad commit history
WIP
fix stuff
asdf
updated code
```

---

## Pull Request Process

### Before Submitting

Ensure your PR:

- [ ] Follows code standards
- [ ] Includes tests
- [ ] Passes all CI checks
- [ ] Updates relevant documentation
- [ ] Has descriptive commit messages
- [ ] Is based on latest main branch

### PR Template

When creating a PR, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added
- [ ] All tests passing
- [ ] No new warnings
```

### Review Process

1. **Automated Checks**: CI runs tests, linters, type checking
2. **Code Review**: Maintainer reviews code
3. **Feedback**: Address any comments or requested changes
4. **Approval**: Once approved, maintainer will merge

### Review Response Time

- Initial response: Within 3-5 days
- Follow-up: Within 2-3 days
- Merge: After approval and CI passes

---

## Code Review Guidelines

### For Contributors

When responding to reviews:

- Be receptive to feedback
- Ask questions if unclear
- Make requested changes
- Respond to each comment
- Mark conversations as resolved

### For Reviewers

When reviewing code:

- Be respectful and constructive
- Explain your reasoning
- Suggest improvements, don't demand
- Focus on code, not the person
- Approve when ready

**Review Checklist:**

- [ ] Code is clear and maintainable
- [ ] Tests cover new functionality
- [ ] Documentation is updated
- [ ] No unnecessary complexity
- [ ] Follows project standards
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed

---

## Release Process

### Versioning

We use **Semantic Versioning** (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. **Update Version**
   ```python
   # pyproject.toml
   [tool.poetry]
   version = "2.3.0"
   ```

2. **Update CHANGELOG.md**
   ```markdown
   ## [2.3.0] - 2025-11-10

   ### Added
   - New feature X

   ### Fixed
   - Bug Y

   ### Changed
   - Improvement Z
   ```

3. **Run Full Test Suite**
   ```bash
   pytest --cov=src
   mypy src/
   ruff check src/
   bandit -r src/
   ```

4. **Create Release Tag**
   ```bash
   git tag -a v2.3.0 -m "Release version 2.3.0"
   git push origin v2.3.0
   ```

5. **Create GitHub Release**
   - Go to GitHub Releases
   - Create new release from tag
   - Copy CHANGELOG entry
   - Upload artifacts if needed

---

## Common Tasks

### Adding a New Module

1. Create file: `src/new_module.py`
2. Add type hints and docstrings
3. Create test file: `tests/test_new_module.py`
4. Update `src/__init__.py` if needed
5. Document in appropriate guides

### Adding a New Dependency

```bash
# Using Poetry
poetry add package-name

# Using pip
pip install package-name
# Then update requirements.txt
pip freeze > requirements.txt
```

**Dependency Guidelines:**
- Only add if truly necessary
- Prefer pure Python libraries
- Check license compatibility
- Consider package size and maintenance

### Fixing a Bug

1. Create issue describing bug
2. Write failing test reproducing bug
3. Fix the bug
4. Verify test now passes
5. Submit PR with reference to issue

### Improving Documentation

- Keep documentation up-to-date
- Use clear, simple language
- Include code examples
- Add diagrams where helpful
- Check for broken links

---

## Getting Help

### Resources

- **Documentation**: [README.md](README.md), [ARCHITECTURE.md](ARCHITECTURE.md), [TESTING_GUIDE.md](TESTING_GUIDE.md)
- **Examples**: [examples/](examples/) directory
- **API Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Issues**: [GitHub Issues](https://github.com/owner/screen_automator/issues)

### Communication Channels

- **Bug Reports**: Open GitHub issue with "bug" label
- **Feature Requests**: Open GitHub issue with "enhancement" label
- **Questions**: Open GitHub issue with "question" label
- **Discussions**: Use GitHub Discussions for general topics

### Issue Templates

When reporting bugs, include:

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. ...

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: Windows 10
- Python: 3.10
- Version: 2.2.0

## Additional Context
Screenshots, logs, etc.
```

---

## Recognition

### Contributors

All contributors are listed in:
- GitHub Contributors page
- CHANGELOG.md (for significant contributions)
- Special thanks in release notes

### Hall of Fame

Contributors who make exceptional contributions may be recognized with:
- Maintainer status
- Special mention in documentation
- Community spotlight

---

## License

By contributing to Screen Automator, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE) file).

---

## Questions?

If you have questions not covered in this guide:

1. Check existing documentation
2. Search closed issues
3. Open a new issue with "question" label

We're here to help and appreciate your contributions!

---

*Last Updated: 2025-11-10*
*Version: 2.3.0*

**Thank you for contributing to Screen Automator! 🎉**
