"""Splits long text documents into ordered, sentence-boundary-aware chunks for TTS streaming."""

import re
from typing import List

class TextChunker:
    """Chunks text cleanly at sentence or word boundaries for incremental TTS generation."""

    def __init__(self, chunk_size: int = 3000):
        """Initializes chunker with maximum character size per chunk."""
        self.chunk_size = chunk_size

    def chunk_text(self, text: str) -> List[str]:
        """Splits input text into ordered chunks respecting sentence boundaries."""
        if not text or not text.strip():
            return []

        text = text.strip()
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        # Split text into sentence candidate tokens
        sentences = re.split(r"(?<=[.!?])\s+", text)
        current_chunk = []
        current_len = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # If a single sentence exceeds max chunk size, break by words
            if len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_len = 0
                
                words = sentence.split()
                sub_chunk = []
                sub_len = 0
                for word in words:
                    if sub_len + len(word) + 1 > self.chunk_size:
                        chunks.append(" ".join(sub_chunk))
                        sub_chunk = [word]
                        sub_len = len(word)
                    else:
                        sub_chunk.append(word)
                        sub_len += len(word) + 1
                if sub_chunk:
                    chunks.append(" ".join(sub_chunk))
                continue

            if current_len + len(sentence) + 1 > self.chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_len = len(sentence)
            else:
                current_chunk.append(sentence)
                current_len += len(sentence) + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
