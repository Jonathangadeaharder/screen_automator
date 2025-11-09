#!/usr/bin/env python3
"""
Create a sample rule targeting the Screen Automator window
This will help demonstrate that context switching works
"""

import sys
import os
import time
import uuid

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rule_manager import RuleManager, Rule
from src.action_executor import create_wait_action

def create_sample_rule():
    print("🔧 Creating Sample Rule for Context Switching Test")
    print("=" * 50)
    
    # Initialize rule manager
    rule_manager = RuleManager()
    
    # Create a simple rule targeting the Screen Automator window
    rule_id = str(uuid.uuid4())
    rule = Rule(
        id=rule_id,
        name="Test Context Switching",
        image_path="",  # No image needed for screen_unchanged rule
        actions=[create_wait_action(2)],  # Simple wait action
        enabled=True,
        description="Test rule to verify context switching works",
        priority=50,  # High priority
        condition_type="screen_unchanged",
        screen_unchanged_timeout=0.1,  # Very short timeout for testing
        target_window_title="Screen Automator",  # Target the GUI window
        window_exact_match=True
    )
    
    # Save the rule
    rule_manager.rules[rule_id] = rule
    rule_manager.save_rule(rule)
    
    print(f"✅ Created test rule: 'Test Context Switching'")
    print(f"   - Targets window: 'Screen Automator'")
    print(f"   - Condition: Screen unchanged for 0.1 minutes")
    print(f"   - Action: Wait 2 seconds")
    print("\nThis rule should trigger quickly and demonstrate context switching.")
    print("You should see the Screen Automator window come to the front when the rule triggers.")

if __name__ == "__main__":
    create_sample_rule() 