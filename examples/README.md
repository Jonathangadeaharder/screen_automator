# Framework Examples

This directory contains examples demonstrating the new framework features added to screen_automator.

## What's New

Screen Automator has been enhanced with professional-grade framework features:

1. **Auto-Waiting** - Eliminate flaky tests caused by `time.sleep()`
2. **Expectations API** - Auto-retrying assertions that adapt to environment speed
3. **Page Object Model** - Maintainable, reusable UI abstractions
4. **Data-Driven Testing** - Multiply test coverage with external data files

## Running the Examples

### 1. Install Dependencies

```bash
poetry install --with dev
```

### 2. Create Example Data Files

```bash
python examples/framework_demo.py
```

This creates example CSV and JSON files in the `examples/` directory.

### 3. Review the Code

Open `framework_demo.py` to see complete examples of:
- Auto-waiting for elements
- Robust expectations
- Page object patterns
- Data-driven test loops

## Quick Examples

### Auto-Waiting (No more time.sleep!)

```python
from src.actionability import SmartAutomator

smart = SmartAutomator(automator)
smart.click_image("button.png")  # Auto-waits until button appears!
```

### Expectations (Auto-retrying assertions)

```python
from src.expectations import expect

# Waits up to 5 seconds for button to appear
expect(automator).to_have_image("button.png", timeout=5000)

# Waits for loading to disappear
expect(automator).not_to_have_image("loading.png")
```

### Page Object Model (Maintainable tests)

```python
from src.page_objects import BasePage, Element, image_locator

class CalculatorWindow(BasePage):
    def __init__(self, automator):
        super().__init__(automator)
        self.button_7 = Element(image_locator("calc_7.png"), automator)
        self.button_plus = Element(image_locator("calc_plus.png"), automator)

    def add_7_plus_number(self, num):
        self.button_7.click()
        self.button_plus.click()
        # ...

# Use in tests
calc = CalculatorWindow(automator)
calc.add_7_plus_number(3)
```

### Data-Driven Testing (Multiply test cases)

```python
from src.data_driven import DataProvider

# One loop, many test cases
for row in DataProvider("test_data/users.csv"):
    username = row['username']
    password = row['password']
    # Run test with this data
```

## Full Documentation

For complete documentation, see:

- **[FRAMEWORK_GUIDE.md](../FRAMEWORK_GUIDE.md)** - Comprehensive user guide
- **[IMPROVEMENT_BLUEPRINT_IMPLEMENTATION.md](../IMPROVEMENT_BLUEPRINT_IMPLEMENTATION.md)** - Implementation details

## Example Data Files

After running `framework_demo.py`, you'll have:

- `login_cases.csv` - Example CSV test data
- `config.json` - Example environment configuration

You can use these as templates for your own test data files.

## Next Steps

1. Read `FRAMEWORK_GUIDE.md` for detailed explanations
2. Review `framework_demo.py` for code examples
3. Try the features in your own automation scripts
4. Create page objects for your UI
5. Set up data-driven tests for your scenarios

## Support

For questions or issues:
- Check the [Framework Guide](../FRAMEWORK_GUIDE.md)
- Review the source code (all modules have detailed docstrings)
- Open an issue on GitHub

---

**Happy automating! 🚀**
