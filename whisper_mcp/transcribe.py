"""OpenAI Whisper transcription via gpt-4o-mini-transcribe.

Ported and reduced from ccbot's _transcribe() in src/ccbot/bot.py:956.
Drops session-state, glossary-prompt, spelling-correction, and loop-
detection for MVP. Those are post-MVP iterations.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# OpenAI Whisper API limit per request.
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024

# Default model — modern, better Dutch jargon, logprobs available.
DEFAULT_MODEL = "gpt-4o-mini-transcribe"

# Hardcoded MVP language. Multi-language is post-MVP.
DEFAULT_LANGUAGE = "nl"

# OpenAI Whisper accepteert filename-driven format detection. Telegram
# levert Opus voice als .oga; Whisper rejecteert dat als format. Map naar
# een Whisper-bekende extensie zonder de disk-file te hoeven kopiëren —
# we overriden alleen de filename in de upload-tuple.
_EXT_REMAP = {
    ".oga": ".ogg",  # Telegram voice = Opus, identieke container
}


async def transcribe_audio(file_path: str) -> str:
    """Transcribe an audio file to text via OpenAI Whisper.

    Args:
        file_path: Absolute or relative path to audio file.
                   Supported by OpenAI: .ogg, .mp3, .m4a, .mp4,
                   .mpeg, .mpga, .wav, .webm, .flac.

    Returns:
        Transcribed text, stripped. Empty string if Whisper returns
        empty (e.g. silence).

    Raises:
        FileNotFoundError: if file_path does not exist.
        ValueError: if file is larger than 25 MB (Whisper API limit).
        RuntimeError: if OPENAI_API_KEY is missing or API call fails.
    """
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Not a regular file: {path}")

    size = path.stat().st_size
    if size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"File too large ({size / 1024 / 1024:.1f} MB > 25 MB Whisper "
            "limit). Split required (post-MVP feature)."
        )

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY environment variable not set. Register the MCP "
            "server with --env OPENAI_API_KEY=... via `claude mcp add`."
        )

    logger.info(
        "transcribe: file=%s size=%.1fkb model=%s lang=%s",
        path.name,
        size / 1024,
        DEFAULT_MODEL,
        DEFAULT_LANGUAGE,
    )

    # OpenAI SDK is sync; run in thread to keep MCP async loop responsive.
    transcript = await asyncio.to_thread(_call_openai_sync, path)

    logger.info(
        "transcribe: done file=%s transcript_len=%d",
        path.name,
        len(transcript),
    )
    return transcript


def _call_openai_sync(path: Path) -> str:
    """Sync OpenAI call, wrapped in asyncio.to_thread by caller."""
    import openai

    # Filename-override: OpenAI gebruikt de extensie van de filename voor
    # format-detectie. Telegram's .oga (Opus Audio) wordt afgewezen — map
    # naar .ogg via tuple-upload zonder disk-copy.
    ext = path.suffix.lower()
    upload_name = path.name
    if ext in _EXT_REMAP:
        upload_name = path.stem + _EXT_REMAP[ext]
        logger.debug("ext remap: %s -> %s (upload as)", path.name, upload_name)

    client = openai.OpenAI()
    with open(path, "rb") as audio_file:
        try:
            result = client.audio.transcriptions.create(
                model=DEFAULT_MODEL,
                file=(upload_name, audio_file),
                language=DEFAULT_LANGUAGE,
                temperature=0,
            )
        except openai.OpenAIError as exc:
            raise RuntimeError(f"OpenAI API error: {exc}") from exc

    text = (result.text or "").strip()
    return text
