"""OpenAI Text-to-Speech API integration service with metrics tracking and key validation."""

import time
from pathlib import Path
import openai
from utils.logger import get_logger, log_metrics

class OpenAITTSService:
    """Encapsulates OpenAI TTS API calls, model configuration, and key validation."""

    def __init__(self, api_key: str, model: str = "tts-1", voice: str = "alloy", speed: float = 1.0):
        """Initializes client with API key, model, voice, and playback speed."""
        self.api_key = api_key
        self.model = model
        self.voice = voice
        self.speed = speed
        self.logger = get_logger()
        self.client = openai.OpenAI(api_key=api_key) if api_key else None

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
        """Synthesizes speech from text using OpenAI TTS API and saves to MP3 file."""
        if not self.client:
            raise ValueError("OpenAI client is not initialized. Check OPENAI_API_KEY.")

        start_time = time.time()
        self.logger.info(f"Generating TTS speech for {len(text)} characters using model '{self.model}'")

        try:
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                speed=self.speed,
                response_format="mp3"
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            # Write binary response to file
            if hasattr(response, "write_to_file"):
                response.write_to_file(output_path)
            elif hasattr(response, "stream_to_file"):
                response.stream_to_file(output_path)
            else:
                with open(output_path, "wb") as f:
                    f.write(response.content)

            duration_sec = time.time() - start_time
            file_size = output_path.stat().st_size if output_path.exists() else 0
            words = len(text.split())

            # Log metrics for usage tracking
            log_metrics(
                char_count=len(text),
                word_count=words,
                model=self.model,
                voice=self.voice,
                speed=self.speed,
                audio_bytes=file_size,
                duration_sec=duration_sec,
                cache_hit=False
            )
            
            self.logger.info(f"TTS synthesis completed in {duration_sec:.2f}s ({file_size} bytes).")
            return output_path

        except Exception as e:
            self.logger.error(f"Failed to generate TTS speech: {e}")
            raise
