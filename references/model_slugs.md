# OpenRouter Model Slug Quick Reference

## 1. Resolver Contract

| resolver output | action |
|---|---|
| `STATUS=OK` | use `USE_SLUG` exactly |
| `STATUS=UNVERIFIED` | use only for exact-looking user slug when live validation unavailable |
| `STATUS=AMBIGUOUS` | do not call; ask user or inspect candidates |
| `STATUS=ERROR` | do not call |

| command | purpose |
|---|---|
| `python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "MODEL REQUEST"` | resolve any model text |
| `python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list` | list full live/cache/static set |
| `python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list anthropic` | provider filter |
| `python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list "~"` | latest aliases |
| `python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --refresh` | refresh live model cache |

## 2. Slug Format

| format | example |
|---|---|
| exact | `anthropic/claude-sonnet-5` |
| exact + suffix | `openai/gpt-5.5:exacto` |
| tilde latest alias | `~anthropic/claude-sonnet-latest` |
| tilde + suffix | `~openai/gpt-latest:nitro` |

## 3. Suffixes

| suffix | effect |
|---|---|
| `:nitro` | fastest provider routing |
| `:floor` | cheapest provider routing |
| `:free` | free-tier providers only |
| `:thinking` | reasoning/thinking routing when supported |
| `:extended` | extended-context routing when supported |
| `:exacto` | quality-first routing for reliability/tool use |
| `:online` | deprecated; prefer `openrouter:web_search` |

## 4. Common Confusions

| user says | correct action | avoid |
|---|---|---|
| `latest sonnet` | `~anthropic/claude-sonnet-latest` | non-tilde latest slug |
| `claude latest` | ask family or inspect candidates | silently choosing Sonnet |
| `claude 3.7 sonnet` | error/not in supplied live list | remapping to 4.x silently |
| `sonar pro search` | `perplexity/sonar-pro-search` | `perplexity/sonar-pro` |
| `gpt latest` | `~openai/gpt-latest` | `openai/gpt-latest` |
| `gemini flash latest` | `~google/gemini-flash-latest` | `google/gemini-flash-latest` |
| `deepseek r1` | `deepseek/deepseek-r1-0528` | undated if reproducibility matters |
| `deepseek r2` | error/not in supplied live list | inventing `deepseek-r2` |
| `kimi k2` | `moonshotai/kimi-k2.6` | old `moonshotai/kimi-k2` |
| `mistral medium 3.5` | `mistralai/mistral-medium-3-5` | dot slug |
| `nano banana pro` | `google/gemini-3-pro-image` | flash image variants |
| `grok 3` | error/not in supplied live list | mapping to `grok-4.3` silently |
| current/search | add `openrouter:web_search` | `:online` |

## 5. Tilde Latest Aliases

| natural language | slug | context | max output |
|---|---|---:|---:|
| Claude Sonnet latest | `~anthropic/claude-sonnet-latest` | 1,000,000 | 128,000 |
| Claude Opus latest | `~anthropic/claude-opus-latest` | 1,000,000 | 128,000 |
| Claude Haiku latest | `~anthropic/claude-haiku-latest` | 200,000 | 64,000 |
| Claude Fable latest | `~anthropic/claude-fable-latest` | 1,000,000 | 128,000 |
| Gemini Flash latest | `~google/gemini-flash-latest` | 1,048,576 | 65,536 |
| Gemini Pro latest | `~google/gemini-pro-latest` | 1,048,576 | 65,536 |
| GPT latest | `~openai/gpt-latest` | 1,050,000 | 128,000 |
| GPT Mini latest | `~openai/gpt-mini-latest` | 400,000 | 128,000 |
| Kimi latest | `~moonshotai/kimi-latest` | 262,144 | 262,144 |

## 6. Anthropic Claude

| slug | display | context | max output |
|---|---|---:|---:|
| `anthropic/claude-sonnet-5` | Claude Sonnet 5 | 1,000,000 | 128,000 |
| `anthropic/claude-fable-5` | Claude Fable 5 | 1,000,000 | 128,000 |
| `anthropic/claude-sonnet-4.6` | Claude Sonnet 4.6 | 1,000,000 | 128,000 |
| `anthropic/claude-sonnet-4.5` | Claude Sonnet 4.5 | 1,000,000 | 64,000 |
| `anthropic/claude-sonnet-4` | Claude Sonnet 4 | 1,000,000 | 64,000 |
| `anthropic/claude-opus-4.8` | Claude Opus 4.8 | 1,000,000 | 128,000 |
| `anthropic/claude-opus-4.8-fast` | Claude Opus 4.8 Fast | 1,000,000 | 128,000 |
| `anthropic/claude-opus-4.7` | Claude Opus 4.7 | 1,000,000 | 128,000 |
| `anthropic/claude-opus-4.7-fast` | Claude Opus 4.7 Fast | 1,000,000 | 128,000 |
| `anthropic/claude-opus-4.6` | Claude Opus 4.6 | 1,000,000 | 128,000 |
| `anthropic/claude-opus-4.5` | Claude Opus 4.5 | 200,000 | 64,000 |
| `anthropic/claude-opus-4.1` | Claude Opus 4.1 | 200,000 | 32,000 |
| `anthropic/claude-opus-4` | Claude Opus 4 | 200,000 | 32,000 |
| `anthropic/claude-haiku-4.5` | Claude Haiku 4.5 | 200,000 | 64,000 |
| `anthropic/claude-3-haiku` | Claude 3 Haiku | 200,000 | 4,096 |

| recommended use | slug |
|---|---|
| reproducible current Sonnet | `anthropic/claude-sonnet-5` |
| latest Sonnet alias | `~anthropic/claude-sonnet-latest` |
| strong advisor/judge | `~anthropic/claude-opus-latest` |
| fast/cheap worker | `~anthropic/claude-haiku-latest` |

## 7. OpenAI

| slug | display | context | max output |
|---|---|---:|---:|
| `openai/gpt-5.5` | GPT-5.5 | 1,050,000 | 128,000 |
| `openai/gpt-5.5-pro` | GPT-5.5 Pro | 1,050,000 | 128,000 |
| `openai/gpt-5.4` | GPT-5.4 | 1,050,000 | 128,000 |
| `openai/gpt-5.4-pro` | GPT-5.4 Pro | 1,050,000 | 128,000 |
| `openai/gpt-5.4-mini` | GPT-5.4 Mini | 400,000 | 128,000 |
| `openai/gpt-5.4-nano` | GPT-5.4 Nano | 400,000 | 128,000 |
| `openai/gpt-5.4-image-2` | GPT-5.4 Image 2 | 272,000 | 128,000 |
| `openai/gpt-5.3-chat` | GPT-5.3 Chat | 128,000 | 16,384 |
| `openai/gpt-5.3-codex` | GPT-5.3 Codex | 400,000 | 128,000 |
| `openai/gpt-5.2` | GPT-5.2 | 400,000 | 128,000 |
| `openai/gpt-5.2-chat` | GPT-5.2 Chat | 128,000 | 16,384 |
| `openai/gpt-5.2-pro` | GPT-5.2 Pro | 400,000 | 128,000 |
| `openai/gpt-5.2-codex` | GPT-5.2 Codex | 400,000 | 128,000 |
| `openai/gpt-5.1` | GPT-5.1 | 400,000 | 128,000 |
| `openai/gpt-5.1-chat` | GPT-5.1 Chat | 128,000 | 32,000 |
| `openai/gpt-5.1-codex` | GPT-5.1 Codex | 400,000 | 128,000 |
| `openai/gpt-5.1-codex-max` | GPT-5.1 Codex Max | 400,000 | 128,000 |
| `openai/gpt-5.1-codex-mini` | GPT-5.1 Codex Mini | 400,000 | 100,000 |
| `openai/gpt-5` | GPT-5 | 400,000 | 128,000 |
| `openai/gpt-5-chat` | GPT-5 Chat | 128,000 | 16,384 |
| `openai/gpt-5-pro` | GPT-5 Pro | 400,000 | 128,000 |
| `openai/gpt-5-mini` | GPT-5 Mini | 400,000 | 128,000 |
| `openai/gpt-5-nano` | GPT-5 Nano | 400,000 | ? |
| `openai/gpt-5-codex` | GPT-5 Codex | 400,000 | 128,000 |
| `openai/gpt-5-image` | GPT-5 Image | 400,000 | 128,000 |
| `openai/gpt-5-image-mini` | GPT-5 Image Mini | 400,000 | 128,000 |
| `openai/gpt-chat-latest` | GPT Chat Latest | 400,000 | 128,000 |
| `openai/gpt-4.1` | GPT-4.1 | 1,047,576 | ? |
| `openai/gpt-4.1-mini` | GPT-4.1 Mini | 1,047,576 | 32,768 |
| `openai/gpt-4.1-nano` | GPT-4.1 Nano | 1,047,576 | 32,768 |
| `openai/o3` | o3 | 200,000 | 100,000 |
| `openai/o3-pro` | o3 Pro | 200,000 | 100,000 |
| `openai/o3-mini` | o3 Mini | 200,000 | 100,000 |
| `openai/o3-mini-high` | o3 Mini High | 200,000 | 100,000 |
| `openai/o3-deep-research` | o3 Deep Research | 200,000 | 100,000 |
| `openai/o4-mini` | o4 Mini | 200,000 | 100,000 |
| `openai/o4-mini-high` | o4 Mini High | 200,000 | 100,000 |
| `openai/o4-mini-deep-research` | o4 Mini Deep Research | 200,000 | 100,000 |
| `openai/o1` | o1 | 200,000 | 100,000 |
| `openai/o1-pro` | o1 Pro | 200,000 | 100,000 |
| `openai/gpt-audio` | GPT Audio | 128,000 | 16,384 |
| `openai/gpt-audio-mini` | GPT Audio Mini | 128,000 | 16,384 |


## 8. Google Gemini

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

## 9. Meta Llama

| Slug | Display name | Context | Notes |
|---|---|---:|---|
| `meta-llama/llama-4-maverick` | Llama 4 Maverick | 1M | Flagship Llama 4 |
| `meta-llama/llama-4-scout` | Llama 4 Scout | 10M | Very large context |
| `meta-llama/llama-3.3-70b-instruct` | Llama 3.3 70B Instruct | 131K | Common open model |
| `meta-llama/llama-3.3-70b-instruct:free` | Llama 3.3 70B Instruct Free | 131K | Free variant |

---

## 10. DeepSeek

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

## 11. MoonshotAI Kimi

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

## 12. Mistral

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

## 13. xAI / Grok

| Slug | Display name | Context | Notes |
|---|---|---:|---|
| `x-ai/grok-4.3` | Grok 4.3 | 1M | Current Grok |
| `x-ai/grok-4.20` | Grok 4.20 | 2M | Large context |
| `x-ai/grok-4.20-multi-agent` | Grok 4.20 Multi-Agent | 2M | Multi-agent variant |
| `x-ai/grok-build-0.1` | Grok Build 0.1 | 256K | Build/coding oriented |

---

## 14. Qwen and routers

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

## 15. Multimodal generation

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

## 16. Minimal call checklist

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
