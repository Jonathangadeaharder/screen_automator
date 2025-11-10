import time
from typing import Optional

import cv2
import numpy as np
import pyautogui


class ImageDetector:
    def __init__(self, confidence_threshold: float = 0.9):
        self.confidence_threshold = confidence_threshold
        pyautogui.FAILSAFE = True

    def capture_screen(self) -> np.ndarray:
        """Capture the entire screen"""
        screenshot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def capture_region(self, x: int, y: int, width: int, height: int) -> np.ndarray:
        """Capture a specific region of the screen"""
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def load_template(self, image_path: str) -> np.ndarray:
        """Load template image from file"""
        return cv2.imread(image_path, cv2.IMREAD_COLOR)

    def find_image_on_screen(
        self, template_path: str, screen_image: Optional[np.ndarray] = None
    ) -> Optional[tuple[int, int, int, int]]:
        """
        Find template image on screen using template matching
        Returns (x, y, width, height) of found image or None
        """
        if screen_image is None:
            screen_image = self.capture_screen()

        template = self.load_template(template_path)
        if template is None:
            print(f"Failed to load template image: {template_path}")
            return None

        # Check if template is too small
        if template.shape[0] < 10 or template.shape[1] < 10:
            print(
                f"Warning: Template image is very small ({template.shape[1]}x{template.shape[0]})"
            )

        # Convert to grayscale for template matching
        screen_gray = cv2.cvtColor(screen_image, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        # Perform template matching
        result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # Print confidence level for debugging
        print(f"Match confidence: {max_val:.4f} (threshold: {self.confidence_threshold:.4f})")

        if max_val >= self.confidence_threshold:
            template_height, template_width = template_gray.shape
            x, y = max_loc
            return x, y, template_width, template_height

        return None

    def find_all_matches(
        self, template_path: str, screen_image: Optional[np.ndarray] = None
    ) -> list[tuple[int, int, int, int]]:
        """Find all instances of template image on screen"""
        if screen_image is None:
            screen_image = self.capture_screen()

        template = self.load_template(template_path)
        if template is None:
            return []

        screen_gray = cv2.cvtColor(screen_image, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        template_height, template_width = template_gray.shape

        result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= self.confidence_threshold)

        matches = []
        for pt in zip(*locations[::-1]):
            matches.append((pt[0], pt[1], template_width, template_height))

        return matches

    def find_image(self, template_path: str) -> Optional[tuple[int, int, int, int]]:
        """
        Alias for find_image_on_screen for API compatibility.

        This method exists to support the expectations API which expects
        a find_image() method on image detection objects.

        Returns (x, y, width, height) of found image or None
        """
        return self.find_image_on_screen(template_path)

    def wait_for_image(
        self, template_path: str, timeout: float = 10.0, check_interval: float = 0.5
    ) -> Optional[tuple[int, int, int, int]]:
        """Wait for image to appear on screen with timeout"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            match = self.find_image_on_screen(template_path)
            if match:
                return match
            time.sleep(check_interval)

        return None
