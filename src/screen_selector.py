import time
import tkinter as tk
from tkinter import messagebox, simpledialog

import pyautogui

try:
    from screeninfo import get_monitors
except ImportError:
    get_monitors = None  # graceful fallback

try:
    from pynput import keyboard
except ImportError:
    keyboard = None  # graceful fallback


class ScreenSelector:
    def __init__(self):
        self.selected_region = None  # (x, y, w, h)
        self.monitor_idx = -1  # -1 means any
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None

    def select_region(self, callback=None):
        """Open a fullscreen overlay to select a region"""
        self.callback = callback

        # Prepare monitor layout
        self.monitors = []
        if get_monitors:
            for m in get_monitors():
                self.monitors.append(m)
        else:
            # Fallback – primary monitor only
            w, h = pyautogui.size()

            class Dummy:  # simple struct
                x = 0
                y = 0
                width = w
                height = h

            self.monitors.append(Dummy())

        # Ask which monitor (simple listbox if >1)
        if len(self.monitors) > 1:
            choice = simpledialog.askinteger(
                "Monitor",
                f"Select monitor index (1-{len(self.monitors)}):",
                minvalue=1,
                maxvalue=len(self.monitors),
            )
            if choice is None:
                self.cancel_selection(None)
                return None
            self.monitor_idx = choice - 1
        else:
            self.monitor_idx = 0

        m = self.monitors[self.monitor_idx]

        # Capture screenshot of that monitor to get width/height (could skip)
        pyautogui.screenshot(region=(m.x, m.y, m.width, m.height))
        self.screen_width = m.width
        self.screen_height = m.height

        # Create fullscreen window
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.root.configure(bg="black")
        self.root.attributes("-topmost", True)

        # Offset window to monitor origin
        self.root.geometry(f"{self.screen_width}x{self.screen_height}+{m.x}+{m.y}")

        # Create canvas
        self.canvas = tk.Canvas(
            self.root,
            width=self.screen_width,
            height=self.screen_height,
            highlightthickness=0,
            cursor="crosshair",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind events
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", self.cancel_selection)

        # Instructions
        instructions = tk.Label(
            self.root,
            text="Click and drag to select region. Press ESC to cancel.",
            fg="white",
            bg="black",
            font=("Arial", 16),
        )
        instructions.place(x=50, y=50)

        self.rectangle = None
        self.root.mainloop()

        return (self.selected_region, self.monitor_idx)

    def on_click(self, event):
        """Handle mouse click"""
        self.start_x = event.x
        self.start_y = event.y

        if self.rectangle:
            self.canvas.delete(self.rectangle)

    def on_drag(self, event):
        """Handle mouse drag"""
        if self.start_x and self.start_y:
            if self.rectangle:
                self.canvas.delete(self.rectangle)

            self.rectangle = self.canvas.create_rectangle(
                self.start_x,
                self.start_y,
                event.x,
                event.y,
                outline="red",
                width=2,
                fill="red",
                stipple="gray50",
            )

    def on_release(self, event):
        """Handle mouse release"""
        self.end_x = event.x
        self.end_y = event.y

        if self.start_x and self.start_y and self.end_x and self.end_y:
            # Calculate region bounds
            x1 = min(self.start_x, self.end_x)
            y1 = min(self.start_y, self.end_y)
            x2 = max(self.start_x, self.end_x)
            y2 = max(self.start_y, self.end_y)

            width = x2 - x1
            height = y2 - y1

            if width > 10 and height > 10:  # Minimum size
                # Convert to absolute coordinates within virtual screen
                m = self.monitors[self.monitor_idx]
                abs_x = x1 + m.x
                abs_y = y1 + m.y
                self.selected_region = (abs_x, abs_y, width, height)
                self.root.quit()
                self.root.destroy()

                if self.callback:
                    self.callback((self.selected_region, self.monitor_idx))
            else:
                messagebox.showwarning("Selection too small", "Please select a larger region")

    def cancel_selection(self, event):
        """Cancel selection"""
        self.selected_region = None
        self.root.quit()
        self.root.destroy()

    def capture_region_as_image(self, region, save_path):
        """Capture the selected region and save as image"""
        x, y, width, height = region
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        screenshot.save(save_path)
        return save_path


class ClickRecorder:
    def __init__(self):
        self.recorded_clicks = []
        self.recording = False

    def start_recording(self, callback=None):
        """Start recording clicks"""
        self.callback = callback
        self.recorded_clicks = []
        self.recording = True

        # Create overlay window for instructions
        self.root = tk.Tk()
        self.root.title("Click Recorder")
        self.root.geometry("300x150")
        self.root.attributes("-topmost", True)

        tk.Label(self.root, text="Click Recording Active", font=("Arial", 14, "bold")).pack(pady=10)

        tk.Label(
            self.root,
            text="Click anywhere to record positions.\nPress 'Stop' when done.",
            font=("Arial", 10),
        ).pack(pady=5)

        stop_button = tk.Button(
            self.root,
            text="Stop Recording",
            command=self.stop_recording,
            bg="red",
            fg="white",
            font=("Arial", 12),
        )
        stop_button.pack(pady=10)

        # Start listening for clicks
        from pynput import mouse

        self.mouse = mouse
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()

        self.root.mainloop()

        return self.recorded_clicks

    def on_click(self, x, y, button, pressed):
        """Handle mouse click events"""
        if pressed and self.recording:
            click_type = "left" if button == self.mouse.Button.left else "right"
            self.recorded_clicks.append(
                {"x": x, "y": y, "button": click_type, "timestamp": time.time()}
            )
            print(f"Recorded {click_type} click at ({x}, {y})")

    def stop_recording(self):
        """Stop recording clicks"""
        self.recording = False
        if hasattr(self, "listener"):
            self.listener.stop()

        self.root.quit()
        self.root.destroy()

        if self.callback:
            self.callback(self.recorded_clicks)


class KeyRecorder:
    def __init__(self):
        self.recorded_keys = []
        self.recording = False

    def start_recording(self, callback=None):
        """Start recording keystrokes"""
        self.callback = callback
        self.recorded_keys = []
        self.recording = True

        # Create overlay window for instructions
        self.root = tk.Tk()
        self.root.title("Key Recorder")
        self.root.geometry("300x200")
        self.root.attributes("-topmost", True)

        tk.Label(self.root, text="Key Recording Active", font=("Arial", 14, "bold")).pack(pady=10)

        tk.Label(
            self.root,
            text="Type to record keystrokes.\nPress 'Stop' when done.",
            font=("Arial", 10),
        ).pack(pady=5)

        # Text display
        self.text_display = tk.Text(self.root, height=5, width=30)
        self.text_display.pack(pady=5)

        stop_button = tk.Button(
            self.root,
            text="Stop Recording",
            command=self.stop_recording,
            bg="red",
            fg="white",
            font=("Arial", 12),
        )
        stop_button.pack(pady=5)

        # Start listening for keys
        if keyboard:
            self.listener = keyboard.Listener(
                on_press=self.on_key_press, on_release=self.on_key_release
            )
            self.listener.start()

        self.root.mainloop()

        return self.recorded_keys

    def on_key_press(self, key):
        """Handle key press events"""
        if not self.recording:
            return

        try:
            key_char = key.char
            if key_char:
                self.recorded_keys.append(
                    {"type": "char", "key": key_char, "timestamp": time.time()}
                )
                self.text_display.insert(tk.END, key_char)
                self.text_display.see(tk.END)
        except AttributeError:
            # Special keys
            key_name = str(key).replace("Key.", "")
            self.recorded_keys.append(
                {"type": "special", "key": key_name, "timestamp": time.time()}
            )
            self.text_display.insert(tk.END, f"[{key_name}]")
            self.text_display.see(tk.END)

    def on_key_release(self, key):
        """Handle key release events"""
        if keyboard and key == keyboard.Key.esc and self.recording:
            self.stop_recording()

    def stop_recording(self):
        """Stop recording keys"""
        self.recording = False
        if hasattr(self, "listener"):
            self.listener.stop()

        self.root.quit()
        self.root.destroy()

        if self.callback:
            self.callback(self.recorded_keys)
