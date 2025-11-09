# Examples

Complete examples using the **modern Screen Automator API**.

## Modern API Usage

See `modern_api_usage.py` for comprehensive examples.

### Quick Start

```bash
# Install dependencies
poetry install --with dev

# Run examples
python examples/modern_api_usage.py
```

## Modern API (Recommended)

All examples use the modern API:

```python
from src.modern_api import create_framework

# Create framework instance
framework = create_framework(timeout=10000)

# Click with auto-waiting
framework.click_image("button.png")

# Robust expectations
framework.expect_image("success.png", timeout=5000)
framework.expect_no_image("loading.png")

# Wait for elements
location = framework.wait_for_image("dialog.png")

# Start monitoring
framework.start_monitoring()
```

## What's Included

The modern API includes all framework features:
- 🚀 **Auto-waiting** - No more `time.sleep()`
- ✅ **Expectations** - Auto-retry assertions
- 📦 **Page Objects** - Available via framework
- 📊 **Data-driven** - CSV/JSON/XML support
- 🔄 **Monitoring** - Rule-based automation

## Example Files

- `modern_api_usage.py` - Complete API examples (6 scenarios)
- `login_cases.csv` - Sample CSV test data
- `config.json` - Sample environment config

## Documentation

- [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - API reference
- [FRAMEWORK_GUIDE.md](../FRAMEWORK_GUIDE.md) - Complete guide
- [MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md) - Migration help

---

**Use the modern API for all new code!** 🚀
