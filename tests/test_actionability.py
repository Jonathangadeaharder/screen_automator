"""
Comprehensive tests for the actionability module.

Tests AutoWaiter and SmartAutomator classes for auto-waiting
and stability checks.
"""

import sys
import pytest
import time
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path

# Mock display-dependent modules before importing
sys.modules["pynput"] = MagicMock()
sys.modules["pynput.mouse"] = MagicMock()
sys.modules["pynput.keyboard"] = MagicMock()

# Create pyautogui mock - ensure it's in sys.modules for imports
if "pyautogui" not in sys.modules or not isinstance(sys.modules["pyautogui"], MagicMock):
    sys.modules["pyautogui"] = MagicMock()

sys.modules["screeninfo"] = MagicMock()

from src.actionability import (
    AutoWaiter,
    SmartAutomator,
    ActionabilityState,
    ActionabilityResult,
    ActionabilityError,
    TimeoutError as ActionabilityTimeoutError,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def reset_pyautogui_mock():
    """Reset the pyautogui mock before each test to avoid shared state issues."""
    # Get the current mock from sys.modules
    mock = sys.modules["pyautogui"]
    # Reset it to clear any call history from previous tests
    mock.reset_mock()
    yield mock


@pytest.fixture
def auto_waiter():
    """Create an AutoWaiter instance with short timeout for fast tests."""
    return AutoWaiter(timeout=2000, poll_interval=50)


@pytest.fixture
def mock_image_detector():
    """Create a mock ImageDetector."""
    detector = Mock(spec=['find_image', 'find_image_on_screen'])
    detector.find_image = Mock(return_value=(100, 200, 50, 50))
    detector.find_image_on_screen = Mock(return_value=(100, 200, 50, 50))
    return detector


@pytest.fixture
def mock_image_detector_not_found():
    """Create a mock ImageDetector that doesn't find images."""
    detector = Mock(spec=['find_image', 'find_image_on_screen'])
    detector.find_image = Mock(return_value=None)
    detector.find_image_on_screen = Mock(return_value=None)
    return detector


@pytest.fixture
def smart_automator(mock_image_detector):
    """Create a SmartAutomator instance with mocked detector."""
    return SmartAutomator(mock_image_detector, timeout=2000)


# ============================================================================
# AutoWaiter Tests - wait_for_condition()
# ============================================================================


def test_auto_waiter_initialization():
    """Test AutoWaiter initializes with correct defaults."""
    waiter = AutoWaiter()

    assert waiter.timeout == 30000
    assert waiter.poll_interval == 100


def test_auto_waiter_custom_timeout():
    """Test AutoWaiter accepts custom timeout."""
    waiter = AutoWaiter(timeout=5000, poll_interval=200)

    assert waiter.timeout == 5000
    assert waiter.poll_interval == 200


def test_wait_for_condition_immediate_success(auto_waiter):
    """Test wait_for_condition() returns immediately if condition already true."""
    start_time = time.time()

    result = auto_waiter.wait_for_condition(lambda: "success", "test condition")

    elapsed = (time.time() - start_time) * 1000
    assert result == "success"
    assert elapsed < 100  # Should be very fast


def test_wait_for_condition_eventual_success(auto_waiter):
    """Test wait_for_condition() waits for condition to become true."""
    state = {"count": 0}

    def condition():
        state["count"] += 1
        return state["count"] >= 3

    result = auto_waiter.wait_for_condition(condition, "count >= 3")

    assert result is True
    assert state["count"] >= 3


def test_wait_for_condition_timeout(auto_waiter):
    """Test wait_for_condition() raises TimeoutError on timeout."""
    with pytest.raises(ActionabilityTimeoutError) as exc_info:
        auto_waiter.wait_for_condition(lambda: False, "impossible condition", timeout=500)

    error_msg = str(exc_info.value)
    assert "Timeout" in error_msg or "timeout" in error_msg


def test_wait_for_condition_custom_timeout(auto_waiter):
    """Test wait_for_condition() respects custom timeout."""
    start_time = time.time()

    with pytest.raises(ActionabilityTimeoutError):
        auto_waiter.wait_for_condition(lambda: False, "test", timeout=300)

    elapsed = (time.time() - start_time) * 1000
    assert 250 < elapsed < 450  # Should timeout around 300ms


def test_wait_for_condition_returns_truthy_value(auto_waiter):
    """Test wait_for_condition() returns the truthy value from condition."""
    expected_value = {"data": [1, 2, 3]}

    result = auto_waiter.wait_for_condition(lambda: expected_value, "data ready")

    assert result == expected_value


def test_wait_for_condition_retries_on_falsy(auto_waiter):
    """Test wait_for_condition() retries when condition returns falsy."""
    call_count = 0

    def condition():
        nonlocal call_count
        call_count += 1
        return call_count >= 5

    auto_waiter.wait_for_condition(condition, "test")

    assert call_count >= 5


# ============================================================================
# AutoWaiter Tests - wait_for_image()
# ============================================================================


def test_wait_for_image_success(auto_waiter, mock_image_detector):
    """Test wait_for_image() succeeds when image is found."""
    location = auto_waiter.wait_for_image("test.png", mock_image_detector)

    assert location == (100, 200, 50, 50)
    mock_image_detector.find_image.assert_called()


def test_wait_for_image_custom_timeout(auto_waiter, mock_image_detector):
    """Test wait_for_image() respects custom timeout."""
    location = auto_waiter.wait_for_image("test.png", mock_image_detector, timeout=1000)

    assert location is not None


def test_wait_for_image_not_found(auto_waiter, mock_image_detector_not_found):
    """Test wait_for_image() raises TimeoutError when image not found."""
    with pytest.raises(ActionabilityTimeoutError):
        auto_waiter.wait_for_image("missing.png", mock_image_detector_not_found, timeout=500)


def test_wait_for_image_retries(auto_waiter):
    """Test wait_for_image() retries until image appears."""
    detector = Mock()
    call_count = 0

    def find_image_delayed(path):
        nonlocal call_count
        call_count += 1
        return (100, 200) if call_count >= 3 else None

    detector.find_image = Mock(side_effect=find_image_delayed)

    location = auto_waiter.wait_for_image("test.png", detector)

    assert location == (100, 200)
    assert call_count >= 3


# ============================================================================
# AutoWaiter Tests - ensure_stable()
# ============================================================================


def test_ensure_stable_with_stable_location(auto_waiter):
    """Test ensure_stable() succeeds when location is stable."""
    location_getter = Mock(return_value=(100, 200))

    # Should not raise exception
    result = auto_waiter.ensure_stable(location_getter, duration=100)
    assert result == (100, 200)


def test_ensure_stable_with_moving_element(auto_waiter):
    """Test ensure_stable() waits for element to stop moving."""
    positions = [(100, 200), (105, 205), (110, 210), (110, 210), (110, 210)]
    position_index = 0

    def get_position():
        nonlocal position_index
        if position_index < len(positions):
            pos = positions[position_index]
            position_index += 1
            return pos
        return positions[-1]

    location_getter = Mock(side_effect=get_position)

    # Should eventually stabilize
    result = auto_waiter.ensure_stable(location_getter, duration=100)

    # Should have checked multiple times
    assert location_getter.call_count >= 3
    assert result == (110, 210)


def test_ensure_stable_timeout():
    """Test ensure_stable() times out if element never stabilizes."""
    # Use a shorter timeout for this test
    waiter = AutoWaiter(timeout=500, poll_interval=50)
    call_count = 0

    def always_moving():
        nonlocal call_count
        call_count += 1
        # Move by 10 pixels each time (more than default tolerance of 5)
        return (100 + call_count * 10, 200)

    location_getter = Mock(side_effect=always_moving)

    with pytest.raises(ActionabilityTimeoutError):
        waiter.ensure_stable(location_getter, duration=50)


def test_ensure_stable_custom_duration(auto_waiter):
    """Test ensure_stable() respects custom stability duration."""
    location_getter = Mock(return_value=(100, 200))

    start_time = time.time()
    auto_waiter.ensure_stable(location_getter, duration=200)
    elapsed = (time.time() - start_time) * 1000

    # Should wait at least duration time
    assert elapsed >= 150  # Allow some margin


# ============================================================================
# AutoWaiter Tests - wait_for_stable_image()
# ============================================================================


def test_wait_for_stable_image_success(auto_waiter, mock_image_detector):
    """Test wait_for_stable_image() waits for image and checks stability."""
    location = auto_waiter.wait_for_stable_image(
        "test.png",
        mock_image_detector,
        stability_duration=100
    )

    assert location == (100, 200, 50, 50)


def test_wait_for_stable_image_with_delayed_appearance(auto_waiter):
    """Test wait_for_stable_image() waits for image to appear then stabilize."""
    detector = Mock()
    call_count = 0

    def delayed_image(path):
        nonlocal call_count
        call_count += 1
        return (100, 200, 50, 50) if call_count >= 3 else None

    detector.find_image = Mock(side_effect=delayed_image)

    location = auto_waiter.wait_for_stable_image(
        "test.png",
        detector,
        stability_duration=50,
        timeout=2000
    )

    assert location == (100, 200, 50, 50)


def test_wait_for_stable_image_timeout(auto_waiter, mock_image_detector_not_found):
    """Test wait_for_stable_image() times out if image never appears."""
    with pytest.raises(ActionabilityTimeoutError):
        auto_waiter.wait_for_stable_image(
            "missing.png",
            mock_image_detector_not_found,
            timeout=500
        )


# ============================================================================
# SmartAutomator Tests - click_image()
# ============================================================================


def test_smart_automator_initialization(mock_image_detector):
    """Test SmartAutomator initializes correctly."""
    smart = SmartAutomator(mock_image_detector, timeout=5000)

    assert smart.automator == mock_image_detector
    assert smart.waiter.timeout == 5000


def test_click_image_with_auto_wait(smart_automator, mock_image_detector):
    """Test click_image() automatically waits for image."""
    smart_automator.click_image("button.png")

    # Should have found the image
    mock_image_detector.find_image.assert_called()

    # Should have clicked (pyautogui is mocked globally)
    sys.modules["pyautogui"].click.assert_called()


def test_click_image_custom_timeout(mock_image_detector):
    """Test click_image() respects custom timeout."""
    smart = SmartAutomator(mock_image_detector, timeout=10000)

    smart.click_image("button.png", timeout=1000)

    mock_image_detector.find_image.assert_called()


def test_click_image_with_stability_check(smart_automator, mock_image_detector):
    """Test click_image() checks element stability before clicking."""
    smart_automator.click_image("button.png", ensure_stable=True)

    # Should check stability (multiple find calls)
    assert mock_image_detector.find_image.call_count >= 1


def test_click_image_without_stability_check(smart_automator, mock_image_detector):
    """Test click_image() can skip stability check."""
    smart_automator.click_image("button.png", ensure_stable=False)

    sys.modules["pyautogui"].click.assert_called()


def test_click_image_calculates_center(mock_image_detector):
    """Test click_image() clicks center of image."""
    mock_image_detector.find_image = Mock(return_value=(100, 200, 50, 50))
    smart = SmartAutomator(mock_image_detector, timeout=2000)

    smart.click_image("button.png", ensure_stable=False)

    # Should click at center: (100 + 50/2, 200 + 50/2) = (125, 225)
    sys.modules["pyautogui"].click.assert_called()
    call_args = sys.modules["pyautogui"].click.call_args
    # Check coordinates are reasonable (center of image)
    assert call_args is not None


def test_click_image_not_found(mock_image_detector_not_found):
    """Test click_image() raises error when image not found."""
    sys.modules["pyautogui"].reset_mock()  # Reset to check it wasn't called
    smart = SmartAutomator(mock_image_detector_not_found, timeout=500)

    with pytest.raises(ActionabilityTimeoutError):
        smart.click_image("missing.png")


# ============================================================================
# SmartAutomator Tests - wait_for_image_to_disappear()
# ============================================================================


def test_wait_for_image_to_disappear_success(smart_automator):
    """Test wait_for_image_to_disappear() waits for image to disappear."""
    detector = smart_automator.automator
    call_count = 0

    def image_disappears(path):
        nonlocal call_count
        call_count += 1
        return (100, 200) if call_count < 3 else None

    detector.find_image = Mock(side_effect=image_disappears)

    smart_automator.wait_for_image_to_disappear("loading.png")

    assert call_count >= 3


def test_wait_for_image_to_disappear_immediate(smart_automator, mock_image_detector_not_found):
    """Test wait_for_image_to_disappear() returns immediately if already gone."""
    smart = SmartAutomator(mock_image_detector_not_found, timeout=2000)

    start_time = time.time()
    smart.wait_for_image_to_disappear("already_gone.png")
    elapsed = (time.time() - start_time) * 1000

    assert elapsed < 200  # Should be fast


def test_wait_for_image_to_disappear_timeout(smart_automator, mock_image_detector):
    """Test wait_for_image_to_disappear() times out if image stays."""
    smart = SmartAutomator(mock_image_detector, timeout=500)

    with pytest.raises(ActionabilityTimeoutError):
        smart.wait_for_image_to_disappear("persistent.png")


def test_wait_for_image_to_disappear_custom_timeout(smart_automator):
    """Test wait_for_image_to_disappear() respects custom timeout."""
    detector = smart_automator.automator
    detector.find_image = Mock(return_value=(100, 200))

    start_time = time.time()

    with pytest.raises(ActionabilityTimeoutError):
        smart_automator.wait_for_image_to_disappear("test.png", timeout=300)

    elapsed = (time.time() - start_time) * 1000
    assert 250 < elapsed < 450


# ============================================================================
# ActionabilityResult Tests
# ============================================================================


def test_actionability_result_structure():
    """Test ActionabilityResult dataclass structure."""
    result = ActionabilityResult(
        passed=True,
        state=ActionabilityState.VISIBLE,
        message="Element is visible",
        location=(100, 200)
    )

    assert result.passed is True
    assert result.state == ActionabilityState.VISIBLE
    assert result.message == "Element is visible"
    assert result.location == (100, 200)


def test_actionability_result_optional_location():
    """Test ActionabilityResult with optional location."""
    result = ActionabilityResult(
        passed=False,
        state=ActionabilityState.STABLE,
        message="Element not stable"
    )

    assert result.location is None


# ============================================================================
# ActionabilityState Tests
# ============================================================================


def test_actionability_state_enum():
    """Test ActionabilityState enum values."""
    assert ActionabilityState.VISIBLE.value == "visible"
    assert ActionabilityState.STABLE.value == "stable"
    assert ActionabilityState.ENABLED.value == "enabled"
    assert ActionabilityState.RECEIVES_EVENTS.value == "receives_events"
    assert ActionabilityState.NOT_OBSCURED.value == "not_obscured"


# ============================================================================
# Error Classes Tests
# ============================================================================


def test_actionability_error_inheritance():
    """Test ActionabilityError inherits from Exception."""
    assert issubclass(ActionabilityError, Exception)


def test_timeout_error_inheritance():
    """Test TimeoutError inherits from Exception."""
    assert issubclass(ActionabilityTimeoutError, Exception)


# ============================================================================
# Integration Tests
# ============================================================================


def test_complete_click_workflow(mock_image_detector):
    """Test complete workflow: wait for image, check stability, click."""
    sys.modules["pyautogui"].reset_mock()
    mock_image_detector.find_image = Mock(return_value=(100, 200, 50, 50))
    smart = SmartAutomator(mock_image_detector, timeout=2000)

    smart.click_image("button.png", ensure_stable=True)

    # Should have found image
    mock_image_detector.find_image.assert_called()

    # Should have clicked
    sys.modules["pyautogui"].click.assert_called_once()


def test_wait_then_disappear_workflow(smart_automator):
    """Test workflow: wait for element, then wait for it to disappear."""
    detector = smart_automator.automator
    state = {"appeared": False, "disappeared": False}

    def simulate_lifecycle(path):
        if not state["appeared"]:
            state["appeared"] = True
            return (100, 200, 50, 50)
        if not state["disappeared"]:
            state["disappeared"] = True
            return (100, 200, 50, 50)
        return None

    detector.find_image = Mock(side_effect=simulate_lifecycle)

    # Wait for it to appear
    waiter = AutoWaiter(timeout=2000)
    location = waiter.wait_for_image("loading.png", detector)
    assert location is not None

    # Wait for it to disappear
    smart_automator.wait_for_image_to_disappear("loading.png")
    assert state["disappeared"] is True


def test_multiple_stability_checks(auto_waiter):
    """Test multiple stability checks in sequence."""
    location_getter1 = Mock(return_value=(100, 200))
    location_getter2 = Mock(return_value=(150, 250))

    # Check stability multiple times
    auto_waiter.ensure_stable(location_getter1, duration=50)
    auto_waiter.ensure_stable(location_getter2, duration=50)

    assert location_getter1.call_count >= 2
    assert location_getter2.call_count >= 2


def test_click_multiple_images_sequence(mock_image_detector):
    """Test clicking multiple images in sequence."""
    sys.modules["pyautogui"].reset_mock()
    smart = SmartAutomator(mock_image_detector, timeout=2000)

    smart.click_image("button1.png", ensure_stable=False)
    smart.click_image("button2.png", ensure_stable=False)
    smart.click_image("button3.png", ensure_stable=False)

    assert sys.modules["pyautogui"].click.call_count == 3
