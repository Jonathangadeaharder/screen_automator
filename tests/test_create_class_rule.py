#!/usr/bin/env python3
"""
Create a sample rule targeting by window class name
This provides the most robust window targeting method
"""

import os
import sys
import time
import uuid

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.action_executor import create_wait_action
from src.rule_manager import Rule, RuleManager
from src.window_manager import WindowManager


def create_class_rule():
    print("🔧 Creating Class-Based Rule")
    print("=" * 50)

    # Initialize components
    rule_manager = RuleManager()
    window_manager = WindowManager()

    # Get current window to find its class
    print("Getting current active window...")
    active_window = window_manager.get_active_window()

    if not active_window or not active_window.class_name:
        print("❌ Could not get active window class name")
        return

    print(f"Active window: '{active_window.title}'")
    print(f"Window class: '{active_window.class_name}'")

    # Create a rule targeting the current window by class name
    rule_id = str(uuid.uuid4())
    rule = Rule(
        id=rule_id,
        name="Class-Based Rule",
        image_path="",  # No image needed for screen_unchanged rule
        actions=[create_wait_action(2)],  # Simple wait action
        enabled=True,
        description="Rule that targets by window class name - most robust method",
        priority=10,  # Highest priority
        condition_type="screen_unchanged",
        screen_unchanged_timeout=0.1,  # Very short timeout for testing
        target_window_class=active_window.class_name,  # Target by class name
        window_id_method="class",  # Explicitly use class-based targeting
        cluster_group="class_based",  # Optional: group similar rules
    )

    # Save the rule
    rule_manager.rules[rule_id] = rule
    rule_manager.save_rule(rule)

    print(f"\n✅ Created class-based rule: 'Class-Based Rule'")
    print(f"   - Targets window class: '{active_window.class_name}'")
    print(f"   - Window title: '{active_window.title}'")
    print(f"   - Process: '{active_window.process_name}'")
    print(f"   - Condition: Screen unchanged for 0.1 minutes")
    print(f"   - Action: Wait 2 seconds")
    print(f"   - Identification method: class")
    print(f"   - Cluster group: 'class_based'")
    print("\nThis rule will target any window with the same class.")
    print("This is the most robust targeting method as class names rarely change.")


if __name__ == "__main__":
    create_class_rule()
