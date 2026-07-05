---
name: openrouter-caller
description: "Call OpenRouter models safely. Use when a user asks to call OpenRouter or names Claude, GPT/o-series, Gemini, Sonar, Llama, DeepSeek, Kimi, Mistral, Grok, Qwen, media/TTS models, tilde latest aliases, suffix routing, or OpenRouter server tools."
---

# OpenRouter Caller Skill

## Hard Rules

| rule | action |
|---|---|
| Resolve before every API call | `python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "MODEL TEXT"` |
| Resolve nested server-tool models | advisor/subagent `parameters.model`; fusion `analysis_models` and `model` |
| `STATUS=OK` | Use `USE_SLUG` exactly |
| `STATUS=UNVERIFIED` | Use only for exact-looking user slug when validation is unavailable |
| `STATUS=AMBIGUOUS` | Do not call; ask user or inspect candidates |
| `STATUS=ERROR` | Do not call; fix model request |
| User says latest without version | Prefer tilde alias, e.g. `~anthropic/claude-sonnet-latest` |
| Latest slug | Never invent non-tilde latest slugs |
| Search/current facts | Prefer `openrouter:web_search`, not deprecated `:online` |
| Server tools | Use only when task benefits or user asks |

## S0 — Endpoint Family

| task | endpoint/script |
|---|---|
| chat/text/reasoning/tools/search | `scripts/call_chat.py` → `/api/v1/chat/completions` |
| image generation/editing | `scripts/call_image.py` → `/api/v1/images` |
| in-chat image generation by a text model | `/api/v1/chat/completions` with `openrouter:image_generation` server tool |
| video generation | `scripts/call_video.py` → `/api/v1/videos` async submit+poll |
| TTS/speech | `scripts/call_tts.py` → `/api/v1/audio/speech` |

## S1 — Resolve Model

| command | purpose |
|---|---|
| `python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "claude sonnet latest"` | natural-language → exact/tilde slug |
| `python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "~openai/gpt-latest:nitro"` | validate exact-looking slug |
| `python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list "~"` | list latest aliases |
| `python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --refresh` | refresh model cache |

## S2 — Suffix Modifiers

| suffix | meaning |
|---|---|
| `:nitro` | fastest provider routing |
| `:floor` | cheapest provider routing |
| `:free` | free-tier providers only |
| `:thinking` | thinking routing when supported |
| `:extended` | extended-context routing when supported |
| `:exacto` | quality-first routing for reliability/tool use |
| `:online` | deprecated; prefer `openrouter:web_search` |

Suffixes may be composed when OpenRouter supports the combination, e.g. `model:free:online`. Prefer server tools over `:online`.

## S_RE — Reasoning Effort

| tier | auto-assignment rule |
|---|---|
| none | simple retrieval, formatting, translation, echo tasks |
| minimal | single-step factual Q&A, short summarization |
| low | multi-step but straightforward tasks, standard coding |
| medium | complex coding, analysis, research synthesis; DEFAULT |
| high | architecture design, hard debugging, multi-constraint optimization |
| xhigh | adversarial critique, novel research, complex multi-step reasoning |
| max | only when user explicitly requests maximum effort; very expensive |

OpenRouter exposes current reasoning support per model in `/api/v1/models` under `reasoning`. Prefer that metadata over hard-coded family assumptions.

| family | OpenRouter call_chat mapping | provider/native note |
|---|---|---|
| OpenAI o-series / GPT-5.x | `reasoning.effort`, mapped to the nearest supported effort from `/models.reasoning.supported_efforts` | OpenAI-style effort |
| Anthropic older thinking models | `reasoning.max_tokens=N`; none→omit | raw Anthropic `thinking.budget_tokens`; minimum 1024 |
| Anthropic adaptive-thinking models | `reasoning.effort`; none→omit unless model requires reasoning | newer Claude models expose selectable efforts; use supported efforts |
| Google Gemini 2.5 | `reasoning.max_tokens=N`; none→0 when explicit disable is needed | Google `thinkingBudget` |
| Google Gemini 3.x/3.5 | `reasoning.effort`; none→minimal if reasoning is mandatory | Google `thinkingLevel`; xhigh/max map down if unsupported |
| DeepSeek R1/V4 | `reasoning.effort`, nearest supported value | V4 may expose high/xhigh-style routing through OpenRouter |
| Kimi K2.x | use `/models.reasoning`; otherwise enable/omit only | Moonshot controls thinking natively |
| Qwen thinking variants | `reasoning.max_tokens=N` when exposed | Alibaba-style `thinking_budget`; varies by model |
| Sakana/Z.AI/Nemotron/other reasoning models | use `/models.reasoning.supported_efforts` or `supports_max_tokens` | do not assume low/medium/high are all accepted |
| unsupported families | omit reasoning params | do not force unsupported params |

| tier | Anthropic/Gemini2.5/Qwen budget |
|---|---:|
| none | 0 or omit |
| minimal | 512 Gemini; 1024 Anthropic/Qwen |
| low | 1024 Gemini; 2048 Anthropic/Qwen |
| medium | 4096 Gemini; 8192 Anthropic/Qwen |
| high | 8192 Gemini; 16000 Anthropic/Qwen |
| xhigh | 16384 Gemini; 32000 Anthropic/Qwen |
| max | 32768 Gemini; 64000 Anthropic/Qwen, or lower if model/output cap requires |

## S3 — Direct Scripts

| task | one-liner |
|---|---|
| chat | `python3.11 scripts/call_chat.py --model "USE_SLUG" --prompt "..." --max-tokens 16000 --reasoning-effort medium` |
| full response JSON | `python3.11 scripts/call_chat.py --model "USE_SLUG" --prompt "..." --json-output` |
| chat + web search | `python3.11 scripts/call_chat.py --model "USE_SLUG" --prompt "Cite sources." --tools web_search` |
| chat + advisor | `python3.11 scripts/call_chat.py --model "USE_SLUG" --prompt "Review design." --tools advisor --reasoning-effort high` |
| chat + fusion | `python3.11 scripts/call_chat.py --model "USE_SLUG" --prompt "Compare expert views." --tools fusion` |
| image | `python3.11 scripts/call_image.py --model "USE_SLUG" --prompt "..." --save-dir ./images` |
| video | `python3.11 scripts/call_video.py --model "USE_SLUG" --prompt "..." --save-path ./video.mp4` |
| TTS | `python3.11 scripts/call_tts.py --model "USE_SLUG" --text "..." --voice alloy --save-path speech.mp3` |

## S4 — Verify Output

| check | action |
|---|---|
| `used_model` differs from requested concrete slug | warn; pin provider if exact backend critical |
| requested starts `~` | OK; alias resolved server-side to concrete used model |
| `finish_reason=length` | increase `--max-tokens`, ask continue, chunk task, or choose larger-output model |
| `usage.server_tool_use` present | inspect cost/latency from server tools |

## S5 — Server Tool Decision

| signal | prefer |
|---|---|
| current facts, citations, docs lookup, recent events | `web_search` |
| multi-model perspectives, contradictions, high-stakes analysis | `fusion` |
| stronger reviewer/architect/domain expert | `advisor` |
| delegated extraction/summarization/chunk work | `subagent` |
| research + expert review | `web_search,advisor` |
| panel research with sources | `fusion` |
| many focused research subtasks | `subagent` with nested web search |
| simple static prompt | no server tools |

## S6 — Subagent Model Selection

| task_type | recommended_worker_model | reasoning_effort | why |
|---|---|---:|---|
| text_extraction | `~google/gemini-flash-latest` | low | fast, cheap extraction |
| summarization | `~anthropic/claude-haiku-latest` | low | concise reliable summaries |
| reformatting | `~anthropic/claude-haiku-latest` | low | strong instruction following |
| code_boilerplate | `qwen/qwen3-coder` | medium | efficient code generation |
| focused_research | `~google/gemini-pro-latest` | medium | strong synthesis with tools |
| chunk_processing | `~openai/gpt-mini-latest` | low | cheap parallel chunk work |
| vision_task | `~google/gemini-pro-latest` | medium | strong multimodal handling |
| math_reasoning | `~openai/gpt-latest` | high | deliberate reasoning |
| long_document | `~google/gemini-pro-latest` | medium | long-context strength |

## S7 — Advisor Model Selection

| task_type | recommended_advisor | reasoning_effort | why |
|---|---|---:|---|
| architecture_review | `~anthropic/claude-opus-latest` | high | deep tradeoff review |
| code_review | `~openai/gpt-latest` | medium | strong correctness check |
| security_review | `~anthropic/claude-opus-latest` | xhigh | adversarial critique |
| research_synthesis | `~google/gemini-pro-latest` | high | long-context source synthesis |
| math_proof | `~anthropic/claude-opus-latest` | high | independent proof check |
| vision_review | `~google/gemini-pro-latest` | medium | multimodal reviewer |
| low_cost_review | `~anthropic/claude-sonnet-latest` | medium | balanced cost/capability |

## S8 — Fusion Panel Composition

| analysis_type | panel_models | judge_model | max_tool_calls |
|---|---|---|---:|
| quick_consensus | `~anthropic/claude-haiku-latest`, `~openai/gpt-mini-latest` | `~anthropic/claude-sonnet-latest` | 2 |
| balanced_review | `~anthropic/claude-sonnet-latest`, `~openai/gpt-latest`, `~google/gemini-pro-latest` | `~anthropic/claude-opus-latest` | 4 |
| research_fusion | `~google/gemini-pro-latest`, `~anthropic/claude-sonnet-latest`, `moonshotai/kimi-k2.6` | `~anthropic/claude-opus-latest` | 8 |
| code_review | `qwen/qwen3-coder`, `~openai/gpt-latest`, `~anthropic/claude-sonnet-latest` | `~openai/gpt-latest` | 3 |
| adversarial_check | `~anthropic/claude-sonnet-latest`, `~openai/gpt-latest`, `~google/gemini-pro-latest` | `~anthropic/claude-opus-latest` | 5 |
| low_cost_batch | `~google/gemini-flash-latest`, `~anthropic/claude-haiku-latest`, `~openai/gpt-mini-latest` | `~anthropic/claude-sonnet-latest` | 1 |

## S9 — Minimal Checklist

| step | command/action |
|---|---|
| 1 | resolve every model string |
| 2 | require `STATUS=OK` unless safe `UNVERIFIED` exact slug |
| 3 | choose endpoint/script |
| 4 | auto-assign or set `--reasoning-effort` |
| 5 | add server tools only if justified |
| 6 | run script |
| 7 | inspect `finish_reason`, `used_model`, `usage` |
