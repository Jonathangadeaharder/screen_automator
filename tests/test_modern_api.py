"""
Comprehensive tests for the modern Screen Automator API.

Tests the ScreenAutomatorFramework class and create_framework() factory function.
"""

import sys
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path

# Mock display-dependent modules before importing
sys.modules["pynput"] = MagicMock()
sys.modules["pynput.mouse"] = MagicMock()
sys.modules["pynput.keyboard"] = MagicMock()

# Mock pyautogui
mock_pyautogui = MagicMock()
mock_pyautogui.FAILSAFE = True
sys.modules["pyautogui"] = mock_pyautogui

# Mock screeninfo to return a fake monitor
mock_monitor = MagicMock()
mock_monitor.x = 0
mock_monitor.y = 0
mock_monitor.width = 1920
mock_monitor.height = 1080

mock_screeninfo = MagicMock()
mock_screeninfo.get_monitors = MagicMock(return_value=[mock_monitor])
sys.modules["screeninfo"] = mock_screeninfo

from src.modern_api import ScreenAutomatorFramework, create_framework
from src.rule_manager import Rule
from src.action_executor import create_click_action
from src.expectations import ExpectationTimeoutError


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_rules_dir(tmp_path):
    """Create a temporary rules directory for testing."""
    rules_dir = tmp_path / "test_rules"
    rules_dir.mkdir()
    return str(rules_dir)


@pytest.fixture
def framework(temp_rules_dir):
    """Create a ScreenAutomatorFramework instance for testing."""
    return ScreenAutomatorFramework(rules_dir=temp_rules_dir, timeout=5000)


@pytest.fixture
def mock_image_detector():
    """Create a mock ImageDetector."""
    detector = Mock()
    detector.find_image = Mock(return_value=(100, 200, 50, 50))
    detector.find_image_on_screen = Mock(return_value=(100, 200, 50, 50))
    return detector


@pytest.fixture
def sample_rule(temp_rules_dir):
    """Create a sample rule for testing."""
    actions = [create_click_action(100, 200)]
    rule = Rule(
        id="test-rule-001",
        name="Test Rule",
        image_path="test_image.png",
        actions=actions,
        enabled=True,
        description="Test rule for unit tests",
    )
    return rule


# ============================================================================
# Factory Function Tests
# ============================================================================


def test_create_framework_default_params():
    """Test create_framework() with default parameters."""
    framework = create_framework()

    assert framework is not None
    assert isinstance(framework, ScreenAutomatorFramework)
    assert framework.timeout == 30000
    assert framework.automator is not None


def test_create_framework_custom_params(temp_rules_dir):
    """Test create_framework() with custom parameters."""
    framework = create_framework(rules_dir=temp_rules_dir, timeout=10000)

    assert framework.timeout == 10000
    assert framework.automator.rule_manager.rules_dir == temp_rules_dir


# ============================================================================
# Initialization Tests
# ============================================================================


def test_framework_initialization(temp_rules_dir):
    """Test ScreenAutomatorFramework initialization."""
    framework = ScreenAutomatorFramework(rules_dir=temp_rules_dir, timeout=15000)

    assert framework.automator is not None
    assert framework.smart is not None
    assert framework.waiter is not None
    assert framework.timeout == 15000


def test_framework_default_timeout():
    """Test framework with default timeout."""
    framework = ScreenAutomatorFramework()

    assert framework.timeout == 30000


# ============================================================================
# Monitoring Control Tests
# ============================================================================


def test_start_monitoring(framework):
    """Test start_monitoring() delegates to automator."""
    framework.start_monitoring()

    assert framework.is_running is True


def test_stop_monitoring(framework):
    """Test stop_monitoring() delegates to automator."""
    framework.start_monitoring()
    framework.stop_monitoring()

    assert framework.is_running is False


def test_is_running_property(framework):
    """Test is_running property reflects monitoring state."""
    assert framework.is_running is False

    framework.start_monitoring()
    assert framework.is_running is True

    framework.stop_monitoring()
    assert framework.is_running is False


# ============================================================================
# Rule Management Tests
# ============================================================================


def test_add_rule(framework, sample_rule):
    """Test add_rule() adds rule to manager."""
    framework.add_rule(sample_rule)

    rules = framework.get_rules()
    assert len(rules) == 1
    assert rules[0].id == sample_rule.id


def test_get_rules_empty(framework):
    """Test get_rules() returns empty list initially."""
    rules = framework.get_rules()

    assert rules == []


def test_get_rules_multiple(framework, sample_rule):
    """Test get_rules() returns all rules."""
    # Add first rule
    framework.add_rule(sample_rule)

    # Add second rule
    rule2 = Rule(
        id="test-rule-002",
        name="Test Rule 2",
        image_path="test2.png",
        actions=[],
        enabled=True,
    )
    framework.add_rule(rule2)

    rules = framework.get_rules()
    assert len(rules) == 2


def test_enable_rule(framework, sample_rule):
    """Test enable_rule() enables a disabled rule."""
    # Add rule and disable it
    framework.add_rule(sample_rule)
    sample_rule.enabled = False
    framework.automator.rule_manager.save_rule(sample_rule)

    # Enable it
    framework.enable_rule(sample_rule.id)

    # Verify it's enabled
    rule = framework.automator.rule_manager.get_rule(sample_rule.id)
    assert rule.enabled is True


def test_disable_rule(framework, sample_rule):
    """Test disable_rule() disables an enabled rule."""
    # Add rule (enabled by default)
    framework.add_rule(sample_rule)

    # Disable it
    framework.disable_rule(sample_rule.id)

    # Verify it's disabled
    rule = framework.automator.rule_manager.get_rule(sample_rule.id)
    assert rule.enabled is False


def test_enable_nonexistent_rule(framework):
    """Test enable_rule() handles non-existent rule gracefully."""
    # Should not raise error
    framework.enable_rule("nonexistent-id")


def test_disable_nonexistent_rule(framework):
    """Test disable_rule() handles non-existent rule gracefully."""
    # Should not raise error
    framework.disable_rule("nonexistent-id")


# ============================================================================
# Image Operations Tests
# ============================================================================


@patch("src.modern_api.AutoWaiter")
def test_wait_for_image_default_params(mock_waiter_class, framework):
    """Test wait_for_image() with default parameters."""
    mock_waiter = Mock()
    mock_waiter.wait_for_stable_image = Mock(return_value=(100, 200))
    framework.waiter = mock_waiter

    result = framework.wait_for_image("test.png")

    mock_waiter.wait_for_stable_image.assert_called_once()
    assert result == (100, 200)


@patch("src.modern_api.AutoWaiter")
def test_wait_for_image_custom_timeout(mock_waiter_class, framework):
    """Test wait_for_image() with custom timeout."""
    mock_waiter = Mock()
    mock_waiter.wait_for_stable_image = Mock(return_value=(100, 200))
    framework.waiter = mock_waiter

    framework.wait_for_image("test.png", timeout=10000)

    call_args = mock_waiter.wait_for_stable_image.call_args
    assert call_args[1]["timeout"] == 10000


@patch("src.modern_api.AutoWaiter")
def test_wait_for_image_no_stability(mock_waiter_class, framework):
    """Test wait_for_image() with ensure_stable=False."""
    mock_waiter = Mock()
    mock_waiter.wait_for_image = Mock(return_value=(100, 200))
    framework.waiter = mock_waiter

    framework.wait_for_image("test.png", ensure_stable=False)

    mock_waiter.wait_for_image.assert_called_once()
    mock_waiter.wait_for_stable_image.assert_not_called()


@patch("src.modern_api.SmartAutomator")
def test_click_image_default_params(mock_smart_class, framework):
    """Test click_image() with default parameters."""
    mock_smart = Mock()
    framework.smart = mock_smart

    framework.click_image("button.png")

    mock_smart.click_image.assert_called_once_with(
        "button.png", timeout=None, ensure_stable=True
    )


@patch("src.modern_api.SmartAutomator")
def test_click_image_custom_params(mock_smart_class, framework):
    """Test click_image() with custom parameters."""
    mock_smart = Mock()
    framework.smart = mock_smart

    framework.click_image("button.png", timeout=8000, ensure_stable=False)

    mock_smart.click_image.assert_called_once_with(
        "button.png", timeout=8000, ensure_stable=False
    )


@patch("src.modern_api.SmartAutomator")
def test_wait_for_image_to_disappear(mock_smart_class, framework):
    """Test wait_for_image_to_disappear() delegates to smart automator."""
    mock_smart = Mock()
    framework.smart = mock_smart

    framework.wait_for_image_to_disappear("loading.png", timeout=5000)

    mock_smart.wait_for_image_to_disappear.assert_called_once_with(
        "loading.png", timeout=5000
    )


# ============================================================================
# Expectations API Tests
# ============================================================================


def test_expect_image_found(framework, mock_image_detector):
    """Test expect_image() when image is found."""
    framework.automator.image_detector = mock_image_detector

    # Should not raise exception
    framework.expect_image("test.png")

    mock_image_detector.find_image.assert_called()


def test_expect_image_not_found(framework, mock_image_detector):
    """Test expect_image() when image is not found."""
    mock_image_detector.find_image = Mock(return_value=None)
    framework.automator.image_detector = mock_image_detector

    # Should raise ExpectationTimeoutError
    with pytest.raises(ExpectationTimeoutError):
        framework.expect_image("nonexistent.png", timeout=500)


def test_expect_no_image_not_present(framework, mock_image_detector):
    """Test expect_no_image() when image is not present."""
    mock_image_detector.find_image = Mock(return_value=None)
    framework.automator.image_detector = mock_image_detector

    # Should not raise exception
    framework.expect_no_image("test.png")


def test_expect_no_image_still_present(framework, mock_image_detector):
    """Test expect_no_image() when image is still present."""
    framework.automator.image_detector = mock_image_detector

    # Should raise ExpectationTimeoutError
    with pytest.raises(ExpectationTimeoutError):
        framework.expect_no_image("present.png", timeout=500)


# ============================================================================
# Callbacks Tests
# ============================================================================


def test_on_rule_triggered_callback(framework):
    """Test on_rule_triggered() sets callback."""
    callback = Mock()

    framework.on_rule_triggered(callback)

    assert framework.automator.on_rule_triggered == callback


def test_on_action_executed_callback(framework):
    """Test on_action_executed() sets callback."""
    callback = Mock()

    framework.on_action_executed(callback)

    assert framework.automator.on_action_executed == callback


def test_on_error_callback(framework):
    """Test on_error() sets callback."""
    callback = Mock()

    framework.on_error(callback)

    assert framework.automator.on_error == callback


def test_on_rule_disabled_callback(framework):
    """Test on_rule_disabled() sets callback."""
    callback = Mock()

    framework.on_rule_disabled(callback)

    assert framework.automator.on_rule_disabled == callback


# ============================================================================
# Configuration Tests
# ============================================================================


def test_set_check_interval(framework):
    """Test set_check_interval() updates automator."""
    framework.set_check_interval(15.0)

    assert framework.automator.check_interval == 15.0


def test_set_timeout(framework):
    """Test set_timeout() updates both framework and waiter."""
    framework.set_timeout(20000)

    assert framework.timeout == 20000
    assert framework.waiter.timeout == 20000


def test_set_mouse_idle_threshold(framework):
    """Test set_mouse_idle_threshold() updates automator."""
    framework.set_mouse_idle_threshold(10.0)

    assert framework.automator.mouse_idle_threshold == 10.0


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_workflow_with_rules(temp_rules_dir, sample_rule):
    """Test a complete workflow: create framework, add rules, manage them."""
    # Create framework
    framework = create_framework(rules_dir=temp_rules_dir, timeout=10000)

    # Add rule
    framework.add_rule(sample_rule)

    # Get rules
    rules = framework.get_rules()
    assert len(rules) == 1
    assert rules[0].enabled is True

    # Disable rule
    framework.disable_rule(sample_rule.id)
    rule = framework.automator.rule_manager.get_rule(sample_rule.id)
    assert rule.enabled is False

    # Enable rule
    framework.enable_rule(sample_rule.id)
    rule = framework.automator.rule_manager.get_rule(sample_rule.id)
    assert rule.enabled is True


def test_monitoring_lifecycle(framework):
    """Test complete monitoring start/stop lifecycle."""
    # Initially not running
    assert framework.is_running is False

    # Start monitoring
    framework.start_monitoring()
    assert framework.is_running is True

    # Stop monitoring
    framework.stop_monitoring()
    assert framework.is_running is False

    # Can restart
    framework.start_monitoring()
    assert framework.is_running is True


def test_configuration_chain(framework):
    """Test setting multiple configuration options."""
    framework.set_check_interval(20.0)
    framework.set_timeout(15000)
    framework.set_mouse_idle_threshold(8.0)

    assert framework.automator.check_interval == 20.0
    assert framework.timeout == 15000
    assert framework.waiter.timeout == 15000
    assert framework.automator.mouse_idle_threshold == 8.0
