You are a senior Python architect and AI application engineer.

Build a complete, production-quality Python desktop utility called:

"AI Listener"

Purpose:
I frequently use GitHub Copilot Chat, Cloud Code, ChatGPT, browser-based AI tools, README files, Markdown documents, design documents, and long AI-generated responses.

I do NOT want a VS Code extension.

I want a standalone Python application that runs in the background and automatically converts copied text into speech using OpenAI TTS.

The workflow should be:

1. AI generates text
2. I press Ctrl+A + Ctrl+C
3. Application detects clipboard change
4. Application sends text to OpenAI TTS
5. Audio begins playing automatically
6. Long outputs are handled intelligently
7. I continue working while listening

The experience should feel like having an audiobook reader for AI-generated content.

====================================================================
TECH STACK
====================================================================

Use Python 3.12+

Use the following libraries where appropriate:

- openai
- python-dotenv
- pyperclip
- asyncio
- pathlib
- pydub
- pygame OR simpleaudio OR another reliable audio library
- logging
- threading
- queue
- tkinter (only if lightweight UI is needed)

Keep dependency count low.

ENVIRONMENT VARIABLES

Use a .env file.

Example:

OPENAI_API_KEY="xxxxx"
ACTIVE_MODEL="xxxx"
AI_VOICE="xxxxx"

Never hardcode secrets.
Validate API key on startup.
Show meaningful error messages if missing.

CORE REQUIREMENTS

The application should run continuously.

Behavior:

- Watch clipboard
- Detect clipboard changes
- Ignore duplicate clipboard content
- Ignore empty content
- Ignore very short content

When new text appears:

- Process it automatically
- Generate speech
- Play audio automatically

No user interaction required.

Example:

Copy text
↓
Audio starts

MINIMUM LENGTH FILTER

Do not generate speech when clipboard content is:

- empty
- whitespace
- fewer than 50 characters

Make this configurable.

AI GENERATED CONTENT OPTIMIZATION

The application should be optimized specifically for AI generated text.

Examples:

- GitHub Copilot responses
- Cloud Code responses
- ChatGPT responses
- Claude responses
- README files
- Markdown files
- Documentation

Before sending text to TTS:

Clean it.
Examples:
Convert:

# Architecture Overview

into:
Architecture Overview

Remove or reduce:

- markdown headers
- code fences
- excessive symbols
- markdown formatting characters

Convert markdown into natural speech-friendly text.

Do NOT remove meaningful content.

Implement a dedicated preprocessing pipeline.

CODE BLOCK HANDLING
Very important.
no need to read the code block out loud, you can skip it
AI responses contain lots of code.

TEXT CLEANING PIPELINE

Create a dedicated preprocessing service.

Handle:

- markdown headers , should read as a section header or with some prefix but not the formatting
- bullet points - just say next point or dont mention it at all. but a pause is required to let the user know a setence or point ended and new point begins
- links - just say link and move on.
- tables - no need to read the table, just say refer to the table in file/chat
- excessive newlines - ignore this no need to read out loud
- code fences - ignore this
- HTML tags - say something like refer to html tags,

Convert text into natural speech.

Example:

"## Installation"

becomes

"Installation"

Example:

"<https://example.com>"

becomes

"link available"

OPENAI TTS

Create a dedicated service class.

Features:

- voice selection
- speed selection
- model selection
all 3 from .env file
User configurable.

LONG CONTENT SUPPORT

This is critical.

Clipboard may contain:

- 5,000 words
- entire README files
- architecture documents
- RFCs
- AI discussions

Build robust chunking.

Requirements:

- break near sentence boundaries
- avoid cutting words
- configurable chunk size
- preserve order

Default:

3000 characters per chunk

STREAMING EXPERIENCE

The user should not wait for the entire document.

Desired flow:

Generate chunk 1
↓
Start playback
↓
Generate chunk 2 in background
↓
Generate chunk 3
↓
Continue playback

Implement producer-consumer architecture.

Use queues.

Create separate workers:

Worker A:
TTS generation

Worker B:
Audio playback

PLAYBACK CONTROLS

Provide global keyboard commands or tray commands.

Required:

Pause
Resume
Skip current document
Stop everything
Replay current document

Implement in a clean architecture.

SYSTEM TRAY APPLICATION

Create a lightweight tray icon.

Options:

- Listening
- Pause Monitoring
- Resume Monitoring
- Start Audio
- Pause Audio
- Resume Audio
- Stop Audio
- Exit

The application should minimize to tray.

No large UI needed.

DUPLICATE DETECTION

If the same content is copied multiple times:

Ignore it.

Store recent clipboard hashes.

Prevent duplicate TTS requests.

AUDIO CACHE

Create an optional cache.

Example:

Avoid unnecessary API calls.

LOGGING

Create structured logging.

logs/app.log

Log:

startup
shutdown
clipboard events
cache hits
cache misses
tts generation
errors
playback events

Never log API keys.

maintain a seperate log for metrics, i should be able to feed this metrics to ai and get how much tokens i might have used or credits, or words i sent and audio responses i recived, if there is a way to track token usage or credit usage, i want that too, not for entire account, just for this api key, if there is a limit or pool of credits i want to know that as well

ERROR HANDLING

Handle:

missing API key
network failures
OpenAI failures
corrupted audio
audio device unavailable
clipboard access errors
file permission errors

Application should gracefully crash, notify me some how take ur best judgement call.
Recover gracefully.

PROJECT STRUCTURE

Generate a clean architecture.

Example:

AI_listener/

├── main.py
├── .env
├── requirements.txt
│
├── services/
│   ├── clipboard_monitor.py
│   ├── openai_tts.py
│   ├── audio_player.py
│   ├── cache_manager.py
│   ├── chunker.py
│   ├── text_cleaner.py
│
├── workers/
│   ├── tts_worker.py
│   └── playback_worker.py
│
├── utils/
│   ├── logger.py
│   ├── hashing.py
│   └── config_loader.py
│
├── cache/
├── audio/
└── logs/

DELIVERABLES

Generate:

- all source files
- requirements.txt
- setup instructions
- architecture explanation
- configuration examples
- runnable code

No pseudocode.
No placeholders.

Provide complete production-quality implementation.
The final project should work after:
pip install -r requirements.txt

and

python main.py

with only a valid .env file required.
code should be self documented, but avoid thick doc string, 2-3 lines max is good, it may be at the begining of the file or class and function level or both, but keep it simple, straight forward and max 2-3 lines.
