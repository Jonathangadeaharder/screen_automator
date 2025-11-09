"""Anonymous telemetry for application improvement."""

import json
import platform
import threading
import time
import urllib.request
import uuid
from typing import Any

from utils.config import get_config_dir

# Constants
TELEMETRY_URL = "https://screenauto.example.org/telemetry"
TELEMETRY_ENDPOINT = "/v1/collect"


def get_machine_id() -> str:
    """Get a unique machine ID that's persisted between runs."""
    machine_id_file = get_config_dir() / "machine_id"

    if machine_id_file.exists():
        try:
            return machine_id_file.read_text().strip()
        except Exception:
            pass

    # Generate a new ID
    machine_id = str(uuid.uuid4())
    try:
        machine_id_file.write_text(machine_id)
    except Exception:
        pass

    return machine_id


def send_telemetry(
    event_name: str, event_data: dict[str, Any] = None, opt_in: bool = False
) -> None:
    """Send telemetry data to server if user has opted in."""
    if not opt_in:
        return

    if event_data is None:
        event_data = {}

    # Add basic system data
    payload = {
        "event": event_name,
        "timestamp": int(time.time()),
        "machine_id": get_machine_id(),
        "system_info": {
            "os": platform.system(),
            "os_version": platform.version(),
            "python": platform.python_version(),
        },
        "data": event_data,
    }

    # Send in background thread
    threading.Thread(target=_send_telemetry_worker, args=(payload,), daemon=True).start()


def _send_telemetry_worker(payload: dict[str, Any]) -> None:
    """Worker thread to send telemetry without blocking."""
    try:
        url = TELEMETRY_URL + TELEMETRY_ENDPOINT
        data = json.dumps(payload).encode("utf-8")

        headers = {"Content-Type": "application/json", "User-Agent": "ScreenAutomator/1.0"}

        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=3.0):
            pass  # We don't care about the response
    except Exception:
        pass  # Silently fail on telemetry errors
