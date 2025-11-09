# Screen Automator - Quick Reference

**One-page cheat sheet for the modern API.**

## Modern API

```python
from src.modern_api import create_framework

# Create framework (default timeout: 30 seconds)
framework = create_framework(timeout=30000)
```

### Image Operations

```python
# Wait for image to appear
location = framework.wait_for_image("button.png", timeout=10000)

# Click with auto-wait (recommended)
framework.click_image("button.png", ensure_stable=True)

# Wait for image to disappear
framework.wait_for_image_to_disappear("loading.png", timeout=5000)
```

### Expectations (Assertions)

```python
# Expect image to be visible (auto-retries)
framework.expect_image("success.png", timeout=5000)

# Expect image NOT to be visible
framework.expect_no_image("error.png", timeout=3000)
```

### Rule Monitoring

```python
# Start/stop rule-based monitoring
framework.start_monitoring()
framework.stop_monitoring()

# Check status
if framework.is_running:
    print("Monitoring active")
```

### Configuration

```python
# Set timeouts
framework.set_timeout(20000)  # 20 seconds default

# Set check interval for monitoring
framework.set_check_interval(5.0)  # 5 seconds

# Set mouse idle threshold
framework.set_mouse_idle_threshold(3.0)  # 3 seconds
```

### Rule Management

```python
# Get all rules
rules = framework.get_rules()

# Enable/disable specific rule
framework.enable_rule("rule_id")
framework.disable_rule("rule_id")
```

### Callbacks

```python
# Set callbacks for events
framework.on_rule_triggered(lambda rule: print(f"Triggered: {rule.name}"))
framework.on_error(lambda msg: print(f"Error: {msg}"))
framework.on_action_executed(lambda rule, idx: print(f"Action {idx}"))
```

## Complete Example

```python
from src.modern_api import create_framework

# 1. Create framework
framework = create_framework(timeout=10000)

# 2. Wait for app to load
framework.wait_for_image("app_icon.png", timeout=30000)

# 3. Click menu
framework.click_image("menu_button.png")
framework.click_image("settings.png")

# 4. Verify dialog opened
framework.expect_image("settings_dialog.png")

# 5. Make changes
framework.click_image("checkbox.png")
framework.click_image("save.png")

# 6. Wait for confirmation
framework.expect_no_image("loading.png")
framework.expect_image("saved.png")

# 7. Close
framework.click_image("close.png")
framework.expect_no_image("settings_dialog.png")
```

## Page Objects (Advanced)

For maintainable automation, create page objects:

```python
from src.page_objects import BasePage, Element, image_locator

class SettingsDialog(BasePage):
    def __init__(self, automator):
        super().__init__(automator)
        self.save_button = Element(image_locator("save.png"), automator)

    def save(self):
        self.save_button.click()

# Use in tests
dialog = SettingsDialog(framework.automator)
dialog.save()
```

## Data-Driven Testing (Advanced)

```python
from src.data_driven import DataProvider

# Load test data from CSV/JSON/XML
for row in DataProvider("test_data.csv"):
    framework.click_image(row['button'])
    framework.expect_image(row['expected_result'])
```

## Setup & Tools

```bash
# Install
poetry install --with dev

# Format code
poetry run black .
poetry run isort .

# Check quality
poetry run flake8 .
poetry run mypy src/

# Run tests
poetry run pytest
```

## Common Patterns

### Pattern 1: Wait and Click
```python
# Old (brittle)
import time
time.sleep(5)
automator.click()

# Modern (robust)
framework.click_image("button.png")
```

### Pattern 2: Wait for Element
```python
# Old
time.sleep(3)
assert automator.find_image("x.png")

# Modern
framework.expect_image("x.png", timeout=3000)
```

### Pattern 3: Wait for Loading
```python
# Old
while automator.find_image("loading.png"):
    time.sleep(0.5)

# Modern
framework.wait_for_image_to_disappear("loading.png")
```

## Documentation

- **Modern API Examples**: `examples/modern_api_usage.py`
- **Complete Guide**: [FRAMEWORK_GUIDE.md](FRAMEWORK_GUIDE.md)
- **Migration Help**: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

---

**Use `create_framework()` for all new code!** 🚀
