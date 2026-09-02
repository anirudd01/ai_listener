"""Application entry point validating environment configuration and bootstrapping background services."""

import sys
import os
import signal
import ctypes
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv

# Check for PYTHONDONTWRITEBYTECODE in environment or .env before runtime
load_dotenv()
if os.getenv("PYTHONDONTWRITEBYTECODE", "").strip() in ("1", "true", "True"):
    sys.dont_write_bytecode = True

from services.clipboard_monitor import ClipboardMonitor
from services.openai_tts import OpenAITTSService
from ui.tray_icon import SystemTrayApp
from utils.config_loader import load_config
from utils.logger import setup_logging, get_logger
from workers.pipeline import PipelineManager

_SINGLE_INSTANCE_MUTEX_NAME = "Global\\AIListenerSingleInstanceMutex"
_mutex_handle = (
    None  # module-level so the handle (and lock) survives for the process lifetime
)


def acquire_single_instance_lock() -> bool:
    """Claims a named Windows mutex so double-clicking the launcher can't spawn duplicate instances."""
    global _mutex_handle
    ERROR_ALREADY_EXISTS = 183
    _mutex_handle = ctypes.windll.kernel32.CreateMutexW(
        None, False, _SINGLE_INSTANCE_MUTEX_NAME
    )
    return ctypes.windll.kernel32.GetLastError() != ERROR_ALREADY_EXISTS


def show_error_notification(title: str, message: str) -> None:
    """Displays a graphical error message box if UI subsystem is available."""
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        root.lift()
        messagebox.showerror(title, message, parent=root)
        root.update_idletasks()
        root.destroy()
    except Exception:
        pass


def main() -> None:
    """Bootstraps application, validates API access, starts background workers, and launches UI."""
    config = load_config()
    logger, _ = setup_logging(config.log_dir)

    if not acquire_single_instance_lock():
        logger.info(
            "Another AI Listener instance is already running; exiting this launch."
        )
        show_error_notification(
            "AI Listener",
            "AI Listener is already running.\nCheck your system tray icon.",
        )
        sys.exit(0)

    logger.info("Starting AI Listener Desktop Application...")

    if not config.openai_api_key or config.openai_api_key == "your-openai-api-key-here":
        error_msg = "OPENAI_API_KEY is missing or invalid in your .env file.\nPlease set a valid key and restart."
        logger.error(error_msg)
        show_error_notification("AI Listener - Configuration Error", error_msg)
        sys.exit(1)

    tts_service = OpenAITTSService(
        api_key=config.openai_api_key,
        model=config.active_model,
        voice=config.ai_voice,
        speed=config.tts_speed,
    )

    # Construction is cheap and local; .start() (workers/network) is deferred until the tray icon is visible
    pipeline = PipelineManager(config=config, tts_service=tts_service)
    clipboard_monitor = ClipboardMonitor(
        on_text_copied=pipeline.process_new_clipboard_text,
        min_length=config.min_text_length,
        poll_interval=1.0,
    )

    def shutdown() -> None:
        """Handles clean application shutdown across all background services."""
        logger.info("Shutting down AI Listener application...")
        clipboard_monitor.stop()
        pipeline.stop()
        logger.info("AI Listener shutdown complete.")
        sys.exit(0)

    # Attach signal handler for graceful CLI termination
    def signal_handler(sig, frame):
        shutdown()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    tray_app = SystemTrayApp(
        on_pause_monitoring=clipboard_monitor.pause_monitoring,
        on_resume_monitoring=clipboard_monitor.resume_monitoring,
        is_monitoring=clipboard_monitor.is_monitoring,
        on_pause_audio=pipeline.pause_audio,
        on_resume_audio=pipeline.resume_audio,
        on_skip_document=pipeline.skip_current_document,
        on_stop_audio=pipeline.stop_everything,
        on_replay_document=pipeline.replay_current_document,
        on_exit=shutdown,
    )

    def run_startup_sequence(app: SystemTrayApp) -> None:
        """Runs the slow, network-bound startup work in the background, after the icon is already visible."""
        app.notify("Starting up - validating API key...")
        logger.info("Validating OpenAI API Key on startup...")
        if not tts_service.validate_api_key():
            error_msg = "Failed to validate OpenAI API key. Check your network or API permissions."
            logger.error(error_msg)
            app.notify(error_msg, title="AI Listener - API Key Error")
            app.stop()
            return

        pipeline.start()
        clipboard_monitor.start()
        app.set_title("AI Listener - Active")
        app.notify("AI Listener is ready and monitoring your clipboard.")
        logger.info(
            "AI Listener is actively monitoring clipboard and running in system tray."
        )

    try:
        tray_app.run(on_ready=run_startup_sequence)
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()


if __name__ == "__main__":
    main()
