# OpenRouter Model Slug Reference

> **This file is a curated quick-reference for the most common models.**
> For a complete, always-current list of all models, run:
> ```bash
> python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list
> python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list anthropic
> python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list "~"   # list all latest-alias models
> ```
> To refresh the local cache: `python3.11 .../resolve_model.py --refresh`

---

## Table of Contents

1. [Common Confusions (Read First)](#common-confusions)
2. [Slug Format and Suffix Modifiers](#slug-format-and-suffix-modifiers)
3. [Tilde Latest-Alias Slugs](#tilde-latest-alias-slugs)
4. [Anthropic (Claude)](#anthropic-claude)
5. [Perplexity](#perplexity)
6. [OpenAI](#openai)
7. [Google (Gemini)](#google-gemini)
8. [Meta (Llama)](#meta-llama)
9. [DeepSeek](#deepseek)
10. [MoonshotAI (Kimi)](#moonshotai-kimi)
11. [Mistral](#mistral)

---

## Common Confusions

These are the most frequently confused slug pairs. Check here first before resolving.

| User Says | Correct Slug | Wrong Slug (Do NOT Use) | Why |
|---|---|---|---|
| "claude sonnet 4.6" | `anthropic/claude-sonnet-4.6` | `anthropic/claude-sonnet-4-5` | Version number uses dots, not dashes |
| "sonar pro search" | `perplexity/sonar-pro-search` | `perplexity/sonar-pro` | These are different products: sonar-pro-search is agentic multi-step |
| "claude opus 4.7" | `anthropic/claude-opus-4.7` | `anthropic/claude-opus-4` | Always use the full version number |
| "gemini 2.5 pro" | `google/gemini-2.5-pro` | `google/gemini-2.5-pro-preview` | Use stable release, not preview, unless user specifies |
| "gpt-4.1" | `openai/gpt-4.1` | `openai/gpt-4.1-mini` or `openai/gpt-4.1-nano` | Ambiguous — confirm with user if unclear |
| "kimi k2" | `moonshotai/kimi-k2.6` | `moonshotai/kimi-k2` | Use the latest versioned slug |
| "deepseek r1" | `deepseek/deepseek-r1-0528` | `deepseek/deepseek-r1` | Use the dated version for stability |
| "claude sonnet latest" | `~anthropic/claude-sonnet-latest` | `anthropic/claude-sonnet-latest` | Latest-alias slugs MUST have the `~` prefix |
| "gemini flash latest" | `~google/gemini-flash-latest` | `google/gemini-flash-latest` | Without `~`, the slug is invalid and will error |

---

## Slug Format and Suffix Modifiers

All OpenRouter model IDs follow the pattern: `provider/model-name[:suffix]`

**Always pass the exact slug as the `model` field. Never use display names.**

Suffixes are optional routing modifiers appended with a colon. They do NOT change the underlying model weights — they only change how OpenRouter routes the request to providers.

| Suffix | Effect | When to Use |
|---|---|---|
| `:free` | Routes to free-tier providers only. May have rate limits or lower availability. | When cost is zero priority and rate limits are acceptable |
| `:nitro` | Sorts providers by highest throughput (tokens/sec). Equivalent to `provider.sort = "throughput"`. | When speed matters more than cost |
| `:floor` | Sorts providers by lowest price. Equivalent to `provider.sort = "price"`. | When cost minimization is the priority |
| `:thinking` | Enables extended reasoning / chain-of-thought mode. | For complex reasoning tasks that benefit from step-by-step analysis |
| `:extended` | Routes to providers offering extended context windows. | When you need a larger context window than the standard offering |
| `:exacto` | Quality-first provider sorting using tool-calling reliability signals. Equivalent to explicit Exacto sort. | For agentic/tool-calling workflows where reliability > cost |
| `:online` | **DEPRECATED.** Adds real-time web search. Use `openrouter:web_search` server tool instead. | Legacy only — avoid in new code |

**Note on Auto Exacto:** For any request that includes `tools`, OpenRouter automatically applies Exacto-style quality-first routing without needing the `:exacto` suffix. The suffix is only needed when you want to explicitly force this behavior without sending tools.

**Suffix examples:**
```
anthropic/claude-sonnet-4.6:nitro       # Fastest provider
anthropic/claude-sonnet-4.6:thinking    # Extended reasoning
meta-llama/llama-4-maverick:free        # Free tier
openai/gpt-4.1:exacto                   # Quality-first for tool use
~anthropic/claude-sonnet-latest:nitro   # Tilde slug + suffix (valid combination)
```

---

## Tilde Latest-Alias Slugs

OpenRouter provides a special set of **always-latest alias slugs** that automatically route to the current latest version of a model family. These slugs are prefixed with a tilde (`~`) and always end in `-latest`.

**Key rules:**
- The `~` prefix is **mandatory** — `anthropic/claude-sonnet-latest` (without `~`) is not a valid slug.
- These slugs always point to the most recent stable release; the target may change as new models are released.
- Tilde slugs are compatible with all suffix modifiers (e.g., `~anthropic/claude-sonnet-latest:nitro`).
- Use tilde slugs when the user explicitly says "latest" without specifying a version number.
- Use versioned slugs (e.g., `anthropic/claude-sonnet-4.6`) when reproducibility or a specific version is required.

**All current tilde latest-alias slugs** (run `--list "~"` for live list):

| Slug | Display Name | Context | Max Output |
|---|---|---|---|
| `~anthropic/claude-sonnet-latest` | Anthropic Claude Sonnet Latest | 1M | 128K |
| `~anthropic/claude-opus-latest` | Anthropic Claude Opus Latest | 1M | 128K |
| `~anthropic/claude-haiku-latest` | Anthropic Claude Haiku Latest | 200K | 64K |
| `~google/gemini-flash-latest` | Google Gemini Flash Latest | 1M | 65K |
| `~google/gemini-pro-latest` | Google Gemini Pro Latest | 1M | 65K |
| `~openai/gpt-latest` | OpenAI GPT Latest | 1M | 128K |
| `~openai/gpt-mini-latest` | OpenAI GPT Mini Latest | 400K | 128K |
| `~moonshotai/kimi-latest` | MoonshotAI Kimi Latest | 262K | 16K |

**Natural language → tilde slug mapping:**

| User Says | Resolved Slug |
|---|---|
| "claude sonnet latest" | `~anthropic/claude-sonnet-latest` |
| "claude opus latest" | `~anthropic/claude-opus-latest` |
| "haiku latest" | `~anthropic/claude-haiku-latest` |
| "gemini flash latest" | `~google/gemini-flash-latest` |
| "gemini pro latest" | `~google/gemini-pro-latest` |
| "gpt latest" | `~openai/gpt-latest` |
| "gpt mini latest" | `~openai/gpt-mini-latest` |
| "kimi latest" | `~moonshotai/kimi-latest` |

---

## Anthropic (Claude)

| Slug | Display Name | Context | Max Output | Notes |
|---|---|---|---|---|
| `anthropic/claude-sonnet-4.6` | Claude Sonnet 4.6 | 1M | 128K | **Latest Sonnet** (May 2026) |
| `anthropic/claude-sonnet-4.5` | Claude Sonnet 4.5 | 1M | 64K | Previous Sonnet |
| `anthropic/claude-opus-4.7` | Claude Opus 4.7 | 1M | 128K | **Latest Opus** (May 2026) |
| `anthropic/claude-opus-4.6` | Claude Opus 4.6 | 1M | 128K | |
| `anthropic/claude-opus-4.6-fast` | Claude Opus 4.6 (Fast) | 1M | 128K | Higher cost, faster |
| `anthropic/claude-haiku-4.5` | Claude Haiku 4.5 | 200K | 64K | Fastest/cheapest Claude |
| `anthropic/claude-3.7-sonnet` | Claude 3.7 Sonnet | 200K | 64K | Legacy; retiring May 2026 |
| `anthropic/claude-3.7-sonnet:thinking` | Claude 3.7 Sonnet (thinking) | 200K | 64K | Extended reasoning |
| `anthropic/claude-3.5-haiku` | Claude 3.5 Haiku | 200K | 8K | Legacy |

**Alias slugs (avoid when user specifies a version):**

| Slug | Redirects To |
|---|---|
| `anthropic/claude-sonnet-latest` | Latest Claude Sonnet |
| `anthropic/claude-opus-latest` | Latest Claude Opus |
| `anthropic/claude-haiku-latest` | Latest Claude Haiku |

---

## Perplexity

| Slug | Display Name | Context | Max Output | Notes |
|---|---|---|---|---|
| `perplexity/sonar-pro-search` | Sonar Pro Search | 200K | 8K | **Agentic multi-step search** — exclusive to OpenRouter |
| `perplexity/sonar-pro` | Sonar Pro | 200K | 8K | Standard search with citations |
| `perplexity/sonar` | Sonar | 127K | — | Lightweight, fast |
| `perplexity/sonar-reasoning-pro` | Sonar Reasoning Pro | 128K | — | DeepSeek R1-powered reasoning + search |
| `perplexity/sonar-deep-research` | Sonar Deep Research | 128K | — | Multi-step deep research |

**Key distinction:** `sonar-pro-search` performs agentic multi-step web search and is only available on OpenRouter. `sonar-pro` is the standard single-pass search model available on Perplexity's own API.

---

## OpenAI

| Slug | Display Name | Context | Max Output | Notes |
|---|---|---|---|---|
| `openai/gpt-5.5` | GPT-5.5 | 1.05M | 128K | **Latest Flagship** |
| `openai/gpt-5.5-pro` | GPT-5.5 Pro | 1.05M | 128K | Advanced capabilities |
| `openai/gpt-5.4` | GPT-5.4 | 1.05M | 128K | Previous flagship |
| `openai/gpt-5.4-mini` | GPT-5.4 Mini | 400K | 128K | Fast, cost-efficient |
| `openai/gpt-5.4-nano` | GPT-5.4 Nano | 400K | 128K | Smallest/fastest |
| `openai/o4-mini` | o4 Mini | 200K | 100K | **Latest Fast Reasoning** |
| `openai/o4-mini-high` | o4 Mini High | 200K | 100K | Higher reasoning effort |
| `openai/o3` | o3 | 200K | 100K | Flagship Reasoning |
| `openai/o3-pro` | o3 Pro | 200K | 100K | Highest reasoning quality |
| `openai/o3-mini` | o3 Mini | 200K | 100K | |

---

## Google (Gemini)

| Slug | Display Name | Context | Max Output | Notes |
|---|---|---|---|---|
| `google/gemini-3.1-pro-preview` | Gemini 3.1 Pro Preview | 1M | 65K | **Latest Pro** (preview) |
| `google/gemini-3.1-flash-lite-preview` | Gemini 3.1 Flash Lite Preview | 1M | 65K | Fast, cost-efficient |
| `google/gemini-3-flash-preview` | Gemini 3.0 Flash Preview | 1M | 65K | Previous Flash |
| `google/gemini-2.5-pro` | Gemini 2.5 Pro | 1M | 65K | **Latest stable Pro** |
| `google/gemini-2.5-flash` | Gemini 2.5 Flash | 1M | 65K | Fast, cost-efficient |
| `google/gemini-2.5-flash-lite` | Gemini 2.5 Flash Lite | 1M | 65K | Lightest Gemini |

> **Note on Gemini 3.x:** As of May 2026, Gemini 3.x models are in preview only. The stable production models remain in the `gemini-2.5` series. Use `gemini-3.1-pro-preview` for the latest capabilities, but `gemini-2.5-pro` for production reliability.

---

## Meta (Llama)

| Slug | Display Name | Context | Max Output | Notes |
|---|---|---|---|---|
| `meta-llama/llama-4-maverick` | Llama 4 Maverick | 1M | 16K | Flagship Llama 4 |
| `meta-llama/llama-4-scout` | Llama 4 Scout | 327K | 16K | Efficient Llama 4 |
| `meta-llama/llama-3.3-70b-instruct` | Llama 3.3 70B | — | — | Widely available on free tier |

---

## DeepSeek

| Slug | Display Name | Context | Max Output | Notes |
|---|---|---|---|---|
| `deepseek/deepseek-r1-0528` | DeepSeek R1 0528 | 163K | 32K | **Latest R1** (dated version for stability) |
| `deepseek/deepseek-r1` | DeepSeek R1 | 64K | 16K | Base R1 |
| `deepseek/deepseek-v4-pro` | DeepSeek V4 Pro | 1M | 384K | **Latest V4 chat** |
| `deepseek/deepseek-v4-flash` | DeepSeek V4 Flash | 1M | 384K | Fast V4 |
| `deepseek/deepseek-v3.2` | DeepSeek V3.2 | 131K | 65K | Previous V3 chat |
| `deepseek/deepseek-v3.2-exp` | DeepSeek V3.2 Exp | 163K | 65K | Experimental variant |

---

## MoonshotAI (Kimi)

| Slug | Display Name | Context | Max Output | Notes |
|---|---|---|---|---|
| `moonshotai/kimi-k2.6` | Kimi K2.6 | 262K | 262K | **Latest Kimi** |
| `moonshotai/kimi-k2.5` | Kimi K2.5 | 262K | 65K | Previous Kimi |
| `moonshotai/kimi-k2-thinking` | Kimi K2 Thinking | — | — | Thinking-only mode |
| `moonshotai/kimi-k2-0905` | Kimi K2 0905 | — | — | Dated version |

---

## Mistral

| Slug | Display Name | Context | Max Output | Notes |
|---|---|---|---|---|
| `mistralai/mistral-large-2512` | Mistral Large 2512 | 262K | — | **Latest Large** |
| `mistralai/mistral-medium-3-5` | Mistral Medium 3.5 | 262K | — | Latest Medium |
| `mistralai/mistral-medium-3.1` | Mistral Medium 3.1 | 131K | — | |
| `mistralai/mistral-small-2603` | Mistral Small 2603 | 262K | — | Latest Small |
| `mistralai/mistral-small-3.2-24b-instruct` | Mistral Small 3.2 24B | 128K | 16K | |
| `mistralai/devstral-medium` | Devstral Medium | 131K | — | Code/dev specialist |

---

## Multimodal Generation (Image, Video, Speech)

OpenRouter supports generating images, videos, and speech directly via the standard Chat Completions API or dedicated media endpoints. 

### Image Generation
To generate an image, use the standard Chat Completions API (`/api/v1/chat/completions`). The model will return the image as a base64-encoded data URL in the assistant message.
**Important:** You must specify `modalities: ["image", "text"]` in your request if supported, or simply prompt the model to generate an image.

| Slug | Display Name | Notes |
|---|---|---|
| `openai/gpt-5.4-image-2` | GPT-5.4 Image 2 | Top-tier image generation from OpenAI |
| `google/gemini-3-pro-image-preview` | Gemini 3 Pro Image Preview | Highest-quality Gemini image generation (nano banana pro) |
| `google/gemini-3.1-flash-image-preview` | Gemini 3.1 Flash Image | Fast, high-quality image generation |
| `google/gemini-2.5-flash-image` | Gemini 2.5 Flash Image | Stable image generation variant |
| `bytedance-seed/seedream-4.5` | Seedream 4.5 | Exceptional portrait refinement and multi-image composition |

> **Note:** Image generation models may not appear in the standard `/api/v1/models` list. Use the resolver with `--list` or browse [openrouter.ai/models](https://openrouter.ai/models) filtering by Image output.

### Video Generation
Video generation requires using the dedicated `/api/v1/videos` endpoint. It is an asynchronous process:
1. `POST` to `/api/v1/videos` with `model` and `prompt`.
2. Extract `polling_url` from the response.
3. `GET` the `polling_url` repeatedly until `status` is `"completed"`.
4. Download the video from the `unsigned_urls` list.

| Slug | Display Name | Notes |
|---|---|---|
| `google/veo-3.1` | Veo 3.1 | Maximum visual fidelity, 1080p, native synchronized audio |
| `google/veo-3.1-fast` | Veo 3.1 Fast | Mid-tier, balances speed and quality |
| `bytedance/seedance-2.0` | Seedance 2.0 | Strong character consistency, camera control |
| `bytedance/seedance-2.0-fast` | Seedance 2.0 Fast | Faster, lower cost variant |

> **Note:** Video generation models use a **separate endpoint** (`/api/v1/videos`) and are not listed in the standard `/api/v1/models` response. Their slugs are confirmed from OpenRouter model pages. The resolver script cannot list them via `--list`.

### Speech / Text-to-Speech (TTS)
To generate speech, use the OpenAI-compatible Audio API (`/api/v1/audio/speech`). The response is a raw audio stream (not JSON).

```python
with client.audio.speech.with_streaming_response.create(
  model="google/gemini-3.1-flash-tts-preview",
  input="Hello! This is a text-to-speech test.",
  voice="alloy"
) as response:
  response.stream_to_file("output.mp3")
```

| Slug | Display Name | Notes |
|---|---|---|
| `google/gemini-3.1-flash-tts-preview` | Gemini 3.1 Flash TTS | 70+ languages, natural sounding |
| `openai/gpt-audio` | GPT Audio | High-quality voice synthesis |
| `openai/gpt-audio-mini` | GPT Audio Mini | Faster, lower cost TTS |

> **Note:** TTS models use the OpenAI-compatible `/api/v1/audio/speech` endpoint. The response is a **raw audio stream** (not JSON). The generation ID is returned in the `X-Generation-Id` response header.
