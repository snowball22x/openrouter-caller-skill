# OpenRouter Model Slug Quick Reference

This file is a curated quick-reference. The resolver is authoritative.

```bash
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "claude sonnet 4.6"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list anthropic
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list "~"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --refresh
```

---

## 1. Resolver contract

Use the resolver before every call.

| Resolver output | Meaning | Action |
|---|---|---|
| `STATUS=OK` | Resolved/validated | Use `USE_SLUG` exactly |
| `STATUS=UNVERIFIED` | Exact-looking slug passed through because live validation unavailable | Use only if acceptable |
| `STATUS=AMBIGUOUS` | Top candidates are too close | Ask user / inspect candidates |
| `STATUS=ERROR` | No safe slug | Do not call |

---

## 2. Slug format

```text
provider/model-name[:suffix]
~provider/model-family-latest[:suffix]
```

Examples:

```text
anthropic/claude-sonnet-4.6
anthropic/claude-sonnet-4.6:nitro
~anthropic/claude-sonnet-latest
~google/gemini-flash-latest:floor
```

---

## 3. Suffix modifiers

| Suffix | Effect |
|---|---|
| `:nitro` | Fastest provider routing |
| `:floor` | Cheapest provider routing |
| `:free` | Free-tier providers only |
| `:thinking` | Extended reasoning/thinking routing when supported |
| `:extended` | Extended context routing when supported |
| `:exacto` | Quality-first routing for reliability/tool use |
| `:online` | Deprecated; prefer OpenRouter web search tooling when available |

Suffixes can be appended to normal and tilde slugs.

---

## 4. Common confusions

| User says | Correct slug | Avoid | Reason |
|---|---|---|---|
| `claude sonnet 4.6` | `anthropic/claude-sonnet-4.6` | guessed dash variants | Version uses dot |
| `claude opus 4.7` | `anthropic/claude-opus-4.7` | `anthropic/claude-opus-4` | User specified 4.7 |
| `claude opus latest` | `~anthropic/claude-opus-latest` | guessing latest numbered release | Latest alias is explicit |
| `sonar pro search` | `perplexity/sonar-pro-search` | `perplexity/sonar-pro` | Different products |
| `gpt-4.1` | `openai/gpt-4.1` | `openai/gpt-4.1-mini`, `openai/gpt-4.1-nano` | Mini/nano are distinct |
| `gemini 2.5 pro` | `google/gemini-2.5-pro` | preview unless requested | Stable requested |
| `gemini flash latest` | `~google/gemini-flash-latest` | `google/gemini-flash-latest` | Tilde alias required |
| `deepseek r1` | `deepseek/deepseek-r1-0528` | `deepseek/deepseek-r1` | Dated version preferred |
| `kimi k2` | `moonshotai/kimi-k2.6` | old `kimi-k2` | Latest K2 line |
| `mistral medium 3.5` | `mistralai/mistral-medium-3-5` | dot slug | Slug uses `3-5` |
| `nano banana pro` | `google/gemini-3-pro-image-preview` | flash image variants | Pro image model |

---

## 5. Tilde latest aliases

Use when the user explicitly says “latest” without a version.

| Natural language | Slug | Context |
|---|---|---:|
| Claude Sonnet latest | `~anthropic/claude-sonnet-latest` | 1M |
| Claude Opus latest | `~anthropic/claude-opus-latest` | 1M |
| Claude Haiku latest | `~anthropic/claude-haiku-latest` | 200K |
| Gemini Flash latest | `~google/gemini-flash-latest` | 1M |
| Gemini Pro latest | `~google/gemini-pro-latest` | 1M |
| GPT latest | `~openai/gpt-latest` | 1.05M |
| GPT Mini latest | `~openai/gpt-mini-latest` | 400K |
| Kimi latest | `~moonshotai/kimi-latest` | 262K |

Rules:
- Tilde prefix `~` is part of the slug.
- Latest alias target may change over time.
- Tilde aliases work with suffixes, e.g. `~openai/gpt-latest:nitro`.
- If the user says only “Claude latest” or “Gemini latest”, resolver may return `STATUS=AMBIGUOUS`; ask which family.

---

## 6. Anthropic Claude

| Slug | Display name | Context | Notes |
|---|---|---:|---|
| `anthropic/claude-sonnet-4.6` | Claude Sonnet 4.6 | 1M | Latest Sonnet |
| `anthropic/claude-sonnet-4.5` | Claude Sonnet 4.5 | 1M | Previous Sonnet |
| `anthropic/claude-opus-4.8` | Claude Opus 4.8 | 1M | Latest Opus |
| `anthropic/claude-opus-4.8-fast` | Claude Opus 4.8 Fast | 1M | Faster/higher-cost variant |
| `anthropic/claude-opus-4.7` | Claude Opus 4.7 | 1M | Previous Opus |
| `anthropic/claude-opus-4.6` | Claude Opus 4.6 | 1M | Older Opus |
| `anthropic/claude-haiku-4.5` | Claude Haiku 4.5 | 200K | Fast/low cost |
| `anthropic/claude-3.5-haiku` | Claude 3.5 Haiku | 200K | Legacy |

Recommended:
- Specific reproducible Sonnet: `anthropic/claude-sonnet-4.6`
- Latest Sonnet alias: `~anthropic/claude-sonnet-latest`
- Latest Opus alias: `~anthropic/claude-opus-latest`

---

## 7. Perplexity

| Slug | Display name | Context | Notes |
|---|---|---:|---|
| `perplexity/sonar-pro-search` | Sonar Pro Search | 200K | Agentic multi-step search |
| `perplexity/sonar-pro` | Sonar Pro | 200K | Standard search |
| `perplexity/sonar-reasoning-pro` | Sonar Reasoning Pro | 128K | Reasoning + search |
| `perplexity/sonar-deep-research` | Sonar Deep Research | 128K | Deep research workflow |
| `perplexity/sonar` | Sonar | 127K | Lightweight |

Key distinction: `sonar-pro-search` is not the same as `sonar-pro`.

---

## 8. OpenAI

| Slug | Display name | Context | Notes |
|---|---|---:|---|
| `openai/gpt-5.5` | GPT-5.5 | 1.05M | Latest flagship |
| `openai/gpt-5.5-pro` | GPT-5.5 Pro | 1.05M | Higher capability/cost |
| `openai/gpt-5.4` | GPT-5.4 | 1.05M | Previous flagship |
| `openai/gpt-5.4-pro` | GPT-5.4 Pro | 1.05M | Previous pro |
| `openai/gpt-5.4-mini` | GPT-5.4 Mini | 400K | Efficient |
| `openai/gpt-5.4-nano` | GPT-5.4 Nano | 400K | Smallest/fastest |
| `openai/gpt-4.1` | GPT-4.1 | 1.047M | Exact base; not mini/nano |
| `openai/gpt-4.1-mini` | GPT-4.1 Mini | 1.047M | Efficient |
| `openai/gpt-4.1-nano` | GPT-4.1 Nano | 1.047M | Smallest |
| `openai/o3` | o3 | 200K | Reasoning |
| `openai/o3-pro` | o3 Pro | 200K | Higher reasoning quality |
| `openai/o4-mini` | o4 Mini | 200K | Fast reasoning |
| `openai/o4-mini-high` | o4 Mini High | 200K | Higher effort |

OpenAI image/audio:

| Slug | Modality | Notes |
|---|---|---|
| `openai/gpt-5.4-image-2` | text/image → image/text | Top image model |
| `openai/gpt-5-image` | text/image → image/text | Image generation |
| `openai/gpt-5-image-mini` | text/image → image/text | Efficient image model |
| `openai/gpt-audio` | text/audio → text/audio | Audio/speech |
| `openai/gpt-audio-mini` | text/audio → text/audio | Efficient audio/speech |

---

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