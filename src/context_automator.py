import os
import threading
import time
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Tuple

try:
    import pyautogui

    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False
    print("Warning: pyautogui not available - cursor position restoration disabled")

import os

# Import centralized logging
import sys

from .automator import ScreenAutomator
from .image_detector import ImageDetector
from .rule_manager import Rule
from .window_manager import WindowInfo, WindowManager

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logging import get_logger

logger = get_logger()


class ContextAwareAutomator(ScreenAutomator):
    """
    Extended automator that handles window-specific rule execution with clustering
    """

    def __init__(self, rules_dir: str = "data/rules"):
        super().__init__(rules_dir)
        self.window_manager = WindowManager()

        # Window context tracking
        self.current_context_window: Optional[WindowInfo] = None
        self.context_execution_active = False
        self.keep_context_window_focused = True  # Keep context window in focus after execution

        # Cursor position tracking
        self.original_cursor_pos: Optional[Tuple[int, int]] = None
        self.context_cursor_pos: Optional[Tuple[int, int]] = None

        # Callbacks for window context events
        self.on_window_context_changed: Optional[
            Callable[[Optional[WindowInfo], Optional[WindowInfo]], None]
        ] = None

    def start_monitoring(self):
        """Start monitoring with per-rule context switching"""
        if self.running:
            logger.warning("⚠️ Monitoring already running!")
            return

        logger.info("🚀 Starting rule monitoring...")

        # Show current rule status
        all_rules = self.rule_manager.list_rules()
        enabled_rules = self.rule_manager.list_enabled_rules()
        logger.info(f"📋 Rules status: {len(enabled_rules)}/{len(all_rules)} enabled")

        if enabled_rules:
            logger.info("📝 Enabled rules:")
            for i, rule in enumerate(enabled_rules, 1):
                context_info = ""
                if hasattr(rule, "target_window_class") and rule.target_window_class:
                    context_info = f" → targets window class: '{rule.target_window_class}'"
                elif hasattr(rule, "target_window_process") and rule.target_window_process:
                    context_info = f" → targets process: '{rule.target_window_process}'"
                elif hasattr(rule, "target_window_title") and rule.target_window_title:
                    context_info = f" → targets window: '{rule.target_window_title}'"

                logger.info(f"   {i}. '{rule.name}' ({rule.condition_type}){context_info}")
        else:
            logger.warning("⚠️ No enabled rules found! Please create and enable some rules first.")

        super().start_monitoring()

    def stop_monitoring(self):
        """Stop monitoring and restore original context"""
        self._restore_original_context()
        super().stop_monitoring()

    def _restore_original_context(self):
        """Restore the original window context and cursor position"""
        if self.current_context_window:
            old_window = self.current_context_window

            # Restore original window
            if self.window_manager.restore_original_window():
                print(f"Restored original window context from: {old_window.title}")

                # Restore original cursor position
                if HAS_PYAUTOGUI and self.original_cursor_pos:
                    try:
                        pyautogui.moveTo(
                            self.original_cursor_pos[0], self.original_cursor_pos[1], duration=0.2
                        )
                        print(f"Restored cursor to original position: {self.original_cursor_pos}")
                    except Exception as e:
                        print(f"Warning: Could not restore cursor position: {e}")

                # Clear stored positions
                self.original_cursor_pos = None
                self.context_cursor_pos = None
                self.current_context_window = None

                if self.on_window_context_changed:
                    self.on_window_context_changed(old_window, None)
            else:
                print("Warning: Failed to restore original window")
        else:
            # Clear cursor position even if no window context
            self.original_cursor_pos = None
            self.context_cursor_pos = None

    def _monitor_loop(self):
        """Simple monitoring loop - each rule handles its own context if needed"""
        logger.info("🔄 Starting rule monitoring loop...")

        while self.running:
            try:
                # Note: Global action limit removed - now handled per-rule

                # Check for user activity - restore original window if user is active
                if not self._is_mouse_idle():
                    if self.current_context_window:
                        self._restore_original_context()
                    time.sleep(0.1)
                    continue

                # Get enabled rules
                enabled_rules = self.rule_manager.list_enabled_rules()
                if not enabled_rules:
                    time.sleep(self.check_interval)
                    continue

                current_time = time.time()

                # Process each rule individually
                for rule in enabled_rules:
                    if not self.running or not self._is_mouse_idle():
                        break

                    # Check if this rule has been executed recently
                    last_exec_time = self.last_rule_execution_time.get(rule.id, 0)
                    time_since_last_exec = current_time - last_exec_time

                    if time_since_last_exec < self.min_rule_interval:
                        continue

                    # Execute the rule - it will handle its own context switching if needed
                    try:
                        if self._execute_rule_with_context(rule, current_time):
                            self.last_rule_execution_time[rule.id] = current_time
                    except Exception as rule_error:
                        print(f"❌ Error executing rule '{rule.name}': {rule_error}")

            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                import traceback

                traceback.print_exc()
            finally:
                time.sleep(self.check_interval)

        print("🛑 Rule monitoring loop ended")
        self._restore_original_context()

    def _execute_rule_with_context(self, rule: Rule, current_time: float) -> bool:
        """Execute a single rule, handling context switching if needed"""
        try:
            # Check if this rule needs a specific window context
            needs_context_switch = (
                hasattr(rule, "target_window_class")
                and rule.target_window_class
                or hasattr(rule, "target_window_process")
                and rule.target_window_process
                or hasattr(rule, "target_window_title")
                and rule.target_window_title
            )

            if needs_context_switch:
                # Find the target window for this rule
                target_window = self._get_rule_target_window(rule)
                if not target_window:
                    print(f"⚠️ Target window not found for rule '{rule.name}'")
                    return False

                # Switch to the target window context
                if not self._switch_to_context_window(target_window):
                    print(f"❌ Failed to switch to target window for rule '{rule.name}'")
                    return False

                print(f"🪟 Executing rule '{rule.name}' in window context: {target_window.title}")

            # Execute the rule in the current context
            return self._execute_rule_in_context(rule, current_time)

        except Exception as e:
            print(f"❌ Error executing rule '{rule.name}' with context: {e}")
            return False

    def _get_rule_target_window(self, rule: Rule) -> Optional[WindowInfo]:
        """Get the target window for a specific rule"""
        try:
            # Check window identification method
            window_id_method = getattr(rule, "window_id_method", "auto")

            # Class-based targeting (most reliable)
            if (
                window_id_method == "class"
                and hasattr(rule, "target_window_class")
                and rule.target_window_class
            ):
                window = self.window_manager.find_window_by_class(rule.target_window_class)
                if window:
                    return window

            # Process-based targeting
            elif (
                window_id_method == "process"
                and hasattr(rule, "target_window_process")
                and rule.target_window_process
            ):
                windows = self.window_manager.find_windows_by_process(rule.target_window_process)
                if windows:
                    return windows[0]  # Return first matching window

            # Auto method or fallback: try all available targeting methods
            else:
                # First try class-based targeting if available
                if hasattr(rule, "target_window_class") and rule.target_window_class:
                    window = self.window_manager.find_window_by_class(rule.target_window_class)
                    if window:
                        return window

                # Then try process-based targeting
                if hasattr(rule, "target_window_process") and rule.target_window_process:
                    windows = self.window_manager.find_windows_by_process(
                        rule.target_window_process
                    )
                    if windows:
                        return windows[0]

                # Legacy support: Try title-based targeting as last resort
                if hasattr(rule, "target_window_title") and rule.target_window_title:
                    window = self.window_manager.find_window_by_title(
                        rule.target_window_title,
                        exact_match=getattr(rule, "window_exact_match", False),
                    )
                    if window:
                        return window

            return None

        except Exception as e:
            print(f"Error finding target window for rule '{rule.name}': {e}")
            return None

    def _switch_to_context_window(self, target_window: WindowInfo) -> bool:
        """Determine the target window for a cluster of rules"""
        if not cluster_rules:
            print("⚠️ No rules provided for window targeting")
            if self.on_error:
                self.on_error("No rules provided for window targeting")
            return None

        print(f"🔍 Analyzing {len(cluster_rules)} rules for window targeting...")

        # Check if rules have specific window targeting
        for i, rule in enumerate(cluster_rules):
            print(f"📋 Rule {i+1}: '{rule.name}'")
            print(f"   - target_window_title: '{getattr(rule, 'target_window_title', 'None')}'")
            print(f"   - target_window_process: '{getattr(rule, 'target_window_process', 'None')}'")
            print(f"   - window_exact_match: {getattr(rule, 'window_exact_match', False)}")

            # Determine window identification method
            window_id_method = getattr(rule, "window_id_method", "auto").lower()

            # Try to find window based on the specified method
            if window_id_method == "class" and getattr(rule, "target_window_class", ""):
                # Use class-based targeting (most reliable)
                print(f"🔍 Searching for window with class: '{rule.target_window_class}'")
                window = self.window_manager.find_window_by_class(rule.target_window_class)
                if window:
                    print(f"✅ Found window by class: {window.title} (Class: {window.class_name})")
                    return window
                else:
                    error_msg = f"⚠️ Target window class not found: '{rule.target_window_class}'"
                    print(f"❌ {error_msg}")
                    if self.on_error:
                        self.on_error(error_msg)

            elif window_id_method == "process" and rule.target_window_process:
                # Use process-based targeting
                print(f"🔍 Searching for windows with process: '{rule.target_window_process}'")
                windows = self.window_manager.find_windows_by_process(rule.target_window_process)
                if windows:
                    print(
                        f"✅ Found {len(windows)} windows with process '{rule.target_window_process}'"
                    )
                    print(f"   Using first window: {windows[0].title}")
                    return windows[0]  # Return first matching window
                else:
                    error_msg = f"⚠️ Target process not found: '{rule.target_window_process}'"
                    print(f"❌ {error_msg}")
                    if self.on_error:
                        self.on_error(error_msg)

            # Auto method or fallback: try all available targeting methods
            else:
                # First try class-based targeting if available
                if getattr(rule, "target_window_class", ""):
                    print(f"🔍 Auto: Searching for window with class: '{rule.target_window_class}'")
                    window = self.window_manager.find_window_by_class(rule.target_window_class)
                    if window:
                        print(
                            f"✅ Found window by class: {window.title} (Class: {window.class_name})"
                        )
                        return window

                # Then try process-based targeting
                if rule.target_window_process:
                    print(
                        f"🔍 Auto: Searching for windows with process: '{rule.target_window_process}'"
                    )
                    windows = self.window_manager.find_windows_by_process(
                        rule.target_window_process
                    )
                    if windows:
                        print(
                            f"✅ Found {len(windows)} windows with process '{rule.target_window_process}'"
                        )
                        print(f"   Using first window: {windows[0].title}")
                        return windows[0]  # Return first matching window
                    else:
                        error_msg = f"⚠️ Target process not found: '{rule.target_window_process}'"
                        print(f"❌ {error_msg}")
                        if self.on_error:
                            self.on_error(error_msg)

                # Legacy support: Try title-based targeting as last resort
                if getattr(rule, "target_window_title", ""):
                    print(
                        f"🔍 Auto: Searching for window with title (legacy): '{rule.target_window_title}'"
                    )
                    window = self.window_manager.find_window_by_title(
                        rule.target_window_title,
                        exact_match=getattr(rule, "window_exact_match", False),
                    )
                    if window:
                        print(f"✅ Found window by title: {window.title}")
                        print(
                            f"ℹ️ Note: Title-based targeting is deprecated. Consider using class or process targeting."
                        )
                        return window

        # No specific window targeting, use current active window
        print("🔍 No specific window targeting found, getting active window...")
        active_window = self.window_manager.get_active_window()
        if active_window:
            print(f"✅ Using current active window: {active_window.title}")
        else:
            error_msg = "❌ Could not get active window"
            print(error_msg)
            if self.on_error:
                self.on_error(error_msg)

        return active_window

    def _switch_to_context_window(self, target_window: WindowInfo) -> bool:
        """Switch to the target window context"""
        try:
            # Check if we're switching to a different window
            switching_context = (
                not self.current_context_window
                or self.current_context_window.handle != target_window.handle
            )

            # Skip if already in the correct context
            if not switching_context:
                return True

            # Store original cursor position before switching
            if HAS_PYAUTOGUI and self.original_cursor_pos is None:
                try:
                    self.original_cursor_pos = pyautogui.position()
                    print(f"Stored original cursor position: {self.original_cursor_pos}")
                except Exception as e:
                    print(f"Warning: Could not store cursor position: {e}")

            # Switch to the target window
            if self.window_manager.switch_to_window(target_window):
                self.current_context_window = target_window
                print(f"Switched to window context: {target_window.title}")

                # Reset screen unchanged tracking for the new context window
                # This ensures screen unchanged rules only apply AFTER switching to the context window
                self._reset_screen_unchanged_tracking_for_context(target_window)

                # Notify context change
                if self.on_window_context_changed:
                    self.on_window_context_changed(self.current_context_window, target_window)

                return True
            else:
                print(f"Failed to switch to window: {target_window.title}")
                return False

        except Exception as e:
            print(f"Error switching window context: {e}")
            return False

    def _execute_rule_in_context(self, rule: Rule, current_time: float) -> bool:
        """Execute a rule in the current window context"""
        try:
            print(f"🔍 Evaluating rule '{rule.name}' (condition: {rule.condition_type})")

            # Handle different rule condition types
            if rule.condition_type == "screen_unchanged":
                print(
                    f"⏱️ Checking screen unchanged condition (timeout: {rule.screen_unchanged_timeout} min)"
                )
                result = self._check_screen_unchanged_rule_in_context(rule, current_time)
            elif rule.condition_type == "image":
                print(f"🖼️ Checking image detection condition (image: {rule.image_path})")
                result = self._check_image_rule_in_context(rule, current_time)
            else:
                print(f"❌ Unknown rule condition type: {rule.condition_type}")
                return False

            if result:
                print(f"✅ Rule '{rule.name}' condition met - rule triggered!")
            else:
                print(f"❌ Rule '{rule.name}' condition not met")

            return result

        except Exception as e:
            print(f"❌ Error executing rule {rule.name} in context: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _check_image_rule_in_context(self, rule: Rule, current_time: float) -> bool:
        """Check and execute image-based rule in current window context"""
        try:
            # Capture the current window or screen area
            if self.current_context_window:
                # Use window-specific capture if possible
                screenshot = self.window_manager.get_window_screenshot(self.current_context_window)
                offset_x, offset_y = self.current_context_window.x, self.current_context_window.y

                # If window capture fails, fall back to full screen capture
                if screenshot is None:
                    print(
                        f"⚠️ Window capture failed for image rule '{rule.name}', using full screen capture"
                    )
                    screenshot = self.image_detector.capture_screen()
                    offset_x, offset_y = 0, 0
                else:
                    # Convert PIL Image to numpy array if needed
                    screenshot = self._ensure_numpy_array(screenshot)
            else:
                # Fall back to monitor capture
                monitor_idx = rule.monitor_idx if rule.monitor_idx >= 0 else -1
                if monitor_idx == -1:
                    screenshot = self.image_detector.capture_screen()
                    offset_x, offset_y = 0, 0
                else:
                    screenshot, offset_x, offset_y = self._capture_monitor(monitor_idx)

            if screenshot is None:
                print(f"❌ All screenshot methods failed for rule '{rule.name}'")
                return False

            # Check if trigger image is found
            result = self.image_detector.find_image_on_screen(rule.image_path, screenshot)
            if result:
                match_x, match_y, width, height = result
                print(f"Rule '{rule.name}' triggered in window context")

                # Adjust coordinates for window offset
                adjusted_x = match_x + offset_x
                adjusted_y = match_y + offset_y

                # Execute rule actions
                if self.on_rule_triggered:
                    self.on_rule_triggered(rule)

                return self._execute_rule_actions_in_context(rule, adjusted_x, adjusted_y)

            # Check if any disable_on_image is specified and found
            for enabled_rule in self.rule_manager.list_enabled_rules():
                if enabled_rule.disable_on_image and os.path.exists(enabled_rule.disable_on_image):
                    disable_result = self.image_detector.find_image_on_screen(
                        enabled_rule.disable_on_image, screenshot
                    )
                    if disable_result:
                        print(
                            f"⚠️ Disable image found for rule '{enabled_rule.name}', disabling rule"
                        )
                        self.rule_manager.update_rule(enabled_rule.id, enabled=False)

                        # Notify that rule was disabled
                        if self.on_rule_disabled:
                            self.on_rule_disabled(enabled_rule, "Disable image detected")

            return False

        except Exception as e:
            print(f"Error checking image rule in context: {e}")
            return False

    def _ensure_numpy_array(self, image):
        """Convert PIL Image to numpy array for OpenCV processing"""
        import cv2
        import numpy as np
        from PIL import Image

        if image is None:
            return None

        # If it's already a numpy array, return as-is
        if isinstance(image, np.ndarray):
            return image

        # If it's a PIL Image, convert to numpy array
        if isinstance(image, Image.Image):
            # Convert PIL RGB to numpy array and then to BGR for OpenCV
            img_array = np.array(image)
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                # Convert RGB to BGR for OpenCV
                return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            elif len(img_array.shape) == 3 and img_array.shape[2] == 4:
                # Convert RGBA to BGR for OpenCV
                return cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
            else:
                return img_array

        # If it's some other type, try to convert
        try:
            return np.array(image)
        except Exception as e:
            print(f"Warning: Could not convert image to numpy array: {e}")
            return None

    def _check_screen_unchanged_rule_in_context(self, rule: Rule, current_time: float) -> bool:
        """Check screen unchanged rule by monitoring specific context window content"""
        try:
            # Get window-specific screenshot and hash
            if self.current_context_window:
                screenshot = self.window_manager.get_window_screenshot(self.current_context_window)
                if screenshot is None:
                    print(
                        f"⚠️ Could not capture screenshot of window '{self.current_context_window.title}' for rule '{rule.name}'"
                    )
                    print(f"⚠️ Using full screen hash as fallback for change detection")
                    # Use full screen hash as fallback
                    window_hash = self._get_screen_hash()
                    hash_key = f"screen_fallback_{self.current_context_window.handle}"
                    window_name = (
                        f"{self.current_context_window.title} (using full screen fallback)"
                    )
                else:
                    window_hash = self._get_image_hash(screenshot)
                    hash_key = f"window_{self.current_context_window.handle}"
                    window_name = self.current_context_window.title
            else:
                # Fallback to screen capture if no context window
                window_hash = self._get_screen_hash()
                hash_key = "screen"
                window_name = "entire screen"

            if not window_hash:
                print(f"⚠️ Could not generate hash for window content")
                return False

            if not hasattr(self, "_context_hashes"):
                self._context_hashes = {}
            if not hasattr(self, "_context_unchanged_start"):
                self._context_unchanged_start = {}

            # Check if window content changed
            if (
                hash_key not in self._context_hashes
                or self._context_hashes[hash_key] != window_hash
            ):
                self._context_hashes[hash_key] = window_hash
                self._context_unchanged_start[hash_key] = current_time
                print(
                    f"📸 Window content changed in '{window_name}' for rule '{rule.name}' - resetting timer"
                )
                return False

            # Ensure we have a start time
            if hash_key not in self._context_unchanged_start:
                self._context_unchanged_start[hash_key] = current_time
                print(f"📸 Started monitoring '{window_name}' content for rule '{rule.name}'")
                return False

            # Check if unchanged duration exceeds threshold
            unchanged_duration = current_time - self._context_unchanged_start[hash_key]
            timeout_seconds = rule.screen_unchanged_timeout * 60  # Convert minutes to seconds

            if unchanged_duration >= timeout_seconds:
                print(
                    f"✅ Rule '{rule.name}' triggered - '{window_name}' content unchanged for {unchanged_duration:.1f}s (threshold: {timeout_seconds:.1f}s)"
                )

                if self.on_rule_triggered:
                    self.on_rule_triggered(rule)

                # Reset the timer to prevent immediate re-trigger
                self._context_unchanged_start[hash_key] = current_time

                return self._execute_rule_actions_in_context(rule)
            else:
                remaining_time = timeout_seconds - unchanged_duration
                print(
                    f"📸 Rule '{rule.name}' - '{window_name}' content unchanged for {unchanged_duration:.1f}s, need {remaining_time:.1f}s more"
                )

            return False

        except Exception as e:
            print(f"Error checking screen unchanged rule in context: {e}")
            return False

    def _get_image_hash(self, image) -> str:
        """Get hash of an image for change detection"""
        try:
            if image is not None:
                import hashlib

                import numpy as np

                if hasattr(image, "tobytes"):
                    image_bytes = image.tobytes()
                else:
                    # For PIL images
                    img_array = np.array(image)
                    image_bytes = img_array.tobytes()
                return hashlib.md5(image_bytes).hexdigest()
        except Exception as e:
            print(f"Error computing image hash: {e}")
        return ""

    def _reset_screen_unchanged_tracking_for_context(self, target_window: WindowInfo):
        """Initialize screen unchanged tracking for a new context window if not already tracking"""
        try:
            if not hasattr(self, "_context_hashes"):
                self._context_hashes = {}
            if not hasattr(self, "_context_unchanged_start"):
                self._context_unchanged_start = {}

            # Generate hash key for the target window
            hash_key = f"window_{target_window.handle}"

            # Only initialize if we're not already tracking this window
            # This allows continuous monitoring of the same window across context switches
            if hash_key not in self._context_unchanged_start:
                current_time = time.time()
                self._context_unchanged_start[hash_key] = current_time
                print(f"📸 Started monitoring window content: {target_window.title}")
            else:
                print(f"📸 Continuing to monitor window content: {target_window.title}")

            # Always clear hash to get fresh baseline when switching context
            if hash_key in self._context_hashes:
                del self._context_hashes[hash_key]

        except Exception as e:
            print(f"Warning: Could not initialize screen unchanged tracking: {e}")

    def _execute_rule_actions_in_context(
        self, rule: Rule, trigger_x: int = 0, trigger_y: int = 0
    ) -> bool:
        """Execute rule actions in the current window context"""
        try:
            if not rule.actions:
                return True

            print(f"Executing {len(rule.actions)} actions for rule '{rule.name}' in context")

            # Store current state
            self.executing_actions = True
            self.stop_execution = False

            def stop_condition():
                return self.stop_execution or not self._is_mouse_idle()

            # Execute actions with stop condition
            success = self.action_executor.execute_actions(rule.actions, stop_condition)

            if success:
                self.actions_executed += len(rule.actions)
                print(f"Successfully executed rule '{rule.name}' in context")

                # Increment execution count
                rule.execution_count += 1
                self.rule_manager.update_rule(rule.id, execution_count=rule.execution_count)

                # Check if rule should be disabled after X executions
                if (
                    rule.disable_after_executions > 0
                    and rule.execution_count >= rule.disable_after_executions
                ):
                    print(
                        f"⚠️ Rule '{rule.name}' reached execution limit ({rule.execution_count}/{rule.disable_after_executions}), disabling"
                    )
                    self.rule_manager.update_rule(rule.id, enabled=False)

                    # Notify that rule was disabled
                    if self.on_rule_disabled:
                        self.on_rule_disabled(
                            rule,
                            f"Execution limit reached ({rule.execution_count}/{rule.disable_after_executions})",
                        )

                # Notify action execution
                if self.on_action_executed:
                    self.on_action_executed(rule, len(rule.actions))
            else:
                print(f"Failed to execute rule '{rule.name}' in context")

            return success

        except Exception as e:
            print(f"Error executing rule actions in context: {e}")
            return False
        finally:
            self.executing_actions = False

    # Public methods for manual window selection and testing

    def get_available_windows(self) -> List[WindowInfo]:
        """Get list of available windows for rule targeting"""
        return self.window_manager.get_running_windows(include_minimized=False)

    def test_rule_in_window(
        self, rule_id: str, window_title: str = "", window_process: str = ""
    ) -> bool:
        """Test a rule in a specific window context"""
        rule = self.rule_manager.get_rule(rule_id)
        if not rule:
            print(f"Rule not found: {rule_id}")
            return False

        # Find target window
        target_window = None
        if window_title:
            target_window = self.window_manager.find_window_by_title(window_title)
        elif window_process:
            windows = self.window_manager.find_windows_by_process(window_process)
            target_window = windows[0] if windows else None

        if not target_window:
            print(f"Target window not found: {window_title or window_process}")
            return False

        # Switch to window and test rule
        original_window = self.window_manager.get_active_window()
        try:
            if self._switch_to_context_window(target_window):
                result = self._execute_rule_in_context(rule, time.time())
                return result
            return False
        finally:
            # Restore original window
            if original_window:
                self.window_manager.switch_to_window(original_window)
            self.current_context_window = None

    def set_keep_context_focused(self, keep_focused: bool):
        """Set whether to keep context window focused after rule execution"""
        self.keep_context_window_focused = keep_focused
        if not keep_focused and self.current_context_window:
            # Immediately restore if setting is changed to False
            print("Context focus disabled - restoring original context")
            self._restore_original_context()

    def force_restore_context(self):
        """Manually force restoration of original context and cursor position"""
        if self.current_context_window:
            print("Manually restoring original context and cursor position")
            self._restore_original_context()
        else:
            print("No context to restore")

    def get_cursor_info(self) -> Dict[str, any]:
        """Get current cursor position information"""
        info = {
            "has_pyautogui": HAS_PYAUTOGUI,
            "original_pos": self.original_cursor_pos,
            "context_pos": self.context_cursor_pos,
            "current_context_window": (
                self.current_context_window.title if self.current_context_window else None
            ),
        }

        if HAS_PYAUTOGUI:
            try:
                current_pos = pyautogui.position()
                info["current_pos"] = (current_pos.x, current_pos.y)
            except Exception as e:
                info["current_pos"] = f"Error: {e}"
        else:
            info["current_pos"] = "PyAutoGUI not available"

        return info

    def get_debug_info(self) -> Dict[str, any]:
        """Get comprehensive debug information"""
        info = {
            "context_aware_active": self.context_execution_active,
            "monitoring_running": self.running,
            "current_context_window": (
                self.current_context_window.title if self.current_context_window else None
            ),
            "keep_context_focused": self.keep_context_window_focused,
            "cluster_cooldown": self.cluster_cooldown,
            "cursor_tracking": {
                "has_pyautogui": HAS_PYAUTOGUI,
                "original_pos": self.original_cursor_pos,
                "context_pos": self.context_cursor_pos,
            },
        }

        # Rule information
        all_rules = self.rule_manager.list_rules()
        enabled_rules = self.rule_manager.list_enabled_rules()
        clusters = self.rule_manager.get_rules_by_cluster()

        info["rules"] = {
            "total": len(all_rules),
            "enabled": len(enabled_rules),
            "clusters": len(clusters),
            "cluster_details": {k: len(v) for k, v in clusters.items()},
        }

        # Window manager info
        try:
            windows = self.window_manager.get_running_windows()
            info["windows"] = {
                "total_found": len(windows),
                "active_window": (
                    self.window_manager.get_active_window().title
                    if self.window_manager.get_active_window()
                    else None
                ),
            }
        except Exception as e:
            info["windows"] = {"error": str(e)}

        return info
