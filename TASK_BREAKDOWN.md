# Screen Automator - Detailed Task Breakdown
**Based on**: ANALYSIS_REPORT.md
**Target**: v2.3.0 Production Release
**Timeline**: 6 weeks (4 sprints)

---

## 🎯 Sprint 1: Critical Fixes (v2.0.1 - Week 1)
**Goal**: Stable release with working type checking and core API tests
**Total Effort**: 21-30 hours

### Task 1.1: Quick Security Fixes (Priority: CRITICAL, Effort: 20 min)

**Subtasks:**
- [ ] Fix MD5 security warning #1
  - **File**: `src/automator.py:103`
  - **Change**: `hashlib.md5(image_bytes).hexdigest()`
  - **To**: `hashlib.md5(image_bytes, usedforsecurity=False).hexdigest()`
  - **Effort**: 2 minutes

- [ ] Fix MD5 security warning #2
  - **File**: `src/context_automator.py:536`
  - **Change**: `hashlib.md5(image_bytes).hexdigest()`
  - **To**: `hashlib.md5(image_bytes, usedforsecurity=False).hexdigest()`
  - **Effort**: 2 minutes

- [ ] Add encoding to file opens
  - **File**: `src/rule_manager.py`
  - **Lines**: 328, 338, 360, 366
  - **Change**: `open(file_path)` → `open(file_path, encoding='utf-8')`
  - **Effort**: 15 minutes

- [ ] Run bandit security scan to verify fixes
  - **Command**: `poetry run bandit -r src/`
  - **Verify**: HIGH security issues reduced from 2 to 0
  - **Effort**: 1 minute

**Acceptance Criteria:**
- Bandit shows 0 HIGH security issues
- All file operations use explicit encoding
- No functionality broken

---

### Task 1.2: Resolve GUI Module Conflict (Priority: CRITICAL, Effort: 4-6h)

**Problem**: Both `gui.py` (3,171 lines) and `gui/` package exist, blocking mypy

**Investigation Phase (30 min):**
- [ ] List all imports of `gui` module across codebase
  - **Command**: `grep -r "from gui import" . --include="*.py"`
  - **Command**: `grep -r "import gui" . --include="*.py"`
  - **Document**: Which files import what

- [ ] Check if `gui.py` is used at all
  - **Command**: `git log --follow gui.py`
  - **Check**: Recent changes and usage

- [ ] Check `gui/` package contents
  - **Files**: `gui/__init__.py`, `gui/main_window.py`
  - **Check**: What classes/functions are exported

**Decision Matrix:**

**Option A: Keep gui.py, delete gui/ package**
- Pros: Single file, simpler structure
- Cons: 3,171 line monolith, harder to maintain
- Effort: 1 hour
- Steps:
  1. [ ] Copy any unique code from `gui/main_window.py` to `gui.py`
  2. [ ] Update all imports: `from gui.main_window import` → `from gui import`
  3. [ ] Delete `gui/` directory
  4. [ ] Run tests: `poetry run pytest tests/test_gui*.py`

**Option B: Keep gui/ package, rename gui.py**
- Pros: Better organization, modular structure
- Cons: Need to update all references to gui.py
- Effort: 2-3 hours
- Steps:
  1. [ ] Rename `gui.py` → `gui_main.py`
  2. [ ] Update all imports: `from gui import` → `from gui_main import`
  3. [ ] Update entry points in `pyproject.toml` if any
  4. [ ] Update CLI references in `cli.py`
  5. [ ] Run tests: `poetry run pytest tests/test_gui*.py`

**Option C: Merge into gui/ package (RECOMMENDED)**
- Pros: Clean organization, better maintainability
- Cons: Most work upfront, need careful merge
- Effort: 4-6 hours
- Steps:
  1. [ ] Create backup: `cp gui.py gui.py.backup`
  2. [ ] Identify classes/functions in `gui.py` that should be in `gui/main_window.py`
  3. [ ] Move non-MainWindow code to appropriate modules:
     - [ ] Dialog functions → `gui_components/dialogs.py`
     - [ ] Widget utilities → `gui_components/widgets.py`
     - [ ] Tab implementations → new files in `gui/`
  4. [ ] Merge MainWindow code with `gui/main_window.py`
  5. [ ] Update `gui/__init__.py` to export main classes
  6. [ ] Update all imports throughout codebase
  7. [ ] Delete `gui.py`
  8. [ ] Run all GUI tests
  9. [ ] Run mypy to verify type checking works

**Implementation (Option C - Recommended):**

- [ ] Phase 1: Analyze and categorize (1h)
  ```bash
  # Count classes and functions in gui.py
  grep -c "^class " gui.py
  grep -c "^def " gui.py

  # List all classes
  grep "^class " gui.py
  ```

- [ ] Phase 2: Create module structure (1h)
  - [ ] Create `gui/tabs.py` for tab implementations
  - [ ] Create `gui/dialogs.py` for dialog management
  - [ ] Plan class distribution

- [ ] Phase 3: Move code (2h)
  - [ ] Move tab classes to `gui/tabs.py`
  - [ ] Move dialog managers to `gui/dialogs.py`
  - [ ] Move utilities to appropriate modules
  - [ ] Keep MainWindow in `gui/main_window.py`

- [ ] Phase 4: Update imports (30min)
  - [ ] Update `cli.py`
  - [ ] Update test files
  - [ ] Update any examples

- [ ] Phase 5: Testing (30min)
  - [ ] Run: `poetry run pytest tests/test_gui*.py -v`
  - [ ] Run: `poetry run mypy src/ gui/ --config-file pyproject.toml`
  - [ ] Verify: Mypy shows errors instead of module conflict

**Acceptance Criteria:**
- Only `gui/` package exists (no `gui.py`)
- Mypy runs without module conflict errors
- All GUI tests pass
- Type checking works on gui modules

---

### Task 1.3: Fix Modern API Type Errors (Priority: CRITICAL, Effort: 1-2h)

**File**: `src/modern_api.py`

**Error 1: RuleManager.add_rule (Line 92)**
- [ ] Check RuleManager API
  - **File**: `src/rule_manager.py`
  - **Action**: `grep -n "def add_rule\|def load_rule\|def create_rule" src/rule_manager.py`
  - **Document**: What methods actually exist

- [ ] Fix the method call
  - **Current**: `self.rule_manager.add_rule(rule)`
  - **Options**:
    - If `add_rule` exists: Add type stub/annotation
    - If `load_rule` exists: Change to `load_rule`
    - If neither: Implement `add_rule` method
  - **Effort**: 30 minutes

**Error 2: RuleManager.get_all_rules (Line 96)**
- [ ] Check RuleManager API
  - **Action**: `grep -n "def get_all_rules\|def get_rules\|def list_rules" src/rule_manager.py`

- [ ] Fix the method call
  - **Current**: `self.rule_manager.get_all_rules()`
  - **Options**:
    - If `get_all_rules` exists: Add type annotation
    - If different name: Update call
    - If neither: Implement method
  - **Effort**: 30 minutes

**Error 3: Expectation.to_have_image (Line 200)**
- [ ] Check Expectation API
  - **File**: `src/expectations.py`
  - **Action**: `grep -n "def to_have_image\|def to_be_visible" src/expectations.py`

- [ ] Fix method name
  - **Current**: `expect(detector).to_have_image(image_path)`
  - **Likely should be**: `expect(detector).to_be_visible(image_path)`
  - **Effort**: 15 minutes

**Error 4: Expectation.not_to_have_image (Line 219)**
- [ ] Check Expectation negative assertions
  - **Action**: `grep -n "def not_to" src/expectations.py`

- [ ] Fix method name
  - **Current**: `expect(detector).not_to_have_image(image_path)`
  - **Likely should be**: `expect(detector).not_to_be_visible(image_path)`
  - **Effort**: 15 minutes

**Testing:**
- [ ] Create simple test script
  ```python
  from src.modern_api import create_framework

  framework = create_framework()
  # Test each fixed method
  ```
- [ ] Run mypy: `poetry run mypy src/modern_api.py`
- [ ] Verify: 0 errors in modern_api.py

**Acceptance Criteria:**
- All 4 type errors in modern_api.py fixed
- Mypy shows 0 errors for src/modern_api.py
- Modern API imports successfully
- API calls work as expected

---

### Task 1.4: Create test_modern_api.py (Priority: CRITICAL, Effort: 6-8h)

**Goal**: Comprehensive test coverage for modern API

**Setup (30 min):**
- [ ] Create `tests/test_modern_api.py`
- [ ] Add imports and fixtures
  ```python
  import pytest
  from unittest.mock import Mock, patch, MagicMock
  from src.modern_api import create_framework, ScreenAutomatorFramework
  ```

**Test Suite Structure:**

**1. Factory Function Tests (1h)**
- [ ] Test `create_framework()` with default parameters
  ```python
  def test_create_framework_default():
      framework = create_framework()
      assert isinstance(framework, ScreenAutomatorFramework)
      assert framework.timeout == 30000
  ```

- [ ] Test `create_framework()` with custom parameters
  ```python
  def test_create_framework_custom_timeout():
      framework = create_framework(timeout=5000)
      assert framework.timeout == 5000
  ```

- [ ] Test `create_framework()` with custom rules_dir
  ```python
  def test_create_framework_custom_rules_dir():
      framework = create_framework(rules_dir="custom/path")
      # Verify automator initialized with custom path
  ```

**2. Image Operations Tests (2h)**
- [ ] Test `click_image()` with mocked dependencies
  ```python
  @patch('src.modern_api.SmartAutomator')
  def test_click_image_default(mock_smart):
      framework = create_framework()
      framework.click_image("test.png")
      mock_smart.return_value.click_image.assert_called_once()
  ```

- [ ] Test `click_image()` with custom timeout
- [ ] Test `click_image()` with ensure_stable=False
- [ ] Test `double_click_image()`
- [ ] Test `right_click_image()`

**3. Expectation Tests (2h)**
- [ ] Test `expect_image()` success case
  ```python
  @patch('src.modern_api.expect')
  def test_expect_image_success(mock_expect):
      framework = create_framework()
      framework.expect_image("test.png")
      mock_expect.assert_called_once()
  ```

- [ ] Test `expect_image()` timeout
- [ ] Test `expect_not_image()`
- [ ] Test expectation with custom timeout

**4. Waiting Operations Tests (1.5h)**
- [ ] Test `wait_for_image()`
- [ ] Test `wait_for_condition()`
- [ ] Test `wait()` simple delay
- [ ] Test waiting with timeout expiration

**5. Rule Operations Tests (1.5h)**
- [ ] Test `start_monitoring()`
- [ ] Test `stop_monitoring()`
- [ ] Test `add_rule()` (if fixed in Task 1.3)
- [ ] Test `get_rules()` (if fixed in Task 1.3)

**6. Integration Tests (1h)**
- [ ] Test complete workflow
  ```python
  @patch('src.modern_api.SmartAutomator')
  @patch('src.modern_api.expect')
  def test_complete_workflow(mock_expect, mock_smart):
      framework = create_framework()
      framework.click_image("button.png")
      framework.expect_image("result.png")
      # Verify sequence
  ```

**7. Error Handling Tests (30min)**
- [ ] Test invalid parameters
- [ ] Test timeout errors
- [ ] Test image not found
- [ ] Test graceful degradation

**Documentation:**
- [ ] Add module docstring to test file
- [ ] Add docstrings to each test
- [ ] Add README section about running tests

**Acceptance Criteria:**
- 20+ tests covering all modern API methods
- All tests pass
- Code coverage >80% for src/modern_api.py
- Tests are well-documented

---

### Task 1.5: Sprint 1 Verification (Effort: 1h)

**Quality Checks:**
- [ ] Run full test suite
  ```bash
  poetry run pytest -v --cov=src/modern_api
  ```

- [ ] Run mypy on all source
  ```bash
  poetry run mypy src/ --config-file pyproject.toml
  ```
  - Verify: GUI module conflict resolved
  - Verify: modern_api.py shows 0 errors
  - Document: Remaining error count

- [ ] Run security scan
  ```bash
  poetry run bandit -r src/
  ```
  - Verify: 0 HIGH security issues

- [ ] Run all quality tools
  ```bash
  poetry run ruff check src/
  poetry run pylint src/modern_api.py
  ```

**Version Bump:**
- [ ] Update version in `pyproject.toml`: `2.0.0` → `2.0.1`
- [ ] Update version in `src/__init__.py`: `2.0.0` → `2.0.1`
- [ ] Update CHANGELOG.md with Sprint 1 changes

**Git Operations:**
- [ ] Commit all changes: `git add -A && git commit -m "feat: v2.0.1 - critical fixes and modern API tests"`
- [ ] Tag release: `git tag -a v2.0.1 -m "Version 2.0.1 - Critical fixes"`
- [ ] Push: `git push && git push --tags`

**Acceptance Criteria:**
- Version 2.0.1 tagged and pushed
- Modern API fully tested
- Type checking works
- Security issues fixed
- All Sprint 1 goals met

---

## 🧪 Sprint 2: Framework Testing (v2.1.0 - Weeks 2-3)
**Goal**: Comprehensive test coverage for all framework modules
**Total Effort**: 20-28 hours

### Task 2.1: Create test_expectations.py (Priority: HIGH, Effort: 4-6h)

**Setup (30 min):**
- [ ] Create `tests/test_expectations.py`
- [ ] Set up fixtures and mocks

**Test Categories:**

**1. expect() Function Tests (1h)**
- [ ] Test with ImageDetector subject
- [ ] Test with WindowManager subject
- [ ] Test with generic state subject
- [ ] Test type detection logic

**2. ImageExpectation Tests (1.5h)**
- [ ] Test `to_be_visible()` success
- [ ] Test `to_be_visible()` timeout
- [ ] Test `not_to_be_visible()`
- [ ] Test retry logic
- [ ] Test custom timeout
- [ ] Test polling interval

**3. WindowExpectation Tests (1h)**
- [ ] Test `to_be_active()`
- [ ] Test `to_have_title()`
- [ ] Test window state expectations
- [ ] Test retry mechanism

**4. StateExpectation Tests (1h)**
- [ ] Test custom condition expectations
- [ ] Test boolean state checks
- [ ] Test retry on state change

**5. Error Handling Tests (30min)**
- [ ] Test timeout errors with clear messages
- [ ] Test retry history in error messages
- [ ] Test invalid subjects

**6. Integration Tests (30min)**
- [ ] Test chaining expectations
- [ ] Test complex scenarios
- [ ] Test with real-world use cases

**Acceptance Criteria:**
- 25+ tests for expectations module
- All tests pass
- Coverage >85% for src/expectations.py

---

### Task 2.2: Create test_actionability.py (Priority: HIGH, Effort: 6-8h)

**Setup (30 min):**
- [ ] Create `tests/test_actionability.py`
- [ ] Mock pyautogui and time functions

**Test Categories:**

**1. AutoWaiter Tests (2h)**
- [ ] Test `wait_for_condition()` success
- [ ] Test `wait_for_condition()` timeout
- [ ] Test custom polling interval
- [ ] Test custom timeout
- [ ] Test condition evaluation frequency
- [ ] Test immediate success (no wait needed)

**2. Stability Checker Tests (1.5h)**
- [ ] Test `check_element_stable()` with stable element
- [ ] Test with moving element (should wait)
- [ ] Test with animating element
- [ ] Test stability timeout
- [ ] Test custom stability duration
- [ ] Test position change detection

**3. SmartAutomator Tests (2.5h)**
- [ ] Test `click_image()` with auto-wait
- [ ] Test `click_image()` with stability check
- [ ] Test `click_image()` timeout
- [ ] Test `double_click_image()`
- [ ] Test `right_click_image()`
- [ ] Test `type_text()` with field detection
- [ ] Test interaction with image detector

**4. Edge Cases (1h)**
- [ ] Test rapid position changes
- [ ] Test element appears then disappears
- [ ] Test multiple elements matching
- [ ] Test zero timeout
- [ ] Test very long timeout

**5. Performance Tests (30min)**
- [ ] Test polling doesn't use excessive CPU
- [ ] Test efficient image matching
- [ ] Test stability check performance

**Acceptance Criteria:**
- 30+ tests for actionability module
- All tests pass
- Coverage >80% for src/actionability.py
- Performance tests show efficient polling

---

### Task 2.3: Create test_page_objects.py (Priority: HIGH, Effort: 6-8h)

**Setup (1h):**
- [ ] Create `tests/test_page_objects.py`
- [ ] Create sample page objects for testing
- [ ] Mock automator and locators

**Test Categories:**

**1. Locator Tests (1h)**
- [ ] Test ImageLocator
- [ ] Test PropertyLocator (title, class, id)
- [ ] Test RelativeLocator (near, above, below)
- [ ] Test locator strategy selection

**2. Element Tests (2h)**
- [ ] Test `Element.find()` with image locator
- [ ] Test `Element.find()` with property locator
- [ ] Test `Element.click()`
- [ ] Test `Element.type()`
- [ ] Test `Element.is_visible()`
- [ ] Test `Element.wait_until_visible()`
- [ ] Test element caching

**3. BasePage Tests (2h)**
- [ ] Test page initialization
- [ ] Test element registration
- [ ] Test `get_element()` retrieval
- [ ] Test page navigation methods
- [ ] Test `wait_for_page_load()`
- [ ] Test page state validation

**4. BaseDialog Tests (1h)**
- [ ] Test dialog appearance detection
- [ ] Test dialog dismissal
- [ ] Test `wait_until_present()`
- [ ] Test dialog-specific interactions

**5. Page Object Pattern Tests (1.5h)**
- [ ] Test inheritance from BasePage
- [ ] Test custom page implementations
- [ ] Test page transitions
- [ ] Test element hierarchies
- [ ] Test reusable components

**6. Integration Tests (30min)**
- [ ] Test complete page object workflow
- [ ] Test multi-page scenarios
- [ ] Test page object composition

**Acceptance Criteria:**
- 35+ tests for page_objects module
- All tests pass
- Coverage >75% for src/page_objects.py
- Example page objects documented

---

### Task 2.4: Create test_data_driven.py (Priority: MEDIUM, Effort: 4-6h)

**Setup (30 min):**
- [ ] Create `tests/test_data_driven.py`
- [ ] Create sample data files (CSV, JSON, XML)
- [ ] Set up temp directory for test data

**Test Categories:**

**1. DataProvider Tests - CSV (1h)**
- [ ] Test CSV file loading
- [ ] Test column name extraction
- [ ] Test data row iteration
- [ ] Test CSV with headers
- [ ] Test CSV without headers
- [ ] Test malformed CSV handling

**2. DataProvider Tests - JSON (1h)**
- [ ] Test JSON array loading
- [ ] Test JSON object loading
- [ ] Test nested JSON
- [ ] Test JSON validation
- [ ] Test malformed JSON handling

**3. DataProvider Tests - XML (1h)**
- [ ] Test XML parsing
- [ ] Test element extraction
- [ ] Test attribute reading
- [ ] Test nested elements
- [ ] Test malformed XML handling
- [ ] Test XML security (XXE prevention)

**4. DataDrivenTest Tests (1.5h)**
- [ ] Test parameterized test execution
- [ ] Test test multiplier effect
- [ ] Test data iteration
- [ ] Test test reporting with data
- [ ] Test skip conditions

**5. ConfigManager Tests (1h)**
- [ ] Test environment-specific configs
- [ ] Test config loading
- [ ] Test config merging
- [ ] Test config validation
- [ ] Test missing config handling

**Acceptance Criteria:**
- 25+ tests for data_driven module
- All tests pass
- Coverage >70% for src/data_driven.py
- Sample data files included in tests/

---

### Task 2.5: Sprint 2 Verification (Effort: 2h)

**Test Execution:**
- [ ] Run new test suites
  ```bash
  poetry run pytest tests/test_expectations.py -v
  poetry run pytest tests/test_actionability.py -v
  poetry run pytest tests/test_page_objects.py -v
  poetry run pytest tests/test_data_driven.py -v
  ```

- [ ] Run full test suite
  ```bash
  poetry run pytest --cov=src --cov-report=html
  ```
  - Verify: Framework modules now have >70% coverage
  - Generate coverage report

**Coverage Analysis:**
- [ ] Check coverage for each module
  ```bash
  poetry run pytest --cov=src.modern_api --cov=src.expectations --cov=src.actionability --cov=src.page_objects --cov=src.data_driven --cov-report=term-missing
  ```

- [ ] Document coverage gaps
- [ ] Identify untested edge cases

**Quality Checks:**
- [ ] Run ruff: `poetry run ruff check tests/`
- [ ] Run pylint on tests: `poetry run pylint tests/test_expectations.py tests/test_actionability.py`
- [ ] Verify test quality

**Version Bump:**
- [ ] Update version: `2.0.1` → `2.1.0`
- [ ] Update CHANGELOG.md with Sprint 2 achievements
- [ ] Commit and tag: `git tag -a v2.1.0 -m "Version 2.1.0 - Framework test coverage"`

**Acceptance Criteria:**
- All 5 framework modules have dedicated test files
- Framework test coverage >70%
- All tests pass
- Version 2.1.0 released

---

## 🎨 Sprint 3: Type Safety & GUI (v2.2.0 - Weeks 4-5)
**Goal**: Clean type checking and refactored GUI
**Total Effort**: 24-35 hours

### Task 3.1: Fix gui_components Type Errors (Priority: HIGH, Effort: 8-12h)

**widgets.py (15 errors - 4h)**
- [ ] Fix tkinter method/property confusion (Lines 159, 194, 225, 266, 271)
  - Issue: Assigning to methods instead of creating properties
  - Solution: Use proper property decorators or instance variables

- [ ] Fix operator errors (Lines 181-182)
  - Issue: Callable type operations
  - Solution: Proper type annotations

- [ ] Fix function/attribute mismatches (Lines 213, 217, 231, 232, 242)
  - Issue: Mixing function calls and attribute access
  - Solution: Consistent method calls

**dialogs.py (5 errors - 2h)**
- [ ] Resolve circular import (Line 10)
  - Current: `from gui.main_window import MainWindow`
  - Solution: Use TYPE_CHECKING or dependency injection

- [ ] Fix MainWindow undefined errors (Lines 23, 62, 113, 204)
  - Root cause: Circular import
  - Solution: Forward references or protocol

- [ ] Remove bare except (Line 212)
  - Change: `except: pass` → `except Exception as e: logger.warning(e)`

**rule_editor.py (14 errors - 3h)**
- [ ] Fix LabelFrame vs Labelframe (Lines 50, 61, 89, 114)
  - Issue: ttkbootstrap API inconsistency
  - Solution: Use correct class names

- [ ] Fix tuple type mismatch (Line 302)
- [ ] Fix rule editing type issues (Lines 348, 363, 381)

**record_hud.py - Review and fix any issues (1h)**

**Testing after fixes (2h)**
- [ ] Run mypy on gui_components: `poetry run mypy gui_components/`
- [ ] Test GUI functionality
- [ ] Run GUI smoke tests

---

### Task 3.2: Resolve Circular Dependencies (Priority: HIGH, Effort: 3-4h)

**Analysis (1h):**
- [ ] Map all import dependencies
  ```bash
  # Find all imports
  grep -r "from gui" . --include="*.py"
  grep -r "from gui_components" . --include="*.py"
  ```

- [ ] Create dependency graph
- [ ] Identify circular loops

**Fix Strategy (2-3h):**

**Option A: Dependency Injection**
- [ ] Pass MainWindow as parameter to dialogs
  ```python
  # Instead of importing
  def create_dialog(parent_window: MainWindow):
      # Use passed reference
  ```

**Option B: Event System**
- [ ] Create event bus for GUI communication
- [ ] Remove direct class dependencies
- [ ] Use callbacks/signals

**Option C: Protocol/Interface (RECOMMENDED)**
- [ ] Define protocols in `gui_components/protocols.py`
  ```python
  from typing import Protocol

  class WindowProtocol(Protocol):
      def refresh(self) -> None: ...
      def show_message(self, msg: str) -> None: ...
  ```

- [ ] Use protocols instead of concrete types
- [ ] Remove circular imports

**Implementation:**
- [ ] Choose strategy (recommend Option C)
- [ ] Implement solution
- [ ] Update all affected files
- [ ] Test GUI functionality

**Verification:**
- [ ] Run: `poetry run mypy gui/ gui_components/`
- [ ] Verify: No circular import errors
- [ ] Test: GUI functionality unchanged

---

### Task 3.3: Refactor Complex Functions (Priority: MEDIUM, Effort: 7-9h)

**_process_rules_on_image() Refactor (4-5h)**

**File**: `src/automator.py:277`
**Stats**: 19 branches, 63 statements, 7 nested blocks

- [ ] Extract sanity check method (1h)
  ```python
  def _check_rule_sanity(self, rule: Rule) -> Optional[str]:
      """Return error message if rule fails sanity check."""
      if not rule.enabled:
          return f"Rule '{rule.name}' is disabled"
      # ... other checks
      return None
  ```

- [ ] Extract cooldown check method (30min)
  ```python
  def _check_rule_cooldown(self, rule: Rule) -> bool:
      """Return True if rule can execute (not in cooldown)."""
      # Move cooldown logic here
  ```

- [ ] Extract action execution method (1h)
  ```python
  def _execute_rule_actions(self, rule: Rule, location: tuple) -> bool:
      """Execute all actions for a triggered rule."""
      # Move execution logic here
  ```

- [ ] Refactor main loop (1h)
  ```python
  def _process_rules_on_image(self, image):
      for rule in self.rules:
          error = self._check_rule_sanity(rule)
          if error:
              continue

          if not self._check_rule_cooldown(rule):
              continue

          location = self._find_rule_match(image, rule)
          if location:
              self._execute_rule_actions(rule, location)
  ```

- [ ] Add comprehensive tests (1.5h)
- [ ] Verify no behavior changes

**_rule_matches_window() Refactor (3-4h)**

**File**: `src/rule_manager.py:209`
**Stats**: 15 return statements, 24 branches

- [ ] Create matching strategy interface (1h)
  ```python
  class WindowMatchStrategy(ABC):
      @abstractmethod
      def matches(self, rule: Rule, window: WindowInfo) -> bool:
          pass

  class ClassMatcher(WindowMatchStrategy):
      def matches(self, rule, window):
          return window.class_name == rule.target_window_class

  class TitleMatcher(WindowMatchStrategy):
      ...

  class ProcessMatcher(WindowMatchStrategy):
      ...
  ```

- [ ] Implement strategy pattern (1.5h)
- [ ] Update RuleManager to use strategies (30min)
- [ ] Add tests for each strategy (1h)

---

### Task 3.4: Fix Remaining Mypy Errors (Priority: MEDIUM, Effort: 10-15h)

**By Module:**

**cli.py (8 errors - 2h)**
- [ ] Fix List __setitem__ overload mismatches (Lines 358, 368, 404, 414)
- [ ] Add proper type annotations
- [ ] Test CLI functionality

**src/data_driven.py (7 errors - 2h)**
- [ ] Fix operator type issues (Lines 301, 307, 310)
- [ ] Fix attribute access on object (Line 311)
- [ ] Add proper type annotations for XML parsing

**src/automator.py (5 errors - 1.5h)**
- [ ] Fix Thread initialization (Lines 82, 116-117)
- [ ] Fix Monitor initialization (Line 135)

**src/context_automator.py (3 errors - 1h)**
- [ ] Add type annotation for _context_hashes (Line 472)
- [ ] Fix cluster_cooldown attribute (Line 714)
- [ ] Fix Optional[WindowInfo] union (Line 740)

**src/window_manager.py (1 error - 30min)**
- [ ] Add type annotation for windows variable (Line 76)

**src/page_objects.py (3 errors - 1h)**
- [ ] Fix no-any-return issues (Lines 112, 116)
- [ ] Add proper return type annotations

**src/actionability.py (1 error - 30min)**
- [ ] Fix no-any-return (Line 156)

**src/screen_selector.py (2 errors - 1h)**
- [ ] Fix get_monitors type issues

**src/rule_manager.py (2 errors - 1h)**
- [ ] Add type annotation for clusters (Line 166)

**src/image_detector.py (3 errors - 1h)**
- [ ] Fix ndarray return types (Lines 17, 22, 26)

**Verification (1h)**
- [ ] Run mypy on all modules
- [ ] Document remaining acceptable errors
- [ ] Target: <10 mypy errors total

---

### Task 3.5: Sprint 3 Verification (Effort: 2h)

**Type Checking:**
- [ ] Run comprehensive mypy check
  ```bash
  poetry run mypy src/ gui/ gui_components/ core/ utils/ --config-file pyproject.toml
  ```
- [ ] Document remaining errors
- [ ] Verify significant reduction (70+ → <10)

**GUI Testing:**
- [ ] Run all GUI tests
- [ ] Manual GUI smoke test
- [ ] Test all dialogs and widgets

**Quality Checks:**
- [ ] Run full test suite: `poetry run pytest`
- [ ] Run ruff: `poetry run ruff check .`
- [ ] Run pylint: `poetry run pylint src/`

**Version Bump:**
- [ ] Update version: `2.1.0` → `2.2.0`
- [ ] Update CHANGELOG.md
- [ ] Commit and tag: `git tag -a v2.2.0 -m "Version 2.2.0 - Type safety and GUI improvements"`

**Acceptance Criteria:**
- Type errors reduced from 70+ to <10
- GUI circular dependencies resolved
- Complex functions refactored
- Version 2.2.0 released

---

## 📚 Sprint 4: Polish & Documentation (v2.3.0 - Week 6)
**Goal**: Production-ready release with excellent documentation
**Total Effort**: 13-18 hours

### Task 4.1: Create ARCHITECTURE.md (Priority: MEDIUM, Effort: 4-6h)

**Structure:**

- [ ] Introduction (30min)
  - Project overview
  - Design philosophy
  - Target audience

- [ ] System Architecture (1.5h)
  - High-level architecture diagram
  - Module organization
  - Component relationships
  - Data flow diagrams

- [ ] Core Components (2h)
  - ImageDetector - Pattern matching
  - RuleManager - Rule processing
  - ActionExecutor - Action handling
  - WindowManager - Window operations
  - Modern API - Unified interface

- [ ] Framework Modules (1h)
  - Actionability - Auto-waiting
  - Expectations - Assertions
  - PageObjects - Page Object Model
  - DataDriven - Data management

- [ ] Extension Points (30min)
  - Custom actions
  - Custom matchers
  - Plugin system (if any)

- [ ] Design Patterns (30min)
  - Patterns used
  - Rationale for each

**Tools:**
- [ ] Create diagrams with Mermaid
- [ ] Add code examples
- [ ] Link to relevant files

---

### Task 4.2: Create TESTING_GUIDE.md (Priority: MEDIUM, Effort: 2-3h)

**Content:**

- [ ] Testing Philosophy (30min)
  - Why test
  - Test pyramid
  - Coverage goals

- [ ] Setting Up Tests (30min)
  - Install dependencies
  - Run test suite
  - IDE integration

- [ ] Writing Unit Tests (1h)
  - Test structure
  - Mocking patterns
  - Fixtures and setup
  - Example tests

- [ ] Writing Integration Tests (30min)
  - When to use
  - Setup and teardown
  - Data handling

- [ ] Running Tests (30min)
  - Local execution
  - CI/CD pipeline
  - Coverage reports
  - Debugging tests

---

### Task 4.3: Create CONTRIBUTING.md (Priority: MEDIUM, Effort: 2-3h)

**Content:**

- [ ] Welcome and Code of Conduct (30min)

- [ ] Development Setup (1h)
  - Prerequisites
  - Installation steps
  - IDE setup
  - Pre-commit hooks

- [ ] Development Workflow (1h)
  - Branching strategy
  - Commit conventions
  - Code style
  - Running quality checks

- [ ] Pull Request Process (30min)
  - PR template
  - Review process
  - Merging criteria

---

### Task 4.4: Replace Star Imports (Priority: LOW, Effort: 1h)

**Files with star imports (5 files):**

- [ ] gui_components/dialogs.py
  ```python
  # From:
  from ttkbootstrap.constants import *

  # To:
  from ttkbootstrap.constants import (
      PRIMARY, SECONDARY, SUCCESS, INFO, WARNING, DANGER,
      LIGHT, DARK, LEFT, RIGHT, TOP, BOTTOM, CENTER,
      # ... list all used constants
  )
  ```

- [ ] gui_components/record_hud.py
- [ ] gui_components/rule_editor.py
- [ ] gui_components/widgets.py
- [ ] gui/main_window.py

**Process per file (10-15 min each):**
- [ ] Run to find used constants: `grep -o '[A-Z_]\+' file.py | sort -u`
- [ ] Check ttkbootstrap docs for constant names
- [ ] Replace star import with explicit list
- [ ] Test functionality
- [ ] Run ruff to verify no F405 errors

---

### Task 4.5: Improve Error Handling (Priority: MEDIUM, Effort: 4-6h)

**Phase 1: Logging Infrastructure (1h)**
- [ ] Review utils/logging.py
- [ ] Ensure all modules use logger
- [ ] Add log levels appropriately

**Phase 2: Custom Exceptions (2h)**
- [ ] Create exceptions.py
  ```python
  class ScreenAutomatorError(Exception):
      """Base exception"""

  class ImageNotFoundError(ScreenAutomatorError):
      """Image not found on screen"""

  class WindowNotFoundError(ScreenAutomatorError):
      """Target window not found"""

  class ActionExecutionError(ScreenAutomatorError):
      """Action failed to execute"""

  class TimeoutError(ScreenAutomatorError):
      """Operation timed out"""
  ```

**Phase 3: Replace Broad Catches (2-3h)**
- [ ] Find all `except Exception:` (50+ occurrences)
- [ ] Replace with specific exceptions where possible
- [ ] Add logging to catch blocks
- [ ] Ensure graceful degradation

**Phase 4: Error Recovery (1h)**
- [ ] Add retry logic to transient failures
- [ ] Implement fallback strategies
- [ ] Document error handling in code

---

### Task 4.6: Sprint 4 Final Verification (Effort: 3h)

**Documentation Review:**
- [ ] Proofread all new documentation
- [ ] Check all links work
- [ ] Verify code examples
- [ ] Spell check

**Code Quality:**
- [ ] Run all quality tools
  ```bash
  poetry run black . --check
  poetry run isort . --check-only
  poetry run ruff check .
  poetry run mypy src/
  poetry run pylint src/
  poetry run bandit -r src/
  ```

- [ ] Verify all checks pass

**Testing:**
- [ ] Run full test suite: `poetry run pytest --cov=src --cov-report=html`
- [ ] Check coverage report
- [ ] Manual testing of key features

**Release Preparation:**
- [ ] Update version: `2.2.0` → `2.3.0`
- [ ] Final CHANGELOG.md update
  - Summarize all Sprint 4 work
  - Highlight production readiness
- [ ] Update README.md if needed

**Release:**
- [ ] Commit final changes
- [ ] Tag release: `git tag -a v2.3.0 -m "Version 2.3.0 - Production Ready"`
- [ ] Push: `git push && git push --tags`
- [ ] Create GitHub release with notes

**Celebration:**
- [ ] 🎉 Production-ready v2.3.0 released!
- [ ] Document lessons learned
- [ ] Plan next features

---

## 📊 Summary Checklist

### Sprint 1 (Week 1) - v2.0.1
- [ ] Security fixes (MD5, encoding)
- [ ] GUI module conflict resolved
- [ ] Modern API type errors fixed
- [ ] test_modern_api.py created (20+ tests)

### Sprint 2 (Weeks 2-3) - v2.1.0
- [ ] test_expectations.py (25+ tests)
- [ ] test_actionability.py (30+ tests)
- [ ] test_page_objects.py (35+ tests)
- [ ] test_data_driven.py (25+ tests)
- [ ] Framework coverage >70%

### Sprint 3 (Weeks 4-5) - v2.2.0
- [ ] gui_components type errors fixed
- [ ] Circular dependencies resolved
- [ ] Complex functions refactored
- [ ] Mypy errors reduced from 70+ to <10

### Sprint 4 (Week 6) - v2.3.0
- [ ] ARCHITECTURE.md created
- [ ] TESTING_GUIDE.md created
- [ ] CONTRIBUTING.md created
- [ ] Star imports replaced
- [ ] Error handling improved
- [ ] Production ready! 🚀

---

## 🎯 Tracking Progress

Use this document alongside `ANALYSIS_REPORT.md` to:
1. Track completion of each task
2. Estimate remaining effort
3. Identify blockers
4. Coordinate team work
5. Report progress to stakeholders

**Update Strategy:**
- Check off [ ] items as completed
- Note any deviations in comments
- Update effort estimates based on reality
- Add new tasks as discovered

**Success Metrics:**
- All checkboxes completed
- Version 2.3.0 released
- Health Score: 9.0/10+
- Type errors: <10
- Test coverage: >70%
- Security issues: 0 HIGH/MEDIUM

---

*This task breakdown is a living document. Update as you make progress!*
