"""Configuration loader for environment variables and runtime settings."""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

@dataclass
class Config:
    """Stores application configuration parameters loaded from environment."""
    openai_api_key: str
    active_model: str = "tts-1"
    ai_voice: str = "alloy"
    tts_speed: float = 1.0
    min_text_length: int = 50
    chunk_size: int = 3000
    enable_cache: bool = True
    cache_dir: Path = Path("cache")
    audio_dir: Path = Path("audio")
    log_dir: Path = Path("logs")

def load_config() -> Config:
    """Loads configuration settings from environment variables and dotenv file."""
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("ACTIVE_MODEL", "tts-1").strip()
    voice = os.getenv("AI_VOICE", "alloy").strip()
    
    try:
        speed = float(os.getenv("TTS_SPEED", "1.0"))
    except ValueError:
        speed = 1.0

    try:
        min_length = int(os.getenv("MIN_TEXT_LENGTH", "50"))
    except ValueError:
        min_length = 50

    try:
        chunk_size = int(os.getenv("CHUNK_SIZE", "3000"))
    except ValueError:
        chunk_size = 3000

    enable_cache = os.getenv("ENABLE_CACHE", "true").lower() in ("true", "1", "yes")

    cache_dir = Path(os.getenv("CACHE_DIR", "cache"))
    audio_dir = Path(os.getenv("AUDIO_DIR", "audio"))
    log_dir = Path(os.getenv("LOG_DIR", "logs"))

    # Ensure required directories exist
    cache_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    return Config(
        openai_api_key=api_key,
        active_model=model,
        ai_voice=voice,
        tts_speed=speed,
        min_text_length=min_length,
        chunk_size=chunk_size,
        enable_cache=enable_cache,
        cache_dir=cache_dir,
        audio_dir=audio_dir,
        log_dir=log_dir
    )
