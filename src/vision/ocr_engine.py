#src/vision/ocr_engine.py
"""PaddleOCR, your wrapper needs to parse its nested list structure: [ [[[x,y], [x,y], [x,y], [x,y]], ("text", confidence)], ... ].
This wrapper is designed to return "Agent-Ready" dictionaries, where coordinates are already converted from local window crops back to absolute screen coordinates."""

import numpy as np
from paddleocr import PaddleOCR

class OCRWrapper:
    def __init__(self, lang='en'):
        # use_angle_cls=True handles rotated text (common in custom UI labels)
        # show_log=False keeps your terminal clean for the agent's output
        self.engine = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

    def analyze_ui(self, screenshot_np, window_rect):
        """
        Processes a raw numpy image and returns semantic anchors.
        window_rect: {'x', 'y', 'w', 'h'} used to offset local coords to screen coords.
        """
        # PaddleOCR expects a BGR numpy array (OpenCV format)
        results = self.engine.ocr(screenshot_np, cls=True)
        
        # Handle cases where no text is detected
        if not results or results[0] is None:
            return {}

        semantic_data = {}
        
        # Results are wrapped in an extra list for multi-page/batch support
        for line in results[0]:
            coords = line[0]    # The 4 bounding box points
            text_info = line[1] # ("Text content", Confidence)
            
            text_str = text_info[0].strip()
            confidence = text_info[1]

            if confidence < 0.8: # Filter out low-confidence "noise"
                continue

            # 1. Calculate the center of the bounding box
            # coords is [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
            box = np.array(coords).astype(np.int32)
            center_x = int(np.mean(box[:, 0]))
            center_y = int(np.mean(box[:, 1]))

            # 2. Offset to Absolute Screen Coordinates
            # This is vital so the agent can click(x, y) directly
            abs_x = center_x + window_rect['x']
            abs_y = center_y + window_rect['y']

            # 3. Create a unique ID for the script to use
            # "Login Button" -> "login_button"
            clean_id = text_str.lower().replace(" ", "_").replace(":", "")
            
            semantic_data[clean_id] = {
                "text": text_str,
                "click_coords": (abs_x, abs_y),
                "confidence": confidence,
                "local_box": coords # Useful for visual debugging
            }

        return semantic_data

    def find_text_region(self, screenshot_np, target_text):
        """Helper to find a specific string quickly in a new snapshot."""
        data = self.analyze_ui(screenshot_np, {'x': 0, 'y': 0})
        for key, val in data.items():
            if target_text.lower() in val['text'].lower():
                return val['click_coords']
        return None

"""Key Logic for Your Agent:

    Coordinate Transformation: By adding window_rect['x'] and y, your DesktopOracle bypasses the need for the agent to know about "crops." It just sees the whole desktop as one grid.
    Semantic Sanitization: Converting "Email Address:" into the key email_address makes your pure-code scripts much more readable: if "email_address" in ui_state: ....
    Confidence Thresholding: Setting a baseline (e.g., 0.8) prevents your script from attempting to "click" on desktop wallpaper artifacts or rendering glitches.

Developer Tip:
PaddleOCR uses PaddlePaddle as its backend. If you have an NVIDIA GPU, installing paddlepaddle-gpu will make this extraction 5-10x faster than the CPU version, which is crucial for a responsive "on-demand" agent. """

"""2. Refined Spam & Engagement Keyword List
Modern 2026 spam filters prioritize patterns of "fake urgency" and "financial hype". Update your AdFilter keywords to include these expanded categories: 
Category 	Keywords to Block	Purpose
Financial Hype	crypto, airdrop, solana, presale, moon, 100x, pump, whitelist	High-noise crypto spam.
Urgency/Scams	giveaway, winner, claim now, limited offer, urgent, last chance, act now	Common "too good to be true" triggers.
Engagement Bait	drop your wallet, follow + rt, massive giveaway, don't miss out, free gift	Low-value automated engagement bots.
Link-Based Spam	t.me/, bit.ly/, link in bio, click below, visit site	Prevents clicking malicious or low-quality external links.

3. Implementing the "Hardware-Targeted" Vision Scan
Modify your PaddleOCR initialization in src/vision/ocr_engine.py to target the GTX 2070
specifically. This ensures the RTX 4090
remains fully available for the LLM."""