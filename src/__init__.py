# Screen Automator Package
"""
Modern Screen Automator Framework

For the recommended modern API, use:
    from src import create_framework
    framework = create_framework()

Or import directly:
    from src.modern_api import create_framework
"""

# Export modern API as primary interface
from src.modern_api import ScreenAutomatorFramework, create_framework

__all__ = ["create_framework", "ScreenAutomatorFramework"]

__version__ = "2.0.0"
