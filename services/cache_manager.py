"""Manages disk caching for synthesized audio chunks to prevent redundant API calls."""

import shutil
from pathlib import Path
from typing import Optional
from utils.logger import get_logger

class CacheManager:
    """Handles saving and retrieving synthesized audio files using SHA-256 cache keys."""

    def __init__(self, cache_dir: Path, enabled: bool = True):
        """Initializes cache directory and enable flag."""
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled
        self.logger = get_logger()
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cached_audio(self, cache_key: str) -> Optional[Path]:
        """Retrieves path to cached audio file if it exists."""
        if not self.enabled:
            return None

        cached_file = self.cache_dir / f"{cache_key}.mp3"
        if cached_file.exists() and cached_file.stat().st_size > 0:
            self.logger.info(f"Cache HIT for key: {cache_key[:8]}...")
            return cached_file

        self.logger.info(f"Cache MISS for key: {cache_key[:8]}...")
        return None

    def save_to_cache(self, cache_key: str, source_path: Path) -> Path:
        """Saves generated audio file into cache directory."""
        if not self.enabled:
            return source_path

        target_file = self.cache_dir / f"{cache_key}.mp3"
        if source_path != target_file:
            shutil.copy2(source_path, target_file)
        self.logger.info(f"Saved audio to cache: {cache_key[:8]}...")
        return target_file
