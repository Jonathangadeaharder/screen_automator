"""Localization support for Screen Automator."""

import json
from pathlib import Path
from typing import Dict, Optional

# Global translation dictionary
_TRANSL: Dict[str, str] = {}


def load_translations(locale: str = "en") -> None:
    """Load translations for the specified locale."""
    global _TRANSL
    try:
        loc_file = Path(__file__).resolve().parent.parent / "locales" / f"{locale}.json"
        if loc_file.exists():
            _TRANSL = json.loads(loc_file.read_text(encoding="utf-8"))
    except Exception:
        _TRANSL = {}


def _(text: str) -> str:
    """Return translated text or original if missing."""
    return _TRANSL.get(text, text)


# Load default translations on import
load_translations()
