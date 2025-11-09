import os
import platform
import sys
import time
from unittest.mock import MagicMock, call, patch

import pytest

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.action_executor import Action, ActionType
from src.context_automator import ContextAwareAutomator
from src.rule_manager import Rule
from src.window_manager import WindowInfo, WindowManager


@pytest.fixture
def mock_window_info():
    """Create a mock WindowInfo for testing"""
    return WindowInfo(
        handle=123456,
        title="Test Window",
        process_name="test.exe",
        process_id=1234,
        x=100,
        y=200,
        width=800,
        height=600,
        is_visible=True,
        is_minimized=False,
        class_name="TestClass",
    )


@pytest.fixture
def mock_windows_list():
    """Create a list of mock windows for testing"""
    return [
        WindowInfo(
            handle=111,
            title="Notepad",
            process_name="notepad.exe",
            process_id=1111,
            x=0,
            y=0,
            width=640,
            height=480,
            is_visible=True,
            is_minimized=False,
        ),
        WindowInfo(
            handle=222,
            title="Calculator",
            process_name="calc.exe",
            process_id=2222,
            x=100,
            y=100,
            width=300,
            height=400,
            is_visible=True,
            is_minimized=False,
        ),
        WindowInfo(
            handle=333,
            title="Browser Window",
            process_name="chrome.exe",
            process_id=3333,
            x=200,
            y=200,
            width=1024,
            height=768,
            is_visible=True,
            is_minimized=True,
        ),
    ]


class TestWindowManager:
    """Test cases for WindowManager"""

    @pytest.mark.timeout(30)
    def test_window_manager_init(self):
        """Test WindowManager initialization"""
        wm = WindowManager()
        assert wm.system in ["Windows", "Linux", "Darwin"]
        assert wm._current_active_window is None
        assert wm._original_active_window is None

    @pytest.mark.timeout(30)
    @patch("src.window_manager.platform.system")
    def test_get_running_windows_unsupported_system(self, mock_system):
        """Test get_running_windows on unsupported system"""
        mock_system.return_value = "UnknownOS"
        wm = WindowManager()

        windows = wm.get_running_windows()
        assert windows == []

    @pytest.mark.timeout(30)
    @patch("src.window_manager.HAS_WIN32", True)
    @patch("src.window_manager.win32gui")
    @patch("src.window_manager.win32process")
    @patch("src.window_manager.psutil")
    def test_get_windows_windows(self, mock_psutil, mock_win32process, mock_win32gui):
        """Test Windows-specific window enumeration"""
        # Mock win32gui functions
        mock_win32gui.IsWindow.return_value = True
        mock_win32gui.IsWindowVisible.return_value = True
        mock_win32gui.GetWindowText.return_value = "Test Window"
        mock_win32gui.GetWindowRect.return_value = (100, 200, 900, 800)
        mock_win32gui.IsIconic.return_value = False
        mock_win32gui.GetClassName.return_value = "TestClass"

        # Mock win32process
        mock_win32process.GetWindowThreadProcessId.return_value = (0, 1234)

        # Mock psutil
        mock_process = MagicMock()
        mock_process.name.return_value = "test.exe"
        mock_psutil.Process.return_value = mock_process

        # Mock EnumWindows to call callback once
        def mock_enum_windows(callback, windows_list):
            callback(123456, windows_list)
            return True

        mock_win32gui.EnumWindows.side_effect = mock_enum_windows

        with patch("src.window_manager.platform.system", return_value="Windows"):
            wm = WindowManager()
            windows = wm._get_windows_windows(include_minimized=True)

        assert len(windows) == 1
        assert windows[0].handle == 123456
        assert windows[0].title == "Test Window"
        assert windows[0].process_name == "test.exe"

    @pytest.mark.timeout(30)
    def test_window_info_to_dict(self, mock_window_info):
        """Test WindowInfo serialization"""
        data = mock_window_info.to_dict()

        expected_keys = {
            "handle",
            "title",
            "process_name",
            "process_id",
            "x",
            "y",
            "width",
            "height",
            "is_visible",
            "is_minimized",
            "class_name",
        }
        assert set(data.keys()) == expected_keys
        assert data["handle"] == 123456
        assert data["title"] == "Test Window"

    @pytest.mark.timeout(30)
    def test_find_window_by_title(self, mock_windows_list):
        """Test finding window by title"""
        with patch.object(WindowManager, "get_running_windows", return_value=mock_windows_list):
            wm = WindowManager()

            # Test partial match
            window = wm.find_window_by_title("Notepad", exact_match=False)
            assert window is not None
            assert window.title == "Notepad"

            # Test exact match
            window = wm.find_window_by_title("Calculator", exact_match=True)
            assert window is not None
            assert window.title == "Calculator"

            # Test no match
            window = wm.find_window_by_title("NonExistent", exact_match=True)
            assert window is None

    @pytest.mark.timeout(30)
    def test_find_windows_by_process(self, mock_windows_list):
        """Test finding windows by process name"""
        with patch.object(WindowManager, "get_running_windows", return_value=mock_windows_list):
            wm = WindowManager()

            windows = wm.find_windows_by_process("notepad")
            assert len(windows) == 1
            assert windows[0].process_name == "notepad.exe"

            windows = wm.find_windows_by_process("chrome")
            assert len(windows) == 1
            assert windows[0].process_name == "chrome.exe"

            windows = wm.find_windows_by_process("nonexistent")
            assert len(windows) == 0


class TestRuleManagerWindowExtensions:
    """Test cases for RuleManager window-related extensions"""

    @pytest.mark.timeout(30)
    def test_rule_with_window_targeting(self):
        """Test Rule class with window targeting fields"""
        from src.action_executor import Action, ActionType

        actions = [Action(ActionType.CLICK, {"x": 100, "y": 200})]
        rule = Rule(
            id="test-rule",
            name="Test Rule",
            image_path="test.png",
            actions=actions,
            target_window_title="Notepad",
            target_window_process="notepad.exe",
            window_exact_match=True,
            cluster_group="text_editors",
        )

        assert rule.target_window_title == "Notepad"
        assert rule.target_window_process == "notepad.exe"
        assert rule.window_exact_match is True
        assert rule.cluster_group == "text_editors"

    @pytest.mark.timeout(30)
    def test_rule_serialization_with_window_fields(self):
        """Test Rule serialization includes window fields"""
        from src.action_executor import Action, ActionType

        actions = [Action(ActionType.CLICK, {"x": 100, "y": 200})]
        rule = Rule(
            id="test-rule",
            name="Test Rule",
            image_path="test.png",
            actions=actions,
            target_window_title="Calculator",
            cluster_group="utilities",
        )

        data = rule.to_dict()
        assert "target_window_title" in data
        assert "target_window_process" in data
        assert "window_exact_match" in data
        assert "cluster_group" in data

        assert data["target_window_title"] == "Calculator"
        assert data["cluster_group"] == "utilities"

    @pytest.mark.timeout(30)
    def test_rule_deserialization_with_window_fields(self):
        """Test Rule deserialization handles window fields"""
        data = {
            "id": "test-rule",
            "name": "Test Rule",
            "image_path": "test.png",
            "actions": [{"type": "click", "params": {"x": 100, "y": 200}}],
            "target_window_title": "Browser",
            "target_window_process": "chrome.exe",
            "window_exact_match": False,
            "cluster_group": "browsers",
        }

        rule = Rule.from_dict(data)
        assert rule.target_window_title == "Browser"
        assert rule.target_window_process == "chrome.exe"
        assert rule.window_exact_match is False
        assert rule.cluster_group == "browsers"

    @pytest.mark.timeout(30)
    def test_get_rules_by_cluster(self):
        """Test rule clustering functionality"""
        # Create temporary rules directory
        import tempfile

        from src.action_executor import Action, ActionType
        from src.rule_manager import RuleManager

        with tempfile.TemporaryDirectory() as temp_dir:
            rm = RuleManager(temp_dir)

            # Create test rules with different clustering
            actions = [Action(ActionType.CLICK, {"x": 100, "y": 200})]

            rule1 = rm.create_rule(
                name="Notepad Rule 1", image_path="notepad1.png", actions=actions
            )
            rule1.target_window_title = "Notepad"
            rule1.cluster_group = "text_editors"
            rm.save_rule(rule1)

            rule2 = rm.create_rule(
                name="Notepad Rule 2", image_path="notepad2.png", actions=actions
            )
            rule2.target_window_title = "Notepad"
            rule2.cluster_group = "text_editors"
            rm.save_rule(rule2)

            rule3 = rm.create_rule(name="Calculator Rule", image_path="calc.png", actions=actions)
            rule3.target_window_title = "Calculator"
            rm.save_rule(rule3)

            # Test clustering
            clusters = rm.get_rules_by_cluster()

            # Should have different clusters
            assert len(clusters) > 1

            # Find text editor cluster
            text_editor_cluster = None
            for key, rules in clusters.items():
                if "text_editors" in key:
                    text_editor_cluster = rules
                    break

            assert text_editor_cluster is not None
            assert len(text_editor_cluster) == 2

    @pytest.mark.timeout(30)
    def test_rule_matches_window(self):
        """Test rule window matching logic"""
        import tempfile

        from src.rule_manager import RuleManager

        with tempfile.TemporaryDirectory() as temp_dir:
            rm = RuleManager(temp_dir)

            # Test partial title match
            assert rm._rule_matches_window(
                MagicMock(
                    target_window_title="Notepad",
                    target_window_process="",
                    window_exact_match=False,
                ),
                "Notepad - Document1.txt",
                "notepad.exe",
            )

            # Test exact title match
            assert rm._rule_matches_window(
                MagicMock(
                    target_window_title="Calculator",
                    target_window_process="",
                    window_exact_match=True,
                ),
                "Calculator",
                "calc.exe",
            )

            # Test exact title mismatch
            assert not rm._rule_matches_window(
                MagicMock(
                    target_window_title="Calculator",
                    target_window_process="",
                    window_exact_match=True,
                ),
                "Calculator - Scientific",
                "calc.exe",
            )

            # Test process match
            assert rm._rule_matches_window(
                MagicMock(
                    target_window_title="", target_window_process="chrome", window_exact_match=False
                ),
                "Google Chrome",
                "chrome.exe",
            )

            # Test no targeting (matches any)
            assert rm._rule_matches_window(
                MagicMock(
                    target_window_title="", target_window_process="", window_exact_match=False
                ),
                "Any Window",
                "any.exe",
            )


class TestContextAwareAutomator:
    """Test cases for ContextAwareAutomator"""

    @pytest.mark.timeout(30)
    def test_context_automator_init(self):
        """Test ContextAwareAutomator initialization"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            automator = ContextAwareAutomator(temp_dir)

            assert hasattr(automator, "window_manager")
            assert automator.current_context_window is None
            assert automator.context_execution_active is False
            assert automator.cluster_cooldown == 2.0

    @pytest.mark.timeout(30)
    @patch("src.context_automator.ScreenAutomator.start_monitoring")
    def test_start_context_monitoring(self, mock_start):
        """Test starting context-aware monitoring"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            automator = ContextAwareAutomator(temp_dir)

            automator.start_context_monitoring()

            assert automator.context_execution_active is True
            mock_start.assert_called_once()

    @pytest.mark.timeout(30)
    @patch("src.context_automator.ScreenAutomator.stop_monitoring")
    def test_stop_context_monitoring(self, mock_stop):
        """Test stopping context-aware monitoring"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            automator = ContextAwareAutomator(temp_dir)

            # Set up a mock current window
            mock_window = MagicMock()
            automator.current_context_window = mock_window

            with patch.object(automator.window_manager, "restore_original_window") as mock_restore:
                automator.stop_context_monitoring()

            assert automator.context_execution_active is False
            assert automator.current_context_window is None
            mock_restore.assert_called_once()
            mock_stop.assert_called_once()

    @pytest.mark.timeout(30)
    def test_get_cluster_target_window(self, mock_windows_list):
        """Test determining target window for rule cluster"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            automator = ContextAwareAutomator(temp_dir)

            # Mock window manager methods
            automator.window_manager.find_window_by_title = MagicMock(
                return_value=mock_windows_list[0]
            )
            automator.window_manager.find_windows_by_process = MagicMock(
                return_value=[mock_windows_list[1]]
            )

            # Test rule with window title targeting
            rule1 = MagicMock()
            rule1.target_window_title = "Notepad"
            rule1.target_window_process = ""
            rule1.window_exact_match = False

            target = automator._get_cluster_target_window([rule1])
            assert target == mock_windows_list[0]

            # Test rule with process targeting
            rule2 = MagicMock()
            rule2.target_window_title = ""
            rule2.target_window_process = "calc.exe"

            target = automator._get_cluster_target_window([rule2])
            assert target == mock_windows_list[1]

    @pytest.mark.timeout(30)
    def test_switch_to_context_window(self, mock_window_info):
        """Test switching to context window"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            automator = ContextAwareAutomator(temp_dir)

            # Mock successful window switch
            automator.window_manager.switch_to_window = MagicMock(return_value=True)

            # Test callback
            callback_called = False

            def test_callback(window_info):
                nonlocal callback_called
                callback_called = True
                assert window_info == mock_window_info

            automator.on_window_context_changed = test_callback

            result = automator._switch_to_context_window(mock_window_info)

            assert result is True
            assert automator.current_context_window == mock_window_info
            assert callback_called

    @pytest.mark.timeout(30)
    def test_get_available_windows(self, mock_windows_list):
        """Test getting available windows for rule targeting"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            automator = ContextAwareAutomator(temp_dir)

            with patch.object(
                automator.window_manager, "get_running_windows", return_value=mock_windows_list
            ):
                windows = automator.get_available_windows()

            assert len(windows) == 3
            assert windows == mock_windows_list

    @pytest.mark.timeout(30)
    def test_test_rule_in_window(self, mock_window_info):
        """Test testing a rule in specific window context"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            automator = ContextAwareAutomator(temp_dir)

            # Create a test rule
            from src.action_executor import Action, ActionType

            actions = [Action(ActionType.CLICK, {"x": 100, "y": 200})]
            rule = automator.rule_manager.create_rule(
                name="Test Rule", image_path="test.png", actions=actions
            )

            # Mock window operations
            automator.window_manager.find_window_by_title = MagicMock(return_value=mock_window_info)
            automator.window_manager.get_active_window = MagicMock(return_value=mock_window_info)
            automator.window_manager.switch_to_window = MagicMock(return_value=True)

            # Mock rule execution
            automator._execute_rule_in_context = MagicMock(return_value=True)

            result = automator.test_rule_in_window(rule.id, window_title="Test Window")

            assert result is True
            assert automator._execute_rule_in_context.called

    @pytest.mark.timeout(30)
    def test_cluster_cooldown_settings(self):
        """Test cluster cooldown configuration"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            automator = ContextAwareAutomator(temp_dir)

            # Test setting cooldown
            automator.set_cluster_cooldown(5.0)
            assert automator.cluster_cooldown == 5.0

            # Test minimum cooldown
            automator.set_cluster_cooldown(0.05)
            assert automator.cluster_cooldown == 0.1  # Should be clamped to minimum

    @pytest.mark.timeout(30)
    def test_get_cluster_status(self):
        """Test getting cluster status information"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            automator = ContextAwareAutomator(temp_dir)

            # Create test rules
            from src.action_executor import Action, ActionType

            actions = [Action(ActionType.CLICK, {"x": 100, "y": 200})]

            rule1 = automator.rule_manager.create_rule(
                name="Test Rule 1", image_path="test1.png", actions=actions
            )
            rule1.cluster_group = "test_cluster"
            automator.rule_manager.save_rule(rule1)

            rule2 = automator.rule_manager.create_rule(
                name="Test Rule 2", image_path="test2.png", actions=actions
            )
            rule2.cluster_group = "test_cluster"
            automator.rule_manager.save_rule(rule2)

            status = automator.get_cluster_status()

            assert isinstance(status, dict)
            assert len(status) > 0

            # Find our test cluster
            test_cluster = None
            for key, info in status.items():
                if "test_cluster" in key:
                    test_cluster = info
                    break

            assert test_cluster is not None
            assert test_cluster["rule_count"] == 2
            assert "Test Rule 1" in test_cluster["rules"]
            assert "Test Rule 2" in test_cluster["rules"]
            assert test_cluster["ready_for_execution"] is True  # No previous execution


class TestWindowManagementIntegration:
    """Integration tests for window management features"""

    @pytest.mark.timeout(30)
    @patch("src.window_manager.platform.system")
    def test_cross_platform_compatibility(self, mock_system):
        """Test that window manager handles different platforms gracefully"""
        # Test Windows
        mock_system.return_value = "Windows"
        wm = WindowManager()
        assert wm.system == "Windows"

        # Test Linux
        mock_system.return_value = "Linux"
        wm = WindowManager()
        assert wm.system == "Linux"

        # Test macOS
        mock_system.return_value = "Darwin"
        wm = WindowManager()
        assert wm.system == "Darwin"

        # Test unsupported system
        mock_system.return_value = "UnknownOS"
        wm = WindowManager()
        windows = wm.get_running_windows()
        assert windows == []

    @pytest.mark.timeout(30)
    def test_rule_window_targeting_workflow(self):
        """Test complete workflow of creating and targeting rules to windows"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            automator = ContextAwareAutomator(temp_dir)

            # Create rule with window targeting
            from src.action_executor import Action, ActionType

            actions = [Action(ActionType.CLICK, {"x": 100, "y": 200})]

            rule = automator.rule_manager.create_rule(
                name="Notepad Click Rule", image_path="notepad_button.png", actions=actions
            )

            # Set window targeting
            rule.target_window_title = "Notepad"
            rule.target_window_process = "notepad.exe"
            rule.window_exact_match = False
            rule.cluster_group = "text_editors"
            automator.rule_manager.save_rule(rule)

            # Verify clustering
            clusters = automator.rule_manager.get_rules_by_cluster()

            # Should have at least one cluster
            assert len(clusters) > 0

            # Find our cluster
            notepad_cluster = None
            for key, rules in clusters.items():
                if any("Notepad" in r.target_window_title for r in rules):
                    notepad_cluster = rules
                    break

            assert notepad_cluster is not None
            assert len(notepad_cluster) == 1
            assert notepad_cluster[0].name == "Notepad Click Rule"
