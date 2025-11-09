#!/usr/bin/env python3
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.font import Font

import pyautogui
import pynput
from PIL import Image, ImageTk
from pynput import keyboard, mouse

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


class ToggleSwitch(tk.Canvas):
    """Custom modern toggle switch widget"""

    def __init__(
        self, parent, width=60, height=30, bg="#FFFFFF", fg="#0078D7", command=None, **kwargs
    ):
        # Get parent's background color safely
        try:
            parent_bg = parent["background"]
        except (tk.TclError, KeyError):
            try:
                parent_bg = parent.cget("background")
            except (tk.TclError, AttributeError):
                parent_bg = "#F0F0F0"  # Default background

        super().__init__(
            parent, width=width, height=height, background=parent_bg, highlightthickness=0, **kwargs
        )
        self.command = command
        self.is_on = False
        self.on_color = fg
        self.off_color = "#CCCCCC"
        self.handle_color = "#FFFFFF"
        self.width = width
        self.height = height
        self.r = height // 2
        self.draw_switch()

        # Bind events for better UX
        self.bind("<Button-1>", self.toggle)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        """Draw a rounded rectangle on the canvas"""
        points = [
            x1 + r,
            y1,
            x2 - r,
            y1,
            x2,
            y1,
            x2,
            y1 + r,
            x2,
            y2 - r,
            x2,
            y2,
            x2 - r,
            y2,
            x1 + r,
            y2,
            x1,
            y2,
            x1,
            y2 - r,
            x1,
            y1 + r,
            x1,
            y1,
        ]
        return self.create_polygon(points, **kwargs, smooth=True)

    def draw_switch(self):
        """Draw the switch in its current state"""
        self.delete("all")
        bg_color = self.on_color if self.is_on else self.off_color

        # Draw the background track
        self.create_rounded_rect(0, 0, self.width, self.height, self.r, fill=bg_color, outline="")

        # Calculate handle position
        x0 = self.width - self.height + 3 if self.is_on else 3
        y0 = 3
        x1 = x0 + self.height - 6
        y1 = self.height - 3

        # Draw the handle
        # Use a solid dark gray for shadow instead of transparent color
        self.create_oval(x0 + 1, y0 + 1, x1 + 1, y1 + 1, fill="#DDDDDD", outline="")
        self.create_oval(x0, y0, x1, y1, fill=self.handle_color, outline="")

    def toggle(self, event=None):
        """Toggle the switch state and call command"""
        self.is_on = not self.is_on
        self.draw_switch()
        if self.command:
            self.command(self.is_on)

    def set(self, value):
        """Set the toggle state without triggering the callback"""
        self.is_on = bool(value)
        self.draw_switch()

    def on_enter(self, event=None):
        """Mouse enter event - highlight the switch"""
        self.config(cursor="hand2")

    def on_leave(self, event=None):
        """Mouse leave event - restore normal appearance"""
        self.config(cursor="")


from src.action_executor import (
    Action,
    ActionExecutor,
    ActionType,
    create_click_action,
    create_click_image_action,
    create_double_click_action,
    create_key_combination_action,
    create_key_press_action,
    create_right_click_action,
    create_scroll_action,
    create_type_text_action,
    create_wait_action,
)
from src.automator import ScreenAutomator
from src.context_automator import ContextAwareAutomator
from src.screen_selector import KeyRecorder, ScreenSelector
from src.window_manager import WindowInfo, WindowManager
from utils.logging import get_logger, setup_gui_logging

# Using our own implementation of ClickRecorder for better control


class CustomScreenSelector:
    def __init__(self):
        self.root = tk.Toplevel()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")

        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.selected_region = None

        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Escape>", self.cancel)
        self.root.bind("<Escape>", self.cancel)

        # Instructions
        self.canvas.create_text(
            self.root.winfo_screenwidth() // 2,
            self.root.winfo_screenheight() // 2,
            text="Click and drag to select a region. Press ESC to cancel.",
            fill="white",
            font=("Arial", 24),
        )

    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, outline="white", width=2
        )

    def on_mouse_drag(self, event):
        if self.rect_id:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_mouse_up(self, event):
        end_x = event.x
        end_y = event.y

        # Ensure coordinates are ordered correctly
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        # Store the selected region
        self.selected_region = (x1, y1, x2 - x1, y2 - y1)  # x, y, width, height
        self.root.destroy()

    def cancel(self, event=None):
        self.selected_region = None
        self.root.destroy()

    def select_region(self):
        self.root.wait_window()
        return self.selected_region

    def capture_region_as_image(self, region, save_path):
        if not region:
            return None

        x, y, width, height = region
        screenshot = pyautogui.screenshot(region=region)
        screenshot.save(save_path)
        return save_path


class ClickRecorder:
    def __init__(self):
        self.clicks = []
        self.recording = False
        self.exclude_region = None

    def on_click(self, x, y, button, pressed):
        if pressed:
            # Skip if the click is within the excluded region (stop button)
            if self.exclude_region:
                x1, y1, x2, y2 = self.exclude_region
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return True  # Continue listening

            if button == mouse.Button.left:
                self.clicks.append({"x": x, "y": y, "button": "left"})
            elif button == mouse.Button.right:
                self.clicks.append({"x": x, "y": y, "button": "right"})

        return True  # Continue listening

    def start_recording(self):
        self.recording = True

        # Display recording instructions
        messagebox.showinfo(
            "Recording", "Click on screen positions to record. Press ESC to stop recording."
        )

        with mouse.Listener(on_click=self.on_click) as listener:
            listener.join()

        return self.clicks

    def record_until(self, stop_condition, exclude_region=None):
        """Record clicks until stop_condition returns True"""
        self.clicks = []
        self.recording = True
        self.exclude_region = exclude_region

        with mouse.Listener(on_click=self.on_click) as listener:
            while self.recording and not stop_condition():
                time.sleep(0.1)
            listener.stop()

        return self.clicks


class ScreenAutomatorGUI:
    """Main GUI class for the Screen Automator application"""

    def __init__(self):
        """Initialize the GUI"""
        self.root = tk.Tk()
        self.root.title("Screen Automator")

        # Set window size and position - increased for better visibility
        window_width = 1400
        window_height = 900

        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calculate position to center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # Set geometry with centered position
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(1300, 800)  # Increased minimum size to ensure all elements are visible

        # Global keyboard shortcuts
        self.root.bind("<Control-t>", lambda e: self.toggle_all_rules())

        # Initialize window management
        self.window_manager = WindowManager()

        # Initialize automator (always use context-aware automator)
        self.automator = ContextAwareAutomator()
        self.setup_automator_callbacks()

        # Setup centralized logging to route all logs to GUI activity log
        setup_gui_logging(self._gui_log_callback)

        # Available windows cache
        self.available_windows = []

        # Current rule being edited
        self.current_rule = None
        self.current_actions = []

        # Capture coordinates for sanity check
        # These will be set when capturing a screen region
        # and used when saving a rule

        # Define fonts used throughout the application
        self.title_font = ("Segoe UI", 16, "bold")
        self.heading_font = ("Segoe UI", 12, "bold")
        self.normal_font = ("Segoe UI", 10)
        self.small_font = ("Segoe UI", 9)

        # Set application styling
        self.set_style()

        # Create main container with padding
        main_container = ttk.Frame(self.root, padding="10 10 10 10")
        main_container.pack(fill=tk.BOTH, expand=True)

        # App title and header
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(header_frame, text="Screen Automator", font=self.title_font)
        title_label.pack(side=tk.LEFT)

        # Create notebook for tabs with modern styling
        self.notebook = ttk.Notebook(main_container, style="Modern.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create frames for tabs
        self.rules_frame = ttk.Frame(self.notebook, style="Tab.TFrame", padding=5)
        self.editor_frame = ttk.Frame(self.notebook, style="Tab.TFrame", padding=5)
        self.monitor_frame = ttk.Frame(self.notebook, style="Tab.TFrame", padding=5)

        # Add tabs to notebook
        self.notebook.add(self.rules_frame, text="Rules")
        self.notebook.add(self.editor_frame, text="Rule Editor")
        self.notebook.add(self.monitor_frame, text="Monitoring")

        # Set up tab content
        self.setup_rules_tab()
        self.setup_editor_tab()
        self.setup_monitor_tab()

        # Status bar
        status_frame = ttk.Frame(self.root, style="StatusBar.TFrame")
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))

        ttk.Separator(status_frame, orient=tk.HORIZONTAL).pack(fill=tk.X)
        status_bar = ttk.Frame(status_frame)
        status_bar.pack(fill=tk.X, padx=5, pady=2)

        self.status_label = ttk.Label(status_bar, text="Ready", font=self.small_font)
        self.status_label.pack(side=tk.LEFT)

        version_label = ttk.Label(
            status_bar, text="v1.0", font=self.small_font, foreground="#888888"
        )
        version_label.pack(side=tk.RIGHT)

        # Start status update thread
        self.status_thread = threading.Thread(target=self.update_status_loop)
        self.status_thread.daemon = True
        self.status_thread.start()

    def set_style(self):
        """Set modern style for the application"""
        style = ttk.Style()

        # Configure colors
        bg_color = "#F5F5F5"  # Light gray background
        accent_color = "#0078D7"  # Microsoft blue accent
        text_color = "#333333"  # Dark gray text
        light_accent = "#E1F0FF"  # Light accent for hover effects

        # Apply system theme as base
        style.theme_use("clam")

        # Configure the root window
        self.root.configure(background=bg_color)

        # Configure general styles
        style.configure(".", font=("Segoe UI", 10), background=bg_color, foreground=text_color)

        # Frame styles
        style.configure("TFrame", background=bg_color)
        style.configure("Tab.TFrame", background=bg_color)
        style.configure("StatusBar.TFrame", background=bg_color)

        # Label styles
        style.configure("TLabel", background=bg_color, foreground=text_color)

        # Button styles
        style.configure("TButton", background=bg_color, foreground=text_color, padding=(5, 2))
        style.map(
            "TButton",
            background=[("active", light_accent), ("pressed", accent_color)],
            foreground=[("pressed", "white")],
        )

        # Accent button style
        style.configure("Accent.TButton", font=self.normal_font, padding=(5, 2))
        style.map(
            "Accent.TButton",
            foreground=[("!disabled", "white")],
            background=[("!disabled", accent_color), ("active", "#005EA8"), ("pressed", "#004C85")],
        )

        # Entry style
        style.configure("TEntry", fieldbackground="white", borderwidth=1)

        # Notebook style
        style.configure("Modern.TNotebook", background=bg_color, tabmargins=[2, 5, 2, 0])
        style.configure(
            "Modern.TNotebook.Tab", background=bg_color, padding=[10, 2], font=("Segoe UI", 10)
        )
        style.map(
            "Modern.TNotebook.Tab",
            background=[("selected", "white"), ("active", light_accent)],
            expand=[("selected", [1, 1, 1, 0])],
        )

        # Treeview style
        style.configure(
            "Treeview",
            background="white",
            foreground=text_color,
            fieldbackground="white",
            borderwidth=1,
            rowheight=25,
        )
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.map(
            "Treeview",
            background=[("selected", light_accent)],
            foreground=[("selected", accent_color)],
        )

        # LabelFrame style
        style.configure("TLabelframe", background=bg_color)
        style.configure(
            "TLabelframe.Label",
            background=bg_color,
            foreground=text_color,
            font=("Segoe UI", 9, "bold"),
        )

    def setup_automator_callbacks(self):
        """Setup callbacks for the current automator instance"""
        self.automator.on_rule_triggered = self.on_rule_triggered
        self.automator.on_error = self.on_error
        self.automator.on_rule_disabled = self.on_rule_disabled

    def setup_rules_tab(self):
        """Setup the rules management tab"""
        # Main container with padding
        main_container = ttk.Frame(self.rules_frame, padding="10 10 10 10")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Header section with title and toolbar
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Section title
        title_label = ttk.Label(header_frame, text="Automation Rules", font=self.heading_font)
        title_label.pack(side=tk.LEFT, pady=5)

        # Toolbar with improved layout
        toolbar = ttk.Frame(header_frame)
        toolbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Primary action buttons (most important)
        primary_buttons = ttk.Frame(toolbar)
        primary_buttons.pack(side=tk.LEFT, padx=(0, 8))

        new_btn = ttk.Button(
            primary_buttons, text="+ New Rule", command=self.new_rule, style="Accent.TButton"
        )
        new_btn.pack(side=tk.LEFT, padx=1)

        ttk.Button(primary_buttons, text="Edit", command=self.edit_rule).pack(side=tk.LEFT, padx=1)
        ttk.Button(primary_buttons, text="Delete", command=self.delete_rule).pack(
            side=tk.LEFT, padx=1
        )

        # Secondary action buttons
        secondary_buttons = ttk.Frame(toolbar)
        secondary_buttons.pack(side=tk.LEFT)

        ttk.Button(secondary_buttons, text="Test", command=self.test_rule).pack(
            side=tk.LEFT, padx=1
        )
        ttk.Button(
            secondary_buttons, text="🔥 Fire Up", command=self.fire_up_rule, style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=1)
        ttk.Button(secondary_buttons, text="Refresh", command=self.refresh_rules).pack(
            side=tk.LEFT, padx=1
        )

        # Toggle All button positioned above the rules table
        toggle_all_frame = ttk.Frame(main_container)
        toggle_all_frame.pack(fill=tk.X, pady=(0, 5))

        toggle_all_btn = ttk.Button(
            toggle_all_frame, text="🔄 Toggle All (Ctrl+T)", command=self.toggle_all_rules
        )
        toggle_all_btn.pack(side=tk.LEFT)

        # Rules list frame
        list_frame = ttk.Frame(main_container)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for rules with toggle column integrated
        self.rules_tree = ttk.Treeview(
            list_frame,
            columns=("Name", "Status", "Type", "Trigger", "Actions", "Window"),
            show="tree headings",
        )
        # Configure headings with proper alignment - Toggle is now #0 column
        self.rules_tree.heading("#0", text="Enable", anchor="center")
        self.rules_tree.heading("Name", text="Name", anchor="w")
        self.rules_tree.heading("Status", text="Status", anchor="center")
        self.rules_tree.heading("Type", text="Type", anchor="center")
        self.rules_tree.heading("Trigger", text="Trigger", anchor="w")
        self.rules_tree.heading("Actions", text="Actions", anchor="center")
        self.rules_tree.heading("Window", text="Window Target", anchor="w")

        # Configure columns with better proportions and alignment
        self.rules_tree.column(
            "#0", width=70, minwidth=70, anchor="center"
        )  # Toggle column (leftmost)
        self.rules_tree.column("Name", width=160, minwidth=120, anchor="w")  # Name column
        self.rules_tree.column("Status", width=70, minwidth=60, anchor="center")
        self.rules_tree.column("Type", width=90, minwidth=80, anchor="center")
        self.rules_tree.column("Trigger", width=140, minwidth=100, anchor="w")
        self.rules_tree.column("Actions", width=60, minwidth=50, anchor="center")
        self.rules_tree.column(
            "Window", width=150, minwidth=100, anchor="w"
        )  # Window Target column

        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.rules_tree.yview)
        self.rules_tree.configure(yscrollcommand=scrollbar.set)

        # Pack with proper spacing to match toggle switches
        self.rules_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 0), pady=1)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=1)

        # Context menu
        self.rules_tree.bind("<Button-3>", self.show_context_menu)

        # Drag and drop functionality
        self.rules_tree.bind("<Button-1>", self.on_tree_press)
        self.rules_tree.bind("<B1-Motion>", self.on_tree_motion)
        self.rules_tree.bind("<ButtonRelease-1>", self.on_tree_release)

        self.drag_data = {"item": None, "target": None}

        # Load initial rules
        self.refresh_rules()

        # Bind double-click to edit
        self.rules_tree.bind("<Double-1>", lambda e: self.edit_rule())

        # Bind right-click for context menu
        self.rules_tree.bind("<Button-3>", self.show_context_menu)

        # Bind keyboard shortcut for toggle all (Ctrl+T)
        self.rules_tree.bind("<Control-t>", lambda e: self.toggle_all_rules())
        self.rules_tree.focus_set()  # Allow the treeview to receive keyboard events

        # Bind click handler for toggle column
        self.rules_tree.bind("<Button-1>", self.on_toggle_click)

        # Variables for drag and drop
        self.drag_source = None
        self.drag_target = None
        self.dragging = False

    def setup_editor_tab(self):
        """Setup the rule editor tab"""
        # Rule info section
        info_frame = ttk.LabelFrame(self.editor_frame, text="Rule Information")
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(info_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.name_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.name_var, width=30).grid(
            row=0, column=1, padx=5, pady=2
        )

        ttk.Label(info_frame, text="Description:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.desc_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.desc_var, width=30).grid(
            row=1, column=1, padx=5, pady=2
        )

        # Priority note (now managed by drag-and-drop)
        priority_note = ttk.Label(
            info_frame,
            text="Note: Rule priority is determined by the order in the rules list. Drag and drop to reorder.",
        )
        priority_note.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        # Auto-disable options
        ttk.Label(info_frame, text="Disable after executions:").grid(
            row=3, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.disable_after_var = tk.IntVar(value=0)
        disable_frame = ttk.Frame(info_frame)
        disable_frame.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Spinbox(
            disable_frame, from_=0, to=9999, textvariable=self.disable_after_var, width=10
        ).pack(side=tk.LEFT)
        ttk.Label(disable_frame, text="(0 = never disable)").pack(side=tk.LEFT, padx=5)

        # Disable on image detection
        ttk.Label(info_frame, text="Disable on image:").grid(
            row=4, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.disable_image_var = tk.StringVar()
        disable_image_frame = ttk.Frame(info_frame)
        disable_image_frame.grid(row=4, column=1, sticky=tk.W + tk.E, padx=5, pady=2)

        ttk.Entry(disable_image_frame, textvariable=self.disable_image_var, width=25).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(disable_image_frame, text="Browse...", command=self.browse_disable_image).pack(
            side=tk.LEFT, padx=(5, 0)
        )

        # Condition type section
        condition_frame = ttk.LabelFrame(self.editor_frame, text="Rule Condition")
        condition_frame.pack(fill=tk.X, padx=5, pady=5)

        self.condition_var = tk.StringVar(value="image")
        ttk.Radiobutton(
            condition_frame,
            text="Trigger on Image Detection",
            variable=self.condition_var,
            value="image",
            command=self.on_condition_change,
        ).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(
            condition_frame,
            text="Trigger when Screen Unchanged",
            variable=self.condition_var,
            value="screen_unchanged",
            command=self.on_condition_change,
        ).pack(anchor=tk.W, pady=2)

        # Timeout for screen unchanged condition
        timeout_frame = ttk.Frame(condition_frame)
        timeout_frame.pack(fill=tk.X, pady=5)

        ttk.Label(timeout_frame, text="Timeout (minutes):").pack(side=tk.LEFT, padx=5)
        self.timeout_var = tk.DoubleVar(value=5.0)
        self.timeout_spinbox = ttk.Spinbox(
            timeout_frame,
            from_=0.5,
            to=60.0,
            increment=0.5,
            textvariable=self.timeout_var,
            width=10,
        )
        self.timeout_spinbox.pack(side=tk.LEFT, padx=5)

        # Window targeting section
        window_frame = ttk.LabelFrame(self.editor_frame, text="Window Targeting (Optional)")
        window_frame.pack(fill=tk.X, padx=5, pady=5)

        # Simple window selector with explanation
        select_frame = ttk.Frame(window_frame)
        select_frame.pack(fill=tk.X, pady=5)

        select_btn = ttk.Button(
            select_frame,
            text="Select Target Window",
            command=self.select_target_window,
            style="Accent.TButton",
        )
        select_btn.pack(side=tk.LEFT, padx=10)

        ttk.Label(select_frame, text="Click to choose which window this rule applies to").pack(
            side=tk.LEFT, padx=5
        )

        # Window info display
        info_frame = ttk.Frame(window_frame)
        info_frame.pack(fill=tk.X, pady=5)

        self.window_info_var = tk.StringVar(
            value="No window selected (rule will apply to any window)"
        )
        window_info_label = ttk.Label(
            info_frame, textvariable=self.window_info_var, wraplength=400, justify=tk.LEFT
        )
        window_info_label.pack(fill=tk.X, padx=10, pady=5)

        # Cluster group (keep this as it's useful for organization)
        cluster_frame = ttk.Frame(window_frame)
        cluster_frame.pack(fill=tk.X, pady=5)

        ttk.Label(cluster_frame, text="Cluster Group:").pack(side=tk.LEFT, padx=5)
        self.cluster_group_var = tk.StringVar()
        cluster_combo = ttk.Combobox(cluster_frame, textvariable=self.cluster_group_var, width=25)
        cluster_combo.pack(side=tk.LEFT, padx=5)

        # Set common cluster groups
        cluster_combo["values"] = (
            "",
            "browsers",
            "text_editors",
            "dev_tools",
            "communication",
            "media",
            "utilities",
        )
        ttk.Label(cluster_frame, text="(Optional - for organizing related rules)").pack(
            side=tk.LEFT, padx=5
        )

        # Hidden variables for backend functionality
        self.window_id_method_var = tk.StringVar(value="auto")
        self.target_window_class_var = tk.StringVar()
        self.target_window_process_var = tk.StringVar()
        self.target_window_title_var = tk.StringVar()
        self.window_exact_match_var = tk.BooleanVar()

        # Image section (for image-based rules)
        self.image_frame = ttk.LabelFrame(self.editor_frame, text="Trigger Image")
        self.image_frame.pack(fill=tk.X, padx=5, pady=5)

        img_buttons = ttk.Frame(self.image_frame)
        img_buttons.pack(fill=tk.X, pady=5)

        ttk.Button(img_buttons, text="Select Image File", command=self.select_image_file).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(
            img_buttons, text="Capture Screen Region", command=self.capture_screen_region
        ).pack(side=tk.LEFT, padx=5)

        self.image_path_var = tk.StringVar()
        ttk.Label(self.image_frame, textvariable=self.image_path_var, foreground="blue").pack(
            pady=5
        )

        # Image preview
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack(pady=5)

        # Actions section
        actions_frame = ttk.LabelFrame(self.editor_frame, text="Actions")
        actions_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Action buttons with improved layout
        action_buttons = ttk.Frame(actions_frame)
        action_buttons.pack(fill=tk.X, pady=5)

        # Row 1: Recording and basic actions
        action_row1 = ttk.Frame(action_buttons)
        action_row1.pack(fill=tk.X, pady=(0, 3))

        ttk.Button(action_row1, text="Record Clicks", command=self.record_clicks).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(action_row1, text="Record Keys", command=self.record_keys).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(action_row1, text="Add Wait", command=self.add_wait_action).pack(
            side=tk.LEFT, padx=2
        )

        # Row 2: Advanced actions and controls
        action_row2 = ttk.Frame(action_buttons)
        action_row2.pack(fill=tk.X)

        ttk.Button(action_row2, text="Add Manual", command=self.add_manual_action).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(action_row2, text="Click on Image", command=self.add_click_image_action).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(action_row2, text="Clear All", command=self.clear_actions).pack(
            side=tk.LEFT, padx=2
        )

        # Actions list
        actions_list_frame = ttk.Frame(actions_frame)
        actions_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.actions_listbox = tk.Listbox(actions_list_frame, height=8)
        actions_scrollbar = ttk.Scrollbar(
            actions_list_frame, orient=tk.VERTICAL, command=self.actions_listbox.yview
        )
        self.actions_listbox.configure(yscrollcommand=actions_scrollbar.set)

        self.actions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        actions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Action list controls
        action_controls = ttk.Frame(actions_frame)
        action_controls.pack(fill=tk.X, pady=5)

        ttk.Button(action_controls, text="Edit Selected", command=self.edit_action).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(action_controls, text="Remove Selected", command=self.remove_action).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(action_controls, text="Move Up", command=self.move_action_up).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(action_controls, text="Move Down", command=self.move_action_down).pack(
            side=tk.LEFT, padx=5
        )

        # Save/Cancel buttons
        save_frame = ttk.Frame(self.editor_frame)
        save_frame.pack(fill=tk.X, pady=5)

        ttk.Button(save_frame, text="Save Rule", command=self.save_rule).pack(side=tk.RIGHT, padx=5)
        ttk.Button(save_frame, text="Cancel", command=self.cancel_edit).pack(side=tk.RIGHT, padx=5)

    def setup_monitor_tab(self):
        """Setup the monitoring tab with modern styling"""
        # Main container with padding
        main_container = ttk.Frame(self.monitor_frame, padding="10 10 10 10")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Header with title
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Section title
        title_label = ttk.Label(header_frame, text="Monitoring", font=self.heading_font)
        title_label.pack(side=tk.LEFT, pady=5)

        # Header controls
        header_controls = ttk.Frame(header_frame)
        header_controls.pack(side=tk.RIGHT)

        # Add sort button
        ttk.Button(
            header_controls, text="View Rules by Priority", command=self.show_priority_list
        ).pack(side=tk.LEFT, padx=5)

        # Top section with status and controls
        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill=tk.X, pady=5)

        # Status indicator
        status_frame = ttk.Frame(top_frame)
        status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(status_frame, text="Status:", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        self.status_var = tk.StringVar(value="Stopped")
        status_label = ttk.Label(
            status_frame, textvariable=self.status_var, font=("Segoe UI", 11, "bold")
        )
        status_label.pack(side=tk.LEFT, padx=5)

        # Action counter indicator
        self.action_counter_var = tk.StringVar(value="")
        action_counter_label = ttk.Label(
            status_frame,
            textvariable=self.action_counter_var,
            font=self.normal_font,
            foreground="#666666",
        )
        action_counter_label.pack(side=tk.LEFT, padx=10)

        # Control buttons with modern styling
        control_frame = ttk.Frame(top_frame)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.toggle_monitoring_button = ttk.Button(
            control_frame, text="▶ Start", command=self.toggle_monitoring, style="Accent.TButton"
        )
        self.toggle_monitoring_button.pack(side=tk.LEFT, padx=5)

        # Schedule button
        self.schedule_button = ttk.Button(
            control_frame, text="⏰ Schedule", command=self.schedule_monitoring, style="TButton"
        )
        self.schedule_button.pack(side=tk.LEFT, padx=5)

        # Schedule status variables
        self.scheduled_timer = None
        self.schedule_active = False

        # Settings section
        settings_frame = ttk.LabelFrame(main_container, text="Settings", padding="10 5 10 10")
        settings_frame.pack(fill=tk.X, pady=10)

        settings_grid = ttk.Frame(settings_frame)
        settings_grid.pack(fill=tk.X)

        # Check interval setting
        ttk.Label(settings_grid, text="Check Interval:", font=self.normal_font).grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )

        interval_frame = ttk.Frame(settings_grid)
        interval_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        self.interval_var = tk.DoubleVar(value=10.0)
        interval_spin = ttk.Spinbox(
            interval_frame,
            from_=0.1,
            to=10.0,
            increment=0.1,
            textvariable=self.interval_var,
            width=10,
        )
        interval_spin.pack(side=tk.LEFT)

        ttk.Label(interval_frame, text="seconds").pack(side=tk.LEFT, padx=5)

        # Note: Action limits are now configured per-rule in rule settings
        ttk.Label(settings_grid, text="Note:", font=self.normal_font).grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        ttk.Label(
            settings_grid, text="Action limits are now configured per-rule", font=self.normal_font
        ).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # Apply and Reset buttons
        button_frame = ttk.Frame(settings_grid)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)

        ttk.Button(button_frame, text="Apply Settings", command=self.apply_settings).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Reset Counter", command=self.reset_action_counter).pack(
            side=tk.LEFT, padx=5
        )

        # Log section with modern styling
        log_frame = ttk.LabelFrame(main_container, text="Activity Log", padding="10 5 10 10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_container,
            height=15,
            state=tk.DISABLED,
            font=self.small_font,
            bg="#FFFFFF",
            borderwidth=1,
            relief="solid",
        )

        log_scrollbar = ttk.Scrollbar(
            log_container, orient=tk.VERTICAL, command=self.log_text.yview
        )
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add clear log button
        log_toolbar = ttk.Frame(log_frame)
        log_toolbar.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(log_toolbar, text="Clear Log", command=self.clear_log).pack(side=tk.RIGHT)

    def clear_log(self):
        """Clear the activity log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log_message("Log cleared")

    def log_message(self, message):
        """Add message to log with proper formatting"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)

        # First insert timestamp in gray
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")

        # Then insert the message
        if "error" in message.lower() or "failed" in message.lower() or "❌" in message:
            self.log_text.insert(tk.END, f"{message}\n", "error")
        elif "target window not found" in message.lower() or "⚠️" in message:
            self.log_text.insert(tk.END, f"{message}\n", "important_warning")
        elif "success" in message.lower() or "enabled" in message.lower() or "✅" in message:
            self.log_text.insert(tk.END, f"{message}\n", "success")
        elif "disabled" in message.lower() or "stopped" in message.lower():
            self.log_text.insert(tk.END, f"{message}\n", "warning")
        elif "window" in message.lower() and "found" in message.lower():
            self.log_text.insert(tk.END, f"{message}\n", "window_info")
        elif "switched to" in message.lower() or "context" in message.lower():
            self.log_text.insert(tk.END, f"{message}\n", "context_info")
        else:
            self.log_text.insert(tk.END, f"{message}\n", "normal")

        # Create tags for colorization if they don't exist
        if not hasattr(self, "_log_tags_created"):
            self.log_text.tag_configure("timestamp", foreground="#888888")
            self.log_text.tag_configure("error", foreground="#FF0000")
            self.log_text.tag_configure(
                "important_warning", foreground="#FF6600", font=("Segoe UI", 10, "bold")
            )
            self.log_text.tag_configure("success", foreground="#008800")
            self.log_text.tag_configure("warning", foreground="#DD8800")
            self.log_text.tag_configure("window_info", foreground="#0066CC")
            self.log_text.tag_configure("context_info", foreground="#9900CC")
            self.log_text.tag_configure("normal", foreground="#000000")
            self._log_tags_created = True

        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _gui_log_callback(self, message):
        """Callback function for centralized logging system to display logs in GUI"""
        # This is called by the logging system to display messages in the activity log
        # Use try-safe approach since we might be called from different threads
        try:
            if hasattr(self, "root") and self.root:
                # Schedule the log message to be displayed in the main thread
                self.root.after_idle(lambda: self.log_message(message))
        except Exception:
            # Ignore errors to prevent logging loops
            pass

    def on_rule_triggered(self, rule):
        """Callback when rule is triggered"""
        self.log_message(f"Rule '{rule.name}' triggered!")

    def on_error(self, error_msg):
        """Callback for errors"""
        self.log_message(f"ERROR: {error_msg}")

        # Show popup for important window targeting errors
        if "target window not found" in error_msg.lower():
            window_name = error_msg.split("'")[1] if "'" in error_msg else "unknown"
            messagebox.showwarning(
                "Target Window Not Found",
                f"The window '{window_name}' targeted by one or more rules was not found.\n\n"
                f"This is why you're not seeing context switching happen.\n\n"
                f"Please either:\n"
                f"1. Open the target window, or\n"
                f"2. Edit your rules to target a window that is currently open.",
            )

    def on_rule_disabled(self, rule, reason):
        """Callback when a rule is automatically disabled"""
        self.log_message(f"Rule '{rule.name}' automatically disabled: {reason}")

        # Update the UI to reflect the disabled state
        self.refresh_rules()

    def toggle_rule(self, rule_id, is_enabled):
        """Toggle the enabled status of a rule"""
        rule = self.automator.rule_manager.get_rule(rule_id)
        if not rule:
            return

        # Update rule status in the database
        self.automator.rule_manager.update_rule(rule_id, enabled=is_enabled)

        # Update display in treeview without full refresh
        for item_id in self.rules_tree.get_children():
            if rule_id in self.rules_tree.item(item_id)["tags"]:
                # Update toggle column (#0 column - text)
                toggle_text = "✅ ON" if is_enabled else "❌ OFF"
                # Update status column (second regular column)
                status = "Active" if is_enabled else "Disabled"

                # Update the #0 column (text)
                self.rules_tree.item(item_id, text=toggle_text)

                # Update the status column (second in values array)
                current_values = list(self.rules_tree.item(item_id)["values"])
                current_values[1] = status  # Status column is now index 1
                self.rules_tree.item(item_id, values=tuple(current_values))

                # Update color styling
                if is_enabled:
                    self.rules_tree.tag_configure(f"enabled_{rule_id}", foreground="#008800")
                    self.rules_tree.item(item_id, tags=(rule_id, f"enabled_{rule_id}"))
                else:
                    self.rules_tree.tag_configure(f"disabled_{rule_id}", foreground="#888888")
                    self.rules_tree.item(item_id, tags=(rule_id, f"disabled_{rule_id}"))
                break

        # Log the status change
        rule_name = rule.name
        action = "enabled" if is_enabled else "disabled"
        self.log_message(f"Rule '{rule_name}' {action}")

    def on_tree_press(self, event):
        """Handle mouse button press on treeview for drag-and-drop"""
        # Get the item that was clicked
        item = self.rules_tree.identify_row(event.y)
        if not item:
            return

        # Remember the item we're dragging
        self.drag_source = item

    def on_tree_motion(self, event):
        """Handle mouse movement for drag-and-drop"""
        if not self.drag_source:
            return

        # Get the item under the cursor
        target = self.rules_tree.identify_row(event.y)
        if not target or target == self.drag_source:
            return

        # Show visual feedback - we're now dragging
        if not self.dragging:
            self.dragging = True
            self.rules_tree.selection_set(self.drag_source)

        # Find the target position
        target_y = self.rules_tree.bbox(target)[1]

        # Visual indicator of insert position
        self.rules_tree.tag_configure("insert_marker", background="#CCFFCC")
        for item in self.rules_tree.get_children():
            self.rules_tree.item(item, tags=())
        self.rules_tree.item(target, tags=("insert_marker",))

        self.drag_target = target

    def on_tree_release(self, event):
        """Handle mouse button release for drag-and-drop"""
        if not self.dragging or not self.drag_source or not self.drag_target:
            self.drag_source = None
            self.drag_target = None
            self.dragging = False
            return

        # Move the item and update priorities
        self.move_rule(self.drag_source, self.drag_target)

        # Reset drag variables
        self.drag_source = None
        self.drag_target = None
        self.dragging = False

        # Remove any highlighting
        for item in self.rules_tree.get_children():
            self.rules_tree.item(item, tags=())

    def move_rule(self, source_id, target_id):
        """Move a rule before another and update priorities"""
        # Get the original order of rules
        items = self.rules_tree.get_children()

        # Find the positions in the tree
        source_index = items.index(source_id)
        target_index = items.index(target_id)

        # Move the item in the tree
        self.rules_tree.move(source_id, "", target_index)

        # Update the priorities in the rule manager
        # Get the new order after moving
        new_items = self.rules_tree.get_children()

        # Assign new priorities (100, 200, 300, etc.) to maintain gaps for future insertions
        for i, item_id in enumerate(new_items):
            rule_id = self.rules_tree.item(item_id, "tags")[0]  # Get rule ID from tags
            if rule_id:
                self.automator.rule_manager.update_rule(rule_id, priority=(i + 1) * 100)

        self.log_message(f"Rule order updated")

    def toggle_all_rules(self):
        """Toggle all rules on or off based on current state"""
        rules = self.automator.rule_manager.list_rules()
        if not rules:
            self.log_message("No rules found to toggle")
            return

        # Count enabled vs disabled rules
        enabled_count = sum(1 for rule in rules if rule.enabled)
        disabled_count = len(rules) - enabled_count

        # Determine action: if more rules are enabled, disable all; otherwise enable all
        target_state = disabled_count > enabled_count
        action = "enable" if target_state else "disable"

        # Update all rules
        updated_count = 0
        failed_count = 0
        for rule in rules:
            if rule.enabled != target_state:
                if self.automator.rule_manager.update_rule(rule.id, enabled=target_state):
                    updated_count += 1
                else:
                    failed_count += 1

        # Refresh the display
        self.refresh_rules()

        # Log the action with detailed feedback
        if failed_count > 0:
            self.log_message(f"Toggle All: {updated_count} rules {action}d, {failed_count} failed")
        else:
            self.log_message(f"Toggle All: {updated_count} rules {action}d successfully")

    def refresh_rules(self):
        """Refresh the rules list with integrated toggle column"""
        # Clear existing items
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)

        # Repopulate from rule manager, sorted by name
        rules = self.automator.rule_manager.list_rules()
        rules.sort(key=lambda r: r.name.lower())  # Sort alphabetically by name (case-insensitive)

        for rule in rules:
            # Toggle display
            toggle_text = "✅ ON" if rule.enabled else "❌ OFF"

            # Status
            status = "Active" if rule.enabled else "Disabled"
            condition_type = getattr(rule, "condition_type", "image")
            rule_type = "Image" if condition_type == "image" else "Screen Idle"

            if condition_type == "image":
                trigger_info = os.path.basename(rule.image_path) if rule.image_path else "No image"
            else:
                timeout = getattr(rule, "screen_unchanged_timeout", 5.0)
                trigger_info = f"{timeout:.1f} min"

            action_count = len(rule.actions)

            # Window targeting info
            window_target = ""
            if hasattr(rule, "target_window_title") and rule.target_window_title:
                window_target = rule.target_window_title[:20] + (
                    "..." if len(rule.target_window_title) > 20 else ""
                )
            elif hasattr(rule, "target_window_process") and rule.target_window_process:
                window_target = f"({rule.target_window_process})"
            elif hasattr(rule, "cluster_group") and rule.cluster_group:
                window_target = f"[{rule.cluster_group}]"
            else:
                window_target = "Any"

            # Insert with toggle in #0 column and name in first regular column
            item_id = self.rules_tree.insert(
                "",
                "end",
                text=toggle_text,
                values=(rule.name, status, rule_type, trigger_info, action_count, window_target),
                tags=(rule.id,),
            )

            # Apply color styling
            if rule.enabled:
                self.rules_tree.tag_configure(f"enabled_{rule.id}", foreground="#008800")
                self.rules_tree.item(item_id, tags=(rule.id, f"enabled_{rule.id}"))
            else:
                self.rules_tree.tag_configure(f"disabled_{rule.id}", foreground="#888888")
                self.rules_tree.item(item_id, tags=(rule.id, f"disabled_{rule.id}"))

    def on_toggle_click(self, event):
        """Handle clicks on the toggle column"""
        item = self.rules_tree.identify("item", event.x, event.y)
        column = self.rules_tree.identify("column", event.x, event.y)

        # Check if click was on the toggle column (#0 = leftmost column)
        if item and column == "#0":
            rule_id = self.rules_tree.item(item)["tags"][0]
            rule = self.automator.rule_manager.get_rule(rule_id)
            if rule:
                # Toggle the rule
                new_state = not rule.enabled
                self.toggle_rule(rule_id, new_state)
                # Prevent drag-and-drop from starting for toggle clicks
                return "break"

        # For other columns, call the original tree press handler
        self.on_tree_press(event)

    def new_rule(self):
        """Start creating a new rule"""
        self.current_rule = None
        self.current_actions = []

        # Clear form
        self.name_var.set("")
        self.desc_var.set("")
        self.image_path_var.set("")
        self.condition_var.set("image")
        self.timeout_var.set(5.0)
        self.disable_after_var.set(0)
        self.disable_image_var.set("")

        # Clear window targeting fields
        self.target_window_class_var.set("")
        self.target_window_process_var.set("")
        self.window_id_method_var.set("auto")
        self.target_window_title_var.set("")
        self.window_exact_match_var.set(False)
        self.cluster_group_var.set("")

        # Reset window info display
        self.window_info_var.set("No window selected (rule will apply to any window)")

        # Clear actions
        self.actions_listbox.delete(0, tk.END)

        # Clear image preview
        self.image_label.configure(image="")

        # Update condition display
        self.on_condition_change()

        # Switch to editor tab
        self.notebook.select(self.editor_frame)

    def edit_rule(self):
        """Edit selected rule"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a rule to edit")
            return

        item = selection[0]
        rule_id = self.rules_tree.item(item)["tags"][0]
        self.current_rule = self.automator.rule_manager.get_rule(rule_id)

        if not self.current_rule:
            messagebox.showerror("Error", "Rule not found")
            return

        # Populate editor
        self.name_var.set(self.current_rule.name)
        self.desc_var.set(self.current_rule.description)
        self.image_path_var.set(self.current_rule.image_path)
        self.condition_var.set(getattr(self.current_rule, "condition_type", "image"))
        self.timeout_var.set(getattr(self.current_rule, "screen_unchanged_timeout", 5.0))
        self.disable_after_var.set(getattr(self.current_rule, "disable_after_executions", 0))
        self.disable_image_var.set(getattr(self.current_rule, "disable_on_image", ""))

        # Populate window targeting fields
        self.target_window_class_var.set(getattr(self.current_rule, "target_window_class", ""))
        self.target_window_process_var.set(getattr(self.current_rule, "target_window_process", ""))
        self.window_id_method_var.set(getattr(self.current_rule, "window_id_method", "auto"))
        self.cluster_group_var.set(getattr(self.current_rule, "cluster_group", ""))

        # Update window info display
        if getattr(self.current_rule, "target_window_class", ""):
            self.window_info_var.set(
                f"Target: {getattr(self.current_rule, 'target_window_class', '')}\n"
                + f"Using: Window Class"
            )
        elif getattr(self.current_rule, "target_window_process", ""):
            self.window_info_var.set(
                f"Target: {getattr(self.current_rule, 'target_window_process', '')}\n"
                + f"Using: Process Name"
            )
        else:
            self.window_info_var.set("Rule will apply to any window")

        self.current_actions = self.current_rule.actions.copy()

        # Update UI based on condition type
        self.on_condition_change()

        # Load image preview
        self.load_image_preview(self.current_rule.image_path)

        # Populate actions
        self.actions_listbox.delete(0, tk.END)
        for i, action in enumerate(self.current_actions):
            self.actions_listbox.insert(tk.END, self.action_to_string(action))

        self.notebook.select(self.editor_frame)

    def delete_rule(self):
        """Delete selected rule"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a rule to delete")
            return

        item = selection[0]
        rule_name = self.rules_tree.item(item)["text"]
        rule_id = self.rules_tree.item(item)["tags"][0]

        if messagebox.askyesno("Confirm Delete", f"Delete rule '{rule_name}'?"):
            if self.automator.rule_manager.delete_rule(rule_id):
                self.refresh_rules()
                messagebox.showinfo("Success", f"Rule '{rule_name}' deleted")
            else:
                messagebox.showerror("Error", "Failed to delete rule")

    def test_rule(self):
        """Test selected rule"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a rule to test")
            return

        item = selection[0]
        rule_id = self.rules_tree.item(item)["tags"][0]
        rule_name = self.rules_tree.item(item)["text"]

        self.log_message(f"Testing rule '{rule_name}'...")

        # Run test in thread to avoid blocking UI
        def test_thread():
            if self.automator.test_rule(rule_id):
                self.log_message(f"Test of rule '{rule_name}' completed successfully")
            else:
                self.log_message(f"Test of rule '{rule_name}' failed - trigger image not found")

        threading.Thread(target=test_thread, daemon=True).start()

    def fire_up_rule(self):
        """Fire up (force execute) selected rule immediately"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a rule to fire up")
            return

        item = selection[0]
        rule_id = self.rules_tree.item(item)["tags"][0]
        rule_name = self.rules_tree.item(item)["text"]

        # Get the rule to check its type
        rule = self.automator.rule_manager.get_rule(rule_id)
        if not rule:
            messagebox.showerror("Error", "Rule not found")
            return

        # Check if rule has actions
        if not rule.actions:
            messagebox.showwarning("No Actions", f"Rule '{rule_name}' has no actions to execute")
            return

        # Confirm before executing
        condition_type = getattr(rule, "condition_type", "image")
        if condition_type == "image":
            message = f"Fire up rule '{rule_name}'?\n\nThis will immediately execute all {len(rule.actions)} actions without checking for the trigger image."
        else:
            timeout = getattr(rule, "screen_unchanged_timeout", 5.0)
            message = f"Fire up rule '{rule_name}'?\n\nThis will immediately execute all {len(rule.actions)} actions without waiting for {timeout} minutes of screen inactivity."

        if not messagebox.askyesno("Confirm Fire Up", message):
            return

        self.log_message(
            f"🔥 Firing up rule '{rule_name}' - executing {len(rule.actions)} actions immediately..."
        )

        # Run force execution in thread to avoid blocking UI
        def fire_up_thread():
            try:
                success = self.automator.force_execute_rule(rule_id)
                if success:
                    self.log_message(f"🔥 Rule '{rule_name}' fired up successfully!")
                else:
                    self.log_message(f"❌ Rule '{rule_name}' fire up failed")
            except Exception as e:
                self.log_message(f"❌ Error firing up rule '{rule_name}': {e}")

        threading.Thread(target=fire_up_thread, daemon=True).start()

    def show_context_menu(self, event):
        """Show context menu for rules tree"""
        # Select the item under cursor
        item = self.rules_tree.identify_row(event.y)
        if item:
            self.rules_tree.selection_set(item)

            # Create context menu
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="🔥 Fire Up", command=self.fire_up_rule)
            context_menu.add_separator()
            context_menu.add_command(label="Edit", command=self.edit_rule)
            context_menu.add_command(label="Test", command=self.test_rule)
            context_menu.add_separator()
            context_menu.add_command(label="Delete", command=self.delete_rule)

            # Show context menu
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

    def select_image_file(self):
        """Select image file for trigger"""
        file_path = filedialog.askopenfilename(
            title="Select Trigger Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")],
        )

        if file_path:
            self.image_path_var.set(file_path)
            self.load_image_preview(file_path)

    def browse_disable_image(self):
        """Browse for an image to use as disable trigger"""
        file_path = filedialog.askopenfilename(
            title="Select Disable Trigger Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")],
        )

        if file_path:
            self.disable_image_var.set(file_path)

    def capture_screen_region(self):
        """Capture screen region as trigger image"""
        self.root.withdraw()  # Hide main window

        try:
            selector = CustomScreenSelector()
            region = selector.select_region()

            if region:
                # Save captured region
                save_path = filedialog.asksaveasfilename(
                    title="Save Captured Image",
                    defaultextension=".png",
                    filetypes=[("PNG files", "*.png")],
                )

                if save_path:
                    selector.capture_region_as_image(region, save_path)
                    self.image_path_var.set(save_path)
                    self.load_image_preview(save_path)

                    # Store capture coordinates for sanity check
                    x, y, width, height = region
                    self.capture_x = x
                    self.capture_y = y
                    self.capture_width = width
                    self.capture_height = height
                    print(f"Captured region: {region}")

        finally:
            self.root.deiconify()  # Show main window

    def load_image_preview(self, image_path):
        """Load and display image preview"""
        try:
            if os.path.exists(image_path):
                img = Image.open(image_path)
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.image_label.config(image=photo)
                self.image_label.image = photo  # Keep reference
        except Exception as e:
            print(f"Error loading image preview: {e}")

    def record_clicks(self):
        """Record mouse clicks with persistent stop button"""
        # Create a floating stop button window
        stop_window = tk.Toplevel(self.root)
        stop_window.title("Recording")
        stop_window.attributes("-topmost", True)  # Keep on top
        stop_window.geometry("150x60")
        stop_window.resizable(False, False)

        # Center the window in a visible corner
        x = self.root.winfo_screenwidth() - 170
        y = 70
        stop_window.geometry(f"+{x}+{y}")

        recording_active = tk.BooleanVar(value=True)
        clicks_recorded = []
        stop_button_region = None

        ttk.Label(stop_window, text="Recording clicks...", font=("Segoe UI", 10)).pack(pady=3)
        btn = ttk.Button(
            stop_window, text="Stop Recording", command=lambda: recording_active.set(False)
        )
        btn.pack(pady=5, padx=10, fill=tk.X)

        # Get the coordinates of the stop button to avoid recording clicks on it
        def get_button_region():
            nonlocal stop_button_region
            if btn.winfo_viewable():
                x1 = stop_window.winfo_x() + btn.winfo_x()
                y1 = stop_window.winfo_y() + btn.winfo_y()
                x2 = x1 + btn.winfo_width()
                y2 = y1 + btn.winfo_height()
                stop_button_region = (x1, y1, x2, y2)
                stop_window.after_cancel(update_id)

        update_id = stop_window.after(200, get_button_region)

        # Minimize the main window
        self.root.withdraw()

        # Record clicks in a separate thread
        def record_thread():
            try:
                recorder = ClickRecorder()
                nonlocal clicks_recorded
                clicks_recorded = recorder.record_until(
                    lambda: not recording_active.get(), exclude_region=stop_button_region
                )
            except Exception as e:
                print(f"Error recording clicks: {e}")
            finally:
                # Always close the stop window
                stop_window.after(0, stop_window.destroy)
                self.root.after(100, self.root.deiconify)

        threading.Thread(target=record_thread, daemon=True).start()

        # Wait for the stop window to be closed before proceeding
        self.root.wait_window(stop_window)

        # Add recorded clicks as actions
        for click in clicks_recorded:
            if click["button"] == "left":
                action = create_click_action(click["x"], click["y"])
            else:
                action = create_right_click_action(click["x"], click["y"])

            self.current_actions.append(action)
            self.actions_listbox.insert(tk.END, self.action_to_string(action))

    def record_keys(self):
        """Open a dialog to input keyboard actions."""
        dialog = KeyInputDialog(self.root)
        action = dialog.get_action()

        if action:
            self.current_actions.append(action)
            self.actions_listbox.insert(tk.END, self.action_to_string(action))

    def add_wait_action(self):
        """Add wait action"""
        duration = simpledialog.askfloat(
            "Wait Duration", "Enter wait duration in seconds:", initialvalue=1.0
        )
        if duration:
            action = create_wait_action(duration)
            self.current_actions.append(action)
            self.actions_listbox.insert(tk.END, self.action_to_string(action))

    def add_manual_action(self):
        """Add manual action via dialog"""
        dialog = ActionDialog(self.root)
        action = dialog.get_action()

        if action:
            self.current_actions.append(action)
            self.actions_listbox.insert(tk.END, self.action_to_string(action))

    def add_click_image_action(self):
        """Add action to click on an image"""
        # Let the user select an image file
        image_path = filedialog.askopenfilename(
            title="Select Image to Click", filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")]
        )

        if not image_path:
            return

        # Option to capture a new image instead
        if messagebox.askyesno(
            "Image Selection",
            "Would you like to capture a new screen region instead of using this image?",
        ):
            self.root.withdraw()  # Hide main window

            try:
                selector = ScreenSelector()
                region = selector.select_region()

                if region:
                    # Save captured region
                    save_path = filedialog.asksaveasfilename(
                        title="Save Image for Click Target",
                        defaultextension=".png",
                        filetypes=[("PNG files", "*.png")],
                    )

                    if save_path:
                        selector.capture_region_as_image(region, save_path)
                        image_path = save_path
                    else:
                        self.root.deiconify()  # Show main window
                        return
                else:
                    self.root.deiconify()  # Show main window
                    return

            finally:
                self.root.deiconify()  # Show main window

        # Ask for the confidence level
        confidence = simpledialog.askfloat(
            "Match Confidence",
            "Enter confidence level (0.1-1.0):\n(Lower values are less strict)",
            initialvalue=0.8,
            minvalue=0.1,
            maxvalue=1.0,
        )

        if confidence is None:
            return

        # Create the click image action
        action = create_click_image_action(image_path, confidence)
        self.current_actions.append(action)
        self.actions_listbox.insert(tk.END, self.action_to_string(action))

    def clear_actions(self):
        """Clear all actions"""
        if messagebox.askyesno("Confirm", "Clear all actions?"):
            self.current_actions = []
            self.actions_listbox.delete(0, tk.END)

    def remove_action(self):
        """Remove selected action"""
        selection = self.actions_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_actions.pop(index)
            self.actions_listbox.delete(index)

    def move_action_up(self):
        """Move selected action up"""
        selection = self.actions_listbox.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            # Swap actions
            self.current_actions[index], self.current_actions[index - 1] = (
                self.current_actions[index - 1],
                self.current_actions[index],
            )

            # Update listbox
            self.actions_listbox.delete(index - 1, index)
            self.actions_listbox.insert(
                index - 1, self.action_to_string(self.current_actions[index - 1])
            )
            self.actions_listbox.insert(index, self.action_to_string(self.current_actions[index]))
            self.actions_listbox.selection_set(index - 1)

    def move_action_down(self):
        """Move selected action down"""
        selection = self.actions_listbox.curselection()
        if selection and selection[0] < len(self.current_actions) - 1:
            index = selection[0]
            # Swap actions
            self.current_actions[index], self.current_actions[index + 1] = (
                self.current_actions[index + 1],
                self.current_actions[index],
            )

            # Update listbox
            self.actions_listbox.delete(index, index + 1)
            self.actions_listbox.insert(index, self.action_to_string(self.current_actions[index]))
            self.actions_listbox.insert(
                index + 1, self.action_to_string(self.current_actions[index + 1])
            )
            self.actions_listbox.selection_set(index + 1)

    def edit_action(self):
        """Edit selected action"""
        selection = self.actions_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an action to edit")
            return

        index = selection[0]
        current_action = self.current_actions[index]

        # Create appropriate dialog based on action type
        if current_action.type == ActionType.TYPE_TEXT:
            dialog = EditTextActionDialog(self.root, current_action.params["text"])
            new_text = dialog.get_text()
            if new_text is not None:
                # Update the action
                self.current_actions[index] = create_type_text_action(new_text)
                # Update the listbox display
                self.actions_listbox.delete(index)
                self.actions_listbox.insert(
                    index, self.action_to_string(self.current_actions[index])
                )
                self.actions_listbox.selection_set(index)
        elif current_action.type == ActionType.KEY_PRESS:
            dialog = EditKeyActionDialog(self.root, current_action.params["key"])
            new_key = dialog.get_key()
            if new_key is not None:
                # Update the action
                self.current_actions[index] = create_key_press_action(new_key)
                # Update the listbox display
                self.actions_listbox.delete(index)
                self.actions_listbox.insert(
                    index, self.action_to_string(self.current_actions[index])
                )
                self.actions_listbox.selection_set(index)
        elif current_action.type == ActionType.KEY_COMBINATION:
            dialog = EditKeyComboActionDialog(self.root, current_action.params["keys"])
            new_keys = dialog.get_keys()
            if new_keys is not None:
                # Update the action
                self.current_actions[index] = create_key_combination_action(new_keys)
                # Update the listbox display
                self.actions_listbox.delete(index)
                self.actions_listbox.insert(
                    index, self.action_to_string(self.current_actions[index])
                )
                self.actions_listbox.selection_set(index)
        elif current_action.type == ActionType.WAIT:
            dialog = EditWaitActionDialog(self.root, current_action.params["duration"])
            new_duration = dialog.get_duration()
            if new_duration is not None:
                # Update the action
                self.current_actions[index] = create_wait_action(new_duration)
                # Update the listbox display
                self.actions_listbox.delete(index)
                self.actions_listbox.insert(
                    index, self.action_to_string(self.current_actions[index])
                )
                self.actions_listbox.selection_set(index)
        elif current_action.type in [
            ActionType.CLICK,
            ActionType.DOUBLE_CLICK,
            ActionType.RIGHT_CLICK,
        ]:
            dialog = EditClickActionDialog(
                self.root,
                current_action.type,
                current_action.params["x"],
                current_action.params["y"],
            )
            result = dialog.get_coordinates()
            if result is not None:
                x, y = result
                # Update the action based on type
                if current_action.type == ActionType.CLICK:
                    self.current_actions[index] = create_click_action(x, y)
                elif current_action.type == ActionType.DOUBLE_CLICK:
                    self.current_actions[index] = create_double_click_action(x, y)
                elif current_action.type == ActionType.RIGHT_CLICK:
                    self.current_actions[index] = create_right_click_action(x, y)
                # Update the listbox display
                self.actions_listbox.delete(index)
                self.actions_listbox.insert(
                    index, self.action_to_string(self.current_actions[index])
                )
                self.actions_listbox.selection_set(index)
        elif current_action.type == ActionType.SCROLL:
            dialog = EditScrollActionDialog(self.root, current_action.params["clicks"])
            new_clicks = dialog.get_clicks()
            if new_clicks is not None:
                # Update the action
                self.current_actions[index] = create_scroll_action(new_clicks)
                # Update the listbox display
                self.actions_listbox.delete(index)
                self.actions_listbox.insert(
                    index, self.action_to_string(self.current_actions[index])
                )
                self.actions_listbox.selection_set(index)
        else:
            messagebox.showinfo(
                "Not Editable", f"Actions of type '{current_action.type.value}' cannot be edited"
            )

    def action_to_string(self, action):
        """Convert action to display string"""
        if action.type == ActionType.CLICK:
            return f"Click at ({action.params['x']}, {action.params['y']})"
        elif action.type == ActionType.DOUBLE_CLICK:
            return f"Double-click at ({action.params['x']}, {action.params['y']})"
        elif action.type == ActionType.RIGHT_CLICK:
            return f"Right-click at ({action.params['x']}, {action.params['y']})"
        elif action.type == ActionType.TYPE_TEXT:
            text = (
                action.params["text"][:50] + "..."
                if len(action.params["text"]) > 50
                else action.params["text"]
            )
            return f"Type: '{text}'"
        elif action.type == ActionType.KEY_PRESS:
            return f"Press key: {action.params['key']}"
        elif action.type == ActionType.KEY_COMBINATION:
            return f"Key combo: {'+'.join(action.params['keys'])}"
        elif action.type == ActionType.WAIT:
            return f"Wait {action.params['duration']}s"
        elif action.type == ActionType.SCROLL:
            return f"Scroll {action.params['clicks']} clicks"
        elif action.type == ActionType.CLICK_IMAGE:
            image_name = os.path.basename(action.params["image_path"])
            return f"Click on image: {image_name}"
        else:
            return str(action.type.value)

    def save_rule(self):
        """Save current rule"""
        name = self.name_var.get().strip()
        image_path = self.image_path_var.get().strip()
        description = self.desc_var.get().strip()
        condition_type = self.condition_var.get()
        timeout = self.timeout_var.get()

        # Priority is now managed by drag-and-drop ordering in the rules list
        # For new rules, assign a default priority that will be updated by drag-and-drop
        priority = 100  # Default priority for new rules

        if not name:
            messagebox.showerror("Error", "Rule name is required")
            return

        # Validate based on condition type
        if condition_type == "image":
            if not image_path or not os.path.exists(image_path):
                messagebox.showerror(
                    "Error", "Valid trigger image is required for image-based rules"
                )
                return
        else:  # screen_unchanged
            if timeout <= 0:
                messagebox.showerror(
                    "Error", "Timeout must be greater than 0 for screen unchanged rules"
                )
                return
            image_path = ""  # No image needed for screen unchanged rules

        if not self.current_actions:
            messagebox.showerror("Error", "At least one action is required")
            return

        try:
            # Get capture coordinates if available
            capture_x = getattr(self, "capture_x", 0)
            capture_y = getattr(self, "capture_y", 0)
            capture_width = getattr(self, "capture_width", 0)
            capture_height = getattr(self, "capture_height", 0)

            if self.current_rule:
                # Update existing rule
                self.automator.rule_manager.update_rule(
                    self.current_rule.id,
                    name=name,
                    image_path=image_path,
                    description=description,
                    priority=priority,
                    actions=self.current_actions,
                    capture_x=capture_x,
                    capture_y=capture_y,
                    capture_width=capture_width,
                    capture_height=capture_height,
                    condition_type=condition_type,
                    screen_unchanged_timeout=timeout,
                    target_window_class=self.target_window_class_var.get(),
                    target_window_process=self.target_window_process_var.get(),
                    window_id_method=self.window_id_method_var.get(),
                    target_window_title="",  # Empty for backward compatibility
                    window_exact_match=False,  # Default for backward compatibility
                    cluster_group=self.cluster_group_var.get(),
                    disable_after_executions=self.disable_after_var.get(),
                    disable_on_image=self.disable_image_var.get(),
                )
                messagebox.showinfo("Success", f"Rule '{name}' updated")
            else:
                # Create new rule
                rule = self.automator.rule_manager.create_rule(
                    name=name,
                    image_path=image_path,
                    actions=self.current_actions,
                    description=description,
                    condition_type=condition_type,
                    screen_unchanged_timeout=timeout,
                )

                # Update priority, capture coordinates, and window targeting
                self.automator.rule_manager.update_rule(
                    rule.id,
                    priority=priority,
                    capture_x=capture_x,
                    capture_y=capture_y,
                    capture_width=capture_width,
                    capture_height=capture_height,
                    target_window_class=self.target_window_class_var.get(),
                    target_window_process=self.target_window_process_var.get(),
                    window_id_method=self.window_id_method_var.get(),
                    target_window_title="",  # Empty for backward compatibility
                    window_exact_match=False,  # Default for backward compatibility
                    cluster_group=self.cluster_group_var.get(),
                    disable_after_executions=self.disable_after_var.get(),
                    disable_on_image=self.disable_image_var.get(),
                )

                rule_type = "Image-based" if condition_type == "image" else "Screen unchanged"
                messagebox.showinfo("Success", f"{rule_type} rule '{name}' created")

            # Reset capture coordinates
            if hasattr(self, "capture_x"):
                del self.capture_x
                del self.capture_y
                del self.capture_width
                del self.capture_height

            self.refresh_rules()
            self.notebook.select(self.rules_frame)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save rule: {e}")

    def on_condition_change(self):
        """Handle condition type change"""
        condition_type = self.condition_var.get()

        if condition_type == "image":
            # Show image frame, hide timeout spinbox state
            self.image_frame.pack(fill=tk.X, padx=5, pady=5)
            self.timeout_spinbox.configure(state="disabled")
        else:  # screen_unchanged
            # Hide image frame, enable timeout spinbox
            self.image_frame.pack_forget()
            self.timeout_spinbox.configure(state="normal")

    def on_window_method_change(self, event=None):
        """Handle window identification method changes"""
        method = self.window_id_method_var.get()

        # Highlight the recommended field based on the selected method
        if method == "class":
            self.target_window_class_var.set(self.target_window_class_var.get())
            # Show a tip about class-based targeting
            self.log_message(
                "💡 Class-based targeting is the most reliable method for window identification"
            )
        elif method == "process":
            self.target_window_process_var.set(self.target_window_process_var.get())
            # Show a tip about process-based targeting
            self.log_message(
                "💡 Process-based targeting works well for applications with changing window titles"
            )
        else:  # auto
            # Show a tip about auto method
            self.log_message("💡 Auto method will try class and process targeting in that order")

    def cancel_edit(self):
        """Cancel rule editing"""
        self.notebook.select(self.rules_frame)

    def start_monitoring(self):
        """Start the screen automator."""
        if not self.automator.is_running():
            interval = self.interval_var.get()
            self.automator.set_check_interval(interval)

            # Add debug logging
            automator_type = (
                "Context-aware" if isinstance(self.automator, ContextAwareAutomator) else "Standard"
            )
            self.log_message(f"🚀 Starting {automator_type} monitoring with interval {interval}s")

            # Get rule counts for debugging
            rules = self.automator.rule_manager.list_rules()
            enabled_rules = [r for r in rules if r.enabled]

            if enabled_rules:
                self.log_message(
                    f"📋 Found {len(enabled_rules)} enabled rules: {[r.name for r in enabled_rules[:3]]}{'...' if len(enabled_rules) > 3 else ''}"
                )

                # Show context-aware information
                if isinstance(self.automator, ContextAwareAutomator):
                    self.log_message(
                        f"🗂️  Context-aware monitoring enabled - rules will target specific windows"
                    )
            else:
                self.log_message(
                    "⚠️  No enabled rules found - monitoring will run but no automation will occur"
                )

            self.automator.start_monitoring()
            self.log_message(f"✅ Monitoring started successfully")

    def stop_monitoring(self):
        """Stop the screen automator."""
        if self.automator.is_running():
            self.automator.stop()
            self.log_message("Monitoring stopped.")

        # Cancel any active schedule when stopping
        if self.schedule_active:
            self.cancel_schedule()

    def toggle_monitoring(self):
        """Toggle monitoring state."""
        if self.automator.is_running():
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def schedule_monitoring(self):
        """Schedule monitoring to start after a specified delay."""
        if self.schedule_active:
            # Cancel existing schedule
            self.cancel_schedule()
            return

        if self.automator.is_running():
            messagebox.showwarning(
                "Already Running",
                "Monitoring is already active. Stop it first to schedule a new start.",
            )
            return

        # Create custom time input dialog
        delay = self._get_time_delay_dialog()

        if delay is not None and delay > 0:
            # Start countdown
            self.start_schedule_countdown(delay)
        elif delay is not None:
            messagebox.showerror("Invalid Input", "Delay must be greater than 0.")

    def start_schedule_countdown(self, delay):
        """Start the countdown timer for scheduled monitoring."""
        self.schedule_active = True
        self.schedule_button.config(text="❌ Cancel Schedule")

        # Log the schedule with user-friendly time format
        time_str = self._format_time_duration(delay)
        self.log_message(f"⏰ Monitoring scheduled to start in {time_str}")

        # Start countdown in a separate thread
        def countdown():
            remaining = delay
            while remaining > 0 and self.schedule_active:
                if (
                    remaining <= 10 or remaining % 30 == 0
                ):  # Show countdown for last 10 seconds or every 30 seconds
                    self.log_message(f"⏰ Starting in {int(remaining)} seconds...")
                time.sleep(1)
                remaining -= 1

            if self.schedule_active:  # Only start if schedule wasn't cancelled
                self.root.after(0, self.execute_scheduled_start)

        self.scheduled_timer = threading.Thread(target=countdown, daemon=True)
        self.scheduled_timer.start()

    def _get_time_delay_dialog(self):
        """Show a custom dialog to get time delay in hours, minutes, and seconds."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Schedule Monitoring")
        dialog.geometry("350x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        result = [None]

        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Set delay time:", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 15))

        # Time input frame
        time_frame = ttk.Frame(main_frame)
        time_frame.pack(pady=(0, 20))

        # Hours
        hours_frame = ttk.Frame(time_frame)
        hours_frame.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(hours_frame, text="Hours:").pack()
        hours_var = tk.StringVar(value="0")
        hours_spinbox = ttk.Spinbox(hours_frame, from_=0, to=23, width=5, textvariable=hours_var)
        hours_spinbox.pack()

        # Minutes
        minutes_frame = ttk.Frame(time_frame)
        minutes_frame.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(minutes_frame, text="Minutes:").pack()
        minutes_var = tk.StringVar(value="0")
        minutes_spinbox = ttk.Spinbox(
            minutes_frame, from_=0, to=59, width=5, textvariable=minutes_var
        )
        minutes_spinbox.pack()

        # Seconds
        seconds_frame = ttk.Frame(time_frame)
        seconds_frame.pack(side=tk.LEFT)
        ttk.Label(seconds_frame, text="Seconds:").pack()
        seconds_var = tk.StringVar(value="30")
        seconds_spinbox = ttk.Spinbox(
            seconds_frame, from_=0, to=59, width=5, textvariable=seconds_var
        )
        seconds_spinbox.pack()

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)

        def on_ok():
            try:
                hours = int(hours_var.get())
                minutes = int(minutes_var.get())
                seconds = int(seconds_var.get())

                total_seconds = hours * 3600 + minutes * 60 + seconds
                result[0] = total_seconds
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers for time values.")

        def on_cancel():
            result[0] = None
            dialog.destroy()

        ttk.Button(buttons_frame, text="Cancel", command=on_cancel).pack(
            side=tk.RIGHT, padx=(10, 0)
        )
        ttk.Button(buttons_frame, text="OK", command=on_ok).pack(side=tk.RIGHT)

        # Set focus to seconds spinbox
        seconds_spinbox.focus()

        # Handle Enter key
        dialog.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())

        # Wait for dialog to close
        dialog.wait_window()

        return result[0]

    def _format_time_duration(self, total_seconds):
        """Format time duration in a user-friendly way."""
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)

        parts = []
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if (
            seconds > 0 or not parts
        ):  # Always show seconds if it's the only unit or if there are no other parts
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return f"{parts[0]} and {parts[1]}"
        else:
            return f"{', '.join(parts[:-1])}, and {parts[-1]}"

    def execute_scheduled_start(self):
        """Execute the scheduled start of monitoring."""
        self.schedule_active = False
        self.schedule_button.config(text="⏰ Schedule")

        if not self.automator.is_running():
            self.log_message("🚀 Starting scheduled monitoring...")
            self.start_monitoring()
        else:
            self.log_message("⚠️ Monitoring was already started manually")

    def cancel_schedule(self):
        """Cancel the scheduled monitoring start."""
        self.schedule_active = False
        self.schedule_button.config(text="⏰ Schedule")
        self.log_message("❌ Scheduled monitoring cancelled")

    def apply_settings(self):
        """Apply settings"""
        try:
            interval = self.interval_var.get()

            self.automator.set_check_interval(interval)

            self.log_message(f"Check interval set to {interval} seconds")
            self.log_message("Action limits are now configured per-rule")
        except Exception as e:
            self.log_message(f"Error applying settings: {e}")

    def reset_action_counter(self):
        """Reset the action execution counter"""
        try:
            self.automator.reset_action_counter()
            self.log_message("Action counter reset to 0")
        except Exception as e:
            self.log_message(f"Error resetting counter: {e}")

    def show_priority_list(self):
        """Show a dialog with rules sorted by priority"""
        rules = self.automator.rule_manager.list_rules_by_priority()
        if not rules:
            messagebox.showinfo("Priority List", "No rules found.")
            return

        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Rules by Priority")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # Create frame with padding
        main_frame = ttk.Frame(dialog, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Add header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="Rules Sorted by Priority", font=self.heading_font).pack(
            side=tk.LEFT
        )

        ttk.Label(header_frame, text="(Lower number = higher priority)", font=self.small_font).pack(
            side=tk.RIGHT
        )

        # Create treeview
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(tree_frame, columns=("Priority", "Status", "Actions"), show="headings")
        tree.heading("Priority", text="Priority")
        tree.heading("Status", text="Status")
        tree.heading("Actions", text="Actions")

        tree.column("Priority", width=80, anchor=tk.CENTER)
        tree.column("Status", width=100)
        tree.column("Actions", width=80, anchor=tk.CENTER)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add rules to tree
        for rule in rules:
            status = "Enabled" if rule.enabled else "Disabled"
            tree.insert(
                "", tk.END, text=rule.name, values=(rule.priority, status, len(rule.actions))
            )

        # Add info text
        info_text = (
            "Rules are executed in priority order. \n"
            "There is a minimum 5-second delay between rule executions.\n"
            "Higher priority rules will block lower priority rules if executed recently."
        )

        info_label = ttk.Label(
            main_frame,
            text=info_text,
            font=self.small_font,
            foreground="#555555",
            justify=tk.LEFT,
            wraplength=480,
        )
        info_label.pack(pady=10, fill=tk.X)

        # Add close button
        ttk.Button(main_frame, text="Close", command=dialog.destroy).pack(pady=5)

    def update_status_loop(self):
        """Update status in background thread"""
        while True:
            try:
                status = self.automator.get_status()
                is_running = status["running"]
                actions_executed = status.get("actions_executed", 0)

                status_text = "Running" if is_running else "Stopped"

                # Update action counter display (global action limits removed)
                action_text = (
                    f"Actions: {actions_executed}" if is_running or actions_executed > 0 else ""
                )

                # Avoid unnecessary UI updates if status hasn't changed
                if self.status_var.get() != status_text:
                    self.status_var.set(status_text)

                    # Update toggle button
                    if is_running:
                        self.toggle_monitoring_button.config(text="■ Stop", style="TButton")
                    else:
                        self.toggle_monitoring_button.config(text="▶ Start", style="Accent.TButton")

                # Update action counter
                if self.action_counter_var.get() != action_text:
                    self.action_counter_var.set(action_text)

                time.sleep(1)
            except Exception as e:
                print(f"Status update error: {e}")
                break

    def select_target_window(self):
        """Select a target window for the current rule with simplified UI"""
        try:
            # Get current windows
            windows = self.window_manager.get_running_windows()

            if not windows:
                messagebox.showinfo("No Windows", "No windows found")
                return

            # Create simple selection dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Select Target Window")
            dialog.geometry("600x400")
            dialog.transient(self.root)
            dialog.grab_set()

            frame = ttk.Frame(dialog, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)

            # Header with clear instructions
            ttk.Label(
                frame, text="Choose which window this rule applies to:", font=self.heading_font
            ).pack(pady=(0, 5))
            ttk.Label(frame, text="The rule will only run when this window is active").pack(
                pady=(0, 15)
            )

            # Windows listbox with better styling
            list_frame = ttk.Frame(frame)
            list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

            listbox = tk.Listbox(list_frame, height=12, font=self.normal_font)
            scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
            listbox.configure(yscrollcommand=scrollbar.set)

            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            window_list = []
            for window in windows:
                if window.title.strip():
                    # Show both title and process name for better identification
                    display_text = f"{window.title} ({window.process_name})"
                    listbox.insert(tk.END, display_text)
                    window_list.append(window)

            # Option to target any window
            any_window_frame = ttk.Frame(frame)
            any_window_frame.pack(fill=tk.X, pady=(0, 15))

            any_window_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(
                any_window_frame, text="Apply to any window", variable=any_window_var
            ).pack(side=tk.LEFT)

            selected_window = [None]

            def on_select():
                if any_window_var.get():
                    # Clear window targeting
                    self.target_window_class_var.set("")
                    self.target_window_process_var.set("")
                    self.window_id_method_var.set("auto")
                    self.window_info_var.set("Rule will apply to any window")
                    self.log_message("Rule set to apply to any window")
                else:
                    selection = listbox.curselection()
                    if selection:
                        selected_window[0] = window_list[selection[0]]
                        window = selected_window[0]

                        # Intelligently choose the best identification method
                        if hasattr(window, "class_name") and window.class_name:
                            # Use class-based targeting (most reliable)
                            self.target_window_class_var.set(window.class_name)
                            self.target_window_process_var.set(window.process_name)
                            self.window_id_method_var.set("class")

                            # Update the window info display
                            self.window_info_var.set(
                                f"Target: {window.title}\n"
                                + f"Using: Window Class ({window.class_name})"
                            )
                            self.log_message(f"Selected window: {window.title}")
                        else:
                            # Fallback to process-based targeting
                            self.target_window_process_var.set(window.process_name)
                            self.window_id_method_var.set("process")

                            # Update the window info display
                            self.window_info_var.set(
                                f"Target: {window.title}\n"
                                + f"Using: Process Name ({window.process_name})"
                            )
                            self.log_message(f"Selected window: {window.title}")
                    else:
                        messagebox.showinfo(
                            "No Selection", "Please select a window or check 'Apply to any window'"
                        )
                        return

                dialog.destroy()

            def on_cancel():
                dialog.destroy()

            # Button frame with clear actions
            button_frame = ttk.Frame(frame)
            button_frame.pack(fill=tk.X, pady=(10, 0))

            ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="Apply", command=on_select, style="Accent.TButton").pack(
                side=tk.RIGHT, padx=5
            )

            dialog.wait_window()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to select window: {e}")

    def run(self):
        """Start the main loop"""
        # Refresh rules list at startup
        self.refresh_rules()

        # Start the main loop
        self.root.mainloop()


class ActionDialog:
    def __init__(self, parent):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Action")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.setup_dialog()

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def setup_dialog(self):
        """Setup action dialog"""
        # Action type selection
        ttk.Label(self.dialog, text="Action Type:").pack(pady=5)

        self.action_var = tk.StringVar(value="click")
        action_frame = ttk.Frame(self.dialog)
        action_frame.pack(pady=5)

        actions = [
            ("Click", "click"),
            ("Double Click", "double_click"),
            ("Right Click", "right_click"),
            ("Type Text", "type_text"),
            ("Press Key", "key_press"),
            ("Key Combination", "key_combo"),
            ("Press Enter", "press_enter"),
            ("Wait", "wait"),
            ("Scroll", "scroll"),
        ]

        for text, value in actions:
            ttk.Radiobutton(
                action_frame,
                text=text,
                variable=self.action_var,
                value=value,
                command=self.on_action_change,
            ).pack(anchor=tk.W)

        # Parameters frame
        self.params_frame = ttk.LabelFrame(self.dialog, text="Parameters")
        self.params_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(
            side=tk.LEFT, padx=5
        )

        self.on_action_change()

    def on_action_change(self):
        """Handle action type change"""
        # Clear existing widgets
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        action_type = self.action_var.get()

        if action_type in ["click", "double_click", "right_click"]:
            ttk.Label(self.params_frame, text="X:").grid(
                row=0, column=0, sticky=tk.W, padx=5, pady=5
            )
            self.x_var = tk.IntVar()
            ttk.Entry(self.params_frame, textvariable=self.x_var, width=10).grid(
                row=0, column=1, padx=5, pady=5
            )

            ttk.Label(self.params_frame, text="Y:").grid(
                row=1, column=0, sticky=tk.W, padx=5, pady=5
            )
            self.y_var = tk.IntVar()
            ttk.Entry(self.params_frame, textvariable=self.y_var, width=10).grid(
                row=1, column=1, padx=5, pady=5
            )

        elif action_type == "type_text":
            ttk.Label(self.params_frame, text="Text:").grid(
                row=0, column=0, sticky=tk.W, padx=5, pady=5
            )
            self.text_var = tk.StringVar()
            ttk.Entry(self.params_frame, textvariable=self.text_var, width=30).grid(
                row=0, column=1, padx=5, pady=5
            )

        elif action_type == "key_press":
            ttk.Label(self.params_frame, text="Key:").grid(
                row=0, column=0, sticky=tk.W, padx=5, pady=5
            )
            self.key_var = tk.StringVar()
            ttk.Entry(self.params_frame, textvariable=self.key_var, width=20).grid(
                row=0, column=1, padx=5, pady=5
            )

        elif action_type == "key_combo":
            ttk.Label(self.params_frame, text="Keys (comma-separated):").grid(
                row=0, column=0, sticky=tk.W, padx=5, pady=5
            )
            self.keys_var = tk.StringVar()
            ttk.Entry(self.params_frame, textvariable=self.keys_var, width=30).grid(
                row=0, column=1, padx=5, pady=5
            )

        elif action_type == "wait":
            ttk.Label(self.params_frame, text="Duration (seconds):").grid(
                row=0, column=0, sticky=tk.W, padx=5, pady=5
            )
            self.duration_var = tk.DoubleVar(value=1.0)
            ttk.Entry(self.params_frame, textvariable=self.duration_var, width=10).grid(
                row=0, column=1, padx=5, pady=5
            )

        elif action_type == "scroll":
            ttk.Label(self.params_frame, text="Clicks:").grid(
                row=0, column=0, sticky=tk.W, padx=5, pady=5
            )
            self.clicks_var = tk.IntVar(value=3)
            ttk.Entry(self.params_frame, textvariable=self.clicks_var, width=10).grid(
                row=0, column=1, padx=5, pady=5
            )

        elif action_type == "press_enter":
            ttk.Label(self.params_frame, text="No parameters needed.").pack(padx=5, pady=5)

    def ok_clicked(self):
        """Handle OK button"""
        action_type = self.action_var.get()

        try:
            if action_type == "click":
                self.result = create_click_action(self.x_var.get(), self.y_var.get())
            elif action_type == "double_click":
                self.result = create_double_click_action(self.x_var.get(), self.y_var.get())
            elif action_type == "right_click":
                self.result = create_right_click_action(self.x_var.get(), self.y_var.get())
            elif action_type == "type_text":
                self.result = create_type_text_action(self.text_var.get())
            elif action_type == "key_press":
                self.result = create_key_press_action(self.key_var.get())
            elif action_type == "key_combo":
                keys = [k.strip() for k in self.keys_var.get().split(",")]
                self.result = create_key_combination_action(keys)
            elif action_type == "wait":
                self.result = create_wait_action(self.duration_var.get())
            elif action_type == "scroll":
                self.result = create_scroll_action(self.clicks_var.get())
            elif action_type == "press_enter":
                self.result = create_key_press_action("enter")

            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Invalid parameters: {e}")

    def cancel_clicked(self):
        """Handle Cancel button"""
        self.dialog.destroy()

    def get_action(self):
        """Get the created action"""
        self.dialog.wait_window()
        return self.result


class KeyInputDialog:
    def __init__(self, parent):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Keyboard Action")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.setup_dialog()

        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"350x150+{x}+{y}")

    def setup_dialog(self):
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Action type
        self.action_type_var = tk.StringVar(value="text")

        type_frame = ttk.Frame(main_frame)
        type_frame.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(
            type_frame,
            text="Type Text",
            variable=self.action_type_var,
            value="text",
            command=self.on_action_change,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            type_frame,
            text="Key Combination",
            variable=self.action_type_var,
            value="combo",
            command=self.on_action_change,
        ).pack(side=tk.LEFT, padx=5)

        # Input field
        self.input_label = ttk.Label(main_frame, text="Text to type:")
        self.input_label.pack(anchor=tk.W, pady=(10, 0))
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(main_frame, textvariable=self.input_var, width=40)
        self.input_entry.pack(fill=tk.X, pady=5)
        self.input_entry.focus_set()

        self.on_action_change()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10, side=tk.BOTTOM, anchor=tk.E)
        ttk.Button(button_frame, text="OK", command=self.ok_clicked, style="Accent.TButton").pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(
            side=tk.LEFT, padx=5
        )

    def on_action_change(self, *args):
        if self.action_type_var.get() == "text":
            self.input_label.config(text="Text to type:")
        else:
            self.input_label.config(text="Key combination (e.g., ctrl+c):")

    def ok_clicked(self):
        input_value = self.input_var.get()
        if not input_value:
            messagebox.showwarning(
                "Input Required", "Please provide an input value.", parent=self.dialog
            )
            return

        try:
            if self.action_type_var.get() == "text":
                self.result = create_type_text_action(input_value)
            else:  # combo
                keys = [k.strip().lower() for k in input_value.replace("+", " ").split()]
                self.result = create_key_combination_action(keys)

            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid input: {e}", parent=self.dialog)

    def cancel_clicked(self):
        self.dialog.destroy()

    def get_action(self):
        self.dialog.wait_window()
        return self.result


class EditTextActionDialog:
    """Dialog for editing text input actions"""

    def __init__(self, parent, current_text):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Text Action")
        self.dialog.geometry("400x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.current_text = current_text
        self.setup_dialog()

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def setup_dialog(self):
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Text to type:").pack(anchor=tk.W, pady=(0, 5))

        self.text_var = tk.StringVar(value=self.current_text)
        self.text_entry = ttk.Entry(main_frame, textvariable=self.text_var, width=50)
        self.text_entry.pack(fill=tk.X, pady=5)
        self.text_entry.focus_set()
        self.text_entry.select_range(0, tk.END)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10, side=tk.BOTTOM, anchor=tk.E)
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(
            side=tk.LEFT, padx=5
        )

    def ok_clicked(self):
        self.result = self.text_var.get()
        self.dialog.destroy()

    def cancel_clicked(self):
        self.dialog.destroy()

    def get_text(self):
        self.dialog.wait_window()
        return self.result


class EditKeyActionDialog:
    """Dialog for editing key press actions"""

    def __init__(self, parent, current_key):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Key Action")
        self.dialog.geometry("300x120")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.current_key = current_key
        self.setup_dialog()

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def setup_dialog(self):
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Key to press:").pack(anchor=tk.W, pady=(0, 5))

        self.key_var = tk.StringVar(value=self.current_key)
        self.key_entry = ttk.Entry(main_frame, textvariable=self.key_var, width=30)
        self.key_entry.pack(fill=tk.X, pady=5)
        self.key_entry.focus_set()
        self.key_entry.select_range(0, tk.END)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10, side=tk.BOTTOM, anchor=tk.E)
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(
            side=tk.LEFT, padx=5
        )

    def ok_clicked(self):
        self.result = self.key_var.get()
        self.dialog.destroy()

    def cancel_clicked(self):
        self.dialog.destroy()

    def get_key(self):
        self.dialog.wait_window()
        return self.result


class EditKeyComboActionDialog:
    """Dialog for editing key combination actions"""

    def __init__(self, parent, current_keys):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Key Combination Action")
        self.dialog.geometry("400x120")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.current_keys = current_keys
        self.setup_dialog()

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def setup_dialog(self):
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Key combination (comma-separated):").pack(
            anchor=tk.W, pady=(0, 5)
        )

        self.keys_var = tk.StringVar(value=", ".join(self.current_keys))
        self.keys_entry = ttk.Entry(main_frame, textvariable=self.keys_var, width=40)
        self.keys_entry.pack(fill=tk.X, pady=5)
        self.keys_entry.focus_set()
        self.keys_entry.select_range(0, tk.END)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10, side=tk.BOTTOM, anchor=tk.E)
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(
            side=tk.LEFT, padx=5
        )

    def ok_clicked(self):
        keys_str = self.keys_var.get()
        self.result = [k.strip() for k in keys_str.split(",") if k.strip()]
        self.dialog.destroy()

    def cancel_clicked(self):
        self.dialog.destroy()

    def get_keys(self):
        self.dialog.wait_window()
        return self.result


class EditWaitActionDialog:
    """Dialog for editing wait actions"""

    def __init__(self, parent, current_duration):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Wait Action")
        self.dialog.geometry("300x120")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.current_duration = current_duration
        self.setup_dialog()

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def setup_dialog(self):
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Duration (seconds):").pack(anchor=tk.W, pady=(0, 5))

        self.duration_var = tk.DoubleVar(value=self.current_duration)
        self.duration_entry = ttk.Entry(main_frame, textvariable=self.duration_var, width=20)
        self.duration_entry.pack(fill=tk.X, pady=5)
        self.duration_entry.focus_set()
        self.duration_entry.select_range(0, tk.END)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10, side=tk.BOTTOM, anchor=tk.E)
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(
            side=tk.LEFT, padx=5
        )

    def ok_clicked(self):
        try:
            self.result = self.duration_var.get()
            if self.result <= 0:
                messagebox.showerror("Error", "Duration must be greater than 0", parent=self.dialog)
                return
            self.dialog.destroy()
        except tk.TclError:
            messagebox.showerror("Error", "Please enter a valid number", parent=self.dialog)

    def cancel_clicked(self):
        self.dialog.destroy()

    def get_duration(self):
        self.dialog.wait_window()
        return self.result


class EditClickActionDialog:
    """Dialog for editing click actions"""

    def __init__(self, parent, action_type, current_x, current_y):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.action_type = action_type

        if action_type == ActionType.CLICK:
            title = "Edit Click Action"
        elif action_type == ActionType.DOUBLE_CLICK:
            title = "Edit Double-Click Action"
        elif action_type == ActionType.RIGHT_CLICK:
            title = "Edit Right-Click Action"
        else:
            title = "Edit Click Action"

        self.dialog.title(title)
        self.dialog.geometry("300x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.current_x = current_x
        self.current_y = current_y
        self.setup_dialog()

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def setup_dialog(self):
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="X coordinate:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.x_var = tk.IntVar(value=self.current_x)
        ttk.Entry(main_frame, textvariable=self.x_var, width=15).grid(
            row=0, column=1, padx=5, pady=5
        )

        ttk.Label(main_frame, text="Y coordinate:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.y_var = tk.IntVar(value=self.current_y)
        ttk.Entry(main_frame, textvariable=self.y_var, width=15).grid(
            row=1, column=1, padx=5, pady=5
        )

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky=tk.E)
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(
            side=tk.LEFT, padx=5
        )

    def ok_clicked(self):
        try:
            x = self.x_var.get()
            y = self.y_var.get()
            self.result = (x, y)
            self.dialog.destroy()
        except tk.TclError:
            messagebox.showerror("Error", "Please enter valid coordinates", parent=self.dialog)

    def cancel_clicked(self):
        self.dialog.destroy()

    def get_coordinates(self):
        self.dialog.wait_window()
        return self.result


class EditScrollActionDialog:
    """Dialog for editing scroll actions"""

    def __init__(self, parent, current_clicks):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Scroll Action")
        self.dialog.geometry("300x120")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.current_clicks = current_clicks
        self.setup_dialog()

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def setup_dialog(self):
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Number of clicks:").pack(anchor=tk.W, pady=(0, 5))

        self.clicks_var = tk.IntVar(value=self.current_clicks)
        self.clicks_entry = ttk.Entry(main_frame, textvariable=self.clicks_var, width=20)
        self.clicks_entry.pack(fill=tk.X, pady=5)
        self.clicks_entry.focus_set()
        self.clicks_entry.select_range(0, tk.END)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10, side=tk.BOTTOM, anchor=tk.E)
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(
            side=tk.LEFT, padx=5
        )

    def ok_clicked(self):
        try:
            self.result = self.clicks_var.get()
            self.dialog.destroy()
        except tk.TclError:
            messagebox.showerror("Error", "Please enter a valid number", parent=self.dialog)

    def cancel_clicked(self):
        self.dialog.destroy()

    def get_clicks(self):
        self.dialog.wait_window()
        return self.result


if __name__ == "__main__":
    app = ScreenAutomatorGUI()
    print("Starting GUI...")
    app.run()
