#!/usr/bin/env python3
"""
Debug script to test context-aware automation
Run this to see if your rules and window targeting are working
"""

import sys
import os
import time
import threading

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.context_automator import ContextAwareAutomator
from src.rule_manager import RuleManager
from src.window_manager import WindowManager

def test_context_automation():
    print("🔧 Context Automation Debug Test")
    print("=" * 50)
    
    # Initialize components
    print("1. Initializing components...")
    automator = ContextAwareAutomator()
    window_manager = WindowManager()
    rule_manager = automator.rule_manager
    
    # Check for rules
    print("\n2. Checking existing rules...")
    rules = rule_manager.list_rules()
    enabled_rules = [r for r in rules if r.enabled]
    
    print(f"   Total rules: {len(rules)}")
    print(f"   Enabled rules: {len(enabled_rules)}")
    
    if enabled_rules:
        print("   Enabled rules:")
        for rule in enabled_rules:
            window_target = "Any window"
            if rule.target_window_title:
                window_target = f"Title: {rule.target_window_title}"
            elif rule.target_window_process:
                window_target = f"Process: {rule.target_window_process}"
            print(f"     • {rule.name} -> {window_target}")
    else:
        print("   ⚠️  No enabled rules found!")
        print("      You need to create and enable some rules first.")
        return
    
    # Check window targeting
    print("\n3. Testing window detection...")
    windows = window_manager.get_running_windows(include_minimized=False)
    print(f"   Found {len(windows)} windows")
    
    if windows:
        print("   Sample windows:")
        for window in windows[:5]:  # Show first 5
            print(f"     • {window.title[:50]} ({window.process_name})")
    
    # Test rule clustering
    print("\n4. Testing rule clustering...")
    clusters = automator.get_rule_clusters()
    print(f"   Rules organized into {len(clusters)} clusters:")
    
    for cluster_key, cluster_rules in clusters.items():
        window_desc = cluster_key if cluster_key != 'any_window' else 'Any Window'
        print(f"     • {window_desc}: {len(cluster_rules)} rules")
    
    # Test monitoring (short duration)
    print("\n5. Testing monitoring (5 seconds)...")
    print("   This will check if rules would trigger...")
    
    # Set up callbacks to see what happens
    triggered_rules = []
    context_changes = []
    
    def on_rule_triggered(rule):
        triggered_rules.append(rule.name)
        print(f"   🎯 Rule triggered: {rule.name}")
    
    def on_window_context_changed(old_window, new_window):
        old_title = old_window.title if old_window else "None"
        new_title = new_window.title if new_window else "None"
        context_changes.append((old_title, new_title))
        print(f"   🪟 Context changed: {old_title[:30]} -> {new_title[:30]}")
    
    def on_cluster_execution_start(cluster_info, rule_count):
        print(f"   🗂️  Executing cluster: {cluster_info} ({rule_count} rules)")
    
    automator.on_rule_triggered = on_rule_triggered
    automator.on_window_context_changed = on_window_context_changed
    automator.on_cluster_execution_start = on_cluster_execution_start
    
    # Set short interval for testing
    automator.set_check_interval(1)
    
    # Start monitoring
    automator.start_monitoring()
    print("   Monitoring started... (watching for 5 seconds)")
    
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n   Interrupted by user")
    
    # Stop monitoring
    automator.stop()
    
    # Results
    print("\n6. Test Results:")
    print(f"   Rules triggered: {len(triggered_rules)}")
    if triggered_rules:
        for rule_name in triggered_rules:
            print(f"     • {rule_name}")
    
    print(f"   Context changes: {len(context_changes)}")
    if context_changes:
        for old_title, new_title in context_changes:
            print(f"     • {old_title} -> {new_title}")
    
    if not triggered_rules and not context_changes:
        print("   ℹ️  No activity detected. This could mean:")
        print("      - No rule conditions were met")
        print("      - No window changes occurred")
        print("      - Rules are working correctly but no triggers happened")
    
    print("\n✅ Debug test completed!")

if __name__ == "__main__":
    test_context_automation() 