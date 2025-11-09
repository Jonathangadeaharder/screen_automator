"""
Practical Integration Example: Using New Framework Features with Existing Code

This example demonstrates how to use the new framework features with the existing
screen_automator codebase. It shows real-world usage patterns.

Author: Screen Automator Framework Team
"""

import sys
import os

# Add parent directory to path to import screen_automator modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.automator import ScreenAutomator
from src.actionability import AutoWaiter, SmartAutomator
from src.expectations import expect, wait_for
from src.page_objects import BasePage, Element, image_locator
from src.data_driven import DataProvider, ConfigManager


# ==============================================================================
# Example 1: Enhancing Existing Automator with Auto-Waiting
# ==============================================================================

def example_1_basic_auto_waiting():
    """
    Shows how to add auto-waiting to existing screen_automator code.

    Before: Relied on check_interval and manual timing
    After: Explicit, reliable auto-waiting
    """
    print("Example 1: Basic Auto-Waiting")
    print("=" * 60)

    # Create existing automator
    automator = ScreenAutomator()

    # Wrap with SmartAutomator for auto-waiting
    smart = SmartAutomator(automator.image_detector, timeout=10000)

    # Old way (unreliable):
    # time.sleep(5)
    # location = automator.image_detector.find_image("button.png")

    # New way (robust):
    try:
        smart.click_image("data/images/trigger_button.png")
        print("✅ Button clicked with auto-waiting!")
    except Exception as e:
        print(f"⚠️  Button not found: {e}")

    print()


# ==============================================================================
# Example 2: Using Expectations for Robust Assertions
# ==============================================================================

def example_2_expectations_with_rules():
    """
    Shows how to use expectations to verify rule execution.

    Before: Manual checking with potential race conditions
    After: Auto-retrying expectations
    """
    print("Example 2: Expectations with Rule Verification")
    print("=" * 60)

    automator = ScreenAutomator()

    # Load rules
    rules = automator.rule_manager.get_all_rules()
    print(f"Loaded {len(rules)} rules")

    # Use expectations to verify rule triggers
    for rule in rules[:3]:  # Check first 3 rules
        trigger_image = rule.trigger_image
        if trigger_image and os.path.exists(trigger_image):
            print(f"\nChecking rule: {rule.name}")

            # Old way (brittle):
            # location = automator.image_detector.find_image(trigger_image)
            # assert location is not None

            # New way (robust):
            try:
                expect(automator.image_detector).to_have_image(
                    trigger_image,
                    timeout=2000  # 2 second timeout for quick check
                )
                print(f"  ✅ Trigger image found: {os.path.basename(trigger_image)}")
            except Exception:
                print(f"  ⚠️  Trigger image not visible: {os.path.basename(trigger_image)}")

    print()


# ==============================================================================
# Example 3: Page Object Model for GUI Automation
# ==============================================================================

class ScreenAutomatorGUI(BasePage):
    """
    Page Object for the Screen Automator GUI application.

    This encapsulates all UI elements and interactions with the GUI.
    """

    def __init__(self, automator):
        super().__init__(automator)

        # Define all UI elements (these would be actual image files in practice)
        self.start_button = Element(
            image_locator("gui/start_button.png", description="Start monitoring"),
            automator
        )
        self.stop_button = Element(
            image_locator("gui/stop_button.png", description="Stop monitoring"),
            automator
        )
        self.add_rule_button = Element(
            image_locator("gui/add_rule.png", description="Add new rule"),
            automator
        )
        self.settings_button = Element(
            image_locator("gui/settings.png", description="Settings"),
            automator
        )

    def start_monitoring(self):
        """Start the monitoring process."""
        self.start_button.click()

    def stop_monitoring(self):
        """Stop the monitoring process."""
        self.stop_button.click()

    def add_new_rule(self):
        """Open the add rule dialog."""
        self.add_rule_button.click()
        return AddRuleDialog(self.automator)

    def open_settings(self):
        """Open settings dialog."""
        self.settings_button.click()
        return SettingsDialog(self.automator)


class AddRuleDialog(BasePage):
    """
    Page Object for the Add Rule dialog.
    """

    def __init__(self, automator):
        super().__init__(automator)

        self.rule_name_field = Element(
            image_locator("gui/rule_name_field.png"),
            automator
        )
        self.trigger_image_button = Element(
            image_locator("gui/select_trigger.png"),
            automator
        )
        self.save_button = Element(
            image_locator("gui/save_rule.png"),
            automator
        )

    def create_rule(self, name: str):
        """Create a new rule with given name."""
        self.rule_name_field.type_text(name)
        self.save_button.click()


class SettingsDialog(BasePage):
    """Page Object for Settings dialog."""

    def __init__(self, automator):
        super().__init__(automator)
        # Define settings UI elements here


def example_3_page_objects():
    """
    Shows how to use Page Object Model with screen_automator GUI.

    Before: Direct image clicking scattered across code
    After: Clean, maintainable page objects
    """
    print("Example 3: Page Object Model")
    print("=" * 60)

    automator = ScreenAutomator()

    # Create page object for the GUI
    gui = ScreenAutomatorGUI(automator.image_detector)

    print("Using page objects for clean automation:")
    print("  - Start monitoring: gui.start_monitoring()")
    print("  - Add rule: dialog = gui.add_new_rule()")
    print("  - Create rule: dialog.create_rule('My Rule')")
    print()
    print("✅ Page objects provide maintainable, reusable automation!")
    print()


# ==============================================================================
# Example 4: Data-Driven Rule Creation
# ==============================================================================

def example_4_data_driven_rules():
    """
    Shows how to use data-driven testing to create multiple rules.

    Before: Manually create each rule
    After: Load from data file and create in loop
    """
    print("Example 4: Data-Driven Rule Creation")
    print("=" * 60)

    # Create sample data file
    import json

    sample_rules = [
        {
            "name": "Auto-save document",
            "trigger_image": "data/images/unsaved_indicator.png",
            "actions": ["click_save_button"]
        },
        {
            "name": "Close popup",
            "trigger_image": "data/images/popup.png",
            "actions": ["click_close"]
        },
        {
            "name": "Refresh page",
            "trigger_image": "data/images/error.png",
            "actions": ["press_f5"]
        }
    ]

    # Save to file
    data_file = "examples/rules_data.json"
    os.makedirs("examples", exist_ok=True)
    with open(data_file, "w") as f:
        json.dump(sample_rules, f, indent=2)

    # Load and process with DataProvider
    provider = DataProvider(data_file)

    print(f"Loading {len(provider)} rules from {data_file}:")
    for row in provider:
        print(f"  - {row['name']}: {row['trigger_image']}")

    print()
    print("✅ Data-driven approach allows bulk rule management!")
    print()


# ==============================================================================
# Example 5: Configuration Management for Different Environments
# ==============================================================================

def example_5_config_management():
    """
    Shows how to use ConfigManager for environment-specific settings.

    Before: Hard-coded values in code
    After: External config files for each environment
    """
    print("Example 5: Configuration Management")
    print("=" * 60)

    # Create sample config file
    config_data = {
        "dev": {
            "rules_dir": "data/rules_dev",
            "check_interval": 5.0,
            "mouse_idle_threshold": 3.0,
            "log_level": "DEBUG"
        },
        "prod": {
            "rules_dir": "data/rules",
            "check_interval": 10.0,
            "mouse_idle_threshold": 5.0,
            "log_level": "INFO"
        }
    }

    config_file = "examples/automator_config.json"
    import json
    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=2)

    # Load config for different environments
    dev_config = ConfigManager(config_file, environment="dev")
    prod_config = ConfigManager(config_file, environment="prod")

    print("Dev environment:")
    print(f"  - Rules dir: {dev_config.get('rules_dir')}")
    print(f"  - Check interval: {dev_config.get('check_interval')}s")
    print(f"  - Log level: {dev_config.get('log_level')}")

    print("\nProd environment:")
    print(f"  - Rules dir: {prod_config.get('rules_dir')}")
    print(f"  - Check interval: {prod_config.get('check_interval')}s")
    print(f"  - Log level: {prod_config.get('log_level')}")

    print()
    print("✅ Config management enables easy environment switching!")
    print()


# ==============================================================================
# Example 6: Complete Integration - Robust Rule Monitoring
# ==============================================================================

def example_6_complete_integration():
    """
    Complete example: Combining all framework features for robust monitoring.
    """
    print("Example 6: Complete Integration")
    print("=" * 60)

    # 1. Load configuration
    try:
        config = ConfigManager("examples/automator_config.json", environment="dev")
        rules_dir = config.get("rules_dir", default="data/rules")
        check_interval = config.get("check_interval", default=10.0)
        print(f"✅ Configuration loaded")
    except Exception:
        rules_dir = "data/rules"
        check_interval = 10.0
        print(f"⚠️  Using default configuration")

    # 2. Create automator with config
    automator = ScreenAutomator(rules_dir=rules_dir)
    automator.check_interval = check_interval

    # 3. Wrap with smart features
    smart = SmartAutomator(automator.image_detector, timeout=10000)

    # 4. Load rules
    rules = automator.rule_manager.get_all_rules()
    print(f"✅ Loaded {len(rules)} rules")

    # 5. Verify rules with expectations
    print("\nVerifying rule triggers...")
    valid_rules = 0
    for rule in rules[:5]:  # Check first 5
        if rule.trigger_image and os.path.exists(rule.trigger_image):
            try:
                # Use expectation with short timeout
                expect(automator.image_detector).to_have_image(
                    rule.trigger_image,
                    timeout=1000
                )
                print(f"  ✅ {rule.name}: Trigger visible")
                valid_rules += 1
            except Exception:
                print(f"  ⏸️  {rule.name}: Trigger not visible (will check later)")

    print(f"\n✅ {valid_rules} rules have visible triggers")

    # 6. Monitor with auto-waiting
    print("\n💡 Framework features enabled:")
    print("  - Auto-waiting for reliable image detection")
    print("  - Expectations for robust verification")
    print("  - Configuration management for environments")
    print("  - Ready for data-driven rule management")

    print()


# ==============================================================================
# Main Runner
# ==============================================================================

def main():
    """Run all integration examples."""

    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  Screen Automator Framework - Integration Examples".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    examples = [
        ("Basic Auto-Waiting", example_1_basic_auto_waiting),
        ("Expectations with Rules", example_2_expectations_with_rules),
        ("Page Object Model", example_3_page_objects),
        ("Data-Driven Rules", example_4_data_driven_rules),
        ("Config Management", example_5_config_management),
        ("Complete Integration", example_6_complete_integration),
    ]

    for i, (name, func) in enumerate(examples, 1):
        try:
            func()
        except Exception as e:
            print(f"⚠️  Example {i} error: {e}")
            print()

    print("=" * 80)
    print("All examples completed!")
    print()
    print("Next steps:")
    print("  1. Review FRAMEWORK_GUIDE.md for detailed documentation")
    print("  2. Try these patterns in your own automation scripts")
    print("  3. Create page objects for your application's UI")
    print("  4. Set up data-driven tests for your scenarios")
    print()


if __name__ == "__main__":
    main()
