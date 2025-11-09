"""GUI package for Screen Automator."""

from .main_window import MainWindow

__all__ = ["MainWindow", "launch_app"]


def launch_app():
    """Launch the Screen Automator GUI application."""
    from .main_window import MainWindow

    root = MainWindow()
    root.mainloop()
