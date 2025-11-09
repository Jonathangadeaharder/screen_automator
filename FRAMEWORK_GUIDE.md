# Screen Automator Framework Guide

## Introduction to Professional Automation

This guide introduces the professional-grade framework enhancements implemented in Screen Automator, transforming it from a simple automation tool into a robust, maintainable automation framework.

These enhancements are based on industry best practices and lessons learned from modern web automation frameworks like Playwright and Selenium.

## Table of Contents

1. [Auto-Waiting and Actionability](#auto-waiting-and-actionability)
2. [Expectations API](#expectations-api)
3. [Page Object Model](#page-object-model)
4. [Data-Driven Testing](#data-driven-testing)
5. [Code Quality Setup](#code-quality-setup)
6. [CI/CD Pipeline](#cicd-pipeline)

---

## Auto-Waiting and Actionability

### The Problem: Flaky Tests

The #1 problem in UI automation is **flaky tests** - tests that sometimes pass and sometimes fail. The primary cause is timing issues:

```python
# ❌ BRITTLE CODE - This will fail randomly
import time
time.sleep(5)  # Hope 5 seconds is enough
automator.click_image("button.png")
```

**Problems:**
- If the button loads in 5.1 seconds, the test fails
- If the button loads in 0.5 seconds, you waste 4.5 seconds
- Different environments have different speeds

### The Solution: Auto-Waiting

The new `actionability` module provides Playwright-style auto-waiting:

```python
from src.actionability import AutoWaiter

waiter = AutoWaiter(timeout=30000)  # 30 seconds max

# ✅ ROBUST CODE - Waits for element to appear and stabilize
location = waiter.wait_for_stable_image("button.png", automator)
```

### Key Features

#### 1. Wait for Conditions

Instead of guessing how long to wait, wait for a **condition**:

```python
# Wait for image to appear
location = waiter.wait_for_image("save_button.png", automator, timeout=10000)

# Wait for image to disappear
waiter.wait_for_condition(
    lambda: automator.find_image("loading.png") is None,
    "loading spinner to disappear",
    timeout=30000
)
```

#### 2. Stability Checks

Prevent clicking on animating elements:

```python
# Ensure element is stable (not moving) before clicking
stable_location = waiter.ensure_stable(
    lambda: automator.find_image("button.png"),
    duration=100  # Must be stable for 100ms
)
```

#### 3. Smart Automator Wrapper

The `SmartAutomator` wrapper adds auto-waiting to all actions:

```python
from src.actionability import SmartAutomator

# Wrap your existing automator
smart = SmartAutomator(automator, timeout=10000)

# Old way (brittle):
# time.sleep(5)
# automator.click_image("button.png")

# New way (robust):
smart.click_image("button.png")  # Auto-waits AND checks stability!

# Wait for element to disappear
smart.wait_for_image_to_disappear("loading.png")
```

---

## Expectations API

### The Problem: Race Conditions in Assertions

Traditional assertions fail immediately, causing race conditions:

```python
# ❌ BRITTLE - Fails if button hasn't appeared yet
assert automator.find_image("button.png") is not None
```

### The Solution: Auto-Retrying Expectations

The `expectations` module provides assertions that retry:

```python
from src.expectations import expect

# ✅ ROBUST - Retries for up to 5 seconds
expect(automator).to_have_image("button.png", timeout=5000)
```

### Key Features

#### Image Expectations

```python
from src.expectations import expect

# Wait for image to appear
expect(automator).to_be_visible("save_button.png")
expect(automator).to_have_image("save_button.png")  # Alias

# Wait for image to disappear
expect(automator).not_to_be_visible("loading.png")

# Check image location
expect(automator).to_be_at_location(
    "icon.png",
    x=100, y=200,
    tolerance=10  # ±10 pixels
)
```

#### Window Expectations

```python
# Wait for window to appear
expect(window_manager).to_have_window("Calculator")
```

#### State Expectations

```python
# Wait for any condition
expect(lambda: app.get_status()).to_be("ready")
expect(lambda: counter.value).to_be_greater_than(0)
expect(lambda: file_exists()).to_be_truthy()
```

#### Simple Condition Waiting

For custom conditions:

```python
from src.expectations import wait_for
import os

wait_for(
    lambda: os.path.exists("output.txt"),
    timeout=10000,
    error_message="Output file was not created"
)
```

### Benefits

**Before (Brittle):**
```python
time.sleep(5)
assert automator.find_image("button.png") is not None
assert automator.find_image("loading.png") is None
```

**After (Robust):**
```python
expect(automator).to_have_image("button.png")
expect(automator).not_to_have_image("loading.png")
```

**Result:** Tests that adapt to environment speed and eliminate race conditions.

---

## Page Object Model

### The Problem: Unmaintainable Test Scripts

Without structure, automation becomes unmaintainable:

```python
# ❌ BRITTLE - Scattered, hard-coded automation
# test_save_document.py
automator.click_image("file_menu.png")
automator.click_image("save_as.png")
automator.type_text("my_document.txt")
automator.click_image("save_button.png")

# test_save_with_overwrite.py
automator.click_image("file_menu.png")  # Duplicated!
automator.click_image("save_as.png")    # Duplicated!
automator.type_text("existing.txt")
automator.click_image("save_button.png")
automator.click_image("yes_button.png")
```

**When the UI changes, you must update EVERY test script manually.**

### The Solution: Page Object Model

The Page Object Model (POM) encapsulates UI elements and interactions:

```python
# page_objects/main_window.py
from src.page_objects import BasePage, Element, image_locator

class MainWindow(BasePage):
    def __init__(self, automator):
        super().__init__(automator)

        # Locators centralized in ONE place
        self.file_menu = Element(image_locator("file_menu.png"), automator)
        self.save_as_menu = Element(image_locator("save_as.png"), automator)

    def save_as(self):
        """High-level business logic"""
        self.file_menu.click()
        self.save_as_menu.click()
        return SaveDialog(self.automator)  # Return next page


# page_objects/save_dialog.py
class SaveDialog(BaseDialog):
    def __init__(self, automator):
        super().__init__(automator)

        self.filename_field = Element(image_locator("filename.png"), automator)
        self.save_button = Element(image_locator("save_button.png"), automator)

    def save_with_filename(self, filename: str):
        self.filename_field.type_text(filename)
        self.save_button.click()
        self.wait_for_close()
```

### Usage in Tests

Now tests are clean, readable, and maintainable:

```python
# test_save_document.py
def test_save_new_document(automator):
    main = MainWindow(automator)
    dialog = main.save_as()
    dialog.save_with_filename("my_document.txt")

def test_save_with_overwrite(automator):
    main = MainWindow(automator)
    dialog = main.save_as()
    dialog.save_with_filename("existing.txt")
    # Overwrite confirmation is handled in SaveDialog
```

**When the UI changes, you update ONE file (the page object), not every test.**

### Creating Page Objects

#### Basic Page

```python
from src.page_objects import BasePage, Element, image_locator

class CalculatorWindow(BasePage):
    def __init__(self, automator):
        super().__init__(automator)

        # Define elements
        self.button_1 = Element(image_locator("calc_1.png"), automator)
        self.button_plus = Element(image_locator("calc_plus.png"), automator)
        self.button_equals = Element(image_locator("calc_equals.png"), automator)

    def add_numbers(self, a: int, b: int):
        """High-level action"""
        self.button_1.click()
        self.button_plus.click()
        self.button_1.click()
        self.button_equals.click()
```

#### Dialog

```python
from src.page_objects import BaseDialog, Element, image_locator

class SaveDialog(BaseDialog):
    def __init__(self, automator):
        title_locator = image_locator("save_dialog_title.png")
        super().__init__(automator, title_locator)

        self.filename_field = Element(image_locator("filename.png"), automator)
        self.save_button = Element(image_locator("save_button.png"), automator)

    def save_as(self, filename: str):
        self.wait_for_open()  # Automatically waits for dialog
        self.filename_field.type_text(filename)
        self.save_button.click()
        self.wait_for_close()  # Waits for dialog to close
```

#### Window Page

```python
from src.page_objects import WindowPage

class NotepadWindow(WindowPage):
    def __init__(self, automator, window_manager):
        super().__init__(automator, window_manager, window_title="Notepad")

    def type_text(self, text: str):
        self.activate()  # Brings window to foreground
        # ... type text
```

### Locator Types

```python
from src.page_objects import image_locator, text_locator, coordinate_locator

# Image-based (current implementation)
button = Element(image_locator("button.png"), automator)

# Text-based (for future property-based automation)
field = Element(
    text_locator("Username", control_type="Edit"),
    automator
)

# Coordinate-based (fallback)
menu = Element(coordinate_locator(100, 200), automator)
```

---

## Data-Driven Testing

### The Problem: Duplicated Test Code

Testing multiple scenarios requires duplicated code:

```python
# ❌ DUPLICATED
def test_login_valid_user():
    login_page.login("user1", "pass1")
    assert login_page.is_logged_in()

def test_login_admin():
    login_page.login("admin", "admin123")
    assert login_page.is_logged_in()

def test_login_invalid():
    login_page.login("invalid", "wrong")
    assert login_page.has_error()

# ... 100 more users to test?
```

### The Solution: Data-Driven Tests

Separate test logic from test data:

```python
# test_data/login_cases.csv
username,password,expected_result
user1,pass1,success
admin,admin123,success
invalid,wrong,error
locked_user,pass123,locked

# test_login.py
from src.data_driven import DataProvider

provider = DataProvider("test_data/login_cases.csv")

for row in provider:
    username = row['username']
    password = row['password']
    expected = row['expected_result']

    login_page.login(username, password)

    if expected == "success":
        assert login_page.is_logged_in()
    elif expected == "error":
        assert login_page.has_error()
```

**Result:** One test script executes hundreds of test cases.

### Supported Formats

#### JSON

```json
// test_data/users.json
[
    {
        "username": "user1",
        "password": "pass1",
        "role": "admin"
    },
    {
        "username": "user2",
        "password": "pass2",
        "role": "user"
    }
]
```

```python
from src.data_driven import DataProvider

provider = DataProvider("test_data/users.json")
for row in provider:
    print(f"Username: {row['username']}, Role: {row['role']}")
```

#### CSV

```csv
username,password,role
user1,pass1,admin
user2,pass2,user
```

```python
provider = DataProvider("test_data/users.csv")
for row in provider:
    print(row['username'])
```

#### XML

```xml
<testdata>
    <testcase>
        <username>user1</username>
        <password>pass1</password>
    </testcase>
    <testcase>
        <username>user2</username>
        <password>pass2</password>
    </testcase>
</testdata>
```

```python
provider = DataProvider("test_data/users.xml")
for row in provider:
    print(row['username'])
```

### Data-Driven Test Class

For structured data-driven testing:

```python
from src.data_driven import DataDrivenTest, TestDataRow

class LoginTest(DataDrivenTest):
    def __init__(self, automator):
        super().__init__(
            data_file="test_data/login_cases.csv",
            automator=automator
        )

    def setup(self):
        # Run once before all tests
        self.login_page = LoginPage(self.automator)

    def run_test(self, data: TestDataRow):
        # Run once for EACH row in CSV
        username = data['username']
        password = data['password']
        expected = data['expected_result']

        self.login_page.login(username, password)

        if expected == "success":
            assert self.login_page.is_logged_in()

    def teardown(self):
        # Run once after all tests
        pass

# Execute all test cases
test = LoginTest(automator)
results = test.run_all()
print(f"Passed: {results['passed']}/{results['total']}")
```

### Configuration Management

Separate environment config from code:

```python
# config/dev.json
{
    "app_path": "C:/Program Files/MyApp/dev/app.exe",
    "api_url": "https://dev-api.example.com",
    "timeout": 5000
}

# config/prod.json
{
    "app_path": "C:/Program Files/MyApp/app.exe",
    "api_url": "https://api.example.com",
    "timeout": 10000
}
```

```python
from src.data_driven import ConfigManager

# Load environment-specific config
config = ConfigManager("config/dev.json")

app_path = config.get("app_path")
timeout = config.get("timeout", default=30000)

# Switch environments without changing code
# config = ConfigManager("config/prod.json")
```

---

## Code Quality Setup

### Philosophy

Professional projects enforce code quality automatically, not manually.

### Tools Configured

| Tool | Purpose | Command |
|------|---------|---------|
| **Black** | Code formatter | `poetry run black .` |
| **isort** | Import sorter | `poetry run isort .` |
| **Flake8** | Linter | `poetry run flake8 .` |
| **mypy** | Type checker | `poetry run mypy src/` |
| **Bandit** | Security linter | `poetry run bandit -r src/` |
| **Safety** | Dependency security | `poetry run safety check` |

### Setup Instructions

#### 1. Install Poetry

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Or on Windows
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

#### 2. Install Dependencies

```bash
# Install all dependencies (including dev tools)
poetry install --with dev
```

#### 3. Run Quality Checks

```bash
# Format code
poetry run black .
poetry run isort .

# Check code quality
poetry run flake8 .
poetry run mypy src/ gui/ core/ utils/
poetry run bandit -r src/
poetry run safety check

# Run tests with coverage
poetry run pytest
```

#### 4. Install Pre-Commit Hooks

```bash
# Install pre-commit
poetry run pre-commit install

# Run manually on all files
poetry run pre-commit run --all-files
```

**Now every commit automatically:**
- Formats code with Black
- Sorts imports with isort
- Checks for linting errors
- Checks for security issues

### Configuration Files

All tools are configured via:

- **pyproject.toml** - Black, isort, pytest, mypy, bandit, coverage
- **.flake8** - Flake8 configuration
- **.pre-commit-config.yaml** - Pre-commit hooks

---

## CI/CD Pipeline

### Overview

Every push and pull request automatically:

1. **Runs tests** on multiple OS (Linux, Windows, macOS) and Python versions
2. **Checks code quality** (formatting, linting, security)
3. **Generates coverage reports**
4. **Builds the package**

### GitHub Actions Workflow

The workflow is defined in `.github/workflows/main.yaml` with 4 jobs:

#### Job 1: Test

Runs on multiple platforms and Python versions:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]
```

Steps:
1. Checkout code
2. Set up Python
3. Install Poetry
4. Cache dependencies
5. Install dependencies
6. Run tests with coverage
7. Upload coverage reports

#### Job 2: Code Quality

Runs all quality checks:

1. Black (formatter check)
2. isort (import sort check)
3. Flake8 (linter)
4. mypy (type checker)
5. Bandit (security linter)
6. Safety (dependency security)

#### Job 3: Pre-commit

Runs all pre-commit hooks on entire codebase.

#### Job 4: Build

Verifies package can be built successfully.

### Viewing Results

On GitHub:
1. Go to your repository
2. Click "Actions" tab
3. See all workflow runs
4. Click on a run to see detailed results

### Local Testing

Test the CI pipeline locally:

```bash
# Run what CI runs
poetry run pytest --cov
poetry run black . --check
poetry run isort . --check-only
poetry run flake8 .
poetry run mypy src/ gui/ core/ utils/
poetry run bandit -r src/
```

---

## Quick Start Examples

### Example 1: Robust Image Clicking

**Before:**
```python
import time
time.sleep(5)
automator.click_image("button.png")
```

**After:**
```python
from src.actionability import SmartAutomator

smart = SmartAutomator(automator)
smart.click_image("button.png")  # Auto-waits!
```

### Example 2: Reliable Assertions

**Before:**
```python
time.sleep(3)
assert automator.find_image("success.png") is not None
```

**After:**
```python
from src.expectations import expect

expect(automator).to_have_image("success.png")
```

### Example 3: Maintainable Tests with POM

**Before:**
```python
# Scattered automation
automator.click_image("file.png")
automator.click_image("save.png")
automator.type_text("doc.txt")
automator.click_image("ok.png")
```

**After:**
```python
from page_objects import MainWindow

main = MainWindow(automator)
dialog = main.open_save_dialog()
dialog.save_as("doc.txt")
```

### Example 4: Data-Driven Testing

**Before:**
```python
def test_user1():
    login("user1", "pass1")

def test_user2():
    login("user2", "pass2")

# ... 98 more functions
```

**After:**
```python
from src.data_driven import DataProvider

for row in DataProvider("users.csv"):
    login(row['username'], row['password'])
```

---

## Migration Guide

### Step 1: Install Dependencies

```bash
poetry install --with dev
```

### Step 2: Add Auto-Waiting to Existing Tests

Wrap your automator:

```python
from src.actionability import SmartAutomator

# Old
# automator = Automator()

# New
automator = Automator()
smart = SmartAutomator(automator)

# Now use 'smart' instead of 'automator'
smart.click_image("button.png")
```

### Step 3: Replace Assertions

```python
# Find all: assert automator.find_image
# Replace with: expect(automator).to_have_image

from src.expectations import expect

# Old: assert automator.find_image("btn.png")
# New:
expect(automator).to_have_image("btn.png")
```

### Step 4: Create Page Objects

Start with your most-changed UI:

```python
# page_objects/login_page.py
from src.page_objects import BasePage, Element, image_locator

class LoginPage(BasePage):
    def __init__(self, automator):
        super().__init__(automator)

        self.username = Element(image_locator("username.png"), automator)
        self.password = Element(image_locator("password.png"), automator)
        self.login_btn = Element(image_locator("login.png"), automator)

    def login(self, username: str, password: str):
        self.username.type_text(username)
        self.password.type_text(password)
        self.login_btn.click()
```

### Step 5: Enable CI/CD

The workflow is already configured! Just push to your branch:

```bash
git add .
git commit -m "Enable framework features"
git push
```

Check the "Actions" tab on GitHub to see it run.

---

## Best Practices

### 1. Always Use Auto-Waiting

❌ **Never:**
```python
time.sleep(5)
```

✅ **Always:**
```python
smart.click_image("button.png")
# or
expect(automator).to_have_image("button.png")
```

### 2. Use Page Objects for Maintainability

❌ **Don't scatter automation:**
```python
automator.click_image("menu.png")
automator.click_image("item.png")
```

✅ **Encapsulate in page objects:**
```python
class MainPage(BasePage):
    def click_menu_item(self, item):
        self.menu.click()
        self.get_menu_item(item).click()
```

### 3. Use Data-Driven Tests for Variations

❌ **Don't duplicate test functions:**
```python
def test_user_1(): ...
def test_user_2(): ...
```

✅ **Use data files:**
```python
for row in DataProvider("users.csv"):
    test_login(row)
```

### 4. Run Quality Checks Before Committing

```bash
# Format code
poetry run black .
poetry run isort .

# Check quality
poetry run flake8 .

# Run tests
poetry run pytest
```

Or install pre-commit hooks to automate:

```bash
poetry run pre-commit install
```

---

## Troubleshooting

### "Module not found" errors

```bash
# Ensure you're in the Poetry environment
poetry install
poetry shell
```

### Tests failing in CI but passing locally

Check Python version:

```bash
# CI runs on multiple Python versions
# Test with specific version
poetry env use python3.8
poetry install
poetry run pytest
```

### Pre-commit hooks failing

```bash
# Fix automatically
poetry run black .
poetry run isort .

# Then commit
git add .
git commit -m "Fix formatting"
```

---

## Next Steps

1. **Read this guide** to understand the new capabilities
2. **Run the examples** to see them in action
3. **Migrate existing tests** gradually using the migration guide
4. **Write new tests** using the framework patterns
5. **Enable pre-commit hooks** for automatic quality checks

## Support

For issues or questions:
- Check the test files in `tests/` for working examples
- Review the source code in `src/` with detailed docstrings
- Open an issue on GitHub

---

**Welcome to professional automation! 🚀**
