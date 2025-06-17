#!/usr/bin/env python3
"""
Basic test script to verify the screen automator functionality
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.automator import ScreenAutomator
from src.action_executor import create_click_action, create_type_text_action, create_wait_action
import time


def test_basic_functionality():
    """Test basic functionality without GUI"""
    print("Testing Screen Automator basic functionality...")
    
    # Initialize automator
    automator = ScreenAutomator()
    
    # Test 1: Check status
    print("\n1. Testing status...")
    status = automator.get_status()
    print(f"Status: {status}")
    assert not status['running'], "Automator should not be running initially"
    
    # Test 2: Create a simple rule
    print("\n2. Testing rule creation...")
    actions = [
        create_wait_action(1.0),
        create_type_text_action("Hello World!"),
        create_wait_action(0.5)
    ]
    
    # Create a dummy image file for testing
    test_image_path = "data/images/test_trigger.png"
    os.makedirs("data/images", exist_ok=True)
    
    # Create a simple test image
    from PIL import Image
    test_img = Image.new('RGB', (50, 50), color='red')
    test_img.save(test_image_path)
    
    rule = automator.rule_manager.create_rule(
        name="Test Rule",
        image_path=test_image_path,
        actions=actions,
        description="A test rule"
    )
    
    print(f"Created rule: {rule.name} (ID: {rule.id[:8]}...)")
    
    # Test 3: List rules
    print("\n3. Testing rule listing...")
    rules = automator.rule_manager.list_rules()
    print(f"Found {len(rules)} rules")
    assert len(rules) >= 1, "Should have at least one rule"
    
    # Test 4: Test rule management
    print("\n4. Testing rule management...")
    
    # Get rule by name
    found_rule = automator.rule_manager.get_rule_by_name("Test Rule")
    assert found_rule is not None, "Should find rule by name"
    assert found_rule.id == rule.id, "Found rule should match created rule"
    
    # Update rule
    success = automator.rule_manager.update_rule(rule.id, description="Updated description")
    assert success, "Rule update should succeed"
    
    # Test 5: Force execute rule (without trigger check)
    print("\n5. Testing force execution...")
    print("Rule will type 'Hello World!' in 3 seconds...")
    time.sleep(3)  # Give user time to position cursor
    
    success = automator.force_execute_rule(rule.id)
    assert success, "Force execution should succeed"
    
    # Test 6: Clean up
    print("\n6. Cleaning up...")
    success = automator.rule_manager.delete_rule(rule.id)
    assert success, "Rule deletion should succeed"
    
    # Remove test image
    if os.path.exists(test_image_path):
        os.remove(test_image_path)
    
    print("\n+ All tests passed!")
    return True


def test_action_creation():
    """Test action creation helpers"""
    print("\nTesting action creation...")
    
    from src.action_executor import (
        create_click_action, create_double_click_action, create_right_click_action,
        create_type_text_action, create_key_press_action, create_key_combination_action,
        create_wait_action, create_scroll_action, ActionType
    )
    
    # Test click action
    click_action = create_click_action(100, 200)
    assert click_action.type == ActionType.CLICK
    assert click_action.params['x'] == 100
    assert click_action.params['y'] == 200
    
    # Test type action
    type_action = create_type_text_action("Hello")
    assert type_action.type == ActionType.TYPE_TEXT
    assert type_action.params['text'] == "Hello"
    
    # Test wait action
    wait_action = create_wait_action(2.5)
    assert wait_action.type == ActionType.WAIT
    assert wait_action.params['duration'] == 2.5
    
    # Test key combination
    combo_action = create_key_combination_action(['ctrl', 'c'])
    assert combo_action.type == ActionType.KEY_COMBINATION
    assert combo_action.params['keys'] == ['ctrl', 'c']
    
    print("+ Action creation tests passed!")


def test_image_detector():
    """Test image detection functionality"""
    print("\nTesting image detection...")
    
    from src.image_detector import ImageDetector
    import numpy as np
    
    detector = ImageDetector()
    
    # Test screen capture
    screen = detector.capture_screen()
    assert isinstance(screen, np.ndarray), "Screen capture should return numpy array"
    assert len(screen.shape) == 3, "Screen should be 3D array (height, width, channels)"
    
    print(f"Screen captured: {screen.shape}")
    print("+ Image detection tests passed!")


if __name__ == '__main__':
    try:
        print("Starting Screen Automator Tests")
        print("=" * 50)
        
        test_action_creation()
        test_image_detector()
        test_basic_functionality()
        
        print("\n+ All tests completed successfully!")
        print("\nYou can now:")
        print("1. Run the CLI: python cli.py --help")
        print("2. Run the GUI: python gui.py")
        
    except Exception as e:
        print(f"\nX Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)