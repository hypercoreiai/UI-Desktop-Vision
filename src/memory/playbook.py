#src/memory/playbook.py
import json
import os

class RecoveryPlaybook:
    def __init__(self, journal_path="data/recovery_journal.json"):
        self.path = journal_path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.history = [] # Stack of semantic IDs visited

    def record_step(self, sem_id, view_name):
        """Called every time the agent successfully interacts with a region."""
        self.history.append({"id": sem_id, "view": view_name})
        if len(self.history) > 10: 
            self.history.pop(0) # Keep it lean
        self._persist()

    def _persist(self):
        with open(self.path, "w") as f:
            json.dump(self.history, f, indent=4)

    def generate_resume_instructions(self):
        """Generates a Markdown guide for the Agent/LLM after a restart."""
        if not self.history:
            return "No history found. Start from the default entry point."
        
        steps = [f"{i+1}. Navigate to **{step['view']}** via **{step['id']}**" 
                 for i, step in enumerate(self.history)]
        
        md = [
            "## Recovery Playbook: Resuming Session",
            "The following steps represent the last successful actions before the crash:",
            "\n".join(steps),
            "\n**Action Required:** Re-verify visual state at the last step before proceeding."
        ]
        return "\n".join(md)
