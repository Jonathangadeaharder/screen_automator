"""Configuration utilities for Screen Automator."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


def get_config_dir() -> Path:
    """Get the configuration directory, creating it if needed."""
    if os.name == "nt":  # Windows
        config_dir = Path(os.environ.get("APPDATA", "")) / "ScreenAutomator"
    else:  # Linux/Mac
        config_dir = Path(os.path.expanduser("~/.config/screen-automator"))

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def load_config(filename: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    config_path = get_config_dir() / filename
    if config_path.exists():
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_config(filename: str, data: Dict[str, Any]) -> None:
    """Save configuration to JSON file."""
    config_path = get_config_dir() / filename
    try:
        config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass  # Silent fail on config save error
