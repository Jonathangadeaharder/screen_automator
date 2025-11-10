"""Rule editor dialog for creating and editing automation rules."""

import copy
import os
import uuid
from typing import TYPE_CHECKING, Any, Optional, Union

import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, EW, LEFT, NSEW, NW, PRIMARY, RIGHT, W, X
from ttkbootstrap.tooltip import ToolTip

# Monitor info utilities
try:
    from screeninfo import get_monitors
except ImportError:  # graceful fallback – assumes single monitor
    get_monitors = None

from core.localization import _
from src.action_executor import Action

from .record_hud import RecordHUD

if TYPE_CHECKING:
    from gui_components.protocols import WindowProtocol


class RuleEditor(tb.Toplevel):
    """Modal dialog for creating or editing a rule."""

    def __init__(self, master: "WindowProtocol", rule=None):
        super().__init__(master)
        self.title(_("Edit Rule") if rule else _("New Rule"))
        self.geometry("500x600")
        self.resizable(True, True)

        self.rule = rule
        self.automator = master.automator

        # Undo/redo stacks
        self.undo_stack: list[Any] = []
        self.redo_stack: list[Any] = []

        # Create main content
        frame = tb.Frame(self)
        frame.pack(fill=BOTH, expand=True, padx=20, pady=20)

        # Name field
        tb.Label(frame, text=_("Name")).grid(row=0, column=0, sticky=W)
        self.name_var = tb.StringVar(value=rule.name if rule else "")
        name_entry = tb.Entry(frame, textvariable=self.name_var)
        name_entry.grid(row=0, column=1, sticky=EW, padx=(5, 0))
        ToolTip(name_entry, text=_("Enter a descriptive name for this rule"))

        # Monitor selector
        tb.Label(frame, text=_("Monitor")).grid(row=1, column=0, sticky=W)
        mon_count = len(get_monitors()) if get_monitors is not None else 1
        self._mon_options = ["Any"] + [str(i + 1) for i in range(mon_count)]
        self.var_monitor = tb.StringVar()
        init_idx = getattr(rule, "monitor_idx", -1)
        self.var_monitor.set("Any" if init_idx == -1 else str(init_idx + 1))
        self.cmb_monitor = tb.Combobox(
            frame, values=self._mon_options, state="readonly", textvariable=self.var_monitor
        )
        self.cmb_monitor.grid(row=1, column=1, sticky=EW, padx=(5, 0))
        ToolTip(self.cmb_monitor, text=_("Select which monitor to watch (or 'Any' for all monitors)"))

        # Auto-disable options
        disable_frame = tb.Labelframe(frame, text=_("Auto-Disable Options"), padding=10)
        disable_frame.grid(row=2, column=0, columnspan=2, sticky=NSEW, pady=10)

        # Disable after X executions
        tb.Label(disable_frame, text=_("Disable after executions:")).grid(row=0, column=0, sticky=W)
        self.disable_after_var = tb.IntVar(value=getattr(rule, "disable_after_executions", 0))
        disable_after_spin = tb.Spinbox(
            disable_frame, from_=0, to=100, textvariable=self.disable_after_var, width=5
        )
        disable_after_spin.grid(row=0, column=1, sticky=W, padx=(5, 0))
        ToolTip(disable_after_spin, text=_("Set to 0 to never disable based on execution count"))

        # Disable on image
        tb.Label(disable_frame, text=_("Disable on image:")).grid(row=1, column=0, sticky=W)
        self.disable_image_var = tb.StringVar(value=getattr(rule, "disable_on_image", ""))
        disable_image_entry = tb.Entry(disable_frame, textvariable=self.disable_image_var)
        disable_image_entry.grid(row=1, column=1, sticky=EW, padx=(5, 0))
        tb.Button(disable_frame, text=_("Browse..."), command=self._browse_disable_image).grid(
            row=1, column=2, padx=5
        )
        ToolTip(
            disable_image_entry, text=_("When this image is detected, the rule will be disabled")
        )

        # Configure grid
        frame.grid_columnconfigure(1, weight=1)

        # Trigger image preview
        img_frame = tb.Labelframe(frame, text=_("Trigger Image"), padding=10)
        img_frame.grid(row=3, column=0, columnspan=2, sticky=NSEW, pady=10)

        self.image_canvas = tb.Canvas(img_frame, width=300, height=200, background="black")
        self.image_canvas.pack(fill=BOTH, expand=True)

        self.img_ref = None  # Keep reference to prevent GC
        if rule and rule.image_path and os.path.exists(rule.image_path):
            try:
                from PIL import Image, ImageTk

                img = Image.open(rule.image_path)

                # Scale down if needed
                max_width, max_height = 400, 300
                if img.width > max_width or img.height > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                self.img_ref = ImageTk.PhotoImage(img)
                self.image_canvas.create_image(0, 0, anchor=NW, image=self.img_ref)
                self.image_canvas.configure(width=img.width, height=img.height)
            except Exception as e:
                print(f"Error loading image: {e}")

        # Actions
        actions_frame = tb.Labelframe(frame, text=_("Actions"), padding=10)
        actions_frame.grid(row=4, column=0, columnspan=2, sticky=NSEW, pady=10)
        frame.grid_rowconfigure(4, weight=1)

        # Action toolbar
        action_toolbar = tb.Frame(actions_frame)
        action_toolbar.pack(fill=X, pady=(0, 10))

        # Left side - Add actions
        btn_record = tb.Button(action_toolbar, text=f"+ {_('Record')}", command=self._record_actions)
        btn_record.pack(side=LEFT, padx=2)
        ToolTip(btn_record, text=_("Record actions by clicking on screen"))

        btn_key = tb.Button(action_toolbar, text=f"⌨ {_('Key Press')}")
        btn_key.pack(side=LEFT, padx=2)
        ToolTip(btn_key, text=_("Add a keyboard key press action"))

        btn_type = tb.Button(action_toolbar, text=f"📝 {_('Type Text')}", command=self._add_text)
        btn_type.pack(side=LEFT, padx=2)
        ToolTip(btn_type, text=_("Add a text typing action"))

        # Right side - Edit actions
        btn_delete = tb.Button(action_toolbar, text=f"🗑 {_('Delete')}", command=self._delete_selected)
        btn_delete.pack(side=RIGHT, padx=2)
        ToolTip(btn_delete, text=_("Delete selected action (Delete key)"))

        btn_redo = tb.Button(action_toolbar, text=f"↪️ {_('Redo')}", command=self._redo)
        btn_redo.pack(side=RIGHT, padx=2)
        ToolTip(btn_redo, text=_("Redo last undone change (Ctrl+Y)"))

        btn_undo = tb.Button(action_toolbar, text=f"↩️ {_('Undo')}", command=self._undo)
        btn_undo.pack(side=RIGHT, padx=2)
        ToolTip(btn_undo, text=_("Undo last change (Ctrl+Z)"))

        # Action list
        self.action_list = tb.Treeview(
            actions_frame,
            columns=("type", "params"),
            show="headings",
            selectmode="browse",
        )
        self.action_list.heading("type", text=_("Action"))
        self.action_list.heading("params", text=_("Parameters"))
        self.action_list.column("type", width=100)
        self.action_list.column("params", width=300)
        self.action_list.pack(fill=BOTH, expand=True)

        # Make actionlist reorderable with drag-drop
        self.action_list.bind("<Button-1>", self._on_action_click)
        self.action_list.bind("<B1-Motion>", self._on_action_drag)
        self.action_list.bind("<ButtonRelease-1>", self._on_action_drop)
        self._drag_data: dict[str, Union[str, int, None]] = {"item": None, "index": -1}

        # Add keyboard navigation for accessibility
        self.action_list.bind("<Control-Up>", self._move_action_up)
        self.action_list.bind("<Control-Down>", self._move_action_down)
        self.action_list.bind("<Control-Key-Up>", self._move_action_up)  # Alternative binding
        self.action_list.bind("<Control-Key-Down>", self._move_action_down)  # Alternative binding

        # Status label for screen reader feedback
        self.status_label = tb.Label(actions_frame, text="", font=("Segoe UI", 9))
        self.status_label.pack(fill=X, pady=(5, 0))

        # Populate actions
        if rule and rule.actions:
            for act in rule.actions:
                self._add_action_to_list(act)

        # Bottom buttons
        btn_frame = tb.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, sticky=EW, pady=(10, 0))

        tb.Button(btn_frame, text=_("Cancel"), command=self.destroy).pack(side=LEFT)
        tb.Button(btn_frame, text=_("Save"), bootstyle=PRIMARY, command=self._save).pack(side=RIGHT)

        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Modal
        self.transient(master)
        self.grab_set()

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for the rule editor."""
        # Save shortcut
        self.bind_all("<Control-s>", lambda e: self._save())
        self.bind_all("<Control-S>", lambda e: self._save())

        # Undo/Redo shortcuts
        self.bind_all("<Control-z>", lambda e: self._undo())
        self.bind_all("<Control-Z>", lambda e: self._undo())
        self.bind_all("<Control-y>", lambda e: self._redo())
        self.bind_all("<Control-Y>", lambda e: self._redo())

        # Delete shortcut for actions
        self.bind_all("<Delete>", lambda e: self._delete_selected() if self.action_list.focus() else None)

        # Escape to cancel
        self.bind_all("<Escape>", lambda e: self.destroy())

    def _save(self):
        """Save the rule and close the dialog."""
        name = self.name_var.get().strip()
        if not name:
            return

        # Convert actions tree to list
        actions = []
        for item_id in self.action_list.get_children():
            act_id = self.action_list.item(item_id, "tags")[0]
            actions.append(self._action_cache[act_id])

        sel = self.var_monitor.get()
        mon_idx = -1 if sel == "Any" else int(sel) - 1

        # Get disable trigger options
        disable_after = self.disable_after_var.get()
        disable_image = self.disable_image_var.get()

        if self.rule:
            self.automator.rule_manager.update_rule(
                self.rule.id,
                name=name,
                actions=actions,
                monitor_idx=mon_idx,
                disable_after_executions=disable_after,
                disable_on_image=disable_image,
            )
        else:
            new_rule = self.automator.rule_manager.create_rule(
                name=name, image_path="", actions=actions
            )
            self.automator.rule_manager.update_rule(
                new_rule.id,
                monitor_idx=mon_idx,
                disable_after_executions=disable_after,
                disable_on_image=disable_image,
            )

        self.destroy()

    def _action_to_text(self, action: Action) -> tuple[str, str]:
        """Convert an action to displayable text for the treeview."""
        type_str = _(action.type.value.replace("_", " ").title())

        if action.type.value == "click":
            params_str = f"x={action.params['x']}, y={action.params['y']}"
        elif action.type.value == "move":
            params_str = f"x={action.params['x']}, y={action.params['y']}"
        elif action.type.value == "key_press":
            key = action.params["key"]
            params_str = key
        elif action.type.value == "type_text":
            params_str = action.params["text"]
        else:
            params_str = str(action.params)

        return type_str, params_str

    # Action list management
    _action_cache: dict[str, Action] = {}  # Cache actions by UUID

    def _add_action_to_list(self, action: Action) -> None:
        """Add an action to the displayed list."""
        action_id = str(uuid.uuid4())
        self._action_cache[action_id] = copy.deepcopy(action)

        type_str, params_str = self._action_to_text(action)
        self.action_list.insert("", "end", values=(type_str, params_str), tags=(action_id,))

        # Save state for undo
        self._push_undo_state()

    def _push_undo_state(self) -> None:
        """Save current state to undo stack."""
        state = []
        for item_id in self.action_list.get_children():
            act_id = self.action_list.item(item_id, "tags")[0]
            state.append(copy.deepcopy(self._action_cache[act_id]))
        self.undo_stack.append(state)
        self.redo_stack.clear()  # Clear redo stack on new change

    def _restore_state(self, state: list[Action]) -> None:
        """Restore action list to a saved state."""
        # Clear list
        for item in self.action_list.get_children():
            self.action_list.delete(item)

        # Add actions from state
        for action in state:
            self._add_action_to_list(action)

    def _undo(self) -> None:
        """Undo the last action."""
        if len(self.undo_stack) <= 1:  # Keep at least one state
            return

        # Move current state to redo
        current = self.undo_stack.pop()
        self.redo_stack.append(current)

        # Restore previous state
        if self.undo_stack:
            self._restore_state(self.undo_stack[-1])

    def _redo(self) -> None:
        """Redo an undone action."""
        if not self.redo_stack:
            return

        # Get state from redo and move to undo
        state = self.redo_stack.pop()
        self.undo_stack.append(state)

        # Restore the state
        self._restore_state(state)

    def _delete_selected(self) -> None:
        """Delete the selected action."""
        selected = self.action_list.selection()
        if not selected:
            return

        # Save state for undo
        self._push_undo_state()

        # Delete item
        self.action_list.delete(*selected)

    def _record_actions(self) -> None:
        """Open recording HUD to capture actions."""
        hud = RecordHUD(self)
        self.wait_window(hud)

        if hud.events:
            # Save state for undo
            self._push_undo_state()

            # Add recorded actions
            for act in hud.events:
                self._add_action_to_list(act)

    def _add_text(self) -> None:
        """Add a type_text action."""
        from tkinter.simpledialog import askstring

        text = askstring(_("Type Text"), _("Enter text to type:"))
        if text:
            from src.action_executor import create_type_text_action

            act = create_type_text_action(text)
            self._add_action_to_list(act)

    def _browse_disable_image(self) -> None:
        """Browse for an image to use as disable trigger."""
        from tkinter import filedialog

        filetypes = [(_("Image files"), "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), (_("All files"), "*.*")]

        filepath = filedialog.askopenfilename(
            title=_("Select Disable Trigger Image"), filetypes=filetypes
        )

        if filepath:
            self.disable_image_var.set(filepath)

    # Drag and drop reordering
    def _on_action_click(self, event) -> None:
        """Record initial position for drag start."""
        item = self.action_list.identify_row(event.y)
        if not item:
            return

        self._drag_data["item"] = item
        children = self.action_list.get_children()
        self._drag_data["index"] = children.index(item)

    def _on_action_drag(self, event) -> None:
        """Visual feedback during drag."""
        pass  # Could add visual indicator here

    def _on_action_drop(self, event) -> None:
        """Handle drop to reorder items."""
        if not self._drag_data["item"]:
            return

        # Get drop position
        target = self.action_list.identify_row(event.y)
        if not target or target == self._drag_data["item"]:
            return

        # Get positions
        src_idx = self._drag_data["index"]
        children = self.action_list.get_children()
        try:
            dst_idx = children.index(target)
        except ValueError:
            return

        # Move item
        item = self._drag_data["item"]

        # Save state for undo
        self._push_undo_state()

        # Perform move
        if dst_idx < src_idx:  # Moving up
            self.action_list.move(item, "", dst_idx)
        else:  # Moving down
            self.action_list.move(item, "", dst_idx + 1)

        # Clear drag data
        self._drag_data = {"item": None, "index": -1}

    def _move_action_up(self, event=None) -> str:
        """
        Move selected action up one position (keyboard accessibility).

        Returns:
            "break" to prevent default handling
        """
        selection = self.action_list.selection()
        if not selection:
            self.status_label.configure(text=_("No action selected"))
            return "break"

        item = selection[0]
        children = self.action_list.get_children()
        idx = children.index(item)

        if idx == 0:
            self.status_label.configure(text=_("Action already at the top"))
            return "break"

        # Save state for undo
        self._push_undo_state()

        # Move item up
        self.action_list.move(item, "", idx - 1)

        # Keep selection
        self.action_list.selection_set(item)
        self.action_list.focus(item)
        self.action_list.see(item)

        # Announce to screen reader
        self.status_label.configure(
            text=_("Moved action up to position {}").format(idx)
        )

        return "break"  # Prevent default key handling

    def _move_action_down(self, event=None) -> str:
        """
        Move selected action down one position (keyboard accessibility).

        Returns:
            "break" to prevent default handling
        """
        selection = self.action_list.selection()
        if not selection:
            self.status_label.configure(text=_("No action selected"))
            return "break"

        item = selection[0]
        children = self.action_list.get_children()
        idx = children.index(item)

        if idx == len(children) - 1:
            self.status_label.configure(text=_("Action already at the bottom"))
            return "break"

        # Save state for undo
        self._push_undo_state()

        # Move item down
        self.action_list.move(item, "", idx + 1)

        # Keep selection
        self.action_list.selection_set(item)
        self.action_list.focus(item)
        self.action_list.see(item)

        # Announce to screen reader
        self.status_label.configure(
            text=_("Moved action down to position {}").format(idx + 2)
        )

        return "break"  # Prevent default key handling
