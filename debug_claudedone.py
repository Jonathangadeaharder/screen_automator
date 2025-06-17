#!/usr/bin/env python3
"""
Debug script for the Claude Done rule
"""

import time
from src.context_automator import ContextAwareAutomator

def debug_claudedone_rule():
    """Debug the Claude Done rule specifically"""
    print("🔍 Debugging Claude Done rule...")
    
    # Initialize automator
    automator = ContextAwareAutomator()
    
    # Find the Claude Done rule
    rules = automator.rule_manager.list_rules()
    claude_rule = None
    for rule in rules:
        if "claude done" in rule.name.lower():
            claude_rule = rule
            break
    
    if not claude_rule:
        print("❌ Claude Done rule not found!")
        return
    
    print(f"✅ Found rule: {claude_rule.name}")
    print(f"   - ID: {claude_rule.id}")
    print(f"   - Enabled: {claude_rule.enabled}")
    print(f"   - Condition: {claude_rule.condition_type}")
    print(f"   - Timeout: {claude_rule.screen_unchanged_timeout} minutes")
    print(f"   - Target process: {claude_rule.target_window_process}")
    print(f"   - Target class: {claude_rule.target_window_class}")
    print(f"   - Window ID method: {claude_rule.window_id_method}")
    
    if not claude_rule.enabled:
        print("❌ Rule is disabled!")
        return
    
    # Check if Windows Terminal is running
    print("\n🔍 Checking for Windows Terminal...")
    windows = automator.window_manager.get_running_windows()
    terminal_windows = []
    
    for window in windows:
        if ("windowsterminal" in window.process_name.lower() or 
            "CASCADIA_HOSTING_WINDOW_CLASS" in str(window.class_name)):
            terminal_windows.append(window)
            print(f"   ✅ Found: {window.title} (PID: {window.process_id}, Process: {window.process_name})")
            print(f"      Class: {window.class_name}")
    
    if not terminal_windows:
        print("❌ No Windows Terminal windows found!")
        return
    
    # Test rule targeting
    print(f"\n🎯 Testing rule targeting...")
    target_window = automator._get_rule_target_window(claude_rule)
    
    if not target_window:
        print("❌ Rule cannot find target window!")
        return
    
    print(f"   ✅ Target window found: {target_window.title}")
    
    # Set up monitoring callbacks
    def on_rule_triggered(rule):
        print(f"🎯 RULE TRIGGERED: {rule.name}")
    
    def on_error(error_msg):
        print(f"❌ ERROR: {error_msg}")
    
    automator.on_rule_triggered = on_rule_triggered
    automator.on_error = on_error
    
    # Set faster check interval for testing
    automator.set_check_interval(5)  # Check every 5 seconds
    
    print(f"\n⏱️ Starting monitoring (check interval: 5 seconds)...")
    print(f"   Rule will trigger after {claude_rule.screen_unchanged_timeout} minutes of no change")
    print(f"   Press Ctrl+C to stop")
    
    try:
        automator.start_monitoring()
        
        # Monitor for 60 seconds and show progress
        start_time = time.time()
        while time.time() - start_time < 60:
            time.sleep(5)
            elapsed = time.time() - start_time
            print(f"   📊 Monitoring... ({elapsed:.1f}s elapsed)")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    finally:
        automator.stop()
    
    print("✅ Debug complete")

if __name__ == "__main__":
    debug_claudedone_rule() 