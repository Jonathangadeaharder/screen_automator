# Screen Automator Framework - Quick Reference

One-page cheat sheet for the new framework features.

## Setup

```bash
# Install with Poetry (recommended)
poetry install --with dev
poetry run pre-commit install

# Or use pip
pip install -r requirements.txt
```

## Auto-Waiting

### Problem: Flaky time.sleep()
```python
# ❌ Brittle
import time
time.sleep(5)
automator.image_detector.find_image("button.png")
```

### Solution: SmartAutomator
```python
# ✅ Robust
from src.actionability import SmartAutomator

smart = SmartAutomator(automator.image_detector, timeout=10000)
smart.click_image("button.png")  # Auto-waits!
```

### Key Classes
- `AutoWaiter` - Core waiting engine
- `SmartAutomator` - Wrapper for automatic waiting

### Common Methods
```python
waiter = AutoWaiter(timeout=30000)

# Wait for image
location = waiter.wait_for_image("btn.png", automator)

# Wait for stable image (no animation)
location = waiter.wait_for_stable_image("btn.png", automator)

# Wait for condition
result = waiter.wait_for_condition(
    lambda: some_condition(),
    "condition description"
)
```

---

## Expectations API

### Problem: Immediate assertion failures
```python
# ❌ Brittle
assert automator.find_image("success.png") is not None
```

### Solution: Auto-retrying expect()
```python
# ✅ Robust
from src.expectations import expect

expect(automator).to_have_image("success.png", timeout=5000)
```

### Image Expectations
```python
# Wait for image to appear
expect(automator).to_be_visible("button.png")
expect(automator).to_have_image("button.png")  # Alias

# Wait for image to disappear
expect(automator).not_to_be_visible("loading.png")
expect(automator).not_to_have_image("loading.png")  # Alias

# Check location
expect(automator).to_be_at_location("icon.png", x=100, y=200, tolerance=10)
```

### State Expectations
```python
# Wait for any value
expect(lambda: app.status).to_be("ready")
expect(lambda: counter.value).to_be_greater_than(0)
expect(lambda: flag).to_be_truthy()
```

### Simple Waiting
```python
from src.expectations import wait_for

wait_for(
    lambda: os.path.exists("output.txt"),
    timeout=10000,
    error_message="File not created"
)
```

---

## Page Object Model

### Problem: Scattered, duplicated automation
```python
# ❌ Hard to maintain
automator.click_image("file_menu.png")
automator.click_image("save.png")
# Repeated in every test
```

### Solution: Page Objects
```python
# ✅ Maintainable
from src.page_objects import BasePage, Element, image_locator

class MainWindow(BasePage):
    def __init__(self, automator):
        super().__init__(automator)
        self.file_menu = Element(image_locator("file_menu.png"), automator)
        self.save_button = Element(image_locator("save.png"), automator)

    def save_document(self):
        self.file_menu.click()
        self.save_button.click()

# Use in tests
main = MainWindow(automator)
main.save_document()
```

### Base Classes
- `BasePage` - For windows/pages
- `BaseDialog` - For dialogs/modals
- `WindowPage` - For window management integration
- `Element` - Represents single UI element
- `Locator` - Defines how to find element

### Locator Types
```python
from src.page_objects import (
    image_locator,
    text_locator,
    coordinate_locator
)

# Image-based (current)
button = Element(image_locator("button.png"), automator)

# Text-based (future - property automation)
field = Element(text_locator("Username", control_type="Edit"), automator)

# Coordinates (fallback)
menu = Element(coordinate_locator(100, 200), automator)
```

### Element Methods
```python
element = Element(locator, automator)

element.click()                    # Click element
element.type_text("hello")         # Type into element
element.is_visible()               # Check visibility
element.wait_for_visible()         # Wait to appear
element.wait_for_hidden()          # Wait to disappear
```

---

## Data-Driven Testing

### Problem: Duplicated test functions
```python
# ❌ Duplication
def test_user1(): login("user1", "pass1")
def test_user2(): login("user2", "pass2")
# ... 98 more
```

### Solution: Data files
```python
# ✅ One loop, many tests
from src.data_driven import DataProvider

for row in DataProvider("test_data/users.csv"):
    login(row['username'], row['password'])
```

### Supported Formats

#### CSV
```csv
username,password,expected
user1,pass1,success
user2,pass2,success
```

#### JSON
```json
[
  {"username": "user1", "password": "pass1"},
  {"username": "user2", "password": "pass2"}
]
```

#### XML
```xml
<testdata>
  <testcase>
    <username>user1</username>
    <password>pass1</password>
  </testcase>
</testdata>
```

### Data Provider Usage
```python
from src.data_driven import DataProvider

provider = DataProvider("data.csv")  # Auto-detects format

for row in provider:
    username = row['username']
    password = row['password']
    # Run test

# Also supports indexing
first_row = provider[0]
row_count = len(provider)
```

### Structured Testing
```python
from src.data_driven import DataDrivenTest

class LoginTest(DataDrivenTest):
    def __init__(self, automator):
        super().__init__("test_data.csv", automator)

    def run_test(self, data):
        # Runs once per row
        login(data['username'], data['password'])

test = LoginTest(automator)
results = test.run_all()
```

### Configuration Management
```python
from src.data_driven import ConfigManager

# config.json: {"dev": {...}, "prod": {...}}
config = ConfigManager("config.json", environment="dev")

app_path = config.get("app_path")
timeout = config.get("timeout", default=30000)
api_url = config.get("api.url")  # Dot notation
```

---

## Code Quality Tools

### Format Code
```bash
poetry run black .      # Format all code
poetry run isort .      # Sort imports
```

### Check Quality
```bash
poetry run flake8 .     # Lint code (PEP 8)
poetry run mypy src/    # Type check
```

### Security
```bash
poetry run bandit -r src/    # Security scan
poetry run safety check      # Dependency vulnerabilities
```

### Run Tests
```bash
poetry run pytest                # Run all tests
poetry run pytest --cov         # With coverage
```

### Pre-commit Hooks
```bash
poetry run pre-commit install           # Install hooks
poetry run pre-commit run --all-files   # Run manually
git commit                              # Runs automatically
```

---

## Common Patterns

### Pattern 1: Robust Button Click
```python
from src.actionability import SmartAutomator
from src.expectations import expect

smart = SmartAutomator(automator)

# Wait for button
expect(automator).to_have_image("button.png")

# Click with auto-wait
smart.click_image("button.png")

# Verify result
expect(automator).to_have_image("success.png")
```

### Pattern 2: Page Object Test
```python
from page_objects import LoginPage, HomePage

login = LoginPage(automator)
login.login("user", "pass")

home = HomePage(automator)
expect(lambda: home.is_loaded()).to_be_truthy()
```

### Pattern 3: Data-Driven Login
```python
from src.data_driven import DataProvider
from src.expectations import expect

for row in DataProvider("credentials.csv"):
    login_page.login(row['user'], row['pass'])

    if row['expected'] == "success":
        expect(automator).to_have_image("homepage.png")
    else:
        expect(automator).to_have_image("error.png")
```

---

## Migration Quick Guide

### Step 1: Add Auto-Waiting (5 minutes)
```python
from src.actionability import SmartAutomator

smart = SmartAutomator(automator.image_detector)
# Use 'smart' for new code
```

### Step 2: Replace Assertions (15 minutes)
```python
from src.expectations import expect

# Find: assert automator.find_image("x.png")
# Replace: expect(automator).to_have_image("x.png")
```

### Step 3: Create Page Objects (as needed)
Start with frequently-changed UI:
```python
from src.page_objects import BasePage, Element, image_locator

class MyWindow(BasePage):
    def __init__(self, automator):
        super().__init__(automator)
        # Define elements
```

### Step 4: Data-Driven (when needed)
For tests with many variations:
```python
from src.data_driven import DataProvider

for row in DataProvider("data.csv"):
    # Run test with row data
```

---

## Documentation

- **README.md** - Project overview
- **FRAMEWORK_GUIDE.md** - Complete framework guide (800+ lines)
- **MIGRATION_GUIDE.md** - Step-by-step migration
- **IMPROVEMENT_BLUEPRINT_IMPLEMENTATION.md** - Implementation details
- **examples/framework_demo.py** - Working examples
- **examples/integration_example.py** - Integration with existing code

---

## Troubleshooting

### Import Errors
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/path/to/screen_automator  # Linux/Mac
set PYTHONPATH=C:\path\to\screen_automator  # Windows
```

### Module Not Found
```bash
# Install dependencies
poetry install --with dev
```

### Pre-commit Failing
```bash
# Fix automatically
poetry run black .
poetry run isort .
```

---

## Support

- **GitHub Issues**: Report bugs or ask questions
- **Documentation**: Check FRAMEWORK_GUIDE.md
- **Examples**: Review examples/ directory
- **Tests**: Look at test files for usage patterns

---

**Pro Tip**: Start with auto-waiting and expectations first - they provide immediate value with minimal changes to your code!
