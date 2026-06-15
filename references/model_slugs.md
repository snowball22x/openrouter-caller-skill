# OpenRouter Model Slug Quick Reference

This file is a curated quick-reference for June 2026-era live models and common media/server-tool usage. The resolver is authoritative.

    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "claude sonnet 4.6"
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list anthropic
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list "~"
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --refresh

---

## 1. Resolver contract

Use the resolver before every call.

| Resolver output | Meaning | Action |
|---|---|---|
| `STATUS=OK` | Resolved/validated | Use `USE_SLUG` exactly |
| `STATUS=UNVERIFIED` | Exact-looking slug passed through because live validation unavailable | Use only if acceptable |
| `STATUS=AMBIGUOUS` | Top candidates are too close | Ask user / inspect candidates |
| `STATUS=ERROR` | No safe slug | Do not call |

Resolve model strings inside server-tool parameters too, such as advisor/subagent worker models and fusion panel/judge models.

---

## 2. Slug format

    provider/model-name[:suffix]
    ~provider/model-family-latest[:suffix]

Examples:

| Example | Meaning |
|---|---|
| `anthropic/claude-sonnet-4.6` | Exact model |
| `anthropic/claude-sonnet-4.6:nitro` | Exact model with fastest routing |
| `~anthropic/claude-sonnet-latest` | Tilde latest alias |
| `~google/gemini-flash-latest:floor` | Latest Gemini Flash, cheapest routing |

---

## 3. Slug suffixes

| Suffix | Effect |
|---|---|
| `:nitro` | Fastest provider routing |
| `:floor` | Cheapest provider routing |
| `:free` | Free-tier providers only |
| `:thinking` | Extended reasoning/thinking routing when supported |
| `:extended` | Extended context routing when supported |
| `:exacto` | Quality-first routing for reliability/tool use |
| `:online` | Deprecated; prefer `openrouter:web_search` server tool |

Suffixes can be appended to normal and tilde slugs. Use the resolver to apply them.

---

## 4. Common confusions

| User says | Correct slug / action | Avoid | Reason |
|---|---|---|---|
| `claude sonnet 4.6` | `anthropic/claude-sonnet-4.6` | guessed dash variants | Version uses dot |
| `claude opus latest` | `~anthropic/claude-opus-latest` | guessing latest numbered release | Latest alias is explicit |
| `claude latest` | Ask family or inspect resolver candidates | assuming Sonnet | Could mean Sonnet, Opus, Haiku, or Fable |
| `claude 3.7 sonnet` | Not in supplied June 2026 live list; ask for current Claude 4.x or exact slug | mapping to Sonnet 4.x silently | Different model generation |
| `sonar pro search` | `perplexity/sonar-pro-search` | `perplexity/sonar-pro` | Different Perplexity products |
| `gpt-4.1` | `openai/gpt-4.1` | `openai/gpt-4.1-mini`, `openai/gpt-4.1-nano` | Mini/nano are distinct |
| `gpt latest` | `~openai/gpt-latest` | `openai/gpt-latest` | Tilde alias required |
| `gemini flash latest` | `~google/gemini-flash-latest` | `google/gemini-flash-latest` | Tilde alias required |
| `deepseek r1` | `deepseek/deepseek-r1-0528` | old or undated if reproducibility matters | Dated R1 preferred |
| `deepseek r2` | Not in supplied June 2026 live list; use V4/R1/V3.2 or exact slug | inventing `deepseek-r2` | No live slug provided |
| `kimi k2` | `moonshotai/kimi-k2.6` | older `moonshotai/kimi-k2` | Latest general K2 line |
| `mistral medium 3.5` | `mistralai/mistral-medium-3-5` | dot slug | Slug uses `3-5` |
| `nano banana pro` | `google/gemini-3-pro-image-preview` | flash image variants | Pro image model |
| `grok 3` | Not in supplied June 2026 live list; use `x-ai/grok-4.3`/`x-ai/grok-4.20` if acceptable | mapping to `grok-4.3` silently | `4.3` is not Grok 3 |
| search/current info | Add `tools: [{"type": "openrouter:web_search"}]` | `:online` | Server tool is the current path |

---

## 5. Tilde latest aliases

Use when the user explicitly says “latest” without a version.

| Natural language | Slug | Context | Max output |
|---|---|---:|---:|
| Claude Sonnet latest | `~anthropic/claude-sonnet-latest` | 1,000,000 | 128,000 |
| Claude Opus latest | `~anthropic/claude-opus-latest` | 1,000,000 | 128,000 |
| Claude Haiku latest | `~anthropic/claude-haiku-latest` | 200,000 | 64,000 |
| Claude Fable latest | `~anthropic/claude-fable-latest` | 1,000,000 | 128,000 |
| Gemini Flash latest | `~google/gemini-flash-latest` | 1,048,576 | 65,536 |
| Gemini Pro latest | `~google/gemini-pro-latest` | 1,048,576 | 65,536 |
| GPT latest | `~openai/gpt-latest` | 1,050,000 | 128,000 |
| GPT Mini latest | `~openai/gpt-mini-latest` | 400,000 | 128,000 |
| Kimi latest | `~moonshotai/kimi-latest` | 262,144 | 262,142 |

Rules:
- Tilde prefix `~` is part of the slug.
- Latest alias target may change over time.
- Tilde aliases work with suffixes, e.g. `~openai/gpt-latest:nitro`.
- If the user says only “Claude latest” or “Gemini latest”, resolver may return `STATUS=AMBIGUOUS`; ask which family.

---

## 6. Anthropic Claude

| Slug | Display name | Context | Max output | Notes |
|---|---|---:|---:|---|
| `anthropic/claude-fable-5` | Claude Fable 5 | 1,000,000 | 128,000 | Current Fable |
| `anthropic/claude-sonnet-4.6` | Claude Sonnet 4.6 | 1,000,000 | 128,000 | Latest Sonnet in supplied list |
| `anthropic/claude-sonnet-4.5` | Claude Sonnet 4.5 | 1,000,000 | 64,000 | Previous Sonnet |
| `anthropic/claude-sonnet-4` | Claude Sonnet 4 | 1,000,000 | 64,000 | Older Sonnet 4 |
| `anthropic/claude-opus-4.8` | Claude Opus 4.8 | 1,000,000 | 128,000 | Latest Opus in supplied list |
| `anthropic/claude-opus-4.8-fast` | Claude Opus 4.8 Fast | 1,000,000 | 128,000 | Faster variant |
| `anthropic/claude-opus-4.7` | Claude Opus 4.7 | 1,000,000 | 128,000 | Previous Opus |
| `anthropic/claude-opus-4.7-fast` | Claude Opus 4.7 Fast | 1,000,000 | 128,000 | Faster variant |
| `anthropic/claude-opus-4.6` | Claude Opus 4.6 | 1,000,000 | 128,000 | Older Opus |
| `anthropic/claude-opus-4.6-fast` | Claude Opus 4.6 Fast | 1,000,000 | 128,000 | Faster variant |
| `anthropic/claude-opus-4.5` | Claude Opus 4.5 | 200,000 | 64,000 | Older Opus |
| `anthropic/claude-opus-4.1` | Claude Opus 4.1 | 200,000 | 32,000 | Legacy Opus 4.x |
| `anthropic/claude-opus-4` | Claude Opus 4 | 200,000 | 32,000 | Legacy Opus 4 |
| `anthropic/claude-haiku-4.5` | Claude Haiku 4.5 | 200,000 | 64,000 | Fast/low cost |
| `anthropic/claude-3.5-haiku` | Claude 3.5 Haiku | 200,000 | 8,192 | Legacy Haiku |
| `anthropic/claude-3-haiku` | Claude 3 Haiku | 200,000 | 4,096 | Legacy Haiku |

Recommended:
- Specific reproducible Sonnet: `anthropic/claude-sonnet-4.6`
- Latest Sonnet alias: `~anthropic/claude-sonnet-latest`
- Latest Opus alias: `~anthropic/claude-opus-latest`
- Strong advisor/judge: `~anthropic/claude-opus-latest`

---

## 7. Perplexity Sonar

| Slug | Display name | Context | Max output | Notes |
|---|---|---:|---:|---|
| `perplexity/sonar-pro-search` | Sonar Pro Search | 200,000 | 8,000 | Agentic multi-step search |
| `perplexity/sonar-pro` | Sonar Pro | 200,000 | 8,000 | Standard search |
| `perplexity/sonar-reasoning-pro` | Sonar Reasoning Pro | 128,000 | ? | Reasoning + search |
| `perplexity/sonar-deep-research` | Sonar Deep Research | 128,000 | ? | Deep research workflow |
| `perplexity/sonar` | Sonar | 127,072 | ? | Lightweight |

Key distinction: `sonar-pro-search` is not the same as `sonar-pro`.

---

## 8. OpenAI
| Slug | Display name | Context | Max output | Notes |
|---|---|---:|---:|---|
| `openai/gpt-3.5-turbo` | OpenAI: GPT-3.5 Turbo | 16,385 | 4096 |  |
| `openai/gpt-3.5-turbo-0613` | OpenAI: GPT-3.5 Turbo (older v0613) | 4,095 | 4096 |  |
| `openai/gpt-3.5-turbo-16k` | OpenAI: GPT-3.5 Turbo 16k | 16,385 | 4096 |  |
| `openai/gpt-3.5-turbo-instruct` | OpenAI: GPT-3.5 Turbo Instruct | 4,095 | 4096 |  |
| `openai/gpt-4` | OpenAI: GPT-4 | 8,191 | 4096 |  |
| `openai/gpt-4-turbo` | OpenAI: GPT-4 Turbo | 128,000 | 4096 |  |
| `openai/gpt-4-turbo-preview` | OpenAI: GPT-4 Turbo Preview | 128,000 | 4096 |  |
| `openai/gpt-4.1` | OpenAI: GPT-4.1 | 1,047,576 | None | Stable production |
| `openai/gpt-4.1-mini` | OpenAI: GPT-4.1 Mini | 1,047,576 | 32768 |  |
| `openai/gpt-4.1-nano` | OpenAI: GPT-4.1 Nano | 1,047,576 | 32768 |  |
| `openai/gpt-4o` | OpenAI: GPT-4o | 128,000 | 16384 |  |
| `openai/gpt-4o-2024-05-13` | OpenAI: GPT-4o (2024-05-13) | 128,000 | 4096 |  |
| `openai/gpt-4o-2024-08-06` | OpenAI: GPT-4o (2024-08-06) | 128,000 | 16384 |  |
| `openai/gpt-4o-2024-11-20` | OpenAI: GPT-4o (2024-11-20) | 128,000 | 16384 |  |
| `openai/gpt-4o-mini` | OpenAI: GPT-4o-mini | 128,000 | 16384 |  |
| `openai/gpt-4o-mini-2024-07-18` | OpenAI: GPT-4o-mini (2024-07-18) | 128,000 | 16384 |  |
| `openai/gpt-4o-mini-search-preview` | OpenAI: GPT-4o-mini Search Preview | 128,000 | 16384 |  |
| `openai/gpt-4o-search-preview` | OpenAI: GPT-4o Search Preview | 128,000 | 16384 |  |
| `openai/gpt-5` | OpenAI: GPT-5 | 400,000 | 128000 |  |
| `openai/gpt-5-chat` | OpenAI: GPT-5 Chat | 128,000 | 16384 |  |
| `openai/gpt-5-codex` | OpenAI: GPT-5 Codex | 400,000 | 128000 |  |
| `openai/gpt-5-image` | OpenAI: GPT-5 Image | 400,000 | 128000 |  |
| `openai/gpt-5-image-mini` | OpenAI: GPT-5 Image Mini | 400,000 | 128000 |  |
| `openai/gpt-5-mini` | OpenAI: GPT-5 Mini | 400,000 | 128000 |  |
| `openai/gpt-5-nano` | OpenAI: GPT-5 Nano | 400,000 | None |  |
| `openai/gpt-5-pro` | OpenAI: GPT-5 Pro | 400,000 | 128000 |  |
| `openai/gpt-5.1` | OpenAI: GPT-5.1 | 400,000 | 128000 |  |
| `openai/gpt-5.1-chat` | OpenAI: GPT-5.1 Chat | 128,000 | 32000 |  |
| `openai/gpt-5.1-codex` | OpenAI: GPT-5.1-Codex | 400,000 | 128000 |  |
| `openai/gpt-5.1-codex-max` | OpenAI: GPT-5.1-Codex-Max | 400,000 | 128000 |  |
| `openai/gpt-5.1-codex-mini` | OpenAI: GPT-5.1-Codex-Mini | 400,000 | 100000 |  |
| `openai/gpt-5.2` | OpenAI: GPT-5.2 | 400,000 | 128000 |  |
| `openai/gpt-5.2-chat` | OpenAI: GPT-5.2 Chat | 128,000 | 16384 |  |
| `openai/gpt-5.2-codex` | OpenAI: GPT-5.2-Codex | 400,000 | 128000 |  |
| `openai/gpt-5.2-pro` | OpenAI: GPT-5.2 Pro | 400,000 | 128000 |  |
| `openai/gpt-5.3-chat` | OpenAI: GPT-5.3 Chat | 128,000 | 16384 |  |
| `openai/gpt-5.3-codex` | OpenAI: GPT-5.3-Codex | 400,000 | 128000 |  |
| `openai/gpt-5.4` | OpenAI: GPT-5.4 | 1,050,000 | 128000 |  |
| `openai/gpt-5.4-image-2` | OpenAI: GPT-5.4 Image 2 | 272,000 | 128000 |  |
| `openai/gpt-5.4-mini` | OpenAI: GPT-5.4 Mini | 400,000 | 128000 |  |
| `openai/gpt-5.4-nano` | OpenAI: GPT-5.4 Nano | 400,000 | 128000 |  |
| `openai/gpt-5.4-pro` | OpenAI: GPT-5.4 Pro | 1,050,000 | 128000 |  |
| `openai/gpt-5.5` | OpenAI: GPT-5.5 | 1,050,000 | 128000 | Current flagship |
| `openai/gpt-5.5-pro` | OpenAI: GPT-5.5 Pro | 1,050,000 | 128000 | Highest capability |
| `openai/gpt-audio` | OpenAI: GPT Audio | 128,000 | 16384 | TTS/audio |
| `openai/gpt-audio-mini` | OpenAI: GPT Audio Mini | 128,000 | 16384 | TTS/audio |
| `openai/gpt-chat-latest` | OpenAI: GPT Chat Latest | 400,000 | 128000 |  |
| `openai/gpt-oss-120b` | OpenAI: gpt-oss-120b | 131,072 | None |  |
| `openai/gpt-oss-120b:free` | OpenAI: gpt-oss-120b (free) | 131,072 | 131072 |  |
| `openai/gpt-oss-20b` | OpenAI: gpt-oss-20b | 131,072 | None |  |
| `openai/gpt-oss-20b:free` | OpenAI: gpt-oss-20b (free) | 131,072 | 8192 |  |
| `openai/gpt-oss-safeguard-20b` | OpenAI: gpt-oss-safeguard-20b | 131,072 | 65536 |  |
| `openai/o1` | OpenAI: o1 | 200,000 | 100000 |  |
| `openai/o1-pro` | OpenAI: o1-pro | 200,000 | 100000 |  |
| `openai/o3` | OpenAI: o3 | 200,000 | 100000 | Strong reasoning |
| `openai/o3-deep-research` | OpenAI: o3 Deep Research | 200,000 | 100000 | Strong reasoning |
| `openai/o3-mini` | OpenAI: o3 Mini | 200,000 | 100000 |  |
| `openai/o3-mini-high` | OpenAI: o3 Mini High | 200,000 | 100000 |  |
| `openai/o3-pro` | OpenAI: o3 Pro | 200,000 | 100000 | Strong reasoning |
| `openai/o4-mini` | OpenAI: o4 Mini | 200,000 | 100000 | Fast reasoning |
| `openai/o4-mini-deep-research` | OpenAI: o4 Mini Deep Research | 200,000 | 100000 | Fast reasoning |
| `openai/o4-mini-high` | OpenAI: o4 Mini High | 200,000 | 100000 | Fast reasoning |

## 9. Google Gemini

| Slug | Display name | Context | Notes |
|---|---|---:|---|
| `google/gemini-3.5-flash` | Gemini 3.5 Flash | 1M | Latest Flash line |
| `google/gemini-3.1-pro-preview` | Gemini 3.1 Pro Preview | 1M | Latest Pro preview |
| `google/gemini-3.1-pro-preview-customtools` | Gemini 3.1 Pro Preview Custom Tools | 1M | Custom tools variant |
| `google/gemini-3.1-flash-lite` | Gemini 3.1 Flash Lite | 1M | Efficient |
| `google/gemini-3.1-flash-lite-preview` | Gemini 3.1 Flash Lite Preview | 1M | Preview |
| `google/gemini-3-flash-preview` | Gemini 3 Flash Preview | 1M | Preview |
| `google/gemini-2.5-pro` | Gemini 2.5 Pro | 1M | Stable Pro |
| `google/gemini-2.5-flash` | Gemini 2.5 Flash | 1M | Stable Flash |
| `google/gemini-2.5-flash-lite` | Gemini 2.5 Flash Lite | 1M | Stable light model |

Google image/audio:

| Natural language | Slug | Notes |
|---|---|---|
| Nano Banana Pro | `google/gemini-3-pro-image-preview` | Highest-quality Gemini image |
| Nano Banana 2 | `google/gemini-3.1-flash-image-preview` | New flash image |
| Nano Banana | `google/gemini-2.5-flash-image` | Stable image |
| Gemini Flash TTS | `google/gemini-3.1-flash-tts-preview` | TTS endpoint |

---

## 10. Meta Llama

| Slug | Display name | Context | Notes |
|---|---|---:|---|
| `meta-llama/llama-4-maverick` | Llama 4 Maverick | 1M | Flagship Llama 4 |
| `meta-llama/llama-4-scout` | Llama 4 Scout | 10M | Very large context |
| `meta-llama/llama-3.3-70b-instruct` | Llama 3.3 70B Instruct | 131K | Common open model |
| `meta-llama/llama-3.3-70b-instruct:free` | Llama 3.3 70B Instruct Free | 131K | Free variant |

---

## 11. DeepSeek

| Slug | Display name | Context | Notes |
|---|---|---:|---|
| `deepseek/deepseek-r1-0528` | R1 0528 | 163K | Preferred R1 dated version |
| `deepseek/deepseek-r1` | R1 | 163K | Base alias |
| `deepseek/deepseek-v4-pro` | DeepSeek V4 Pro | 1M | Latest V4 pro |
| `deepseek/deepseek-v4-flash` | DeepSeek V4 Flash | 1M | Fast V4 |
| `deepseek/deepseek-v4-flash:free` | DeepSeek V4 Flash Free | 1M | Free variant |
| `deepseek/deepseek-v3.2` | DeepSeek V3.2 | 131K | V3 chat |
| `deepseek/deepseek-v3.2-exp` | DeepSeek V3.2 Exp | 163K | Experimental |

---

## 12. MoonshotAI Kimi

| Slug | Display name | Context | Notes |
|---|---|---:|---|
| `moonshotai/kimi-k2.6` | Kimi K2.6 | 262K | Latest K2 |
| `moonshotai/kimi-k2.6:free` | Kimi K2.6 Free | 262K | Free variant |
| `moonshotai/kimi-k2.5` | Kimi K2.5 | 262K | Previous |
| `moonshotai/kimi-k2-thinking` | Kimi K2 Thinking | 262K | Thinking model |
| `moonshotai/kimi-k2-0905` | Kimi K2 0905 | 262K | Dated |
| `moonshotai/kimi-k2` | Kimi K2 0711 | 131K | Older |

Recommended for “kimi k2”: `moonshotai/kimi-k2.6`.

---

## 13. Mistral

| Slug | Display name | Context | Notes |
|---|---|---:|---|
| `mistralai/mistral-large-2512` | Mistral Large 3 2512 | 262K | Latest Large |
| `mistralai/mistral-medium-3-5` | Mistral Medium 3.5 | 262K | Slug uses `3-5` |
| `mistralai/mistral-medium-3.1` | Mistral Medium 3.1 | 131K | Previous medium |
| `mistralai/mistral-small-2603` | Mistral Small 4 | 262K | Latest Small |
| `mistralai/mistral-small-3.2-24b-instruct` | Mistral Small 3.2 24B | 128K | Small instruct |
| `mistralai/devstral-medium` | Devstral Medium | 131K | Code/dev specialist |
| `mistralai/devstral-2512` | Devstral 2 2512 | 262K | New Devstral |

---

## 14. xAI / Grok

| Slug | Display name | Context | Notes |
|---|---|---:|---|
| `x-ai/grok-4.3` | Grok 4.3 | 1M | Current Grok |
| `x-ai/grok-4.20` | Grok 4.20 | 2M | Large context |
| `x-ai/grok-4.20-multi-agent` | Grok 4.20 Multi-Agent | 2M | Multi-agent variant |
| `x-ai/grok-build-0.1` | Grok Build 0.1 | 256K | Build/coding oriented |

---

## 15. Qwen and routers

| Slug | Display name | Context | Notes |
|---|---|---:|---|
| `qwen/qwen3.7-max` | Qwen3.7 Max | 1M | Latest Max |
| `qwen/qwen3.6-flash` | Qwen3.6 Flash | 1M | Fast |
| `qwen/qwen3.6-plus` | Qwen3.6 Plus | 1M | Plus |
| `qwen/qwen3-coder` | Qwen3 Coder | 1M | Coder |
| `qwen/qwen3-coder:free` | Qwen3 Coder Free | 1M | Free variant |
| `openrouter/auto` | Auto Router | 2M | Let OpenRouter choose |
| `openrouter/free` | Free Models Router | 200K | Free router |
| `openrouter/pareto-code` | Pareto Code Router | 2M | Code router |

Use routers only when user explicitly wants automatic routing.

---

## 16. Multimodal generation

### Endpoint map

| Task | Endpoint | Notes |
|---|---|---|
| Image | `/api/v1/chat/completions` | Use `modalities: ["image", "text"]` when supported |
| Video | `/api/v1/videos` | Async submit+poll |
| TTS | `/api/v1/audio/speech` | Raw audio response |

### Image models

| Slug | Display name | Notes |
|---|---|---|
| `openai/gpt-5.4-image-2` | GPT-5.4 Image 2 | Top OpenAI image model |
| `openai/gpt-5-image` | GPT-5 Image | Image model |
| `openai/gpt-5-image-mini` | GPT-5 Image Mini | Efficient image model |
| `google/gemini-3-pro-image-preview` | Nano Banana Pro | Gemini Pro image |
| `google/gemini-3.1-flash-image-preview` | Nano Banana 2 | Gemini Flash image |
| `google/gemini-2.5-flash-image` | Nano Banana | Stable Gemini image |
| `bytedance-seed/seedream-4.5` | Seedream 4.5 | Portrait/composition image model |

### Video models

| Slug | Display name | Notes |
|---|---|---|
| `google/veo-3.1` | Veo 3.1 | High fidelity video |
| `google/veo-3.1-fast` | Veo 3.1 Fast | Faster/lower cost |
| `bytedance/seedance-2.0` | Seedance 2.0 | Character/camera control |
| `bytedance/seedance-2.0-fast` | Seedance 2.0 Fast | Faster/lower cost |

Video models may not appear in `/api/v1/models`; resolver includes static media fallbacks.

### Speech / TTS models

| Slug | Display name | Notes |
|---|---|---|
| `google/gemini-3.1-flash-tts-preview` | Gemini 3.1 Flash TTS Preview | TTS endpoint |
| `openai/gpt-audio` | GPT Audio | Audio/speech |
| `openai/gpt-audio-mini` | GPT Audio Mini | Efficient audio/speech |

---

## 17. Minimal call checklist

1. Resolve:
   ```bash
   python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "MODEL REQUEST"
   ```
2. Require `STATUS=OK`.
3. Paste `USE_SLUG` exactly into request body.
4. Use correct endpoint for modality.
5. Check HTTP errors.
6. Check `finish_reason`.
7. Check `result["model"]` for unexpected fallback/routing.

## Server Tools Reference

Server tools are passed in the `tools` array with `type` strings. OpenRouter executes them server-side.

| Tool type | Description | Key use case |
|---|---|---|
| `openrouter:web_search` | Real-time web search with citations | Current facts, news, live data |
| `openrouter:web_fetch` | Fetch and extract URL content | Read specific pages/docs |
| `openrouter:fusion` | Multi-model panel + judge analysis | High-stakes research, compare perspectives |
| `openrouter:advisor` | Consult a stronger model mid-generation | Guidance, review, architecture decisions |
| `openrouter:subagent` | Delegate subtasks to a worker model | Summarization, extraction, boilerplate |
| `openrouter:datetime` | Get current date/time | Temporal context |
| `openrouter:image_generation` | Generate images from text | In-chat image creation |
| `openrouter:apply_patch` | Propose file edits via V4A diff | Code editing (Responses API only) |

### Enabling server tools

```python
data["tools"] = [
    {"type": "openrouter:web_search"},                          # basic
    {"type": "openrouter:fusion"},                              # basic
    {"type": "openrouter:advisor", "parameters": {             # with params
        "model": "~anthropic/claude-opus-latest",
        "tools": [{"type": "openrouter:web_search"}]
    }},
    {"type": "openrouter:subagent", "parameters": {            # with params
        "model": "~anthropic/claude-haiku-latest",
        "tools": [{"type": "openrouter:web_search"}]
    }},
]
```

### Workflow combinations

| Goal | Tools combination |
|---|---|
| Grounded research answer | `web_search` |
| Multi-perspective analysis | `fusion` (already includes `web_search` + `web_fetch` on panel) |
| Cheap model + expert guidance | `advisor` with strong advisor model |
| Parallel subtask delegation | `subagent` with fast worker model |
| Research + expert review | `web_search` + `advisor` |
| Many research subtasks | `subagent` with nested `web_search` |

See SKILL.md states S10-S13 for full Python templates and parameter tables.
