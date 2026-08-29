"""Structured application logging and token/credit metrics tracking."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

_app_logger: logging.Logger | None = None
_metrics_logger: logging.Logger | None = None

def setup_logging(log_dir: Path) -> tuple[logging.Logger, logging.Logger]:
    """Sets up separate loggers for application events and metrics tracking."""
    global _app_logger, _metrics_logger
    log_dir.mkdir(parents=True, exist_ok=True)

    app_logger = logging.getLogger("AIListener")
    app_logger.setLevel(logging.INFO)
    app_logger.handlers.clear()

    # Application log file handler
    app_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    app_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    app_handler.setFormatter(app_formatter)
    app_logger.addHandler(app_handler)

    # Console log handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(app_formatter)
    app_logger.addHandler(console_handler)

    # Metrics log file handler
    metrics_logger = logging.getLogger("AIListenerMetrics")
    metrics_logger.setLevel(logging.INFO)
    metrics_logger.handlers.clear()
    metrics_logger.propagate = False

    metrics_handler = logging.FileHandler(log_dir / "metrics.log", encoding="utf-8")
    metrics_handler.setFormatter(logging.Formatter("%(message)s"))
    metrics_logger.addHandler(metrics_handler)

    _app_logger = app_logger
    _metrics_logger = metrics_logger
    return app_logger, metrics_logger

def get_logger() -> logging.Logger:
    """Returns the application logger instance."""
    global _app_logger
    if _app_logger is None:
        setup_logging(Path("logs"))
    return _app_logger # type: ignore

def log_metrics(
    char_count: int,
    word_count: int,
    model: str,
    voice: str,
    speed: float,
    audio_bytes: int,
    duration_sec: float,
    cache_hit: bool = False
) -> None:
    """Logs structured JSON metrics for usage, token estimation, and credit analysis."""
    global _metrics_logger
    if _metrics_logger is None:
        setup_logging(Path("logs"))

    # Estimate tokens (~1 token per 4 characters for English text)
    estimated_tokens = max(1, round(char_count / 4.0))

    # Pricing per 1000 characters: tts-1 is $0.015, tts-1-hd is $0.030
    price_per_1k = 0.030 if "hd" in model.lower() else 0.015
    estimated_cost_usd = (char_count / 1000.0) * price_per_1k if not cache_hit else 0.0

    entry: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "char_count": char_count,
        "word_count": word_count,
        "estimated_tokens": estimated_tokens,
        "audio_bytes": audio_bytes,
        "duration_sec": round(duration_sec, 2),
        "model": model,
        "voice": voice,
        "speed": speed,
        "cache_hit": cache_hit,
        "estimated_cost_usd": round(estimated_cost_usd, 6)
    }

    _metrics_logger.info(json.dumps(entry)) # type: ignore
