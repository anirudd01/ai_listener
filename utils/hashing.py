"""Provides hashing utilities for duplicate content detection and cache keys."""

import hashlib

def compute_text_hash(text: str) -> str:
    """Computes a SHA-256 hash of normalized text for duplicate detection."""
    normalized = text.strip().encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()

def compute_cache_key(text: str, model: str, voice: str, speed: float) -> str:
    """Generates a unique cache filename key based on text, model, voice, and speed."""
    combined = f"{text.strip()}|{model}|{voice}|{speed:.2f}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()
