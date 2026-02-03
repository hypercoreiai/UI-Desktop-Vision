#src/backends/linux.py
"""Linux (X11) Backend, we use python-xlib. The challenge with X11 is that child windows often report coordinates relative to their parent window, not the screen. We use translate_coords to perform the "coordinate lift" to the root window (the desktop) so your clicks land correctly."""

import mss
import numpy as np
import pyautogui
from Xlib import display, X
from ewmh import EWMH

class LinuxBackend:
    def __init__(self):
        # Initialize X11 connection and EWMH helper
        self.d = display.Display()
        self.root = self.d.screen().root
        self.ewmh = EWMH(_display=self.d)
        self.sct = mss.mss()
        
        # PyAutoGUI configuration for Linux X11
        pyautogui.PAUSE = 0.1

    def get_active_window_meta(self):
        """
        Uses EWMH and Xlib to find the focused window and its 
        absolute desktop coordinates.
        """
        try:
            # 1. Get the focused window handle (XID)
            active_win = self.ewmh.getActiveWindow()
            if not active_win:
                return self._get_fallback_meta()

            # 2. Get Window Title and Geometry
            name = self.ewmh.getWMName(active_win)
            if isinstance(name, bytes): name = name.decode('utf-8', 'ignore')
            
            geom = active_win.get_geometry()
            
            # 3. The translate_coords Math:
            # This converts (0,0) of the window into its (x,y) on the root screen.
            # This accounts for window decorations (borders/title bars) added by the WM.
            t_coords = active_win.translate_coords(self.root, 0, 0)
            
            return {
                "title": name if name else "Unknown",
                "pid": self.ewmh.getWmPid(active_win),
                "rect": {
                    "x": t_coords.x,
                    "y": t_coords.y,
                    "w": geom.width,
                    "h": geom.height
                }
            }
        except Exception:
            return self._get_fallback_meta()

    def _get_fallback_meta(self):
        monitor = self.sct.monitors[0]
        return {
            "title": "DESKTOP_FALLBACK",
            "pid": 0,
            "rect": {"x": monitor['left'], "y": monitor['top'], "w": monitor['width'], "h": monitor['height']}
        }

    def capture_window(self, rect):
        """Captures window pixels for OCR/Vision."""
        monitor = {
            "top": rect['y'],
            "left": rect['x'],
            "width": rect['w'],
            "height": rect['h']
        }
        # Grab from X server and strip the alpha channel
        sct_img = self.sct.grab(monitor)
        return np.array(sct_img)[:, :, :3]

    def click(self, coords):
        """X11 Hardware click via PyAutoGUI."""
        x, y = coords
        pyautogui.click(x, y)

    def type_text(self, text, coords=None):
        if coords:
            self.click(coords)
        pyautogui.write(text, interval=0.05)


"""Why this works for an X11 Agent:

    translate_coords(self.root, 0, 0): This is the magic line. In X11, a window's internal x, y might be 0, 0 because it thinks it’s at the start of its own container. This function asks the X Server: "Where is this window's [0,0] relative to the actual screen?"
    EWMH Support: By using EWMH (Extended Window Manager Hints), we can extract the _NET_WM_PID, allowing your library to map a window back to a Linux process (e.g., gnome-terminal or firefox).
    Stability: Since Wayland often blocks screen capture and global coordinates for security, this python-xlib approach is the most reliable "god-mode" view for Linux automation until a standardized Wayland portal is widely adopted."""

