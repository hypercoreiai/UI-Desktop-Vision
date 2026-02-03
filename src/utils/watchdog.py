#src/utils/watchdog.py
"""To prevent your script from freezing when Windows UIA or X11 deadlocks, we use a
Multiprocessing Watchdog. This is superior to threading because Python cannot "force-kill" a thread that is stuck in a C-extension or OS kernel call, but it can terminate a sub-process."""

import multiprocessing
import functools
from queue import Empty

class WatchdogTimeoutError(Exception):
    """Custom exception for when an OS API call exceeds its time limit."""
    pass

def timeout_watchdog(seconds=5):
    """
    Decorator that runs a function in a separate process to enforce a strict timeout.
    Usage:
        @timeout_watchdog(seconds=3)
        def get_ui_tree():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a Queue to receive the result from the sub-process
            queue = multiprocessing.Queue()

            # Define the target function for the process
            def worker(q, *worker_args, **worker_kwargs):
                try:
                    result = func(*worker_args, **worker_kwargs)
                    q.put((True, result))
                except Exception as e:
                    q.put((False, e))

            # Start the isolated process
            process = multiprocessing.Process(
                target=worker, 
                args=(queue, *args), 
                kwargs=kwargs,
                daemon=True # Ensures the process dies if the main script exits
            )
            process.start()

            try:
                # Wait for the result or the timeout
                success, result = queue.get(timeout=seconds)
                process.join()
                
                if success:
                    return result
                else:
                    raise result # Re-raise the exception caught in the worker
            
            except Empty:
                process.terminate() # KILL the hanging OS call
                process.join()      # Clean up zombie process
                raise WatchdogTimeoutError(
                    f"OS API call '{func.__name__}' timed out after {seconds}s. "
                    "Process was terminated to prevent system hang."
                )
        return wrapper
    return decorator


"""Why this is critical for your library:

    The "Z-Order" Trap: On Windows, if a window is being destroyed exactly when you query its UIA Tree, the call can hang indefinitely. This decorator ensures your script continues.
    X11 Socket Timeouts: If the X Server connection stutters, python-xlib calls can block. The watchdog acts as a circuit breaker.
    Clean Recovery: By using process.terminate(), you release the lock on the GIL and OS resources, allowing the DesktopOracle to try a "Fallback" (like full-screen OCR) immediately."""
    
"""Notes: Implementation - Integration in core.py
You simply wrap your backend calls like this:

@timeout_watchdog(seconds=2)
def get_safe_meta(self):
    return self.backend.get_active_window_meta()
    
"""