#!/usr/bin/env python3
import click
import os
import sys
from typing import List
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Modern API (recommended)
from src.modern_api import create_framework
from src.context_automator import ContextAwareAutomator
from src.window_manager import WindowManager
from src.action_executor import (
    create_click_action, create_double_click_action, create_right_click_action,
    create_type_text_action, create_key_press_action, create_key_combination_action,
    create_wait_action, create_scroll_action, Action
)


@click.group()
@click.pass_context
def cli(ctx):
    """Screen Automator - Modern Framework Edition"""
    ctx.ensure_object(dict)
    # Use ContextAwareAutomator for window management features
    # (framework features are available via the automator's components)
    ctx.obj['automator'] = ContextAwareAutomator()


@cli.command()
@click.option('--timeout', type=int, default=0, help='Stop monitoring after N seconds (0 = no timeout)')
@click.pass_context
def start(ctx, timeout):
    """Start monitoring for trigger images"""
    automator = ctx.obj['automator']
    
    def on_rule_triggered(rule):
        click.echo(f"🎯 Rule '{rule.name}' triggered!")
    
    def on_error(error_msg):
        click.echo(f"❌ Error: {error_msg}")
    
    def on_window_context_changed(old_window, new_window):
        if new_window:
            click.echo(f"🪟 Switched to window: {new_window.title}")
        elif old_window:
            click.echo(f"🔙 Restored from window: {old_window.title}")
    
    automator.on_rule_triggered = on_rule_triggered
    automator.on_error = on_error
    automator.on_window_context_changed = on_window_context_changed
    
    try:
        automator.start_monitoring()
        click.echo("🔍 Rule monitoring started. Each rule handles its own window targeting.")
        
        if timeout > 0:
            click.echo(f"   Timeout: {timeout} seconds. Press Ctrl+C to stop early...")
        else:
            click.echo("   Press Ctrl+C to stop...")
        
        # Keep the main thread alive
        import time
        start_time = time.time()
        while automator.running:
            if timeout > 0 and (time.time() - start_time) >= timeout:
                click.echo(f"\n⏰ Timeout reached ({timeout}s). Stopping monitoring...")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        click.echo("\n🛑 Stopping monitoring...")
    finally:
        automator.stop_monitoring()


@cli.command()
@click.pass_context
def status(ctx):
    """Show current status"""
    automator = ctx.obj['automator']
    status_info = automator.get_status()
    
    click.echo("Screen Automator Status:")
    click.echo(f"  Running: {'Yes' if status_info['running'] else 'No'}")
    click.echo(f"  Check Interval: {status_info['check_interval']}s")
    click.echo(f"  Total Rules: {status_info['total_rules']}")
    click.echo(f"  Enabled Rules: {status_info['enabled_rules']}")
    
    actions_executed = status_info.get('actions_executed', 0)
    
    # Note: Action limits are now configured per-rule
    click.echo(f"  Actions Executed: {actions_executed}")


@cli.group()
def rule():
    """Manage automation rules"""
    pass


@rule.command('list')
@click.pass_context
def list_rules(ctx):
    """List all rules"""
    automator = ctx.obj['automator']
    rules = automator.rule_manager.list_rules()
    
    if not rules:
        click.echo("No rules found.")
        return
    
    click.echo("📋 Rules:")
    for rule in rules:
        status = "✅" if rule.enabled else "❌"
        condition_type = getattr(rule, 'condition_type', 'image')
        click.echo(f"  {status} {rule.name} (ID: {rule.id[:8]}...)")
        
        if condition_type == 'image':
            click.echo(f"      Type: Image detection")
            click.echo(f"      Image: {rule.image_path}")
        else:
            timeout = getattr(rule, 'screen_unchanged_timeout', 5.0)
            click.echo(f"      Type: Screen unchanged")
            click.echo(f"      Timeout: {timeout} minutes")
        
        click.echo(f"      Actions: {len(rule.actions)}")
        if rule.description:
            click.echo(f"      Description: {rule.description}")
        click.echo()


@rule.command('create')
@click.option('--name', required=True, help='Rule name')
@click.option('--image', help='Path to trigger image (for image-based rules)')
@click.option('--description', default='', help='Rule description')
@click.option('--condition', type=click.Choice(['image', 'screen_unchanged']), default='image', help='Rule condition type')
@click.option('--timeout', type=float, default=5.0, help='Timeout in minutes for screen_unchanged condition')
@click.pass_context
def create_rule(ctx, name, image, description, condition, timeout):
    """Create a new rule interactively"""
    automator = ctx.obj['automator']
    
    # Validate inputs based on condition type
    if condition == 'image':
        if not image:
            click.echo("❌ Image path is required for image-based rules")
            return
        if not os.path.exists(image):
            click.echo(f"❌ Image file not found: {image}")
            return
        click.echo(f"Creating rule '{name}' with trigger image: {image}")
    else:  # screen_unchanged
        if not image:
            image = ""  # No image needed for screen unchanged rules
        click.echo(f"Creating rule '{name}' that triggers when screen is unchanged for {timeout} minutes")
    
    actions = []
    
    while True:
        click.echo("\nChoose an action to add:")
        click.echo("1. Click")
        click.echo("2. Double Click")
        click.echo("3. Right Click")
        click.echo("4. Type Text")
        click.echo("5. Press Key")
        click.echo("6. Key Combination")
        click.echo("7. Wait")
        click.echo("8. Scroll")
        click.echo("9. Finish and save rule")
        
        choice = click.prompt("Enter choice", type=int)
        
        if choice == 1:
            x = click.prompt("X coordinate", type=int)
            y = click.prompt("Y coordinate", type=int)
            actions.append(create_click_action(x, y))
            click.echo(f"✅ Added click action at ({x}, {y})")
        
        elif choice == 2:
            x = click.prompt("X coordinate", type=int)
            y = click.prompt("Y coordinate", type=int)
            actions.append(create_double_click_action(x, y))
            click.echo(f"✅ Added double-click action at ({x}, {y})")
        
        elif choice == 3:
            x = click.prompt("X coordinate", type=int)
            y = click.prompt("Y coordinate", type=int)
            actions.append(create_right_click_action(x, y))
            click.echo(f"✅ Added right-click action at ({x}, {y})")
        
        elif choice == 4:
            text = click.prompt("Text to type")
            interval = click.prompt("Typing interval (seconds)", type=float, default=0.0)
            actions.append(create_type_text_action(text, interval))
            click.echo(f"✅ Added type text action: '{text}'")
        
        elif choice == 5:
            key = click.prompt("Key to press")
            presses = click.prompt("Number of presses", type=int, default=1)
            actions.append(create_key_press_action(key, presses))
            click.echo(f"✅ Added key press action: '{key}' x{presses}")
        
        elif choice == 6:
            keys_input = click.prompt("Keys for combination (comma-separated)")
            keys = [k.strip() for k in keys_input.split(',')]
            actions.append(create_key_combination_action(keys))
            click.echo(f"✅ Added key combination: {'+'.join(keys)}")
        
        elif choice == 7:
            duration = click.prompt("Wait duration (seconds)", type=float)
            actions.append(create_wait_action(duration))
            click.echo(f"✅ Added wait action: {duration}s")
        
        elif choice == 8:
            clicks = click.prompt("Scroll clicks (positive=up, negative=down)", type=int)
            x = click.prompt("X coordinate (optional)", type=int, default=None)
            y = click.prompt("Y coordinate (optional)", type=int, default=None)
            actions.append(create_scroll_action(clicks, x, y))
            click.echo(f"✅ Added scroll action: {clicks} clicks")
        
        elif choice == 9:
            break
        
        else:
            click.echo("❌ Invalid choice")
    
    if not actions:
        click.echo("❌ No actions added. Rule not created.")
        return
    
    # Create the rule
    rule = automator.rule_manager.create_rule(
        name=name, 
        image_path=image, 
        actions=actions, 
        description=description,
        condition_type=condition,
        screen_unchanged_timeout=timeout
    )
    
    if condition == 'image':
        click.echo(f"✅ Image-based rule '{rule.name}' created successfully! (ID: {rule.id[:8]}...)")
    else:
        click.echo(f"✅ Screen unchanged rule '{rule.name}' created successfully! (ID: {rule.id[:8]}...)")
        click.echo(f"   Will trigger after {timeout} minutes of no screen changes")


@rule.command('delete')
@click.argument('rule_id')
@click.pass_context
def delete_rule(ctx, rule_id):
    """Delete a rule by ID or name"""
    automator = ctx.obj['automator']
    
    # Try to find by ID first, then by name
    rule = automator.rule_manager.get_rule(rule_id)
    if not rule:
        rule = automator.rule_manager.get_rule_by_name(rule_id)
    
    if not rule:
        click.echo(f"❌ Rule not found: {rule_id}")
        return
    
    if click.confirm(f"Delete rule '{rule.name}'?"):
        if automator.rule_manager.delete_rule(rule.id):
            click.echo(f"✅ Rule '{rule.name}' deleted")
        else:
            click.echo(f"❌ Failed to delete rule '{rule.name}'")


@rule.command('enable')
@click.argument('rule_id')
@click.pass_context
def enable_rule(ctx, rule_id):
    """Enable a rule"""
    automator = ctx.obj['automator']
    
    rule = automator.rule_manager.get_rule(rule_id)
    if not rule:
        rule = automator.rule_manager.get_rule_by_name(rule_id)
    
    if not rule:
        click.echo(f"❌ Rule not found: {rule_id}")
        return
    
    automator.rule_manager.update_rule(rule.id, enabled=True)
    click.echo(f"✅ Rule '{rule.name}' enabled")


@rule.command('disable')
@click.argument('rule_id')
@click.pass_context
def disable_rule(ctx, rule_id):
    """Disable a rule"""
    automator = ctx.obj['automator']
    
    rule = automator.rule_manager.get_rule(rule_id)
    if not rule:
        rule = automator.rule_manager.get_rule_by_name(rule_id)
    
    if not rule:
        click.echo(f"❌ Rule not found: {rule_id}")
        return
    
    automator.rule_manager.update_rule(rule.id, enabled=False)
    click.echo(f"✅ Rule '{rule.name}' disabled")


@rule.command('test')
@click.argument('rule_id')
@click.option('--timeout', type=int, default=10, help='Test timeout in seconds (default: 10)')
@click.pass_context
def test_rule(ctx, rule_id, timeout):
    """Test a rule (check for trigger and execute if found)"""
    automator = ctx.obj['automator']
    
    rule = automator.rule_manager.get_rule(rule_id)
    if not rule:
        rule = automator.rule_manager.get_rule_by_name(rule_id)
    
    if not rule:
        click.echo(f"❌ Rule not found: {rule_id}")
        return
    
    click.echo(f"🧪 Testing rule '{rule.name}' (timeout: {timeout}s)...")
    
    import threading
    import time
    
    result = [None]  # Use list to allow modification in nested function
    
    def test_with_timeout():
        try:
            result[0] = automator.test_rule(rule.id)
        except Exception as e:
            click.echo(f"❌ Test error: {e}")
            result[0] = False
    
    # Run test in separate thread with timeout
    test_thread = threading.Thread(target=test_with_timeout)
    test_thread.daemon = True
    test_thread.start()
    test_thread.join(timeout)
    
    if test_thread.is_alive():
        click.echo(f"⏰ Test timed out after {timeout} seconds")
        result[0] = False
    
    if result[0]:
        click.echo("✅ Test completed successfully")
    else:
        click.echo("❌ Test failed")


@rule.command('force')
@click.argument('rule_id')
@click.option('--timeout', type=int, default=30, help='Execution timeout in seconds (default: 30)')
@click.pass_context
def force_rule(ctx, rule_id, timeout):
    """Force execute a rule without checking for trigger"""
    automator = ctx.obj['automator']
    
    rule = automator.rule_manager.get_rule(rule_id)
    if not rule:
        rule = automator.rule_manager.get_rule_by_name(rule_id)
    
    if not rule:
        click.echo(f"❌ Rule not found: {rule_id}")
        return
    
    if click.confirm(f"Force execute rule '{rule.name}' (timeout: {timeout}s)?"):
        click.echo(f"⚡ Force executing rule '{rule.name}'...")
        
        import threading
        import time
        
        result = [None]  # Use list to allow modification in nested function
        
        def execute_with_timeout():
            try:
                result[0] = automator.force_execute_rule(rule.id)
            except Exception as e:
                click.echo(f"❌ Execution error: {e}")
                result[0] = False
        
        # Run execution in separate thread with timeout
        exec_thread = threading.Thread(target=execute_with_timeout)
        exec_thread.daemon = True
        exec_thread.start()
        exec_thread.join(timeout)
        
        if exec_thread.is_alive():
            click.echo(f"⏰ Execution timed out after {timeout} seconds")
            result[0] = False
        
        if result[0]:
            click.echo("✅ Force execution completed")
        else:
            click.echo("❌ Force execution failed")


@rule.command('export')
@click.argument('filepath')
@click.pass_context
def export_rules(ctx, filepath):
    """Export all rules to JSON file"""
    automator = ctx.obj['automator']
    
    try:
        automator.rule_manager.export_rules(filepath)
        click.echo(f"✅ Rules exported to {filepath}")
    except Exception as e:
        click.echo(f"❌ Export failed: {e}")


@rule.command('import')
@click.argument('filepath')
@click.pass_context
def import_rules(ctx, filepath):
    """Import rules from JSON file"""
    automator = ctx.obj['automator']
    
    if not os.path.exists(filepath):
        click.echo(f"❌ File not found: {filepath}")
        return
    
    try:
        count = automator.rule_manager.import_rules(filepath)
        click.echo(f"✅ Imported {count} rules from {filepath}")
    except Exception as e:
        click.echo(f"❌ Import failed: {e}")


@cli.command()
@click.option('--interval', type=float, help='Check interval in seconds')
@click.pass_context
def config(ctx, interval):
    """Configure automator settings"""
    automator = ctx.obj['automator']
    
    if interval is not None:
        automator.set_check_interval(interval)
        click.echo(f"✅ Check interval set to {interval}s")
    
    # Note: Action limits are now configured per-rule in rule settings
    
    status_info = automator.get_status()
    click.echo(f"Current check interval: {status_info['check_interval']}s")
    
    actions_executed = status_info.get('actions_executed', 0)
    click.echo(f"Actions executed: {actions_executed}")


@cli.command()
@click.pass_context  
def reset_counter(ctx):
    """Reset action execution counter"""
    automator = ctx.obj['automator']
    automator.reset_action_counter()
    click.echo("✅ Action counter reset to 0")


@cli.group()
def window():
    """Window management commands"""
    pass


@window.command('list')
@click.option('--include-minimized', is_flag=True, help='Include minimized windows')
def list_windows(include_minimized):
    """List all running windows"""
    window_manager = WindowManager()
    windows = window_manager.get_running_windows(include_minimized=include_minimized)
    
    if not windows:
        click.echo("No windows found.")
        return
    
    click.echo("🪟 Available Windows:")
    for i, window in enumerate(windows, 1):
        status_icons = []
        if window.is_minimized:
            status_icons.append("📐")
        if not window.is_visible:
            status_icons.append("👁️‍🗨️")
        
        status_str = " ".join(status_icons)
        click.echo(f"  {i:2d}. {window.title} {status_str}")
        click.echo(f"      Process: {window.process_name} (PID: {window.process_id})")
        click.echo(f"      Position: ({window.x}, {window.y}) Size: {window.width}x{window.height}")
        click.echo(f"      Handle: {window.handle}")
        if window.class_name:
            click.echo(f"      Class: {window.class_name}")
        click.echo()


@window.command('active')
def show_active_window():
    """Show the currently active window"""
    window_manager = WindowManager()
    active_window = window_manager.get_active_window()
    
    if not active_window:
        click.echo("No active window found.")
        return
    
    click.echo("🪟 Active Window:")
    click.echo(f"  Title: {active_window.title}")
    click.echo(f"  Process: {active_window.process_name} (PID: {active_window.process_id})")
    click.echo(f"  Position: ({active_window.x}, {active_window.y})")
    click.echo(f"  Size: {active_window.width}x{active_window.height}")
    click.echo(f"  Handle: {active_window.handle}")
    if active_window.class_name:
        click.echo(f"  Class: {active_window.class_name}")


@window.command('switch')
@click.option('--title', help='Window title to switch to')
@click.option('--process', help='Process name to switch to')
@click.option('--exact', is_flag=True, help='Exact title match')
def switch_window(title, process, exact):
    """Switch to a specific window"""
    if not title and not process:
        click.echo("❌ Please specify either --title or --process")
        return
    
    window_manager = WindowManager()
    target_window = None
    
    if title:
        target_window = window_manager.find_window_by_title(title, exact_match=exact)
        if not target_window:
            click.echo(f"❌ Window with title '{title}' not found")
            return
    elif process:
        windows = window_manager.find_windows_by_process(process)
        if not windows:
            click.echo(f"❌ No windows found for process '{process}'")
            return
        target_window = windows[0]  # Use first matching window
    
    if target_window:
        if window_manager.switch_to_window(target_window):
            click.echo(f"✅ Switched to window: {target_window.title}")
        else:
            click.echo(f"❌ Failed to switch to window: {target_window.title}")


@rule.command('set-window')
@click.argument('rule_id')
@click.option('--title', help='Target window title')
@click.option('--process', help='Target window process name')
@click.option('--class-name', help='Target window class name (most reliable)')
@click.option('--exact', is_flag=True, help='Exact title match')
@click.pass_context
def set_rule_window(ctx, rule_id, title, process, class_name, exact):
    """Set window targeting for a rule"""
    automator = ctx.obj['automator']
    
    # Find rule by ID or partial ID
    rule = None
    for r in automator.rule_manager.list_rules():
        if r.id.startswith(rule_id):
            rule = r
            break
    
    if not rule:
        click.echo(f"❌ Rule not found: {rule_id}")
        return
    
    # Update rule window targeting
    updates = {}
    if title is not None:
        updates['target_window_title'] = title
    if process is not None:
        updates['target_window_process'] = process
    if class_name is not None:
        updates['target_window_class'] = class_name
    if exact is not None:
        updates['window_exact_match'] = exact
    
    if automator.rule_manager.update_rule(rule.id, **updates):
        click.echo(f"✅ Updated rule '{rule.name}' window targeting:")
        if title:
            match_type = "exact" if exact else "partial"
            click.echo(f"  Window Title: '{title}' ({match_type} match)")
        if process:
            click.echo(f"  Process: '{process}'")
        if class_name:
            click.echo(f"  Window Class: '{class_name}' (recommended)")
    else:
        click.echo(f"❌ Failed to update rule: {rule_id}")


@rule.command('test-window')
@click.argument('rule_id')
@click.option('--title', help='Test in specific window title')
@click.option('--process', help='Test in specific window process')
@click.pass_context
def test_rule_window(ctx, rule_id, title, process):
    """Test a rule in a specific window context"""
    automator = ctx.obj['automator']
    
    # Find rule by ID or partial ID
    rule = None
    for r in automator.rule_manager.list_rules():
        if r.id.startswith(rule_id):
            rule = r
            break
    
    if not rule:
        click.echo(f"❌ Rule not found: {rule_id}")
        return
    
    if not title and not process:
        # Use rule's own window targeting
        title = getattr(rule, 'target_window_title', '')
        process = getattr(rule, 'target_window_process', '')
        
        if not title and not process:
            click.echo("❌ Please specify --title or --process, or set window targeting on the rule")
            return
    
    click.echo(f"🧪 Testing rule '{rule.name}' in window context...")
    
    try:
        result = automator.test_rule_in_window(rule.id, window_title=title or '', window_process=process or '')
        if result:
            click.echo("✅ Rule test successful - rule was triggered!")
        else:
            click.echo("❌ Rule test failed - rule was not triggered")
    except Exception as e:
        click.echo(f"❌ Error during test: {e}")


if __name__ == '__main__':
    cli()