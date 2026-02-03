# Copilot Instructions for UI-Desktop-Vision

## Project Context
This is the **OracleDesktop** library, a unified desktop automation framework that combines structural metadata (UIA/X11), computer vision (OpenCV), and OCR (PaddleOCR) to create a resilient "Semantic UI Map" for AI agents.

## Architectural Principles
- **The Orchestrator**: [src/core.py](src/core.py#L20) (`DesktopOracle`) is the central hub. All high-level logic (scanning, verification, execution) must go through this class.
- **Platform Isolation**: Never put OS-specific code (e.g., `pywinauto`, `Xlib`) in `core.py`. Use the [src/backends/](src/backends/) interface.
- **Fault-Tolerant OS Calls**: All calls to OS Accessibility APIs (UIA/X11) must be isolated via the `@timeout_watchdog` decorator found in [src/watchdog/watchdog.py](src/watchdog/watchdog.py) to prevent process-level hangs.
- **Lazy Initialization**: Initialize heavyweight vision engines (like `PaddleOCR`) only when first requested via a property getter to keep startup fast.

## Coordination & Coordinate Systems
- **Relative vs. Absolute**: Internally, use **relative coordinates** (offset from window top-left) for persistence in [src/memory/persistence.py](src/memory/persistence.py). Convert to **absolute screen coordinates** only at the [DesktopOracle](src/core.py) or `Backend` layer before physical interaction.
- **Semantic IDs**: Map OCR-detected text to `lower_snake_case` IDs. Example: "Login Now" -> `login_now`.

## Core Developer Workflows
- **Memory-First Scanning**: Always check `UIMemory` using a window "fingerprint" (title + dimensions) before performing a full OCR scan.
- **Action Verification**: Before every click, perform a visual check using `VisualVerifier` ([src/vision/visual_check.py](src/vision/visual_check.py)) to ensure the target element hasn't moved or changed state.
- **LLM Escalation**: If a pure-code script cannot find a semantic ID, it should generate a Markdown scene report (as prototyped in [DesktopUIA_Outline_V1.MD](DesktopUIA_Outline_V1.MD)) for LLM reasoning.

## Tech Stack Specifics
- **Vision**: `PaddleOCR` (with `use_angle_cls=True`) for text, `OpenCV` for template matching and contour detection.
- **Backend (Windows)**: `pywinauto` (UIA backend) + `mss` for high-speed capture.
- **Backend (Linux)**: `python-xlib` + `ewmh`.
- **Persistence**: `sqlite3`.

## Programe Patterns to Follow
- **Biased Euclidean Resolver**: When pairing text labels to input boxes, favor candidates to the **Right** or **Below** the label.
- **Fingerprinting**: `hashlib.md5(f"{title}|{w}x{h}")` is the standard key for UI state recall.
- **Watchdog isolation**: Use `multiprocessing` to kill stalled OS API calls.
