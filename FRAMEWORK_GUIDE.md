# Screen Automator Framework Guide

**The modern API for reliable GUI automation.**

## Quick Start

```python
from src.modern_api import create_framework

# Create framework instance
framework = create_framework(timeout=10000)

# Click image with auto-waiting
framework.click_image("button.png")

# Robust assertions
framework.expect_image("success.png", timeout=5000)
framework.expect_no_image("loading.png")

# Start rule monitoring
framework.start_monitoring()
```

## Why This Framework?

- **No flaky tests** - Auto-waiting eliminates race conditions
- **No manual sleeps** - Intelligent waiting for UI elements
- **Simple API** - One clear way to do everything
- **Production-ready** - Built-in code quality and CI/CD

---

## Core Concepts

### 1. Auto-Waiting

**Problem:** Traditional automation uses `time.sleep(5)` and fails randomly.

**Solution:** The framework waits intelligently for elements to appear.

```python
# ❌ Old way (brittle)
import time
time.sleep(5)
location = automator.find_image("button.png")

# ✅ Modern way (robust)
framework.click_image("button.png")  # Waits automatically!
```

### 2. Expectations

**Problem:** Immediate assertions fail if UI hasn't loaded yet.

**Solution:** Expectations auto-retry until condition is met or timeout.

```python
# ❌ Old way (brittle)
assert automator.find_image("success.png") is not None

# ✅ Modern way (robust)
framework.expect_image("success.png", timeout=5000)
```

### 3. Complete Workflow

Here's a real automation workflow:

```python
from src.modern_api import create_framework

# Setup
framework = create_framework(timeout=10000)

# Wait for app to load (up to 30 seconds)
framework.wait_for_image("app_icon.png", timeout=30000)

# Navigate to settings
framework.click_image("menu_button.png")
framework.click_image("settings_option.png")

# Verify dialog opened
framework.expect_image("settings_dialog.png", timeout=5000)

# Make changes
framework.click_image("enable_feature_checkbox.png")
framework.click_image("save_button.png")

# Wait for save to complete
framework.expect_no_image("loading_spinner.png")
framework.expect_image("saved_confirmation.png", timeout=3000)

# Close dialog
framework.click_image("close_button.png")
framework.expect_no_image("settings_dialog.png")

print("✓ Settings updated successfully!")
```

---

## API Reference

### Framework Creation

```python
from src.modern_api import create_framework

# Default 30 second timeout
framework = create_framework()

# Custom timeout
framework = create_framework(timeout=15000)

# Custom rules directory
framework = create_framework(rules_dir="my_rules", timeout=10000)
```

### Image Operations

```python
# Wait for image (returns location)
location = framework.wait_for_image("button.png", timeout=10000)

# Click image (auto-waits)
framework.click_image("button.png")

# Click without stability check (faster but less reliable)
framework.click_image("button.png", ensure_stable=False)

# Wait for image to disappear
framework.wait_for_image_to_disappear("loading.png", timeout=5000)
```

### Expectations (Assertions)

```python
# Expect image to be visible
framework.expect_image("success.png", timeout=5000)

# Expect image NOT to be visible
framework.expect_no_image("error.png", timeout=3000)

# These will auto-retry until timeout is reached
```

### Rule Monitoring

```python
# Start rule-based monitoring
framework.start_monitoring()

# Stop monitoring
framework.stop_monitoring()

# Check if running
if framework.is_running:
    print("Monitoring is active")
```

### Configuration

```python
# Set default timeout (milliseconds)
framework.set_timeout(20000)

# Set check interval for monitoring (seconds)
framework.set_check_interval(5.0)

# Set mouse idle threshold (seconds)
framework.set_mouse_idle_threshold(3.0)
```

### Callbacks

```python
# Set callback for when rules trigger
framework.on_rule_triggered(lambda rule: print(f"Triggered: {rule.name}"))

# Set callback for errors
framework.on_error(lambda msg: print(f"Error: {msg}"))

# Set callback for actions
framework.on_action_executed(lambda rule, idx: print(f"Action {idx} executed"))
```

---

## Advanced Features

### Page Object Model

For maintainable automation, create page objects:

```python
from src.page_objects import BasePage, Element, image_locator

class SettingsDialog(BasePage):
    def __init__(self, automator):
        super().__init__(automator)

        # Define elements
        self.feature_checkbox = Element(
            image_locator("enable_feature.png"),
            automator
        )
        self.save_button = Element(
            image_locator("save.png"),
            automator
        )

    def enable_feature_and_save(self):
        """High-level business logic"""
        self.feature_checkbox.click()
        self.save_button.click()
        self.wait_for_close()

# Use in automation
settings = SettingsDialog(framework.automator)
settings.enable_feature_and_save()
```

### Data-Driven Testing

Run same test with multiple data sets:

```python
from src.data_driven import DataProvider

# Load test data from CSV/JSON/XML
provider = DataProvider("test_data.csv")

for row in provider:
    username = row['username']
    password = row['password']
    expected = row['expected_result']

    # Run test with this data
    framework.click_image("login_button.png")
    # ... test logic ...
```

**Example CSV:**
```csv
username,password,expected_result
user1,pass1,success
admin,admin123,success
invalid,wrong,error
```

---

## Development Setup

### Installation

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install --with dev

# Install pre-commit hooks
poetry run pre-commit install
```

### Code Quality Tools

```bash
# Format code
poetry run black .
poetry run isort .

# Check code quality
poetry run flake8 .
poetry run mypy src/

# Security checks
poetry run bandit -r src/
poetry run safety check

# Run tests
poetry run pytest --cov
```

### CI/CD

GitHub Actions automatically runs on every push:
- Tests on Linux, Windows, macOS
- Python 3.8 through 3.12
- Code quality checks
- Security scans
- Coverage reports

---

## Best Practices

### 1. Always Use the Framework

```python
# ✅ Good - Modern API
from src.modern_api import create_framework
framework = create_framework()

# ❌ Avoid - Low-level APIs
from src.automator import ScreenAutomator
automator = ScreenAutomator()
```

### 2. Use Expectations, Not Assertions

```python
# ✅ Good - Auto-retrying
framework.expect_image("success.png", timeout=5000)

# ❌ Avoid - Immediate failure
assert automator.find_image("success.png") is not None
```

### 3. Never Use time.sleep()

```python
# ✅ Good - Intelligent waiting
framework.wait_for_image("dialog.png")
framework.click_image("button.png")

# ❌ Avoid - Arbitrary waits
import time
time.sleep(5)
automator.click()
```

### 4. Use Descriptive Timeouts

```python
# ✅ Good - Clear intent
framework.wait_for_image("app_startup.png", timeout=30000)  # App takes time
framework.expect_image("quick_popup.png", timeout=2000)     # Should be fast

# ❌ Avoid - Magic numbers
framework.wait_for_image("something.png", timeout=12345)
```

### 5. Create Page Objects for Complex UI

When you find yourself repeating the same sequence of clicks, create a page object.

---

## Troubleshooting

### Image Not Found

```python
# Increase timeout
framework.wait_for_image("button.png", timeout=30000)

# Check image is correct
# - Verify image file exists
# - Ensure image matches what's on screen
# - Consider screen resolution differences
```

### Clicks Missing Target

```python
# Ensure stability (default behavior)
framework.click_image("button.png", ensure_stable=True)

# Or wait explicitly before clicking
location = framework.wait_for_image("button.png")
# Small delay for animation to complete
framework.click_image("button.png")
```

### Tests Still Flaky

```python
# Increase default timeout
framework = create_framework(timeout=20000)

# Or increase per-operation timeout
framework.expect_image("slow_element.png", timeout=30000)
```

---

## Examples

See `examples/modern_api_usage.py` for complete working examples.

## Documentation

- **QUICK_REFERENCE.md** - One-page API reference
- **README.md** - Project overview
- **examples/** - Working code examples

---

**Start building reliable automation today!** 🚀
