"""MainWindow class for Screen Automator GUI."""

import os

try:
    import psutil
except ImportError:
    psutil = None

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.tooltip import ToolTip

from core.localization import _
from gui_components.dialogs import (
    FirstRuleWizard,
    PerformanceOverlay,
    TemplateLibraryDialog,
    TipDialog,
)
from gui_components.widgets import (
    CollapsiblePane,
    SearchEntry,
    ToastNotification,
)
from src.automator import ScreenAutomator
from utils import load_config, save_config


class MainWindow(tb.Window):
    """Main application window for Screen Automator."""

    def __init__(self):
        super().__init__(title=_("Screen Automator"), themename="flatly")
        self.automator = ScreenAutomator()
        self.cfg = load_config("settings.json")
        self.show_tips = self.cfg.get("show_tips", True)
        self.telemetry_opt_in = self.cfg.get("telemetry", False)
        self._frame_count = 0
        self._mem_warned = False
        self._last_fps = 0
        self._last_mem_mb = 0
        self._perf_overlay = None
        self.after_idle(self._increase_frame)
        self.after(1000, self._update_status)
        self._build_toolbar()
        self._build_panes()
        self._build_status_bar()
        self._setup_keyboard_shortcuts()
        self.refresh_rules()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.notifier = None

    def show_error(self, title, message, details=None):
        """
        Show user-friendly error dialog.

        Args:
            title: Short error summary
            message: User-friendly explanation
            details: Technical details (optional, collapsible)
        """
        dialog = tb.Toplevel(self)
        dialog.title(title)
        dialog.geometry("500x300" if details else "500x200")
        dialog.resizable(False, False)

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Main content frame
        content_frame = tb.Frame(dialog, padding=20)
        content_frame.pack(fill=BOTH, expand=True)

        # Error icon and message
        icon_label = tb.Label(content_frame, text="❌", font=("Segoe UI", 24))
        icon_label.pack(pady=(0, 10))

        message_label = tb.Label(
            content_frame, text=message, wraplength=450, justify=LEFT, font=("Segoe UI", 11)
        )
        message_label.pack(pady=(0, 15))

        # Optional details (collapsible)
        if details:
            details_pane = CollapsiblePane(content_frame, text=_("Technical Details"))
            details_pane.pack(fill=X, pady=(0, 15))

            details_text = tb.Text(
                details_pane.content, height=4, wrap=WORD, font=("Courier New", 9)
            )
            details_text.insert("1.0", str(details))
            details_text.configure(state=DISABLED)
            details_text.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Close button
        button_frame = tb.Frame(content_frame)
        button_frame.pack(side=BOTTOM, fill=X)
        tb.Button(
            button_frame, text=_("OK"), command=dialog.destroy, bootstyle=PRIMARY, width=12
        ).pack(side=RIGHT)

        # Make modal
        dialog.transient(self)
        dialog.grab_set()
        self.wait_window(dialog)

    def show_message(self, title, message, icon="info"):
        """
        Show a message dialog.

        Args:
            title: Dialog title
            message: Message text
            icon: Icon type ("info", "warning", "success", "error")
        """
        import tkinter.messagebox as messagebox

        icon_map = {
            "info": messagebox.showinfo,
            "warning": messagebox.showwarning,
            "success": messagebox.showinfo,
            "error": messagebox.showerror,
        }

        show_func = icon_map.get(icon, messagebox.showinfo)
        show_func(title, message)

    def show_toast(
        self, message, toast_type="info", duration=3000, action_text=None, action_callback=None
    ):
        """
        Show a toast notification.

        Args:
            message: Message to display
            toast_type: Type of toast ('success', 'info', 'warning', 'error')
            duration: Auto-dismiss duration in ms (None for manual dismiss, 0 for errors)
            action_text: Optional action button text
            action_callback: Optional action button callback
        """
        ToastNotification(
            self,
            message=message,
            toast_type=toast_type,
            duration=duration if toast_type != "error" else None,
            action_text=action_text,
            action_callback=action_callback,
        )

    def update_status(self, message):
        """
        Update status bar message.

        Args:
            message: Status message to display
        """
        # For now, just print to console
        # TODO: Add actual status bar label for messages
        print(f"Status: {message}")

    def get_rules_dir(self):
        """
        Get the rules directory path.

        Returns:
            Path to rules directory
        """
        from pathlib import Path

        return Path("rules")

    def get_current_rule(self):
        """
        Get the currently selected rule.

        Returns:
            Currently selected rule or None
        """
        selection = self.rules_tree.selection()
        if not selection:
            return None

        rule_id = selection[0]
        return self.automator.rule_manager.get_rule(rule_id)

    def refresh_rules_list(self):
        """Refresh the rules list display."""
        self.refresh_rules()

    def _build_toolbar(self):
        toolbar = tb.Frame(self, padding=10)
        toolbar.pack(fill=X)

        # Menu/Sidebar toggle
        btn_menu = tb.Button(toolbar, text=f'☰ {_("Menu")}', command=self._toggle_sidebar)
        btn_menu.pack(side=LEFT, padx=(0, 8))
        ToolTip(btn_menu, text=_("Toggle sidebar visibility"))

        # New rule
        btn_new = tb.Button(
            toolbar, text=f'➕ {_("New")}', bootstyle=PRIMARY, command=self._new_rule
        )
        btn_new.pack(side=LEFT, padx=2)
        ToolTip(btn_new, text=_("Create a new automation rule (Ctrl+N)"))

        # Edit rule
        btn_edit = tb.Button(toolbar, text=f'✏ {_("Edit")}', command=self._edit_rule)
        btn_edit.pack(side=LEFT, padx=2)
        ToolTip(btn_edit, text=_("Edit the selected rule (Ctrl+E)"))

        # Delete rule
        btn_delete = tb.Button(
            toolbar, text=f'🗑 {_("Delete")}', bootstyle=DANGER, command=self._delete_rule
        )
        btn_delete.pack(side=LEFT, padx=2)
        ToolTip(btn_delete, text=_("Delete the selected rule (Delete)"))

        # Test rule
        btn_test = tb.Button(
            toolbar, text=f'▶ {_("Test")}', bootstyle=SUCCESS, command=self._test_rule
        )
        btn_test.pack(side=LEFT, padx=2)
        ToolTip(btn_test, text=_("Test the selected rule (Ctrl+T)"))

        # Conflicts button (hidden by default)
        self.btn_conflicts = tb.Button(
            toolbar, text="⚠ 0", bootstyle=WARNING, command=self._show_conflicts_dialog
        )
        self.btn_conflicts.pack(side=LEFT, padx=2)
        self.btn_conflicts.pack_forget()
        ToolTip(self.btn_conflicts, text=_("View rule conflicts"))

        # Settings button
        btn_settings = tb.Button(
            toolbar, text=f'⚙️ {_("Settings")}', command=self._open_settings_dialog
        )
        btn_settings.pack(side=RIGHT, padx=5)
        ToolTip(btn_settings, text=_("Open application settings"))

        # Monitor toggle
        self.btn_toggle_monitor = tb.Button(
            toolbar, text=_("Show Monitor"), command=self._toggle_monitor
        )
        self.btn_toggle_monitor.pack(side=RIGHT, padx=5)
        ToolTip(self.btn_toggle_monitor, text=_("Start/stop rule monitoring"))

        # Tips button
        btn_tips = tb.Button(toolbar, text=f'💡 {_("Tips")}', command=self._show_tip)
        btn_tips.pack(side=RIGHT, padx=5)
        ToolTip(btn_tips, text=_("Show helpful tips (F1)"))

        # Help button
        btn_help = tb.Button(toolbar, text=f'❓ {_("Help")}', command=self._show_help)
        btn_help.pack(side=RIGHT, padx=5)
        ToolTip(btn_help, text=_("Open help documentation"))

        # Columns button
        btn_columns = tb.Button(
            toolbar, text=f'📑 {_("Columns")}', command=self._open_column_dialog
        )
        btn_columns.pack(side=RIGHT, padx=5)
        ToolTip(btn_columns, text=_("Configure visible columns"))

        # Theme toggle
        self.btn_theme = tb.Button(toolbar, text=f'🌙 {_("Theme")}', command=self._toggle_theme)
        self.btn_theme.pack(side=RIGHT, padx=5)
        ToolTip(self.btn_theme, text=_("Switch between light and dark theme"))

        # Performance overlay
        btn_perf = tb.Button(
            toolbar, text=f'⚡ {_("Performance")}', command=self._toggle_perf_overlay
        )
        btn_perf.pack(side=RIGHT, padx=5)
        ToolTip(btn_perf, text=_("Show performance metrics (F12)"))

        # Search entry
        self.entry_search = SearchEntry(toolbar, callback=self._filter_rules, width=25)
        self.entry_search.pack(side=RIGHT, padx=5)
        ToolTip(self.entry_search, text=_("Filter rules by name or description"))

    def _build_panes(self):
        self.paned = tb.PanedWindow(self, orient=HORIZONTAL)
        self.paned.pack(fill=BOTH, expand=True)
        self.sidebar = tb.Frame(self.paned, padding=5)
        self.sidebar.configure(width=180)
        self.paned.add(self.sidebar, weight=0)
        self.sidebar_visible = True
        self.main_container = tb.Frame(self.paned)
        self.paned.add(self.main_container, weight=1)

        # Build rules list in main container
        rules_frame = tb.LabelFrame(self.main_container, text=_("Rules"), padding=10)
        rules_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Empty state frame (shown when no rules exist)
        self.empty_state_frame = tb.Frame(rules_frame)

        empty_icon = tb.Label(self.empty_state_frame, text="📋", font=("Segoe UI", 48))
        empty_icon.pack(pady=(40, 20))

        empty_title = tb.Label(
            self.empty_state_frame, text=_("No Automation Rules Yet"), font=("Segoe UI", 16, "bold")
        )
        empty_title.pack(pady=(0, 10))

        empty_desc = tb.Label(
            self.empty_state_frame,
            text=_(
                "Create your first rule to automate repetitive tasks.\nRules can click buttons, type text, and perform actions when images appear."
            ),
            font=("Segoe UI", 11),
            justify=CENTER,
            wraplength=400,
        )
        empty_desc.pack(pady=(0, 30))

        create_btn = tb.Button(
            self.empty_state_frame,
            text=f'➕ {_("Create Your First Rule")}',
            bootstyle=PRIMARY,
            command=self._new_rule,
            width=25,
        )
        create_btn.pack(pady=(0, 10))

        tips_btn = tb.Button(
            self.empty_state_frame,
            text=f'📚 {_("Browse Templates")}',
            command=self._show_template_library,
            width=25,
        )
        tips_btn.pack()

        # Create treeview for rules
        columns = ("status", "name", "enabled", "last_run", "description")
        self.rules_tree = tb.Treeview(rules_frame, columns=columns, show="headings", height=15)

        # Define headings
        self.rules_tree.heading("status", text=_("Status"))
        self.rules_tree.heading("name", text=_("Name"))
        self.rules_tree.heading("enabled", text=_("Enabled"))
        self.rules_tree.heading("last_run", text=_("Last Run"))
        self.rules_tree.heading("description", text=_("Description"))

        # Configure column widths
        self.rules_tree.column("status", width=70, anchor=CENTER)
        self.rules_tree.column("name", width=180)
        self.rules_tree.column("enabled", width=70, anchor=CENTER)
        self.rules_tree.column("last_run", width=120)
        self.rules_tree.column("description", width=250)

        # Configure tags for status colors
        self.rules_tree.tag_configure("success", foreground="#198754")  # Green
        self.rules_tree.tag_configure("error", foreground="#dc3545")  # Red
        self.rules_tree.tag_configure("running", foreground="#0d6efd")  # Blue
        self.rules_tree.tag_configure("idle", foreground="#6c757d")  # Gray

        # Add scrollbar
        scrollbar = tb.Scrollbar(rules_frame, orient=VERTICAL, command=self.rules_tree.yview)
        self.rules_tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview and scrollbar
        self.rules_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

    def _build_status_bar(self):
        bar = tb.Frame(self)
        bar.pack(fill=X, side=BOTTOM)
        self.lbl_fps = tb.Label(bar, text=_("FPS: --"))
        self.lbl_fps.pack(side=LEFT, padx=5)
        self.mem_var = tb.IntVar(value=0)
        self.mem_bar = tb.Progressbar(bar, maximum=500, variable=self.mem_var, length=120)
        self.mem_bar.pack(side=LEFT, padx=5)
        self.lbl_mem = tb.Label(bar, text=_("Mem: -- MB"))
        self.lbl_mem.pack(side=LEFT, padx=5)

    def _setup_keyboard_shortcuts(self):
        """Setup global keyboard shortcuts for the application."""
        # Rule management shortcuts
        self.bind_all("<Control-n>", lambda e: self._new_rule())
        self.bind_all("<Control-N>", lambda e: self._new_rule())
        self.bind_all("<Control-e>", lambda e: self._edit_rule())
        self.bind_all("<Control-E>", lambda e: self._edit_rule())
        self.bind_all("<Delete>", lambda e: self._delete_rule())
        self.bind_all("<Control-t>", lambda e: self._test_rule())
        self.bind_all("<Control-T>", lambda e: self._test_rule())

        # Utility shortcuts
        self.bind_all("<F1>", lambda e: self._show_tip())
        self.bind_all("<F12>", lambda e: self._toggle_perf_overlay())
        self.bind_all("<Control-q>", lambda e: self._on_close())
        self.bind_all("<Control-Q>", lambda e: self._on_close())

        # Refresh shortcut
        self.bind_all("<F5>", lambda e: self.refresh_rules())

        # Show toast with keyboard shortcut info on first launch
        if not self.cfg.get("shortcuts_shown", False):
            self.after(
                1000,
                lambda: self.show_toast(
                    _("Tip: Use Ctrl+N for new rule, Ctrl+E to edit, F1 for help"),
                    toast_type="info",
                    duration=5000,
                ),
            )
            self.cfg["shortcuts_shown"] = True
            save_config("settings.json", self.cfg)

    def _increase_frame(self):
        self._frame_count += 1
        self.after_idle(self._increase_frame)

    def _update_status(self):
        fps = self._frame_count
        self._frame_count = 0
        self.lbl_fps.configure(text=f'{_("FPS: ")}{fps}')
        self._last_fps = fps
        if psutil:
            import psutil

            mem_mb = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
            mem_mb_int = int(mem_mb)
            self._last_mem_mb = mem_mb_int
            self.lbl_mem.configure(text=f'{_("Mem: ")}{mem_mb_int} MB')
            self.mem_var.set(min(mem_mb_int, 500))
        self.after(1000, self._update_status)

    def _toggle_perf_overlay(self):
        if self._perf_overlay and self._perf_overlay.winfo_exists():
            self._perf_overlay.destroy()
            self._perf_overlay = None
        else:
            self._perf_overlay = PerformanceOverlay(self)

    def _toggle_sidebar(self):
        """Toggle the sidebar visibility"""
        if self.sidebar_visible:
            self.paned.forget(self.sidebar)
            self.sidebar_visible = False
        else:
            self.paned.add(self.sidebar, weight=0)
            self.sidebar_visible = True

    def _new_rule(self):
        """Create a new automation rule"""
        try:
            FirstRuleWizard(self)
            # Handle new rule creation
        except Exception as e:
            self.show_error(
                title=_("Cannot Create Rule"),
                message=_("Unable to open the rule creation wizard. Please try again."),
                details=str(e),
            )

    def _edit_rule(self):
        """Edit the selected rule"""
        try:
            selected_rule = self.get_current_rule()
            if not selected_rule:
                self.show_message(
                    title=_("No Rule Selected"),
                    message=_("Please select a rule from the list to edit."),
                    icon="info",
                )
                return

            self.show_message(
                title=_("Feature Not Available"),
                message=_("Rule editing is not yet implemented. This feature is coming soon!"),
                icon="info",
            )
        except Exception as e:
            self.show_error(
                title=_("Cannot Edit Rule"),
                message=_("An error occurred while trying to edit the rule."),
                details=str(e),
            )

    def _delete_rule(self):
        """Delete the selected rule"""
        try:
            selected_rule = self.get_current_rule()
            if not selected_rule:
                self.show_message(
                    title=_("No Rule Selected"),
                    message=_("Please select a rule from the list to delete."),
                    icon="info",
                )
                return

            self.show_message(
                title=_("Feature Not Available"),
                message=_("Rule deletion is not yet implemented. This feature is coming soon!"),
                icon="info",
            )
        except Exception as e:
            self.show_error(
                title=_("Cannot Delete Rule"),
                message=_("An error occurred while trying to delete the rule."),
                details=str(e),
            )

    def _test_rule(self):
        """Test the selected rule"""
        try:
            selected_rule = self.get_current_rule()
            if not selected_rule:
                self.show_message(
                    title=_("No Rule Selected"),
                    message=_("Please select a rule from the list to test."),
                    icon="info",
                )
                return

            self.show_message(
                title=_("Feature Not Available"),
                message=_("Rule testing is not yet implemented. This feature is coming soon!"),
                icon="info",
            )
        except Exception as e:
            self.show_error(
                title=_("Cannot Test Rule"),
                message=_("An error occurred while trying to test the rule."),
                details=str(e),
            )

    def _show_conflicts_dialog(self):
        """Show conflicts dialog"""
        try:
            self.show_message(
                title=_("Feature Not Available"),
                message=_(
                    "Conflict resolution is not yet implemented. This feature is coming soon!"
                ),
                icon="info",
            )
        except Exception as e:
            self.show_error(
                title=_("Cannot Show Conflicts"),
                message=_("An error occurred while trying to show conflicts."),
                details=str(e),
            )

    def _filter_rules(self, query):
        """Filter rules based on search query"""
        try:
            # TODO: Implement actual filtering logic
            print(f"Filtering rules with query: {query}")
        except Exception as e:
            self.show_error(
                title=_("Cannot Filter Rules"),
                message=_("An error occurred while filtering the rules list."),
                details=str(e),
            )

    def _toggle_theme(self):
        """Toggle between light and dark theme"""
        try:
            current_theme = self.style.theme_use()
            if "dark" in current_theme:
                self.style.theme_use("flatly")
                self.btn_theme.configure(text=f'🌙 {_("Theme")}')
                self.show_toast(_("Switched to light theme"), toast_type="success", duration=2000)
            else:
                self.style.theme_use("darkly")
                self.btn_theme.configure(text=f'☀️ {_("Theme")}')
                self.show_toast(_("Switched to dark theme"), toast_type="success", duration=2000)
        except Exception as e:
            self.show_error(
                title=_("Cannot Change Theme"),
                message=_("An error occurred while switching the theme."),
                details=str(e),
            )

    def _open_column_dialog(self):
        """Open column configuration dialog"""
        try:
            self.show_message(
                title=_("Feature Not Available"),
                message=_(
                    "Column configuration is not yet implemented. This feature is coming soon!"
                ),
                icon="info",
            )
        except Exception as e:
            self.show_error(
                title=_("Cannot Open Column Dialog"),
                message=_("An error occurred while trying to open column settings."),
                details=str(e),
            )

    def _show_help(self):
        """Show help dialog"""
        try:
            self.show_message(
                title=_("Feature Not Available"),
                message=_(
                    "Help documentation is not yet implemented. This feature is coming soon!"
                ),
                icon="info",
            )
        except Exception as e:
            self.show_error(
                title=_("Cannot Show Help"),
                message=_("An error occurred while trying to show help."),
                details=str(e),
            )

    def _show_tip(self):
        """Show tip dialog"""
        try:
            if self.show_tips:
                TipDialog(self)
        except Exception as e:
            self.show_error(
                title=_("Cannot Show Tip"),
                message=_("An error occurred while trying to show the tip dialog."),
                details=str(e),
            )

    def _show_template_library(self):
        """Show template library dialog"""
        try:
            TemplateLibraryDialog(self)
        except Exception as e:
            self.show_error(
                title=_("Cannot Open Template Library"),
                message=_("An error occurred while trying to open the template library."),
                details=str(e),
            )

    def _toggle_monitor(self):
        """Toggle monitoring on/off"""
        try:
            if self.automator.is_monitoring:
                self.automator.stop_monitoring()
                self.btn_toggle_monitor.configure(text=_("Start Monitor"))
                self.show_toast(_("Monitoring stopped"), toast_type="info", duration=2000)
            else:
                self.automator.start_monitoring()
                self.btn_toggle_monitor.configure(text=_("Stop Monitor"))
                self.show_toast(_("Monitoring started"), toast_type="success", duration=2000)
        except Exception as e:
            self.show_error(
                title=_("Cannot Toggle Monitor"),
                message=_("An error occurred while starting or stopping the monitor."),
                details=str(e),
            )

    def _open_settings_dialog(self):
        """Open settings dialog"""
        try:
            self.show_message(
                title=_("Feature Not Available"),
                message=_("Settings dialog is not yet implemented. This feature is coming soon!"),
                icon="info",
            )
        except Exception as e:
            self.show_error(
                title=_("Cannot Open Settings"),
                message=_("An error occurred while trying to open settings."),
                details=str(e),
            )

    def refresh_rules(self):
        """Refresh the rules list"""
        try:
            # Clear existing items
            for item in self.rules_tree.get_children():
                self.rules_tree.delete(item)

            # Load rules from rule manager
            rules = self.automator.rule_manager.list_rules()

            # Show/hide empty state based on rule count
            if len(rules) == 0:
                # Show empty state
                self.empty_state_frame.pack(fill=BOTH, expand=True)
                self.rules_tree.pack_forget()
            else:
                # Show rules list
                self.empty_state_frame.pack_forget()
                if not self.rules_tree.winfo_ismapped():
                    self.rules_tree.pack(side=LEFT, fill=BOTH, expand=True)

            # Populate treeview
            for rule in rules:
                # Status badge and tag (idle, success, error)
                status_badge = "⏸ Idle"  # Default
                status_tag = "idle"
                if hasattr(rule, "last_execution_status"):
                    if rule.last_execution_status == "success":
                        status_badge = "✓ Success"
                        status_tag = "success"
                    elif rule.last_execution_status == "error":
                        status_badge = "❌ Error"
                        status_tag = "error"
                    elif rule.last_execution_status == "running":
                        status_badge = "▶ Running"
                        status_tag = "running"

                # Enabled status
                enabled_text = "✓" if rule.enabled else "○"

                # Last run time
                last_run_text = _("Never")
                if hasattr(rule, "last_execution_time") and rule.last_execution_time:
                    import datetime

                    try:
                        # Try to parse if it's a string
                        if isinstance(rule.last_execution_time, str):
                            dt = datetime.datetime.fromisoformat(rule.last_execution_time)
                        else:
                            dt = rule.last_execution_time

                        # Format as relative time
                        now = datetime.datetime.now()
                        diff = now - dt

                        if diff.days > 0:
                            last_run_text = _(f"{diff.days}d ago")
                        elif diff.seconds >= 3600:
                            hours = diff.seconds // 3600
                            last_run_text = _(f"{hours}h ago")
                        elif diff.seconds >= 60:
                            minutes = diff.seconds // 60
                            last_run_text = _(f"{minutes}m ago")
                        else:
                            last_run_text = _("Just now")
                    except:
                        last_run_text = _("Unknown")

                self.rules_tree.insert(
                    "",
                    "end",
                    iid=rule.id,
                    values=(
                        status_badge,
                        rule.name,
                        enabled_text,
                        last_run_text,
                        rule.description or "",
                    ),
                    tags=(status_tag,),
                )

            # Show toast with count (only if called explicitly, not on initial load)
            if hasattr(self, "_initial_load_done"):
                if len(rules) == 0:
                    self.show_toast(_("No rules found"), toast_type="info", duration=2000)
                else:
                    self.show_toast(
                        _(f"Loaded {len(rules)} rule(s)"), toast_type="success", duration=2000
                    )
            else:
                self._initial_load_done = True

        except Exception as e:
            self.show_error(
                title=_("Cannot Refresh Rules"),
                message=_("An error occurred while loading the rules list."),
                details=str(e),
            )

    def _on_close(self):
        """Handle window close event"""
        try:
            if self.automator.is_monitoring:
                self.automator.stop_monitoring()
            save_config("settings.json", self.cfg)
            self.destroy()
        except Exception as e:
            # On close errors, just log and destroy anyway
            print(f"Error during cleanup: {e}")
            self.destroy()
