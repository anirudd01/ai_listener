"""Standalone test script to verify notifications, text cleaning, chunking, and app services."""

import sys
import tkinter as tk
from tkinter import messagebox
from services.text_cleaner import TextCleaner
from services.chunker import TextChunker
from utils.hashing import compute_text_hash, compute_cache_key
from utils.config_loader import load_config

def test_notification_dialog(title: str, message: str, dialog_type: str = "info") -> None:
    """Displays a test Tkinter notification dialog and verifies it closes cleanly."""
    print(f"\n[TEST] Launching {dialog_type.upper()} notification dialog: '{title}'...")
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()

    if dialog_type == "error":
        messagebox.showerror(title, message, parent=root)
    elif dialog_type == "warning":
        messagebox.showwarning(title, message, parent=root)
    else:
        messagebox.showinfo(title, message, parent=root)

    # Process pending events and destroy Tk window cleanly
    root.update_idletasks()
    root.destroy()
    print(f"[SUCCESS] Notification window closed cleanly.")

def test_text_cleaner() -> None:
    """Tests the text cleaner preprocessing pipeline with sample AI markdown."""
    print("\n[TEST] Testing Text Cleaner Pipeline...")
    raw_markdown = """# Architecture Overview

Here is a summary of the system architecture:

```python
def example_code():
    print("This code block should be completely skipped!")
```

## Features
- First feature with [GitHub link](https://github.com)
- Second feature with `inline code` and **bold text**

| Header 1 | Header 2 |
| --- | --- |
| Value 1 | Value 2 |

Check <https://example.com> for more details.
"""
    cleaner = TextCleaner()
    cleaned = cleaner.clean(raw_markdown)
    print("--- RAW INPUT ---")
    print(raw_markdown)
    print("--- CLEANED OUTPUT ---")
    print(cleaned)
    print("----------------------")

def test_text_chunker() -> None:
    """Tests sentence boundary chunking logic."""
    print("\n[TEST] Testing Text Chunker...")
    sample_text = (
        "Sentence one is short. Sentence two provides additional architectural context. "
        "Sentence three contains extra detail about the pipeline design. "
        "Sentence four summarizes the worker queue structure."
    )
    chunker = TextChunker(chunk_size=100)
    chunks = chunker.chunk_text(sample_text)
    print(f"Total chunks generated: {len(chunks)}")
    for i, c in enumerate(chunks, 1):
        print(f"  Chunk {i} ({len(c)} chars): {c}")

def test_hashing_and_config() -> None:
    """Tests hashing functions and config loader."""
    print("\n[TEST] Testing Config and Hashing...")
    config = load_config()
    print(f"Active Model: {config.active_model}")
    print(f"AI Voice: {config.ai_voice}")
    print(f"TTS Speed: {config.tts_speed}")
    print(f"Min Text Length: {config.min_text_length}")

    text_hash = compute_text_hash("Sample test text for hashing")
    cache_key = compute_cache_key("Sample test text for hashing", config.active_model, config.ai_voice, config.tts_speed)
    print(f"Text Hash SHA-256: {text_hash[:16]}...")
    print(f"Cache Key SHA-256: {cache_key[:16]}...")

def main() -> None:
    """Runs all standalone component tests."""
    print("==================================================")
    print("       AI Listener Standalone Test Suite         ")
    print("==================================================")

    test_hashing_and_config()
    test_text_cleaner()
    test_text_chunker()

    print("\n[PROMPT] Testing graphical notification windows...")
    test_notification_dialog(
        "AI Listener - Info Test",
        "✨ Notification System Test\n\nClick OK or [X] to verify this notification closes immediately.",
        dialog_type="info"
    )

    test_notification_dialog(
        "AI Listener - Error Test",
        "⚠️ Error Notification Test\n\nVerifying error dialog dismisses cleanly.",
        dialog_type="error"
    )

    print("\n==================================================")
    print("       ALL STANDALONE TESTS COMPLETED!            ")
    print("==================================================")

if __name__ == "__main__":
    main()
