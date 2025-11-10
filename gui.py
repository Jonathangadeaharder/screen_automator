#!/usr/bin/env python3
"""
Screen Automator GUI Launcher

This launcher provides backward compatibility while using the modern
GUI implementation from the gui/ package.

Usage:
    python gui.py
"""

if __name__ == "__main__":
    from gui import launch_app

    launch_app()
