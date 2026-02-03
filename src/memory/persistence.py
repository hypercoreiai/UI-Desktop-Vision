#src/memory/persistence.py
"""To ensure your agent is fast and resilient, the
persistence.py module uses SQLite to bridge the gap between raw vision and stable memory. Instead of re-running OCR on every frame, it creates a unique structural fingerprint of the window to recall previously discovered semantic IDs."""
import sqlite3
import json
import hashlib

class UIMemory:
    def __init__(self, db_path="data/ui_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the SQLite schema for fast ID recall."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ui_map (
                    fingerprint TEXT,
                    sem_id TEXT,
                    rel_x INTEGER,
                    rel_y INTEGER,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (fingerprint, sem_id)
                )
            """)
            conn.commit()

    def generate_hash(self, meta):
        """
        Creates a 'fingerprint' based on window title and dimensions.
        If the app resizes or the title changes, we treat it as a new state.
        """
        sig = f"{meta['title']}|{meta['rect']['w']}x{meta['rect']['h']}"
        return hashlib.md5(sig.encode()).hexdigest()

    def persist_map(self, fingerprint, semantic_map):
        """
        Stores discovered semantic IDs and their RELATIVE coordinates.
        Relative coords ensure that if the window moves, the memory is still valid.
        """
        with sqlite3.connect(self.db_path) as conn:
            for sem_id, data in semantic_map.items():
                # We only care about the relative offset from window (0,0)
                # Assumes data['click_coords'] are absolute screen coords
                # rel_x = abs_x - win_x
                coords = data['click_coords']
                # These are calculated in the Orchestrator/Core before passing here
                # or we can pass the window_rect to this function.
                
                # For this implementation, we assume semantic_map holds relative data
                # to keep the memory module 'pure'.
                conn.execute("""
                    INSERT OR REPLACE INTO ui_map (fingerprint, sem_id, rel_x, rel_y)
                    VALUES (?, ?, ?, ?)
                """, (fingerprint, sem_id, data['rel_x'], data['rel_y']))
            conn.commit()

    def recall_all(self, fingerprint):
        """
        Returns all known semantic elements for a specific window fingerprint.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT sem_id, rel_x, rel_y FROM ui_map WHERE fingerprint = ?", 
                (fingerprint,)
            )
            rows = cursor.fetchall()
            
        if not rows:
            return None
            
        return {row[0]: {"rel_x": row[1], "rel_y": row[2]} for row in rows}

    def forget(self, fingerprint):
        """Clear memory if a UI update makes the old map invalid."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM ui_map WHERE fingerprint = ?", (fingerprint,))
            conn.commit()


"""Why this Memory Strategy is "Agent-Grade":

    Relative Positioning: By storing rel_x and rel_y (the distance from the window's top-left corner), your script can still find the "Submit" button even if the user drags the window across the screen.
    Fingerprint Stability: By hashing the width and height along with the title, we detect "UI Mutation." If the user expands a sidebar or resizes the window, the fingerprint changes, triggering a fresh OCR pass to ensure accuracy.
    Atomic Persistence: Using SQLite ensures that if your script crashes mid-extraction, the database remains uncorrupted.
    Token Efficiency: Since the DesktopOracle pulls from this local DB, it avoids sending redundant visual data to an LLM, only escalating when the recall_all returns None.

Implementation Detail:
In your core.py, when you call persist_map, you simply subtract the window's rect['x'] and rect['y'] from the absolute coordinates provided by the PaddleOCR engine."""
