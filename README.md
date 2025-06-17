# Screen Automator

A Python application for automating screen interactions based on image detection. Create rules that trigger actions when specific images appear on your screen.

## Features

- **Image-based triggers**: Detect images on screen using OpenCV template matching
- **Screen idle detection**: Trigger actions when screen is unchanged for a specified time period
- **Action sequences**: Chain multiple actions including clicks, keystrokes, and waits
- **CLI interface**: Command-line interface for testing and managing rules
- **GUI interface**: User-friendly graphical interface with visual rule creation
- **Screen capture**: Select regions of screen as trigger images
- **Click recording**: Record mouse clicks visually
- **Keystroke recording**: Record keyboard input
- **Rule management**: Save, load, enable/disable rules

## Installation

1. Clone or download the project
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### CLI Interface

Run the CLI:
```bash
python cli.py --help
```

#### Basic Commands

Start monitoring:
```bash
python cli.py start
```

Create a new image-based rule:
```bash
python cli.py rule create --name "My Rule" --image "/path/to/trigger.png"
```

Create a screen idle rule:
```bash
python cli.py rule create --name "Idle Rule" --condition screen_unchanged --timeout 5.0
```

List all rules:
```bash
python cli.py rule list
```

Test a rule:
```bash
python cli.py rule test "My Rule"
```

#### Rule Management

- `python cli.py rule list` - List all rules
- `python cli.py rule create` - Create new rule interactively
- `python cli.py rule delete <rule_id>` - Delete a rule
- `python cli.py rule enable <rule_id>` - Enable a rule
- `python cli.py rule disable <rule_id>` - Disable a rule
- `python cli.py rule test <rule_id>` - Test a rule
- `python cli.py rule force <rule_id>` - Fire up rule (execute immediately without checking conditions)

### GUI Interface

Run the GUI:
```bash
python gui.py
```

#### GUI Features

1. **Rules Tab**: Manage existing rules
   - View all rules with status
   - Edit, delete, test rules
   - Enable/disable rules
   - Fire up rules (execute immediately without checking conditions)

2. **Rule Editor Tab**: Create and edit rules
   - Set rule name and description
   - Select trigger image from file or capture screen region
   - Build action sequences:
     - Record clicks visually
     - Record keystrokes
     - Add wait periods
     - Add manual actions
   - Reorder actions with drag and drop

3. **Monitoring Tab**: Control automation
   - Start/stop monitoring
   - View activity log
   - Configure check interval

## Project Structure

```
screen_automator/
├── src/
│   ├── __init__.py
│   ├── image_detector.py      # Image detection and matching
│   ├── action_executor.py     # Action execution system
│   ├── rule_manager.py        # Rule storage and management
│   ├── automator.py          # Main automation engine
│   └── screen_selector.py    # GUI utilities for screen interaction
├── data/
│   ├── images/               # Trigger images
│   └── rules/                # Rule definitions (JSON)
├── tests/                    # Test files
├── cli.py                    # Command-line interface
├── gui.py                    # Graphical interface
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## Action Types

- **Click**: Single left mouse click at coordinates
- **Double Click**: Double left mouse click
- **Right Click**: Single right mouse click
- **Type Text**: Simulate keyboard typing
- **Key Press**: Press specific keys (e.g., Enter, Tab)
- **Key Combination**: Press multiple keys simultaneously (e.g., Ctrl+C)
- **Wait**: Pause execution for specified duration
- **Scroll**: Mouse wheel scrolling

## Configuration

### Check Interval
Set how often to check for trigger images (default: 10 seconds):
```bash
python cli.py config --interval 0.5
```

### Action Limit
Set maximum number of actions before auto-stopping (safety feature):
```bash
python cli.py config --max-actions 100  # Stop after 100 actions
python cli.py config --max-actions 0    # Disable limit (default)
```

Reset action counter:
```bash
python cli.py reset-counter
```

### Image Matching Confidence
Modify `confidence_threshold` in `ImageDetector` class (default: 0.8)

## Example Workflow

1. **Create a rule**:
   - Open GUI: `python gui.py`
   - Go to "Rule Editor" tab
   - Enter rule name: "Auto Login"
   - Capture screen region showing login button
   - Record clicks on username field, password field, login button
   - Record typing username and password
   - Save rule

2. **Test the rule**:
   - Go to "Rules" tab
   - Select your rule and click "Test Rule"
   - Verify it works as expected

3. **Start monitoring**:
   - Go to "Monitoring" tab
   - Click "Start Monitoring"
   - The rule will trigger automatically when the login screen appears

## Testing

Run unit tests with pytest:

```bash
pip install -r requirements-dev.txt
pytest
```

Continuous integration suggested: GitHub Actions running tests on push.

## Troubleshooting

### Common Issues

1. **Image not detected**:
   - Check image quality and contrast
   - Adjust confidence threshold
   - Ensure image is visible and not obscured

2. **Actions not working**:
   - Verify coordinates are correct
   - Check if target application has focus
   - Add delays between actions if needed

3. **Permission errors**:
   - Run as administrator on Windows
   - Grant accessibility permissions on macOS

### Debug Mode

Enable debug output by modifying the confidence threshold or adding print statements in the detector.

## Safety Features

- **Action Limit**: Set maximum number of actions before auto-stopping to prevent runaway automation
- **Failsafe**: Move mouse to top-left corner to stop execution
- **Error handling**: Graceful handling of missing images or failed actions
- **Manual override**: Stop monitoring at any time

## Dependencies

- `opencv-python`: Image processing and template matching
- `pillow`: Image handling
- `pyautogui`: Screen capture and automation
- `click`: CLI framework
- `numpy`: Numerical operations
- `pynput`: Input recording

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request