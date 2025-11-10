import hashlib
import os
import threading
import time
from types import SimpleNamespace
from typing import Callable, Optional

from pynput import mouse

# Monitor info utilities
try:
    from screeninfo import get_monitors
except ImportError:  # graceful fallback – assumes single monitor
    get_monitors = None

import pyautogui  # late import ok here

from .action_executor import ActionExecutor
from .image_detector import ImageDetector
from .rule_manager import Rule, RuleManager


class ScreenAutomator:
    def __init__(self, rules_dir: str = "data/rules"):
        self.image_detector = ImageDetector()
        self.action_executor = ActionExecutor()
        self.rule_manager = RuleManager(rules_dir)

        self.running = False
        self.check_interval = 10.0  # Check every 10 seconds
        self.worker_thread = None
        self.mouse_listener = None

        # Mouse tracking
        self.last_mouse_move_time = time.time()
        self.last_mouse_pos = (0, 0)
        self.mouse_idle_threshold = 5.0  # 5 seconds of no movement
        self.executing_actions = False
        self.stop_execution = False

        # Rule execution tracking
        self.last_rule_execution_time: dict[str, float] = {}  # Maps rule_id to last execution time
        self.min_rule_interval = 5.0  # Minimum 5 seconds between rule executions

        # Action tracking (global action limits removed)
        self.actions_executed = 0  # Count of actions executed in current session

        # Screen unchanged tracking
        self.last_screen_hash: Optional[str] = None
        self.screen_unchanged_start_time: Optional[float] = None
        self.screen_unchanged_rules: dict[str, float] = (
            {}
        )  # Maps rule_id to start time when screen first became unchanged

        # Callbacks
        self.on_rule_triggered: Optional[Callable[[Rule], None]] = None
        self.on_action_executed: Optional[Callable[[Rule, int], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_rule_disabled: Optional[Callable[[Rule, str], None]] = None

        # Cache monitors layout (x, y, width, height)
        self._monitors = self._detect_monitors()

        # Start mouse listener
        self._start_mouse_listener()

    def _on_mouse_move(self, x: int, y: int) -> bool:
        """Callback for mouse movement"""
        self.last_mouse_pos = (x, y)
        self.last_mouse_move_time = time.time()

        # If we're executing actions and mouse moves, stop execution
        if self.executing_actions:
            self.stop_execution = True

        return True  # Continue listening

    def _start_mouse_listener(self):
        """Start listening for mouse movement"""
        if self.mouse_listener is None:
            self.mouse_listener = mouse.Listener(on_move=self._on_mouse_move)
            self.mouse_listener.start()

    def _is_mouse_idle(self) -> bool:
        """Check if mouse has been idle for the threshold period"""
        return (time.time() - self.last_mouse_move_time) >= self.mouse_idle_threshold

    def _get_screen_hash(self) -> str:
        """Get a hash of the current screen for change detection"""
        try:
            screenshot = self.image_detector.capture_screen()
            if screenshot is not None:
                # Convert image to bytes and compute hash

                import numpy as np

                if hasattr(screenshot, "tobytes"):
                    image_bytes = screenshot.tobytes()
                else:
                    # For PIL images
                    img_array = np.array(screenshot)
                    image_bytes = img_array.tobytes()
                return hashlib.md5(image_bytes, usedforsecurity=False).hexdigest()
        except Exception as e:
            print(f"Error computing screen hash: {e}")
        return ""

    def start_monitoring(self):
        """Start monitoring the screen for trigger images"""
        if self.running:
            return

        self.running = True
        self.stop_execution = False
        self.actions_executed = 0  # Reset action counter when starting
        self.worker_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.worker_thread.start()

        print("Screen monitoring started")

    def stop_monitoring(self):
        """Stop monitoring the screen"""
        self.running = False
        self.stop_execution = True
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        print("Screen monitoring stopped")

    # Alias for compatibility with GUI
    stop = stop_monitoring

    def _detect_monitors(self):
        """Return ordered list of monitors with x, y, width, height fields."""
        monitors = []
        if get_monitors:
            for m in get_monitors():
                monitors.append(SimpleNamespace(x=m.x, y=m.y, width=m.width, height=m.height))
        else:
            # Fallback – assume single primary monitor
            w, h = pyautogui.size()
            monitors.append(SimpleNamespace(x=0, y=0, width=w, height=h))
        return monitors

    def _capture_monitor(self, idx: int):
        """Capture specific monitor by index (0-based)."""
        if idx < 0 or idx >= len(self._monitors):
            # invalid, capture full screen instead
            return self.image_detector.capture_screen(), 0, 0
        m = self._monitors[idx]
        img = self.image_detector.capture_region(m.x, m.y, m.width, m.height)
        return img, m.x, m.y

    def _monitor_loop(self):
        """Main monitoring loop with per-monitor capture support"""
        while self.running:
            try:
                # Note: Global action limit removed - now handled per-rule

                if not self._is_mouse_idle():
                    time.sleep(0.1)
                    continue

                enabled_rules = self.rule_manager.list_enabled_rules()
                if not enabled_rules:
                    time.sleep(self.check_interval)
                    continue

                current_time = time.time()

                # Check for screen changes for screen_unchanged rules
                screen_unchanged_rules = [
                    r for r in enabled_rules if r.condition_type == "screen_unchanged"
                ]
                if screen_unchanged_rules:
                    self._check_screen_unchanged_rules(screen_unchanged_rules, current_time)

                # Process image-based rules
                image_rules = [r for r in enabled_rules if r.condition_type == "image"]
                if image_rules:
                    # Pre-group rules by monitor index to minimise captures
                    rules_by_monitor: dict[int, list[Rule]] = {}
                    for r in image_rules:
                        rules_by_monitor.setdefault(r.monitor_idx, []).append(r)

                    # Handle any-monitor rules (-1) separately (capture once full screen)
                    if -1 in rules_by_monitor:
                        full_img = self.image_detector.capture_screen()
                        self._process_rules_on_image(
                            rules_by_monitor[-1], full_img, 0, 0, current_time
                        )

                    # Capture per monitor for monitor-specific rules
                    for midx, rules in rules_by_monitor.items():
                        if midx == -1:
                            continue
                        img, off_x, off_y = self._capture_monitor(midx)
                        self._process_rules_on_image(rules, img, off_x, off_y, current_time)

            except Exception as e:
                print(f"Error in monitor loop: {e}")
            finally:
                time.sleep(self.check_interval)

    def _check_screen_unchanged_rules(self, rules: list[Rule], current_time: float):
        """Check screen unchanged rules"""
        try:
            # Get current screen hash
            current_hash = self._get_screen_hash()
            if not current_hash:
                return

            # Check if screen has changed
            if self.last_screen_hash != current_hash:
                # Screen has changed, reset all timers
                self.last_screen_hash = current_hash
                self.screen_unchanged_start_time = current_time
                self.screen_unchanged_rules.clear()
                return

            # Screen is unchanged, check each rule
            for rule in rules:
                if not self.running or not self._is_mouse_idle():
                    break

                # Check if this rule has already been triggered recently
                last_exec_time = self.last_rule_execution_time.get(rule.id, 0)
                time_since_last_exec = current_time - last_exec_time

                if time_since_last_exec < self.min_rule_interval:
                    continue

                # Track when this rule first detected screen unchanged
                if rule.id not in self.screen_unchanged_rules:
                    self.screen_unchanged_rules[rule.id] = current_time
                    continue

                # Check if timeout has been reached
                time_unchanged = current_time - self.screen_unchanged_rules[rule.id]
                timeout_seconds = rule.screen_unchanged_timeout * 60  # Convert minutes to seconds

                if time_unchanged >= timeout_seconds:
                    print(
                        f"Screen unchanged for {rule.screen_unchanged_timeout:.1f} minutes, executing rule '{rule.name}'"
                    )

                    # Execute the rule's actions
                    self.executing_actions = True
                    self.action_executor.execute_actions(
                        rule.actions,
                        stop_condition=lambda: not self._is_mouse_idle() or self.stop_execution,
                    )
                    self.executing_actions = False

                    # Update action counter
                    actions_executed_in_rule = len(rule.actions)
                    self.actions_executed += actions_executed_in_rule
                    print(
                        f"Executed {actions_executed_in_rule} actions. Total: {self.actions_executed}"
                    )

                    self.last_rule_execution_time[rule.id] = time.time()

                    # Remove from unchanged tracking to prevent immediate re-trigger
                    if rule.id in self.screen_unchanged_rules:
                        del self.screen_unchanged_rules[rule.id]

                    if self.on_rule_triggered:
                        self.on_rule_triggered(rule)

                    if self.on_action_executed:
                        for idx, _ in enumerate(rule.actions):
                            self.on_action_executed(rule, idx)

        except Exception as e:
            print(f"Error checking screen unchanged rules: {e}")

    def _process_rules_on_image(
        self, rules: list[Rule], img, offset_x: int, offset_y: int, current_time: float
    ):
        """Evaluate list of rules against provided image captured at offsets."""
        for rule in rules:
            if not self.running or not self._is_mouse_idle():
                break
            try:
                if not rule.image_path or not os.path.exists(rule.image_path):
                    err = f"Invalid image path for rule '{rule.name}': {rule.image_path}"
                    print(err)
                    if self.on_error:
                        self.on_error(err)
                    continue

                match = self.image_detector.find_image_on_screen(rule.image_path, img)

                if match:
                    x, y, width, height = match
                    x += offset_x
                    y += offset_y
                    print(
                        f"Found match for rule '{rule.name}' at {(x, y, width, height)} (monitor offset {offset_x},{offset_y})"
                    )

                    # Perform sanity check: verify match is near the original capture area
                    is_valid_match = True
                    if rule.capture_width > 0 and rule.capture_height > 0:
                        # Calculate distance from original capture area
                        capture_center_x = rule.capture_x + rule.capture_width / 2
                        capture_center_y = rule.capture_y + rule.capture_height / 2
                        match_center_x = x + width / 2
                        match_center_y = y + height / 2

                        # Calculate distance between centers
                        distance = (
                            (match_center_x - capture_center_x) ** 2
                            + (match_center_y - capture_center_y) ** 2
                        ) ** 0.5

                        # Maximum allowed distance (half of the capture area diagonal)
                        max_distance = ((rule.capture_width**2 + rule.capture_height**2) ** 0.5) / 2

                        if distance > max_distance:
                            print(
                                f"Sanity check failed: Match at {(x, y, width, height)} is too far from capture area "
                                f"({rule.capture_x}, {rule.capture_y}, {rule.capture_width}, {rule.capture_height})"
                            )
                            print(f"Distance: {distance:.2f}, Max allowed: {max_distance:.2f}")
                            is_valid_match = False
                        else:
                            print("Sanity check passed: Match is within expected area")

                    # Double-check with higher confidence and sanity check
                    if self._is_mouse_idle() and is_valid_match:
                        last_exec_time = self.last_rule_execution_time.get(rule.id, 0)
                        time_since_last_exec = current_time - last_exec_time

                        if time_since_last_exec < self.min_rule_interval:
                            print(
                                f"Skipping rule '{rule.name}' - executed too recently ({time_since_last_exec:.1f}s ago)"
                            )
                            continue

                        # Execute the rule's actions
                        print(f"Executing actions for rule '{rule.name}'")
                        self.executing_actions = True
                        success = self.action_executor.execute_actions(
                            rule.actions,
                            stop_condition=lambda: not self._is_mouse_idle() or self.stop_execution,
                        )
                        self.executing_actions = False

                        if success:
                            # Update action counter
                            actions_executed_in_rule = len(rule.actions)
                            self.actions_executed += actions_executed_in_rule
                            print(
                                f"Executed {actions_executed_in_rule} actions. Total: {self.actions_executed}"
                            )

                            # Increment rule execution count
                            rule.execution_count += 1
                            self.rule_manager.update_rule(
                                rule.id, execution_count=rule.execution_count
                            )

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

                            self.last_rule_execution_time[rule.id] = time.time()

                            if self.on_rule_triggered:
                                self.on_rule_triggered(rule)

                            if self.on_action_executed:
                                for idx, _ in enumerate(rule.actions):
                                    self.on_action_executed(rule, idx)
                        else:
                            print(f"Failed to execute rule '{rule.name}'")

            except Exception as e:
                msg = f"Error processing rule '{rule.name}': {e}"
                print(msg)
                if self.on_error:
                    self.on_error(msg)

    def test_rule(self, rule_id: str) -> bool:
        """Test a specific rule once"""
        rule = self.rule_manager.get_rule(rule_id)
        if not rule:
            print(f"Rule with ID '{rule_id}' not found")
            return False

        print(f"Testing rule '{rule.name}'...")

        # Check if trigger image is on screen
        match = self.image_detector.find_image_on_screen(rule.image_path)
        if not match:
            print("Trigger image not found on screen")
            return False

        print(f"Trigger image found at {match}")

        # Execute actions
        self._execute_rule_actions(rule)
        print(f"Rule '{rule.name}' test completed")
        return True

    def test_rule_by_name(self, rule_name: str) -> bool:
        """Test a specific rule by name"""
        rule = self.rule_manager.get_rule_by_name(rule_name)
        if not rule:
            print(f"Rule with name '{rule_name}' not found")
            return False

        return self.test_rule(rule.id)

    def force_execute_rule(self, rule_id: str) -> bool:
        """Force execute a rule without checking for trigger image"""
        rule = self.rule_manager.get_rule(rule_id)
        if not rule:
            print(f"Rule with ID '{rule_id}' not found")
            return False

        print(f"Force executing rule '{rule.name}'...")
        self._execute_rule_actions(rule)

        # Update last execution time
        self.last_rule_execution_time[rule_id] = time.time()

        print(f"Rule '{rule.name}' force execution completed")
        return True

    def set_check_interval(self, interval: float):
        """Set the interval between screen checks"""
        self.check_interval = max(0.1, interval)  # Minimum 0.1 seconds

    def is_running(self) -> bool:
        """Check if the automator is currently running"""
        return self.running

    @property
    def is_monitoring(self) -> bool:
        """Check if the automator is currently monitoring (alias for is_running)"""
        return self.running

    def get_status(self) -> dict:
        """Get current status of the automator"""
        return {
            "running": self.running,
            "check_interval": self.check_interval,
            "total_rules": len(self.rule_manager.rules),
            "enabled_rules": len(self.rule_manager.list_enabled_rules()),
            "min_rule_interval": self.min_rule_interval,
            "actions_executed": self.actions_executed,
        }

    def set_min_rule_interval(self, interval: float):
        """Set the minimum interval between rule executions"""
        self.min_rule_interval = max(0.5, interval)  # Minimum 0.5 seconds

    # Note: Global action limits removed - use per-rule disable_after_executions instead

    def reset_action_counter(self):
        """Reset the action execution counter"""
        self.actions_executed = 0

    def _execute_rule_actions(self, rule: Rule):
        """Execute all actions for a triggered rule"""
        self.executing_actions = True
        self.stop_execution = False

        try:
            for i, action in enumerate(rule.actions):
                if not self.running or self.stop_execution or not self._is_mouse_idle():
                    print("Action execution interrupted by mouse movement or stop signal")
                    break

                print(f"  Executing action {i+1}/{len(rule.actions)}: {action.type.value}")
                try:
                    success = self.action_executor.execute_action(action)
                    self.actions_executed += 1  # Increment action counter for each action

                    if self.on_action_executed:
                        self.on_action_executed(rule, i)

                    if not success:
                        error_msg = f"Failed to execute action {i+1} for rule '{rule.name}'"
                        print(error_msg)
                        if self.on_error:
                            self.on_error(error_msg)
                        break
                except Exception as e:
                    error_msg = f"Error executing action {i+1} for rule '{rule.name}': {e}"
                    print(error_msg)
                    if self.on_error:
                        self.on_error(error_msg)
                    break

            # Print action summary
            print(f"Actions executed: {self.actions_executed}")
        finally:
            self.executing_actions = False
