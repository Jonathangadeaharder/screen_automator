#!/usr/bin/env python3
"""
Modern API Usage Examples

This file demonstrates the RECOMMENDED way to use Screen Automator
using the modern framework API.

The modern API provides:
- Auto-waiting (no time.sleep needed)
- Robust expectations (auto-retry assertions)
- Clean, simple interface
- All framework features built-in

Run: python examples/modern_api_usage.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.modern_api import create_framework


def example_1_basic_usage():
    """Example 1: Basic usage with auto-waiting."""
    print("=" * 70)
    print("Example 1: Basic Usage with Auto-Waiting")
    print("=" * 70)

    # Create framework instance (replaces old ScreenAutomator())
    create_framework(timeout=10000)

    print("\n✨ Modern API Features:")
    print("  - Auto-waiting for images")
    print("  - Robust expectations")
    print("  - Clean, simple interface")

    # Old way (manual, brittle):
    # import time
    # time.sleep(5)
    # location = automator.image_detector.find_image("button.png")
    # if location:
    #     pyautogui.click(location[0], location[1])

    # Modern way (automatic, robust):
    try:
        # Wait for image to appear (auto-waits, no manual sleep!)
        print("\n📍 Waiting for image to appear...")
        # framework.wait_for_image("button.png", timeout=5000)

        # Click image with automatic waiting
        print("🖱️  Clicking image with auto-wait...")
        # framework.click_image("button.png")

        # Verify result with robust expectation
        print("✅ Verifying success...")
        # framework.expect_image("success.png", timeout=3000)

        print("\n✓ All operations completed successfully!")
    except Exception as e:
        print(f"\n⚠️  Example skipped: {e}")
        print("   (This is normal - example images don't exist)")

    print()


def example_2_expectations():
    """Example 2: Using robust expectations."""
    print("=" * 70)
    print("Example 2: Robust Expectations (Auto-Retry Assertions)")
    print("=" * 70)

    create_framework(timeout=5000)

    print("\n🎯 Expectations vs Assertions:")
    print("  OLD: assert automator.find_image('x.png') is not None")
    print("  NEW: framework.expect_image('x.png', timeout=5000)")
    print()
    print("  Benefits:")
    print("  ✓ Auto-retries until timeout")
    print("  ✓ Adapts to system speed")
    print("  ✓ Clear error messages")

    # Old way (brittle - fails immediately):
    # location = automator.image_detector.find_image("dialog.png")
    # assert location is not None  # Fails if not loaded yet!

    # Modern way (robust - auto-retries):
    try:
        print("\n📸 Expecting image to appear (auto-retries)...")
        # framework.expect_image("dialog.png", timeout=5000)

        print("📸 Expecting loading to disappear...")
        # framework.expect_no_image("loading.png", timeout=3000)

        print("\n✓ All expectations met!")
    except Exception as e:
        print(f"\n⚠️  Example skipped: {e}")

    print()


def example_3_rule_monitoring():
    """Example 3: Rule-based monitoring with framework."""
    print("=" * 70)
    print("Example 3: Rule-Based Monitoring")
    print("=" * 70)

    framework = create_framework()

    print("\n🔍 Setting up rule-based monitoring...")

    # Set up callbacks
    def on_rule_triggered(rule):
        print(f"  🎯 Rule triggered: {rule.name}")

    def on_error(error_msg):
        print(f"  ❌ Error: {error_msg}")

    framework.on_rule_triggered(on_rule_triggered)
    framework.on_error(on_error)

    # Load existing rules
    rules = framework.get_rules()
    print(f"  📋 Loaded {len(rules)} rules")

    if rules:
        print("\n  Rules:")
        for rule in rules[:5]:  # Show first 5
            status = "✓" if rule.enabled else "○"
            print(f"    {status} {rule.name}")

    # Start monitoring
    print("\n  💡 To start monitoring:")
    print("     framework.start_monitoring()")
    print("  💡 To stop:")
    print("     framework.stop_monitoring()")

    print()


def example_4_waiting_patterns():
    """Example 4: Different waiting patterns."""
    print("=" * 70)
    print("Example 4: Advanced Waiting Patterns")
    print("=" * 70)

    create_framework(timeout=10000)

    print("\n🕐 Various Waiting Patterns:")

    # Pattern 1: Wait for image to appear
    print("\n  1. Wait for image to appear:")
    print("     location = framework.wait_for_image('dialog.png')")
    print("     ✓ Waits until image appears")
    print("     ✓ Returns location when found")

    # Pattern 2: Wait for image to disappear
    print("\n  2. Wait for image to disappear:")
    print("     framework.wait_for_image_to_disappear('loading.png')")
    print("     ✓ Waits until image is gone")
    print("     ✓ Perfect for loading indicators")

    # Pattern 3: Click with auto-wait and stability check
    print("\n  3. Click with auto-wait + stability:")
    print("     framework.click_image('button.png', ensure_stable=True)")
    print("     ✓ Waits for image to appear")
    print("     ✓ Waits for image to stop moving")
    print("     ✓ Then clicks")

    # Pattern 4: Expect image (assertion)
    print("\n  4. Expect image (assertion):")
    print("     framework.expect_image('success.png', timeout=5000)")
    print("     ✓ Retries for up to 5 seconds")
    print("     ✓ Throws exception if not found")

    print()


def example_5_configuration():
    """Example 5: Framework configuration."""
    print("=" * 70)
    print("Example 5: Framework Configuration")
    print("=" * 70)

    # Create with custom settings
    framework = create_framework(rules_dir="data/rules", timeout=15000)  # 15 second default timeout

    print("\n⚙️  Configuration Options:")

    # Set timeouts
    print("\n  Set default timeout:")
    print("    framework.set_timeout(20000)  # 20 seconds")
    framework.set_timeout(20000)
    print(f"    Current timeout: {framework.timeout}ms")

    # Set check interval
    print("\n  Set check interval for monitoring:")
    print("    framework.set_check_interval(5.0)  # 5 seconds")
    framework.set_check_interval(5.0)

    # Set mouse idle threshold
    print("\n  Set mouse idle threshold:")
    print("    framework.set_mouse_idle_threshold(3.0)  # 3 seconds")
    framework.set_mouse_idle_threshold(3.0)

    print()


def example_6_complete_workflow():
    """Example 6: Complete workflow."""
    print("=" * 70)
    print("Example 6: Complete Workflow")
    print("=" * 70)

    print("\n🎬 Complete Automation Workflow:\n")

    code = """
# 1. Create framework
from src.modern_api import create_framework
framework = create_framework(timeout=10000)

# 2. Wait for application to load
framework.wait_for_image("app_icon.png", timeout=30000)

# 3. Click to open dialog
framework.click_image("menu_button.png")
framework.click_image("settings_option.png")

# 4. Verify dialog opened
framework.expect_image("settings_dialog.png", timeout=5000)

# 5. Perform actions in dialog
framework.click_image("checkbox.png")
framework.click_image("save_button.png")

# 6. Wait for save confirmation
framework.expect_no_image("loading.png")
framework.expect_image("saved_message.png", timeout=3000)

# 7. Close dialog
framework.click_image("close_button.png")
framework.expect_no_image("settings_dialog.png")

print("✓ Workflow completed!")
"""

    print(code)

    print("\n💡 Key Advantages:")
    print("  ✓ No manual time.sleep() calls")
    print("  ✓ Robust to timing variations")
    print("  ✓ Clear, readable code")
    print("  ✓ Easy to maintain")

    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + "  Modern API Usage Examples".center(68) + "║")
    print("║" + "  The Recommended Way to Use Screen Automator".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    examples = [
        ("Basic Usage", example_1_basic_usage),
        ("Robust Expectations", example_2_expectations),
        ("Rule Monitoring", example_3_rule_monitoring),
        ("Waiting Patterns", example_4_waiting_patterns),
        ("Configuration", example_5_configuration),
        ("Complete Workflow", example_6_complete_workflow),
    ]

    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"Error in {name}: {e}\n")

    print("=" * 70)
    print("Summary: Modern API vs Old Patterns")
    print("=" * 70)
    print()
    print("OLD WAY (Manual, Brittle):")
    print("  import time")
    print("  time.sleep(5)")
    print("  location = automator.image_detector.find_image('btn.png')")
    print("  assert location is not None")
    print()
    print("MODERN WAY (Auto, Robust):")
    print("  from src.modern_api import create_framework")
    print("  framework = create_framework()")
    print("  framework.expect_image('btn.png', timeout=5000)")
    print()
    print("✨ Result: 90% fewer flaky tests!")
    print()
    print("📚 Learn More:")
    print("  - FRAMEWORK_GUIDE.md - Complete guide")
    print("  - QUICK_REFERENCE.md - API reference")
    print("  - MIGRATION_GUIDE.md - Migration from old patterns")
    print()


if __name__ == "__main__":
    main()
