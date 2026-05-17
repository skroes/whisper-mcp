# whisper-mcp

MCP server that exposes a single `transcribe_audio` tool for Claude
Code to transcribe audio files via OpenAI Whisper.

Built to close the "Channels gap" — the official Claude Code Channels
plugins (Telegram, Discord, iMessage) deliver voice messages as
`'(voice message)'` + `attachment_file_id` without transcription.
Claude can download the audio via `download_attachment` and then call
this tool to get text.

## Tool

```
transcribe_audio(file_path: str) -> str
```

Transcribes an audio file (`.ogg`, `.mp3`, `.m4a`, `.mp4`, `.wav`,
`.flac`) to text. Uses OpenAI's `gpt-4o-mini-transcribe` model with
`language="nl"` by default.

Raises:
- `FileNotFoundError` — path doesn't exist
- `ValueError` — file >25 MB (Whisper API limit)
- `RuntimeError` — API error or missing `OPENAI_API_KEY`

## Install

### Production

```bash
uv tool install git+https://github.com/skroes/whisper-mcp.git
```

### Development

```bash
git clone https://github.com/skroes/whisper-mcp.git
cd whisper-mcp
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Register with Claude Code

```bash
claude mcp add \
  --scope user \
  --env OPENAI_API_KEY="$(op read 'op://Tooling Hub en integraties/.../api_key')" \
  whisper \
  -- "$HOME/.local/bin/whisper-mcp"

# Verify
claude mcp list
claude mcp get whisper
```

For development (venv install):

```bash
claude mcp add \
  --scope user \
  --env OPENAI_API_KEY="$(op read ...)" \
  whisper \
  -- "$HOME/wd-workspace/repo/whisper-mcp/.venv/bin/python" -m whisper_mcp
```

## Claude prompt instruction

Add to `~/.claude/CLAUDE.md`:

```markdown
## Voice attachments in Channels

When a channel message contains a voice/audio attachment (detect via
`attachment_file_id` in the channel tag or `(voice message)` placeholder):

1. Use the channel's attachment download tool (e.g. `download_attachment`
   for Telegram) to save the file locally.
2. Call `transcribe_audio(path)` from the whisper MCP server.
3. Treat the returned transcript as the user's actual message.
4. Continue working in the current session context.
5. If transcription fails, report the error and ask the user to retry
   or type the message.
```

## Testing locally

```bash
# Standalone Python call
.venv/bin/python -c "
import asyncio
from whisper_mcp.transcribe import transcribe_audio
print(asyncio.run(transcribe_audio('/path/to/test.ogg')))
"

# MCP dev mode (interactive)
.venv/bin/mcp dev whisper_mcp/__main__.py
```

## Limits

- File size: 25 MB (OpenAI Whisper API limit). Larger files raise
  `ValueError` — split required (post-MVP feature).
- Language: hardcoded `nl`. Multi-language is post-MVP.

## License

MIT
