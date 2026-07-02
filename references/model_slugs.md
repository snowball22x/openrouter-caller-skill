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
| `claude fable latest` | `~anthropic/claude-fable-latest` | mapping to Sonnet/Opus |
| `fable 5` | `anthropic/claude-fable-5` | `claude-sonnet-5` |
| `opus fast` / `opus 4.8 fast` | `anthropic/claude-opus-4.8-fast` | regular `anthropic/claude-opus-4.8` if speed requested |
| `claude 3.7 sonnet` | error/not in supplied live list | remapping to 4.x silently |
| `sonar pro search` | `perplexity/sonar-pro-search` | `perplexity/sonar-pro` |
| `gpt latest` | `~openai/gpt-latest` | `openai/gpt-latest` |
| `gpt 5.5 pro` | `openai/gpt-5.5-pro` | `openai/gpt-5.5` |
| `gpt 5.3 codex` | `openai/gpt-5.3-codex` | `openai/gpt-5.3-chat` |
| `gemini flash latest` | `~google/gemini-flash-latest` | `google/gemini-flash-latest` |
| `gemini 3.5 flash` | `google/gemini-3.5-flash` | older `gemini-2.5-flash` |
| `lyria` / `music generation` | `google/lyria-3-pro-preview` or `google/lyria-3-clip-preview` | Gemini text/chat models |
| `deepseek r1` | `deepseek/deepseek-r1-0528` | undated if reproducibility matters |
| `deepseek r2` | error/not in supplied live list | inventing `deepseek-r2` |
| `deepseek v4` | ask Pro vs Flash | silently choosing one |
| `deepseek v4 free` | error/not in supplied live list | inventing `deepseek-v4-*:free` |
| `kimi k2` | `moonshotai/kimi-k2.6` | old `moonshotai/kimi-k2` |
| `kimi code` / `kimi k2.7 code` | `moonshotai/kimi-k2.7-code` | `moonshotai/kimi-k2.6` |
| `kimi latest` | `~moonshotai/kimi-latest` | pinning old K2 |
| `mistral medium 3.5` | `mistralai/mistral-medium-3-5` | dot slug |
| `codestral` | `mistralai/codestral-2508` | older Codestral slugs |
| `devstral` | `mistralai/devstral-2512` | nonexistent `devstral-medium` unless live list later adds it |
| `voxtral` | `mistralai/voxtral-small-24b-2507` | treating it as TTS output; it is audio-input speech/audio understanding |
| `nano banana pro` | `google/gemini-3-pro-image` | flash image variants |
| `nano banana 2` | `google/gemini-3.1-flash-image` | Gemini 3 Pro image |
| `grok 3` | error/not in supplied live list | mapping to `grok-4.3` silently |
| `grok 4.20 multi agent` | `x-ai/grok-4.20-multi-agent` | regular `x-ai/grok-4.20` |
| `grok 4 latest` | ask exact 4.3 vs 4.20 vs 4.20 multi-agent | guessing by decimal/version |
| `qwen 3.7 max` | `qwen/qwen3.7-max` | `qwen/qwen3.6-max-preview` |
| `qwen 3.7 plus` | `qwen/qwen3.7-plus` | `qwen/qwen3.6-plus` |
| `qwen max thinking` | `qwen/qwen3-max-thinking` | `qwen/qwen3.7-max` unless user asked 3.7 |
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
| autonomous long-horizon knowledge/coding work | `anthropic/claude-fable-5` |
| latest Fable alias | `~anthropic/claude-fable-latest` |
| strong advisor/judge | `~anthropic/claude-opus-latest` |
| fastest Opus 4.8 routing | `anthropic/claude-opus-4.8-fast` |
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
| `openai/gpt-5-nano` | GPT-5 Nano | 400,000 | 0 |
| `openai/gpt-5-codex` | GPT-5 Codex | 400,000 | 128,000 |
| `openai/gpt-5-image` | GPT-5 Image | 400,000 | 128,000 |
| `openai/gpt-5-image-mini` | GPT-5 Image Mini | 400,000 | 128,000 |
| `openai/gpt-chat-latest` | GPT Chat Latest | 400,000 | 128,000 |
| `openai/gpt-4.1` | GPT-4.1 | 1,047,576 | 0 |
| `openai/gpt-4.1-mini` | GPT-4.1 Mini | 1,047,576 | 32,768 |
| `openai/gpt-4.1-nano` | GPT-4.1 Nano | 1,047,576 | 32,768 |
| `openai/gpt-4o` | GPT-4o | 128,000 | 16,384 |
| `openai/gpt-4o-mini` | GPT-4o Mini | 128,000 | 16,384 |
| `openai/gpt-4o-search-preview` | GPT-4o Search Preview | 128,000 | 16,384 |
| `openai/gpt-4o-mini-search-preview` | GPT-4o Mini Search Preview | 128,000 | 16,384 |
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
| `openai/gpt-oss-120b` | gpt-oss-120b | 131,072 | 131,072 |
| `openai/gpt-oss-120b:free` | gpt-oss-120b Free | 131,072 | 131,072 |
| `openai/gpt-oss-20b` | gpt-oss-20b | 131,072 | 0 |
| `openai/gpt-oss-20b:free` | gpt-oss-20b Free | 131,072 | 32,768 |
| `openai/gpt-oss-safeguard-20b` | gpt-oss-safeguard-20b | 131,072 | 65,536 |

## 8. Google Gemini

| Slug | Display name | Context | Max output | Notes |
|---|---|---:|---:|---|
| `google/gemini-3.5-flash` | Gemini 3.5 Flash | 1,048,576 | 65,536 | Latest Flash line; multimodal text/image/file/audio/video input |
| `google/gemini-3.1-pro-preview` | Gemini 3.1 Pro Preview | 1,048,576 | 65,536 | Latest Pro preview |
| `google/gemini-3.1-pro-preview-customtools` | Gemini 3.1 Pro Preview Custom Tools | 1,048,756 | 65,536 | Custom tools variant |
| `google/gemini-3.1-flash-lite` | Gemini 3.1 Flash Lite | 1,048,576 | 65,536 | Efficient |
| `google/gemini-3.1-flash-lite-preview` | Gemini 3.1 Flash Lite Preview | 1,048,576 | 65,536 | Preview |
| `google/gemini-3-flash-preview` | Gemini 3 Flash Preview | 1,048,576 | 65,535 | Preview |
| `google/gemini-2.5-pro` | Gemini 2.5 Pro | 1,048,576 | 65,536 | Stable Pro |
| `google/gemini-2.5-pro-preview` | Gemini 2.5 Pro Preview 06-05 | 1,048,576 | 65,536 | Pro preview |
| `google/gemini-2.5-pro-preview-05-06` | Gemini 2.5 Pro Preview 05-06 | 1,048,576 | 65,535 | Older Pro preview |
| `google/gemini-2.5-flash` | Gemini 2.5 Flash | 1,048,576 | 65,535 | Stable Flash |
| `google/gemini-2.5-flash-lite` | Gemini 2.5 Flash Lite | 1,048,576 | 65,535 | Stable light model |
| `google/gemini-2.5-flash-lite-preview-09-2025` | Gemini 2.5 Flash Lite Preview 09-2025 | 1,048,576 | 65,535 | Older preview |

Google image/audio:

| Natural language | Slug | Context | Max output | Notes |
|---|---|---:|---:|---|
| Nano Banana Pro | `google/gemini-3-pro-image` | 65,536 | 32,768 | Stable Gemini 3 Pro image |
| Nano Banana Pro Preview | `google/gemini-3-pro-image-preview` | 65,536 | 32,768 | Preview Gemini Pro image |
| Nano Banana 2 | `google/gemini-3.1-flash-image` | 131,072 | 32,768 | Stable Gemini 3.1 Flash image |
| Nano Banana 2 Preview | `google/gemini-3.1-flash-image-preview` | 131,072 | 32,768 | Preview Gemini Flash image |
| Nano Banana 2 Lite | `google/gemini-3.1-flash-lite-image` | 65,536 | 66,000 | Efficient image |
| Nano Banana | `google/gemini-2.5-flash-image` | 32,768 | 32,768 | Stable image |
| Lyria 3 Pro Preview | `google/lyria-3-pro-preview` | 1,048,576 | 65,536 | Full-length music/audio generation; text+image to text+audio |
| Lyria 3 Clip Preview | `google/lyria-3-clip-preview` | 1,048,576 | 65,536 | Short music clips/loops; text+image to text+audio |
| Gemini Flash TTS | `google/gemini-3.1-flash-tts-preview` | n/a | n/a | Static TTS fallback if exposed by media endpoint; not in supplied `/models` list |

---

## 9. Meta Llama

| Slug | Display name | Context | Notes |
|---|---|---:|---|
| `meta-llama/llama-4-maverick` | Llama 4 Maverick | 1M | Flagship Llama 4 |
| `meta-llama/llama-4-scout` | Llama 4 Scout | 10M | Very large context |
| `meta-llama/llama-guard-4-12b` | Llama Guard 4 12B | 163K | Safety/guardrail, vision-capable |
| `meta-llama/llama-3.3-70b-instruct` | Llama 3.3 70B Instruct | 131K | Common open model |
| `meta-llama/llama-3.3-70b-instruct:free` | Llama 3.3 70B Instruct Free | 131K | Free variant |
| `meta-llama/llama-3.2-11b-vision-instruct` | Llama 3.2 11B Vision Instruct | 131K | Vision-capable |
| `meta-llama/llama-3.2-3b-instruct` | Llama 3.2 3B Instruct | 131K | Small |
| `meta-llama/llama-3.2-3b-instruct:free` | Llama 3.2 3B Instruct Free | 131K | Free variant |
| `meta-llama/llama-3.1-70b-instruct` | Llama 3.1 70B Instruct | 131K | Older |
| `meta-llama/llama-3.1-8b-instruct` | Llama 3.1 8B Instruct | 131K | Older |
| `meta-llama/llama-3-8b-instruct` | Llama 3 8B Instruct | 8K | Legacy |

---

## 10. DeepSeek

| Slug | Display name | Context | Max output | Notes |
|---|---|---:|---:|---|
| `deepseek/deepseek-v4-pro` | DeepSeek V4 Pro | 1,048,576 | 384,000 | Latest V4 pro; long-context reasoning/coding |
| `deepseek/deepseek-v4-flash` | DeepSeek V4 Flash | 1,048,576 | 0 | Fast V4; no `:free` variant in supplied live list |
| `deepseek/deepseek-v3.2` | DeepSeek V3.2 | 131,072 | 64,000 | V3.2 chat/reasoning |
| `deepseek/deepseek-v3.2-exp` | DeepSeek V3.2 Exp | 163,840 | 65,536 | Experimental |
| `deepseek/deepseek-v3.1-terminus` | DeepSeek V3.1 Terminus | 163,840 | 32,768 | V3.1 terminus |
| `deepseek/deepseek-chat-v3.1` | DeepSeek V3.1 | 163,840 | 32,768 | V3.1 chat |
| `deepseek/deepseek-chat-v3-0324` | DeepSeek V3 0324 | 163,840 | 16,384 | Dated V3 |
| `deepseek/deepseek-chat` | DeepSeek V3 | 131,072 | 16,000 | Base V3 alias |
| `deepseek/deepseek-r1-0528` | R1 0528 | 163,840 | 32,768 | Preferred R1 dated version |
| `deepseek/deepseek-r1` | R1 | 163,840 | 16,000 | Base alias |
| `deepseek/deepseek-r1-distill-llama-70b` | R1 Distill Llama 70B | 128,000 | 8,192 | Distilled open model |

---

## 11. MoonshotAI Kimi

| Slug | Display name | Context | Max output | Notes |
|---|---|---:|---:|---|
| `moonshotai/kimi-k2.7-code` | Kimi K2.7 Code | 262,144 | 16,384 | Latest coding-focused Kimi K2 variant |
| `moonshotai/kimi-k2.6` | Kimi K2.6 | 262,144 | 262,144 | Latest general K2 in supplied list |
| `moonshotai/kimi-k2.5` | Kimi K2.5 | 262,144 | 0 | Previous multimodal K2 |
| `moonshotai/kimi-k2-thinking` | Kimi K2 Thinking | 262,144 | 100,352 | Thinking model |
| `moonshotai/kimi-k2-0905` | Kimi K2 0905 | 262,144 | 100,352 | Dated |
| `moonshotai/kimi-k2` | Kimi K2 0711 | 131,072 | 100,352 | Older |
| `~moonshotai/kimi-latest` | Kimi Latest | 262,144 | 262,144 | Latest alias |

Recommended for “kimi k2”: `moonshotai/kimi-k2.6`.

Recommended for “kimi code” or “kimi k2.7”: `moonshotai/kimi-k2.7-code`.

Recommended for moving latest Kimi target: `~moonshotai/kimi-latest`.

---

## 12. Mistral

| Slug | Display name | Context | Max output | Notes |
|---|---|---:|---:|---|
| `mistralai/mistral-large-2512` | Mistral Large 3 2512 | 262,144 | 0 | Latest Large |
| `mistralai/mistral-large` | Mistral Large | 128,000 | 0 | Base large alias |
| `mistralai/mistral-large-2407` | Mistral Large 2407 | 131,072 | 0 | Older dated large |
| `mistralai/mistral-medium-3-5` | Mistral Medium 3.5 | 262,144 | 0 | Slug uses `3-5` |
| `mistralai/mistral-medium-3.1` | Mistral Medium 3.1 | 131,072 | 0 | Previous medium |
| `mistralai/mistral-medium-3` | Mistral Medium 3 | 131,072 | 0 | Older medium |
| `mistralai/mistral-small-2603` | Mistral Small 4 | 262,144 | 0 | Latest Small |
| `mistralai/mistral-small-3.2-24b-instruct` | Mistral Small 3.2 24B | 128,000 | 16,384 | Small instruct |
| `mistralai/mistral-small-3.1-24b-instruct` | Mistral Small 3.1 24B | 128,000 | 128,000 | Previous small instruct |
| `mistralai/mistral-small-24b-instruct-2501` | Mistral Small 3 | 32,768 | 16,384 | Older small |
| `mistralai/devstral-2512` | Devstral 2 2512 | 262,144 | 0 | Agentic coding/dev specialist |
| `mistralai/codestral-2508` | Codestral 2508 | 256,000 | 0 | Code/FIM/correction/test generation |
| `mistralai/voxtral-small-24b-2507` | Voxtral Small 24B 2507 | 32,000 | 0 | Audio input speech transcription/translation/understanding |
| `mistralai/ministral-14b-2512` | Ministral 3 14B 2512 | 262,144 | 0 | Small vision-capable Mistral |
| `mistralai/ministral-8b-2512` | Ministral 3 8B 2512 | 262,144 | 0 | Small vision-capable Mistral |
| `mistralai/ministral-3b-2512` | Ministral 3 3B 2512 | 131,072 | 0 | Small vision-capable Mistral |
| `mistralai/mistral-nemo` | Mistral Nemo | 131,072 | 0 | Efficient open model |
| `mistralai/mistral-saba` | Saba | 32,768 | 0 | Regional/language specialist |
| `mistralai/mixtral-8x22b-instruct` | Mixtral 8x22B Instruct | 65,536 | 0 | Legacy MoE |
| `mistralai/devstral-medium` | Devstral Medium | 131K | n/a | Historical/static fallback only; prefer live `mistralai/devstral-2512` |

---

## 13. xAI / Grok

| Slug | Display name | Context | Max output | Notes |
|---|---|---:|---:|---|
| `x-ai/grok-4.3` | Grok 4.3 | 1,000,000 | 0 | Current Grok 4.3 reasoning/chat |
| `x-ai/grok-4.20` | Grok 4.20 | 2,000,000 | 0 | Large-context Grok 4.20 |
| `x-ai/grok-4.20-multi-agent` | Grok 4.20 Multi-Agent | 2,000,000 | 0 | Multi-agent research/workflow variant |
| `x-ai/grok-build-0.1` | Grok Build 0.1 | 256,000 | 0 | Build/coding oriented |

---

## 14. Qwen and routers

| Slug | Display name | Context | Max output | Notes |
|---|---|---:|---:|---|
| `qwen/qwen3.7-max` | Qwen3.7 Max | 1,000,000 | 65,536 | Latest Max, text-only |
| `qwen/qwen3.7-plus` | Qwen3.7 Plus | 1,000,000 | 65,536 | Latest Plus, text+image |
| `qwen/qwen3.6-max-preview` | Qwen3.6 Max Preview | 262,144 | 65,536 | Previous Max preview |
| `qwen/qwen3.6-plus` | Qwen3.6 Plus | 1,000,000 | 65,536 | Multimodal Plus |
| `qwen/qwen3.6-flash` | Qwen3.6 Flash | 1,000,000 | 65,536 | Fast multimodal |
| `qwen/qwen3.6-35b-a3b` | Qwen3.6 35B A3B | 262,144 | 262,144 | Open/efficient multimodal |
| `qwen/qwen3.6-27b` | Qwen3.6 27B | 262,144 | 262,140 | Open/efficient multimodal |
| `qwen/qwen3.5-plus-20260420` | Qwen3.5 Plus 2026-04-20 | 1,000,000 | 65,536 | Previous Plus dated |
| `qwen/qwen3.5-plus-02-15` | Qwen3.5 Plus 2026-02-15 | 1,000,000 | 65,536 | Previous Plus dated |
| `qwen/qwen3.5-flash-02-23` | Qwen3.5 Flash | 1,000,000 | 65,536 | Previous Flash |
| `qwen/qwen3.5-397b-a17b` | Qwen3.5 397B A17B | 256,000 | 0 | Large multimodal |
| `qwen/qwen3.5-122b-a10b` | Qwen3.5 122B A10B | 262,144 | 262,144 | Large multimodal |
| `qwen/qwen3.5-35b-a3b` | Qwen3.5 35B A3B | 262,144 | 81,920 | Efficient multimodal |
| `qwen/qwen3.5-27b` | Qwen3.5 27B | 262,144 | 65,536 | Multimodal |
| `qwen/qwen3.5-9b` | Qwen3.5 9B | 262,144 | 262,144 | Small multimodal |
| `qwen/qwen3-max` | Qwen3 Max | 262,144 | 32,768 | Earlier Max |
| `qwen/qwen3-max-thinking` | Qwen3 Max Thinking | 262,144 | 32,768 | Earlier Max reasoning |
| `qwen/qwen3-coder` | Qwen3 Coder 480B A35B | 1,048,576 | 65,536 | Coder |
| `qwen/qwen3-coder:free` | Qwen3 Coder 480B A35B Free | 1,048,576 | 262,000 | Free variant |
| `qwen/qwen3-coder-plus` | Qwen3 Coder Plus | 1,000,000 | 65,536 | Coder Plus |
| `qwen/qwen3-coder-flash` | Qwen3 Coder Flash | 1,000,000 | 65,536 | Fast coder |
| `qwen/qwen3-coder-next` | Qwen3 Coder Next | 262,144 | 262,144 | Next coder |
| `qwen/qwen3-coder-30b-a3b-instruct` | Qwen3 Coder 30B A3B Instruct | 160,000 | 32,768 | Smaller coder |
| `qwen/qwen3-vl-235b-a22b-instruct` | Qwen3 VL 235B A22B Instruct | 262,144 | 16,384 | Vision-language |
| `qwen/qwen3-vl-235b-a22b-thinking` | Qwen3 VL 235B A22B Thinking | 131,072 | 32,768 | Vision-language reasoning |
| `qwen/qwen3-vl-30b-a3b-instruct` | Qwen3 VL 30B A3B Instruct | 262,144 | 32,768 | Vision-language |
| `qwen/qwen3-vl-30b-a3b-thinking` | Qwen3 VL 30B A3B Thinking | 131,072 | 32,768 | Vision-language reasoning |
| `qwen/qwen3-vl-32b-instruct` | Qwen3 VL 32B Instruct | 262,144 | 32,768 | Vision-language |
| `qwen/qwen3-vl-8b-instruct` | Qwen3 VL 8B Instruct | 256,000 | 32,768 | Vision-language |
| `qwen/qwen3-vl-8b-thinking` | Qwen3 VL 8B Thinking | 256,000 | 32,768 | Vision-language reasoning |
| `qwen/qwen-plus` | Qwen Plus | 1,000,000 | 32,768 | Plus alias |
| `qwen/qwen-plus-2025-07-28` | Qwen Plus 0728 | 1,000,000 | 32,768 | Dated |
| `qwen/qwen-plus-2025-07-28:thinking` | Qwen Plus 0728 Thinking | 1,000,000 | 32,768 | Dated thinking |
| `openrouter/auto` | Auto Router | 2,000,000 | 0 | Let OpenRouter choose |
| `openrouter/bodybuilder` | Body Builder (beta) | 128,000 | 0 | Optimized for physical/fitness domain tasks |

Use routers only when user explicitly wants automatic routing.

---

## 15a. Sakana AI

| Slug | Display name | Context | Max output | Notes |
|---|---|---:|---:|---|
| `sakana/fugu-ultra` | Fugu Ultra | 1,000,000 | 128,000 | Flagship Sakana model; text+image input; strong reasoning |

---

## 15b. Z.AI / Zhipu (GLM)

| Slug | Display name | Context | Max output | Notes |
|---|---|---:|---:|---|
| `z-ai/glm-5.2` | GLM 5.2 | 1,048,576 | 32,768 | Latest GLM 5.x; 1M context |
| `z-ai/glm-5.1` | GLM 5.1 | 202,752 | 0 | GLM 5.1 |
| `z-ai/glm-5` | GLM 5 | 202,752 | 0 | GLM 5 base |
| `z-ai/glm-5-turbo` | GLM 5 Turbo | 262,144 | 131,072 | Fast GLM 5 |
| `z-ai/glm-5v-turbo` | GLM 5V Turbo | 202,752 | 131,072 | Vision+video input |
| `z-ai/glm-4.7` | GLM 4.7 | 202,752 | 131,072 | GLM 4.7 |
| `z-ai/glm-4.7-flash` | GLM 4.7 Flash | 202,752 | 16,384 | Fast GLM 4.7 |
| `z-ai/glm-4.6` | GLM 4.6 | 202,752 | 131,072 | GLM 4.6 |
| `z-ai/glm-4.6v` | GLM 4.6V | 131,072 | 32,768 | Vision+video input |
| `z-ai/glm-4.5` | GLM 4.5 | 131,072 | 98,304 | GLM 4.5 |
| `z-ai/glm-4.5-air` | GLM 4.5 Air | 131,072 | 98,304 | Efficient GLM 4.5 |
| `z-ai/glm-4.5v` | GLM 4.5V | 65,536 | 16,384 | Vision input |

Reasoning: GLM 5.x supports `reasoning.effort` (low/medium/high); GLM 4.x does not support reasoning params — omit.

---

## 15c. NVIDIA Nemotron

| Slug | Display name | Context | Max output | Notes |
|---|---|---:|---:|---|
| `nvidia/nemotron-3-ultra-550b-a55b` | Nemotron 3 Ultra | 1,000,000 | 16,384 | Flagship 550B MoE; free variant available |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | Nemotron 3 Ultra Free | 1,000,000 | 16,384 | Free tier |
| `nvidia/nemotron-3-super-120b-a12b` | Nemotron 3 Super | 1,000,000 | 16,384 | 120B MoE; free variant available |
| `nvidia/nemotron-3-super-120b-a12b:free` | Nemotron 3 Super Free | 1,000,000 | 16,384 | Free tier |

Reasoning: Nemotron does not expose reasoning params — omit.

---

## 15d. Other Notable Models

| Slug | Display name | Context | Max output | Notes |
|---|---|---:|---:|---|
| `nousresearch/hermes-4-405b` | Hermes 4 405B | 131,072 | 0 | Flagship Hermes 4; strong instruction following |
| `nousresearch/hermes-4-70b` | Hermes 4 70B | 131,072 | 0 | Efficient Hermes 4 |
| `poolside/laguna-m.1` | Laguna M.1 | 262,144 | 32,768 | Poolside coding model; free variant available |
| `poolside/laguna-m.1:free` | Laguna M.1 Free | 262,144 | 32,768 | Free tier |
| `poolside/laguna-xs.2` | Laguna XS.2 | 262,144 | 32,768 | Smaller Poolside model; free variant available |
| `writer/palmyra-x5` | Palmyra X5 | 1,040,000 | 8,192 | Writer flagship; enterprise/long-doc |
| `upstage/solar-pro-3` | Solar Pro 3 | 128,000 | 0 | Upstage flagship |
| `stepfun/step-3.7-flash` | Step 3.7 Flash | 256,000 | 256,000 | StepFun multimodal (text+image+video input); 256K output |
| `stepfun/step-3.5-flash` | Step 3.5 Flash | 262,144 | 65,536 | StepFun text model |
| `openrouter/pareto-code` | Pareto Code Router | 2,000,000 | 0 | OpenRouter code-optimized router |

Reasoning: None of the above expose reasoning params — omit for all.

---

## 15e. Qwen3 Coder & VL additions

| Slug | Display name | Context | Max output | Notes |
|---|---|---:|---:|---|
| `qwen/qwen3-coder-next` | Qwen3 Coder Next | 262,144 | 262,144 | Next-gen coder; 262K output |
| `qwen/qwen3-30b-a3b-instruct-2507` | Qwen3 30B A3B Instruct 2507 | 131,072 | 32,000 | Dated instruct |
| `qwen/qwen3-30b-a3b-thinking-2507` | Qwen3 30B A3B Thinking 2507 | 131,072 | 32,768 | Dated thinking |
| `qwen/qwen3-235b-a22b-2507` | Qwen3 235B A22B Instruct 2507 | 262,144 | 16,384 | Dated instruct |
| `qwen/qwen3-235b-a22b-thinking-2507` | Qwen3 235B A22B Thinking 2507 | 262,144 | 0 | Dated thinking |
| `qwen/qwen3-vl-8b-thinking` | Qwen3 VL 8B Thinking | 256,000 | 32,768 | Small VL reasoning |

---

## 16. Multimodal generation

### Endpoint map

| Task | Endpoint | Notes |
|---|---|---|
| Image | `/api/v1/chat/completions` | Use `modalities: ["image", "text"]` when supported |
| Music / audio generation | `/api/v1/chat/completions` | Lyria models return `text+audio` from text/image prompts when supported |
| Video | `/api/v1/videos` | Async submit+poll |
| TTS | `/api/v1/audio/speech` | Raw audio response |
| Audio understanding / speech transcription | `/api/v1/chat/completions` | Use audio input content parts when supported |

### Image models

| Slug | Display name | Notes |
|---|---|---|
| `openai/gpt-image-2` | GPT Image 2 | Canonical OpenAI image generation model; served via media endpoint, may not appear in `/models` |
| `openai/gpt-5.4-image-2` | GPT-5.4 Image 2 | Top OpenAI image model |
| `openai/gpt-5-image` | GPT-5 Image | Image model |
| `openai/gpt-5-image-mini` | GPT-5 Image Mini | Efficient image model |
| `google/gemini-3-pro-image` | Nano Banana Pro | Stable Gemini Pro image |
| `google/gemini-3-pro-image-preview` | Nano Banana Pro Preview | Gemini Pro image preview |
| `google/gemini-3.1-flash-image` | Nano Banana 2 | Stable Gemini Flash image |
| `google/gemini-3.1-flash-image-preview` | Nano Banana 2 Preview | Gemini Flash image preview |
| `google/gemini-3.1-flash-lite-image` | Nano Banana 2 Lite | Efficient image model |
| `google/gemini-2.5-flash-image` | Nano Banana | Stable Gemini image |
| `bytedance-seed/seedream-4.5` | Seedream 4.5 | Portrait/composition image model; static media fallback if not in `/models` |

### Music / audio generation models

| Slug | Display name | Context | Max output | Notes |
|---|---|---:|---:|---|
| `google/lyria-3-pro-preview` | Lyria 3 Pro Preview | 1,048,576 | 65,536 | Full-length music/song generation; text+image input, text+audio output |
| `google/lyria-3-clip-preview` | Lyria 3 Clip Preview | 1,048,576 | 65,536 | Short clips/loops/previews; text+image input, text+audio output |

### Video models

| Slug | Display name | Notes |
|---|---|---|
| `google/veo-3.1` | Veo 3.1 | High fidelity video |
| `google/veo-3.1-fast` | Veo 3.1 Fast | Faster/lower cost |
| `bytedance/seedance-2.0` | Seedance 2.0 | Character/camera control |
| `bytedance/seedance-2.0-fast` | Seedance 2.0 Fast | Faster/lower cost |

Video models may not appear in `/api/v1/models`; resolver includes static media fallbacks.

### Speech / audio-input models

| Slug | Display name | Notes |
|---|---|---|
| `mistralai/voxtral-small-24b-2507` | Voxtral Small 24B 2507 | Speech transcription, translation, and audio understanding; audio input, text output |
| `openai/gpt-audio` | GPT Audio | Audio/speech input and output |
| `openai/gpt-audio-mini` | GPT Audio Mini | Efficient audio/speech input and output |
| `google/gemini-3.1-flash-tts-preview` | Gemini 3.1 Flash TTS Preview | Static TTS endpoint fallback if exposed outside `/models` |

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

## 18. Server Tools Reference

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

