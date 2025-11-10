# Testing Guide

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Organization](#test-organization)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Testing Patterns](#testing-patterns)
- [Mocking Strategies](#mocking-strategies)
- [Test Coverage](#test-coverage)
- [Continuous Integration](#continuous-integration)

---

## Testing Philosophy

### Why Test?

Screen Automator has **111 comprehensive tests** ensuring:

1. **Reliability**: Code works as expected
2. **Refactoring Safety**: Change code with confidence
3. **Documentation**: Tests show how to use the API
4. **Regression Prevention**: Catch breaks early

### Test Pyramid

```
        ┌──────────────┐
        │   Manual     │  ← Rare: GUI smoke tests
        │              │
        ├──────────────┤
        │ Integration  │  ← Some: Full workflow tests
        │              │
        ├──────────────┤
        │              │
        │     Unit     │  ← Most: Fast, isolated tests
        │              │
        └──────────────┘
```

**Our Distribution:**
- **Unit Tests**: ~85% (fast, isolated, numerous)
- **Integration Tests**: ~15% (slower, full workflows)
- **Manual Tests**: Minimal (GUI validation only)

---

## Test Organization

### Directory Structure

```
tests/
├── test_expectations.py       # 44 tests - Expectations framework
├── test_actionability.py      # 39 tests - Auto-waiting & stability
├── test_page_objects.py       # 28 tests - Page Object Model
├── test_basic.py              # Basic image detection
├── test_modern_api.py         # Modern API integration
├── test_rule_manager.py       # Rule CRUD operations
├── test_window_management.py  # Window operations
├── test_image_detection.py    # Image matching
├── test_gui_smoke.py          # GUI smoke tests
└── conftest.py                # Shared fixtures
```

### Test Files

Each test file follows a consistent structure:

```python
"""
Module docstring explaining what is being tested
"""

# Imports
import pytest
from unittest.mock import Mock, MagicMock
from src.module import ClassToTest

# Mock setup (if needed for display-dependent code)
sys.modules["pyautogui"] = MagicMock()

# Fixtures
@pytest.fixture
def subject():
    """Fixture docstring"""
    return ClassToTest()

# Test sections with clear headers
# ============================================================================
# Section Name - Method Being Tested
# ============================================================================

def test_descriptive_name(subject, other_fixtures):
    """Test one specific behavior"""
    # Arrange
    setup_code()

    # Act
    result = subject.method()

    # Assert
    assert result == expected
```

---

## Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_expectations.py

# Run specific test
pytest tests/test_expectations.py::test_expect_returns_image_expectation

# Run tests matching pattern
pytest -k "image"

# Run with coverage
pytest --cov=src --cov-report=html

# Run in parallel (faster)
pytest -n auto
```

### Configuration

Tests are configured in `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
markers =
    slow: marks tests as slow
    gui: marks tests requiring GUI
    integration: marks integration tests
```

### Environment Setup

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-xdist pytest-mock

# Or with poetry
poetry install --with dev

# Run tests
pytest
```

---

## Writing Tests

### Test Naming Convention

```python
# ✅ Good: Descriptive, specific
def test_expect_returns_image_expectation_for_automator():
    """Test expect() returns ImageExpectation when subject has find_image."""

def test_wait_for_image_retries_until_found():
    """Test wait_for_image() polls until image appears."""

# ❌ Bad: Vague, unclear
def test_expect():
    """Test expect"""

def test_image():
    """Test image stuff"""
```

### Arrange-Act-Assert Pattern

```python
def test_click_image_with_auto_wait(smart_automator, mock_detector):
    """Test click_image() waits for image before clicking."""

    # Arrange - Set up test data and mocks
    mock_detector.find_image.return_value = (100, 200, 50, 50)
    expected_center = (125, 225)  # Center of found image

    # Act - Execute the code under test
    smart_automator.click_image("button.png")

    # Assert - Verify the outcome
    mock_detector.find_image.assert_called_once_with("button.png")
    # Could also check pyautogui.click was called with expected_center
```

### Fixture Usage

**Define fixtures once, use everywhere:**

```python
# conftest.py or test file
@pytest.fixture
def mock_automator():
    """Create a mock automator with find_image method."""
    automator = Mock()
    automator.find_image = Mock(return_value=(100, 200, 50, 50))
    return automator

@pytest.fixture
def auto_waiter():
    """Create AutoWaiter with short timeout for fast tests."""
    return AutoWaiter(timeout=2000, poll_interval=50)

# Use in tests
def test_something(mock_automator, auto_waiter):
    result = auto_waiter.wait_for_image("test.png", mock_automator)
    assert result is not None
```

### Parameterized Tests

Test multiple scenarios efficiently:

```python
@pytest.mark.parametrize("input,expected", [
    (0, False),
    (1, False),
    (2, True),
    (3, True),
    (4, False),  # Not prime: 2*2
])
def test_is_prime(input, expected):
    """Test is_prime() with various inputs."""
    assert is_prime(input) == expected
```

---

## Testing Patterns

### 1. Testing Auto-Waiting

**Pattern:** Simulate delayed availability

```python
def test_wait_for_image_eventual_success(auto_waiter, mock_detector):
    """Test wait_for_image() succeeds when image appears after retries."""

    # Arrange - Image appears on 3rd call
    mock_detector.find_image.side_effect = [
        None,  # First attempt: not found
        None,  # Second attempt: not found
        (100, 200, 50, 50),  # Third attempt: found!
    ]

    # Act
    result = auto_waiter.wait_for_image("test.png", mock_detector, timeout=2000)

    # Assert
    assert result == (100, 200, 50, 50)
    assert mock_detector.find_image.call_count >= 3
```

### 2. Testing Stability Checks

**Pattern:** Simulate movement then stability

```python
def test_ensure_stable_with_moving_element(auto_waiter):
    """Test ensure_stable() waits for element to stop moving."""

    # Arrange - Element moves, then stabilizes
    positions = [
        (100, 200),  # Initial position
        (110, 210),  # Moved 10px (exceeds tolerance)
        (120, 220),  # Moved another 10px
        (120, 220),  # Stable
        (120, 220),  # Still stable
    ]

    position_index = 0
    def get_position():
        nonlocal position_index
        if position_index < len(positions):
            pos = positions[position_index]
            position_index += 1
            return pos
        return positions[-1]

    location_getter = Mock(side_effect=get_position)

    # Act
    result = auto_waiter.ensure_stable(
        location_getter,
        duration=100,
        tolerance=5
    )

    # Assert
    assert result == (120, 220)
    assert location_getter.call_count >= 3  # Multiple checks
```

### 3. Testing Expectations

**Pattern:** Check retry behavior

```python
def test_image_expectation_retries_until_success():
    """Test expectation retries multiple times before succeeding."""

    # Arrange
    automator = Mock()

    # Image not found first 2 times, then found
    automator.find_image.side_effect = [
        None,
        None,
        (100, 200, 50, 50)
    ]

    # Act
    expectation = expect(automator).to_have_image("test.png")

    # No exception = success
    # Assert
    assert automator.find_image.call_count == 3
```

### 4. Testing Page Objects

**Pattern:** Test element interactions

```python
def test_element_click_finds_and_clicks(mock_automator):
    """Test Element.click() finds location and clicks center."""

    # Arrange
    mock_automator.find_image.return_value = (100, 200, 50, 50)
    locator = Locator(type=LocatorType.IMAGE, value="button.png")
    element = Element(locator, mock_automator)

    # Act
    element.click()

    # Assert - find_image called
    mock_automator.find_image.assert_called_once_with("button.png")

    # pyautogui.click called with center coordinates
    # (This requires mocking pyautogui at module level)
```

### 5. Testing Error Cases

**Pattern:** Use pytest.raises

```python
def test_wait_for_image_timeout(auto_waiter, mock_detector):
    """Test wait_for_image() raises TimeoutError when image never appears."""

    # Arrange - Image never found
    mock_detector.find_image.return_value = None

    # Act & Assert
    with pytest.raises(TimeoutError) as exc_info:
        auto_waiter.wait_for_image(
            "missing.png",
            mock_detector,
            timeout=500  # Short timeout for fast test
        )

    # Optionally check error message
    assert "missing.png" in str(exc_info.value)
```

---

## Mocking Strategies

### 1. Mocking Display Libraries

Screen Automator depends on display libraries that don't work in CI:

```python
# At top of test file, BEFORE imports
import sys
from unittest.mock import MagicMock

# Mock display-dependent modules
sys.modules["pynput"] = MagicMock()
sys.modules["pynput.mouse"] = MagicMock()
sys.modules["pynput.keyboard"] = MagicMock()
sys.modules["pyautogui"] = MagicMock()
sys.modules["screeninfo"] = MagicMock()

# NOW import your code
from src.actionability import SmartAutomator
```

**Why this works:**
- Python checks `sys.modules` before importing
- Mocks get imported instead of real modules
- Code runs without display/input hardware

### 2. Shared Mock State (IMPORTANT!)

**Problem:** When multiple test files mock the same module, they can interfere:

```python
# tests/test_file_a.py
mock_pyautogui = MagicMock()
sys.modules["pyautogui"] = mock_pyautogui

# tests/test_file_b.py
sys.modules["pyautogui"] = MagicMock()  # Different mock!

# Tests in file_a now fail because their mock was replaced!
```

**Solution:** Use autouse fixture to reset mock state:

```python
@pytest.fixture(autouse=True)
def reset_pyautogui_mock():
    """Reset the pyautogui mock before each test."""
    mock = sys.modules["pyautogui"]
    mock.reset_mock()
    yield mock
```

### 3. Mock Specifications

**Use `spec` to prevent false positives:**

```python
# ❌ Bad: Mock matches any attribute check
manager = Mock()
hasattr(manager, "anything")  # True!

# ✅ Good: Mock only has specified attributes
manager = Mock(spec=['get_windows', 'get_active_window'])
hasattr(manager, "get_windows")  # True
hasattr(manager, "nonexistent")  # False!
```

**Real example from our tests:**

```python
@pytest.fixture
def mock_image_detector():
    """Create a mock ImageDetector with specific methods."""
    detector = Mock(spec=['find_image', 'find_image_on_screen'])
    detector.find_image = Mock(return_value=(100, 200, 50, 50))
    detector.find_image_on_screen = Mock(return_value=(100, 200, 50, 50))
    return detector
```

### 4. Side Effects for Stateful Behavior

```python
# Simulate state changes
call_count = 0

def find_image_side_effect(path):
    nonlocal call_count
    call_count += 1
    if call_count < 3:
        return None  # Not found first 2 times
    return (100, 200, 50, 50)  # Found on 3rd call

mock.find_image.side_effect = find_image_side_effect
```

---

## Test Coverage

### Current Coverage

```
Module                 Statements   Missing   Coverage
------------------------------------------------------
src/expectations.py           234        12      95%
src/actionability.py          189         8      96%
src/page_objects.py           156        18      88%
src/modern_api.py             120        24      80%
src/rule_manager.py           200        45      77%
------------------------------------------------------
TOTAL                        1250       150      88%
```

**Target:** Maintain >70% overall coverage

### Measuring Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html

# Check coverage threshold
pytest --cov=src --cov-fail-under=70
```

### Coverage Configuration

**pyproject.toml:**
```toml
[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

### What to Cover

**High Priority:**
- ✅ Core logic (expectations, waiting, page objects)
- ✅ Public APIs (modern_api.py)
- ✅ Error handling paths

**Lower Priority:**
- Platform-specific code (hard to test)
- GUI code (manual testing)
- Trivial getters/setters

---

## Continuous Integration

### GitHub Actions Workflow

**.github/workflows/test.yml:**

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.9', '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: pytest --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks

**.pre-commit-config.yaml:**

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

Run tests before every commit:
```bash
pre-commit install
git commit -m "message"  # Tests run automatically
```

---

## Best Practices

### 1. **Keep Tests Fast**

```python
# ✅ Good: Fast timeouts in tests
AutoWaiter(timeout=500, poll_interval=10)

# ❌ Bad: Production timeouts in tests
AutoWaiter(timeout=30000, poll_interval=500)
```

### 2. **One Assertion per Test (Generally)**

```python
# ✅ Good: Focused test
def test_click_calls_find_image(smart_automator, mock_detector):
    smart_automator.click_image("button.png")
    mock_detector.find_image.assert_called_once()

# ✅ Also good: Related assertions
def test_click_image_workflow(smart_automator, mock_detector):
    smart_automator.click_image("button.png")
    mock_detector.find_image.assert_called()
    # Check click was at correct location
    assert_click_at_image_center()
```

### 3. **Use Descriptive Test Names**

Test names should answer: "What behavior is being tested?"

```python
# ✅ Good
def test_wait_for_image_retries_until_found()
def test_ensure_stable_waits_for_animation_to_stop()
def test_expect_raises_timeout_error_when_image_never_appears()

# ❌ Bad
def test_wait()
def test_stable()
def test_expect_error()
```

### 4. **Test Behavior, Not Implementation**

```python
# ✅ Good: Tests observable behavior
def test_click_image_clicks_at_center_of_found_image():
    smart.click_image("button.png")
    # Verify click happened at expected location

# ❌ Bad: Tests internal details
def test_click_image_calls_private_method():
    smart.click_image("button.png")
    assert smart._internal_helper_was_called
```

### 5. **Clean Up After Tests**

```python
# Use fixtures for setup/teardown
@pytest.fixture
def temp_file():
    # Setup
    path = "temp_test_file.json"
    with open(path, 'w') as f:
        f.write('{}')

    yield path

    # Teardown
    if os.path.exists(path):
        os.remove(path)
```

---

## Troubleshooting Tests

### Problem: Tests Pass Individually, Fail Together

**Cause:** Shared mock state

**Solution:**
```python
@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks before each test."""
    sys.modules["pyautogui"].reset_mock()
    sys.modules["pynput"].reset_mock()
    yield
```

### Problem: Tests are Flaky

**Causes & Solutions:**

1. **Race conditions**
   - ✅ Use `wait_for` instead of `sleep`
   - ✅ Use shorter timeouts in tests

2. **Time-dependent tests**
   - ✅ Mock `time.time()` for deterministic tests
   - ✅ Use `freezegun` library

3. **External dependencies**
   - ✅ Mock all external services
   - ✅ Use fixtures for test data

### Problem: Import Errors in Tests

**Cause:** Mocks not set up before imports

**Solution:**
```python
# ❌ Wrong order
from src.module import Class  # Imports pyautogui
sys.modules["pyautogui"] = MagicMock()  # Too late!

# ✅ Correct order
sys.modules["pyautogui"] = MagicMock()
from src.module import Class  # Now imports mock
```

---

## Testing Checklist

When adding new code, ensure:

- [ ] Unit tests for new functions/methods
- [ ] Integration test for new features
- [ ] Error cases covered
- [ ] Edge cases tested
- [ ] Mocks use `spec` parameter
- [ ] Tests follow naming convention
- [ ] Coverage ≥ 70% for new code
- [ ] All tests pass: `pytest`
- [ ] No warnings: `pytest -W error`

---

## Example: Complete Test File

```python
"""
Tests for the SmartAutomator class.

SmartAutomator provides auto-waiting and stability checking
for reliable UI automation.
"""

import sys
import pytest
from unittest.mock import Mock, MagicMock

# Mock display libraries BEFORE imports
sys.modules["pyautogui"] = MagicMock()

from src.actionability import SmartAutomator, AutoWaiter


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_pyautogui():
    """Reset pyautogui mock before each test."""
    sys.modules["pyautogui"].reset_mock()
    yield sys.modules["pyautogui"]


@pytest.fixture
def mock_detector():
    """Create mock ImageDetector."""
    detector = Mock(spec=['find_image'])
    detector.find_image.return_value = (100, 200, 50, 50)
    return detector


@pytest.fixture
def smart_automator(mock_detector):
    """Create SmartAutomator with mock detector."""
    return SmartAutomator(mock_detector, timeout=2000)


# ============================================================================
# Tests - Initialization
# ============================================================================

def test_smart_automator_initialization(mock_detector):
    """Test SmartAutomator initializes with correct defaults."""
    smart = SmartAutomator(mock_detector, timeout=5000)

    assert smart.automator == mock_detector
    assert smart.waiter.timeout == 5000


# ============================================================================
# Tests - click_image()
# ============================================================================

def test_click_image_finds_and_clicks(smart_automator, mock_detector):
    """Test click_image() finds image location and clicks."""
    smart_automator.click_image("button.png", ensure_stable=False)

    # Verify image was searched for
    mock_detector.find_image.assert_called()

    # Verify click happened
    sys.modules["pyautogui"].click.assert_called()


def test_click_image_waits_for_stability(smart_automator, mock_detector):
    """Test click_image() ensures element is stable before clicking."""
    mock_detector.find_image.return_value = (100, 200, 50, 50)

    smart_automator.click_image("button.png", ensure_stable=True)

    # Should wait for stability (multiple position checks)
    assert mock_detector.find_image.call_count > 1


# ============================================================================
# Tests - Error Handling
# ============================================================================

def test_click_image_raises_on_not_found(smart_automator, mock_detector):
    """Test click_image() raises TimeoutError if image not found."""
    mock_detector.find_image.return_value = None

    with pytest.raises(TimeoutError):
        smart_automator.click_image("missing.png")
```

---

## Resources

- **pytest Documentation**: https://docs.pytest.org/
- **unittest.mock Guide**: https://docs.python.org/3/library/unittest.mock.html
- **Coverage.py**: https://coverage.readthedocs.io/
- **Testing Best Practices**: https://testdriven.io/blog/testing-best-practices/

---

*Last Updated: 2025-11-10*
*Version: 2.3.0*
