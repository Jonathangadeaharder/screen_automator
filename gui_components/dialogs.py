"""Common dialog components for the Screen Automator GUI."""
import os
import time
import random
from typing import List, Optional, Dict, Any, Tuple, Callable

import ttkbootstrap as tb
from ttkbootstrap.constants import *

try:
    import psutil
except ImportError:
    psutil = None

try:
    from win10toast import ToastNotifier
except ImportError:
    ToastNotifier = None

from core.localization import _


class TipDialog(tb.Toplevel):
    """Simple modal showing a random tip with Next button."""
    
    def __init__(self, master: 'MainWindow', tip: str):
        super().__init__(master)
        self.title(_('Tip of the Day'))
        self.resizable(False, False)
        
        frame = tb.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)
        
        tb.Label(frame, text='💡', font=('Segoe UI', 24)).pack(pady=(0, 10))
        tb.Label(frame, text=tip, wraplength=300, justify=CENTER).pack(pady=10)
        
        chk_var = tb.BooleanVar(value=master.show_tips)
        chk = tb.Checkbutton(
            frame, 
            text=_('Show tips on startup'), 
            variable=chk_var,
            command=lambda: setattr(master, 'show_tips', chk_var.get())
        )
        chk.pack(pady=10)
        
        tb.Button(frame, text=_('Close'), command=self.destroy).pack(pady=10)
        
        # Position
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Modal
        self.transient(master)
        self.grab_set()
        self.focus_set()


class ConflictsDialog(tb.Toplevel):
    """Dialog showing conflicts between rules."""
    
    def __init__(self, master: 'MainWindow', conflicts):
        super().__init__(master)
        self.title(_('Rule Conflicts'))
        self.geometry('500x300')
        self.resizable(True, True)
        
        frame = tb.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)
        
        tb.Label(
            frame, 
            text=_('The following rules have matching triggers but different actions:'),
            wraplength=460
        ).pack(anchor='w', pady=(0, 10))
        
        # Conflicts list
        self.conflicts_list = tb.Treeview(
            frame, 
            columns=('rule1', 'rule2'), 
            show='headings',
            height=8
        )
        self.conflicts_list.heading('rule1', text=_('Rule 1'))
        self.conflicts_list.heading('rule2', text=_('Rule 2'))
        self.conflicts_list.column('rule1', width=220)
        self.conflicts_list.column('rule2', width=220)
        self.conflicts_list.pack(fill=BOTH, expand=True, pady=10)
        
        # Add conflicts
        for c in conflicts:
            r1 = c['rule1'].name
            r2 = c['rule2'].name
            self.conflicts_list.insert('', 'end', values=(r1, r2))
        
        info = tb.Label(
            frame, 
            text=_('Conflicts occur when multiple rules use the same trigger image. Only the highest priority rule will run.'),
            wraplength=460,
            foreground='gray'
        )
        info.pack(pady=10)
        
        tb.Button(frame, text=_('Close'), command=self.destroy).pack()
        
        # Modal
        self.transient(master)
        self.grab_set()


class FirstRuleWizard(tb.Toplevel):
    """3-step overlay wizard guiding user through first rule creation."""
    
    def __init__(self, master: 'MainWindow'):
        super().__init__(master)
        self.title(_('Create Your First Rule'))
        self.geometry('600x400')
        self.resizable(False, False)
        
        # Store main window
        self.main_window = master
        
        frame = tb.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)
        
        # Header
        header = tb.Label(
            frame, 
            text=_('Welcome to Screen Automator!'),
            font=('Segoe UI', 18, 'bold')
        )
        header.pack(pady=(0, 20))
        
        # Steps
        self.steps = [
            _('Step 1: Click "Capture Screen" to select a region of the screen that will trigger your automation.'),
            _('Step 2: Add actions that will run when the trigger is detected (clicks, key presses, text entry).'),
            _('Step 3: Give your rule a name, save it, and enable monitoring to start automation.')
        ]
        
        self.idx = 0
        
        # Image
        self.img_label = tb.Label(frame)
        self.img_label.pack(pady=10)
        
        # Step text
        self.lbl = tb.Label(
            frame, 
            text=self.steps[0],
            font=('Segoe UI', 12),
            wraplength=560,
            justify=CENTER
        )
        self.lbl.pack(pady=20)
        
        # Bottom buttons
        btn_frame = tb.Frame(frame)
        btn_frame.pack(fill=X, pady=20)
        
        self.btn_prev = tb.Button(
            btn_frame, 
            text=_('Previous'),
            state=DISABLED,
            command=self._prev_step
        )
        self.btn_prev.pack(side=LEFT)
        
        self.btn_next = tb.Button(
            btn_frame, 
            text=_('Next'),
            bootstyle=PRIMARY,
            command=self._next_step
        )
        self.btn_next.pack(side=RIGHT)
        
        tb.Button(
            btn_frame,
            text=_('Skip Tutorial'),
            command=self.destroy
        ).pack(side=RIGHT, padx=10)
        
        # Center on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
    def _next_step(self):
        """Go to next step."""
        if self.idx < len(self.steps) - 1:
            self.idx += 1
            self.lbl.configure(text=self.steps[self.idx])
            self.btn_prev.configure(state=NORMAL)
            if self.idx == len(self.steps) - 1:
                self.btn_next.configure(text=_('Finish'))
        else:
            self.destroy()
    
    def _prev_step(self):
        """Go to previous step."""
        if self.idx > 0:
            self.idx -= 1
            self.lbl.configure(text=self.steps[self.idx])
            if self.idx == 0:
                self.btn_prev.configure(state=DISABLED)
            self.btn_next.configure(text=_('Next'))


class PerformanceOverlay(tb.Toplevel):
    """Floating transparent window showing FPS and memory diagnostics."""

    def __init__(self, master: 'MainWindow'):
        super().__init__(master)
        self.master_window = master
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        # Semi-transparent black background if supported
        try:
            self.attributes('-alpha', 0.7)
        except Exception:
            pass

        self.configure(bg='black')

        self.lbl_stats = tb.Label(
            self,
            text='--',
            foreground='lime',
            background='black',
            font=('Consolas', 12, 'bold')
        )
        self.lbl_stats.pack(padx=10, pady=6)

        # Position top-left with slight margin
        self.geometry(f'+20+20')

        # periodic refresh
        self._refresh()

        # Close on click
        self.bind('<Button-1>', lambda *_: self.destroy())

    def _refresh(self):
        """Update performance statistics."""
        if not self.winfo_exists():
            return
        fps = getattr(self.master_window, '_last_fps', 0)
        mem = getattr(self.master_window, '_last_mem_mb', 0)
        self.lbl_stats.configure(text=f'FPS: {fps}\nMem: {mem} MB')
        self.after(500, self._refresh)
