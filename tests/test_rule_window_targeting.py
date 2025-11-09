#!/usr/bin/env python3
"""
Debug script to test rule window targeting
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.rule_manager import RuleManager
from src.window_manager import WindowManager


def test_rule_window_targeting():
    print("🔧 Rule Window Targeting Debug Test")
    print("=" * 50)

    # Initialize components
    print("1. Initializing components...")
    rule_manager = RuleManager()
    window_manager = WindowManager()

    # Get all rules
    print("\n2. Getting all rules...")
    rules = rule_manager.list_rules()
    enabled_rules = [r for r in rules if r.enabled]

    print(f"   Found {len(rules)} rules, {len(enabled_rules)} enabled")

    if not enabled_rules:
        print("   ❌ No enabled rules found!")
        return

    # Get all windows
    print("\n3. Getting all windows...")
    windows = window_manager.get_running_windows(include_minimized=False)
    print(f"   Found {len(windows)} windows")

    if not windows:
        print("   ❌ No windows found!")
        return

    # Display window targets for rules
    print("\n4. Rule window targeting:")
    for i, rule in enumerate(enabled_rules):
        window_target = "Any window"
        if rule.target_window_title:
            window_target = f"Title: {rule.target_window_title}"
        elif rule.target_window_process:
            window_target = f"Process: {rule.target_window_process}"

        print(f"   Rule {i+1}: '{rule.name}' -> {window_target}")

    # Test window matching
    print("\n5. Testing window matching for each rule...")

    for rule in enabled_rules:
        print(f"\n   Testing rule: '{rule.name}'")

        matching_windows = []
        for window in windows:
            if rule.target_window_title:
                if rule.window_exact_match:
                    if rule.target_window_title == window.title:
                        matching_windows.append(window)
                else:
                    if rule.target_window_title.lower() in window.title.lower():
                        matching_windows.append(window)
            elif rule.target_window_process:
                if rule.target_window_process.lower() in window.process_name.lower():
                    matching_windows.append(window)
            else:
                # Rule targets any window
                matching_windows.append(window)
                break  # Just add one window to avoid huge list

        if matching_windows:
            print(f"   ✅ Found {len(matching_windows)} matching windows")
            for j, window in enumerate(matching_windows[:3]):  # Show first 3
                print(f"      {j+1}. '{window.title[:50]}' ({window.process_name})")
            if len(matching_windows) > 3:
                print(f"      ... and {len(matching_windows) - 3} more")
        else:
            print(f"   ❌ No matching windows found for rule '{rule.name}'")

    # Test rule clustering
    print("\n6. Testing rule clustering...")
    clusters = rule_manager.get_rules_by_cluster()
    print(f"   Rules organized into {len(clusters)} clusters:")

    for cluster_key, cluster_rules in clusters.items():
        print(f"   Cluster '{cluster_key}': {len(cluster_rules)} rules")
        for rule in cluster_rules:
            print(f"      • {rule.name}")

    print("\n✅ Rule window targeting test completed!")


if __name__ == "__main__":
    test_rule_window_targeting()
