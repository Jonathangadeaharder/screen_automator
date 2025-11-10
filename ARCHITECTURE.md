# Screen Automator - Architecture Documentation

## Table of Contents

- [Overview](#overview)
- [Design Philosophy](#design-philosophy)
- [System Architecture](#system-architecture)
- [Core Components](#core-components)
- [Framework Modules](#framework-modules)
- [GUI Architecture](#gui-architecture)
- [Data Flow](#data-flow)
- [Extension Points](#extension-points)
- [Design Patterns](#design-patterns)

---

## Overview

Screen Automator is a Python-based desktop automation tool that combines image recognition, rule-based automation, and a modern testing framework. The project is structured in three main layers:

1. **Core Engine**: Image detection, window management, action execution
2. **Framework Layer**: Modern API with auto-waiting, expectations, page objects
3. **User Interfaces**: CLI and GUI for rule management

**Key Design Goals:**
- Eliminate flaky automation with intelligent waiting
- Provide both low-level control and high-level abstraction
- Enable reliable, maintainable automation code
- Support multiple use cases (testing, RPA, monitoring)

**Target Audience:**
- QA Engineers building UI tests
- Automation Engineers creating RPA workflows
- Power Users automating repetitive tasks
- Developers integrating automation into applications

---

## Design Philosophy

### 1. **Auto-Waiting Over Time.sleep()**

Traditional automation code is brittle:
```python
# ❌ Flaky approach
time.sleep(5)  # Maybe enough? Maybe too long?
button = find_image("button.png")
click(button)
```

Screen Automator uses intelligent waiting:
```python
# ✅ Robust approach
framework.click_image("button.png", timeout=10000)
# Waits until found OR timeout, no guessing
```

### 2. **Layered Architecture**

The system provides multiple levels of abstraction:

```
High Level    → Modern API (create_framework, expect_image)
              ↓
Framework     → Expectations, Actionability, Page Objects
              ↓
Core          → ImageDetector, RuleManager, ActionExecutor
              ↓
Low Level     → cv2, pyautogui, pynput
```

Users can work at any level based on their needs.

### 3. **Separation of Concerns**

Each module has a single, well-defined responsibility:
- `ImageDetector` → Find images, nothing else
- `RuleManager` → Manage rules, not execute them
- `ActionExecutor` → Execute actions, not decide when
- `WindowManager` → Window operations only

### 4. **Type Safety**

The codebase uses Python type hints extensively:
- Catches errors at development time
- Provides IDE autocomplete
- Serves as inline documentation
- Enables refactoring with confidence

### 5. **Testability**

All components are designed for testing:
- Dependency injection for mocks
- Pure functions where possible
- Clear interfaces (Protocols)
- Comprehensive test suite (111 tests)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interfaces                         │
│  ┌────────────────┐              ┌─────────────────────┐   │
│  │   CLI (cli.py) │              │  GUI (gui_components)│   │
│  └────────┬───────┘              └──────────┬──────────┘   │
│           │                                  │              │
└───────────┼──────────────────────────────────┼──────────────┘
            │                                  │
┌───────────┼──────────────────────────────────┼──────────────┐
│           │      Modern API Layer            │              │
│           ↓                                  ↓              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │   ScreenAutomatorFramework (modern_api.py)            │ │
│  │   - Unified interface                                 │ │
│  │   - Factory methods                                   │ │
│  │   - Rule integration                                  │ │
│  └────┬──────────────┬──────────────┬────────────────────┘ │
└───────┼──────────────┼──────────────┼───────────────────────┘
        │              │              │
┌───────┼──────────────┼──────────────┼───────────────────────┐
│       │  Framework Modules          │                       │
│       ↓              ↓              ↓                       │
│  ┌─────────┐  ┌──────────┐  ┌──────────────┐             │
│  │ Expect- │  │ Action-  │  │ Page         │             │
│  │ ations  │  │ ability  │  │ Objects      │             │
│  └─────────┘  └──────────┘  └──────────────┘             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           DataDriven (CSV/JSON/XML)                 │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
        │              │              │
┌───────┼──────────────┼──────────────┼───────────────────────┐
│       │   Core Engine Components    │                       │
│       ↓              ↓              ↓                       │
│  ┌─────────┐  ┌──────────┐  ┌──────────────┐             │
│  │ Image   │  │ Rule     │  │ Action       │             │
│  │Detector │  │ Manager  │  │ Executor     │             │
│  └─────────┘  └──────────┘  └──────────────┘             │
│                                                             │
│  ┌─────────┐  ┌──────────┐  ┌──────────────┐             │
│  │ Window  │  │Screen    │  │ Context      │             │
│  │ Manager │  │Automator │  │ Automator    │             │
│  └─────────┘  └──────────┘  └──────────────┘             │
└──────────────────────────────────────────────────────────────┘
        │              │              │
┌───────┼──────────────┼──────────────┼───────────────────────┐
│       │   Low-Level Libraries       │                       │
│       ↓              ↓              ↓                       │
│  ┌─────────┐  ┌──────────┐  ┌──────────────┐             │
│  │  cv2    │  │pyautogui │  │   pynput     │             │
│  │ (OpenCV)│  │          │  │              │             │
│  └─────────┘  └──────────┘  └──────────────┘             │
└──────────────────────────────────────────────────────────────┘
```

### Module Organization

```
screen_automator/
├── src/                      # Core engine
│   ├── automator.py          # Main automation loop
│   ├── context_automator.py # Window-aware automation
│   ├── image_detector.py    # Image matching (OpenCV)
│   ├── action_executor.py   # Action execution
│   ├── rule_manager.py      # Rule CRUD operations
│   ├── window_manager.py    # Window operations
│   ├── screen_selector.py   # Screen region selection
│   ├── modern_api.py        # Unified framework API
│   ├── expectations.py      # Assertion framework
│   ├── actionability.py     # Auto-waiting utilities
│   ├── page_objects.py      # Page Object Model
│   └── data_driven.py       # Data source integration
│
├── gui_components/          # GUI modules
│   ├── main_window.py       # Main window (Tkinter)
│   ├── rule_editor.py       # Rule editor dialog
│   ├── dialogs.py           # Common dialogs
│   ├── widgets.py           # Custom widgets
│   ├── record_hud.py        # Recording overlay
│   └── protocols.py         # Type protocols
│
├── core/                    # Utilities
│   └── localization.py      # i18n support
│
├── utils/                   # Helper modules
│   └── config.py            # Configuration management
│
├── tests/                   # Test suite
│   ├── test_expectations.py # Framework tests
│   ├── test_actionability.py
│   ├── test_page_objects.py
│   └── ...
│
├── cli.py                   # Command-line interface
├── gui.py                   # GUI entry point
└── examples/                # Example usage
```

---

## Core Components

### 1. ImageDetector (`src/image_detector.py`)

**Purpose:** Find images on screen using template matching

**Key Methods:**
- `find_image(template_path)` → `(x, y, width, height)` or `None`
- `capture_screen()` → Screenshot as numpy array
- `save_screenshot(filename)` → Save screen capture

**Algorithm:**
1. Capture full screen or window region
2. Load template image
3. Use OpenCV `matchTemplate` with normalized correlation
4. Apply confidence threshold (default: 0.8)
5. Return coordinates if match found

**Example:**
```python
detector = ImageDetector()
location = detector.find_image("button.png")
if location:
    x, y, w, h = location
    center = (x + w//2, y + h//2)
```

**Design Notes:**
- Stateless: Each call is independent
- Thread-safe: No shared mutable state
- Configurable confidence threshold
- Supports multiple monitors

---

### 2. RuleManager (`src/rule_manager.py`)

**Purpose:** Manage automation rules (CRUD operations)

**Rule Structure:**
```python
@dataclass
class Rule:
    id: str                    # Unique identifier
    name: str                  # Display name
    enabled: bool              # Active flag
    triggers: list[Trigger]    # What activates the rule
    actions: list[Action]      # What to do
    priority: int              # Execution order
    cluster_group: str         # Grouping for efficiency
```

**Trigger Types:**
- `ImageTrigger`: Detect image on screen
- `IdleTrigger`: Screen unchanged for duration
- `WindowTrigger`: Specific window active
- `ProcessTrigger`: Process detected

**Action Types:**
- `ClickAction`: Mouse click at coordinates
- `KeyAction`: Keyboard input
- `WaitAction`: Delay execution
- `WindowAction`: Activate window
- `ProcessAction`: Launch process

**Key Methods:**
- `load_rule(rule_id)` → Load from disk
- `save_rule(rule)` → Persist to JSON
- `list_enabled_rules()` → Get active rules
- `get_rules_by_cluster()` → Group for efficient execution

**Design Notes:**
- Rules stored as JSON in `data/rules/`
- Clustering reduces redundant screen captures
- Priority system for conflict resolution

---

### 3. ActionExecutor (`src/action_executor.py`)

**Purpose:** Execute actions (clicks, keystrokes, waits)

**Key Methods:**
- `execute_action(action, context)` → Execute single action
- `execute_action_sequence(actions)` → Execute multiple actions

**Action Execution:**
```python
executor = ActionExecutor()

# Click action
action = Action(type="click", params={"x": 100, "y": 200})
executor.execute_action(action)

# Keyboard action
action = Action(type="key", params={"keys": "ctrl+c"})
executor.execute_action(action)
```

**Supported Actions:**
- `click`: Mouse click (left/right/middle)
- `double_click`: Double-click
- `key`: Keyboard input (supports modifiers)
- `wait`: Sleep for duration
- `window`: Activate window by title
- `process`: Launch application

**Safety Features:**
- Mouse idle detection (don't interfere with user)
- Execution can be interrupted
- Actions have configurable timeouts

---

### 4. WindowManager (`src/window_manager.py`)

**Purpose:** Cross-platform window operations

**Key Methods:**
- `get_running_windows()` → List all windows
- `get_active_window()` → Currently focused window
- `activate_window(window_info)` → Bring window to front
- `find_window_by_title(title)` → Search by title

**WindowInfo Structure:**
```python
@dataclass
class WindowInfo:
    handle: int           # OS window handle
    title: str           # Window title
    process_name: str    # Executable name
    x: int, y: int       # Position
    width: int, height: int  # Dimensions
```

**Platform Support:**
- Windows: Uses `win32gui`
- Linux: Uses `Xlib`
- macOS: Uses `Quartz` (limited)

**Design Notes:**
- Abstraction layer over OS-specific APIs
- Handles minimized windows
- Supports partial title matching

---

### 5. ScreenAutomator (`src/automator.py`)

**Purpose:** Main automation loop and monitoring

**Workflow:**
```
Start → Load Rules → Enter Loop
                        ↓
        ┌───────────────┴────────────────┐
        │                                │
        ↓                                │
  Check Mouse Idle?                     │
        ↓                                │
  Screen Changed?                       │
        ↓                                │
  Evaluate Triggers                     │
        ↓                                │
  Execute Matching Rules                │
        ↓                                │
  Wait (check_interval)                 │
        │                                │
        └────────────────────────────────┘
```

**Key Features:**
- Mouse idle detection: Don't execute while user is active
- Screen change detection: Hash-based screen comparison
- Configurable check interval (default: 10s)
- Background thread execution
- Graceful shutdown

**Example:**
```python
automator = ScreenAutomator(rules_dir="data/rules")
automator.start()  # Runs in background
# ... later ...
automator.stop()
```

---

### 6. ContextAwareAutomator (`src/context_automator.py`)

**Purpose:** Window-specific rule execution

**Enhancement over ScreenAutomator:**
- Tracks active window context
- Only executes rules for current window
- Maintains cursor position
- Restores focus after execution

**Use Case:**
```python
# Rule only triggers in specific application
rule = Rule(
    name="Excel Macro",
    triggers=[
        WindowTrigger(window_title="*Excel*"),
        ImageTrigger(image="calculate_button.png")
    ],
    actions=[...]
)
```

**Design Notes:**
- Extends `ScreenAutomator`
- Uses `WindowManager` for context
- Implements cursor position restoration
- Supports window focus preservation

---

## Framework Modules

### 1. Expectations (`src/expectations.py`)

**Purpose:** Playwright-style assertions with auto-retry

**Philosophy:**
```python
# ❌ Traditional assertions fail immediately
assert find_image("button.png") is not None  # Flaky!

# ✅ Expectations auto-retry until timeout
expect(automator).to_have_image("button.png", timeout=5000)
# Retries for up to 5 seconds, eliminates flakiness
```

**Expectation Types:**

**ImageExpectation:**
```python
expect(automator).to_have_image("success.png")
expect(automator).not_to_have_image("error.png")
expect(automator).to_be_at_location("icon.png", (100, 100))
```

**WindowExpectation:**
```python
expect(window_manager).to_have_window("Notepad")
expect(window_manager).to_have_window("*Chrome*", partial=True)
```

**StateExpectation:**
```python
expect(value).to_be(expected)
expect(count).to_be_greater_than(0)
expect(result).to_be_truthy()
```

**Architecture:**
```python
class Expectation(ABC):
    @abstractmethod
    def check(self) -> ExpectationResult:
        """Check if expectation is met"""

    def wait_until_met(self, timeout: int):
        """Poll until met or timeout"""
        start = time.time()
        while time.time() - start < timeout/1000:
            if self.check().passed:
                return
            time.sleep(self.poll_interval/1000)
        raise ExpectationTimeoutError(...)
```

**Design Notes:**
- Inspired by Playwright's `expect()` API
- All expectations are retryable
- Configurable timeout and poll interval
- Clear error messages on failure

---

### 2. Actionability (`src/actionability.py`)

**Purpose:** Smart waiting and element stability

**Problem It Solves:**
UI elements can be:
- Not yet visible
- Still loading
- Animating into position
- Being rendered

Traditional automation clicks too early, leading to failures.

**Components:**

**AutoWaiter:**
```python
waiter = AutoWaiter(timeout=10000, poll_interval=50)

# Wait for condition
result = waiter.wait_for_condition(
    lambda: is_ready(),
    "system to be ready"
)

# Wait for image
location = waiter.wait_for_image("button.png", automator)

# Wait for stability (not animating)
stable_pos = waiter.ensure_stable(
    lambda: get_position(),
    duration=100,  # Must be stable for 100ms
    tolerance=5    # Within 5 pixels
)
```

**SmartAutomator:**
```python
smart = SmartAutomator(automator, timeout=10000)

# Automatically waits and ensures stability
smart.click_image("button.png", ensure_stable=True)

# Wait for element to disappear
smart.wait_for_image_to_disappear("loading.png")
```

**Stability Algorithm:**
```
1. Get initial position
2. Wait duration_ms
3. Get new position
4. If moved > tolerance pixels → reset timer, goto 2
5. If stable for duration → return position
6. If timeout → raise TimeoutError
```

**Benefits:**
- Eliminates race conditions
- No manual `time.sleep()`
- Adapts to system speed
- Handles animations gracefully

---

### 3. Page Objects (`src/page_objects.py`)

**Purpose:** Organize automation code using Page Object Model

**Pattern:**
```python
class LoginPage(BasePage):
    def __init__(self, automator):
        super().__init__(automator)

        # Define locators
        self.username = Element(
            Locator(type=LocatorType.IMAGE, value="username.png"),
            automator
        )
        self.password = Element(
            Locator(type=LocatorType.IMAGE, value="password.png"),
            automator
        )
        self.submit = Element(
            Locator(type=LocatorType.IMAGE, value="submit.png"),
            automator
        )

    def login(self, username: str, password: str):
        """High-level login action"""
        self.username.click()
        self.username.type(username)
        self.password.click()
        self.password.type(password)
        self.submit.click()
```

**Usage:**
```python
login_page = LoginPage(automator)
login_page.login("admin", "password123")
```

**Benefits:**
- Encapsulates page structure
- Reusable across tests
- Easy to maintain (change locators in one place)
- Readable test code

**Locator Types:**
- `IMAGE`: Template matching
- `COORDINATES`: Fixed (x, y) position
- `TEXT`: Text-based (future: property automation)
- `WINDOW_TITLE`: Window title matching

---

### 4. Data-Driven (`src/data_driven.py`)

**Purpose:** Drive automation from external data sources

**Supported Formats:**
- CSV
- JSON
- XML
- Excel (XLSX)

**Example:**

**data.csv:**
```csv
username,password,expected
alice,pass123,Success
bob,wrongpass,Error
```

**Test:**
```python
from src.data_driven import CSVDataSource

data = CSVDataSource("data.csv")
for row in data.iterate():
    login_page.login(row["username"], row["password"])
    expect(automator).to_have_image(f"{row['expected']}.png")
```

**Features:**
- Iterate over rows
- Filter by condition
- Transform data
- Validate schema
- Cache for performance

**Design Notes:**
- Each data source implements `DataSource` interface
- Lazy loading for large files
- Supports nested data (JSON/XML)
- Excel: Reads first sheet by default

---

## GUI Architecture

### Component Structure

```
MainWindow (gui/main_window.py)
├── RulesListView
│   ├── Rule items (with enable/disable)
│   └── Context menu (Edit, Delete, Duplicate)
│
├── ControlPanel
│   ├── Start/Stop monitoring
│   ├── Create new rule
│   └── Import/Export rules
│
└── StatusBar
    └── Current status messages

RuleEditor (gui_components/rule_editor.py)
├── BasicInfoPanel
│   ├── Name input
│   ├── Priority slider
│   └── Cluster group selector
│
├── TriggersPanel
│   ├── Trigger type dropdown
│   ├── Add/Remove triggers
│   └── Screen capture tool
│
├── ActionsPanel
│   ├── Action list (reorderable)
│   ├── Record actions button
│   └── Action editor
│
└── ButtonBar
    └── Save, Cancel, Test

RecordHUD (gui_components/record_hud.py)
├── Transparent overlay
├── Click capture
├── Keystroke capture
└── ESC to stop
```

### Type Safety with Protocols

To avoid circular imports, the GUI uses **Protocols** (structural typing):

**gui_components/protocols.py:**
```python
class WindowProtocol(Protocol):
    """Interface for MainWindow"""
    def refresh_rules_list(self) -> None: ...
    def show_message(self, title: str, message: str) -> None: ...
    # ... other methods
```

**Usage:**
```python
# Instead of:
from gui.main_window import MainWindow  # Circular!

# Use:
from gui_components.protocols import WindowProtocol

def __init__(self, master: WindowProtocol):
    # Type-safe without circular import
    self.window = master
    self.window.refresh_rules_list()
```

---

## Data Flow

### 1. Rule Execution Flow

```
User Creates Rule
       ↓
Saved to JSON (data/rules/)
       ↓
ScreenAutomator.start()
       ↓
Background Thread Starts
       ↓
┌──────────────────────┐
│ Monitoring Loop      │
│                      │
│ 1. Check mouse idle  │ ← If user active, skip
│ 2. Capture screen    │
│ 3. Load enabled rules│
│ 4. Check triggers    │
│    ├─ Image found?   │
│    ├─ Window match?  │
│    └─ Idle timeout?  │
│ 5. Execute actions   │
│    ├─ Click          │
│    ├─ Type keys      │
│    └─ Wait           │
│ 6. Sleep interval    │
└──────────────────────┘
       ↓
Continue loop until stop()
```

### 2. Modern API Flow

```
User Code
framework.click_image("button.png")
       ↓
SmartAutomator
       ↓
AutoWaiter.wait_for_image()
       ↓
┌─────────────────────────┐
│ Polling Loop            │
│                         │
│ while timeout not reached:│
│   ImageDetector.find_image()│
│   if found → break      │
│   sleep(poll_interval)  │
└─────────────────────────┘
       ↓
ensure_stable()
       ↓
┌─────────────────────────┐
│ Stability Check         │
│                         │
│ while not stable:       │
│   pos1 = get_position() │
│   sleep(duration)       │
│   pos2 = get_position() │
│   if distance < tolerance:│
│     stable = True       │
└─────────────────────────┘
       ↓
pyautogui.click(x, y)
       ↓
Return to user code
```

### 3. Expectation Flow

```
expect(automator).to_have_image("success.png", timeout=5000)
       ↓
ImageExpectation created
       ↓
wait_until_met(5000)
       ↓
┌─────────────────────────┐
│ Retry Loop              │
│                         │
│ start_time = now()      │
│ while now() - start < timeout:│
│   result = check()      │
│   if result.passed:     │
│     return success      │
│   sleep(poll_interval)  │
│                         │
│ raise ExpectationTimeoutError│
└─────────────────────────┘
```

---

## Extension Points

### 1. Custom Actions

Add new action types by extending `ActionExecutor`:

```python
# src/action_executor.py
class ActionExecutor:
    def execute_action(self, action, context=None):
        if action.type == "custom_action":
            return self._execute_custom_action(action)
        # ... existing actions

    def _execute_custom_action(self, action):
        # Your implementation
        params = action.params
        # ... do something
```

### 2. Custom Triggers

Extend trigger evaluation in `ScreenAutomator`:

```python
# src/automator.py
def _check_trigger(self, trigger):
    if trigger.type == "custom_trigger":
        return self._check_custom_trigger(trigger)
    # ... existing triggers

def _check_custom_trigger(self, trigger):
    # Your implementation
    return True  # or False
```

### 3. Custom Matchers

Add new expectation types:

```python
# src/expectations.py
class CustomExpectation(Expectation):
    def __init__(self, subject, expected):
        self.subject = subject
        self.expected = expected

    def check(self) -> ExpectationResult:
        # Your logic
        passed = self.subject.check_something(self.expected)
        return ExpectationResult(
            passed=passed,
            message=f"Custom check: {passed}"
        )

# Usage
expect(my_obj).to_satisfy_custom_condition(value)
```

### 4. Custom Data Sources

Implement the `DataSource` protocol:

```python
# src/data_driven.py
class CustomDataSource:
    def __init__(self, source: str):
        self.source = source
        self.data = self._load_data()

    def _load_data(self):
        # Load from your source
        pass

    def iterate(self):
        for item in self.data:
            yield item
```

---

## Design Patterns

### 1. **Factory Pattern**

Used in `modern_api.py`:
```python
def create_framework(timeout=10000, poll_interval=50):
    """Factory for creating framework instances"""
    return ScreenAutomatorFramework(timeout, poll_interval)
```

**Benefits:**
- Simple creation
- Hides complexity
- Allows future changes

### 2. **Strategy Pattern**

Used in data sources:
```python
# Different strategies for loading data
csv_source = CSVDataSource("data.csv")
json_source = JSONDataSource("data.json")
xml_source = XMLDataSource("data.xml")

# Same interface
for row in source.iterate():
    # Process data
```

### 3. **Template Method Pattern**

Used in expectations:
```python
class Expectation(ABC):
    @abstractmethod
    def check(self) -> ExpectationResult:
        """Subclass implements check logic"""

    def wait_until_met(self, timeout):
        """Template method - same for all expectations"""
        # Retry logic here
        while not timeout:
            if self.check().passed:
                return
```

### 4. **Observer Pattern**

Used in automation loop:
```python
# ScreenAutomator monitors screen
# Notifies via callbacks when rules trigger
automator.on_rule_triggered = lambda rule: print(f"Rule {rule.name} fired")
```

### 5. **Builder Pattern**

Used in rule creation:
```python
rule = (RuleBuilder()
    .with_name("Auto Save")
    .with_trigger(ImageTrigger("save_icon.png"))
    .with_action(ClickAction(100, 200))
    .with_priority(5)
    .build())
```

### 6. **Facade Pattern**

`ScreenAutomatorFramework` is a facade:
```python
class ScreenAutomatorFramework:
    """Unified interface to complex subsystems"""
    def __init__(self):
        self.automator = ScreenAutomator()
        self.detector = ImageDetector()
        self.waiter = AutoWaiter()
        self.smart = SmartAutomator(self.detector)

    def click_image(self, image):
        """Simple interface hiding complexity"""
        self.smart.click_image(image)
```

### 7. **Protocol Pattern (Structural Typing)**

Used for type safety without coupling:
```python
class WindowProtocol(Protocol):
    def refresh_rules_list(self) -> None: ...

# Any class matching this structure works
# No inheritance needed
```

---

## Performance Considerations

### 1. **Image Detection Optimization**

- **Region of Interest:** Only capture relevant screen area
- **Caching:** Cache template images
- **Downsampling:** Reduce resolution for faster matching
- **Multi-scale:** Try different scales if not found

### 2. **Rule Clustering**

Rules with same triggers are grouped:
```python
# Instead of 10 screen captures for 10 rules
# Group rules by window → 1 capture per window
clusters = rule_manager.get_rules_by_cluster()
```

### 3. **Polling Intervals**

- Main loop: 10s (configurable)
- Waiting: 50ms default (configurable)
- Balance responsiveness vs CPU usage

### 4. **Thread Safety**

- Use locks for shared state
- Image detection is stateless
- Rule manager uses file locking

---

## Security Considerations

### 1. **Rule Validation**

- Validate rule JSON before loading
- Sanitize file paths
- Check action parameters

### 2. **Safe Action Execution**

- Mouse idle detection prevents interference
- Action timeouts prevent infinite loops
- User can interrupt execution

### 3. **File System Access**

- Rules stored in designated directory
- No arbitrary file execution
- Images loaded from trusted paths

### 4. **Dependency Security**

- Regular dependency updates
- Bandit for security scanning
- No eval() or exec() usage

---

## Future Architecture Improvements

### 1. **Plugin System**

Enable third-party extensions:
```python
# plugins/my_plugin.py
class MyPlugin:
    def on_load(self, framework):
        framework.register_action("my_action", self.execute)
```

### 2. **Remote Control**

Enable REST API for remote automation:
```python
@app.post("/rules/{rule_id}/execute")
def execute_rule(rule_id: str):
    automator.execute_rule(rule_id)
```

### 3. **Cloud Sync**

Sync rules across machines:
```python
framework.sync.upload_rules()
framework.sync.download_rules()
```

### 4. **ML-Based Detection**

Enhance image detection with ML:
```python
# Fallback to ML if template matching fails
detector.enable_ml_fallback(model="yolov8")
```

---

## Conclusion

Screen Automator's architecture emphasizes:

1. **Reliability**: Auto-waiting eliminates flakiness
2. **Maintainability**: Clear separation of concerns
3. **Extensibility**: Multiple extension points
4. **Type Safety**: Comprehensive type hints
5. **Testability**: High test coverage

The layered design allows users to work at their preferred abstraction level, from low-level control to high-level framework APIs.

For implementation details, see:
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing approach
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guide
- [FRAMEWORK_GUIDE.md](FRAMEWORK_GUIDE.md) - Framework usage

---

*Last Updated: 2025-11-10*
*Version: 2.3.0*
