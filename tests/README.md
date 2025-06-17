# Screen Automator Testing Documentation

This directory contains comprehensive automated tests for the Screen Automator project, designed to ensure all components work correctly without requiring manual intervention or system dependencies.

## Test Structure

### Test Files

1. **`test_comprehensive.py`** - Main comprehensive test suite with mocks
   - CLI functionality tests
   - Core component tests (ScreenAutomator, RuleManager, ActionExecutor, ImageDetector)
   - GUI tests (with graceful skipping on headless systems)
   - Integration tests
   - Error handling tests

2. **`test_basic.py`** (in project root) - Basic functionality tests
   - Real component integration tests
   - Manual verification tests

3. **`test_headless.py`** - Headless-specific tests (placeholder)
   - Tests that avoid GUI initialization completely

### Test Categories

#### CLI Tests (`TestCLIComprehensive`)
- Command help output
- Status command functionality  
- Rule management commands
- Error handling for invalid commands

#### Core Tests (`TestCoreComprehensive`)
- **ScreenAutomator**: Initialization, monitoring lifecycle, status reporting
- **RuleManager**: CRUD operations, rule validation, conflict detection
- **ActionExecutor**: Click, type, wait actions with mouse position restoration
- **ImageDetector**: Screen capture, template matching, confidence thresholds

#### GUI Tests (`TestGUIComprehensive`)
- Widget creation and functionality
- Event handling
- Integration with core components
- Graceful skipping on systems without GUI support

#### Integration Tests (`TestIntegration`)
- End-to-end rule creation and management
- Action sequence execution
- Component interaction verification

#### Error Handling Tests (`TestErrorHandling`)
- Invalid action parameters
- Nonexistent rule operations
- File system errors
- Network-related failures

## Running Tests

### Using the Test Runner

```bash
# Run all tests
python run_tests.py

# Run with coverage reporting
python run_tests.py --coverage

# Run only comprehensive tests
python run_tests.py --comprehensive-only

# Run with verbose output
python run_tests.py --verbose

# Install test dependencies
python run_tests.py --install-deps
```

### Direct pytest Usage

```bash
# Run comprehensive tests
pytest tests/test_comprehensive.py -v

# Run with coverage
pytest tests/test_comprehensive.py --cov=src --cov-report=html

# Run specific test class
pytest tests/test_comprehensive.py::TestCoreComprehensive -v

# Run tests matching pattern
pytest tests/test_comprehensive.py -k "rule_manager" -v
```

## Test Configuration

### pytest.ini
Configuration file for pytest with:
- Test discovery patterns
- Output formatting
- Coverage thresholds
- Test markers

### Mock Strategy

The tests use extensive mocking to:

1. **Avoid System Dependencies**
   - Mock `pyautogui` for mouse/keyboard actions
   - Mock `cv2` for image processing
   - Mock file system operations

2. **Control Test Environment**
   - Predictable return values
   - Isolated component testing
   - Consistent test conditions

3. **Test Error Conditions**
   - Simulated failures
   - Edge case handling
   - Exception propagation

### Mocked Components

- **`pyautogui`**: Mouse and keyboard automation
- **`cv2`**: Computer vision operations
- **`time.sleep`**: Wait operations
- **`tkinter`**: GUI components (with graceful fallback)
- **File I/O**: JSON rule storage
- **Network**: Future web-based features

## Test Fixtures

### Temporary Directories
Each test class uses isolated temporary directories for:
- Rule storage
- Image files
- Configuration files
- Log outputs

### Mock Objects
Standardized mock objects for:
- Rule instances with realistic attributes
- Action objects with proper parameters
- Status dictionaries with expected keys

## Coverage Goals

### Current Coverage Areas
- ✅ CLI command functionality
- ✅ Rule CRUD operations  
- ✅ Action execution
- ✅ Image detection basics
- ✅ Error handling
- ✅ Configuration management

### Target Coverage
- 70%+ overall code coverage
- 90%+ for critical paths
- 100% for CLI commands
- 85%+ for core components

## Windows-Specific Considerations

### Unicode Handling
- Tests avoid Unicode characters that cause encoding issues on Windows
- Fallback to ASCII alternatives for test output

### GUI Testing
- Tests gracefully skip when Tkinter/GUI components unavailable
- Headless environment detection
- Virtual display support (future)

### Path Handling
- Cross-platform path handling in tests
- Temporary directory cleanup
- File permission handling

## Continuous Integration

### Test Automation
- Automated test execution on code changes
- Coverage reporting
- Performance benchmarking
- Cross-platform testing (future)

### Quality Gates
- All tests must pass before merge
- Coverage thresholds enforced
- No new test failures allowed
- Performance regression detection

## Adding New Tests

### Test Naming Convention
```python
def test_[component]_[functionality]_[scenario](self):
    """Test [component] [functionality] [expected behavior]."""
```

### Test Structure
```python
def test_example(self):
    """Test example functionality."""
    # 1. Setup
    # 2. Execute
    # 3. Assert
    # 4. Cleanup (if needed)
```

### Mock Usage
```python
@patch('module.dependency')
def test_with_mock(self, mock_dependency):
    """Test with mocked dependency."""
    mock_dependency.return_value = expected_value
    # Test code
    mock_dependency.assert_called_once_with(expected_args)
```

## Troubleshooting

### Common Issues

1. **GUI Tests Failing**
   - Usually due to headless environment
   - Tests should skip gracefully
   - Check Tkinter installation

2. **Import Errors**
   - Verify Python path setup
   - Check test dependencies installed
   - Ensure project structure correct

3. **Mock Assertion Failures**
   - Verify mock call counts
   - Check parameter matching
   - Review mock setup

4. **File System Errors**
   - Check temporary directory permissions
   - Verify cleanup in teardown
   - Handle Windows file locking

### Debugging Tests

```bash
# Run specific test with debugging
pytest tests/test_comprehensive.py::TestClass::test_method -v -s

# Run with PDB on failure
pytest tests/test_comprehensive.py --pdb

# Run with coverage and show missing lines
pytest tests/test_comprehensive.py --cov=src --cov-report=term-missing
```

## Future Enhancements

### Planned Improvements
- Performance benchmarking tests
- Load testing for continuous monitoring
- Cross-platform CI/CD integration
- Visual regression testing
- API endpoint testing (future web features)
- Database integration tests (future)

### Test Infrastructure
- Docker-based test environments
- Automated screenshot comparison
- Test data management
- Parallel test execution
- Test result analytics 