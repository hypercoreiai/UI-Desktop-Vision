#run_agent.py
"""How this script "thinks":

    Semantic Targeting: It doesn't look for (500, 400). It looks for username. If the window moved, the Memory Module translates the relative coordinates back to the new screen position automatically.
    Safety First: execute_action triggers the OpenCV Visual Check to ensure that even if the coordinates match, the pixels at that spot still look like an input box.
    Traceable Failures: If it fails to find the password field, the generate_scene_description creates a Markdown table. You can literally copy-paste that table into ChatGPT or Claude and ask: "Which of these IDs is most likely the password field?"
    Resilience: If the Windows UIA backend hangs while getting the window title, the @timeout_watchdog in core.py will kill the process, and this script will catch the exception rather than freezing your computer.

Recommended Development Workflow

    Run the script once to "Train" it (Initial PaddleOCR pass).
    Check data/ui_memory.db to see the stored fingerprints.
    Check logs/audit/ to see the Markdown representation of your desktop.

Final Pro-Tip: For the best experience, run the target application in Windowed Mode (not full screen) during initial testing so you can monitor the terminal output alongside the UI actions."""

import time
from src.core import DesktopOracle

def main():
    # 1. Initialize the Oracle (Sets up Backends, Memory, and OCR)
    oracle = DesktopOracle(db_path="data/ui_memory.db", log_dir="logs/audit")
    
    print("--- Starting Login Agent ---")
    
    try:
        # 2. Extract current state (Metadata + Semantic Map)
        # This will automatically use SQL Memory or fire up PaddleOCR if needed.
        state = oracle.get_full_state()
        sem_map = state['semantic_map']
        
        # 3. Decision Logic: Check if we are on the Login Screen
        if "username" not in sem_map:
            print("[Agent] Login fields not detected. Escalating to LLM-ready Scene Report...")
            report = oracle.generate_scene_description(sem_map)
            oracle.audit.log_snapshot(report, "IDENTIFICATION_FAILURE")
            return

        # 4. Interaction: Fill out the form
        # We use execute_action with 'type' to ensure the 'box' hasn't disappeared
        print("[Agent] Entering credentials...")
        
        if oracle.execute_action("username", action_type="type", text="admin_user"):
            print("[Agent] Username entered.")
            
        if oracle.execute_action("password", action_type="type", text="secure_password123"):
            print("[Agent] Password entered.")
            
        # 5. Execution: Click Submit
        if "submit" in sem_map or "login" in sem_map:
            target = "submit" if "submit" in sem_map else "login"
            print(f"[Agent] Submitting via {target}...")
            oracle.execute_action(target)
        if oracle.execute_action("login") or oracle.execute_action("sign_in"):
            print("[Agent] Login sequence complete.")
            oracle.audit.log_snapshot("Login action performed successfully.", "SUCCESS")
        else:
            print("[Agent] Could not find submit button visually.")

    except Exception as e:
        # Handle Watchdog timeouts or OS crashes
        print(f"[Critical] Agent Failure: {e}")
        # Here you would trigger the hard_restart() logic discussed earlier
        # oracle.watchdog.hard_restart()

if __name__ == "__main__":
    main()
