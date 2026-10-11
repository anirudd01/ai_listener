"""Pipeline manager orchestrating text processing, queue streaming, workers, and playback controls."""

import queue
import time
from typing import Optional
from services.audio_player import AudioPlayer
from services.cache_manager import CacheManager
from services.chunker import TextChunker
from services.openai_tts import OpenAITTSService
from services.text_cleaner import TextCleaner
from utils.config_loader import Config
from utils.hashing import compute_text_hash
from utils.logger import get_logger
from workers.playback_worker import PlaybackWorker
from workers.tts_worker import TTSWorker, TextTask

class PipelineManager:
    """Orchestrates producer-consumer streaming pipeline and manages application playback controls."""

    def __init__(self, config: Config, tts_service: OpenAITTSService):
        """Initializes pipeline services, worker queues, and playback controllers."""
        self.config = config
        self.tts_service = tts_service
        self.logger = get_logger()

        self.cleaner = TextCleaner()
        self.chunker = TextChunker(chunk_size=config.chunk_size)
        self.cache_manager = CacheManager(cache_dir=config.cache_dir, enabled=config.enable_cache)
        self.audio_player = AudioPlayer()

        self.text_queue: queue.Queue = queue.Queue()
        self.audio_queue: queue.Queue = queue.Queue()

        self.tts_worker = TTSWorker(
            text_queue=self.text_queue,
            audio_queue=self.audio_queue,
            tts_service=self.tts_service,
            cache_manager=self.cache_manager,
            audio_dir=config.audio_dir
        )

        self.playback_worker = PlaybackWorker(
            audio_queue=self.audio_queue,
            audio_player=self.audio_player
        )

        self._last_raw_text: Optional[str] = None
        self._last_cleaned_text: Optional[str] = None
        self._current_doc_id: Optional[str] = None

    def start(self) -> None:
        """Starts worker threads for TTS generation and audio streaming."""
        self.tts_worker.start()
        self.playback_worker.start()
        self.logger.info("Pipeline manager started.")

    def stop(self) -> None:
        """Stops worker threads and halts playback."""
        self.stop_everything()
        self.tts_worker.stop()
        self.playback_worker.stop()
        self.logger.info("Pipeline manager stopped.")

    def process_new_clipboard_text(self, raw_text: str) -> None:
        """Cleans, chunks, and queues new copied text for streaming TTS generation and playback."""
        cleaned_text = self.cleaner.clean(raw_text)
        if not cleaned_text or len(cleaned_text) < self.config.min_text_length:
            self.logger.info("Cleaned text is too short or empty; skipping synthesis.")
            return

        doc_id = f"doc_{int(time.time())}_{compute_text_hash(cleaned_text)[:8]}"
        chunks = self.chunker.chunk_text(cleaned_text)
        
        self._last_raw_text = raw_text
        self._last_cleaned_text = cleaned_text
        self._current_doc_id = doc_id

        self.logger.info(f"Queuing document {doc_id[:12]} ({len(cleaned_text)} chars, {len(chunks)} chunks)...")

        for idx, chunk in enumerate(chunks):
            task = TextTask(
                doc_id=doc_id,
                chunk_index=idx,
                total_chunks=len(chunks),
                text=chunk
            )
            self.text_queue.put(task)

    def pause_audio(self) -> None:
        """Pauses current audio playback."""
        self.audio_player.pause()

    def resume_audio(self) -> None:
        """Resumes current audio playback."""
        self.audio_player.resume()

    def toggle_pause_audio(self) -> None:
        """Toggles audio playback pause/resume state."""
        self.audio_player.toggle_pause()

    def skip_current_document(self) -> None:
        """Skips current document playback and clears queued chunks for this document."""
        self.logger.info("Skipping current document...")
        self.playback_worker.skip_current_document()
        # Drain text queue for matching tasks
        with self.text_queue.mutex:
            self.text_queue.queue.clear()
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()

    def stop_everything(self) -> None:
        """Clears all pending tasks and stops audio playback immediately."""
        self.logger.info("Stopping all audio generation and playback...")
        self.audio_player.stop()
        with self.text_queue.mutex:
            self.text_queue.queue.clear()
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()

    def replay_current_document(self) -> None:
        """Replays the most recently processed text document."""
        if self._last_raw_text:
            self.logger.info("Replaying current document...")
            self.stop_everything()
            self.process_new_clipboard_text(self._last_raw_text)
        else:
            self.logger.info("No active document available to replay.")
