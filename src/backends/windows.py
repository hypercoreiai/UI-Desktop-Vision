#src/backends/windows.py
"""Windows Backend, we use pywinauto for structural metadata and mss for pixel capture. This module is responsible for the heavy lifting of "Structural Querying" and coordinate translation."""

import mss
import numpy as np
from pywinauto import Desktop
import pyautogui

class WindowsBackend:
    def __init__(self):
        # Initialize mss for high-speed screen grabbing
        self.sct = mss.mss()
        # Ensure PyAutoGUI is snappy
        pyautogui.PAUSE = 0.1

    def get_active_window_meta(self):
        """
        Extracts structural 'Ground Truth' from Windows UIA.
        Returns coordinates, title, and process ID.
        """
        try:
            # Connect to the currently focused window via UIA backend
            top_win = Desktop(backend="uia").active()
            rect = top_win.rectangle()
            
            return {
                "title": top_win.window_text(),
                "pid": top_win.process_id(),
                "rect": {
                    "x": rect.left,
                    "y": rect.top,
                    "w": rect.width(),
                    "h": rect.height()
                }
            }
        except Exception as e:
            # Fallback to primary monitor if UIA is hanging or busy
            monitor = self.sct.monitors[1]
            return {
                "title": "DESKTOP_FALLBACK",
                "pid": 0,
                "rect": {"x": monitor['left'], "y": monitor['top'], "w": monitor['width'], "h": monitor['height']}
            }

    def capture_window(self, rect):
        """
        Captures raw pixels for the specified region.
        """
        # mss expects: {'top': y, 'left': x, 'width': w, 'height': h}
        monitor = {
            "top": rect['y'],
            "left": rect['x'],
            "width": rect['w'],
            "height": rect['h']
        }
        sct_img = self.sct.grab(monitor)
        
        # Convert to BGR Numpy array (Standard for OpenCV/PaddleOCR)
        return np.array(sct_img)[:, :, :3]

    def click(self, coords):
        """Performs a hardware-level click at absolute coordinates."""
        x, y = coords
        pyautogui.click(x, y)

    def type_text(self, text, coords=None):
        """Clicks and types. Essential for 'Input Field' semantic actions."""
        if coords:
            self.click(coords)
        pyautogui.write(text, interval=0.05)

"""Why this is the "Gold Standard" for Windows:

    UIA Backend: Unlike older libraries that use Win32 (which misses modern apps), the uia backend sees everything—from legacy Control Panel apps to modern Windows Terminal and Electron apps.
    mss vs. PIL: We use mss because it is significantly faster than ImageGrab. It captures only the active_window region, reducing the memory footprint before the pixels hit your OCR engine.
    Coordinate Consistency: The top_win.rectangle() returns absolute screen coordinates, which perfectly match the inputs required by PyAutoGUI.

Pro-Tip for your Agent:
When your agent needs to fill a form, use get_active_window_meta to verify the window title before calling type_text. If the user accidentally clicks away, the backend can detect the title change and pause the script, preventing it from typing sensitive data into the wrong window."""