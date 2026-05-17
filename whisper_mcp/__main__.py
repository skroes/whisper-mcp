"""MCP server entry-point — stdio transport, single tool transcribe_audio.

Registers with Claude Code via:
  claude mcp add --scope user --env OPENAI_API_KEY=... whisper -- whisper-mcp

Or for venv-dev install:
  claude mcp add --scope user --env OPENAI_API_KEY=... whisper -- \
    /path/to/.venv/bin/python -m whisper_mcp
"""

from __future__ import annotations

import logging
import sys

from mcp.server.fastmcp import FastMCP

from whisper_mcp.transcribe import transcribe_audio as _transcribe_impl

# Log to stderr — stdout is reserved for MCP JSON-RPC protocol.
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="[whisper-mcp] %(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)

mcp = FastMCP("whisper")


@mcp.tool()
async def transcribe_audio(file_path: str) -> str:
    """Transcribe an audio file to text via OpenAI Whisper.

    Use this after `download_attachment` on a channel voice/audio
    attachment to get the user's actual spoken message as text.

    Args:
        file_path: Absolute or relative path to the audio file
            (e.g. /home/.../STATE_DIR/inbox/voice-123.ogg).
            Supported formats: .ogg .mp3 .m4a .mp4 .wav .webm .flac.

    Returns:
        Transcribed text. May be empty for silent audio.

    Errors are returned as MCP isError responses with the exception
    type and message (FileNotFoundError, ValueError for >25 MB, or
    RuntimeError for API/config failures).
    """
    logger.info("tool call: transcribe_audio(%s)", file_path)
    return await _transcribe_impl(file_path)


def run() -> None:
    """Entry point installed as `whisper-mcp` console script."""
    logger.info("whisper-mcp server starting on stdio")
    mcp.run()


if __name__ == "__main__":
    run()
