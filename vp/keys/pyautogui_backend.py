from __future__ import annotations
import time
from typing import List
import pyautogui

class PyAutoGUIBackend:
    def __init__(self, panic_hotcorner: bool = True) -> None:
        pyautogui.FAILSAFE = bool(panic_hotcorner)

    def press(self, keys: List[str], hold_secs: float) -> None:
        if not keys:
            return
        downs: List[str] = []
        try:
            for k in keys:
                pyautogui.keyDown(k)
                downs.append(k)
            if hold_secs > 0:
                time.sleep(hold_secs)
        finally:
            for k in reversed(downs):
                try:
                    pyautogui.keyUp(k)
                except Exception:
                    pass
