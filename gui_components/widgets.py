"""Custom widget components for Screen Automator GUI."""

import tkinter as tk

import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, END, LEFT, PRIMARY, X

from core.localization import _


class ColorBox(tb.Frame):
    """Simple color display rectangle."""

    def __init__(self, master, color="#000000", width=20, height=20, **kwargs):
        super().__init__(master, width=width, height=height, **kwargs)
        self.configure(background=color)
        self.color = color

    def set_color(self, color: str) -> None:
        """Change the displayed color."""
        self.color = color
        self.configure(background=color)


class ConfirmDialog(tb.Toplevel):
    """Simple Yes/No confirmation dialog."""

    def __init__(self, master, title=None, message=None, yes_text=None, no_text=None, **kwargs):
        super().__init__(master, **kwargs)
        self.title(title or _("Confirm"))
        self.resizable(False, False)

        self.result = False

        frame = tb.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)

        tb.Label(frame, text=message or _("Are you sure?"), wraplength=300).pack(pady=10)

        btn_frame = tb.Frame(frame)
        btn_frame.pack(fill=X, pady=10)

        tb.Button(btn_frame, text=no_text or _("No"), command=self._on_no).pack(
            side=LEFT, padx=(0, 10)
        )

        tb.Button(
            btn_frame, text=yes_text or _("Yes"), bootstyle=PRIMARY, command=self._on_yes
        ).pack(side=LEFT)

        # Position
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Modal
        self.transient(master)
        self.grab_set()
        self.focus_set()

    def _on_yes(self) -> None:
        """Handle Yes button click."""
        self.result = True
        self.destroy()

    def _on_no(self) -> None:
        """Handle No button click."""
        self.result = False
        self.destroy()


class SearchEntry(tb.Entry):
    """Entry field with search icon and clear button."""

    def __init__(self, master, callback=None, width=20, **kwargs):
        super().__init__(master, width=width, **kwargs)

        self.callback = callback

        # Add clear button inside entry
        self.clear_button = tb.Label(self, text="✕", cursor="hand2")
        self.clear_button.bind("<Button-1>", self._clear)

        # Only show clear button when there's text
        self.bind("<KeyRelease>", self._check_text)

        # Update position when entry resizes
        self.bind("<Configure>", self._on_configure)

    def _check_text(self, event=None) -> None:
        """Check if there's text and show/hide clear button."""
        if self.get():
            self._place_clear_button()
        else:
            self.clear_button.place_forget()

        # Call callback if provided
        if self.callback:
            self.callback(self.get())

    def _clear(self, event=None) -> None:
        """Clear the entry and trigger callback."""
        self.delete(0, END)
        self.clear_button.place_forget()
        if self.callback:
            self.callback("")

    def _on_configure(self, event=None) -> None:
        """Reposition clear button when entry resizes."""
        if self.get():
            self._place_clear_button()

    def _place_clear_button(self) -> None:
        """Position the clear button in the entry."""
        w = self.winfo_width()
        self.clear_button.place(x=w - 20, y=0, height=self.winfo_height())


class CollapsiblePane(tb.Frame):
    """Frame that can be expanded/collapsed with a header button."""

    def __init__(self, master, title="", expanded=True, **kwargs):
        super().__init__(master, **kwargs)
        self.expanded = expanded

        # Header
        self.header = tb.Button(
            self, text=f'{"▼" if expanded else "►"} {title}', command=self.toggle, bootstyle="link"
        )
        self.header.pack(fill=X, anchor="w")

        # Content frame
        self.content = tb.Frame(self)
        if expanded:
            self.content.pack(fill=BOTH, expand=True, padx=10, pady=5)

    def toggle(self) -> None:
        """Toggle expanded/collapsed state."""
        self.expanded = not self.expanded

        # Update header
        self.header.configure(text=f'{"▼" if self.expanded else "►"} {self.header["text"][2:]}')

        # Show/hide content
        if self.expanded:
            self.content.pack(fill=BOTH, expand=True, padx=10, pady=5)
        else:
            self.content.pack_forget()


class StatusIndicator(tb.Frame):
    """
    Status indicator with icon, color, and text (accessible).

    Uses multiple visual cues (color, icon, text) to convey status,
    ensuring accessibility for colorblind users and screen readers.
    """

    def __init__(self, master, status="ok", show_text=True, **kwargs):
        super().__init__(master, **kwargs)
        self.show_text = show_text

        # Define status configurations (color + icon + text)
        self.status_configs = {
            "ok": {
                "color": "#44cc44",  # Green
                "icon": "✓",
                "text": _("Active"),
                "tooltip": _("Status: Active and running")
            },
            "warning": {
                "color": "#ffaa00",  # Yellow/Orange
                "icon": "⚠",
                "text": _("Warning"),
                "tooltip": _("Status: Warning - requires attention")
            },
            "error": {
                "color": "#ff4444",  # Red
                "icon": "❌",
                "text": _("Error"),
                "tooltip": _("Status: Error - not functioning")
            },
            "inactive": {
                "color": "#aaaaaa",  # Gray
                "icon": "○",
                "text": _("Inactive"),
                "tooltip": _("Status: Inactive or disabled")
            }
        }

        # Create icon label (always visible)
        self.icon_label = tb.Label(
            self,
            text="",
            font=("Segoe UI", 12),
            width=2
        )
        self.icon_label.pack(side=LEFT, padx=(0, 5))

        # Create text label (optional)
        if show_text:
            self.text_label = tb.Label(
                self,
                text="",
                font=("Segoe UI", 10)
            )
            self.text_label.pack(side=LEFT)
        else:
            self.text_label = None

        # Initialize with default status
        self.set_status(status)

    def set_status(self, status: str) -> None:
        """
        Set the indicator status and update all visual cues.

        Args:
            status: One of "ok", "warning", "error", "inactive"
        """
        self.status = status
        config = self.status_configs.get(status, self.status_configs["inactive"])

        # Update icon (with color)
        self.icon_label.configure(
            text=config["icon"],
            foreground=config["color"]
        )

        # Update text label if present
        if self.text_label:
            self.text_label.configure(
                text=config["text"],
                foreground=config["color"]
            )

        # Update tooltip (accessible description)
        try:
            from ttkbootstrap.tooltip import ToolTip
            # Remove old tooltip if exists
            if hasattr(self, '_tooltip'):
                self._tooltip.hide_tip()

            # Create new tooltip
            self._tooltip = ToolTip(
                self.icon_label,
                text=config["tooltip"],
                bootstyle="info"
            )
        except:
            pass  # Tooltip is optional


class KeybindField(tb.Frame):
    """Field for capturing keyboard shortcuts."""

    def __init__(self, master, current_keys=None, callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.callback = callback

        # Current keybind
        self.key_list = current_keys or []

        # Display entry
        self.entry = tb.Entry(self)
        self.entry.pack(side=LEFT, fill=X, expand=True)
        self.entry.bind("<Key>", self._on_key)
        self.entry.bind("<KeyRelease>", self._on_key_release)

        # Update display
        self._update_display()

        # Clear button
        tb.Button(self, text="✕", width=3, command=self.clear).pack(side=LEFT, padx=2)

        # Recording state
        self.recording = False

    def _update_display(self) -> None:
        """Update the displayed keybind text."""
        if not self.key_list:
            self.entry.delete(0, END)
            self.entry.insert(0, _("<Press keys>"))
        else:
            text = "+".join(self.key_list)
            self.entry.delete(0, END)
            self.entry.insert(0, text)

    def _on_key(self, event) -> str:
        """Handle key press events."""
        if not self.recording:
            self.recording = True
            self.key_list = []

        # Get key name
        key = self._normalize_key(event.keysym)

        # Add to active keys if not already there
        if key not in self.key_list:
            self.key_list.append(key)

        self._update_display()
        return "break"  # Prevent default behavior

    def _on_key_release(self, event) -> None:
        """Handle key release events."""
        self.recording = False

        # Trigger callback with new keybind
        if self.callback and self.key_list:
            self.callback(self.key_list)

    def _normalize_key(self, key: str) -> str:
        """Normalize key names to standard format."""
        key = key.capitalize()

        # Handle special keys
        key_map = {
            "Control_L": "Ctrl",
            "Control_R": "Ctrl",
            "Alt_L": "Alt",
            "Alt_R": "Alt",
            "Shift_L": "Shift",
            "Shift_R": "Shift",
            "Return": "Enter",
            "Escape": "Esc",
            "space": "Space",
        }

        return key_map.get(key, key)

    def set_keys(self, keys: list[str]) -> None:
        """Set the keybind externally."""
        self.key_list = keys
        self._update_display()

    def clear(self) -> None:
        """Clear the current keybind."""
        self.key_list = []
        self._update_display()
        if self.callback:
            self.callback([])
