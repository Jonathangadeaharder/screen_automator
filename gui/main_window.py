"""MainWindow class for Screen Automator GUI."""

import os
import sys
import threading
import time
from typing import Any, Dict, Optional

try:
    import psutil
except ImportError:
    psutil = None

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.tooltip import ToolTip

from core.localization import _
from core.telemetry import send_telemetry
from gui_components.dialogs import FirstRuleWizard, PerformanceOverlay, TipDialog
from gui_components.record_hud import RecordHUD
from gui_components.rule_editor import RuleEditor
from gui_components.widgets import (
    CollapsiblePane,
    ColorBox,
    ConfirmDialog,
    KeybindField,
    SearchEntry,
    StatusIndicator,
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
        self.refresh_rules()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.notifier = None

    def _build_toolbar(self):
        toolbar = tb.Frame(self, padding=10)
        toolbar.pack(fill=X)
        tb.Button(toolbar, text="☰", command=self._toggle_sidebar).pack(side=LEFT, padx=(0, 8))
        tb.Button(toolbar, text=f'➕ {_("New")}', bootstyle=PRIMARY, command=self._new_rule).pack(
            side=LEFT, padx=2
        )
        tb.Button(toolbar, text=f'✏ {_("Edit")}', command=self._edit_rule).pack(side=LEFT, padx=2)
        tb.Button(
            toolbar, text=f'🗑 {_("Delete")}', bootstyle=DANGER, command=self._delete_rule
        ).pack(side=LEFT, padx=2)
        tb.Button(toolbar, text=f'▶ {_("Test")}', bootstyle=SUCCESS, command=self._test_rule).pack(
            side=LEFT, padx=2
        )
        self.btn_conflicts = tb.Button(
            toolbar, text="⚠ 0", bootstyle=WARNING, command=self._show_conflicts_dialog
        )
        self.btn_conflicts.pack(side=LEFT, padx=2)
        self.btn_conflicts.pack_forget()
        self.entry_search = SearchEntry(toolbar, callback=self._filter_rules, width=25)
        self.entry_search.pack(side=RIGHT, padx=5)
        ToolTip(self.entry_search, text=_("Filter rules (type)"))
        tb.Button(toolbar, text="⚡", command=self._toggle_perf_overlay).pack(side=RIGHT, padx=5)
        self.btn_theme = tb.Button(toolbar, text="🌙", command=self._toggle_theme)
        self.btn_theme.pack(side=RIGHT, padx=5)
        tb.Button(toolbar, text="📑", command=self._open_column_dialog).pack(side=RIGHT, padx=5)
        tb.Button(toolbar, text="❓", command=self._show_help).pack(side=RIGHT, padx=5)
        tb.Button(toolbar, text="💡", command=self._show_tip).pack(side=RIGHT, padx=5)
        self.btn_toggle_monitor = tb.Button(
            toolbar, text=_("Show Monitor"), command=self._toggle_monitor
        )
        self.btn_toggle_monitor.pack(side=RIGHT, padx=5)
        tb.Button(toolbar, text="⚙️", command=self._open_settings_dialog).pack(side=RIGHT, padx=5)

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

        # Create treeview for rules
        columns = ("name", "enabled", "description")
        self.rules_tree = tb.Treeview(rules_frame, columns=columns, show="headings", height=15)

        # Define headings
        self.rules_tree.heading("name", text=_("Name"))
        self.rules_tree.heading("enabled", text=_("Enabled"))
        self.rules_tree.heading("description", text=_("Description"))

        # Configure column widths
        self.rules_tree.column("name", width=200)
        self.rules_tree.column("enabled", width=80)
        self.rules_tree.column("description", width=300)

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
            wizard = FirstRuleWizard(self)
            # Handle new rule creation
        except Exception as e:
            print(f"Error creating new rule: {e}")

    def _edit_rule(self):
        """Edit the selected rule"""
        try:
            # Get selected rule and open editor
            print("Edit rule functionality not yet implemented")
        except Exception as e:
            print(f"Error editing rule: {e}")

    def _delete_rule(self):
        """Delete the selected rule"""
        try:
            # Confirm and delete selected rule
            print("Delete rule functionality not yet implemented")
        except Exception as e:
            print(f"Error deleting rule: {e}")

    def _test_rule(self):
        """Test the selected rule"""
        try:
            # Test the selected rule
            print("Test rule functionality not yet implemented")
        except Exception as e:
            print(f"Error testing rule: {e}")

    def _show_conflicts_dialog(self):
        """Show conflicts dialog"""
        try:
            print("Show conflicts dialog not yet implemented")
        except Exception as e:
            print(f"Error showing conflicts: {e}")

    def _filter_rules(self, query):
        """Filter rules based on search query"""
        try:
            print(f"Filtering rules with query: {query}")
        except Exception as e:
            print(f"Error filtering rules: {e}")

    def _toggle_theme(self):
        """Toggle between light and dark theme"""
        try:
            current_theme = self.style.theme_use()
            if "dark" in current_theme:
                self.style.theme_use("flatly")
                self.btn_theme.configure(text="🌙")
            else:
                self.style.theme_use("darkly")
                self.btn_theme.configure(text="☀️")
        except Exception as e:
            print(f"Error toggling theme: {e}")

    def _open_column_dialog(self):
        """Open column configuration dialog"""
        try:
            print("Column dialog not yet implemented")
        except Exception as e:
            print(f"Error opening column dialog: {e}")

    def _show_help(self):
        """Show help dialog"""
        try:
            print("Help dialog not yet implemented")
        except Exception as e:
            print(f"Error showing help: {e}")

    def _show_tip(self):
        """Show tip dialog"""
        try:
            if self.show_tips:
                tip_dialog = TipDialog(self)
        except Exception as e:
            print(f"Error showing tip: {e}")

    def _toggle_monitor(self):
        """Toggle monitoring on/off"""
        try:
            if self.automator.is_monitoring:
                self.automator.stop_monitoring()
                self.btn_toggle_monitor.configure(text=_("Start Monitor"))
            else:
                self.automator.start_monitoring()
                self.btn_toggle_monitor.configure(text=_("Stop Monitor"))
        except Exception as e:
            print(f"Error toggling monitor: {e}")

    def _open_settings_dialog(self):
        """Open settings dialog"""
        try:
            print("Settings dialog not yet implemented")
        except Exception as e:
            print(f"Error opening settings: {e}")

    def refresh_rules(self):
        """Refresh the rules list"""
        try:
            print("Refreshing rules list")

            # Clear existing items
            for item in self.rules_tree.get_children():
                self.rules_tree.delete(item)

            # Load rules from rule manager
            rules = self.automator.rule_manager.list_rules()

            # Populate treeview
            for rule in rules:
                enabled_text = _("Yes") if rule.enabled else _("No")
                self.rules_tree.insert(
                    "", "end", iid=rule.id, values=(rule.name, enabled_text, rule.description)
                )

            print(f"Loaded {len(rules)} rules")

        except Exception as e:
            print(f"Error refreshing rules: {e}")
            # Show error in GUI if possible
            try:
                import tkinter.messagebox as messagebox

                messagebox.showerror(_("Error"), f"Failed to refresh rules: {e}")
            except:
                pass

    def _on_close(self):
        """Handle window close event"""
        try:
            if self.automator.is_monitoring:
                self.automator.stop_monitoring()
            save_config("settings.json", self.cfg)
            self.destroy()
        except Exception as e:
            print(f"Error closing application: {e}")
            self.destroy()
