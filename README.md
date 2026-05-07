# openrouter-caller — Manus Agent Skill

A Manus agent skill that ensures correct OpenRouter model slug resolution and API usage.

## What It Does

- **Exact slug passthrough** — If you give a slug like `anthropic/claude-sonnet-4.6` or `~google/gemini-flash-latest`, it is used as-is.
- **Natural language resolution** — "claude sonnet 4.6", "opus 4.7", "gemini flash latest" → resolved to the correct exact slug via live OpenRouter API.
- **Tilde latest-alias support** — Handles `~provider/model-latest` slugs correctly, including natural language like "claude sonnet latest".
- **Suffix-aware scoring** — Penalizes `:free`, `:nitro`, `:floor`, `:thinking`, `:extended`, `:exacto`, `:online` variants unless explicitly requested.
- **Ambiguity warnings** — Warns when two candidates score similarly close.
- **Multimodal generation** — Instructions for image (`/api/v1/chat/completions`), video (`/api/v1/videos`), and speech (`/api/v1/audio/speech`) generation endpoints.

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | Main skill instructions for Manus — read this first |
| `scripts/resolve_model.py` | Live model slug resolver (queries OpenRouter API, 6h cache) |
| `references/model_slugs.md` | Curated reference: slugs, context lengths, max output, confusions, suffixes, multimodal models |

## Usage

```bash
# Resolve a model slug
python3.11 scripts/resolve_model.py "claude sonnet 4.6"
python3.11 scripts/resolve_model.py "gemini flash latest"
python3.11 scripts/resolve_model.py "sonar pro search"

# List all models for a provider
python3.11 scripts/resolve_model.py --list anthropic
python3.11 scripts/resolve_model.py --list "~"   # all latest-alias models

# Force cache refresh
python3.11 scripts/resolve_model.py --refresh
```

## Installation

Place this directory at `/home/ubuntu/skills/openrouter-caller/` in your Manus sandbox.
