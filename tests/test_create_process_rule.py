#!/usr/bin/env python3
"""
Create a sample rule targeting by process name
This provides more robust window targeting than using titles
"""

import os
import sys
import uuid

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.action_executor import create_wait_action
from src.rule_manager import Rule, RuleManager


def create_process_rule():
    print("🔧 Creating Process-Based Rule")
    print("=" * 50)

    # Initialize rule manager
    rule_manager = RuleManager()

    # Create a rule targeting python.exe (which runs the GUI)
    rule_id = str(uuid.uuid4())
    rule = Rule(
        id=rule_id,
        name="Process-Based Rule",
        image_path="",  # No image needed for screen_unchanged rule
        actions=[create_wait_action(2)],  # Simple wait action
        enabled=True,
        description="Rule that targets by process name instead of window title",
        priority=25,  # Very high priority
        condition_type="screen_unchanged",
        screen_unchanged_timeout=0.1,  # Very short timeout for testing
        target_window_process="python.exe",  # Target by process name
        window_exact_match=False,
        cluster_group="python_apps",  # Optional: group similar rules
    )

    # Save the rule
    rule_manager.rules[rule_id] = rule
    rule_manager.save_rule(rule)

    print("✅ Created process-based rule: 'Process-Based Rule'")
    print("   - Targets process: 'python.exe'")
    print("   - Condition: Screen unchanged for 0.1 minutes")
    print("   - Action: Wait 2 seconds")
    print("   - Cluster group: 'python_apps'")
    print("\nThis rule will target any window from the python.exe process.")
    print("This is more robust than targeting by window title.")


if __name__ == "__main__":
    create_process_rule()
