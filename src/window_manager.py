import platform
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Windows-specific imports
if platform.system() == "Windows":
    try:
        import psutil
        import win32con
        import win32gui
        import win32process

        HAS_WIN32 = True
    except ImportError:
        HAS_WIN32 = False
else:
    HAS_WIN32 = False


@dataclass
class WindowInfo:
    """Information about a window"""

    handle: int  # Window handle/ID
    title: str
    process_name: str
    process_id: int
    x: int
    y: int
    width: int
    height: int
    is_visible: bool
    is_minimized: bool
    class_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "handle": self.handle,
            "title": self.title,
            "process_name": self.process_name,
            "process_id": self.process_id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "is_visible": self.is_visible,
            "is_minimized": self.is_minimized,
            "class_name": self.class_name,
        }


class WindowManager:
    """Manages window enumeration, selection, and context switching"""

    def __init__(self):
        self.system = platform.system()
        self._current_active_window = None
        self._original_active_window = None

    def get_running_windows(self, include_minimized: bool = True) -> List[WindowInfo]:
        """Get list of all running windows"""
        if self.system == "Windows" and HAS_WIN32:
            return self._get_windows_windows(include_minimized)
        elif self.system == "Linux":
            return self._get_linux_windows(include_minimized)
        elif self.system == "Darwin":  # macOS
            return self._get_macos_windows(include_minimized)
        else:
            print(f"Window management not supported on {self.system}")
            return []

    def _get_windows_windows(self, include_minimized: bool) -> List[WindowInfo]:
        """Get windows on Windows OS using win32gui"""
        windows = []

        def enum_windows_callback(hwnd, windows_list):
            if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:  # Only include windows with titles
                    try:
                        # Get window rectangle
                        rect = win32gui.GetWindowRect(hwnd)
                        x, y, right, bottom = rect
                        width = right - x
                        height = bottom - y

                        # Get process info
                        _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                        process_name = ""
                        try:
                            process = psutil.Process(process_id)
                            process_name = process.name()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            process_name = "Unknown"

                        # Check if minimized
                        is_minimized = win32gui.IsIconic(hwnd)

                        # Get class name
                        class_name = win32gui.GetClassName(hwnd)

                        if include_minimized or not is_minimized:
                            window_info = WindowInfo(
                                handle=hwnd,
                                title=title,
                                process_name=process_name,
                                process_id=process_id,
                                x=x,
                                y=y,
                                width=width,
                                height=height,
                                is_visible=True,
                                is_minimized=is_minimized,
                                class_name=class_name,
                            )
                            windows_list.append(window_info)
                    except Exception as e:
                        print(f"Error getting window info for {title}: {e}")
            return True

        try:
            win32gui.EnumWindows(enum_windows_callback, windows)
        except Exception as e:
            print(f"Error enumerating windows: {e}")

        return windows

    def _get_linux_windows(self, include_minimized: bool) -> List[WindowInfo]:
        """Get windows on Linux using wmctrl"""
        windows = []
        try:
            # Use wmctrl to get window list
            result = subprocess.run(["wmctrl", "-lG"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line:
                        parts = line.split(None, 7)  # Split into at most 8 parts
                        if len(parts) >= 8:
                            window_id = int(parts[0], 16)  # Hex to int
                            desktop = parts[1]
                            x = int(parts[2])
                            y = int(parts[3])
                            width = int(parts[4])
                            height = int(parts[5])
                            class_name = parts[6]
                            title = parts[7] if len(parts) > 7 else ""

                            # Try to get process info
                            process_name = "Unknown"
                            process_id = 0
                            try:
                                pid_result = subprocess.run(
                                    ["xprop", "-id", hex(window_id), "_NET_WM_PID"],
                                    capture_output=True,
                                    text=True,
                                    timeout=2,
                                )
                                if pid_result.returncode == 0 and "=" in pid_result.stdout:
                                    process_id = int(pid_result.stdout.split("=")[1].strip())
                                    process = psutil.Process(process_id)
                                    process_name = process.name()
                            except (
                                subprocess.TimeoutExpired,
                                psutil.NoSuchProcess,
                                psutil.AccessDenied,
                                ValueError,
                            ):
                                pass

                            window_info = WindowInfo(
                                handle=window_id,
                                title=title,
                                process_name=process_name,
                                process_id=process_id,
                                x=x,
                                y=y,
                                width=width,
                                height=height,
                                is_visible=True,
                                is_minimized=False,  # wmctrl doesn't easily show minimized state
                                class_name=class_name,
                            )
                            windows.append(window_info)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"Error getting Linux windows (wmctrl required): {e}")

        return windows

    def _get_macos_windows(self, include_minimized: bool) -> List[WindowInfo]:
        """Get windows on macOS using AppleScript"""
        windows = []
        try:
            # Use AppleScript to get window information
            script = """
            tell application "System Events"
                set windowList to {}
                repeat with proc in (every process whose background only is false)
                    repeat with win in (every window of proc)
                        try
                            set windowInfo to {name of win, name of proc, position of win, size of win}
                            set end of windowList to windowInfo
                        end try
                    end repeat
                end repeat
                return windowList
            end tell
            """

            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                # Parse the AppleScript output (this is simplified)
                # Real implementation would need more robust parsing
                for i, line in enumerate(result.stdout.strip().split("\n")):
                    if line:
                        window_info = WindowInfo(
                            handle=i,  # Use index as handle
                            title=line.strip(),
                            process_name="Unknown",
                            process_id=0,
                            x=0,
                            y=0,
                            width=0,
                            height=0,
                            is_visible=True,
                            is_minimized=False,
                        )
                        windows.append(window_info)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"Error getting macOS windows: {e}")

        return windows

    def get_active_window(self) -> Optional[WindowInfo]:
        """Get the currently active window"""
        if self.system == "Windows" and HAS_WIN32:
            return self._get_active_window_windows()
        elif self.system == "Linux":
            return self._get_active_window_linux()
        elif self.system == "Darwin":
            return self._get_active_window_macos()
        return None

    def _get_active_window_windows(self) -> Optional[WindowInfo]:
        """Get active window on Windows"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                windows = self._get_windows_windows(include_minimized=False)
                for window in windows:
                    if window.handle == hwnd:
                        return window
        except Exception as e:
            print(f"Error getting active window: {e}")
        return None

    def _get_active_window_linux(self) -> Optional[WindowInfo]:
        """Get active window on Linux"""
        try:
            result = subprocess.run(
                ["xprop", "-root", "_NET_ACTIVE_WINDOW"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and "window id" in result.stdout:
                window_id_str = result.stdout.split("window id # ")[1].split()[0]
                window_id = int(window_id_str, 16)

                windows = self._get_linux_windows(include_minimized=False)
                for window in windows:
                    if window.handle == window_id:
                        return window
        except Exception as e:
            print(f"Error getting active window on Linux: {e}")
        return None

    def _get_active_window_macos(self) -> Optional[WindowInfo]:
        """Get active window on macOS"""
        try:
            script = """
            tell application "System Events"
                set frontApp to first application process whose frontmost is true
                set frontWindow to first window of frontApp
                return {name of frontWindow, name of frontApp}
            end tell
            """
            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(", ")
                if len(parts) >= 2:
                    return WindowInfo(
                        handle=0,
                        title=parts[0],
                        process_name=parts[1],
                        process_id=0,
                        x=0,
                        y=0,
                        width=0,
                        height=0,
                        is_visible=True,
                        is_minimized=False,
                    )
        except Exception as e:
            print(f"Error getting active window on macOS: {e}")
        return None

    def switch_to_window(self, window_info: WindowInfo) -> bool:
        """Switch to the specified window"""
        if self.system == "Windows" and HAS_WIN32:
            return self._switch_to_window_windows(window_info)
        elif self.system == "Linux":
            return self._switch_to_window_linux(window_info)
        elif self.system == "Darwin":
            return self._switch_to_window_macos(window_info)
        return False

    def _switch_to_window_windows(self, window_info: WindowInfo) -> bool:
        """Switch to window on Windows"""
        try:
            hwnd = window_info.handle

            # Store original active window if not already stored
            if self._original_active_window is None:
                self._original_active_window = self.get_active_window()

            # If window is minimized, restore it
            if window_info.is_minimized:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.2)  # Give time for window to restore

            # Bring window to foreground
            win32gui.SetForegroundWindow(hwnd)
            win32gui.BringWindowToTop(hwnd)

            # Update current active window
            self._current_active_window = window_info

            # Give time for window to become active
            time.sleep(0.3)
            return True
        except Exception as e:
            print(f"Error switching to window on Windows: {e}")
            return False

    def _switch_to_window_linux(self, window_info: WindowInfo) -> bool:
        """Switch to window on Linux"""
        try:
            # Store original active window if not already stored
            if self._original_active_window is None:
                self._original_active_window = self.get_active_window()

            window_id = hex(window_info.handle)
            result = subprocess.run(
                ["wmctrl", "-i", "-a", window_id], capture_output=True, text=True, timeout=5
            )

            self._current_active_window = window_info
            time.sleep(0.3)
            return result.returncode == 0
        except Exception as e:
            print(f"Error switching to window on Linux: {e}")
            return False

    def _switch_to_window_macos(self, window_info: WindowInfo) -> bool:
        """Switch to window on macOS"""
        try:
            # Store original active window if not already stored
            if self._original_active_window is None:
                self._original_active_window = self.get_active_window()

            script = f"""
            tell application "{window_info.process_name}"
                activate
                set index of window "{window_info.title}" to 1
            end tell
            """
            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=5
            )

            self._current_active_window = window_info
            time.sleep(0.3)
            return result.returncode == 0
        except Exception as e:
            print(f"Error switching to window on macOS: {e}")
            return False

    def restore_original_window(self) -> bool:
        """Restore the original active window"""
        if self._original_active_window:
            success = self.switch_to_window(self._original_active_window)
            if success:
                self._current_active_window = self._original_active_window
                self._original_active_window = None
            return success
        return True

    def find_window_by_title(self, title: str, exact_match: bool = False) -> Optional[WindowInfo]:
        """Find a window by its title"""
        windows = self.get_running_windows()
        for window in windows:
            if exact_match:
                if window.title == title:
                    return window
            else:
                if title.lower() in window.title.lower():
                    return window
        return None

    def find_window_by_class(self, class_name: str) -> Optional[WindowInfo]:
        """Find a window by its class name (more reliable than title)"""
        windows = self.get_running_windows()
        for window in windows:
            if class_name.lower() in window.class_name.lower():
                return window
        return None

    def find_windows_by_process(self, process_name: str) -> List[WindowInfo]:
        """Find windows by process name"""
        windows = self.get_running_windows()
        return [w for w in windows if process_name.lower() in w.process_name.lower()]

    def get_window_screenshot(self, window_info: WindowInfo) -> Optional[Any]:
        """Get a screenshot of a specific window"""
        if self.system == "Windows" and HAS_WIN32:
            # Try the Windows-specific approach first
            screenshot = self._get_window_screenshot_windows(window_info)
            if screenshot:
                return screenshot

            print(
                f"Windows-specific capture failed for '{window_info.title}', trying fallback method..."
            )
            # Fallback to region-based screenshot
            screenshot = self._get_window_screenshot_fallback(window_info)
            if screenshot:
                return screenshot

            print(
                f"Fallback capture also failed for '{window_info.title}', trying screen capture..."
            )
            # Last resort: capture full screen for hash comparison
            return self._get_fullscreen_screenshot_fallback()
        else:
            # For other systems, use region-based screenshot
            return self._get_window_screenshot_fallback(window_info)

    def _get_window_screenshot_fallback(self, window_info: WindowInfo) -> Optional[Any]:
        """Fallback method using pyautogui to capture window region"""
        try:
            import pyautogui

            # Update window position in case it moved
            if self.system == "Windows" and HAS_WIN32:
                try:
                    left, top, right, bottom = win32gui.GetWindowRect(window_info.handle)
                    x, y, width, height = left, top, right - left, bottom - top
                except:
                    # Use stored coordinates if GetWindowRect fails
                    x, y, width, height = (
                        window_info.x,
                        window_info.y,
                        window_info.width,
                        window_info.height,
                    )
            else:
                x, y, width, height = (
                    window_info.x,
                    window_info.y,
                    window_info.width,
                    window_info.height,
                )

            # Ensure valid dimensions
            if width <= 0 or height <= 0:
                print(f"Invalid window dimensions for '{window_info.title}': {width}x{height}")
                return None

            # Take screenshot of the window region
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            return screenshot

        except Exception as e:
            print(f"Error taking fallback screenshot for '{window_info.title}': {e}")
            return None

    def _get_window_screenshot_windows(self, window_info: WindowInfo) -> Optional[Any]:
        """Get window screenshot on Windows without switching focus"""
        try:
            import win32gui
            import win32ui
            from PIL import Image

            hwnd = window_info.handle

            # Check if window is valid and visible
            if not win32gui.IsWindow(hwnd):
                print(f"Invalid window handle: {hwnd}")
                return None

            if not win32gui.IsWindowVisible(hwnd):
                print(f"Window not visible: {window_info.title}")
                return None

            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            # Skip windows that are too small
            if width <= 0 or height <= 0:
                print(f"Window has invalid size: {width}x{height}")
                return None

            # Capture window content using BitBlt
            try:
                hwndDC = win32gui.GetWindowDC(hwnd)
                mfcDC = win32ui.CreateDCFromHandle(hwndDC)
                saveDC = mfcDC.CreateCompatibleDC()

                # Create bitmap
                saveBitMap = win32ui.CreateBitmap()
                saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
                saveDC.SelectObject(saveBitMap)

                # Copy window content using BitBlt
                result = saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)

                if result:
                    # Convert to PIL Image
                    bmpinfo = saveBitMap.GetInfo()
                    bmpstr = saveBitMap.GetBitmapBits(True)
                    img = Image.frombuffer(
                        "RGB",
                        (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
                        bmpstr,
                        "raw",
                        "BGRX",
                        0,
                        1,
                    )

                    # Cleanup
                    win32gui.DeleteObject(saveBitMap.GetHandle())
                    saveDC.DeleteDC()
                    mfcDC.DeleteDC()
                    win32gui.ReleaseDC(hwnd, hwndDC)

                    return img
                else:
                    print(f"Failed to capture window content for: {window_info.title}")
                    # Cleanup on failure
                    win32gui.DeleteObject(saveBitMap.GetHandle())
                    saveDC.DeleteDC()
                    mfcDC.DeleteDC()
                    win32gui.ReleaseDC(hwnd, hwndDC)

            except Exception as inner_e:
                print(f"Error in window capture process: {inner_e}")
                # Ensure cleanup on exception
                try:
                    if "saveBitMap" in locals():
                        win32gui.DeleteObject(saveBitMap.GetHandle())
                    if "saveDC" in locals():
                        saveDC.DeleteDC()
                    if "mfcDC" in locals():
                        mfcDC.DeleteDC()
                    if "hwndDC" in locals():
                        win32gui.ReleaseDC(hwnd, hwndDC)
                except:
                    pass

        except Exception as e:
            print(f"Error taking window screenshot for '{window_info.title}': {e}")

        return None

    def _get_fullscreen_screenshot_fallback(self) -> Optional[Any]:
        """Last resort fallback: capture full screen"""
        try:
            import pyautogui

            print("Using full screen capture as last resort for change detection")
            screenshot = pyautogui.screenshot()
            return screenshot
        except Exception as e:
            print(f"Error taking full screen fallback screenshot: {e}")
            return None
