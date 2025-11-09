"""
Modern API for Screen Automator using framework features.

This module provides the recommended, modern way to use Screen Automator
with auto-waiting, expectations, and page objects built-in.

Instead of using low-level APIs directly, use this module for:
- Automatic waiting for elements
- Robust assertions
- Clean, maintainable code

Example:
    from src.modern_api import ScreenAutomatorFramework

    # Modern, framework-based usage
    framework = ScreenAutomatorFramework()

    # Auto-waiting image detection
    framework.wait_for_image("button.png", timeout=5000)

    # Click with automatic waiting
    framework.click_image("button.png")

    # Robust expectations
    framework.expect_image("success.png")
    framework.expect_no_image("loading.png")
"""

from typing import Optional
from .automator import ScreenAutomator
from .actionability import SmartAutomator, AutoWaiter
from .expectations import expect
from .rule_manager import Rule


class ScreenAutomatorFramework:
    """
    Modern, framework-based interface to Screen Automator.

    This class wraps the core ScreenAutomator with framework features:
    - Auto-waiting via SmartAutomator
    - Expectations API for robust assertions
    - Simplified API for common operations

    Use this instead of directly using ScreenAutomator for new code.
    """

    def __init__(self, rules_dir: str = "data/rules", timeout: int = 30000):
        """
        Initialize the framework.

        Args:
            rules_dir: Directory containing rule definitions
            timeout: Default timeout for operations in milliseconds
        """
        # Core automator (manages rules and monitoring)
        self.automator = ScreenAutomator(rules_dir=rules_dir)

        # Smart automator (auto-waiting for images)
        self.smart = SmartAutomator(
            self.automator.image_detector,
            timeout=timeout
        )

        # Auto-waiter (for custom waiting logic)
        self.waiter = AutoWaiter(timeout=timeout)

        # Default timeout
        self.timeout = timeout

    # =================================================================
    # Monitoring Control (delegates to core automator)
    # =================================================================

    def start_monitoring(self):
        """Start rule-based monitoring."""
        self.automator.start_monitoring()

    def stop_monitoring(self):
        """Stop rule-based monitoring."""
        self.automator.stop_monitoring()

    @property
    def is_running(self) -> bool:
        """Check if monitoring is active."""
        return self.automator.running

    # =================================================================
    # Rule Management (modern API)
    # =================================================================

    def add_rule(self, rule: Rule):
        """Add a rule to the automator."""
        self.automator.rule_manager.add_rule(rule)

    def get_rules(self):
        """Get all rules."""
        return self.automator.rule_manager.get_all_rules()

    def enable_rule(self, rule_id: str):
        """Enable a specific rule."""
        rule = self.automator.rule_manager.get_rule(rule_id)
        if rule:
            rule.enabled = True
            self.automator.rule_manager.save_rule(rule)

    def disable_rule(self, rule_id: str):
        """Disable a specific rule."""
        rule = self.automator.rule_manager.get_rule(rule_id)
        if rule:
            rule.enabled = False
            self.automator.rule_manager.save_rule(rule)

    # =================================================================
    # Modern Image Operations (with auto-waiting)
    # =================================================================

    def wait_for_image(
        self,
        image_path: str,
        timeout: Optional[int] = None,
        ensure_stable: bool = True
    ):
        """
        Wait for an image to appear on screen.

        This is the modern replacement for manual time.sleep() + find_image().

        Args:
            image_path: Path to image to wait for
            timeout: Override default timeout (milliseconds)
            ensure_stable: Wait for image to be stable (not animating)

        Returns:
            Tuple of (x, y) coordinates where image was found

        Example:
            location = framework.wait_for_image("button.png", timeout=5000)
        """
        timeout_ms = timeout if timeout is not None else self.timeout

        if ensure_stable:
            return self.waiter.wait_for_stable_image(
                image_path,
                self.automator.image_detector,
                timeout=timeout_ms
            )
        else:
            return self.waiter.wait_for_image(
                image_path,
                self.automator.image_detector,
                timeout=timeout_ms
            )

    def click_image(
        self,
        image_path: str,
        timeout: Optional[int] = None,
        ensure_stable: bool = True
    ):
        """
        Click an image with automatic waiting.

        Modern replacement for find_image() + manual click.

        Args:
            image_path: Path to image to click
            timeout: Override default timeout (milliseconds)
            ensure_stable: Wait for stable location before clicking

        Example:
            framework.click_image("save_button.png")
        """
        self.smart.click_image(image_path, timeout=timeout, ensure_stable=ensure_stable)

    def wait_for_image_to_disappear(
        self,
        image_path: str,
        timeout: Optional[int] = None
    ):
        """
        Wait for an image to disappear from screen.

        Modern replacement for manual polling loops.

        Args:
            image_path: Path to image that should disappear
            timeout: Override default timeout (milliseconds)

        Example:
            framework.wait_for_image_to_disappear("loading.png")
        """
        self.smart.wait_for_image_to_disappear(image_path, timeout=timeout)

    # =================================================================
    # Modern Expectations API
    # =================================================================

    def expect_image(self, image_path: str, timeout: Optional[int] = None):
        """
        Assert that an image is visible (with auto-retry).

        Modern replacement for assert find_image() is not None.

        Args:
            image_path: Path to image that should be visible
            timeout: Override default timeout (milliseconds)

        Raises:
            ExpectationTimeoutError: If image not found within timeout

        Example:
            framework.expect_image("success.png", timeout=5000)
        """
        timeout_ms = timeout if timeout is not None else self.timeout
        expect(self.automator.image_detector, timeout=timeout_ms).to_have_image(
            image_path
        )

    def expect_no_image(self, image_path: str, timeout: Optional[int] = None):
        """
        Assert that an image is NOT visible (with auto-retry).

        Modern replacement for assert find_image() is None.

        Args:
            image_path: Path to image that should NOT be visible
            timeout: Override default timeout (milliseconds)

        Raises:
            ExpectationTimeoutError: If image still visible after timeout

        Example:
            framework.expect_no_image("loading.png")
        """
        timeout_ms = timeout if timeout is not None else self.timeout
        expect(self.automator.image_detector, timeout=timeout_ms).not_to_have_image(
            image_path
        )

    # =================================================================
    # Callbacks (delegates to core automator)
    # =================================================================

    def on_rule_triggered(self, callback):
        """Set callback for when a rule triggers."""
        self.automator.on_rule_triggered = callback

    def on_action_executed(self, callback):
        """Set callback for when an action executes."""
        self.automator.on_action_executed = callback

    def on_error(self, callback):
        """Set callback for errors."""
        self.automator.on_error = callback

    def on_rule_disabled(self, callback):
        """Set callback for when a rule is auto-disabled."""
        self.automator.on_rule_disabled = callback

    # =================================================================
    # Configuration
    # =================================================================

    def set_check_interval(self, seconds: float):
        """Set how often to check for triggers."""
        self.automator.check_interval = seconds

    def set_timeout(self, milliseconds: int):
        """Set default timeout for operations."""
        self.timeout = milliseconds
        self.waiter.timeout = milliseconds

    def set_mouse_idle_threshold(self, seconds: float):
        """Set how long mouse must be idle before executing actions."""
        self.automator.mouse_idle_threshold = seconds


# Convenience function to create framework instance
def create_framework(rules_dir: str = "data/rules", timeout: int = 30000):
    """
    Create a Screen Automator Framework instance.

    This is the recommended way to use Screen Automator.

    Args:
        rules_dir: Directory containing rule definitions
        timeout: Default timeout for operations in milliseconds

    Returns:
        ScreenAutomatorFramework instance

    Example:
        from src.modern_api import create_framework

        framework = create_framework(timeout=10000)
        framework.wait_for_image("button.png")
        framework.click_image("button.png")
        framework.expect_image("success.png")
    """
    return ScreenAutomatorFramework(rules_dir=rules_dir, timeout=timeout)
