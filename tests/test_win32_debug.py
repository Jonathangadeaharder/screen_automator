#!/usr/bin/env python3
"""
Test if Windows APIs are available
"""

import platform

print(f"System: {platform.system()}")

if platform.system() == "Windows":
    try:
        import psutil
        import win32con
        import win32gui
        import win32process

        print("✅ All win32 modules imported successfully")
        print(f"win32gui version: {win32gui.__file__}")

        # Test basic functionality
        hwnd = win32gui.GetForegroundWindow()
        print(f"✅ Current window handle: {hwnd}")

        title = win32gui.GetWindowText(hwnd)
        print(f"✅ Current window title: {title}")

        HAS_WIN32 = True
        print("✅ HAS_WIN32 = True")

    except ImportError as e:
        print(f"❌ ImportError: {e}")
        HAS_WIN32 = False
        print("❌ HAS_WIN32 = False")

    except Exception as e:
        print(f"❌ Other error: {e}")
        HAS_WIN32 = False
else:
    print("Not running on Windows")
    HAS_WIN32 = False

print(f"\nFinal HAS_WIN32: {HAS_WIN32}")
