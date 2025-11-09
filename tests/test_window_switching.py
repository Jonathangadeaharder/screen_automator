#!/usr/bin/env python3
"""
Debug script to test window switching functionality
"""

import os
import sys
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.window_manager import WindowManager


def test_window_switching():
    print("🔧 Window Switching Debug Test")
    print("=" * 50)

    # Initialize components
    print("1. Initializing window manager...")
    window_manager = WindowManager()

    # Get all windows
    print("\n2. Getting all windows...")
    windows = window_manager.get_running_windows(include_minimized=False)
    print(f"   Found {len(windows)} windows")

    if not windows:
        print("   ❌ No windows found!")
        return

    # Display available windows
    print("\n3. Available windows:")
    for i, window in enumerate(windows):
        print(f"   {i+1}. '{window.title[:50]}' ({window.process_name})")

    # Get active window
    print("\n4. Getting active window...")
    active_window = window_manager.get_active_window()
    if active_window:
        print(f"   Current active window: '{active_window.title}' ({active_window.process_name})")
    else:
        print("   ❌ Could not get active window!")
        return

    # Test window switching
    print("\n5. Testing window switching...")

    # Choose a different window to switch to
    target_window = None
    for window in windows:
        if window.handle != active_window.handle:
            target_window = window
            break

    if not target_window:
        print("   ❌ Could not find a different window to switch to!")
        return

    print(f"   Will switch to: '{target_window.title}' ({target_window.process_name})")

    # Switch to target window
    print("   Switching window in 2 seconds...")
    time.sleep(2)
    success = window_manager.switch_to_window(target_window)

    if success:
        print("   ✅ Successfully switched to target window")
    else:
        print("   ❌ Failed to switch to target window")

    # Wait a moment to see the switch
    print("   Waiting 3 seconds to observe window switch...")
    time.sleep(3)

    # Restore original window
    print("\n6. Restoring original window...")
    success = window_manager.restore_original_window()

    if success:
        print("   ✅ Successfully restored original window")
    else:
        print("   ❌ Failed to restore original window")

    print("\n✅ Window switching test completed!")


if __name__ == "__main__":
    test_window_switching()
