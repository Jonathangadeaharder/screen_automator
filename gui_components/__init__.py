"""GUI component wrappers extracted from gui_v2 for cleaner imports.
Future refactors will fully move implementations here; currently they re-export
classes from gui_v2 so existing code keeps working while callers migrate.
"""
from .record_hud import RecordHUD
from .rule_editor import RuleEditor
from .dialogs import TipDialog, FirstRuleWizard, PerformanceOverlay
from .widgets import ColorBox, ConfirmDialog, SearchEntry, CollapsiblePane, StatusIndicator, KeybindField

__all__ = [
    'RecordHUD',
    'RuleEditor',
    'TipDialog',
    'FirstRuleWizard',
    'PerformanceOverlay',
    'ColorBox',
    'ConfirmDialog',
    'SearchEntry',
    'CollapsiblePane',
    'StatusIndicator',
    'KeybindField',
]
