"""OpenAI Text-to-Speech API integration service with metrics tracking and key validation."""

import time
from pathlib import Path
from typing import Callable, Optional
import openai
from utils.logger import get_logger, log_metrics

# Healthy 128 kbps MP3 output is ~1000 bytes per input char at speed 1.0; a stalled stream yields far less
MIN_BYTES_PER_CHAR_AT_1X = 150
# A healthy stream never pauses more than a couple of seconds; fail fast instead of waiting minutes on a stall
READ_TIMEOUT_SEC = 60
MAX_ATTEMPTS = 2

class IncompleteAudioError(Exception):
    """Raised when the TTS API returns audio far too short for the input text."""

class OpenAITTSService:
    """Encapsulates OpenAI TTS API calls, model configuration, and key validation."""

    def __init__(
        self,
        api_key: str,
        model: str = "tts-1",
        voice: str = "alloy",
        speed: float = 1.0,
        notifier: Optional[Callable[[str, Optional[str]], None]] = None
    ):
        """Initializes client with API key, model, voice, playback speed, and optional user notifier."""
        self.api_key = api_key
        self.model = model
        self.voice = voice
        self.speed = speed
        self.notifier = notifier
        self.logger = get_logger()
        timeout = openai.Timeout(600.0, connect=10.0, read=READ_TIMEOUT_SEC)
        self.client = openai.OpenAI(api_key=api_key, timeout=timeout) if api_key else None

    def _notify(self, message: str, title: str) -> None:
        """Shows a user-facing notification if a notifier is attached."""
        if self.notifier:
            self.notifier(message, title)

    def validate_api_key(self) -> bool:
        """Validates API key on startup by attempting a lightweight API check."""
        if not self.api_key or not self.client:
            self.logger.error("OpenAI API key is missing or empty.")
            return False

        try:
            # Lightweight verification call to OpenAI models API
            self.client.models.list()
            self.logger.info("OpenAI API key validation successful.")
            return True
        except openai.AuthenticationError as e:
            self.logger.error(f"OpenAI Authentication Failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"OpenAI API Key validation error: {e}")
            return False

    def generate_speech(self, text: str, output_path: Path) -> Path:
        """Synthesizes speech to an MP3 file, retrying once if the audio comes back incomplete."""
        if not self.client:
            raise ValueError("OpenAI client is not initialized. Check OPENAI_API_KEY.")

        min_bytes = int(len(text) * MIN_BYTES_PER_CHAR_AT_1X / max(self.speed, 0.25))

        for attempt in range(1, MAX_ATTEMPTS + 1):
            file_size = self._synthesize_once(text, output_path)
            if file_size >= min_bytes:
                return output_path

            output_path.unlink(missing_ok=True)
            self.logger.warning(
                f"Incomplete audio on attempt {attempt}/{MAX_ATTEMPTS}: {file_size} bytes "
                f"for {len(text)} chars (expected at least {min_bytes})."
            )
            if attempt < MAX_ATTEMPTS:
                self._notify("Audio came back incomplete. Retrying once...", "AI Listener - Audio Issue")

        self._notify(
            f"Audio is still incomplete after a retry. OpenAI model '{self.model}' may be having problems. "
            f"Try a different ACTIVE_MODEL in .env.",
            "AI Listener - Audio Failed"
        )
        raise IncompleteAudioError(f"Audio incomplete after {MAX_ATTEMPTS} attempts using model '{self.model}'")

    def _synthesize_once(self, text: str, output_path: Path) -> int:
        """Makes one TTS API call, writes the MP3, logs metrics, and returns the bytes written."""
        start_time = time.time()
        self.logger.info(f"Generating TTS speech for {len(text)} characters using model '{self.model}'")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with self.client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=self.voice,
                input=text,
                speed=self.speed,
                response_format="mp3"
            ) as response:
                try:
                    response.stream_to_file(output_path)
                except Exception as e:
                    # A stalled/dropped stream leaves a partial file; the size check treats it as incomplete
                    self.logger.error(f"TTS audio stream interrupted: {type(e).__name__}: {e}")
        except Exception as e:
            self.logger.error(f"Failed to generate TTS speech: {e}")
            raise

        duration_sec = time.time() - start_time
        file_size = output_path.stat().st_size if output_path.exists() else 0

        # Log metrics for usage tracking (incomplete responses are still billed)
        log_metrics(
            char_count=len(text),
            word_count=len(text.split()),
            model=self.model,
            voice=self.voice,
            speed=self.speed,
            audio_bytes=file_size,
            duration_sec=duration_sec,
            cache_hit=False
        )

        self.logger.info(f"TTS synthesis completed in {duration_sec:.2f}s ({file_size} bytes).")
        return file_size
