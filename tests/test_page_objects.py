"""
Essential tests for the page_objects module.

Tests Locator, Element, and BasePage classes.
"""

import sys
import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path

# Mock display-dependent modules
sys.modules["pynput"] = MagicMock()
sys.modules["pynput.mouse"] = MagicMock()
sys.modules["pynput.keyboard"] = MagicMock()
sys.modules["pyautogui"] = MagicMock()
sys.modules["screeninfo"] = MagicMock()

from src.page_objects import (
    LocatorType,
    Locator,
    Element,
    BasePage,
    locator,
    image_locator,
    text_locator,
    coordinate_locator,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_automator():
    """Create a mock automator."""
    automator = Mock(spec=['find_image', 'click_image', 'type_text'])
    automator.find_image = Mock(return_value=(100, 200, 50, 50))
    automator.click_image = Mock()
    automator.type_text = Mock()
    return automator


# ============================================================================
# LocatorType Tests
# ============================================================================


def test_locator_type_enum_values():
    """Test LocatorType enum has correct values."""
    assert LocatorType.IMAGE.value == "image"
    assert LocatorType.TEXT.value == "text"
    assert LocatorType.WINDOW_TITLE.value == "window_title"
    assert LocatorType.CONTROL_TYPE.value == "control_type"
    assert LocatorType.COORDINATES.value == "coordinates"


# ============================================================================
# Locator Tests
# ============================================================================


def test_locator_creation_with_image():
    """Test creating an image-based locator."""
    loc = Locator(type=LocatorType.IMAGE, value="button.png")

    assert loc.type == LocatorType.IMAGE
    assert loc.value == "button.png"
    assert loc.timeout == 5000


def test_locator_creation_with_text():
    """Test creating a text-based locator."""
    loc = Locator(
        type=LocatorType.TEXT,
        value="Submit",
        control_type="Button"
    )

    assert loc.type == LocatorType.TEXT
    assert loc.value == "Submit"
    assert loc.control_type == "Button"


def test_locator_custom_timeout():
    """Test locator with custom timeout."""
    loc = Locator(type=LocatorType.IMAGE, value="slow.png", timeout=10000)

    assert loc.timeout == 10000


def test_locator_with_description():
    """Test locator with custom description."""
    loc = Locator(
        type=LocatorType.IMAGE,
        value="icon.png",
        description="Save button icon"
    )

    assert loc.description == "Save button icon"
    assert "Save button icon" in str(loc)


def test_locator_str_without_description():
    """Test locator string representation without description."""
    loc = Locator(type=LocatorType.IMAGE, value="test.png")

    loc_str = str(loc)
    assert "image" in loc_str
    assert "test.png" in loc_str


# ============================================================================
# Element Tests
# ============================================================================


def test_element_initialization(mock_automator):
    """Test Element initializes correctly."""
    loc = Locator(type=LocatorType.IMAGE, value="button.png")
    element = Element(loc, mock_automator)

    assert element.locator == loc
    assert element.automator == mock_automator
    assert element.parent is None


def test_element_with_parent(mock_automator):
    """Test Element with parent element."""
    parent_loc = Locator(type=LocatorType.IMAGE, value="dialog.png")
    parent = Element(parent_loc, mock_automator)

    child_loc = Locator(type=LocatorType.IMAGE, value="button.png")
    child = Element(child_loc, mock_automator, parent=parent)

    assert child.parent == parent


def test_element_find_with_image_locator(mock_automator):
    """Test Element.find() with image locator."""
    loc = Locator(type=LocatorType.IMAGE, value="button.png")
    element = Element(loc, mock_automator)

    result = element.find()

    # find() returns (x, y) extracted from (x, y, width, height)
    assert result == (100, 200, 50, 50)
    mock_automator.find_image.assert_called_once_with("button.png")


def test_element_find_raises_when_not_found(mock_automator):
    """Test Element.find() raises TimeoutError when element not found."""
    mock_automator.find_image = Mock(return_value=None)
    loc = Locator(type=LocatorType.IMAGE, value="missing.png")
    element = Element(loc, mock_automator)

    with pytest.raises(TimeoutError):
        element.find()


def test_element_click(mock_automator):
    """Test Element.click() calls find and clicks."""
    # Mock pyautogui since Element uses it as fallback
    import sys
    mock_pg = MagicMock()
    sys.modules['pyautogui'].click = mock_pg

    loc = Locator(type=LocatorType.IMAGE, value="button.png")
    element = Element(loc, mock_automator)

    element.click()

    mock_automator.find_image.assert_called()


def test_element_type_text(mock_automator):
    """Test Element.type_text() types text."""
    # Mock pyautogui
    import sys
    sys.modules['pyautogui'].typewrite = MagicMock()

    loc = Locator(type=LocatorType.IMAGE, value="textfield.png")
    element = Element(loc, mock_automator)

    element.type_text("Hello World")

    mock_automator.find_image.assert_called()


def test_element_is_visible_true(mock_automator):
    """Test Element.is_visible() returns True when found."""
    loc = Locator(type=LocatorType.IMAGE, value="button.png")
    element = Element(loc, mock_automator)

    assert element.is_visible() is True


def test_element_is_visible_false(mock_automator):
    """Test Element.is_visible() returns False when not found."""
    mock_automator.find_image = Mock(return_value=None)
    loc = Locator(type=LocatorType.IMAGE, value="button.png")
    element = Element(loc, mock_automator)

    assert element.is_visible() is False


# ============================================================================
# BasePage Tests
# ============================================================================


def test_base_page_initialization(mock_automator):
    """Test BasePage initializes correctly."""
    page = BasePage(mock_automator)

    assert page.automator == mock_automator
    assert hasattr(page, '_elements')
    assert isinstance(page._elements, dict)


def test_base_page_stores_automator(mock_automator):
    """Test BasePage stores automator reference."""
    page = BasePage(mock_automator)

    assert page.automator == mock_automator


def test_base_page_get_element_by_name(mock_automator):
    """Test BasePage.get_element() retrieves elements."""
    page = BasePage(mock_automator)

    # Create an element attribute
    page.save_button = Element(
        Locator(type=LocatorType.IMAGE, value="save.png"),
        mock_automator
    )

    element = page.get_element('save_button')

    assert isinstance(element, Element)
    assert element == page.save_button


def test_base_page_get_nonexistent_element(mock_automator):
    """Test BasePage.get_element() raises for nonexistent element."""
    page = BasePage(mock_automator)

    with pytest.raises(AttributeError):
        page.get_element('nonexistent')


def test_base_page_wait_for_load(mock_automator):
    """Test BasePage.wait_for_load() method exists."""
    page = BasePage(mock_automator)

    # Should not raise - base implementation does nothing
    page.wait_for_load()


# ============================================================================
# Helper Function Tests
# ============================================================================


def test_locator_helper_function():
    """Test locator() helper function."""
    loc = locator("image", "button.png", timeout=8000)

    assert loc.type == LocatorType.IMAGE
    assert loc.value == "button.png"
    assert loc.timeout == 8000


def test_locator_helper_with_enum():
    """Test locator() helper with enum type."""
    loc = locator(LocatorType.TEXT, "Submit")

    assert loc.type == LocatorType.TEXT
    assert loc.value == "Submit"


def test_image_locator_helper():
    """Test image_locator() convenience function."""
    loc = image_locator("icon.png", timeout=7000)

    assert loc.type == LocatorType.IMAGE
    assert loc.value == "icon.png"
    assert loc.timeout == 7000


def test_text_locator_helper():
    """Test text_locator() convenience function."""
    loc = text_locator("Click Me", control_type="Button")

    assert loc.type == LocatorType.TEXT
    assert loc.value == "Click Me"
    assert loc.control_type == "Button"


def test_coordinate_locator_helper():
    """Test coordinate_locator() convenience function."""
    loc = coordinate_locator(150, 250)

    assert loc.type == LocatorType.COORDINATES
    assert loc.value == (150, 250)


def test_coordinate_locator_with_description():
    """Test coordinate_locator() with description."""
    loc = coordinate_locator(100, 200, description="Menu item")

    assert loc.description == "Menu item"
    assert "Menu item" in str(loc)


# ============================================================================
# Integration Tests
# ============================================================================


def test_page_object_workflow(mock_automator):
    """Test complete page object workflow."""
    # Create page with elements
    page = BasePage(mock_automator)

    # Add elements as attributes
    page.save_button = Element(image_locator("save_button.png"), mock_automator)
    page.name_field = Element(image_locator("name_field.png"), mock_automator)

    # Interact with elements - check they were found
    button = page.get_element('save_button')
    assert button.is_visible()

    field = page.get_element('name_field')
    assert field.is_visible()


def test_element_operations_on_page(mock_automator):
    """Test element operations through page object."""
    page = BasePage(mock_automator)

    # Add elements
    page.button1 = Element(image_locator("button1.png"), mock_automator)
    page.button2 = Element(image_locator("button2.png"), mock_automator)

    # Get elements and check visibility
    elem1 = page.get_element('button1')
    elem2 = page.get_element('button2')

    assert elem1.is_visible()
    assert elem2.is_visible()


def test_multiple_locator_types(mock_automator):
    """Test page with multiple locator types."""
    # Different locator types
    img_loc = image_locator("icon.png")
    txt_loc = text_locator("Submit")
    coord_loc = coordinate_locator(100, 200)

    # All should create valid elements
    elem1 = Element(img_loc, mock_automator)
    elem2 = Element(txt_loc, mock_automator)
    elem3 = Element(coord_loc, mock_automator)

    assert elem1.locator.type == LocatorType.IMAGE
    assert elem2.locator.type == LocatorType.TEXT
    assert elem3.locator.type == LocatorType.COORDINATES
