"""
Expectations library for robust, auto-retrying assertions.

This module provides Playwright-style expect() assertions that automatically
retry, eliminating race conditions and flaky tests.

Instead of brittle assertions that fail immediately:
    assert automator.find_image("button.png") is not None

Use expectations that auto-retry:
    expect(automator).to_have_image("button.png", timeout=5000)

Based on the comprehensive improvement blueprint for screen_automator.
"""

import time
from dataclasses import dataclass
from typing import Any, Callable


class ExpectationError(AssertionError):
    """Raised when an expectation fails after retrying."""

    pass


class ExpectationTimeoutError(ExpectationError):
    """Raised when an expectation times out."""

    pass


@dataclass
class ExpectationResult:
    """Result of an expectation check."""

    passed: bool
    message: str
    actual: Any = None
    expected: Any = None


class Expectation:
    """
    Base class for expectations that auto-retry.

    This implements the core retry logic that polls a condition
    until it passes or timeout is reached.
    """

    def __init__(self, subject: Any, timeout: int = 5000, poll_interval: int = 100):
        """
        Initialize expectation.

        Args:
            subject: The object to make assertions about
            timeout: Maximum time to retry in milliseconds (default: 5000ms)
            poll_interval: How often to check in milliseconds (default: 100ms)
        """
        self.subject = subject
        self.timeout = timeout
        self.poll_interval = poll_interval

    def _retry_until_true(
        self, condition: Callable[[], ExpectationResult], expectation_name: str
    ) -> ExpectationResult:
        """
        Retry a condition until it passes or timeout is reached.

        Args:
            condition: Function that returns ExpectationResult
            expectation_name: Name of expectation for error messages

        Returns:
            The passing ExpectationResult

        Raises:
            ExpectationTimeoutError: If condition never passes
        """
        start_time = time.time()
        last_result = None

        while (time.time() - start_time) * 1000 < self.timeout:
            result = condition()
            if result.passed:
                return result

            last_result = result
            time.sleep(self.poll_interval / 1000.0)

        # Timeout reached
        elapsed = (time.time() - start_time) * 1000
        error_msg = f"Expectation '{expectation_name}' failed after {elapsed:.0f}ms"
        if last_result:
            error_msg += f"\n{last_result.message}"
            if last_result.expected is not None:
                error_msg += f"\nExpected: {last_result.expected}"
            if last_result.actual is not None:
                error_msg += f"\nActual: {last_result.actual}"

        raise ExpectationTimeoutError(error_msg)


class ImageExpectation(Expectation):
    """
    Expectations for image-based automation.

    Example:
        expect(automator).to_have_image("button.png")
        expect(automator).not_to_have_image("loading.png")
    """

    def to_be_visible(self, image_path: str) -> "ImageExpectation":
        """
        Expect an image to be visible on screen.

        This replaces brittle code like:
            assert automator.find_image("button.png") is not None

        Args:
            image_path: Path to image that should be visible

        Returns:
            self for chaining

        Raises:
            ExpectationTimeoutError: If image not visible within timeout

        Example:
            expect(automator).to_be_visible("save_button.png")
        """

        def check():
            try:
                location = self.subject.find_image(image_path)
                if location:
                    return ExpectationResult(
                        passed=True, message=f"Image '{image_path}' is visible at {location}"
                    )
                else:
                    return ExpectationResult(
                        passed=False,
                        message=f"Image '{image_path}' is not visible",
                        expected="Image to be visible",
                        actual="Image not found",
                    )
            except Exception as e:
                return ExpectationResult(
                    passed=False,
                    message=f"Error checking image: {e}",
                    expected="Image to be visible",
                    actual=f"Error: {e}",
                )

        self._retry_until_true(check, f"image '{image_path}' to be visible")
        return self

    def to_have_image(self, image_path: str) -> "ImageExpectation":
        """Alias for to_be_visible for better readability."""
        return self.to_be_visible(image_path)

    def not_to_be_visible(self, image_path: str) -> "ImageExpectation":
        """
        Expect an image to NOT be visible (to have disappeared).

        Example:
            # Wait for loading spinner to disappear
            expect(automator).not_to_be_visible("loading.png")
        """

        def check():
            try:
                location = self.subject.find_image(image_path)
                if location is None:
                    return ExpectationResult(
                        passed=True, message=f"Image '{image_path}' is not visible (as expected)"
                    )
                else:
                    return ExpectationResult(
                        passed=False,
                        message=f"Image '{image_path}' is still visible at {location}",
                        expected="Image not to be visible",
                        actual=f"Image found at {location}",
                    )
            except Exception:
                # If find_image throws error, image is not visible
                return ExpectationResult(
                    passed=True, message=f"Image '{image_path}' is not visible (error finding it)"
                )

        self._retry_until_true(check, f"image '{image_path}' not to be visible")
        return self

    def not_to_have_image(self, image_path: str) -> "ImageExpectation":
        """Alias for not_to_be_visible."""
        return self.not_to_be_visible(image_path)

    def to_be_at_location(
        self, image_path: str, x: int, y: int, tolerance: int = 10
    ) -> "ImageExpectation":
        """
        Expect image to be at specific location.

        Args:
            image_path: Path to image
            x: Expected x coordinate
            y: Expected y coordinate
            tolerance: Allowed pixel difference (default: 10px)

        Returns:
            self for chaining
        """

        def check():
            try:
                location = self.subject.find_image(image_path)
                if location:
                    actual_x, actual_y = location
                    dx = abs(actual_x - x)
                    dy = abs(actual_y - y)

                    if dx <= tolerance and dy <= tolerance:
                        return ExpectationResult(
                            passed=True,
                            message=f"Image at expected location ({actual_x}, {actual_y})",
                        )
                    else:
                        return ExpectationResult(
                            passed=False,
                            message="Image at wrong location",
                            expected=f"({x}, {y}) ±{tolerance}px",
                            actual=f"({actual_x}, {actual_y})",
                        )
                else:
                    return ExpectationResult(
                        passed=False,
                        message=f"Image '{image_path}' not found",
                        expected=f"Image at ({x}, {y})",
                        actual="Image not visible",
                    )
            except Exception as e:
                return ExpectationResult(
                    passed=False,
                    message=f"Error: {e}",
                    expected=f"Image at ({x}, {y})",
                    actual=f"Error: {e}",
                )

        self._retry_until_true(check, f"image '{image_path}' to be at ({x}, {y})")
        return self


class WindowExpectation(Expectation):
    """
    Expectations for window-based automation.

    Example:
        expect(window_manager).to_have_window("Calculator")
        expect(window_manager).to_have_active_window("Notepad")
    """

    def to_have_window(self, title: str, partial: bool = True) -> "WindowExpectation":
        """
        Expect a window with given title to exist.

        Args:
            title: Window title to search for
            partial: Whether to do partial match (default: True)

        Returns:
            self for chaining
        """

        def check():
            try:
                windows = self.subject.get_windows()
                for window in windows:
                    window_title = getattr(window, "title", str(window))
                    if partial:
                        if title.lower() in window_title.lower():
                            return ExpectationResult(
                                passed=True, message=f"Found window: '{window_title}'"
                            )
                    else:
                        if title == window_title:
                            return ExpectationResult(
                                passed=True, message=f"Found window: '{window_title}'"
                            )

                return ExpectationResult(
                    passed=False,
                    message="Window not found",
                    expected=f"Window with title '{title}'",
                    actual=f"Available windows: {[getattr(w, 'title', str(w)) for w in windows]}",
                )
            except Exception as e:
                return ExpectationResult(passed=False, message=f"Error checking windows: {e}")

        self._retry_until_true(check, f"window '{title}' to exist")
        return self


class StateExpectation(Expectation):
    """
    Expectations for general state checks.

    Example:
        expect(lambda: app.get_status()).to_be("ready")
        expect(lambda: counter.value).to_be_greater_than(0)
    """

    def to_be(self, expected: Any) -> "StateExpectation":
        """Expect subject to equal expected value."""

        def check():
            actual = self.subject() if callable(self.subject) else self.subject
            passed = actual == expected
            return ExpectationResult(
                passed=passed,
                message=f"Value {'matches' if passed else 'does not match'} expected",
                expected=expected,
                actual=actual,
            )

        self._retry_until_true(check, f"value to be {expected}")
        return self

    def to_be_truthy(self) -> "StateExpectation":
        """Expect subject to be truthy."""

        def check():
            actual = self.subject() if callable(self.subject) else self.subject
            passed = bool(actual)
            return ExpectationResult(
                passed=passed,
                message=f"Value is {'truthy' if passed else 'falsy'}",
                expected="Truthy value",
                actual=actual,
            )

        self._retry_until_true(check, "value to be truthy")
        return self

    def to_be_greater_than(self, threshold: float) -> "StateExpectation":
        """Expect subject to be greater than threshold."""

        def check():
            actual = self.subject() if callable(self.subject) else self.subject
            passed = actual > threshold
            return ExpectationResult(
                passed=passed,
                message=f"Value is {'>' if passed else '<='} threshold",
                expected=f"> {threshold}",
                actual=actual,
            )

        self._retry_until_true(check, f"value to be > {threshold}")
        return self


def expect(subject: Any, timeout: int = 5000) -> Expectation:
    """
    Create an expectation for the given subject.

    This is the main entry point for the expectations API.

    Args:
        subject: The object to make assertions about
        timeout: Maximum time to retry in milliseconds (default: 5000ms)

    Returns:
        Appropriate Expectation subclass based on subject type

    Examples:
        # Image expectations
        expect(automator).to_have_image("button.png")
        expect(automator).not_to_have_image("loading.png")

        # Window expectations
        expect(window_manager).to_have_window("Calculator")

        # State expectations
        expect(lambda: app.status).to_be("ready")
        expect(lambda: counter.value).to_be_greater_than(0)
    """
    # Determine appropriate expectation type based on subject
    if hasattr(subject, "find_image"):
        return ImageExpectation(subject, timeout=timeout)
    elif hasattr(subject, "get_windows"):
        return WindowExpectation(subject, timeout=timeout)
    else:
        return StateExpectation(subject, timeout=timeout)


# Convenience function for quick checks
def wait_for(
    condition: Callable[[], bool], timeout: int = 5000, error_message: str = "Condition not met"
):
    """
    Wait for a condition to become true.

    This is a simpler alternative to expect() for custom conditions.

    Args:
        condition: Function that returns True when condition is met
        timeout: Maximum wait time in milliseconds
        error_message: Message to show if timeout is reached

    Raises:
        ExpectationTimeoutError: If condition not met within timeout

    Example:
        wait_for(
            lambda: os.path.exists("output.txt"),
            timeout=10000,
            error_message="Output file was not created"
        )
    """
    start_time = time.time()
    while (time.time() - start_time) * 1000 < timeout:
        if condition():
            return
        time.sleep(0.1)

    elapsed = (time.time() - start_time) * 1000
    raise ExpectationTimeoutError(f"{error_message} (waited {elapsed:.0f}ms)")
