# OpenRouter Model Slug Quick Reference

Last proofchecked: 2026-07-05. OpenRouter's `/models`, `/images/models`, `/videos/models`, and audio model availability change frequently. **Prefer the resolver and live cache over this document whenever they disagree.**

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
| exact + suffix chain | `openai/gpt-oss-120b:free:nitro` |
| tilde latest alias | `~anthropic/claude-sonnet-latest` |
| tilde + suffix | `~openai/gpt-latest:nitro` |

## 3. Suffixes

| suffix | effect |
|---|---|
| `:nitro` | fastest provider routing |
| `:floor` | cheapest provider routing |
| `:free` | free-tier providers only, where a free variant exists |
| `:thinking` | reasoning/thinking routing when supported |
| `:extended` | extended-context routing when supported |
| `:exacto` | quality-first routing for reliability/tool use |
| `:online` | legacy/deprecated search suffix; prefer server tool `openrouter:web_search` |

## 4. Reasoning Parameter Rules

Use the model metadata from `GET /api/v1/models` when available.

| metadata / case | correct handling |
|---|---|
| model has no `reasoning` object | omit `reasoning`, `include_reasoning`, and `reasoning_effort` unless the user explicitly requests and you have verified support |
| `reasoning.mandatory=true` | do not send `reasoning: {"effort":"none"}` or disable reasoning |
| `reasoning.supported_efforts` present | only send one of those effort strings (`max`, `xhigh`, `high`, `medium`, `low`, `minimal`, `none`) |
| `reasoning.supports_max_tokens=true` | `reasoning.max_tokens` may be used; otherwise prefer `reasoning.effort` |
| Claude 4.6+ / 5 family | supports OpenRouter reasoning controls; preserve `reasoning_details` across multi-turn tool calls |
| OpenAI GPT-5 / o-series | supports reasoning effort where exposed; some Pro models require reasoning |
| Gemini thinking/image models | often have mandatory or default-on reasoning; check metadata |
| Qwen thinking / some Qwen 3.x | reasoning support varies by slug; check metadata |
| DeepSeek R1/V4 | reasoning models; include reasoning only if caller wants trace/control and metadata allows |
| xAI Grok 4/4.x | reasoning behavior varies by model; some expose enable/effort, older `x-ai/grok-4` reasoning is not controllable |
| Nemotron 3 Ultra | exposes reasoning controls; do not blanket-omit reasoning |

## 5. Common Confusions

| user says | correct action | avoid |
|---|---|---|
| `latest sonnet` | `~anthropic/claude-sonnet-latest` | non-tilde latest slug |
| `claude latest` | ask family or inspect candidates | silently choosing Sonnet |
| `claude fable latest` | `~anthropic/claude-fable-latest` | mapping to Sonnet/Opus |
| `fable 5` | `anthropic/claude-fable-5` | `claude-sonnet-5` |
| `opus fast` / `opus 4.8 fast` | `anthropic/claude-opus-4.8-fast` | regular `anthropic/claude-opus-4.8` if speed requested |
| `claude 3.7 sonnet` | `anthropic/claude-3.7-sonnet` if resolver confirms; otherwise ask | remapping to 4.x/5 silently |
| `sonar pro search` | `perplexity/sonar-pro-search` | `perplexity/sonar-pro` |
| `gpt latest` | `~openai/gpt-latest` | `openai/gpt-latest` |
| `gpt mini latest` | `~openai/gpt-mini-latest` | pinning an old mini |
| `gpt 5.5 pro` | `openai/gpt-5.5-pro` | `openai/gpt-5.5` |
| `gpt image 2` | `openai/gpt-image-2` via `/api/v1/images` | `openai/gpt-5.4-image-2` unless user said GPT-5.4 |
| `gpt 5.4 image 2` | `openai/gpt-5.4-image-2` | plain `openai/gpt-image-2` |
| `gemini flash latest` | `~google/gemini-flash-latest` | `google/gemini-flash-latest` |
| `gemini pro latest` | `~google/gemini-pro-latest` | hard-coding the current Pro |
| `gemini 3.5 flash` | `google/gemini-3.5-flash` | older `gemini-2.5-flash` |
| `lyria` / `music generation` | `google/lyria-3-pro-preview` or `google/lyria-3-clip-preview` | Gemini text/chat models |
| `deepseek r1` | prefer dated `deepseek/deepseek-r1-0528` for reproducibility | undated alias if repeatability matters |
| `deepseek v4` | ask Pro vs Flash if behavior/cost matters | silently choosing one for critical work |
| `deepseek v4 free` | verify with resolver; do not invent free variants | `deepseek-v4-*:free` unless listed |
| `kimi k2` | `moonshotai/kimi-k2.6` unless user asked coding | old `moonshotai/kimi-k2` |
| `kimi code` / `kimi k2.7 code` | `moonshotai/kimi-k2.7-code` | `moonshotai/kimi-k2.6` |
| `kimi latest` | `~moonshotai/kimi-latest` | pinning old K2 |
| `mistral medium 3.5` | `mistralai/mistral-medium-3-5` | dot slug |
| `codestral` | `mistralai/codestral-2508` | older Codestral slugs |
| `devstral` | `mistralai/devstral-2512` | nonexistent `devstral-medium` unless live list later adds it |
| `voxtral` | `mistralai/voxtral-small-24b-2507` for audio input understanding | treating it as TTS output |
| `voxtral tts` | `mistralai/voxtral-mini-tts-2603` if live resolver confirms | `voxtral-small-24b-2507` |
| `nano banana pro` | `google/gemini-3-pro-image` | Flash image variants |
| `nano banana 2` | `google/gemini-3.1-flash-image` | Gemini 3 Pro image |
| `seedream` | `bytedance-seed/seedream-4.5` via `/api/v1/images` | `bytedance/seedream-*` |
| `grok image` / `grok imagine` | `x-ai/grok-imagine-image-quality` via `/api/v1/images` | Grok chat models |
| `grok 3` | use `x-ai/grok-3` only if resolver confirms | mapping to Grok 4.x silently |
| `grok 4.20 multi agent` | `x-ai/grok-4.20-multi-agent` | regular `x-ai/grok-4.20` |
| `grok 4 latest` | ask exact 4 Fast vs 4.20 vs multi-agent vs old Grok 4 | guessing by decimal/version |
| `qwen 3.7 max` | `qwen/qwen3.7-max` | `qwen/qwen3.6-max-preview` |
| `qwen 3.7 plus` | `qwen/qwen3.7-plus` | `qwen/qwen3.6-plus` |
| `qwen max thinking` | `qwen/qwen3-max-thinking` | `qwen/qwen3.7-max` unless user asked 3.7 |
| current/search/live/news | add server tool `openrouter:web_search` | `:online` |

## 6. Tilde Latest Aliases

These are resolver aliases and should be kept in the live alias table.

| natural language | slug | typical current target family | context | max output |
|---|---|---|---:|---:|
| Claude Sonnet latest | `~anthropic/claude-sonnet-latest` | latest Claude Sonnet | 1,000,000 | 128,000 |
| Claude Opus latest | `~anthropic/claude-opus-latest` | latest Claude Opus | 1,000,000 | 128,000 |
| Claude Haiku latest | `~anthropic/claude-haiku-latest` | latest Claude Haiku | 200,000 | 64,000 |
| Claude Fable latest | `~anthropic/claude-fable-latest` | latest Claude Fable | 1,000,000 | 128,000 |
| Gemini Flash latest | `~google/gemini-flash-latest` | latest Gemini Flash | 1,048,576 | 65,536 |
| Gemini Pro latest | `~google/gemini-pro-latest` | latest Gemini Pro | 1,048,576 | 65,536 |
| GPT latest | `~openai/gpt-latest` | latest OpenAI GPT | 1,050,000 | 128,000 |
| GPT Mini latest | `~openai/gpt-mini-latest` | latest OpenAI GPT Mini | 400,000 | 128,000 |
| Kimi latest | `~moonshotai/kimi-latest` | latest MoonshotAI Kimi | 262,144 | 262,144 |

## 7. Anthropic Claude

| slug | display | context | max output | reasoning notes |
|---|---|---:|---:|---|
| `anthropic/claude-sonnet-5` | Claude Sonnet 5 | 1,000,000 | 128,000 | optional reasoning; efforts include `xhigh/high/medium/low` and may include `max` |
| `anthropic/claude-fable-5` | Claude Fable 5 | 1,000,000 | 128,000 | mandatory reasoning |
| `anthropic/claude-sonnet-4.6` | Claude Sonnet 4.6 | 1,000,000 | 128,000 | supports reasoning |
| `anthropic/claude-sonnet-4.5` | Claude Sonnet 4.5 | 1,000,000 | 64,000 | supports reasoning |
| `anthropic/claude-sonnet-4` | Claude Sonnet 4 | 1,000,000 | 64,000 | supports reasoning |
| `anthropic/claude-opus-4.8` | Claude Opus 4.8 | 1,000,000 | 128,000 | supports reasoning |
| `anthropic/claude-opus-4.8-fast` | Claude Opus 4.8 Fast | 1,000,000 | 128,000 | same capability, faster/premium |
| `anthropic/claude-opus-4.7` | Claude Opus 4.7 | 1,000,000 | 128,000 | supports reasoning |
| `anthropic/claude-opus-4.7-fast` | Claude Opus 4.7 Fast | 1,000,000 | 128,000 | same capability, faster/premium |
| `anthropic/claude-opus-4.6` | Claude Opus 4.6 | 1,000,000 | 128,000 | supports reasoning |
| `anthropic/claude-opus-4.6-fast` | Claude Opus 4.6 Fast | 1,000,000 | 128,000 | legacy/expiry-prone; prefer 4.8 fast |
| `anthropic/claude-opus-4.5` | Claude Opus 4.5 | 200,000 | 64,000 | supports reasoning/verbosity |
| `anthropic/claude-opus-4.1` | Claude Opus 4.1 | 200,000 | 32,000 | supports reasoning |
| `anthropic/claude-opus-4` | Claude Opus 4 | 200,000 | 32,000 | supports reasoning |
| `anthropic/claude-haiku-4.5` | Claude Haiku 4.5 | 200,000 | 64,000 | supports reasoning |
| `anthropic/claude-3.7-sonnet` | Claude 3.7 Sonnet | 200,000 | 64,000 | legacy hybrid reasoning; verify live |
| `anthropic/claude-3.5-sonnet` | Claude 3.5 Sonnet | 200,000 | 8,192 | legacy |
| `anthropic/claude-3-haiku` | Claude 3 Haiku | 200,000 | 4,096 | no modern reasoning controls |

| recommended use | slug |
|---|---|
| reproducible current Sonnet | `anthropic/claude-sonnet-5` |
| latest Sonnet alias | `~anthropic/claude-sonnet-latest` |
| autonomous long-horizon knowledge/coding work | `anthropic/claude-fable-5` |
| latest Fable alias | `~anthropic/claude-fable-latest` |
| strong advisor/judge | `~anthropic/claude-opus-latest` |
| fastest Opus 4.8 routing | `anthropic/claude-opus-4.8-fast` |
| fast/cheap worker | `~anthropic/claude-haiku-latest` |

## 8. OpenAI

| slug | display | context | max output | reasoning notes |
|---|---|---:|---:|---|
| `openai/gpt-5.5` | GPT-5.5 | 1,050,000 | 128,000 | optional/default-on reasoning; supports efforts |
| `openai/gpt-5.5-pro` | GPT-5.5 Pro | 1,050,000 | 128,000 | high-capability; reasoning may be mandatory |
| `openai/gpt-5.4` | GPT-5.4 | 1,050,000 | 128,000 | supports reasoning |
| `openai/gpt-5.4-pro` | GPT-5.4 Pro | 1,050,000 | 128,000 | high-capability; supports reasoning |
| `openai/gpt-5.4-mini` | GPT-5.4 Mini | 400,000 | 128,000 | supports reasoning |
| `openai/gpt-5.4-nano` | GPT-5.4 Nano | 400,000 | 128,000 | supports reasoning where metadata says so |
| `openai/gpt-5.4-image-2` | GPT-5.4 Image 2 | 272,000 | 128,000 | text+image output; use chat/image modality correctly |
| `openai/gpt-5.3-chat` | GPT-5.3 Chat | 128,000 | 16,384 | chat-optimized |
| `openai/gpt-5.3-codex` | GPT-5.3 Codex | 400,000 | 128,000 | coding |
| `openai/gpt-5.2` | GPT-5.2 | 400,000 | 128,000 | supports reasoning |
| `openai/gpt-5.2-chat` | GPT-5.2 Chat | 128,000 | 16,384 | chat-optimized |
| `openai/gpt-5.2-pro` | GPT-5.2 Pro | 400,000 | 128,000 | high-capability |
| `openai/gpt-5.2-codex` | GPT-5.2 Codex | 400,000 | 128,000 | coding |
| `openai/gpt-5.1` | GPT-5.1 | 400,000 | 128,000 | supports reasoning |
| `openai/gpt-5.1-chat` | GPT-5.1 Chat | 128,000 | 32,000 | chat-optimized |
| `openai/gpt-5.1-codex` | GPT-5.1 Codex | 400,000 | 128,000 | coding |
| `openai/gpt-5.1-codex-max` | GPT-5.1 Codex Max | 400,000 | 128,000 | coding |
| `openai/gpt-5.1-codex-mini` | GPT-5.1 Codex Mini | 400,000 | 100,000 | coding |
| `openai/gpt-5` | GPT-5 | 400,000 | 128,000 | supports reasoning |
| `openai/gpt-5-chat` | GPT-5 Chat | 128,000 | 16,384 | chat-optimized |
| `openai/gpt-5-pro` | GPT-5 Pro | 400,000 | 128,000 | high-capability |
| `openai/gpt-5-mini` | GPT-5 Mini | 400,000 | 128,000 | efficient |
| `openai/gpt-5-nano` | GPT-5 Nano | 400,000 | ? | efficient; verify max output live |
| `openai/gpt-5-codex` | GPT-5 Codex | 400,000 | 128,000 | coding |
| `openai/gpt-5-image` | GPT-5 Image | 400,000 | 128,000 | image-capable |
| `openai/gpt-5-image-mini` | GPT-5 Image Mini | 400,000 | 128,000 | image-capable efficient |
| `openai/gpt-chat-latest` | GPT Chat Latest | 400,000 | 128,000 | stable chat alias; not same as `~openai/gpt-latest` |
| `openai/gpt-4.1` | GPT-4.1 | 1,047,576 | ? | legacy long-context |
| `openai/gpt-4.1-mini` | GPT-4.1 Mini | 1,047,576 | 32,768 | legacy efficient |
| `openai/gpt-4.1-nano` | GPT-4.1 Nano | 1,047,576 | 32,768 | legacy efficient |
| `openai/gpt-4o` | GPT-4o | 128,000 | 16,384 | multimodal legacy |
| `openai/gpt-4o-mini` | GPT-4o Mini | 128,000 | 16,384 | efficient legacy |
| `openai/gpt-4o-search-preview` | GPT-4o Search Preview | 128,000 | 16,384 | prefer server `openrouter:web_search` for new calls |
| `openai/gpt-4o-mini-search-preview` | GPT-4o Mini Search Preview | 128,000 | 16,384 | prefer server `openrouter:web_search` for new calls |
| `openai/o3` | o3 | 200,000 | 100,000 | reasoning |
| `openai/o3-pro` | o3 Pro | 200,000 | 100,000 | reasoning |
| `openai/o3-mini` | o3 Mini | 200,000 | 100,000 | reasoning |
| `openai/o3-mini-high` | o3 Mini High | 200,000 | 100,000 | high-effort convenience slug |
| `openai/o3-deep-research` | o3 Deep Research | 200,000 | 100,000 | research |
| `openai/o4-mini` | o4 Mini | 200,000 | 100,000 | reasoning |
| `openai/o4-mini-high` | o4 Mini High | 200,000 | 100,000 | high-effort convenience slug |
| `openai/o4-mini-deep-research` | o4 Mini Deep Research | 200,000 | 100,000 | research |
| `openai/o1` | o1 | 200,000 | 100,000 | reasoning |
| `openai/o1-pro` | o1 Pro | 200,000 | 100,000 | reasoning |
| `openai/gpt-audio` | GPT Audio | 128,000 | 16,384 | audio input/output via chat/responses |
| `openai/gpt-audio-mini` | GPT Audio Mini | 128,000 | 16,384 | efficient audio input/output |
| `openai/gpt-oss-120b` | gpt-oss-120b | 131,072 | 131,072 | open-weight |
| `openai/gpt-oss-120b:free` | gpt-oss-120b Free | 131,072 | 131,072 | free variant |
| `openai/gpt-oss-20b` | gpt-oss-20b | 131,072 | ? | open-weight; verify output limit |
| `openai/gpt-oss-20b:free` | gpt-oss-20b Free | 131,072 | 32,768 | free variant |
| `openai/gpt-oss-safeguard-20b` | gpt-oss-safeguard-20b | 131,072 | 65,536 | safeguard |

## 9. Google Gemini

| slug | display | context | max output | notes |
|---|---|---:|---:|---|
| `google/gemini-3.5-flash` | Gemini 3.5 Flash | 1,048,576 | 65,536 | latest Flash line; multimodal input |
| `google/gemini-3.1-pro-preview` | Gemini 3.1 Pro Preview | 1,048,576 | 65,536 | latest Pro preview |
| `google/gemini-3.1-pro-preview-customtools` | Gemini 3.1 Pro Preview Custom Tools | 1,048,576 | 65,536 | custom tools variant |
| `google/gemini-3.1-flash-lite` | Gemini 3.1 Flash Lite | 1,048,576 | 65,536 | efficient |
| `google/gemini-3.1-flash-lite-preview` | Gemini 3.1 Flash Lite Preview | 1,048,576 | 65,536 | preview |
| `google/gemini-3-flash-preview` | Gemini 3 Flash Preview | 1,048,576 | 65,535 | preview |
| `google/gemini-2.5-pro` | Gemini 2.5 Pro | 1,048,576 | 65,536 | stable Pro |
| `google/gemini-2.5-pro-preview` | Gemini 2.5 Pro Preview | 1,048,576 | 65,536 | older Pro preview |
| `google/gemini-2.5-pro-preview-05-06` | Gemini 2.5 Pro Preview 05-06 | 1,048,576 | 65,535 | older Pro preview |
| `google/gemini-2.5-flash` | Gemini 2.5 Flash | 1,048,576 | 65,535 | stable Flash |
| `google/gemini-2.5-flash-lite` | Gemini 2.5 Flash Lite | 1,048,576 | 65,535 | stable light model |
| `google/gemini-2.5-flash-lite-preview-09-2025` | Gemini 2.5 Flash Lite Preview 09-2025 | 1,048,576 | 65,535 | older preview |

Google image/audio:

| natural language | slug | context | max output | notes |
|---|---|---:|---:|---|
| Nano Banana Pro | `google/gemini-3-pro-image` | 65,536 | 32,768 | stable Gemini 3 Pro image; mandatory reasoning |
| Nano Banana Pro Preview | `google/gemini-3-pro-image-preview` | 65,536 | 32,768 | preview Gemini Pro image |
| Nano Banana 2 | `google/gemini-3.1-flash-image` | 131,072 | 32,768 | stable Gemini 3.1 Flash image |
| Nano Banana 2 Preview | `google/gemini-3.1-flash-image-preview` | 131,072 | 32,768 | preview Gemini Flash image |
| Nano Banana 2 Lite | `google/gemini-3.1-flash-lite-image` | 65,536 | 66,000 | efficient image |
| Nano Banana | `google/gemini-2.5-flash-image` | 32,768 | 32,768 | stable image |
| Lyria 3 Pro Preview | `google/lyria-3-pro-preview` | 1,048,576 | 65,536 | full-length music/audio generation |
| Lyria 3 Clip Preview | `google/lyria-3-clip-preview` | 1,048,576 | 65,536 | short clips/loops |
| Gemini Flash TTS | `google/gemini-3.1-flash-tts-preview` | 8,000 | n/a | TTS via `/api/v1/audio/speech`; text to speech |

## 10. Meta Llama

| slug | display | context | max output | notes |
|---|---|---:|---:|---|
| `meta-llama/llama-4-maverick` | Llama 4 Maverick | 1,000,000 | ? | flagship Llama 4 |
| `meta-llama/llama-4-scout` | Llama 4 Scout | 10,000,000 | ? | very large context |
| `meta-llama/llama-guard-4-12b` | Llama Guard 4 12B | 163,840 | ? | safety/guardrail, vision-capable |
| `meta-llama/llama-3.3-70b-instruct` | Llama 3.3 70B Instruct | 131,072 | ? | common open model |
| `meta-llama/llama-3.3-70b-instruct:free` | Llama 3.3 70B Instruct Free | 131,072 | ? | free variant |
| `meta-llama/llama-3.2-11b-vision-instruct` | Llama 3.2 11B Vision Instruct | 131,072 | ? | vision-capable |
| `meta-llama/llama-3.2-3b-instruct` | Llama 3.2 3B Instruct | 131,072 | ? | small |
| `meta-llama/llama-3.2-3b-instruct:free` | Llama 3.2 3B Instruct Free | 131,072 | ? | free variant |
| `meta-llama/llama-3.1-70b-instruct` | Llama 3.1 70B Instruct | 131,072 | ? | older |
| `meta-llama/llama-3.1-8b-instruct` | Llama 3.1 8B Instruct | 131,072 | ? | older |
| `meta-llama/llama-3-8b-instruct` | Llama 3 8B Instruct | 8,192 | ? | legacy |

## 11. DeepSeek

| slug | display | context | max output | notes |
|---|---|---:|---:|---|
| `deepseek/deepseek-v4-pro` | DeepSeek V4 Pro | 1,048,576 | 384,000 | latest V4 pro; long-context reasoning/coding |
| `deepseek/deepseek-v4-flash` | DeepSeek V4 Flash | 1,048,576 | ? | fast V4; verify output limit |
| `deepseek/deepseek-v3.2` | DeepSeek V3.2 | 131,072 | 64,000 | V3.2 chat/reasoning |
| `deepseek/deepseek-v3.2-exp` | DeepSeek V3.2 Exp | 163,840 | 65,536 | experimental |
| `deepseek/deepseek-v3.1-terminus` | DeepSeek V3.1 Terminus | 163,840 | 32,768 | V3.1 terminus |
| `deepseek/deepseek-chat-v3.1` | DeepSeek V3.1 | 163,840 | 32,768 | V3.1 chat |
| `deepseek/deepseek-chat-v3-0324` | DeepSeek V3 0324 | 163,840 | 16,384 | dated V3 |
| `deepseek/deepseek-chat` | DeepSeek V3 | 131,072 | 16,000 | base V3 alias |
| `deepseek/deepseek-r1-0528` | R1 0528 | 163,840 | 32,768 | preferred R1 dated version |
| `deepseek/deepseek-r1` | R1 | 163,840 | 16,000 | base alias |
| `deepseek/deepseek-r1-distill-llama-70b` | R1 Distill Llama 70B | 128,000 | 8,192 | distilled open model |

## 12. MoonshotAI Kimi

| slug | display | context | max output | notes |
|---|---|---:|---:|---|
| `moonshotai/kimi-k2.7-code` | Kimi K2.7 Code | 262,144 | 16,384 | latest coding-focused Kimi K2 variant; mandatory reasoning |
| `moonshotai/kimi-k2.6` | Kimi K2.6 | 262,144 | 262,144 | latest general K2 |
| `moonshotai/kimi-k2.6:free` | Kimi K2.6 Free | 262,144 | 262,144 | free variant if live resolver confirms |
| `moonshotai/kimi-k2.5` | Kimi K2.5 | 262,144 | ? | previous multimodal K2 |
| `moonshotai/kimi-k2-thinking` | Kimi K2 Thinking | 262,144 | 100,352 | thinking model |
| `moonshotai/kimi-k2-0905` | Kimi K2 0905 | 262,144 | 100,352 | dated |
| `moonshotai/kimi-k2` | Kimi K2 0711 | 131,072 | 100,352 | older |
| `~moonshotai/kimi-latest` | Kimi Latest | 262,144 | 262,144 | latest alias |

Recommended for “kimi k2”: `moonshotai/kimi-k2.6`.

Recommended for “kimi code” or “kimi k2.7”: `moonshotai/kimi-k2.7-code`.

Recommended for moving latest Kimi target: `~moonshotai/kimi-latest`.

## 13. Mistral

| slug | display | context | max output | notes |
|---|---|---:|---:|---|
| `mistralai/mistral-large-2512` | Mistral Large 3 2512 | 262,144 | ? | latest Large |
| `mistralai/mistral-large` | Mistral Large | 128,000 | ? | base large alias |
| `mistralai/mistral-large-2407` | Mistral Large 2407 | 131,072 | ? | older dated large |
| `mistralai/mistral-medium-3-5` | Mistral Medium 3.5 | 262,144 | ? | slug uses `3-5` |
| `mistralai/mistral-medium-3.1` | Mistral Medium 3.1 | 131,072 | ? | previous medium |
| `mistralai/mistral-medium-3` | Mistral Medium 3 | 131,072 | ? | older medium |
| `mistralai/mistral-small-2603` | Mistral Small 4 | 262,144 | ? | latest Small |
| `mistralai/mistral-small-3.2-24b-instruct` | Mistral Small 3.2 24B | 128,000 | 16,384 | small instruct |
| `mistralai/mistral-small-3.1-24b-instruct` | Mistral Small 3.1 24B | 128,000 | 128,000 | previous small instruct |
| `mistralai/mistral-small-24b-instruct-2501` | Mistral Small 3 | 32,768 | 16,384 | older small |
| `mistralai/devstral-2512` | Devstral 2 2512 | 262,144 | ? | agentic coding/dev specialist |
| `mistralai/codestral-2508` | Codestral 2508 | 256,000 | ? | code/FIM/correction/test generation |
| `mistralai/voxtral-small-24b-2507` | Voxtral Small 24B 2507 | 32,000 | ? | audio input speech transcription/translation/understanding |
| `mistralai/voxtral-mini-tts-2603` | Voxtral Mini TTS 2603 | n/a | n/a | TTS via `/api/v1/audio/speech`; verify live |
| `mistralai/ministral-14b-2512` | Ministral 3 14B 2512 | 262,144 | ? | small vision-capable Mistral |
| `mistralai/ministral-8b-2512` | Ministral 3 8B 2512 | 262,144 | ? | small vision-capable Mistral |
| `mistralai/ministral-3b-2512` | Ministral 3 3B 2512 | 131,072 | ? | small vision-capable Mistral |
| `mistralai/mistral-nemo` | Mistral Nemo | 131,072 | ? | efficient open model |
| `mistralai/mistral-saba` | Saba | 32,768 | ? | regional/language specialist |
| `mistralai/mixtral-8x22b-instruct` | Mixtral 8x22B Instruct | 65,536 | ? | legacy MoE |

## 14. xAI / Grok

| slug | display | context | max output | notes |
|---|---|---:|---:|---|
| `x-ai/grok-4.20` | Grok 4.20 | 2,000,000 | ? | flagship 4.20 |
| `x-ai/grok-4.20-multi-agent` | Grok 4.20 Multi-Agent | 2,000,000 | ? | multi-agent research/workflow variant |
| `x-ai/grok-4.1-fast` | Grok 4.1 Fast | 2,000,000 | ? | fast agentic/tool model |
| `x-ai/grok-4-fast` | Grok 4 Fast | 2,000,000 | ? | multimodal fast; reasoning can be enabled/disabled |
| `x-ai/grok-4` | Grok 4 | 256,000 | ? | older Grok 4; reasoning not user-controllable |
| `x-ai/grok-3` | Grok 3 | ? | ? | use only if resolver confirms live |
| `x-ai/grok-build-0.1` | Grok Build 0.1 | 256,000 | ? | build/coding oriented |
| `x-ai/grok-imagine-image-quality` | Grok Imagine Image Quality | 66,000 | n/a | image generation/editing via `/api/v1/images` |

## 15. Qwen and Routers

| slug | display | context | max output | notes |
|---|---|---:|---:|---|
| `qwen/qwen3.7-max` | Qwen3.7 Max | 1,000,000 | 65,536 | latest Max, text-only |
| `qwen/qwen3.7-plus` | Qwen3.7 Plus | 1,000,000 | 65,536 | latest Plus, text+image |
| `qwen/qwen3.6-max-preview` | Qwen3.6 Max Preview | 262,144 | 65,536 | previous Max preview |
| `qwen/qwen3.6-plus` | Qwen3.6 Plus | 1,000,000 | 65,536 | multimodal Plus |
| `qwen/qwen3.6-flash` | Qwen3.6 Flash | 1,000,000 | 65,536 | fast multimodal |
| `qwen/qwen3.6-35b-a3b` | Qwen3.6 35B A3B | 262,144 | 262,144 | open/efficient multimodal |
| `qwen/qwen3.6-27b` | Qwen3.6 27B | 262,144 | 262,140 | open/efficient multimodal |
| `qwen/qwen3.5-plus-20260420` | Qwen3.5 Plus 2026-04-20 | 1,000,000 | 65,536 | previous Plus dated |
| `qwen/qwen3.5-plus-02-15` | Qwen3.5 Plus 2026-02-15 | 1,000,000 | 65,536 | previous Plus dated |
| `qwen/qwen3.5-flash-02-23` | Qwen3.5 Flash | 1,000,000 | 65,536 | previous Flash |
| `qwen/qwen3.5-397b-a17b` | Qwen3.5 397B A17B | 256,000 | ? | large multimodal |
| `qwen/qwen3.5-122b-a10b` | Qwen3.5 122B A10B | 262,144 | 262,144 | large multimodal |
| `qwen/qwen3.5-35b-a3b` | Qwen3.5 35B A3B | 262,144 | 81,920 | efficient multimodal |
| `qwen/qwen3.5-27b` | Qwen3.5 27B | 262,144 | 65,536 | multimodal |
| `qwen/qwen3.5-9b` | Qwen3.5 9B | 262,144 | 262,144 | small multimodal |
| `qwen/qwen3-max` | Qwen3 Max | 262,144 | 32,768 | earlier Max |
| `qwen/qwen3-max-thinking` | Qwen3 Max Thinking | 262,144 | 32,768 | earlier Max reasoning |
| `qwen/qwen3-coder` | Qwen3 Coder 480B A35B | 1,048,576 | 65,536 | coder |
| `qwen/qwen3-coder:free` | Qwen3 Coder 480B A35B Free | 1,048,576 | 262,000 | free variant |
| `qwen/qwen3-coder-plus` | Qwen3 Coder Plus | 1,000,000 | 65,536 | coder Plus |
| `qwen/qwen3-coder-flash` | Qwen3 Coder Flash | 1,000,000 | 65,536 | fast coder |
| `qwen/qwen3-coder-next` | Qwen3 Coder Next | 262,144 | 262,144 | next coder |
| `qwen/qwen3-coder-30b-a3b-instruct` | Qwen3 Coder 30B A3B Instruct | 160,000 | 32,768 | smaller coder |
| `qwen/qwen3-30b-a3b-instruct-2507` | Qwen3 30B A3B Instruct 2507 | 131,072 | 32,000 | dated instruct |
| `qwen/qwen3-30b-a3b-thinking-2507` | Qwen3 30B A3B Thinking 2507 | 131,072 | 32,768 | dated thinking |
| `qwen/qwen3-235b-a22b-2507` | Qwen3 235B A22B Instruct 2507 | 262,144 | 16,384 | dated instruct |
| `qwen/qwen3-235b-a22b-thinking-2507` | Qwen3 235B A22B Thinking 2507 | 262,144 | ? | dated thinking |
| `qwen/qwen3-vl-235b-a22b-instruct` | Qwen3 VL 235B A22B Instruct | 262,144 | 16,384 | vision-language |
| `qwen/qwen3-vl-235b-a22b-thinking` | Qwen3 VL 235B A22B Thinking | 131,072 | 32,768 | vision-language reasoning |
| `qwen/qwen3-vl-30b-a3b-instruct` | Qwen3 VL 30B A3B Instruct | 262,144 | 32,768 | vision-language |
| `qwen/qwen3-vl-30b-a3b-thinking` | Qwen3 VL 30B A3B Thinking | 131,072 | 32,768 | vision-language reasoning |
| `qwen/qwen3-vl-32b-instruct` | Qwen3 VL 32B Instruct | 262,144 | 32,768 | vision-language |
| `qwen/qwen3-vl-8b-instruct` | Qwen3 VL 8B Instruct | 256,000 | 32,768 | vision-language |
| `qwen/qwen3-vl-8b-thinking` | Qwen3 VL 8B Thinking | 256,000 | 32,768 | vision-language reasoning |
| `qwen/qwen-plus` | Qwen Plus | 1,000,000 | 32,768 | Plus alias |
| `qwen/qwen-plus-2025-07-28` | Qwen Plus 0728 | 1,000,000 | 32,768 | dated |
| `qwen/qwen-plus-2025-07-28:thinking` | Qwen Plus 0728 Thinking | 1,000,000 | 32,768 | dated thinking |
| `openrouter/auto` | Auto Router | 2,000,000 | ? | let OpenRouter choose |
| `openrouter/fusion` | Fusion Router | 1,000,000 | ? | multi-model deliberation model/router |
| `openrouter/bodybuilder` | Body Builder (beta) | 128,000 | ? | optimized for physical/fitness domain tasks |
| `openrouter/pareto-code` | Pareto Code Router | 2,000,000 | ? | code-optimized router |

Use routers only when user explicitly wants automatic routing or multi-model routing.

## 16. Sakana AI

| slug | display | context | max output | notes |
|---|---|---:|---:|---|
| `sakana/fugu-ultra` | Fugu Ultra | 1,000,000 | 128,000 | flagship Sakana model; text+image input; mandatory reasoning |

## 17. Z.AI / Zhipu (GLM)

| slug | display | context | max output | reasoning notes |
|---|---|---:|---:|---|
| `z-ai/glm-5.2` | GLM 5.2 | 1,048,576 | 131,072 | supports reasoning; efforts include `xhigh/high` |
| `z-ai/glm-5.1` | GLM 5.1 | 202,752 | ? | supports reasoning if metadata exposes it |
| `z-ai/glm-5` | GLM 5 | 202,752 | ? | supports reasoning if metadata exposes it |
| `z-ai/glm-5-turbo` | GLM 5 Turbo | 262,144 | 131,072 | fast GLM 5 |
| `z-ai/glm-5v-turbo` | GLM 5V Turbo | 202,752 | 131,072 | vision+video input |
| `z-ai/glm-4.7` | GLM 4.7 | 202,752 | 131,072 | GLM 4.7 |
| `z-ai/glm-4.7-flash` | GLM 4.7 Flash | 202,752 | 16,384 | fast GLM 4.7 |
| `z-ai/glm-4.6` | GLM 4.6 | 202,752 | 131,072 | GLM 4.6 |
| `z-ai/glm-4.6v` | GLM 4.6V | 131,072 | 32,768 | vision+video input |
| `z-ai/glm-4.5` | GLM 4.5 | 131,072 | 98,304 | GLM 4.5 |
| `z-ai/glm-4.5-air` | GLM 4.5 Air | 131,072 | 98,304 | efficient GLM 4.5 |
| `z-ai/glm-4.5v` | GLM 4.5V | 65,536 | 16,384 | vision input |

## 18. NVIDIA Nemotron

| slug | display | context | max output | reasoning notes |
|---|---|---:|---:|---|
| `nvidia/nemotron-3-ultra-550b-a55b` | Nemotron 3 Ultra | 1,000,000 listed / 262,144 top provider | 16,384 | reasoning exposed; supports `reasoning.max_tokens`; efforts include `high/medium` |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | Nemotron 3 Ultra Free | 1,000,000 | 65,536 | free tier; reasoning exposed |
| `nvidia/nemotron-3-super-120b-a12b` | Nemotron 3 Super | 1,000,000 | 16,384 | verify reasoning metadata |
| `nvidia/nemotron-3-super-120b-a12b:free` | Nemotron 3 Super Free | 1,000,000 | 16,384 | free tier |
| `nvidia/nemotron-3.5-content-safety:free` | Nemotron 3.5 Content Safety Free | 128,000 | 8,192 | multimodal guardrail |

## 19. Other Notable Models

| slug | display | context | max output | notes |
|---|---|---:|---:|---|
| `cohere/north-mini-code` | North Mini Code | 256,000 | 64,000 | Cohere coding model; verify paid/free variants |
| `cohere/north-mini-code:free` | North Mini Code Free | 256,000 | 64,000 | free tier |
| `nousresearch/hermes-4-405b` | Hermes 4 405B | 131,072 | ? | flagship Hermes 4 |
| `nousresearch/hermes-4-70b` | Hermes 4 70B | 131,072 | ? | efficient Hermes 4 |
| `poolside/laguna-m.1` | Laguna M.1 | 262,144 | 32,768 | Poolside coding model; free variant may exist |
| `poolside/laguna-m.1:free` | Laguna M.1 Free | 262,144 | 32,768 | free tier if live |
| `poolside/laguna-xs-2.1` | Laguna XS 2.1 | 262,144 | 32,768 | current Poolside small coding agent model |
| `poolside/laguna-xs-2.1:free` | Laguna XS 2.1 Free | 262,144 | 32,768 | free tier |
| `writer/palmyra-x5` | Palmyra X5 | 1,040,000 | 8,192 | Writer flagship; enterprise/long-doc |
| `upstage/solar-pro-3` | Solar Pro 3 | 128,000 | ? | Upstage flagship |
| `stepfun/step-3.7-flash` | Step 3.7 Flash | 256,000 | 256,000 | StepFun multimodal; text+image+video input |
| `stepfun/step-3.5-flash` | Step 3.5 Flash | 262,144 | 65,536 | StepFun text model |
| `nex-agi/nex-n2-pro` | Nex-N2-Pro | 262,144 | 262,144 | text+image; optional reasoning |
| `nex-agi/nex-n2-pro:free` | Nex-N2-Pro Free | 262,144 | 262,144 | free tier if live |
| `bytedance-seed/seed-2.0-lite` | Seed-2.0-Lite | 262,144 | ? | multimodal agent/workhorse |
| `bytedance-seed/seed-2.0-mini` | Seed-2.0-Mini | 262,144 | ? | efficient multimodal; reasoning efforts |
| `bytedance-seed/seed-1.6` | Seed 1.6 | 262,144 | ? | multimodal |
| `bytedance-seed/seed-1.6-flash` | Seed 1.6 Flash | 262,144 | 16,000 | fast multimodal thinking |
| `morph/morph-v3-large` | Morph V3 Large | 262,144 | 131,072 | code edit/apply model |
| `morph/morph-v3-fast` | Morph V3 Fast | 262,144 | 131,072 | fast code edit/apply model |

## 20. Multimodal Generation

### Endpoint Map

| task | endpoint | notes |
|---|---|---|
| Chat/text/image-output models | `/api/v1/chat/completions` or `/api/v1/responses` | Use model-supported multimodal content and `modalities`/image config where applicable |
| Dedicated image generation | `/api/v1/images` | Use for image API models such as `openai/gpt-image-2`, Seedream, Grok Imagine |
| List image models | `/api/v1/images/models` | Use to discover current image model slugs and parameters |
| Music / audio generation | `/api/v1/chat/completions` | Lyria models return text+audio when supported |
| Video generation | `/api/v1/videos` | Async submit+poll |
| List video models | `/api/v1/videos/models` | Use to discover current video model slugs and parameters |
| TTS | `/api/v1/audio/speech` | Raw audio response; OpenAI-compatible speech endpoint |
| Speech-to-text / transcription | `/api/v1/audio/transcriptions` | Dedicated transcription endpoint |
| Audio understanding | `/api/v1/chat/completions` or `/api/v1/responses` | Use audio input content parts for models such as GPT Audio/Voxtral |

### Image Models

Use `/api/v1/images/models` for the definitive current list. Resolver should include at least:

| slug | display | endpoint | notes |
|---|---|---|---|
| `openai/gpt-image-2` | GPT Image 2 | `/api/v1/images` | canonical OpenAI latest image generation/editing model |
| `openai/gpt-image-1` | GPT Image 1 | `/api/v1/images` | OpenAI image generation/editing |
| `openai/gpt-image-1-mini` | GPT Image 1 Mini | `/api/v1/images` | efficient OpenAI image model |
| `openai/gpt-5.4-image-2` | GPT-5.4 Image 2 | chat/image | GPT-5.4 + GPT Image 2 workflow model |
| `openai/gpt-5-image` | GPT-5 Image | chat/image | image-capable GPT-5 model |
| `openai/gpt-5-image-mini` | GPT-5 Image Mini | chat/image | efficient image-capable GPT-5 model |
| `google/gemini-3-pro-image` | Nano Banana Pro | chat/image | stable Gemini Pro image |
| `google/gemini-3-pro-image-preview` | Nano Banana Pro Preview | chat/image | Gemini Pro image preview |
| `google/gemini-3.1-flash-image` | Nano Banana 2 | chat/image | stable Gemini Flash image |
| `google/gemini-3.1-flash-image-preview` | Nano Banana 2 Preview | chat/image | Gemini Flash image preview |
| `google/gemini-3.1-flash-lite-image` | Nano Banana 2 Lite | chat/image | efficient image model |
| `google/gemini-2.5-flash-image` | Nano Banana | chat/image | stable Gemini image |
| `bytedance-seed/seedream-4.5` | Seedream 4.5 | `/api/v1/images` | ByteDance image generation/editing |
| `bytedance-seed/seedream-4.5:free` | Seedream 4.5 Free | `/api/v1/images` | free variant if available |
| `x-ai/grok-imagine-image-quality` | Grok Imagine Image Quality | `/api/v1/images` | xAI image generation/editing |

### Music / Audio Generation Models

| slug | display | context | max output | notes |
|---|---|---:|---:|---|
| `google/lyria-3-pro-preview` | Lyria 3 Pro Preview | 1,048,576 | 65,536 | full-length music/song generation; text+image input, text+audio output |
| `google/lyria-3-clip-preview` | Lyria 3 Clip Preview | 1,048,576 | 65,536 | short clips/loops/previews; text+image input, text+audio output |
| `openai/gpt-audio` | GPT Audio | 128,000 | 16,384 | general audio input/output via chat/responses |
| `openai/gpt-audio-mini` | GPT Audio Mini | 128,000 | 16,384 | efficient general audio input/output |

### Video Models

Use `/api/v1/videos/models` for the definitive current list. Resolver should include at least:

| slug | display | notes |
|---|---|---|
| `google/veo-3.1` | Veo 3.1 | high fidelity video; supports synchronized audio where provider allows |
| `google/veo-3.1-fast` | Veo 3.1 Fast | faster/lower cost |
| `openai/sora-2-pro` | Sora 2 Pro | OpenAI flagship video generation; verify live availability |
| `bytedance/seedance-2.0` | Seedance 2.0 | ByteDance video; character/camera/reference control |
| `bytedance/seedance-2.0-fast` | Seedance 2.0 Fast | faster/lower cost |
| `bytedance-seed/seedance-2.0` | Seedance 2.0 | provider namespace variant; use resolver |
| `bytedance-seed/seedance-2.0-fast` | Seedance 2.0 Fast | provider namespace variant; use resolver |

Video models may not appear in `/api/v1/models`; resolver includes static media fallbacks and should refresh from `/api/v1/videos/models`.

### TTS Models

Use `GET /api/v1/models?output_modalities=speech` for the definitive current list. Known current/documented slugs:

| slug | display | endpoint | notes |
|---|---|---|---|
| `google/gemini-3.1-flash-tts-preview` | Gemini 3.1 Flash TTS Preview | `/api/v1/audio/speech` | Google TTS; text to speech |
| `microsoft/mai-voice-2` | MAI-Voice-2 | `/api/v1/audio/speech` | Microsoft/Azure voice model; supports Azure-style voices/options |
| `mistralai/voxtral-mini-tts-2603` | Voxtral Mini TTS 2603 | `/api/v1/audio/speech` | Mistral TTS; verify live |
| `elevenlabs/eleven-turbo-v2` | Eleven Turbo v2 | `/api/v1/audio/speech` | ElevenLabs TTS; documented SDK example |
| `openai/gpt-4o-mini-tts-2025-12-15` | GPT-4o Mini TTS | `/api/v1/audio/speech` | documented example but may be unavailable; use resolver before calling |

### Speech / Audio-Input / Transcription Models

| slug | display | endpoint | notes |
|---|---|---|---|
| `mistralai/voxtral-small-24b-2507` | Voxtral Small 24B 2507 | chat/responses | speech transcription, translation, and audio understanding; audio input, text output |
| `openai/gpt-audio` | GPT Audio | chat/responses | audio/speech input and output |
| `openai/gpt-audio-mini` | GPT Audio Mini | chat/responses | efficient audio/speech input and output |
| `openai/whisper-1` | Whisper 1 | `/api/v1/audio/transcriptions` | speech-to-text/transcription; verify exact slug live |
| `openai/gpt-4o-transcribe` | GPT-4o Transcribe | `/api/v1/audio/transcriptions` | speech-to-text/transcription; verify exact slug live |
| `microsoft/mai-transcribe-1.5` | MAI-Transcribe 1.5 | `/api/v1/audio/transcriptions` | speech-to-text/transcription; verify exact slug live |
| `google/chirp-3` | Chirp 3 | `/api/v1/audio/transcriptions` | Google speech-to-text; verify exact slug live |
| `nvidia/parakeet-tdt-0.6b-v3` | Parakeet TDT 0.6B v3 | `/api/v1/audio/transcriptions` | NVIDIA speech-to-text; verify exact slug live |

## 21. Minimal Call Checklist

1. Resolve:
   