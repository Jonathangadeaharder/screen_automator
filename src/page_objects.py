"""
Page Object Model (POM) base classes for maintainable automation.

The Page Object Model is an industry-standard design pattern that encapsulates
UI elements and interactions into reusable classes, dramatically reducing
maintenance costs when the UI changes.

Instead of scattered, brittle automation code:
    automator.click_image("save_button.png")
    automator.type_text("document.txt")

Create maintainable page objects:
    main_window = MainWindow(automator)
    main_window.save_document("document.txt")

When the UI changes, update only the page object, not every test script.

Based on the comprehensive improvement blueprint for screen_automator.
"""

from typing import Any, Dict, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum


class LocatorType(Enum):
    """Types of locators for finding elements."""
    IMAGE = "image"
    TEXT = "text"
    WINDOW_TITLE = "window_title"
    CONTROL_TYPE = "control_type"
    COORDINATES = "coordinates"


@dataclass
class Locator:
    """
    A locator defines how to find an element.

    This abstraction allows page objects to work with both image-based
    and property-based automation seamlessly.

    Examples:
        # Image-based locator
        save_button = Locator(type=LocatorType.IMAGE, value="save.png")

        # Property-based locator
        file_name = Locator(
            type=LocatorType.TEXT,
            value="File Name",
            control_type="Edit"
        )

        # Coordinate-based locator (fallback)
        menu_item = Locator(type=LocatorType.COORDINATES, value=(100, 200))
    """
    type: LocatorType
    value: Any
    control_type: Optional[str] = None
    timeout: int = 5000
    description: Optional[str] = None

    def __str__(self):
        desc = self.description or f"{self.type.value}='{self.value}'"
        return desc


class Element:
    """
    Represents a single UI element.

    This wraps both the locator and the automator, providing a unified
    interface for interacting with elements regardless of how they're found.
    """

    def __init__(
        self,
        locator: Locator,
        automator: Any,
        parent: Optional['Element'] = None
    ):
        """
        Initialize element.

        Args:
            locator: How to find this element
            automator: The automator instance to use
            parent: Optional parent element for scoped searches
        """
        self.locator = locator
        self.automator = automator
        self.parent = parent
        self._cached_location: Optional[Tuple[int, int]] = None

    def find(self, timeout: Optional[int] = None) -> Tuple[int, int]:
        """
        Find this element and return its location.

        Args:
            timeout: Override default timeout

        Returns:
            Tuple of (x, y) coordinates

        Raises:
            TimeoutError: If element not found within timeout
        """
        timeout_ms = timeout if timeout is not None else self.locator.timeout

        if self.locator.type == LocatorType.IMAGE:
            # Use image-based finding
            if hasattr(self.automator, 'find_image'):
                location = self.automator.find_image(self.locator.value)
                if location:
                    self._cached_location = location
                    return location
                raise TimeoutError(f"Image '{self.locator.value}' not found")

        elif self.locator.type == LocatorType.COORDINATES:
            return self.locator.value

        elif self.locator.type == LocatorType.TEXT:
            # Property-based finding would go here
            # This would integrate with pywinauto or similar
            raise NotImplementedError("Text-based locators require property automation")

        raise ValueError(f"Unknown locator type: {self.locator.type}")

    def click(self, timeout: Optional[int] = None):
        """
        Click this element.

        Args:
            timeout: Override default timeout
        """
        location = self.find(timeout)

        if hasattr(self.automator, 'click_at'):
            self.automator.click_at(location[0], location[1])
        else:
            # Fallback to pyautogui
            import pyautogui
            pyautogui.click(location[0], location[1])

    def type_text(self, text: str, timeout: Optional[int] = None):
        """
        Type text into this element.

        Args:
            text: Text to type
            timeout: Override default timeout
        """
        location = self.find(timeout)

        # Click to focus first
        self.click(timeout)

        if hasattr(self.automator, 'type_text'):
            self.automator.type_text(text)
        else:
            # Fallback to pyautogui
            import pyautogui
            pyautogui.typewrite(text)

    def is_visible(self, timeout: int = 1000) -> bool:
        """
        Check if element is currently visible.

        Args:
            timeout: How long to wait for element (short by default)

        Returns:
            True if visible, False otherwise
        """
        try:
            self.find(timeout)
            return True
        except (TimeoutError, Exception):
            return False

    def wait_for_visible(self, timeout: Optional[int] = None):
        """
        Wait for element to become visible.

        Args:
            timeout: Override default timeout

        Raises:
            TimeoutError: If element doesn't appear within timeout
        """
        self.find(timeout)

    def wait_for_hidden(self, timeout: Optional[int] = None):
        """
        Wait for element to become hidden.

        Args:
            timeout: Override default timeout

        Raises:
            TimeoutError: If element still visible after timeout
        """
        import time
        timeout_ms = timeout if timeout is not None else self.locator.timeout
        start_time = time.time()

        while (time.time() - start_time) * 1000 < timeout_ms:
            if not self.is_visible(timeout=100):
                return
            time.sleep(0.1)

        raise TimeoutError(
            f"Element {self.locator} still visible after {timeout_ms}ms"
        )


class BasePage:
    """
    Base class for all Page Objects.

    This provides common functionality and enforces the pattern that each
    page/window/dialog in your application should be represented by a class.

    Example:
        class CalculatorWindow(BasePage):
            def __init__(self, automator):
                super().__init__(automator)

                # Define locators
                self.button_7 = Element(
                    Locator(LocatorType.IMAGE, "calc_7.png"),
                    automator
                )
                self.button_plus = Element(
                    Locator(LocatorType.IMAGE, "calc_plus.png"),
                    automator
                )
                self.button_equals = Element(
                    Locator(LocatorType.IMAGE, "calc_equals.png"),
                    automator
                )

            def add_numbers(self, a: int, b: int):
                # High-level business logic
                self.button_7.click()
                self.button_plus.click()
                self.button_7.click()
                self.button_equals.click()

        # Usage in test
        calc = CalculatorWindow(automator)
        calc.add_numbers(7, 7)
    """

    def __init__(self, automator: Any):
        """
        Initialize page object.

        Args:
            automator: The automator instance
        """
        self.automator = automator
        self._elements: Dict[str, Element] = {}

    def get_element(self, name: str) -> Element:
        """
        Get an element by name.

        Args:
            name: Name of the element attribute

        Returns:
            The Element instance

        Raises:
            AttributeError: If element not found
        """
        if name in self._elements:
            return self._elements[name]

        if hasattr(self, name):
            elem = getattr(self, name)
            if isinstance(elem, Element):
                self._elements[name] = elem
                return elem

        raise AttributeError(f"Element '{name}' not found in {self.__class__.__name__}")

    def wait_for_load(self, timeout: int = 10000):
        """
        Wait for this page to be fully loaded.

        Override this in subclasses to define page-specific load conditions.

        Args:
            timeout: Maximum time to wait in milliseconds

        Example:
            class LoginPage(BasePage):
                def wait_for_load(self, timeout=10000):
                    self.username_field.wait_for_visible(timeout)
                    self.password_field.wait_for_visible(timeout)
                    self.login_button.wait_for_visible(timeout)
        """
        pass


class BaseDialog(BasePage):
    """
    Base class for dialog/modal page objects.

    Dialogs typically have additional behaviors like checking if they're open,
    waiting for them to close, etc.

    Example:
        class SaveDialog(BaseDialog):
            def __init__(self, automator):
                super().__init__(automator)

                self.filename_field = Element(
                    Locator(LocatorType.TEXT, "File name", control_type="Edit"),
                    automator
                )
                self.save_button = Element(
                    Locator(LocatorType.IMAGE, "save_button.png"),
                    automator
                )
                self.cancel_button = Element(
                    Locator(LocatorType.IMAGE, "cancel_button.png"),
                    automator
                )

            def save_as(self, filename: str):
                self.wait_for_open()
                self.filename_field.type_text(filename)
                self.save_button.click()
                self.wait_for_close()
    """

    def __init__(self, automator: Any, title_locator: Optional[Locator] = None):
        """
        Initialize dialog.

        Args:
            automator: The automator instance
            title_locator: Locator for dialog title (to check if open)
        """
        super().__init__(automator)
        self.title_locator = title_locator

    def is_open(self, timeout: int = 1000) -> bool:
        """
        Check if dialog is currently open.

        Args:
            timeout: Short timeout for check

        Returns:
            True if dialog is open
        """
        if self.title_locator:
            elem = Element(self.title_locator, self.automator)
            return elem.is_visible(timeout)
        return False

    def wait_for_open(self, timeout: int = 10000):
        """
        Wait for dialog to open.

        Args:
            timeout: Maximum wait time

        Raises:
            TimeoutError: If dialog doesn't open in time
        """
        if self.title_locator:
            elem = Element(self.title_locator, self.automator)
            elem.wait_for_visible(timeout)
        else:
            # If no title locator, just call wait_for_load
            self.wait_for_load(timeout)

    def wait_for_close(self, timeout: int = 10000):
        """
        Wait for dialog to close.

        Args:
            timeout: Maximum wait time

        Raises:
            TimeoutError: If dialog still open after timeout
        """
        if self.title_locator:
            elem = Element(self.title_locator, self.automator)
            elem.wait_for_hidden(timeout)


class WindowPage(BasePage):
    """
    Page object for application windows with window management capabilities.

    Example:
        class NotepadWindow(WindowPage):
            def __init__(self, automator, window_manager):
                super().__init__(
                    automator,
                    window_manager,
                    window_title="Notepad"
                )

                self.text_area = Element(
                    Locator(LocatorType.IMAGE, "notepad_text.png"),
                    automator
                )

            def type_text(self, text: str):
                self.activate()  # Bring window to front
                self.text_area.type_text(text)
    """

    def __init__(
        self,
        automator: Any,
        window_manager: Any,
        window_title: Optional[str] = None
    ):
        """
        Initialize window page.

        Args:
            automator: The automator instance
            window_manager: Window manager for window operations
            window_title: Title of this window
        """
        super().__init__(automator)
        self.window_manager = window_manager
        self.window_title = window_title

    def activate(self):
        """Bring this window to the foreground."""
        if self.window_manager and self.window_title:
            # This would use window_manager.activate_window(self.window_title)
            pass

    def close(self):
        """Close this window."""
        if self.window_manager and self.window_title:
            # This would use window_manager.close_window(self.window_title)
            pass

    def is_active(self) -> bool:
        """Check if this window is currently active."""
        if self.window_manager and self.window_title:
            # This would check if window is active
            pass
        return False


# Factory function for creating locators easily
def locator(
    type: Union[str, LocatorType],
    value: Any,
    **kwargs
) -> Locator:
    """
    Factory function for creating locators with less boilerplate.

    Args:
        type: Locator type (string or enum)
        value: Locator value
        **kwargs: Additional locator parameters

    Returns:
        Locator instance

    Examples:
        save_btn = locator("image", "save.png", description="Save button")
        file_field = locator("text", "File name", control_type="Edit")
    """
    if isinstance(type, str):
        type = LocatorType(type)

    return Locator(type=type, value=value, **kwargs)


# Convenience functions for common locator types
def image_locator(path: str, **kwargs) -> Locator:
    """Create image-based locator."""
    return Locator(type=LocatorType.IMAGE, value=path, **kwargs)


def text_locator(text: str, control_type: Optional[str] = None, **kwargs) -> Locator:
    """Create text-based locator."""
    return Locator(
        type=LocatorType.TEXT,
        value=text,
        control_type=control_type,
        **kwargs
    )


def coordinate_locator(x: int, y: int, **kwargs) -> Locator:
    """Create coordinate-based locator."""
    return Locator(type=LocatorType.COORDINATES, value=(x, y), **kwargs)
