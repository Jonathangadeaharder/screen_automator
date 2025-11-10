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
        ToolTip(
            self.cmb_monitor, text=_("Select which monitor to watch (or 'Any' for all monitors)")
        )

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
        btn_record = tb.Button(
            action_toolbar, text=f"+ {_('Record')}", command=self._record_actions
        )
        btn_record.pack(side=LEFT, padx=2)
        ToolTip(btn_record, text=_("Record actions by clicking on screen"))

        btn_key = tb.Button(action_toolbar, text=f"⌨ {_('Key Press')}")
        btn_key.pack(side=LEFT, padx=2)
        ToolTip(btn_key, text=_("Add a keyboard key press action"))

        btn_type = tb.Button(action_toolbar, text=f"📝 {_('Type Text')}", command=self._add_text)
        btn_type.pack(side=LEFT, padx=2)
        ToolTip(btn_type, text=_("Add a text typing action"))

        # Right side - Edit actions
        btn_delete = tb.Button(
            action_toolbar, text=f"🗑 {_('Delete')}", command=self._delete_selected
        )
        btn_delete.pack(side=RIGHT, padx=2)
        ToolTip(btn_delete, text=_("Delete selected action (Delete key)"))

        btn_redo = tb.Button(action_toolbar, text=f"↪️ {_('Redo')}", command=self._redo)
        btn_redo.pack(side=RIGHT, padx=2)
        ToolTip(btn_redo, text=_("Redo last undone change (Ctrl+Y)"))

        btn_undo = tb.Button(action_toolbar, text=f"↩️ {_('Undo')}", command=self._undo)
        btn_undo.pack(side=RIGHT, padx=2)
        ToolTip(btn_undo, text=_("Undo last change (Ctrl+Z)"))

        # Action list - Card-based layout with visual flow
        # Create scrollable container
        self.action_canvas = tb.Canvas(actions_frame, highlightthickness=0)
        action_scrollbar = tb.Scrollbar(
            actions_frame, orient="vertical", command=self.action_canvas.yview
        )
        self.action_list_frame = tb.Frame(self.action_canvas)

        # Configure scrolling
        self.action_list_frame.bind(
            "<Configure>",
            lambda e: self.action_canvas.configure(scrollregion=self.action_canvas.bbox("all")),
        )

        self.action_canvas_window = self.action_canvas.create_window(
            (0, 0), window=self.action_list_frame, anchor="nw"
        )
        self.action_canvas.configure(yscrollcommand=action_scrollbar.set)

        # Pack canvas and scrollbar
        self.action_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        action_scrollbar.pack(side=RIGHT, fill="y")

        # Resize canvas window to match canvas width
        self.action_canvas.bind("<Configure>", self._on_canvas_configure)

        # Track action cards and selection
        self.action_cards: dict[str, tb.Frame] = {}  # action_id -> card frame
        self.selected_action_id: Optional[str] = None

        # Drag-drop state
        self._drag_data: dict[str, Union[str, int, None]] = {"item": None, "index": -1}

        # Add keyboard navigation for accessibility
        self.action_canvas.bind("<Control-Up>", self._move_action_up)
        self.action_canvas.bind("<Control-Down>", self._move_action_down)
        self.action_canvas.bind("<Control-Key-Up>", self._move_action_up)  # Alternative binding
        self.action_canvas.bind("<Control-Key-Down>", self._move_action_down)  # Alternative binding

        # Make canvas focusable for keyboard events
        self.action_canvas.focus_set()

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
        self.bind_all(
            "<Delete>", lambda e: self._delete_selected() if self.action_list.focus() else None
        )

        # Escape to cancel
        self.bind_all("<Escape>", lambda e: self.destroy())

    def _save(self):
        """Save the rule and close the dialog."""
        name = self.name_var.get().strip()
        if not name:
            return

        # Convert action cards to list
        actions = []
        for action_id in self.action_cards.keys():
            actions.append(self._action_cache[action_id])

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

    def _on_canvas_configure(self, event=None) -> None:
        """Update canvas window width when canvas is resized."""
        canvas_width = event.width if event else self.action_canvas.winfo_width()
        self.action_canvas.itemconfig(self.action_canvas_window, width=canvas_width)

    def _get_action_icon(self, action: Action) -> str:
        """Get emoji icon for action type."""
        icon_map = {
            "click": "🖱️",
            "move": "↔️",
            "key_press": "⌨️",
            "type_text": "📝",
            "wait": "⏱️",
            "scroll": "📜",
            "drag": "👆",
        }
        return icon_map.get(action.type.value, "⚙️")

    def _action_to_text(self, action: Action) -> tuple[str, str]:
        """Convert an action to displayable text for the card view."""
        type_str = _(action.type.value.replace("_", " ").title())

        if action.type.value == "click":
            params_str = f"x={action.params['x']}, y={action.params['y']}"
        elif action.type.value == "move":
            params_str = f"x={action.params['x']}, y={action.params['y']}"
        elif action.type.value == "key_press":
            key = action.params["key"]
            params_str = key
        elif action.type.value == "type_text":
            text = action.params["text"]
            # Truncate long text
            params_str = text if len(text) <= 50 else text[:47] + "..."
        else:
            params_str = str(action.params)

        return type_str, params_str

    # Action list management
    _action_cache: dict[str, Action] = {}  # Cache actions by UUID

    def _add_action_to_list(self, action: Action) -> None:
        """Add an action to the displayed card list."""
        action_id = str(uuid.uuid4())
        self._action_cache[action_id] = copy.deepcopy(action)

        # Create action card
        self._create_action_card(action_id, action)

        # Save state for undo
        self._push_undo_state()

    def _create_action_card(self, action_id: str, action: Action) -> None:
        """Create a visual card for an action."""
        # Get action text
        type_str, params_str = self._action_to_text(action)
        icon = self._get_action_icon(action)

        # Add arrow before this card if there are existing cards
        existing_cards = list(self.action_cards.keys())
        if existing_cards:
            arrow_frame = tb.Frame(self.action_list_frame, height=30)
            arrow_frame.pack(fill=X, pady=0)

            arrow_label = tb.Label(
                arrow_frame, text="↓", font=("Segoe UI", 20), foreground="#6c757d"
            )
            arrow_label.pack()

        # Create card frame
        card = tb.Frame(self.action_list_frame, padding=10, relief="raised", borderwidth=1)
        card.pack(fill=X, pady=5, padx=5)

        # Store reference
        self.action_cards[action_id] = card

        # Header with icon and type
        header = tb.Frame(card)
        header.pack(fill=X, pady=(0, 5))

        icon_label = tb.Label(header, text=icon, font=("Segoe UI", 16))
        icon_label.pack(side=LEFT, padx=(0, 10))

        type_label = tb.Label(header, text=type_str, font=("Segoe UI", 11, "bold"))
        type_label.pack(side=LEFT)

        # Position indicator (e.g., "Step 1")
        position = len(self.action_cards)
        position_label = tb.Label(
            header, text=f"Step {position}", font=("Segoe UI", 9), foreground="#6c757d"
        )
        position_label.pack(side=RIGHT)

        # Parameters
        params_label = tb.Label(
            card,
            text=params_str,
            font=("Segoe UI", 10),
            foreground="#495057",
            wraplength=400,
            justify=LEFT,
        )
        params_label.pack(fill=X)

        # Make card clickable for selection
        for widget in [card, icon_label, type_label, position_label, params_label]:
            widget.bind("<Button-1>", lambda e, aid=action_id: self._select_action_card(aid))
            widget.bind("<Enter>", lambda e, c=card: self._on_card_hover(c, True))
            widget.bind("<Leave>", lambda e, c=card: self._on_card_hover(c, False))

        # Drag-drop bindings
        card.bind("<Button-1>", lambda e, aid=action_id: self._on_card_click(e, aid))
        card.bind("<B1-Motion>", lambda e, aid=action_id: self._on_card_drag(e, aid))
        card.bind("<ButtonRelease-1>", lambda e: self._on_card_drop(e))

    def _select_action_card(self, action_id: str) -> None:
        """Select an action card."""
        # Deselect previous
        if self.selected_action_id and self.selected_action_id in self.action_cards:
            old_card = self.action_cards[self.selected_action_id]
            old_card.configure(relief="raised", borderwidth=1)

        # Select new
        self.selected_action_id = action_id
        card = self.action_cards[action_id]
        card.configure(relief="solid", borderwidth=2)

        # Focus canvas for keyboard events
        self.action_canvas.focus_set()

    def _on_card_hover(self, card: tb.Frame, entering: bool) -> None:
        """Handle hover effect on action card."""
        if entering:
            # Check if this card is selected
            is_selected = any(
                card == self.action_cards[aid]
                for aid in [self.selected_action_id]
                if self.selected_action_id
            )
            if not is_selected:
                card.configure(relief="raised", borderwidth=2)
        else:
            # Check if this card is selected
            is_selected = any(
                card == self.action_cards[aid]
                for aid in [self.selected_action_id]
                if self.selected_action_id
            )
            if not is_selected:
                card.configure(relief="raised", borderwidth=1)

    def _push_undo_state(self) -> None:
        """Save current state to undo stack."""
        state = []
        for action_id in self.action_cards.keys():
            state.append(copy.deepcopy(self._action_cache[action_id]))
        self.undo_stack.append(state)
        self.redo_stack.clear()  # Clear redo stack on new change

    def _restore_state(self, state: list[Action]) -> None:
        """Restore action list to a saved state."""
        # Clear all cards
        for widget in self.action_list_frame.winfo_children():
            widget.destroy()

        self.action_cards.clear()
        self._action_cache.clear()
        self.selected_action_id = None

        # Add actions from state
        for action in state:
            action_id = str(uuid.uuid4())
            self._action_cache[action_id] = copy.deepcopy(action)
            self._create_action_card(action_id, action)

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
        """Delete the selected action card."""
        if not self.selected_action_id:
            self.status_label.configure(text=_("No action selected"))
            return

        # Save state for undo
        self._push_undo_state()

        # Remove from cache and cards
        if self.selected_action_id in self._action_cache:
            del self._action_cache[self.selected_action_id]

        # Rebuild the card list
        self._rebuild_card_list()

        self.selected_action_id = None

    def _rebuild_card_list(self) -> None:
        """Rebuild the entire card list from cache."""
        # Clear all widgets
        for widget in self.action_list_frame.winfo_children():
            widget.destroy()

        # Get current order from action_cards
        ordered_ids = list(self.action_cards.keys())

        # Clear cards dict
        self.action_cards.clear()

        # Recreate cards
        for action_id in ordered_ids:
            if action_id in self._action_cache:
                self._create_action_card(action_id, self._action_cache[action_id])

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
    def _on_card_click(self, event, action_id: str) -> None:
        """Record initial position for drag start."""
        self._select_action_card(action_id)
        self._drag_data["item"] = action_id
        ordered_ids = list(self.action_cards.keys())
        self._drag_data["index"] = ordered_ids.index(action_id)

    def _on_card_drag(self, event, action_id: str) -> None:
        """Visual feedback during drag."""
        pass  # Could add visual indicator here

    def _on_card_drop(self, event) -> None:
        """Handle drop to reorder cards."""
        if not self._drag_data["item"]:
            return

        # Find which card we're hovering over
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
        if not widget:
            return

        # Find the card this widget belongs to
        target_id = None
        for action_id, card in self.action_cards.items():
            if widget == card or widget.master == card or self._is_child_of(widget, card):
                target_id = action_id
                break

        if not target_id or target_id == self._drag_data["item"]:
            self._drag_data = {"item": None, "index": -1}
            return

        # Get positions
        src_id = self._drag_data["item"]
        if not isinstance(src_id, str):
            return

        ordered_ids = list(self.action_cards.keys())
        src_idx = ordered_ids.index(src_id)
        dst_idx = ordered_ids.index(target_id)

        # Save state for undo
        self._push_undo_state()

        # Reorder the action_cards dictionary
        ordered_ids.remove(src_id)
        if dst_idx < src_idx:  # Moving up
            ordered_ids.insert(dst_idx, src_id)
        else:  # Moving down
            ordered_ids.insert(dst_idx, src_id)

        # Rebuild cards in new order
        new_cards = {}
        for action_id in ordered_ids:
            new_cards[action_id] = self.action_cards[action_id]
        self.action_cards = new_cards

        self._rebuild_card_list()

        # Reselect the moved card
        self._select_action_card(src_id)

        # Clear drag data
        self._drag_data = {"item": None, "index": -1}

    def _is_child_of(self, widget, parent) -> bool:
        """Check if widget is a child of parent."""
        while widget:
            if widget == parent:
                return True
            widget = widget.master if hasattr(widget, "master") else None
        return False

    def _move_action_up(self, event=None) -> str:
        """
        Move selected action card up one position (keyboard accessibility).

        Returns:
            "break" to prevent default handling
        """
        if not self.selected_action_id:
            self.status_label.configure(text=_("No action selected"))
            return "break"

        ordered_ids = list(self.action_cards.keys())
        idx = ordered_ids.index(self.selected_action_id)

        if idx == 0:
            self.status_label.configure(text=_("Action already at the top"))
            return "break"

        # Save state for undo
        self._push_undo_state()

        # Swap positions
        ordered_ids[idx], ordered_ids[idx - 1] = ordered_ids[idx - 1], ordered_ids[idx]

        # Rebuild cards dict in new order
        new_cards = {}
        for action_id in ordered_ids:
            new_cards[action_id] = self.action_cards[action_id]
        self.action_cards = new_cards

        # Rebuild display
        self._rebuild_card_list()

        # Reselect
        self._select_action_card(self.selected_action_id)

        # Announce to screen reader
        self.status_label.configure(text=_("Moved action up to position {}").format(idx))

        return "break"  # Prevent default key handling

    def _move_action_down(self, event=None) -> str:
        """
        Move selected action card down one position (keyboard accessibility).

        Returns:
            "break" to prevent default handling
        """
        if not self.selected_action_id:
            self.status_label.configure(text=_("No action selected"))
            return "break"

        ordered_ids = list(self.action_cards.keys())
        idx = ordered_ids.index(self.selected_action_id)

        if idx == len(ordered_ids) - 1:
            self.status_label.configure(text=_("Action already at the bottom"))
            return "break"

        # Save state for undo
        self._push_undo_state()

        # Swap positions
        ordered_ids[idx], ordered_ids[idx + 1] = ordered_ids[idx + 1], ordered_ids[idx]

        # Rebuild cards dict in new order
        new_cards = {}
        for action_id in ordered_ids:
            new_cards[action_id] = self.action_cards[action_id]
        self.action_cards = new_cards

        # Rebuild display
        self._rebuild_card_list()

        # Reselect
        self._select_action_card(self.selected_action_id)

        # Announce to screen reader
        self.status_label.configure(text=_("Moved action down to position {}").format(idx + 2))

        return "break"  # Prevent default key handling
