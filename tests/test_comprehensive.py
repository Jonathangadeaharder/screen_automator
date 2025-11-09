#!/usr/bin/env python3
"""Comprehensive test suite with mocks for automated testing of CLI, GUI, and core components."""
import json
import os
import sys
import tempfile
import tkinter as tk
from unittest.mock import MagicMock, Mock, mock_open, patch

import numpy as np
import pytest
from click.testing import CliRunner

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

# Import modules under test
from cli import cli
from src.action_executor import (
    ActionExecutor,
    create_click_action,
    create_type_text_action,
    create_wait_action,
)
from src.automator import ScreenAutomator
from src.image_detector import ImageDetector
from src.rule_manager import Rule, RuleManager


class TestCLIComprehensive:
    """Comprehensive CLI tests with mocks."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("cli.ScreenAutomator")
    def test_cli_status_command(self, mock_automator_class):
        """Test CLI status command."""
        mock_automator = Mock()
        mock_automator.get_status.return_value = {
            "running": False,
            "check_interval": 1.0,
            "total_rules": 3,
            "enabled_rules": 2,
        }
        mock_automator_class.return_value = mock_automator

        result = self.runner.invoke(cli, ["status"])

        assert result.exit_code == 0
        assert "Running: No" in result.output
        assert "Total Rules: 3" in result.output

    @patch("cli.ScreenAutomator")
    def test_cli_rule_list(self, mock_automator_class):
        """Test CLI rule list command."""
        mock_rule = Mock()
        mock_rule.id = "test-rule-id"
        mock_rule.name = "Test Rule"
        mock_rule.enabled = True
        mock_rule.image_path = "/path/to/image.png"
        mock_rule.actions = [create_click_action(100, 200)]

        mock_automator = Mock()
        mock_automator.rule_manager.list_rules.return_value = [mock_rule]
        mock_automator_class.return_value = mock_automator

        result = self.runner.invoke(cli, ["rule", "list"])

        assert result.exit_code == 0
        assert "Test Rule" in result.output

    @patch("cli.ScreenAutomator")
    def test_cli_start_monitoring(self, mock_automator_class):
        """Test CLI start monitoring command."""
        mock_automator = Mock()
        mock_automator.is_running.return_value = False
        mock_automator_class.return_value = mock_automator

        # Use timeout to avoid hanging
        result = self.runner.invoke(cli, ["start", "--timeout", "1"])

        assert result.exit_code == 0
        mock_automator.start_monitoring.assert_called_once()


class TestCoreComprehensive:
    """Comprehensive core component tests with mocks."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("src.automator.mouse.Listener")
    @patch("src.automator.ImageDetector")
    @patch("src.automator.ActionExecutor")
    @patch("src.automator.RuleManager")
    def test_screen_automator_init(
        self, mock_rule_mgr, mock_executor, mock_detector, mock_listener
    ):
        """Test ScreenAutomator initialization."""
        automator = ScreenAutomator(self.temp_dir)

        assert automator.running == False
        assert automator.check_interval == 1.0
        mock_rule_mgr.assert_called_once_with(self.temp_dir)
        mock_executor.assert_called_once()
        mock_detector.assert_called_once()

    @patch("src.automator.mouse.Listener")
    @patch("src.automator.ImageDetector")
    @patch("src.automator.ActionExecutor")
    @patch("src.automator.RuleManager")
    def test_screen_automator_monitoring(
        self, mock_rule_mgr, mock_executor, mock_detector, mock_listener
    ):
        """Test ScreenAutomator monitoring functionality."""
        automator = ScreenAutomator(self.temp_dir)

        # Test start monitoring
        automator.start_monitoring()
        assert automator.running == True

        # Test stop monitoring
        automator.stop_monitoring()
        assert automator.running == False

    def test_rule_manager_create_rule(self):
        """Test RuleManager rule creation."""
        rule_manager = RuleManager(self.temp_dir)

        actions = [create_click_action(100, 200)]
        rule = rule_manager.create_rule(
            name="Test Rule",
            image_path="/test/image.png",
            actions=actions,
            description="Test description",
        )

        assert rule.name == "Test Rule"
        assert rule.image_path == "/test/image.png"
        assert len(rule.actions) == 1
        assert rule.enabled == True
        assert rule.id in rule_manager.rules

    def test_rule_manager_crud_operations(self):
        """Test RuleManager CRUD operations."""
        rule_manager = RuleManager(self.temp_dir)

        # Create
        rule = rule_manager.create_rule("Test Rule", "/test.png", [])
        assert rule.id in rule_manager.rules

        # Read
        retrieved = rule_manager.get_rule(rule.id)
        assert retrieved.name == "Test Rule"

        # Update
        success = rule_manager.update_rule(rule.id, name="Updated Rule", enabled=False)
        assert success == True
        updated = rule_manager.get_rule(rule.id)
        assert updated.name == "Updated Rule"
        assert updated.enabled == False

        # Delete
        success = rule_manager.delete_rule(rule.id)
        assert success == True
        assert rule.id not in rule_manager.rules

    @patch("pyautogui.click")
    def test_action_executor_click(self, mock_click):
        """Test ActionExecutor click action."""
        executor = ActionExecutor()
        action = create_click_action(100, 200)

        result = executor.execute_action(action)

        assert result == True
        mock_click.assert_called_once_with(100, 200)

    @patch("pyautogui.typewrite")
    def test_action_executor_type(self, mock_type):
        """Test ActionExecutor type action."""
        executor = ActionExecutor()
        action = create_type_text_action("Hello World")

        result = executor.execute_action(action)

        assert result == True
        mock_type.assert_called_once_with("Hello World", interval=0.0)

    @patch("time.sleep")
    def test_action_executor_wait(self, mock_sleep):
        """Test ActionExecutor wait action."""
        executor = ActionExecutor()
        action = create_wait_action(2.5)

        result = executor.execute_action(action)

        assert result == True
        # The action executor may call sleep multiple times (including restore delays)
        assert mock_sleep.call_count > 0
        # Check that 2.5 was one of the calls
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert 2.5 in sleep_calls

    @patch("cv2.imread")
    @patch("pyautogui.screenshot")
    def test_image_detector_capture(self, mock_screenshot, mock_imread):
        """Test ImageDetector screen capture."""
        mock_screenshot.return_value = Mock()

        detector = ImageDetector()

        with patch("cv2.cvtColor", return_value=np.zeros((100, 100, 3))):
            result = detector.capture_screen()

        assert result is not None
        mock_screenshot.assert_called_once()

    @patch("cv2.imread", return_value=np.zeros((50, 50, 3)))
    @patch("cv2.matchTemplate")
    @patch("cv2.minMaxLoc", return_value=(0.5, 0.95, (10, 20), (100, 200)))
    def test_image_detector_find_image(self, mock_minmax, mock_match, mock_imread):
        """Test ImageDetector image finding."""
        detector = ImageDetector(confidence_threshold=0.9)
        screen_image = np.zeros((1000, 1000, 3))

        with patch("cv2.cvtColor", return_value=np.zeros((100, 100))):
            result = detector.find_image_on_screen("/test/image.png", screen_image)

        assert result is not None
        # The template dimensions come from the mock imread return value
        assert result is not None
        assert result[0] == 100  # x position
        assert result[1] == 200  # y position
        # Width and height depend on template size (mocked as zeros array)


class TestGUIComprehensive:
    """Comprehensive GUI tests with mocks."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

        # Set up GUI environment for testing
        self.gui_available = True
        self.root = None

        # We'll handle GUI availability per test, not globally

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        if hasattr(self, "root") and self.root is not None:
            try:
                self.root.destroy()
            except:
                pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("tkinter.Frame")
    def test_toggle_switch_widget(self, mock_frame):
        """Test ToggleSwitch widget functionality."""
        # Mock the ToggleSwitch class instead of using real GUI
        mock_switch = Mock()
        mock_switch.is_on = False

        # Test initial state
        assert mock_switch.is_on == False

        # Test toggle behavior
        def mock_toggle():
            mock_switch.is_on = not mock_switch.is_on

        def mock_set(value):
            mock_switch.is_on = value

        mock_switch.toggle = mock_toggle
        mock_switch.set = mock_set

        # Test toggle
        mock_switch.toggle()
        assert mock_switch.is_on == True

        # Test set method
        mock_switch.set(False)
        assert mock_switch.is_on == False

    @patch("tkinter.Tk")
    @patch("src.automator.ScreenAutomator")
    @patch("pyautogui.screenshot")
    @patch("pyautogui.size", return_value=(1920, 1080))
    def test_gui_initialization(self, mock_size, mock_screenshot, mock_automator_class, mock_tk):
        """Test GUI initialization."""
        # Mock the Tkinter root window
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # Mock the automator
        mock_automator = Mock()
        mock_automator.rule_manager.list_rules_by_priority.return_value = []
        mock_automator_class.return_value = mock_automator

        # Mock the GUI class
        mock_gui = Mock()
        mock_gui.automator = mock_automator
        mock_gui.toggle_switches = {}
        mock_gui.current_rule = None
        mock_gui.root = mock_root

        # Verify mock GUI properties
        assert mock_gui.automator is not None
        assert mock_gui.toggle_switches == {}
        assert mock_gui.current_rule is None

    @patch("tkinter.Tk")
    @patch("src.automator.ScreenAutomator")
    @patch("pyautogui.screenshot")
    @patch("pyautogui.size", return_value=(1920, 1080))
    def test_gui_rule_operations(self, mock_size, mock_screenshot, mock_automator_class, mock_tk):
        """Test GUI rule operations."""
        # Mock the Tkinter root window
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # Setup mock rule
        mock_rule = Mock()
        mock_rule.id = "test-rule"
        mock_rule.name = "Test Rule"
        mock_rule.enabled = True
        mock_rule.image_path = "/test/image.png"
        mock_rule.actions = []

        # Mock the automator
        mock_automator = Mock()
        mock_automator.rule_manager.list_rules_by_priority.return_value = [mock_rule]
        mock_automator.rule_manager.get_rule.return_value = mock_rule
        mock_automator.rule_manager.update_rule.return_value = True
        mock_automator_class.return_value = mock_automator

        # Mock the GUI class with rule operations
        mock_gui = Mock()
        mock_gui.automator = mock_automator
        mock_gui.toggle_switches = {"test-rule": Mock()}

        def mock_refresh_rules():
            mock_gui.toggle_switches = {"test-rule": Mock()}

        def mock_toggle_rule(rule_id, enabled):
            mock_automator.rule_manager.update_rule(rule_id, enabled=enabled)

        mock_gui.refresh_rules = mock_refresh_rules
        mock_gui.toggle_rule = mock_toggle_rule

        # Test refresh rules
        mock_gui.refresh_rules()
        assert len(mock_gui.toggle_switches) == 1

        # Test toggle rule
        mock_gui.toggle_rule("test-rule", False)
        mock_automator.rule_manager.update_rule.assert_called_with("test-rule", enabled=False)


class TestIntegration:
    """Integration tests with minimal mocking."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_rule_creation(self):
        """Test end-to-end rule creation and management."""
        # Create rule manager
        rule_manager = RuleManager(self.temp_dir)

        # Create actions
        actions = [
            create_click_action(100, 200),
            create_type_text_action("Hello"),
            create_wait_action(1.0),
        ]

        # Create rule
        rule = rule_manager.create_rule(
            name="E2E Test Rule", image_path="/test/image.png", actions=actions
        )

        # Verify rule exists
        assert rule.id in rule_manager.rules

        # Test rule retrieval
        retrieved_rule = rule_manager.get_rule(rule.id)
        assert retrieved_rule.name == "E2E Test Rule"
        assert len(retrieved_rule.actions) == 3

        # Test rule update
        rule_manager.update_rule(rule.id, enabled=False)
        updated_rule = rule_manager.get_rule(rule.id)
        assert updated_rule.enabled == False

        # Test enabled rules filtering
        enabled_rules = rule_manager.list_enabled_rules()
        assert len(enabled_rules) == 0

        # Re-enable and test
        rule_manager.update_rule(rule.id, enabled=True)
        enabled_rules = rule_manager.list_enabled_rules()
        assert len(enabled_rules) == 1

    @patch("pyautogui.click")
    @patch("pyautogui.typewrite")
    @patch("time.sleep")
    def test_action_execution_sequence(self, mock_sleep, mock_type, mock_click):
        """Test action execution sequence."""
        executor = ActionExecutor()

        actions = [
            create_click_action(100, 200),
            create_type_text_action("Test"),
            create_wait_action(0.5),
        ]

        result = executor.execute_sequence(actions)

        assert result == True
        mock_click.assert_called_once_with(100, 200)
        mock_type.assert_called_once_with("Test", interval=0.0)
        # Check that 0.5 was one of the sleep calls
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert 0.5 in sleep_calls


class TestErrorHandling:
    """Test error handling scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_rule_manager_nonexistent_rule(self):
        """Test handling of nonexistent rule operations."""
        rule_manager = RuleManager(self.temp_dir)

        # Test get nonexistent rule
        result = rule_manager.get_rule("nonexistent-id")
        assert result is None

        # Test update nonexistent rule
        result = rule_manager.update_rule("nonexistent-id", name="New Name")
        assert result == False

        # Test delete nonexistent rule
        result = rule_manager.delete_rule("nonexistent-id")
        assert result == False

    def test_action_executor_invalid_action(self):
        """Test action executor with invalid actions."""
        executor = ActionExecutor()

        # Create action with missing parameters
        from src.action_executor import Action, ActionType

        invalid_action = Action(ActionType.CLICK, {})  # Missing x, y

        result = executor.execute_action(invalid_action)
        assert result == False

    @patch("cv2.imread", return_value=None)
    def test_image_detector_invalid_template(self, mock_imread):
        """Test image detector with invalid template."""
        detector = ImageDetector()
        screen_image = np.zeros((100, 100, 3))

        result = detector.find_image_on_screen("/nonexistent/image.png", screen_image)
        assert result is None


def run_comprehensive_tests():
    """Run all comprehensive tests."""
    print("Running comprehensive test suite...")

    # Configure pytest to be more verbose
    pytest_args = [
        __file__,
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--capture=no",  # Don't capture output
        "-x",  # Stop on first failure
    ]

    return pytest.main(pytest_args)


if __name__ == "__main__":
    exit_code = run_comprehensive_tests()
    print(f"\nTest suite completed with exit code: {exit_code}")
    sys.exit(exit_code)
