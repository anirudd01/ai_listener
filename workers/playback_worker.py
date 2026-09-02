"""Playback Worker thread consuming synthesized audio files and sending them to audio player."""

import queue
import threading
from typing import Callable, Optional
from services.audio_player import AudioPlayer
from workers.tts_worker import AudioTask
from utils.logger import get_logger

class PlaybackWorker:
    """Consumer worker processing audio playback queue sequentially."""

    def __init__(
        self,
        audio_queue: queue.Queue,
        audio_player: AudioPlayer,
        on_playback_complete: Optional[Callable[[str], None]] = None
    ):
        """Initializes playback queue, audio player service, and completion callback."""
        self.audio_queue = audio_queue
        self.audio_player = audio_player
        self.on_playback_complete = on_playback_complete
        self.logger = get_logger()

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._current_doc_id: Optional[str] = None
        self._skip_requested = False

    def start(self) -> None:
        """Starts background thread for audio playback."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="PlaybackWorkerThread")
        self._thread.start()
        self.logger.info("Audio Playback Worker started.")

    def stop(self) -> None:
        """Stops background playback worker thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self.logger.info("Audio Playback Worker stopped.")

    def skip_current_document(self) -> None:
        """Flags current document to skip and stops currently playing chunk."""
        self._skip_requested = True
        self.audio_player.stop()

    def _run(self) -> None:
        """Main loop consuming audio tasks and executing playback."""
        while self._running:
            try:
                task: AudioTask = self.audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            # Check if this document was skipped
            if self._skip_requested and task.doc_id == self._current_doc_id:
                self.audio_queue.task_done()
                continue
            elif task.doc_id != self._current_doc_id:
                self._current_doc_id = task.doc_id
                self._skip_requested = False

            self.logger.info(f"Playing chunk {task.chunk_index + 1}/{task.total_chunks} for doc {task.doc_id[:8]}...")
            success = self.audio_player.play_file(task.audio_path)

            if success and task.chunk_index + 1 == task.total_chunks:
                self.logger.info(f"Finished playback for document {task.doc_id[:8]}.")
                if self.on_playback_complete:
                    self.on_playback_complete(task.doc_id)

            self.audio_queue.task_done()
