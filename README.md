# AI Listener

A production-quality standalone Python desktop utility that runs continuously in the background, automatically converting copied text (from ChatGPT, GitHub Copilot, Claude, README files, Markdown documents, etc.) into high-quality speech using OpenAI TTS.

It acts like an **audiobook reader for AI-generated content**, allowing you to press `Ctrl+A + Ctrl+C` on any text output and immediately start listening while continuing to work.

---

## 🌟 Key Features

- 🎧 **Automatic Background Listening**: Continuously monitors the system clipboard; no manual button pressing required.
- 🧹 **AI-Optimized Preprocessing Pipeline**: Strips code fences, markdown headers, raw URLs, tables, HTML tags, and non-speech symbols while preserving clean natural speech flow.
- ⚡ **Producer-Consumer Audio Streaming**: Chunks long documents into sentence-boundary-aware segments and begins audio playback for Chunk 1 immediately while Chunk 2 synthesizes in the background.
- 💾 **Smart Disk Caching**: Computes SHA-256 hashes based on text, model, voice, and playback speed to eliminate redundant OpenAI API calls.
- ⏸️ **System Tray Controls**: Minimal tray icon supporting Monitoring Toggle (Active/Paused), Pause Audio, Resume Audio, Skip Document, Replay Document, Stop Audio, and Exit.
- 📊 **Structured Metrics & Token Tracker**: Logs structured JSON metrics (`logs/metrics.log`) tracking total characters, estimated tokens, words, payload sizes, API costs, and model usage per request.
- 🛡️ **Graceful Error Handling & Startup Validation**: Validates the OpenAI API key on startup and provides desktop notifications for misconfigurations.

---

## 🏗️ Architecture Overview

```
Copy Text (Ctrl+A + Ctrl+C)
          │
          ▼
┌─────────────────────────┐
│   Clipboard Monitor     │ ──(Filter duplicates & length < 50)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│      Text Cleaner       │ ──(Strip code blocks, tables, URLs, headers)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│      Text Chunker       │ ──(Sentence-boundary splitting ~3000 chars)
└────────────┬────────────┘
             │
             ▼
      [ text_queue ]
             │
             ▼
┌─────────────────────────┐
│     Worker A: TTS       │ ──(Check cache / Call OpenAI API)
└────────────┬────────────┘
             │
             ▼
     [ audio_queue ]
             │
             ▼
┌─────────────────────────┐
│   Worker B: Playback    │ ──(Stream MP3 audio via Pygame)
└─────────────────────────┘
```

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.12+
- Valid OpenAI API Key with access to Audio TTS endpoints.

### Setup Instructions

1. **Clone or Navigate to the Workspace**:

   ```bash
   cd pyvoicer
   ```

2. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and enter your OpenAI API key:

   ```bash
   cp .env.example .env
   ```

   Edit `.env`:

   ```env
   OPENAI_API_KEY="sk-proj-xxxxxxxxxxxxxxxxxxxx"
   ACTIVE_MODEL="tts-1"
   AI_VOICE="alloy"
   TTS_SPEED="1.0"

   MIN_TEXT_LENGTH=50
   CHUNK_SIZE=3000
   ENABLE_CACHE=true

   # Prevent Python bytecode compilation (.pyc / __pycache__)
   PYTHONDONTWRITEBYTECODE=1

   CACHE_DIR="cache"
   AUDIO_DIR="audio"
   LOG_DIR="logs"
   ```

4. **Run the Application**:

   ```bash
   python main.py
   ```

---

## 🎛️ System Tray Options

When running, AI Listener operates quietly in your system tray (supporting both **left-click** and **right-click**):

- ⏸️ **Pause / Resume Monitoring**: Temporarily disable clipboard detection.
- ⏯️ **Pause Audio / Resume Audio**: Pause or unpause playback.
- ─── *(Line Divider)* ───
- ⏭️ **Skip Current Document**: Instantly stop current document audio and move to next.
- 🔁 **Replay Current Document**: Re-chunk and replay the last copied document.
- ─── *(Line Divider)* ───
- ⏹️ **Stop Audio**: Immediately clear all pending playback queues and stop audio.
- ❌ **Exit**: Cleanly shut down background workers and exit without errors.

---

## 🧪 Testing Notifications & Components

Run the standalone test script to test notifications, text cleaner, chunker, and config loading:

```bash
python test_app.py
```

---

## 📊 Usage & Metrics Tracking

AI Listener maintains two log files inside `logs/`:

1. `logs/app.log`: General application events, error tracking, and startup logs.
2. `logs/metrics.log`: JSON-line structured metrics format containing:
   - `timestamp`
   - `char_count`
   - `word_count`
   - `estimated_tokens`
   - `audio_bytes`
   - `duration_sec`
   - `model` & `voice`
   - `cache_hit` status
   - `estimated_cost_usd`

You can feed `logs/metrics.log` directly into an LLM or analysis tool to calculate exact character counts, token usage, API costs, or credit consumption.

---

## 📁 Project Structure

```
AI_listener/
├── main.py                   # Application entry point & startup validation
├── test_app.py               # Standalone test suite for notifications & services
├── .env                      # Environment variables & secrets (ignored)
├── .env.example              # Configuration template
├── requirements.txt          # Dependencies list
├── README.md                 # Project documentation
│
├── services/
│   ├── clipboard_monitor.py  # Background clipboard polling
│   ├── text_cleaner.py       # Markdown & AI text preprocessor
│   ├── chunker.py            # Sentence-boundary text splitter
│   ├── cache_manager.py      # Disk audio caching
│   ├── openai_tts.py         # OpenAI TTS API integration & key validation
│   └── audio_player.py       # Pygame audio player & state controls
│
├── workers/
│   ├── tts_worker.py         # Worker A: TTS generation & caching
│   ├── playback_worker.py    # Worker B: Sequential audio playback
│   └── pipeline.py           # Pipeline manager orchestrating streaming
│
├── ui/
│   └── tray_icon.py          # System tray icon & context menu interface
│
└── utils/
    ├── config_loader.py      # Environment configuration dataclass
    ├── logger.py             # Structured logger & metrics collector
    └── hashing.py            # SHA-256 duplicate & cache key generator
```
