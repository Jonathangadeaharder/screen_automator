"""Common dialog components for the Screen Automator GUI."""

from typing import TYPE_CHECKING

import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, CENTER, DISABLED, LEFT, NORMAL, PRIMARY, RIGHT, X

try:
    import psutil
except ImportError:
    psutil = None

try:
    from win10toast import ToastNotifier
except ImportError:
    ToastNotifier = None

from core.localization import _

if TYPE_CHECKING:
    from gui_components.protocols import WindowProtocol


class TipDialog(tb.Toplevel):
    """Simple modal showing a random tip with Next button."""

    def __init__(self, master: "WindowProtocol", tip: str):
        super().__init__(master)
        self.title(_("Tip of the Day"))
        self.resizable(False, False)

        frame = tb.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)

        tb.Label(frame, text="💡", font=("Segoe UI", 24)).pack(pady=(0, 10))
        tb.Label(frame, text=tip, wraplength=300, justify=CENTER).pack(pady=10)

        chk_var = tb.BooleanVar(value=master.show_tips)
        chk = tb.Checkbutton(
            frame,
            text=_("Show tips on startup"),
            variable=chk_var,
            command=lambda: setattr(master, "show_tips", chk_var.get()),
        )
        chk.pack(pady=10)

        tb.Button(frame, text=_("Close"), command=self.destroy).pack(pady=10)

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


class ConflictsDialog(tb.Toplevel):
    """Dialog showing conflicts between rules."""

    def __init__(self, master: "WindowProtocol", conflicts):
        super().__init__(master)
        self.title(_("Rule Conflicts"))
        self.geometry("500x300")
        self.resizable(True, True)

        frame = tb.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)

        tb.Label(
            frame,
            text=_("The following rules have matching triggers but different actions:"),
            wraplength=460,
        ).pack(anchor="w", pady=(0, 10))

        # Conflicts list
        self.conflicts_list = tb.Treeview(
            frame, columns=("rule1", "rule2"), show="headings", height=8
        )
        self.conflicts_list.heading("rule1", text=_("Rule 1"))
        self.conflicts_list.heading("rule2", text=_("Rule 2"))
        self.conflicts_list.column("rule1", width=220)
        self.conflicts_list.column("rule2", width=220)
        self.conflicts_list.pack(fill=BOTH, expand=True, pady=10)

        # Add conflicts
        for c in conflicts:
            r1 = c["rule1"].name
            r2 = c["rule2"].name
            self.conflicts_list.insert("", "end", values=(r1, r2))

        info = tb.Label(
            frame,
            text=_(
                "Conflicts occur when multiple rules use the same trigger image. Only the highest priority rule will run."
            ),
            wraplength=460,
            foreground="gray",
        )
        info.pack(pady=10)

        tb.Button(frame, text=_("Close"), command=self.destroy).pack()

        # Modal
        self.transient(master)
        self.grab_set()


class FirstRuleWizard(tb.Toplevel):
    """3-step overlay wizard guiding user through first rule creation."""

    def __init__(self, master: "WindowProtocol"):
        super().__init__(master)
        self.title(_("Create Your First Rule"))
        self.geometry("600x400")
        self.resizable(False, False)

        # Store main window
        self.main_window = master

        frame = tb.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)

        # Header
        header = tb.Label(
            frame, text=_("Welcome to Screen Automator!"), font=("Segoe UI", 18, "bold")
        )
        header.pack(pady=(0, 20))

        # Steps
        self.steps = [
            _(
                'Step 1: Click "Capture Screen" to select a region of the screen that will trigger your automation.'
            ),
            _(
                "Step 2: Add actions that will run when the trigger is detected (clicks, key presses, text entry)."
            ),
            _("Step 3: Give your rule a name, save it, and enable monitoring to start automation."),
        ]

        self.idx = 0

        # Image
        self.img_label = tb.Label(frame)
        self.img_label.pack(pady=10)

        # Step text
        self.lbl = tb.Label(
            frame, text=self.steps[0], font=("Segoe UI", 12), wraplength=560, justify=CENTER
        )
        self.lbl.pack(pady=20)

        # Bottom buttons
        btn_frame = tb.Frame(frame)
        btn_frame.pack(fill=X, pady=20)

        self.btn_prev = tb.Button(
            btn_frame, text=_("Previous"), state=DISABLED, command=self._prev_step
        )
        self.btn_prev.pack(side=LEFT)

        self.btn_next = tb.Button(
            btn_frame, text=_("Next"), bootstyle=PRIMARY, command=self._next_step
        )
        self.btn_next.pack(side=RIGHT)

        tb.Button(btn_frame, text=_("Skip Tutorial"), command=self.destroy).pack(
            side=RIGHT, padx=10
        )

        # Center on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _next_step(self):
        """Go to next step."""
        if self.idx < len(self.steps) - 1:
            self.idx += 1
            self.lbl.configure(text=self.steps[self.idx])
            self.btn_prev.configure(state=NORMAL)
            if self.idx == len(self.steps) - 1:
                self.btn_next.configure(text=_("Finish"))
        else:
            self.destroy()

    def _prev_step(self):
        """Go to previous step."""
        if self.idx > 0:
            self.idx -= 1
            self.lbl.configure(text=self.steps[self.idx])
            if self.idx == 0:
                self.btn_prev.configure(state=DISABLED)
            self.btn_next.configure(text=_("Next"))


class PerformanceOverlay(tb.Toplevel):
    """Floating transparent window showing FPS and memory diagnostics."""

    def __init__(self, master: "WindowProtocol"):
        super().__init__(master)
        self.master_window = master
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        # Semi-transparent black background if supported
        try:
            self.attributes("-alpha", 0.7)
        except Exception:
            pass

        self.configure(bg="black")

        self.lbl_stats = tb.Label(
            self, text="--", foreground="lime", background="black", font=("Consolas", 12, "bold")
        )
        self.lbl_stats.pack(padx=10, pady=6)

        # Position top-left with slight margin
        self.geometry("+20+20")

        # periodic refresh
        self._refresh()

        # Close on click
        self.bind("<Button-1>", lambda *_: self.destroy())

    def _refresh(self):
        """Update performance statistics."""
        if not self.winfo_exists():
            return
        fps = getattr(self.master_window, "_last_fps", 0)
        mem = getattr(self.master_window, "_last_mem_mb", 0)
        self.lbl_stats.configure(text=f"FPS: {fps}\nMem: {mem} MB")
        self.after(500, self._refresh)


class TemplateLibraryDialog(tb.Toplevel):
    """Dialog showing pre-built rule templates for quick setup."""

    # Template definitions
    TEMPLATES = [
        {
            "name": "Auto-Click OK Button",
            "icon": "✓",
            "category": "Common",
            "description": "Automatically clicks 'OK' buttons when they appear on screen",
            "difficulty": "Beginner",
            "actions": ["Wait for OK button image", "Click at image location"],
        },
        {
            "name": "Auto-Close Popup",
            "icon": "✕",
            "category": "Common",
            "description": "Closes annoying popup windows with X button",
            "difficulty": "Beginner",
            "actions": ["Wait for close button image", "Click close button"],
        },
        {
            "name": "Form Auto-Fill",
            "icon": "📝",
            "category": "Productivity",
            "description": "Automatically fills out repetitive form fields",
            "difficulty": "Intermediate",
            "actions": ["Click field 1", "Type text", "Tab", "Type text", "Submit"],
        },
        {
            "name": "Login Automation",
            "icon": "🔐",
            "category": "Productivity",
            "description": "Automates login process with username and password",
            "difficulty": "Intermediate",
            "actions": [
                "Click username field",
                "Type username",
                "Tab",
                "Type password",
                "Press Enter",
            ],
        },
        {
            "name": "Screenshot on Error",
            "icon": "📸",
            "category": "Debugging",
            "description": "Takes a screenshot when error dialog appears",
            "difficulty": "Intermediate",
            "actions": ["Wait for error dialog", "Take screenshot", "Save to folder"],
        },
        {
            "name": "Timer Reminder",
            "icon": "⏰",
            "category": "Productivity",
            "description": "Shows reminder notification after set time",
            "difficulty": "Beginner",
            "actions": ["Wait 25 minutes", "Show notification", "Play sound"],
        },
        {
            "name": "File Downloader",
            "icon": "⬇️",
            "category": "Productivity",
            "description": "Clicks download button when page loads",
            "difficulty": "Beginner",
            "actions": ["Wait for download button", "Click button", "Wait 1s", "Close dialog"],
        },
        {
            "name": "Email Responder",
            "icon": "📧",
            "category": "Productivity",
            "description": "Auto-replies to specific emails with template",
            "difficulty": "Advanced",
            "actions": ["Wait for new email", "Open email", "Click reply", "Type message", "Send"],
        },
        {
            "name": "Window Closer",
            "icon": "🗔",
            "category": "Common",
            "description": "Closes specific windows when they open",
            "difficulty": "Beginner",
            "actions": ["Wait for window title", "Press Alt+F4"],
        },
        {
            "name": "Copy-Paste Automation",
            "icon": "📋",
            "category": "Productivity",
            "description": "Copies text from one field to another",
            "difficulty": "Intermediate",
            "actions": ["Click source field", "Ctrl+A", "Ctrl+C", "Click target", "Ctrl+V"],
        },
        {
            "name": "Idle Detector",
            "icon": "💤",
            "category": "Monitoring",
            "description": "Performs action when user is idle for X minutes",
            "difficulty": "Advanced",
            "actions": ["Wait for idle state", "Show notification", "Execute custom action"],
        },
        {
            "name": "Page Refresher",
            "icon": "🔄",
            "category": "Monitoring",
            "description": "Refreshes page every X seconds",
            "difficulty": "Beginner",
            "actions": ["Wait 30 seconds", "Press F5", "Repeat"],
        },
    ]

    def __init__(self, master: "WindowProtocol"):
        super().__init__(master)
        self.master_window = master
        self.selected_template = None

        self.title(_("Template Library"))
        self.geometry("800x600")
        self.resizable(True, True)

        # Main container with padding
        main_frame = tb.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        # Header
        header_frame = tb.Frame(main_frame)
        header_frame.pack(fill=X, pady=(0, 20))

        title_label = tb.Label(
            header_frame, text=_("Choose a Template"), font=("Segoe UI", 18, "bold")
        )
        title_label.pack(side=LEFT)

        subtitle_label = tb.Label(
            header_frame,
            text=_(f"{len(self.TEMPLATES)} pre-built templates to get you started"),
            font=("Segoe UI", 10),
            foreground="#6c757d",
        )
        subtitle_label.pack(side=LEFT, padx=(10, 0))

        # Search/filter frame
        filter_frame = tb.Frame(main_frame)
        filter_frame.pack(fill=X, pady=(0, 10))

        tb.Label(filter_frame, text=_("Category:")).pack(side=LEFT, padx=(0, 5))

        self.category_var = tb.StringVar(value="All")
        categories = ["All", "Common", "Productivity", "Debugging", "Monitoring"]
        category_combo = tb.Combobox(
            filter_frame,
            textvariable=self.category_var,
            values=categories,
            state="readonly",
            width=15,
        )
        category_combo.pack(side=LEFT, padx=(0, 10))
        category_combo.bind("<<ComboboxSelected>>", lambda e: self._filter_templates())

        # Templates list (scrollable)
        list_frame = tb.Frame(main_frame)
        list_frame.pack(fill=BOTH, expand=True, pady=(0, 10))

        # Create canvas for scrolling
        canvas = tb.Canvas(list_frame, highlightthickness=0)
        scrollbar = tb.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.templates_frame = tb.Frame(canvas)

        self.templates_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.templates_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill="y")

        # Bottom buttons
        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=X, pady=(10, 0))

        tb.Button(button_frame, text=_("Cancel"), command=self.destroy, width=12).pack(
            side=RIGHT, padx=(5, 0)
        )

        self.use_btn = tb.Button(
            button_frame,
            text=_("Use Template"),
            bootstyle=PRIMARY,
            command=self._use_template,
            width=15,
            state=DISABLED,
        )
        self.use_btn.pack(side=RIGHT)

        # Populate templates
        self._populate_templates()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

        # Modal
        self.transient(master)
        self.grab_set()

    def _populate_templates(self):
        """Populate the templates list with cards."""
        # Clear existing
        for widget in self.templates_frame.winfo_children():
            widget.destroy()

        category_filter = self.category_var.get()

        for template in self.TEMPLATES:
            if category_filter != "All" and template["category"] != category_filter:
                continue

            self._create_template_card(template)

    def _create_template_card(self, template):
        """Create a card widget for a template."""
        card = tb.Frame(self.templates_frame, padding=15, relief="raised", borderwidth=1)
        card.pack(fill=X, pady=5)

        # Make card clickable
        card.bind("<Button-1>", lambda e, t=template: self._select_template(t))

        # Header row (icon + name + difficulty badge)
        header = tb.Frame(card)
        header.pack(fill=X, pady=(0, 5))

        # Icon
        icon_label = tb.Label(header, text=template["icon"], font=("Segoe UI", 20))
        icon_label.pack(side=LEFT, padx=(0, 10))
        icon_label.bind("<Button-1>", lambda e, t=template: self._select_template(t))

        # Name and category
        name_frame = tb.Frame(header)
        name_frame.pack(side=LEFT, fill=X, expand=True)
        name_frame.bind("<Button-1>", lambda e, t=template: self._select_template(t))

        name_label = tb.Label(name_frame, text=template["name"], font=("Segoe UI", 12, "bold"))
        name_label.pack(anchor="w")
        name_label.bind("<Button-1>", lambda e, t=template: self._select_template(t))

        category_label = tb.Label(
            name_frame, text=template["category"], font=("Segoe UI", 9), foreground="#6c757d"
        )
        category_label.pack(anchor="w")
        category_label.bind("<Button-1>", lambda e, t=template: self._select_template(t))

        # Difficulty badge
        difficulty_colors = {"Beginner": "success", "Intermediate": "warning", "Advanced": "danger"}
        difficulty_badge = tb.Label(
            header,
            text=template["difficulty"],
            bootstyle=f"{difficulty_colors[template['difficulty']]}-inverse",
            padding=5,
        )
        difficulty_badge.pack(side=RIGHT)
        difficulty_badge.bind("<Button-1>", lambda e, t=template: self._select_template(t))

        # Description
        desc_label = tb.Label(
            card, text=template["description"], wraplength=700, justify=LEFT, font=("Segoe UI", 10)
        )
        desc_label.pack(anchor="w", pady=(0, 5))
        desc_label.bind("<Button-1>", lambda e, t=template: self._select_template(t))

        # Actions preview
        actions_text = " → ".join(template["actions"][:3])
        if len(template["actions"]) > 3:
            actions_text += "..."

        actions_label = tb.Label(
            card,
            text=f"📋 {actions_text}",
            font=("Segoe UI", 9),
            foreground="#495057",
            wraplength=700,
            justify=LEFT,
        )
        actions_label.pack(anchor="w")
        actions_label.bind("<Button-1>", lambda e, t=template: self._select_template(t))

        # Store card reference
        card._template = template

    def _filter_templates(self):
        """Filter templates by category."""
        self._populate_templates()

    def _select_template(self, template):
        """Select a template."""
        self.selected_template = template
        self.use_btn.configure(state=NORMAL)

        # Visual feedback - highlight selected card
        for card in self.templates_frame.winfo_children():
            if hasattr(card, "_template") and card._template == template:
                card.configure(bootstyle="primary", relief="solid", borderwidth=2)
            else:
                card.configure(relief="raised", borderwidth=1)

    def _use_template(self):
        """Use the selected template."""
        if self.selected_template:
            # Show success toast
            self.master_window.show_toast(
                _(f"Template '{self.selected_template['name']}' selected!"),
                toast_type="success",
                duration=3000,
            )

            # In a real implementation, this would create a rule from the template
            # For now, just close the dialog
            self.destroy()
