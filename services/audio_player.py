"""Cross-platform audio player service utilizing Pygame mixer for playback and controls."""

import time
import threading
from pathlib import Path
import pygame
from utils.logger import get_logger

class AudioPlayer:
    """Manages audio playback, queue processing state, and pause/resume/stop controls."""

    def __init__(self):
        """Initializes Pygame mixer audio subsystem."""
        self.logger = get_logger()
        self._lock = threading.Lock()
        self._is_paused = False
        self._is_stopped = False
        self._current_file: Path | None = None
        
        try:
            pygame.mixer.init()
            self.logger.info("Audio player initialized successfully with pygame.mixer.")
        except Exception as e:
            self.logger.error(f"Failed to initialize audio mixer: {e}")

    def play_file(self, file_path: Path) -> bool:
        """Plays specified MP3 audio file and blocks until completed or interrupted."""
        with self._lock:
            self._is_paused = False
            self._is_stopped = False
            self._current_file = file_path

        if not file_path.exists():
            self.logger.error(f"Audio file not found: {file_path}")
            return False

        try:
            self.logger.info(f"Playing audio: {file_path.name}")
            pygame.mixer.music.load(str(file_path))
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy() or self._is_paused:
                if self._is_stopped:
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.1)

            return not self._is_stopped
        except Exception as e:
            self.logger.error(f"Playback error for file {file_path.name}: {e}")
            return False

    def pause(self) -> None:
        """Pauses currently playing audio stream."""
        with self._lock:
            if pygame.mixer.music.get_busy() and not self._is_paused:
                pygame.mixer.music.pause()
                self._is_paused = True
                self.logger.info("Audio playback paused.")

    def resume(self) -> None:
        """Resumes paused audio stream."""
        with self._lock:
            if self._is_paused:
                pygame.mixer.music.unpause()
                self._is_paused = False
                self.logger.info("Audio playback resumed.")

    def toggle_pause(self) -> None:
        """Toggles between pause and resume states."""
        if self._is_paused:
            self.resume()
        else:
            self.pause()

    def stop(self) -> None:
        """Stops current audio playback immediately."""
        with self._lock:
            self._is_stopped = True
            self._is_paused = False
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            self.logger.info("Audio playback stopped.")

    def is_playing(self) -> bool:
        """Checks if audio is currently playing."""
        return pygame.mixer.music.get_busy() and not self._is_paused

    def is_paused(self) -> bool:
        """Returns True if audio playback is currently paused."""
        return self._is_paused

    def get_current_file(self) -> Path | None:
        """Returns path of the current audio file being played."""
        return self._current_file
