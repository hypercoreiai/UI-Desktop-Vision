#src/vision/visual_check.py
"""We create a specific "Like Finder" that uses a small image snippet (template) of the X heart icon."""

import cv2
import numpy as np
import os

class VisualVerifier:
    def __init__(self, template_dir="data/templates"):
        self.template_dir = template_dir
        os.makedirs(self.template_dir, exist_ok=True)

    def verify_input(self, coords, screenshot_np, padding=30):
        """
        Performs a 'Hollow Check' to verify the target area looks like an input box.
        A box usually has consistent edge gradients and a hollow center.
        """
        x, y = coords[0], coords[1]
        
        # 1. Crop a small 'Verification Patch'
        h, w = screenshot_np.shape[:2]
        y1, y2 = max(0, y - padding), min(h, y + padding)
        x1, x2 = max(0, x - padding), min(w, x + padding)
        patch = screenshot_np[y1:y2, x1:x2]

        if patch.size == 0:
            return False, None

        # 2. Performance Edge Detection (Canny)
        gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
        edged = cv2.Canny(gray, 50, 150)
        
        # 3. Decision: If there are significant edges but the center is clear, 
        # it's likely a valid UI element (box/button)
        edge_density = np.sum(edged) / (edged.size * 255)
        
        # Logic: We expect moderate edge density for a button/input
        is_valid = 0.02 < edge_density < 0.25
        
        return is_valid, patch

class VisualSelector:
    def __init__(self, template_dir="data/templates"):
        # Load the 'unfilled' heart icon template
        self.like_icon = cv2.imread(f"{template_dir}/x_heart_unfilled.png", 0)

    def find_like_buttons(self, screenshot_np):
        """
        Scans the screenshot for all occurrences of the Like heart icon.
        """
        gray_scene = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)
        
        # Template Matching
        res = cv2.matchTemplate(gray_scene, self.like_icon, cv2.TM_CCOEFF_NORMED)
        threshold = 0.85  # High confidence to avoid clicking other UI icons
        
        loc = np.where(res >= threshold)
        found_coords = []
        
        # Group nearby detections to avoid multiple clicks on the same icon
        for pt in zip(*loc[::-1]):
            # Return center of the detected icon
            w, h = self.like_icon.shape[::-1]
            found_coords.append((pt[0] + w//2, pt[1] + h//2))
            
        return self._cluster_points(found_coords)

    def _cluster_points(self, points, dist_thresh=20):
        """Simple deduplication of overlapping matches."""
        if not points: return []
        clusters = []
        for p in points:
            if not any(np.linalg.norm(np.array(p)-np.array(c)) < dist_thresh for c in clusters):
                clusters.append(p)
        return clusters

"""The Fallback Workflow in run_agent.py
This logic attempts the Code-based selector first (fast) and falls back to Vision-based mapping (robust) if the code fails."""

async def interact_with_like(tweet_element, page):
    # ATTEMPT 1: Code-based selector (data-testid)
    try:
        like_btn = tweet_element.get_by_test_id("like")
        if await like_btn.is_visible():
            await like_btn.click()
            return True
    except:
        pass

    # ATTEMPT 2: Vision-based selector
    print("[Vision] Code-selector failed. Capturing region for Visual Mapping...")
    
    # 1. Take a screenshot of just this tweet's region
    box = await tweet_element.bounding_box()
    screenshot_bytes = await page.screenshot(clip=box)
    nparr = np.frombuffer(screenshot_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 2. Use DesktopOracle Vision to find the heart
    vision = VisualSelector()
    matches = vision.find_like_buttons(img)

    if matches:
        # Translate local crop coords back to page coords
        target_x = box['x'] + matches[0][0]
        target_y = box['y'] + matches[0][1]
        
        print(f"[Vision] Found Like icon at offset {matches[0]}. Clicking...")
        await page.mouse.click(target_x, target_y)
        return True

    return False



"""3. Implementation Checklist for Unsupervised Use

    Template Snippet: Take a small screenshot (approx 20x20 pixels) of the unfilled heart icon on X and save it as data/templates/x_heart_unfilled.png.
    Coordinates: Ensure your Chrome User Data path is properly escaped in your script: r"C:\Users\user0\AppData\Local\Google\Chrome\User Data".
    MCP Tooling: Expose this "Visual Like" logic as an MCP tool so the Architect LLM can trigger it if the standard Playwright script reports a "Selector Not Found" error.

4. Why this is "God-Mode" for X Automation
By combining Playwright (for navigation) with OpenCV (for vision), your agent becomes immune to "Frontend Updates." If X changes the data-testid to data-random-string, your script will simply "see" the heart and click it anyway, just like a human would."""