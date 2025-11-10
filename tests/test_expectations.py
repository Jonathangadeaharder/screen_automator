"""
Comprehensive tests for the expectations module.

Tests the expect() function and all expectation types:
- ImageExpectation
- WindowExpectation
- StateExpectation
"""

import sys
import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

# Mock display-dependent modules before importing
sys.modules["pynput"] = MagicMock()
sys.modules["pynput.mouse"] = MagicMock()
sys.modules["pynput.keyboard"] = MagicMock()
sys.modules["pyautogui"] = MagicMock()
sys.modules["screeninfo"] = MagicMock()

from src.expectations import (
    expect,
    ExpectationError,
    ExpectationTimeoutError,
    ExpectationResult,
    Expectation,
    ImageExpectation,
    WindowExpectation,
    StateExpectation,
    wait_for,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_image_detector():
    """Create a mock ImageDetector with find_image method."""
    detector = Mock()
    detector.find_image = Mock(return_value=(100, 200, 50, 50))
    return detector


@pytest.fixture
def mock_image_detector_not_found():
    """Create a mock ImageDetector that doesn't find images."""
    detector = Mock()
    detector.find_image = Mock(return_value=None)
    return detector


@pytest.fixture
def mock_window_manager():
    """Create a mock WindowManager with get_windows method."""
    manager = Mock(spec=['get_windows'])
    window = Mock()
    window.title = "Test Window"
    manager.get_windows = Mock(return_value=[window])
    return manager


@pytest.fixture
def mock_window_manager_no_windows():
    """Create a mock WindowManager with no windows."""
    manager = Mock(spec=['get_windows'])
    manager.get_windows = Mock(return_value=[])
    return manager


# ============================================================================
# expect() Function Tests
# ============================================================================


def test_expect_returns_image_expectation_for_image_detector(mock_image_detector):
    """Test expect() returns ImageExpectation for objects with find_image()."""
    result = expect(mock_image_detector)

    assert isinstance(result, ImageExpectation)
    assert result.subject == mock_image_detector
    assert result.timeout == 5000


def test_expect_returns_window_expectation_for_window_manager(mock_window_manager):
    """Test expect() returns WindowExpectation for objects with get_windows()."""
    result = expect(mock_window_manager)

    assert isinstance(result, WindowExpectation)
    assert result.subject == mock_window_manager


def test_expect_returns_state_expectation_for_generic_subject():
    """Test expect() returns StateExpectation for generic objects."""
    # Use spec=[] to ensure no find_image or get_windows attributes
    generic_obj = Mock(spec=['some_other_method'])
    result = expect(generic_obj)

    assert isinstance(result, StateExpectation)
    assert result.subject == generic_obj


def test_expect_custom_timeout(mock_image_detector):
    """Test expect() accepts custom timeout."""
    result = expect(mock_image_detector, timeout=10000)

    assert result.timeout == 10000


def test_expect_type_detection_priority(mock_image_detector, mock_window_manager):
    """Test expect() prioritizes find_image over get_windows."""
    # Add get_windows to image detector
    mock_image_detector.get_windows = Mock()

    result = expect(mock_image_detector)

    # Should still be ImageExpectation (find_image takes priority)
    assert isinstance(result, ImageExpectation)


# ============================================================================
# ImageExpectation Tests
# ============================================================================


def test_image_expectation_to_be_visible_success(mock_image_detector):
    """Test to_be_visible() succeeds when image is found."""
    expectation = expect(mock_image_detector, timeout=1000)

    # Should not raise exception
    result = expectation.to_be_visible("test.png")

    assert result == expectation  # Returns self for chaining
    mock_image_detector.find_image.assert_called()


def test_image_expectation_to_be_visible_timeout(mock_image_detector_not_found):
    """Test to_be_visible() times out when image not found."""
    expectation = expect(mock_image_detector_not_found, timeout=500)

    with pytest.raises(ExpectationTimeoutError) as exc_info:
        expectation.to_be_visible("missing.png")

    assert "test.png" in str(exc_info.value) or "missing.png" in str(exc_info.value)
    assert "failed after" in str(exc_info.value)


def test_image_expectation_to_have_image_alias(mock_image_detector):
    """Test to_have_image() is an alias for to_be_visible()."""
    expectation = expect(mock_image_detector, timeout=1000)

    result = expectation.to_have_image("test.png")

    assert result == expectation
    mock_image_detector.find_image.assert_called()


def test_image_expectation_not_to_be_visible_success(mock_image_detector_not_found):
    """Test not_to_be_visible() succeeds when image is not found."""
    expectation = expect(mock_image_detector_not_found, timeout=1000)

    result = expectation.not_to_be_visible("test.png")

    assert result == expectation


def test_image_expectation_not_to_be_visible_timeout(mock_image_detector):
    """Test not_to_be_visible() times out when image is still visible."""
    expectation = expect(mock_image_detector, timeout=500)

    with pytest.raises(ExpectationTimeoutError):
        expectation.not_to_be_visible("visible.png")


def test_image_expectation_not_to_have_image_alias(mock_image_detector_not_found):
    """Test not_to_have_image() is an alias for not_to_be_visible()."""
    expectation = expect(mock_image_detector_not_found, timeout=1000)

    result = expectation.not_to_have_image("test.png")

    assert result == expectation


def test_image_expectation_to_be_at_location_success(mock_image_detector):
    """Test to_be_at_location() succeeds when image is at expected location."""
    mock_image_detector.find_image = Mock(return_value=(100, 200, 50, 50))
    expectation = expect(mock_image_detector, timeout=1000)

    result = expectation.to_be_at_location("test.png", x=100, y=200, tolerance=10)

    assert result == expectation


def test_image_expectation_to_be_at_location_within_tolerance(mock_image_detector):
    """Test to_be_at_location() accepts position within tolerance."""
    mock_image_detector.find_image = Mock(return_value=(105, 205, 50, 50))
    expectation = expect(mock_image_detector, timeout=1000)

    # Should succeed (within 10px tolerance)
    result = expectation.to_be_at_location("test.png", x=100, y=200, tolerance=10)

    assert result == expectation


def test_image_expectation_to_be_at_location_outside_tolerance(mock_image_detector):
    """Test to_be_at_location() fails when position outside tolerance."""
    mock_image_detector.find_image = Mock(return_value=(120, 220, 50, 50))
    expectation = expect(mock_image_detector, timeout=500)

    with pytest.raises(ExpectationTimeoutError):
        expectation.to_be_at_location("test.png", x=100, y=200, tolerance=10)


def test_image_expectation_retry_behavior(mock_image_detector_not_found):
    """Test ImageExpectation retries until timeout."""
    call_count = 0

    def side_effect(path):
        nonlocal call_count
        call_count += 1
        return None

    mock_image_detector_not_found.find_image.side_effect = side_effect
    expectation = expect(mock_image_detector_not_found, timeout=500)

    with pytest.raises(ExpectationTimeoutError):
        expectation.to_be_visible("test.png")

    # Should have retried multiple times (default poll_interval is 100ms)
    assert call_count >= 4


def test_image_expectation_custom_poll_interval():
    """Test ImageExpectation respects custom poll interval."""
    detector = Mock()
    detector.find_image = Mock(return_value=None)

    expectation = ImageExpectation(detector, timeout=500, poll_interval=200)

    start_time = time.time()
    with pytest.raises(ExpectationTimeoutError):
        expectation.to_be_visible("test.png")
    elapsed = (time.time() - start_time) * 1000

    # Should take at least 500ms
    assert elapsed >= 400  # Allow some margin


# ============================================================================
# WindowExpectation Tests
# ============================================================================


def test_window_expectation_to_have_window_success(mock_window_manager):
    """Test to_have_window() succeeds when window exists."""
    expectation = expect(mock_window_manager, timeout=1000)

    result = expectation.to_have_window("Test Window")

    assert result == expectation


def test_window_expectation_to_have_window_partial_match(mock_window_manager):
    """Test to_have_window() supports partial title matching."""
    expectation = expect(mock_window_manager, timeout=1000)

    # Should find "Test Window" with partial match "Test"
    result = expectation.to_have_window("Test", partial=True)

    assert result == expectation


def test_window_expectation_to_have_window_exact_match(mock_window_manager):
    """Test to_have_window() with exact matching."""
    expectation = expect(mock_window_manager, timeout=1000)

    result = expectation.to_have_window("Test Window", partial=False)

    assert result == expectation


def test_window_expectation_to_have_window_exact_match_fails(mock_window_manager):
    """Test to_have_window() exact match fails for partial title."""
    expectation = expect(mock_window_manager, timeout=500)

    with pytest.raises(ExpectationTimeoutError):
        expectation.to_have_window("Test", partial=False)


def test_window_expectation_to_have_window_not_found(mock_window_manager_no_windows):
    """Test to_have_window() times out when window not found."""
    expectation = expect(mock_window_manager_no_windows, timeout=500)

    with pytest.raises(ExpectationTimeoutError) as exc_info:
        expectation.to_have_window("Missing Window")

    assert "Missing Window" in str(exc_info.value)


def test_window_expectation_case_insensitive(mock_window_manager):
    """Test to_have_window() is case-insensitive for partial matches."""
    expectation = expect(mock_window_manager, timeout=1000)

    # Should find "Test Window" with lowercase
    result = expectation.to_have_window("test", partial=True)

    assert result == expectation


def test_window_expectation_retry_mechanism(mock_window_manager_no_windows):
    """Test WindowExpectation retries until timeout."""
    call_count = 0

    def side_effect():
        nonlocal call_count
        call_count += 1
        return []

    mock_window_manager_no_windows.get_windows.side_effect = side_effect
    expectation = expect(mock_window_manager_no_windows, timeout=500)

    with pytest.raises(ExpectationTimeoutError):
        expectation.to_have_window("Test")

    assert call_count >= 4


# ============================================================================
# StateExpectation Tests
# ============================================================================


def test_state_expectation_to_be_success():
    """Test to_be() succeeds when values match."""
    state = {"value": 42}
    expectation = expect(lambda: state["value"], timeout=1000)

    result = expectation.to_be(42)

    assert result == expectation


def test_state_expectation_to_be_failure():
    """Test to_be() times out when values don't match."""
    state = {"value": 42}
    expectation = expect(lambda: state["value"], timeout=500)

    with pytest.raises(ExpectationTimeoutError) as exc_info:
        expectation.to_be(99)

    error_msg = str(exc_info.value)
    assert "Expected: 99" in error_msg
    assert "Actual: 42" in error_msg


def test_state_expectation_to_be_with_non_callable():
    """Test to_be() works with non-callable subjects."""
    expectation = expect(42, timeout=1000)

    result = expectation.to_be(42)

    assert result == expectation


def test_state_expectation_to_be_truthy_success():
    """Test to_be_truthy() succeeds for truthy values."""
    expectation = expect(lambda: True, timeout=1000)

    result = expectation.to_be_truthy()

    assert result == expectation


def test_state_expectation_to_be_truthy_with_numbers():
    """Test to_be_truthy() works with non-zero numbers."""
    expectation = expect(lambda: 42, timeout=1000)

    result = expectation.to_be_truthy()

    assert result == expectation


def test_state_expectation_to_be_truthy_failure():
    """Test to_be_truthy() times out for falsy values."""
    expectation = expect(lambda: False, timeout=500)

    with pytest.raises(ExpectationTimeoutError):
        expectation.to_be_truthy()


def test_state_expectation_to_be_greater_than_success():
    """Test to_be_greater_than() succeeds when value is greater."""
    expectation = expect(lambda: 100, timeout=1000)

    result = expectation.to_be_greater_than(50)

    assert result == expectation


def test_state_expectation_to_be_greater_than_failure():
    """Test to_be_greater_than() times out when value is not greater."""
    expectation = expect(lambda: 10, timeout=500)

    with pytest.raises(ExpectationTimeoutError) as exc_info:
        expectation.to_be_greater_than(50)

    error_msg = str(exc_info.value)
    assert "> 50" in error_msg
    assert "Actual: 10" in error_msg


def test_state_expectation_eventual_success():
    """Test StateExpectation waits for value to change."""
    state = {"value": 0}

    def increment_after_delay():
        """Simulates async state change."""
        if state["value"] < 3:
            state["value"] += 1
        return state["value"]

    expectation = expect(increment_after_delay, timeout=2000)

    # Should eventually become 3
    result = expectation.to_be(3)

    assert result == expectation
    assert state["value"] == 3


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_expectation_timeout_error_message_includes_timeout(mock_image_detector_not_found):
    """Test ExpectationTimeoutError includes elapsed time."""
    expectation = expect(mock_image_detector_not_found, timeout=500)

    with pytest.raises(ExpectationTimeoutError) as exc_info:
        expectation.to_be_visible("test.png")

    error_msg = str(exc_info.value)
    assert "failed after" in error_msg
    assert "ms" in error_msg


def test_expectation_timeout_error_includes_context(mock_image_detector_not_found):
    """Test ExpectationTimeoutError includes helpful context."""
    expectation = expect(mock_image_detector_not_found, timeout=500)

    with pytest.raises(ExpectationTimeoutError) as exc_info:
        expectation.to_be_visible("missing.png")

    error_msg = str(exc_info.value)
    assert "to be visible" in error_msg or "missing.png" in error_msg


def test_expectation_result_structure():
    """Test ExpectationResult dataclass structure."""
    result = ExpectationResult(
        passed=True,
        message="Test passed",
        expected="expected value",
        actual="actual value",
    )

    assert result.passed is True
    assert result.message == "Test passed"
    assert result.expected == "expected value"
    assert result.actual == "actual value"


def test_expectation_error_inheritance():
    """Test ExpectationError inherits from AssertionError."""
    assert issubclass(ExpectationError, AssertionError)
    assert issubclass(ExpectationTimeoutError, ExpectationError)


# ============================================================================
# wait_for() Convenience Function Tests
# ============================================================================


def test_wait_for_success():
    """Test wait_for() succeeds when condition becomes true."""
    state = {"ready": False}

    # Set ready after a delay
    def set_ready():
        state["ready"] = True

    import threading
    timer = threading.Timer(0.2, set_ready)
    timer.start()

    # Should succeed without timeout
    wait_for(lambda: state["ready"], timeout=2000)

    assert state["ready"] is True
    timer.join()


def test_wait_for_timeout():
    """Test wait_for() raises timeout error when condition not met."""
    with pytest.raises(ExpectationTimeoutError) as exc_info:
        wait_for(lambda: False, timeout=500, error_message="Custom error message")

    error_msg = str(exc_info.value)
    assert "Custom error message" in error_msg
    assert "waited" in error_msg


def test_wait_for_immediate_success():
    """Test wait_for() returns immediately if condition already true."""
    start_time = time.time()

    wait_for(lambda: True, timeout=5000)

    elapsed = (time.time() - start_time) * 1000
    # Should be very fast (less than 100ms)
    assert elapsed < 100


def test_wait_for_custom_timeout():
    """Test wait_for() respects custom timeout."""
    start_time = time.time()

    with pytest.raises(ExpectationTimeoutError):
        wait_for(lambda: False, timeout=300)

    elapsed = (time.time() - start_time) * 1000
    # Should timeout around 300ms
    assert 250 < elapsed < 400


# ============================================================================
# Integration Tests
# ============================================================================


def test_chaining_multiple_expectations(mock_image_detector):
    """Test chaining multiple expectation calls."""
    mock_image_detector.find_image = Mock(return_value=(100, 200, 50, 50))

    expectation = expect(mock_image_detector, timeout=1000)

    # Chain multiple expectations
    result = (expectation
              .to_be_visible("test1.png")
              .to_be_visible("test2.png"))

    assert result == expectation
    assert mock_image_detector.find_image.call_count == 2


def test_complex_workflow_with_state_change():
    """Test complex workflow with eventual state changes."""
    app_state = {"status": "initializing", "count": 0}

    def update_state():
        """Simulates app state changes."""
        if app_state["count"] < 5:
            app_state["count"] += 1
            if app_state["count"] >= 3:
                app_state["status"] = "ready"
        return app_state["status"]

    expectation = expect(update_state, timeout=2000)

    # Should wait for status to become "ready"
    result = expectation.to_be("ready")

    assert result == expectation
    assert app_state["status"] == "ready"


def test_real_world_login_flow_simulation(mock_image_detector):
    """Test real-world login flow with expectations."""
    # Simulate login flow state
    login_state = {"button_visible": True, "logged_in": False}

    def check_logged_in():
        return login_state["logged_in"]

    # Expect login button to be visible
    mock_image_detector.find_image = Mock(return_value=(100, 200, 50, 50))
    expect(mock_image_detector, timeout=1000).to_be_visible("login_button.png")

    # Simulate clicking and logging in
    login_state["logged_in"] = True

    # Expect logged in state
    expect(check_logged_in, timeout=1000).to_be_truthy()

    assert login_state["logged_in"] is True


def test_combining_image_and_state_expectations(mock_image_detector):
    """Test combining different expectation types in workflow."""
    app_state = {"initialized": True}

    # Check image is visible
    mock_image_detector.find_image = Mock(return_value=(100, 200, 50, 50))
    expect(mock_image_detector, timeout=1000).to_be_visible("app.png")

    # Check state is correct
    expect(lambda: app_state["initialized"], timeout=1000).to_be_truthy()

    assert app_state["initialized"] is True
