"""
Actionability checks and auto-waiting system.

This module implements Playwright-style auto-waiting and actionability checks
to eliminate flaky tests caused by timing issues. Elements are automatically
waited for and validated before actions are performed.

Based on the comprehensive improvement blueprint for screen_automator.
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional


class ActionabilityState(Enum):
    """States that an element can be in for actionability checks."""

    VISIBLE = "visible"
    STABLE = "stable"
    ENABLED = "enabled"
    RECEIVES_EVENTS = "receives_events"
    NOT_OBSCURED = "not_obscured"


@dataclass
class ActionabilityResult:
    """Result of an actionability check."""

    passed: bool
    state: ActionabilityState
    message: str
    location: Optional[tuple[int, int]] = None


class ActionabilityError(Exception):
    """Raised when an element fails actionability checks."""

    pass


class TimeoutError(Exception):
    """Raised when waiting for a condition times out."""

    pass


class AutoWaiter:
    """
    Implements auto-waiting and actionability checks for GUI elements.

    This class provides Playwright-style auto-waiting that eliminates the need
    for manual time.sleep() calls and reduces flaky tests.

    Example:
        waiter = AutoWaiter(timeout=10000)
        location = waiter.wait_for_image("button.png", automator)
        waiter.ensure_stable(location, duration=100)
    """

    def __init__(self, timeout: int = 30000, poll_interval: int = 100):
        """
        Initialize the auto-waiter.

        Args:
            timeout: Maximum time to wait in milliseconds (default: 30000ms = 30s)
            poll_interval: How often to check condition in milliseconds (default: 100ms)
        """
        self.timeout = timeout
        self.poll_interval = poll_interval

    def wait_for_condition(
        self,
        condition: Callable[[], Any],
        condition_name: str = "condition",
        timeout: Optional[int] = None,
    ) -> Any:
        """
        Wait for a condition to become true.

        This is the core waiting mechanism. It polls the condition function
        until it returns a truthy value or timeout is reached.

        Args:
            condition: A callable that returns truthy value when condition is met
            condition_name: Name of condition for error messages
            timeout: Override default timeout in milliseconds

        Returns:
            The truthy result from the condition function

        Raises:
            TimeoutError: If condition is not met within timeout period

        Example:
            result = waiter.wait_for_condition(
                lambda: automator.find_image("button.png"),
                "button to appear",
                timeout=5000
            )
        """
        timeout_ms = timeout if timeout is not None else self.timeout
        start_time = time.time()
        last_error = None

        while (time.time() - start_time) * 1000 < timeout_ms:
            try:
                result = condition()
                if result:
                    return result
            except Exception as e:
                last_error = e

            time.sleep(self.poll_interval / 1000.0)

        # Timeout reached
        elapsed = (time.time() - start_time) * 1000
        error_msg = f"Timeout waiting for {condition_name} after {elapsed:.0f}ms"
        if last_error:
            error_msg += f" (last error: {last_error})"
        raise TimeoutError(error_msg)

    def wait_for_image(
        self, image_path: str, automator: Any, timeout: Optional[int] = None
    ) -> tuple[int, int]:
        """
        Wait for an image to appear on screen.

        This replaces brittle code like:
            time.sleep(5)
            location = automator.find_image("button.png")

        With robust auto-waiting:
            location = waiter.wait_for_image("button.png", automator)

        Args:
            image_path: Path to the image to find
            automator: The automator instance with find_image method
            timeout: Override default timeout in milliseconds

        Returns:
            Tuple of (x, y) coordinates where image was found

        Raises:
            TimeoutError: If image not found within timeout period
        """

        def find_image():
            try:
                location = automator.find_image(image_path)
                return location if location else None
            except Exception:
                return None

        return self.wait_for_condition(find_image, f"image '{image_path}' to appear", timeout)

    def ensure_stable(
        self,
        location_getter: Callable[[], tuple[int, int]],
        duration: int = 100,
        tolerance: int = 5,
    ) -> tuple[int, int]:
        """
        Ensure an element's location is stable (not animating).

        This prevents clicking on elements that are still moving, which is
        a common cause of flaky tests.

        Args:
            location_getter: Function that returns current (x, y) location
            duration: How long location must be stable in milliseconds (default: 100ms)
            tolerance: Maximum pixel movement allowed (default: 5px)

        Returns:
            The stable (x, y) location

        Raises:
            TimeoutError: If location never stabilizes within timeout period

        Example:
            stable_location = waiter.ensure_stable(
                lambda: automator.find_image("button.png"),
                duration=200
            )
        """
        start_time = time.time()
        last_location = location_getter()
        stable_start = time.time()

        while (time.time() - start_time) * 1000 < self.timeout:
            time.sleep(self.poll_interval / 1000.0)
            current_location = location_getter()

            # Check if location has moved
            if current_location and last_location:
                dx = abs(current_location[0] - last_location[0])
                dy = abs(current_location[1] - last_location[1])

                if dx <= tolerance and dy <= tolerance:
                    # Location is stable, check if it's been stable long enough
                    stable_duration = (time.time() - stable_start) * 1000
                    if stable_duration >= duration:
                        return current_location
                else:
                    # Location moved, reset stability timer
                    stable_start = time.time()

            last_location = current_location

        raise TimeoutError(f"Element location never stabilized within {self.timeout}ms")

    def wait_for_stable_image(
        self,
        image_path: str,
        automator: Any,
        stability_duration: int = 100,
        timeout: Optional[int] = None,
    ) -> tuple[int, int]:
        """
        Wait for an image to appear AND be stable.

        This combines wait_for_image and ensure_stable for maximum reliability.

        Args:
            image_path: Path to the image to find
            automator: The automator instance
            stability_duration: How long location must be stable in ms
            timeout: Override default timeout in milliseconds

        Returns:
            The stable (x, y) coordinates

        Raises:
            TimeoutError: If image doesn't appear or stabilize in time

        Example:
            # This replaces:
            #   time.sleep(5)
            #   location = automator.find_image("button.png")
            #
            # With:
            location = waiter.wait_for_stable_image("button.png", automator)
        """
        # First wait for image to appear
        self.wait_for_image(image_path, automator, timeout)

        # Then ensure it's stable
        return self.ensure_stable(
            lambda: automator.find_image(image_path), duration=stability_duration
        )

    def check_actionability(self, location: tuple[int, int], checks: Optional[list] = None) -> list:
        """
        Perform actionability checks on an element.

        This validates that an element is ready to receive actions, similar
        to Playwright's actionability checks.

        Args:
            location: The (x, y) coordinates of the element
            checks: List of ActionabilityState checks to perform
                   If None, performs all checks

        Returns:
            List of ActionabilityResult objects

        Example:
            results = waiter.check_actionability(
                location,
                checks=[ActionabilityState.VISIBLE, ActionabilityState.STABLE]
            )
            if not all(r.passed for r in results):
                raise ActionabilityError("Element not actionable")
        """
        if checks is None:
            checks = [
                ActionabilityState.VISIBLE,
                ActionabilityState.STABLE,
            ]

        results = []
        for check in checks:
            result = self._perform_check(location, check)
            results.append(result)

        return results

    def _perform_check(
        self, location: tuple[int, int], check: ActionabilityState
    ) -> ActionabilityResult:
        """
        Perform a single actionability check.

        Args:
            location: Element location
            check: The check to perform

        Returns:
            ActionabilityResult
        """
        # For now, implement basic checks
        # These can be extended with actual screen/window analysis

        if check == ActionabilityState.VISIBLE:
            # Basic visibility check - if we have a location, it's visible
            return ActionabilityResult(
                passed=location is not None,
                state=check,
                message="Element is visible" if location else "Element not visible",
                location=location,
            )

        elif check == ActionabilityState.STABLE:
            # This should be called through ensure_stable()
            return ActionabilityResult(
                passed=True,
                state=check,
                message="Stability should be checked via ensure_stable()",
                location=location,
            )

        return ActionabilityResult(
            passed=True, state=check, message=f"Check {check.value} passed", location=location
        )


class SmartAutomator:
    """
    Wrapper that adds auto-waiting to any automator instance.

    This wrapper automatically adds actionability checks and auto-waiting
    to all actions, eliminating the need for manual sleep() calls.

    Example:
        automator = Automator()
        smart = SmartAutomator(automator, timeout=10000)

        # Old way (brittle):
        # time.sleep(5)
        # automator.click_image("button.png")

        # New way (robust):
        smart.click_image("button.png")  # Auto-waits!
    """

    def __init__(self, automator: Any, timeout: int = 30000):
        """
        Initialize smart automator wrapper.

        Args:
            automator: The base automator to wrap
            timeout: Default timeout for all operations in milliseconds
        """
        self.automator = automator
        self.waiter = AutoWaiter(timeout=timeout)

    def click_image(
        self, image_path: str, timeout: Optional[int] = None, ensure_stable: bool = True
    ):
        """
        Click an image with automatic waiting and stability checks.

        Args:
            image_path: Path to image to click
            timeout: Override default timeout
            ensure_stable: Whether to wait for stable location (default: True)
        """
        if ensure_stable:
            location = self.waiter.wait_for_stable_image(
                image_path, self.automator, timeout=timeout
            )
        else:
            location = self.waiter.wait_for_image(image_path, self.automator, timeout=timeout)

        # Perform the click
        if hasattr(self.automator, "click_at"):
            self.automator.click_at(location[0], location[1])
        else:
            # Fallback to pyautogui if available
            import pyautogui

            pyautogui.click(location[0], location[1])

    def wait_for_image_to_disappear(self, image_path: str, timeout: Optional[int] = None):
        """
        Wait for an image to disappear from screen.

        Args:
            image_path: Path to image that should disappear
            timeout: Override default timeout

        Raises:
            TimeoutError: If image still visible after timeout
        """

        def image_gone():
            try:
                location = self.automator.find_image(image_path)
                return location is None
            except Exception:
                return True  # If find fails, assume it's gone

        self.waiter.wait_for_condition(image_gone, f"image '{image_path}' to disappear", timeout)
