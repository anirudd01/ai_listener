"""Text preprocessing pipeline to convert AI-generated markdown into speech-friendly natural text."""

import re

class TextCleaner:
    """Preprocesses and cleans raw markdown or AI output for speech synthesis."""

    def clean(self, text: str) -> str:
        """Cleans input text by stripping code blocks, formatting, links, and tables."""
        if not text or not text.strip():
            return ""

        # 1. Skip entire code fences / code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)

        # 2. Convert markdown tables to simple reference message
        table_pattern = r"(?:(?:\|[^\n]+\|\n)+)"
        text = re.sub(table_pattern, " Refer to table. ", text)

        # 3. Handle HTML tags
        if re.search(r"<[a-zA-Z/][^>]*>", text):
            text = re.sub(r"<[a-zA-Z/][^>]*>", " refer to html tags ", text)

        # 4. Handle links: [link text](url) -> "link text, link available"
        text = re.sub(r"\[([^\]]+)\]\((https?://[^\s\)]+)\)", r"\1, link available.", text)
        # Standalone URLs: <http...> or http://... -> "link available"
        text = re.sub(r"<https?://[^\s>]+>", "link available.", text)
        text = re.sub(r"(?<!\()https?://[^\s\)]+", "link available.", text)

        # 5. Clean markdown headers (# Header -> Header.)
        text = re.sub(r"^#{1,6}\s*(.+)$", r"\1.", text, flags=re.MULTILINE)

        # 6. Clean inline code backticks (`code` -> code)
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # 7. Clean bold / italic formatting (**text** or *text* -> text)
        text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
        text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", text)

        # 8. Clean horizontal rules (---, ***, ___)
        text = re.sub(r"^[\-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

        # 9. Clean bullet points and numbered lists (ensure full stop for pause)
        text = re.sub(r"^\s*[\*\-+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

        # 10. Clean blockquotes (> quote -> quote)
        text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)

        # 11. Normalize excessive whitespace and blank lines
        text = re.sub(r"\n\s*\n+", ". ", text)
        text = re.sub(r"\s+", " ", text).strip()

        # 12. Ensure proper sentence ending for smooth TTS flow
        if text and text[-1] not in ".!?":
            text += "."

        return text
