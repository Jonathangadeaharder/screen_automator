# Window Management Features

The Screen Automator now includes powerful window management capabilities that allow rules to target specific applications and windows. This document explains how to use these features effectively.

## Overview

The window management system allows you to:

1. **Target specific windows**: Rules can be configured to run only when specific applications or windows are active
2. **Automatic context switching**: The system can automatically switch between windows to execute different rule groups
3. **Rule clustering**: Rules targeting the same window are grouped together for efficient execution
4. **Cross-platform support**: Works on Windows, Linux, and macOS

## Getting Started

### Enable Context-Aware Mode

To use window management features, start the automator in context-aware mode:

```bash
python cli.py --context-aware start
```

### List Available Windows

See all currently running windows:

```bash
python cli.py window list
```

Example output:
```
🪟 Available Windows:
   1. Notepad
      Process: notepad.exe (PID: 1234)
      Position: (100, 200) Size: 800x600
      Handle: 123456

   2. Calculator
      Process: calc.exe (PID: 5678)
      Position: (300, 400) Size: 320x240
      Handle: 789012
```

### Show Active Window

Display information about the currently active window:

```bash
python cli.py window active
```

## Rule Window Targeting

### Set Window Target for a Rule

Configure a rule to target a specific window:

```bash
# Target by window title (partial match)
python cli.py rule set-window RULE_ID --title "Notepad"

# Target by window title (exact match)
python cli.py rule set-window RULE_ID --title "Calculator" --exact

# Target by process name
python cli.py rule set-window RULE_ID --process "chrome.exe"

# Assign to a cluster group for efficient execution
python cli.py rule set-window RULE_ID --title "VS Code" --cluster "dev_tools"
```

### Test Rule in Specific Window

Test a rule in a specific window context:

```bash
# Test using rule's configured window target
python cli.py --context-aware rule test-window RULE_ID

# Test in specific window
python cli.py --context-aware rule test-window RULE_ID --title "Notepad"
python cli.py --context-aware rule test-window RULE_ID --process "calc.exe"
```

## Rule Clustering

Rules are automatically grouped into clusters based on their window targeting and cluster group settings. This allows for efficient execution by minimizing window switching.

### View Cluster Status

```bash
python cli.py --context-aware cluster-status
```

Example output:
```
🔄 Rule Cluster Status:
  ✅ cluster:text_editors|title:Notepad
      Rules: 3
      Rule Names: Find Text, Replace Text, Save Document
      Last Execution: Never

  ⏳ cluster:browsers|process:chrome.exe
      Rules: 2
      Rule Names: Check Email, Update Status
      Last Execution: 2.3s ago
```

### Manual Window Switching

Switch to a specific window manually:

```bash
# Switch by title
python cli.py window switch --title "Notepad"

# Switch by process
python cli.py window switch --process "chrome.exe"

# Switch with exact title match
python cli.py window switch --title "Calculator" --exact
```

## Programming Interface

### Using WindowManager

```python
from src.window_manager import WindowManager

# Initialize window manager
wm = WindowManager()

# Get all running windows
windows = wm.get_running_windows()
for window in windows:
    print(f"{window.title} - {window.process_name}")

# Find specific window
notepad = wm.find_window_by_title("Notepad")
if notepad:
    print(f"Found Notepad: {notepad.handle}")

# Switch to window
if wm.switch_to_window(notepad):
    print("Successfully switched to Notepad")

# Get active window
active = wm.get_active_window()
print(f"Active window: {active.title}")

# Restore original window
wm.restore_original_window()
```

### Using ContextAwareAutomator

```python
from src.context_automator import ContextAwareAutomator

# Initialize context-aware automator
automator = ContextAwareAutomator()

# Set up callbacks
def on_window_changed(window_info):
    if window_info:
        print(f"Switched to: {window_info.title}")
    else:
        print("Restored original window")

def on_cluster_start(cluster_key, rules):
    print(f"Executing cluster {cluster_key} with {len(rules)} rules")

automator.on_window_context_changed = on_window_changed
automator.on_cluster_execution_start = on_cluster_start

# Start context-aware monitoring
automator.start_context_monitoring()

# Get available windows for targeting
windows = automator.get_available_windows()

# Test rule in specific window
result = automator.test_rule_in_window("rule-id", window_title="Notepad")

# Configure cluster settings
automator.set_cluster_cooldown(3.0)  # 3 seconds between cluster executions

# Get cluster status
status = automator.get_cluster_status()
```

### Creating Rules with Window Targeting

```python
from src.rule_manager import RuleManager
from src.action_executor import create_click_action

# Create rule manager
rm = RuleManager()

# Create rule with window targeting
actions = [create_click_action(100, 200)]
rule = rm.create_rule(
    name="Click Save Button",
    image_path="save_button.png",
    actions=actions
)

# Set window targeting
rule.target_window_title = "Notepad"
rule.target_window_process = "notepad.exe"
rule.window_exact_match = False
rule.cluster_group = "text_editors"

# Save the rule
rm.save_rule(rule)
```

## Rule Data Structure

Rules now include these additional fields for window targeting:

```python
@dataclass
class Rule:
    # ... existing fields ...
    
    # Window targeting
    target_window_title: str = ""      # Target window title (empty = any window)
    target_window_process: str = ""    # Target window process name (empty = any process)  
    window_exact_match: bool = False   # Whether to match window title exactly
    cluster_group: str = ""            # Rules with same cluster_group execute together
```

## Platform-Specific Features

### Windows
- Full window enumeration with Win32 API
- Process information via psutil
- Window screenshots without focus switching
- Minimized window restoration

### Linux
- Window management via wmctrl
- Process information via xprop and psutil
- Requires wmctrl and xprop packages

### macOS
- Window management via AppleScript
- Limited window information available
- Requires accessibility permissions

## Configuration Options

### Cluster Cooldown

Set minimum time between cluster executions:

```python
automator.set_cluster_cooldown(2.0)  # 2 seconds
```

### Window Matching

- **Partial match**: Window title contains the target string (default)
- **Exact match**: Window title matches exactly
- **Process match**: Process name contains the target string

## Best Practices

### Rule Organization

1. **Group related rules**: Use cluster groups to organize rules by application or workflow
2. **Specific targeting**: Use both window title and process for precise targeting
3. **Fallback rules**: Create rules without window targeting for universal actions

### Performance

1. **Minimize clusters**: Too many clusters can cause excessive window switching
2. **Cluster cooldown**: Set appropriate cooldown to prevent rapid switching
3. **Rule priority**: Use rule priorities within clusters for execution order

### Cross-Platform Compatibility

1. **Test on target platform**: Window titles and process names vary by OS
2. **Handle missing windows**: Rules should gracefully handle missing target windows
3. **Platform-specific rules**: Create OS-specific rules when needed

## Troubleshooting

### Common Issues

1. **Window not found**: Check exact window title and process name
2. **Rules not clustering**: Verify window targeting configuration
3. **Context switching fails**: Check window accessibility and permissions

### Debug Commands

```bash
# List all windows with details
python cli.py window list --include-minimized

# Show active window information
python cli.py window active

# View cluster organization
python cli.py --context-aware cluster-status

# Test window switching
python cli.py window switch --title "Target Window"
```

### Logging

Enable verbose logging to debug window management issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Examples

### Example 1: Text Editor Automation

```python
# Rule 1: Auto-save in Notepad every 5 minutes
rule1 = rm.create_rule(
    name="Auto Save",
    image_path="save_icon.png", 
    actions=[create_key_combination_action(["ctrl", "s"])]
)
rule1.target_window_title = "Notepad"
rule1.cluster_group = "text_editors"
rule1.condition_type = "screen_unchanged"
rule1.screen_unchanged_timeout = 5.0

# Rule 2: Insert timestamp
rule2 = rm.create_rule(
    name="Insert Timestamp",
    image_path="timestamp_button.png",
    actions=[create_type_text_action(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")]
)
rule2.target_window_title = "Notepad"
rule2.cluster_group = "text_editors"
```

### Example 2: Browser Automation

```python
# Rule for Chrome browser
rule = rm.create_rule(
    name="Close Tab Shortcut",
    image_path="close_tab.png",
    actions=[create_key_combination_action(["ctrl", "w"])]
)
rule.target_window_process = "chrome.exe"
rule.cluster_group = "browsers"
```

### Example 3: Multi-Application Workflow

```python
# Email checker rule
email_rule = rm.create_rule(
    name="Check Email",
    image_path="new_email.png",
    actions=[create_click_action(200, 100)]
)
email_rule.target_window_title = "Outlook"
email_rule.cluster_group = "communication"

# Slack notification rule  
slack_rule = rm.create_rule(
    name="Check Slack",
    image_path="slack_notification.png", 
    actions=[create_click_action(150, 50)]
)
slack_rule.target_window_title = "Slack"
slack_rule.cluster_group = "communication"
```

## API Reference

### WindowInfo Class

```python
@dataclass
class WindowInfo:
    handle: int                 # System window handle
    title: str                 # Window title
    process_name: str          # Process executable name  
    process_id: int            # Process ID
    x: int                     # Window X position
    y: int                     # Window Y position
    width: int                 # Window width
    height: int                # Window height
    is_visible: bool           # Whether window is visible
    is_minimized: bool         # Whether window is minimized
    class_name: str           # Window class name (Windows only)
```

### WindowManager Methods

- `get_running_windows(include_minimized=True)` - Get list of all windows
- `get_active_window()` - Get currently active window
- `switch_to_window(window_info)` - Switch to specific window
- `restore_original_window()` - Restore original active window
- `find_window_by_title(title, exact_match=False)` - Find window by title
- `find_windows_by_process(process_name)` - Find windows by process
- `get_window_screenshot(window_info)` - Capture window screenshot

### ContextAwareAutomator Methods

- `start_context_monitoring()` - Start context-aware monitoring
- `stop_context_monitoring()` - Stop context-aware monitoring  
- `get_available_windows()` - Get windows available for targeting
- `test_rule_in_window(rule_id, window_title, window_process)` - Test rule in window
- `set_cluster_cooldown(seconds)` - Set cluster execution cooldown
- `get_cluster_status()` - Get status of all rule clusters

This comprehensive window management system enables sophisticated automation workflows that can intelligently target specific applications and contexts, making your screen automation much more powerful and efficient. 