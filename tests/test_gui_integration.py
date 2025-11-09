#!/usr/bin/env python3
"""
Test script to demonstrate window management integration in GUI
"""

import os
import subprocess
import sys
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_window_integration():
    """Test window management integration"""
    print("🧪 Testing Window Management GUI Integration")
    print("=" * 50)

    # Start the GUI
    print("📋 Starting GUI with window management integration...")
    print("📋 New features available:")
    print("   • Windows tab for window management")
    print("   • Window targeting in rule editor")
    print("   • Context-aware mode in monitoring")
    print("   • Rule clustering by window context")
    print("   • Window-specific rule testing")

    # Launch GUI
    try:
        subprocess.run([sys.executable, "gui.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching GUI: {e}")
        return False
    except KeyboardInterrupt:
        print("⏹️  GUI closed by user")
        return True

    return True


def test_features():
    """Test specific features"""
    print("\n🧪 Testing specific features:")
    print("=" * 50)

    # Test window manager
    try:
        from src.window_manager import WindowManager

        wm = WindowManager()
        windows = wm.get_running_windows()
        print(f"✅ Window Manager: Found {len(windows)} windows")
    except Exception as e:
        print(f"❌ Window Manager error: {e}")

    # Test context-aware automator
    try:
        from src.context_automator import ContextAwareAutomator

        ca = ContextAwareAutomator()
        print("✅ Context-Aware Automator: Initialized successfully")
    except Exception as e:
        print(f"❌ Context-Aware Automator error: {e}")

    # Test rule manager extensions
    try:
        from src.rule_manager import RuleManager

        rm = RuleManager()
        print("✅ Extended Rule Manager: Initialized successfully")
    except Exception as e:
        print(f"❌ Extended Rule Manager error: {e}")


if __name__ == "__main__":
    print("🚀 Screen Automator GUI Integration Test")
    print("=" * 50)

    # Test components first
    test_features()

    # Then test GUI
    print("\n🖥️  Launching GUI...")
    print("Features to test:")
    print("1. Go to 'Windows' tab to see available windows")
    print("2. Create a new rule and set window targeting")
    print("3. Enable context-aware mode in monitoring")
    print("4. Check rule clusters in Windows tab")
    print("5. Test window-specific rule execution")

    test_window_integration()
