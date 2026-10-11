"""TTS Worker thread generating or retrieving cached audio chunks into the playback queue."""

import queue
import threading
from dataclasses import dataclass
from pathlib import Path
from services.cache_manager import CacheManager
from services.openai_tts import OpenAITTSService
from utils.hashing import compute_cache_key
from utils.logger import get_logger

@dataclass
class TextTask:
    """Represents a text chunk task waiting for speech synthesis."""
    doc_id: str
    chunk_index: int
    total_chunks: int
    text: str

@dataclass
class AudioTask:
    """Represents a synthesized audio file ready for playback."""
    doc_id: str
    chunk_index: int
    total_chunks: int
    audio_path: Path
    text: str

class TTSWorker:
    """Producer worker converting text chunks to speech using cache or OpenAI API."""

    def __init__(
        self,
        text_queue: queue.Queue,
        audio_queue: queue.Queue,
        tts_service: OpenAITTSService,
        cache_manager: CacheManager,
        audio_dir: Path
    ):
        """Initializes queues, TTS service, cache manager, and output directory."""
        self.text_queue = text_queue
        self.audio_queue = audio_queue
        self.tts_service = tts_service
        self.cache_manager = cache_manager
        self.audio_dir = Path(audio_dir)
        self.logger = get_logger()

        self._running = False
        self._thread: threading.Thread | None = None
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def start(self) -> None:
        """Starts worker thread for TTS generation."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="TTSWorkerThread")
        self._thread.start()
        self.logger.info("TTS Generation Worker started.")

    def stop(self) -> None:
        """Stops TTS worker thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self.logger.info("TTS Generation Worker stopped.")

    def _run(self) -> None:
        """Main processing loop fetching text tasks and outputting audio tasks."""
        while self._running:
            try:
                task: TextTask = self.text_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                cache_key = compute_cache_key(
                    task.text,
                    self.tts_service.model,
                    self.tts_service.voice,
                    self.tts_service.speed
                )

                cached_audio = self.cache_manager.get_cached_audio(cache_key)
                if cached_audio:
                    audio_path = cached_audio
                else:
                    temp_path = self.audio_dir / f"{task.doc_id}_chunk_{task.chunk_index}.mp3"
                    generated_path = self.tts_service.generate_speech(task.text, temp_path)
                    audio_path = self.cache_manager.save_to_cache(cache_key, generated_path)

                audio_task = AudioTask(
                    doc_id=task.doc_id,
                    chunk_index=task.chunk_index,
                    total_chunks=task.total_chunks,
                    audio_path=audio_path,
                    text=task.text
                )
                self.audio_queue.put(audio_task)
            except Exception as e:
                self.logger.error(f"Error in TTS worker processing chunk {task.chunk_index}: {e}")
            finally:
                self.text_queue.task_done()
