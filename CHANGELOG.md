# Changelog

All notable changes to Screen Automator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-11-09

### 🎉 Major Release - Modern API

This release represents a major refactoring focused on simplicity, reliability, and developer experience.

### Added

#### Modern API Framework
- **`src/modern_api.py`** - New unified framework interface
  - `create_framework()` - Primary entry point for all automation
  - `ScreenAutomatorFramework` class - Clean, comprehensive API wrapper
  - Auto-waiting built into all operations
  - Expectations as default assertions
  - Rule monitoring integration

#### Framework Features
- **`src/actionability.py`** - Auto-waiting and stability checks
  - Playwright-style condition-based waiting
  - Stability checks before clicking (prevent clicks on animating elements)
  - Configurable polling intervals and timeouts
  - `AutoWaiter` and `SmartAutomator` classes

- **`src/expectations.py`** - Auto-retrying assertions
  - `expect()` function for fluent assertions
  - Auto-retry until timeout (eliminates race conditions)
  - Support for images, windows, and state expectations
  - Clear error messages with retry history

- **`src/page_objects.py`** - Page Object Model implementation
  - `BasePage` and `BaseDialog` base classes
  - `Element` class with locator abstraction
  - Support for image-based and property-based locators
  - Element hierarchies and relative locators

- **`src/data_driven.py`** - Data-driven testing support
  - `DataProvider` for CSV, JSON, XML test data
  - `DataDrivenTest` base class for parameterized tests
  - `ConfigManager` for environment-specific configurations
  - Iterator interface for clean test loops

#### Developer Tools
- **Poetry** - Modern dependency management
  - `pyproject.toml` with complete dependency specification
  - Separate dev dependencies
  - Python 3.9+ requirement

- **Code Quality Tools**
  - Black formatting (line length: 100)
  - isort for import sorting
  - Flake8 for linting
  - **Ruff** - Fast Python linter (304 auto-fixes applied)
  - **Pylint** - Comprehensive code analysis (9.16/10 score on new modules)
  - mypy for type checking
  - Bandit for security scanning
  - Safety for dependency security

- **Pre-commit Hooks**
  - `.pre-commit-config.yaml` with all quality checks
  - Automatic formatting before commits
  - Security scanning

- **CI/CD Pipeline**
  - `.github/workflows/main.yaml` - Comprehensive GitHub Actions workflow
  - Multi-platform testing (Linux, Windows, macOS)
  - Multi-version testing (Python 3.9-3.12)
  - Automated quality checks
  - Coverage reporting

#### Documentation
- **FRAMEWORK_GUIDE.md** - Complete guide to modern API (403 lines)
  - Quick start examples
  - Core concepts (auto-waiting, expectations)
  - API reference
  - Advanced features
  - Best practices
  - Troubleshooting

- **QUICK_REFERENCE.md** - One-page API cheat sheet (204 lines)
  - Modern API patterns
  - Common usage examples
  - Setup commands

- **README.md** - Updated with modern API focus
  - Quick start at top
  - Feature highlights
  - Clear modern API examples

- **examples/modern_api_usage.py** - 6 comprehensive examples
  - Basic usage
  - Robust expectations
  - Rule monitoring
  - Waiting patterns
  - Configuration
  - Complete workflows

#### Configuration
- **`.flake8`** - Linting configuration
- **`.gitignore`** - Proper Python .gitignore
- **`.pre-commit-config.yaml`** - Pre-commit hook configuration

### Changed

- **Python requirement** - Now requires Python 3.9+ (was 3.8+)
  - Required for flake8 >=7.0 compatibility
  - Updated in pyproject.toml and mypy config

- **Import structure** - Polished for developer experience
  - `from src import create_framework` - Clean top-level import
  - `from src.modern_api import create_framework` - Explicit import
  - Added `__all__` exports to src/__init__.py

- **Code formatting** - All code now follows Black style
  - 44 files reformatted
  - Consistent 100-character line length
  - Proper import sorting with isort

- **Test organization** - Moved all test files to tests/ directory
  - 12 test files relocated from root
  - Cleaner project structure

### Removed

#### Documentation Cleanup (74% reduction)
- **Removed 5 documentation files** (-58.4KB):
  - `IMPROVEMENT_BLUEPRINT_IMPLEMENTATION.md` (-18KB, 646 lines)
  - `MIGRATION_GUIDE.md` (-11KB, 468 lines)
  - `WINDOW_MANAGEMENT.md` (-12KB, 424 lines)
  - `WINDOW_TARGETING.md` (-4.4KB, 99 lines)
  - `TESTING_REPORT.md` (-6.9KB, 220 lines)

- **Rewrote FRAMEWORK_GUIDE.md**
  - From 979 lines to 403 lines (59% reduction)
  - Removed all old pattern examples
  - Focused exclusively on modern API

- **Rewrote QUICK_REFERENCE.md**
  - From ~500 lines to 204 lines (60% reduction)
  - Removed old pattern documentation

- **Slimmed README.md**
  - Removed verbose old pattern examples
  - Focused on modern API quick start

- **Removed example files**:
  - `examples/framework_demo.py` (replaced by modern_api_usage.py)
  - `examples/integration_example.py` (consolidated into modern_api_usage.py)

#### Code Cleanup
- **Removed debug files**:
  - `debug_claudedone.py`
  - `run_tests.py`
  - `__pycache__/__init__.cpython-311.pyc` (removed from git tracking)

#### Old Patterns Removed
- No longer documenting or supporting old patterns:
  - Direct `ScreenAutomator()` instantiation (use `create_framework()`)
  - Manual `time.sleep()` calls (use auto-waiting)
  - Direct assertions (use expectations)
  - Scattered imports (use unified framework)

### Deprecated

- **Old API patterns** - Still functional but no longer documented:
  - `ScreenAutomator()` - Use `create_framework()` instead
  - Manual waiting with `time.sleep()` - Use framework auto-waiting
  - Direct `find_image()` + assert - Use `expect_image()`
  - Scattered component imports - Use unified framework

### Migration Guide

For users upgrading from version 1.x:

#### Old Pattern
```python
from src.automator import ScreenAutomator
import time

automator = ScreenAutomator()
time.sleep(5)
location = automator.image_detector.find_image("button.png")
assert location is not None
```

#### Modern Pattern
```python
from src import create_framework

framework = create_framework(timeout=10000)
framework.click_image("button.png")  # Auto-waits!
framework.expect_image("success.png", timeout=5000)  # Auto-retries!
```

### Breaking Changes

- **Python 3.8 no longer supported** - Minimum version is now Python 3.9
- **Old documentation removed** - Only modern API is documented
- **Import paths changed** - Recommended import is now `from src import create_framework`

### Technical Details

- **Dependencies**: 110 packages installed via Poetry
- **Code formatting**: 44 files reformatted with Black
- **Documentation**: Reduced from 79KB to 20.6KB (74% reduction, 3,339→906 lines)
- **Test files**: Organized into tests/ directory
- **Quality tools**: black, isort, flake8, mypy, bandit, safety, pre-commit

### Why Version 2.0.0?

This is a major version bump because:
1. **Breaking changes** - Python 3.8 support dropped
2. **API paradigm shift** - Modern API is now the primary interface
3. **Documentation rewrite** - Complete focus on modern patterns
4. **Massive cleanup** - 74% documentation reduction, code reorganization

### Credits

This release focused on:
- **Simplicity** - One clear way to do everything
- **Reliability** - Auto-waiting eliminates flaky tests
- **Developer Experience** - Clean API, great documentation
- **Code Quality** - Professional tooling and CI/CD

---

## [0.1.0] - Previous

Initial release with core functionality.
