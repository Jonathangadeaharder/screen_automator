"""Centralized logging system for Screen Automator."""

import logging
import sys
import threading
from typing import Callable, Optional


class GUILogHandler(logging.Handler):
    """Custom logging handler that sends logs to the GUI activity log."""

    def __init__(self):
        super().__init__()
        self.gui_log_callback: Optional[Callable[[str], None]] = None
        self._lock = threading.Lock()

    def set_gui_callback(self, callback: Callable[[str], None]):
        """Set the callback function for GUI logging."""
        with self._lock:
            self.gui_log_callback = callback

    def emit(self, record):
        """Emit a log record to the GUI."""
        try:
            msg = self.format(record)
            with self._lock:
                if self.gui_log_callback:
                    # Execute in main thread if possible
                    self.gui_log_callback(msg)
        except Exception:
            # Silently ignore errors to prevent logging loops
            pass


class ScreenAutomatorLogger:
    """Centralized logger for Screen Automator application."""

    def __init__(self):
        self.logger = logging.getLogger("screen_automator")
        self.logger.setLevel(logging.DEBUG)

        # Remove any existing handlers
        self.logger.handlers.clear()

        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # Create GUI handler
        self.gui_handler = GUILogHandler()
        self.gui_handler.setLevel(logging.DEBUG)
        gui_formatter = logging.Formatter("%(message)s")
        self.gui_handler.setFormatter(gui_formatter)
        self.logger.addHandler(self.gui_handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def set_gui_callback(self, callback: Callable[[str], None]):
        """Set the GUI callback for log messages."""
        self.gui_handler.set_gui_callback(callback)

    def debug(self, msg: str):
        """Log debug message."""
        self.logger.debug(msg)

    def info(self, msg: str):
        """Log info message."""
        self.logger.info(msg)

    def warning(self, msg: str):
        """Log warning message."""
        self.logger.warning(msg)

    def error(self, msg: str):
        """Log error message."""
        self.logger.error(msg)

    def critical(self, msg: str):
        """Log critical message."""
        self.logger.critical(msg)


# Global logger instance
_global_logger: Optional[ScreenAutomatorLogger] = None


def get_logger() -> ScreenAutomatorLogger:
    """Get the global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = ScreenAutomatorLogger()
    return _global_logger


def setup_gui_logging(gui_log_callback: Callable[[str], None]):
    """Setup GUI logging with the provided callback."""
    logger = get_logger()
    logger.set_gui_callback(gui_log_callback)


# Convenience functions for logging
def debug(msg: str):
    """Log debug message."""
    get_logger().debug(msg)


def info(msg: str):
    """Log info message."""
    get_logger().info(msg)


def warning(msg: str):
    """Log warning message."""
    get_logger().warning(msg)


def error(msg: str):
    """Log error message."""
    get_logger().error(msg)


def critical(msg: str):
    """Log critical message."""
    get_logger().critical(msg)


# Function to help migrate from print statements
def log_print(msg: str):
    """Log a message that was previously a print statement."""
    get_logger().info(msg)
