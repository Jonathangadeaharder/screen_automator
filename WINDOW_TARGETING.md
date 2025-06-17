# Window Targeting Methods in Screen Automator

This document explains the different methods available for targeting specific windows in Screen Automator's context-aware mode.

## Overview

When using context-aware automation, rules can be configured to target specific windows. This ensures that rules only execute in the appropriate context. There are two primary methods for identifying windows:

1. **Class-based targeting** (Most reliable)
2. **Process-based targeting** (Also reliable)
3. **Auto mode** (Uses both methods in order of reliability)

## Window Class Targeting

**Window class** is a unique identifier assigned to window types by the operating system. Unlike window titles, class names rarely change and are consistent across instances of the same application.

### Advantages:
- **Most reliable**: Class names remain consistent even when window titles change
- **Consistent across instances**: All windows of the same type share the same class
- **OS-level identification**: Directly uses the operating system's window management system

### Example:
- Chrome browser windows: `Chrome_WidgetWin_1`
- Notepad windows: `Notepad`

### When to use:
- When you need rules to target a specific application regardless of window title
- For applications that frequently change their window titles (like browsers)
- For the most robust window identification

## Process-based Targeting

**Process-based targeting** identifies windows by the name of the process that created them. This is reliable for applications with unique process names.

### Advantages:
- **Moderately reliable**: Process names typically don't change between application versions
- **Works across multiple windows**: Targets all windows from the same application
- **Simple to understand**: Process names are usually straightforward (e.g., "chrome.exe")

### Example:
- Chrome browser: `chrome.exe`
- Visual Studio Code: `Code.exe`

### When to use:
- When multiple windows from the same application should be targeted
- When class name is unavailable or inconsistent
- For applications with distinctive process names

## Auto Mode

**Auto mode** attempts all targeting methods in order of reliability (class → process). This is the default mode and provides a balance of specificity and reliability.

### Advantages:
- **Comprehensive**: Tries all available targeting methods
- **Prioritizes reliability**: Starts with the most reliable method first
- **Fallback mechanism**: If one method fails, it tries the next

### When to use:
- When you're unsure which method is best
- For general-purpose rules
- When multiple targeting criteria are available

## Legacy Support

For backward compatibility, the system still maintains limited support for title-based targeting in existing rules, but this method is deprecated and no longer exposed in the UI. Title-based targeting is only used as a last resort in auto mode if both class and process targeting fail.

### Why title-based targeting was removed:
- Window titles often change dynamically
- Many applications use dynamic content in titles (e.g., document names, URLs)
- Different language versions of applications have different titles
- Requires exact spelling and case matching
- Leads to brittle automation rules that break easily

## Tips for Effective Window Targeting

1. **Use class-based targeting whenever possible** for the most reliable automation
2. **Test your rules** with the "Test Rules in Window" feature to verify targeting
3. **Combine targeting methods** by using Auto mode with multiple criteria
4. **Group similar rules** using cluster groups for efficient execution

## How to Set Window Targeting

1. In the Rule Editor, select a Window Identification Method
2. Use the "Select Window" button to automatically populate targeting fields
3. Adjust the targeting criteria as needed
4. Test the rule using the "Test Rule" button

## Troubleshooting

If your rules aren't triggering in the expected windows:

1. Check the log for "Target window not found" messages
2. Verify that the target window is actually running
3. Try using a different targeting method
4. Use the "Debug Info" button to see detailed window information
5. Consider using more generic targeting (process-based instead of class-based)

---

Remember that class-based targeting is the most reliable method and should be preferred when possible. The "Select Window" button will automatically populate all targeting fields, including the window class when available. 