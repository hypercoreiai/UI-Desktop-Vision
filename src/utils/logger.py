#src/utils/logger.py
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

class OracleLogger:
    def __init__(self, log_dir="logs/audit"):
        os.makedirs(log_dir, exist_ok=True)
        self.log_dir = log_dir
        
        # Configure daily rotation at midnight
        self.handler = TimedRotatingFileHandler(
            filename=f"{log_dir}/audit_log.md",
            when="midnight",
            interval=1,
            backupCount=30  # Keep 30 days of history
        )
        self.handler.setFormatter(logging.Formatter('%(message)s'))
        
        self.logger = logging.getLogger("OracleAudit")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            self.logger.addHandler(self.handler)

    def log_snapshot(self, scene_md, event_type="ON_DEMAND"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = [
            f"---",
            f"### Event: {event_type}",
            f"**Timestamp:** {timestamp}",
            f"\n{scene_md}",
            f"\n---"
        ]
        self.logger.info("\n".join(entry))
