"""
Framework Features Demo

This example demonstrates the new framework features:
1. Auto-waiting and actionability
2. Expectations API
3. Page Object Model
4. Data-driven testing

Run this to see the new framework in action!
"""

# Example 1: Auto-Waiting
# =====================

from src.actionability import AutoWaiter, SmartAutomator

def demo_auto_waiting(automator):
    """
    Demonstrates auto-waiting instead of time.sleep().

    Old way (brittle):
        import time
        time.sleep(5)
        automator.click_image("button.png")

    New way (robust):
    """
    # Create auto-waiter
    waiter = AutoWaiter(timeout=30000)  # 30 seconds

    # Wait for image to appear
    location = waiter.wait_for_image("button.png", automator)
    print(f"Button found at {location}")

    # Wait for image to appear AND stabilize (no animation)
    stable_location = waiter.wait_for_stable_image(
        "button.png",
        automator,
        stability_duration=100  # Stable for 100ms
    )
    print(f"Button stable at {stable_location}")

    # Use SmartAutomator wrapper (easiest)
    smart = SmartAutomator(automator, timeout=10000)
    smart.click_image("button.png")  # Auto-waits!


# Example 2: Expectations API
# ===========================

from src.expectations import expect, wait_for

def demo_expectations(automator):
    """
    Demonstrates auto-retrying expectations.

    Old way (brittle):
        assert automator.find_image("button.png") is not None

    New way (robust):
    """
    # Wait for image to appear
    expect(automator).to_have_image("button.png", timeout=5000)
    expect(automator).to_be_visible("save_button.png")

    # Wait for image to disappear
    expect(automator).not_to_have_image("loading.png")

    # Check image location
    expect(automator).to_be_at_location(
        "icon.png",
        x=100, y=200,
        tolerance=10  # ±10 pixels
    )

    # Wait for custom conditions
    import os
    wait_for(
        lambda: os.path.exists("output.txt"),
        timeout=10000,
        error_message="Output file not created"
    )


# Example 3: Page Object Model
# ============================

from src.page_objects import BasePage, BaseDialog, Element, image_locator

class CalculatorWindow(BasePage):
    """
    Page object for Calculator application.

    Encapsulates all UI elements and interactions.
    """
    def __init__(self, automator):
        super().__init__(automator)

        # Define all UI elements in one place
        self.button_1 = Element(
            image_locator("calc_1.png", description="Number 1 button"),
            automator
        )
        self.button_7 = Element(
            image_locator("calc_7.png", description="Number 7 button"),
            automator
        )
        self.button_plus = Element(
            image_locator("calc_plus.png", description="Plus button"),
            automator
        )
        self.button_equals = Element(
            image_locator("calc_equals.png", description="Equals button"),
            automator
        )

    def add_7_plus_1(self):
        """High-level business logic."""
        self.button_7.click()
        self.button_plus.click()
        self.button_1.click()
        self.button_equals.click()

    def enter_number(self, number: int):
        """Enter a number digit by digit."""
        for digit in str(number):
            button = getattr(self, f"button_{digit}")
            button.click()


class SaveDialog(BaseDialog):
    """
    Page object for Save dialog.

    Demonstrates dialog-specific features.
    """
    def __init__(self, automator):
        # Title locator to check if dialog is open
        title_locator = image_locator("save_dialog_title.png")
        super().__init__(automator, title_locator)

        self.filename_field = Element(
            image_locator("filename_field.png"),
            automator
        )
        self.save_button = Element(
            image_locator("save_button.png"),
            automator
        )
        self.cancel_button = Element(
            image_locator("cancel_button.png"),
            automator
        )

    def save_as(self, filename: str):
        """Save file with given name."""
        self.wait_for_open()  # Auto-waits for dialog
        self.filename_field.type_text(filename)
        self.save_button.click()
        self.wait_for_close()  # Waits for dialog to close


def demo_page_objects(automator):
    """
    Demonstrates Page Object Model usage.

    Old way (scattered, hard to maintain):
        automator.click_image("calc_7.png")
        automator.click_image("calc_plus.png")
        automator.click_image("calc_1.png")
        automator.click_image("calc_equals.png")

    New way (maintainable, reusable):
    """
    # Create page object
    calc = CalculatorWindow(automator)

    # Use high-level methods
    calc.add_7_plus_1()

    # Or use lower-level element access
    calc.button_7.click()


# Example 4: Data-Driven Testing
# ==============================

from src.data_driven import DataProvider, DataDrivenTest, ConfigManager

def demo_data_provider():
    """
    Demonstrates loading test data from files.

    Old way (duplicated test functions):
        def test_user_1(): login("user1", "pass1")
        def test_user_2(): login("user2", "pass2")
        # ... 98 more functions

    New way (one loop, many test cases):
    """
    # Load from CSV
    provider = DataProvider("examples/test_data.csv")

    for row in provider:
        username = row['username']
        password = row['password']
        expected = row['expected_result']

        print(f"Testing: {username}/{password} -> {expected}")
        # Run test with this data...

    # Also works with JSON and XML
    # provider = DataProvider("test_data.json")
    # provider = DataProvider("test_data.xml")


class LoginTest(DataDrivenTest):
    """
    Example of structured data-driven test.
    """
    def __init__(self, automator):
        super().__init__(
            data_file="examples/login_cases.csv",
            automator=automator
        )

    def setup(self):
        """Runs once before all tests."""
        print("Opening application...")

    def run_test(self, data):
        """Runs once for EACH row in CSV."""
        username = data['username']
        password = data['password']
        expected = data['expected_result']

        print(f"Testing login: {username}")
        # Perform login test...

    def teardown(self):
        """Runs once after all tests."""
        print("Closing application...")


def demo_config_manager():
    """
    Demonstrates environment configuration management.

    Allows switching between dev/staging/prod without changing code.
    """
    # Load environment-specific config
    config = ConfigManager("examples/config.json", environment="dev")

    app_path = config.get("app_path")
    timeout = config.get("timeout", default=30000)
    api_url = config.get("api.url")  # Supports dot notation

    print(f"App path: {app_path}")
    print(f"Timeout: {timeout}")
    print(f"API URL: {api_url}")


# Example 5: Complete Test Example
# ================================

def complete_example(automator):
    """
    Complete example combining all features.

    This shows how everything works together.
    """
    # 1. Create smart automator with auto-waiting
    smart = SmartAutomator(automator, timeout=10000)

    # 2. Create page objects
    calc = CalculatorWindow(smart.automator)

    # 3. Use expectations for robust assertions
    expect(smart.automator).to_have_image("calculator_title.png")

    # 4. Perform actions with page objects
    calc.add_7_plus_1()

    # 5. Verify results with expectations
    expect(smart.automator).to_have_image("result_8.png")

    # 6. Use data-driven testing for multiple scenarios
    provider = DataProvider("examples/calc_tests.csv")
    for row in provider:
        num1 = int(row['num1'])
        num2 = int(row['num2'])
        expected = int(row['result'])

        # Run calculation
        calc.enter_number(num1)
        calc.button_plus.click()
        calc.enter_number(num2)
        calc.button_equals.click()

        # Verify result
        expect(smart.automator).to_have_image(f"result_{expected}.png")


# Example test data files (create these)
# ======================================

def create_example_data_files():
    """
    Creates example data files for the demos.
    Run this once to set up example data.
    """
    import csv
    import json
    from pathlib import Path

    examples_dir = Path("examples")
    examples_dir.mkdir(exist_ok=True)

    # Create CSV example
    with open(examples_dir / "login_cases.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'password', 'expected_result'])
        writer.writerow(['user1', 'pass1', 'success'])
        writer.writerow(['admin', 'admin123', 'success'])
        writer.writerow(['invalid', 'wrong', 'error'])

    # Create JSON config example
    config = {
        "dev": {
            "app_path": "C:/Program Files/MyApp/dev/app.exe",
            "timeout": 5000,
            "api": {
                "url": "https://dev-api.example.com"
            }
        },
        "prod": {
            "app_path": "C:/Program Files/MyApp/app.exe",
            "timeout": 10000,
            "api": {
                "url": "https://api.example.com"
            }
        }
    }

    with open(examples_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("Example data files created in examples/")


if __name__ == "__main__":
    print("Screen Automator Framework Demo")
    print("=" * 50)
    print()
    print("This file contains examples of new framework features:")
    print("1. Auto-waiting and actionability")
    print("2. Expectations API")
    print("3. Page Object Model")
    print("4. Data-driven testing")
    print()
    print("To use these features:")
    print("1. Import the modules as shown in the examples")
    print("2. Create page objects for your UI")
    print("3. Use expectations instead of assertions")
    print("4. Load test data from files")
    print()
    print("See FRAMEWORK_GUIDE.md for full documentation!")
    print()

    # Create example data files
    create_example_data_files()
    print()
    print("✅ Example data files created!")
    print()
    print("Next steps:")
    print("1. Read FRAMEWORK_GUIDE.md")
    print("2. Review the examples in this file")
    print("3. Try the features in your own tests")
