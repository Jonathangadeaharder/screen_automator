"""Recording HUD overlay for capturing user actions."""

import threading
import time

import ttkbootstrap as tb
from pynput import keyboard, mouse
from ttkbootstrap.constants import BOTH, DANGER, END, LEFT, X

from core.localization import _
from src.action_executor import (
    Action,
    create_click_action,
    create_key_press_action,
    create_move_action,
)


class RecordHUD(tb.Toplevel):
    """Floating HUD that records clicks + keys + moves until the user stops."""

    def __init__(self, master: tb.Window):
        super().__init__(master)
        self.title(_("Recording…"))
        self.geometry("180x250")
        self.attributes("-topmost", True)
        self.resizable(False, False)

        topbar = tb.Frame(self)
        topbar.pack(fill=X, padx=10, pady=(8, 5))
        self.btn_pause = tb.Button(topbar, text="⏸ Pause", command=self._toggle_pause)
        self.btn_pause.pack(side=LEFT, expand=True, fill=X, padx=(0, 5))
        self.btn_stop = tb.Button(topbar, text="⏹ Stop", bootstyle=DANGER, command=self._stop)
        self.btn_stop.pack(side=LEFT, expand=True, fill=X)

        # Mini timeline listbox
        tb.Label(self, text=_("Last events")).pack()
        self.lst_timeline = tb.Listbox(self, height=5)
        self.lst_timeline.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))

        # center right-top corner
        x = master.winfo_screenwidth() - 220
        y = 80
        self.geometry(f"+{x}+{y}")

        self._running = True
        self.paused = False
        self.idle_threshold = 60  # seconds
        self._last_activity = time.time()
        self.events: list[Action] = []

        # Threads
        threading.Thread(target=self._mouse_thread, daemon=True).start()
        threading.Thread(target=self._keyboard_thread, daemon=True).start()
        threading.Thread(target=self._idle_watch_thread, daemon=True).start()

        self.bind("<Escape>", lambda *_: self._stop())

    def _stop(self):
        """Stop recording and close the HUD."""
        self._running = False
        self.destroy()

    def _mouse_thread(self):
        """Background thread to monitor mouse movement and clicks."""

        def on_move(x, y):
            if not self._running or self.paused:
                return False
            act = create_move_action(int(x), int(y))
            self._add_event(act)

        def on_click(x, y, button, pressed):
            if not self._running or self.paused:
                return False
            if pressed and button.name == "left":
                act = create_click_action(int(x), int(y))
                self._add_event(act)
            return True

        with mouse.Listener(on_move=on_move, on_click=on_click) as listener:
            while self._running:
                time.sleep(0.05)
            listener.stop()

    def _keyboard_thread(self):
        """Background thread to monitor keyboard presses."""

        def on_press(key):
            if not self._running or self.paused:
                return False
            try:
                k = key.char if hasattr(key, "char") and key.char else str(key)
            except Exception:
                k = str(key)
            # Debounce – skip repeats quickly
            if (
                self.events
                and self.events[-1].type.value == "key_press"
                and self.events[-1].params["key"] == k
            ):
                return True
            act = create_key_press_action(k)
            self._add_event(act)
            return True

        with keyboard.Listener(on_press=on_press) as listener:
            while self._running:
                time.sleep(0.05)
            listener.stop()

    def _add_event(self, act: Action):
        """Add a new action to the event list and update the UI."""
        self.events.append(act)
        self.lst_timeline.insert(0, f"{act.type.value}: {act.params}")
        if self.lst_timeline.size() > 5:
            self.lst_timeline.delete(5, END)
        self._last_activity = time.time()

    def _toggle_pause(self):
        """Toggle the pause state of the recorder."""
        self.paused = not self.paused
        self.btn_pause.configure(text="▶ Resume" if self.paused else "⏸ Pause")

    def _idle_watch_thread(self):
        """Background thread to auto-stop recording after inactivity."""
        while self._running:
            time.sleep(1)
            if not self.paused and time.time() - self._last_activity > self.idle_threshold:
                if self._running:
                    self._stop()
                break
