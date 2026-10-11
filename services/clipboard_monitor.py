"""Background clipboard monitor service detecting new text content with duplicate filtering."""

import time
import threading
from typing import Callable, Optional
import pyperclip
from utils.hashing import compute_text_hash
from utils.logger import get_logger

class ClipboardMonitor:
    """Monitors system clipboard for new text content and triggers processing callbacks."""

    def __init__(
        self,
        on_text_copied: Callable[[str], None],
        min_length: int = 50,
        poll_interval: float = 1.0
    ):
        """Initializes monitor callback, minimum text length filter, and polling frequency."""
        self.on_text_copied = on_text_copied
        self.min_length = min_length
        self.poll_interval = poll_interval
        self.logger = get_logger()

        self._running = False
        self._monitoring_active = True
        self._thread: Optional[threading.Thread] = None
        self._recent_hashes: set[str] = set()
        self._last_content: str = ""

    def start(self) -> None:
        """Starts background clipboard polling thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="ClipboardMonitorThread")
        self._thread.start()
        self.logger.info("Clipboard monitor service started.")

    def stop(self) -> None:
        """Stops background clipboard polling thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self.logger.info("Clipboard monitor service stopped.")

    def pause_monitoring(self) -> None:
        """Pauses clipboard change detection."""
        self._monitoring_active = False
        self.logger.info("Clipboard monitoring paused.")

    def resume_monitoring(self) -> None:
        """Resumes clipboard change detection."""
        self._monitoring_active = True
        self.logger.info("Clipboard monitoring resumed.")

    def is_monitoring(self) -> bool:
        """Returns monitoring state flag."""
        return self._monitoring_active

    def _poll_loop(self) -> None:
        """Internal polling thread loop fetching and inspecting clipboard contents."""
        while self._running:
            if self._monitoring_active:
                try:
                    text = pyperclip.paste()
                    if text and text != self._last_content:
                        self._last_content = text
                        text_clean = text.strip()
                        
                        # Filter out empty or text shorter than minimum configured length
                        if len(text_clean) >= self.min_length:
                            text_hash = compute_text_hash(text_clean)
                            if text_hash not in self._recent_hashes:
                                self._recent_hashes.add(text_hash)
                                # Cap recent hashes set size to prevent unbounded memory growth
                                if len(self._recent_hashes) > 100:
                                    self._recent_hashes.pop()

                                self.logger.info(f"New valid clipboard content detected ({len(text_clean)} chars).")
                                self.on_text_copied(text_clean)
                            else:
                                self.logger.info("Ignored duplicate clipboard content.")
                        else:
                            self.logger.info(f"Ignored short content ({len(text_clean)} < {self.min_length} chars).")
                except Exception as e:
                    self.logger.error(f"Error accessing clipboard: {e}")

            time.sleep(self.poll_interval)
