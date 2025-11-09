import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import pyautogui

from src.image_detector import ImageDetector


class ActionType(Enum):
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    TYPE_TEXT = "type_text"
    KEY_PRESS = "key_press"
    KEY_COMBINATION = "key_combination"
    WAIT = "wait"
    SCROLL = "scroll"
    MOVE = "move"
    CLICK_IMAGE = "click_image"


@dataclass
class Action:
    type: ActionType
    params: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type.value, "params": self.params}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Action":
        return cls(type=ActionType(data["type"]), params=data["params"])


class ActionExecutor:
    def __init__(self):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1  # Small pause between actions

    def execute_action(self, action: Action) -> bool:
        """Execute a single action"""
        try:
            # Store original mouse position for restoration
            original_pos = pyautogui.position()
            result = False

            try:
                if action.type == ActionType.CLICK:
                    result = self._click(action.params)
                elif action.type == ActionType.DOUBLE_CLICK:
                    result = self._double_click(action.params)
                elif action.type == ActionType.RIGHT_CLICK:
                    result = self._right_click(action.params)
                elif action.type == ActionType.TYPE_TEXT:
                    result = self._type_text(action.params)
                elif action.type == ActionType.KEY_PRESS:
                    result = self._key_press(action.params)
                elif action.type == ActionType.KEY_COMBINATION:
                    result = self._key_combination(action.params)
                elif action.type == ActionType.WAIT:
                    result = self._wait(action.params)
                elif action.type == ActionType.SCROLL:
                    result = self._scroll(action.params)
                elif action.type == ActionType.MOVE:
                    result = self._move(action.params)
                elif action.type == ActionType.CLICK_IMAGE:
                    result = self._click_image(action.params)
                else:
                    print(f"Unknown action type: {action.type}")
                    result = False

            finally:
                # Always restore mouse position after action execution
                pyautogui.moveTo(original_pos)

            return result
        except Exception as e:
            print(f"Error executing action {action.type}: {e}")
            return False

    def execute_sequence(self, actions: list[Action]) -> bool:
        """Execute a sequence of actions"""
        for i, action in enumerate(actions):
            print(f"Executing action {i+1}/{len(actions)}: {action.type.value}")
            if not self.execute_action(action):
                print(f"Failed to execute action {i+1}")
                return False
        return True

    def execute_actions(self, actions: list[Action], stop_condition=None) -> bool:
        """Execute a sequence of actions with optional stop condition"""
        for i, action in enumerate(actions):
            if stop_condition and stop_condition():
                print("Action execution stopped by condition")
                return False
            print(f"Executing action {i+1}/{len(actions)}: {action.type.value}")
            if not self.execute_action(action):
                print(f"Failed to execute action {i+1}")
                return False
        return True

    def _click(self, params: dict[str, Any]) -> bool:
        x = params.get("x")
        y = params.get("y")
        if x is None or y is None:
            return False

        pyautogui.click(x, y)
        return True

    def _double_click(self, params: dict[str, Any]) -> bool:
        x = params.get("x")
        y = params.get("y")
        if x is None or y is None:
            return False

        pyautogui.doubleClick(x, y)
        return True

    def _right_click(self, params: dict[str, Any]) -> bool:
        x = params.get("x")
        y = params.get("y")
        if x is None or y is None:
            return False

        pyautogui.rightClick(x, y)
        return True

    def _type_text(self, params: dict[str, Any]) -> bool:
        text = params.get("text")
        if text is None:
            return False

        interval = params.get("interval", 0.0)
        pyautogui.typewrite(text, interval=interval)
        return True

    def _key_press(self, params: dict[str, Any]) -> bool:
        key = params.get("key")
        if key is None:
            return False

        presses = params.get("presses", 1)
        interval = params.get("interval", 0.0)
        pyautogui.press(key, presses=presses, interval=interval)
        return True

    def _key_combination(self, params: dict[str, Any]) -> bool:
        keys = params.get("keys")
        if not keys or not isinstance(keys, list):
            return False

        pyautogui.hotkey(*keys)
        return True

    def _wait(self, params: dict[str, Any]) -> bool:
        duration = params.get("duration", 1.0)
        time.sleep(duration)
        return True

    def _scroll(self, params: dict[str, Any]) -> bool:
        clicks = params.get("clicks", 0)
        x = params.get("x", None)
        y = params.get("y", None)

        if x is not None and y is not None:
            pyautogui.moveTo(x, y)

        pyautogui.scroll(clicks)
        return True

    def _move(self, params: dict[str, Any]) -> bool:
        """Move mouse to a position"""
        x = params.get("x")
        y = params.get("y")
        duration = params.get("duration", 0)
        if x is None or y is None:
            return False
        pyautogui.moveTo(x, y, duration=duration)
        return True

    def _click_image(self, params: dict[str, Any]) -> bool:
        """Find an image on screen and click its center"""
        image_path = params.get("image_path")
        confidence = params.get("confidence", 0.8)

        if not image_path or not os.path.exists(image_path):
            print(f"Image path not found: {image_path}")
            return False

        try:
            detector = ImageDetector(confidence_threshold=confidence)
            result = detector.find_image_on_screen(image_path)

            if result:
                x, y, width, height = result
                # Click center of the found image
                center_x = x + width // 2
                center_y = y + height // 2

                pyautogui.click(center_x, center_y)
                return True
            else:
                print(f"Image not found on screen: {image_path}")
                return False
        except Exception as e:
            print(f"Error finding/clicking image: {e}")
            return False


# Helper functions for creating actions
def create_click_action(x: int, y: int) -> Action:
    return Action(ActionType.CLICK, {"x": x, "y": y})


def create_double_click_action(x: int, y: int) -> Action:
    return Action(ActionType.DOUBLE_CLICK, {"x": x, "y": y})


def create_right_click_action(x: int, y: int) -> Action:
    return Action(ActionType.RIGHT_CLICK, {"x": x, "y": y})


def create_type_text_action(text: str, interval: float = 0.0) -> Action:
    return Action(ActionType.TYPE_TEXT, {"text": text, "interval": interval})


def create_key_press_action(key: str, presses: int = 1, interval: float = 0.0) -> Action:
    return Action(ActionType.KEY_PRESS, {"key": key, "presses": presses, "interval": interval})


def create_key_combination_action(keys: list[str]) -> Action:
    return Action(ActionType.KEY_COMBINATION, {"keys": keys})


def create_wait_action(duration: float) -> Action:
    return Action(ActionType.WAIT, {"duration": duration})


def create_scroll_action(clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> Action:
    params = {"clicks": clicks}
    if x is not None and y is not None:
        params["x"] = x
        params["y"] = y
    return Action(ActionType.SCROLL, params)


def create_move_action(x: int, y: int, duration: float = 0) -> Action:
    """Create an action to move the mouse to a position"""
    return Action(ActionType.MOVE, {"x": x, "y": y, "duration": duration})


def create_click_image_action(image_path: str, confidence: float = 0.8) -> Action:
    """Create an action to click on the center of an image found on screen"""
    return Action(ActionType.CLICK_IMAGE, {"image_path": image_path, "confidence": confidence})
