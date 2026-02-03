# UI-Desktop-Vision (OracleDesktop)

A unified desktop state analysis and automation library that combines structural metadata (UIA/X11), computer vision (OpenCV), and OCR (PaddleOCR) to create a resilient "Semantic UI Map" for AI agents.

## 🚀 Overview

OracleDesktop solves the "Blind AI" problem by providing a structured, semantic view of any desktop environment. It abstracts OS-specific complexities into a unified state model, making it easy to build agents that work across Windows and Linux.

### Key Features
- **Unified State Model**: Standardized JSON/Markdown output across Windows (UIA) and Linux (X11).
- **Hybrid Extraction**: Combines OS Accessibility trees with high-detail PaddleOCR.
- **Semantic Memory**: Persistent SQLite storage of UI layouts using structural "Fingerprints".
- **Self-Healing**: Multiprocessing watchdogs to recover from OS API hangs and automated application reboot logic.
- **LLM-Ready**: Exports UI scenes as token-efficient Markdown tables for GPT-4o/Claude reasoning.

## 🛠 Tech Stack
- **Vision**: PaddleOCR, OpenCV, mss
- **Windows Backend**: pywinauto (UIA), pywin32
- **Linux Backend**: python-xlib, ewmh
- **Core**: Python 3.10+, SQLite3

## 📂 Project Structure
```
oracle_desktop/
├── run_agent.py             # Entry point for automation scripts
├── data/
│   ├── ui_memory.db         # Persistent fingerprint storage
│   └── templates/           # PNG snippets for icon matching
├── logs/
│   └── audit/               # Daily-rotating Markdown audit logs
└── src/
    ├── core.py              # Main DesktopOracle Orchestrator
    ├── backends/            # OS-specific abstraction layer (Windows/Linux)
    ├── vision/              # OCR Wrapper and Visual Verification
    ├── memory/              # SQLite Persistence and Recovery Playbook
    └── utils/               # Watchdog decorators and Logger
```

## ⚡ Quick Start

### 1. Prerequisites
Ensure you have Python 3.10+ installed. It is highly recommended to use a virtual environment.

```bash
pip install -r requirements.txt
```

### 2. Basic Usage
```python
from src.core import DesktopOracle

# Initialize the Oracle
oracle = DesktopOracle()

# Get the current semantic state of the active window
state = oracle.get_full_state()

# Click the "Submit" button with visual verification
oracle.execute_action("submit_button")
```

## 🛡 Fault Tolerance
The library implements a **Watchdog Pattern**. OS-level API calls (which are prone to hanging) are executed in isolated processes. If a call exceeds the timeout, the process is terminated, and a recovery branch is triggered.

## 📝 Audit & Reasoning
Every action and UI state can be logged to a daily Markdown file. This provides a human-readable (and LLM-readable) trail of what the agent "saw" and why it made specific decisions.

## ⚖ License
MIT License. See [LICENSE](LICENSE) for details.
