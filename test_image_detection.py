#!/usr/bin/env python
import os
import sys
import time
from typing import Optional
import cv2
import numpy as np

# Import necessary modules from the project
from src.image_detector import ImageDetector
from src.window_manager import WindowManager, WindowInfo

def test_window_screenshot_methods():
    """Test which window screenshot method works best on this system"""
    print("==== Testing Window Screenshot Methods ====")
    
    # Initialize window manager
    wm = WindowManager()
    
    # Get active window
    active_window = wm.get_active_window()
    if not active_window:
        print("❌ Error: Could not get active window")
        return False
        
    print(f"🪟 Using active window: {active_window.title} (Class: {active_window.class_name})")
    
    # Test 1: Direct Windows Screenshot (Windows-only)
    if wm.system == "Windows":
        print("\nTest 1: Direct Windows Screenshot (win32ui + BitBlt)")
        try:
            start_time = time.time()
            screenshot = wm._get_window_screenshot_windows(active_window)
            elapsed = time.time() - start_time
            
            if screenshot is not None:
                print(f"✅ Success! Screenshot taken in {elapsed:.3f}s")
                print(f"   Size: {screenshot.width}x{screenshot.height}")
                screenshot.save("test_windows_screenshot.png")
                print("   Saved to: test_windows_screenshot.png")
                print("   This is the most reliable and recommended method.")
            else:
                print("❌ Failed: Could not capture window content directly")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("\nTest 1: Direct Windows Screenshot - Skipped (Windows only)")
    
    # Test 2: Fallback Region Screenshot
    print("\nTest 2: PyAutoGUI Region Screenshot")
    try:
        start_time = time.time()
        screenshot = wm._get_window_screenshot_fallback(active_window)
        elapsed = time.time() - start_time
        
        if screenshot is not None:
            print(f"✅ Success! Screenshot taken in {elapsed:.3f}s")
            print(f"   Size: {screenshot.width}x{screenshot.height}")
            screenshot.save("test_pyautogui_region.png")
            print("   Saved to: test_pyautogui_region.png")
        else:
            print("❌ Failed: Could not capture window region")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Full Screen Fallback
    print("\nTest 3: Full Screen Fallback")
    try:
        start_time = time.time()
        screenshot = wm._get_fullscreen_screenshot_fallback()
        elapsed = time.time() - start_time
        
        if screenshot is not None:
            print(f"✅ Success! Screenshot taken in {elapsed:.3f}s")
            print(f"   Size: {screenshot.width}x{screenshot.height}")
            screenshot.save("test_full_screen.png")
            print("   Saved to: test_full_screen.png")
        else:
            print("❌ Failed: Could not capture full screen")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test if CV2 can handle the images correctly
    print("\nVerifying image compatibility with OpenCV...")
    image_paths = ["test_windows_screenshot.png", "test_pyautogui_region.png", "test_full_screen.png"]
    for path in image_paths:
        if os.path.exists(path):
            img = cv2.imread(path)
            if img is not None:
                print(f"✅ OpenCV can read {path} - Size: {img.shape[1]}x{img.shape[0]}")
            else:
                print(f"❌ OpenCV failed to read {path}")
    
    return True

def test_image_detection():
    """Test image detection functionality"""
    print("\n==== Testing Image Detection ====")
    
    detector = ImageDetector(confidence_threshold=0.8)
    
    # Create a small test image to search for
    test_image_path = "test_target.png"
    if not os.path.exists(test_image_path):
        import pyautogui
        # Capture a small region of the screen to use as a target
        region_x, region_y = 100, 100
        region_width, region_height = 200, 200
        print(f"Creating test target image from screen region: {region_x},{region_y} {region_width}x{region_height}")
        
        screenshot = pyautogui.screenshot(region=(region_x, region_y, region_width, region_height))
        screenshot.save(test_image_path)
        print(f"Test target saved to: {test_image_path}")
    
    # Test finding the image with direct screen capture
    print("\nTest 1: Finding image with direct screen capture")
    start_time = time.time()
    screen = detector.capture_screen()
    result = detector.find_image_on_screen(test_image_path, screen)
    elapsed = time.time() - start_time
    
    if result:
        x, y, width, height = result
        print(f"✅ Image found at {x},{y} (size: {width}x{height}) in {elapsed:.3f}s")
    else:
        print(f"❌ Image not found in screen capture (took {elapsed:.3f}s)")
    
    # Test using Windows-specific screenshot if available
    wm = WindowManager()
    active_window = wm.get_active_window()
    if active_window:
        if wm.system == "Windows":
            print("\nTest 2: Using Windows-specific window capture")
            win_screenshot = wm._get_window_screenshot_windows(active_window)
            if win_screenshot:
                # Convert PIL to OpenCV format
                win_screenshot_cv = cv2.cvtColor(np.array(win_screenshot), cv2.COLOR_RGB2BGR)
                start_time = time.time()
                result = detector.find_image_on_screen(test_image_path, win_screenshot_cv)
                elapsed = time.time() - start_time
                
                if result:
                    x, y, width, height = result
                    print(f"✅ Image found at {x},{y} (size: {width}x{height}) in {elapsed:.3f}s")
                else:
                    print(f"❌ Image not found in Windows screenshot (took {elapsed:.3f}s)")
        
        print("\nTest 3: Using PyAutoGUI region capture")
        region_screenshot = wm._get_window_screenshot_fallback(active_window)
        if region_screenshot:
            # Convert PIL to OpenCV format
            region_screenshot_cv = cv2.cvtColor(np.array(region_screenshot), cv2.COLOR_RGB2BGR)
            start_time = time.time()
            result = detector.find_image_on_screen(test_image_path, region_screenshot_cv)
            elapsed = time.time() - start_time
            
            if result:
                x, y, width, height = result
                print(f"✅ Image found at {x},{y} (size: {width}x{height}) in {elapsed:.3f}s")
            else:
                print(f"❌ Image not found in region screenshot (took {elapsed:.3f}s)")

def main():
    """Run all tests and print results"""
    print("======= SCREEN AUTOMATOR IMAGE DETECTION TESTS =======")
    print(f"Running tests at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test window screenshot methods
    test_window_screenshot_methods()
    
    # Test image detection with those methods
    test_image_detection()
    
    print("\n======= TEST RESULTS SUMMARY =======")
    print("Review the test results above to determine which method works best on your system.")
    print("Recommendations:")
    print("1. For window screenshots: Use the Windows direct method if it works, otherwise use PyAutoGUI region capture.")
    print("2. For image detection: Use the method that successfully found the test image with highest confidence.")

if __name__ == "__main__":
    main() 