#!/usr/bin/env python3
"""
Test script to demonstrate cursor position restoration functionality
"""

import os
import sys
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_cursor_restoration():
    """Test cursor position restoration"""
    print("🖱️  Testing Cursor Position Restoration")
    print("=" * 50)

    try:
        from src.context_automator import ContextAwareAutomator
        from src.window_manager import WindowManager

        # Create context-aware automator
        automator = ContextAwareAutomator()
        window_manager = WindowManager()

        print("✅ Context-aware automator initialized")

        # Check PyAutoGUI availability
        cursor_info = automator.get_cursor_info()
        print(f"🖱️  PyAutoGUI available: {cursor_info['has_pyautogui']}")

        if cursor_info["has_pyautogui"]:
            print(f"📍 Current cursor position: {cursor_info['current_pos']}")
        else:
            print("❌ PyAutoGUI not available - cursor restoration will not work")
            return

        # Get available windows
        windows = window_manager.get_running_windows()
        target_window = None

        for window in windows:
            if window.title.strip() and "python" not in window.title.lower():
                target_window = window
                break

        if not target_window:
            print("❌ No suitable target window found for testing")
            return

        print(f"\n🪟 Testing with window: {target_window.title}")
        print("\n📋 Test Procedure:")
        print("1. Your current cursor position will be stored")
        print("2. Window will switch to target")
        print("3. Wait 3 seconds, then move your mouse")
        print("4. Your cursor should return to the original position")
        print("5. Original window should be restored")

        input("\nPress Enter to start the test...")

        # Get initial cursor position
        print("📍 Storing current cursor position...")

        # Simulate context switching
        success = automator._switch_to_context_window(target_window)
        if success:
            print(f"✅ Switched to: {target_window.title}")
            print(f"📍 Original cursor position stored: {automator.original_cursor_pos}")

            print("\n⏳ Waiting 3 seconds... MOVE YOUR MOUSE to trigger restoration!")
            time.sleep(3)

            # Check if user moved mouse (simulate mouse idle check failing)
            print("🖱️  Simulating mouse movement detection...")
            automator._restore_original_context()

            print("✅ Context restoration triggered!")

            # Show final cursor info
            final_info = automator.get_cursor_info()
            print(f"📍 Final cursor position: {final_info['current_pos']}")

        else:
            print("❌ Failed to switch to target window")

        print("\n📋 In the real application:")
        print("• Rules execute → Target window comes to front")
        print("• Your cursor position is automatically stored")
        print("• When you move mouse → Everything restores to original state")
        print("• Both window context AND cursor position return to where you were")
        print("• Use 'Restore Context' button for manual restoration")

    except Exception as e:
        print(f"❌ Error testing cursor restoration: {e}")


def test_gui_integration():
    """Test GUI integration with cursor restoration"""
    print("\n🖥️  GUI Integration Test")
    print("=" * 30)

    print("📋 New GUI features for cursor restoration:")
    print("• 'Restore Context' button in Windows tab")
    print("• Automatic cursor position logging")
    print("• Real-time cursor position tracking")
    print("• Manual restoration capability")

    print("\n🔧 How to test in GUI:")
    print("1. Launch GUI: python gui.py")
    print("2. Enable context-aware mode")
    print("3. Create rule targeting specific window")
    print("4. Start monitoring")
    print("5. When rule triggers → note cursor is stored")
    print("6. Move mouse → cursor and window restore automatically")
    print("7. Use 'Restore Context' button for manual control")


if __name__ == "__main__":
    print("🧪 Screen Automator Cursor Restoration Test")
    print("=" * 50)

    test_cursor_restoration()
    test_gui_integration()
