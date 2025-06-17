#!/usr/bin/env python3
"""
Test script to demonstrate improved window focus behavior
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_window_focus_behavior():
    """Test the new window focus behavior"""
    print("🔍 Testing Window Focus Behavior")
    print("=" * 50)
    
    try:
        from src.context_automator import ContextAwareAutomator
        from src.window_manager import WindowManager
        
        # Create context-aware automator
        automator = ContextAwareAutomator()
        window_manager = WindowManager()
        
        print("✅ Context-aware automator initialized")
        
        # Get available windows
        windows = window_manager.get_running_windows()
        print(f"📋 Found {len(windows)} windows")
        
        if len(windows) < 2:
            print("❌ Need at least 2 windows to test focus behavior")
            return
        
        # Show window focus settings
        print(f"🎯 Keep context focused: {automator.keep_context_window_focused}")
        print(f"⏱️  Cluster cooldown: {automator.cluster_cooldown}s")
        
        # Test focus behavior
        target_window = None
        for window in windows:
            if window.title.strip() and "python" not in window.title.lower():
                target_window = window
                break
        
        if target_window:
            print(f"\n🪟 Testing window focus with: {target_window.title}")
            print("📋 Instructions:")
            print("1. The target window should come to front when rules are triggered")
            print("2. With 'keep focused' enabled, it will stay in front")
            print("3. Move your mouse to restore the original window")
            print("4. Use the GUI checkbox to change this behavior")
            
            # Switch to target window
            success = window_manager.switch_to_window(target_window)
            if success:
                print(f"✅ Successfully switched to: {target_window.title}")
                print("🎯 Window should now be in front!")
                
                time.sleep(3)
                print("🔄 Restoring original window...")
                window_manager.restore_original_window()
                print("✅ Original window restored")
            else:
                print("❌ Failed to switch to target window")
        else:
            print("❌ No suitable target window found")
        
        print("\n📋 To test the full behavior:")
        print("1. Launch the GUI: python gui.py")
        print("2. Enable context-aware mode in Monitoring tab")
        print("3. Create a rule targeting a specific window")
        print("4. Start monitoring")
        print("5. Wait for rule trigger - target window will come to front")
        print("6. Use 'Keep context window focused' checkbox to control behavior")
        
    except Exception as e:
        print(f"❌ Error testing window focus: {e}")

if __name__ == "__main__":
    test_window_focus_behavior() 