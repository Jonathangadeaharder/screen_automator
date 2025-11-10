"""
Protocol definitions for GUI components to avoid circular dependencies.

This module defines interfaces (protocols) that allow type checking without
requiring concrete class imports, breaking circular dependency chains.
"""

from typing import Protocol, Optional, Any
from pathlib import Path


class WindowProtocol(Protocol):
    """
    Protocol for main window interface.

    This allows dialogs and other components to reference the main window
    without importing the concrete MainWindow class, avoiding circular imports.
    """

    show_tips: bool  # Whether to show tips on startup
    automator: Any  # Automator instance

    def refresh_rules_list(self) -> None:
        """Refresh the rules list display."""
        ...

    def show_message(self, title: str, message: str, icon: str = "info") -> None:
        """Show a message dialog."""
        ...

    def get_rules_dir(self) -> Path:
        """Get the rules directory path."""
        ...

    def get_current_rule(self) -> Optional[Any]:
        """Get the currently selected rule."""
        ...

    def update_status(self, message: str) -> None:
        """Update status bar message."""
        ...


class RuleEditorProtocol(Protocol):
    """Protocol for rule editor interface."""

    def save_rule(self) -> bool:
        """Save the current rule. Returns True if successful."""
        ...

    def load_rule(self, rule_id: str) -> None:
        """Load a rule by ID."""
        ...

    def clear_form(self) -> None:
        """Clear all form fields."""
        ...


class DialogProtocol(Protocol):
    """Protocol for dialog interface."""

    def show(self) -> Optional[Any]:
        """Show the dialog and return result."""
        ...

    def destroy(self) -> None:
        """Close and destroy the dialog."""
        ...
