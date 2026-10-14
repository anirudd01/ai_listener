"""Summarizes logs/metrics.log: total estimated spend and seconds of generated audio.

Only fresh OpenAI generations are logged; local cache hits and replays make no API call and no entry.
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

# OpenAI TTS returns 128 kbps MP3 (16,000 bytes per second of audio)
MP3_BYTES_PER_SEC = 16000
# Same rule as services/openai_tts.py: below 150 bytes per char at 1x speed means a cut-off stream
MIN_BYTES_PER_CHAR_AT_1X = 150

def format_seconds(seconds: float) -> str:
    """Formats seconds as 'Hh Mm Ss'."""
    s = int(round(seconds))
    return f"{s // 3600}h {s % 3600 // 60}m {s % 60}s"

def main() -> None:
    """Reads metrics log lines and prints cost and audio-duration totals."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default="logs/metrics.log", help="metrics log file")
    parser.add_argument("--daily", action="store_true", help="also print a per-day breakdown")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"Metrics file not found: {path}")
        return

    total_cost = total_audio = total_wait = 0.0
    requests = chars = bad_lines = 0
    truncated = []
    daily = defaultdict(lambda: [0, 0.0, 0.0])  # requests, cost, audio seconds

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            bad_lines += 1
            continue

        cost = float(entry.get("estimated_cost_usd", 0.0))
        audio_bytes = int(entry.get("audio_bytes", 0))
        audio_sec = audio_bytes / MP3_BYTES_PER_SEC
        char_count = int(entry.get("char_count", 0))

        requests += 1
        chars += char_count
        total_cost += cost
        total_audio += audio_sec
        total_wait += float(entry.get("duration_sec", 0.0))

        speed = max(float(entry.get("speed", 1.0)), 0.25)
        if char_count and audio_bytes / char_count < MIN_BYTES_PER_CHAR_AT_1X / speed:
            truncated.append(entry)

        day = daily[entry.get("timestamp", "")[:10]]
        day[0] += 1
        day[1] += cost
        day[2] += audio_sec

    print(f"Metrics file        : {path}")
    print(f"TTS requests        : {requests}")
    print(f"Characters sent     : {chars:,}")
    print(f"Total spend (est.)  : ${total_cost:.4f}")
    print(f"Audio generated     : {total_audio:,.1f} sec ({format_seconds(total_audio)})  [from audio_bytes]")
    print(f"API wait time       : {total_wait:,.1f} sec ({format_seconds(total_wait)})  [sum of duration_sec]")
    if bad_lines:
        print(f"Unparseable lines   : {bad_lines}")

    if truncated:
        print(f"\nWARNING: {len(truncated)} request(s) returned truncated audio (paid for, not delivered):")
        for e in truncated:
            print(f"  {e['timestamp']}  {e['char_count']} chars -> {e['audio_bytes']} bytes "
                  f"({e['audio_bytes'] / MP3_BYTES_PER_SEC:.1f}s audio, took {e['duration_sec']}s)")

    if args.daily:
        print("\nDate         Requests     Cost      Audio")
        for date in sorted(daily):
            n, cost, sec = daily[date]
            print(f"{date}   {n:>8}   ${cost:>7.4f}   {format_seconds(sec):>10}")

if __name__ == "__main__":
    main()
