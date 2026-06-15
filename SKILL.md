---
name: openrouter-caller
description: "Call OpenRouter models safely. Use when a user asks to call an AI model through OpenRouter or names models such as Claude Sonnet/Opus/Haiku/Fable, GPT, o-series, Gemini, Perplexity Sonar, Llama, DeepSeek, Kimi, Mistral, Grok, Qwen, image/video/TTS models, OpenRouter server tools, tilde latest aliases, or natural-language latest model requests. Resolves exact model slugs, tilde slugs, natural-language names, suffix modifiers, and server-tool model parameters before API calls."
---

# OpenRouter Caller Skill

OpenRouter calls require exact `model` slugs. Do **not** guess slugs. Always resolve and validate first.

Server tools are passed in the top-level `tools` array with type strings such as `openrouter:web_search`, `openrouter:fusion`, `openrouter:advisor`, and `openrouter:subagent`. OpenRouter executes server tools server-side; do not implement those tool calls client-side.

## Hard Rules

1. **Always run the resolver before an API call**, even if the input looks like an exact slug.
2. Also resolve every model slug embedded inside server-tool parameters, such as:
   - `openrouter:fusion.parameters.analysis_models`
   - `openrouter:fusion.parameters.model`
   - `openrouter:advisor.parameters.model`
   - `openrouter:subagent.parameters.model`
3. Use `USE_SLUG=...` only when:
   - `STATUS=OK`, or
   - `STATUS=UNVERIFIED` and the user explicitly supplied an exact-looking slug and validation was unavailable.
4. If `STATUS=AMBIGUOUS`: **do not call**. Ask the user to choose or inspect candidates.
5. If `STATUS=ERROR`: **do not call**. Fix the model request first.
6. If the user says “latest” without a version, prefer a tilde latest alias such as `~anthropic/claude-sonnet-latest`.
7. Never invent non-tilde latest slugs such as `anthropic/claude-sonnet-latest`; run the resolver.
8. Do not use deprecated `:online` for search unless explicitly required for legacy behavior; prefer `tools: [{"type": "openrouter:web_search"}]`.
9. Server tools may add cost and latency. Use them only when the task benefits from them, or when the user explicitly requests them.

---

## Server Tool Decision Table

| User/task signal | Prefer | Why |
|---|---|---|
| Needs current facts, recent news, live prices, citations, documentation lookup, source-grounded answer | `openrouter:web_search` | Lets the model search 0-N times and synthesize cited current results |
| Needs multiple independent model perspectives, high-stakes analysis, compare/contrast, adversarial critique, "what do different experts/models think?" | `openrouter:fusion` | Runs a model panel plus judge and returns consensus/contradictions/unique insights |
| Needs a stronger reviewer/architect/expert to advise the main model, especially before an approach or final answer | `openrouter:advisor` | Main model consults a higher-capability advisor mid-generation |
| Needs delegated subtasks such as extraction, summarization, reformatting, boilerplate drafting, chunk-level work | `openrouter:subagent` | Main model delegates self-contained work to a smaller/faster worker |
| Needs both fresh research and stronger review | `openrouter:web_search` + `openrouter:advisor` | Advisor can also receive nested web search |
| Needs panel research with fresh sources | `openrouter:fusion` | Fusion panel and judge already run with `web_search` and `web_fetch` enabled |
| Needs many small research subtasks | `openrouter:subagent` with nested `openrouter:web_search` | Worker searches inside the delegated task |
| Simple static prompt, no current info, no delegation/review needed | No server tools | Avoid unnecessary cost/latency |

---

## State Machine

### S0 — Determine endpoint family

| User task | Endpoint |
|---|---|
| Text/chat/reasoning/tool calling/search model output/server tools | `/api/v1/chat/completions` |
| Image generation/editing | `/api/v1/chat/completions` with `modalities: ["image", "text"]` |
| Video generation | `/api/v1/videos` async submit+poll |
| Text-to-speech / speech generation | `/api/v1/audio/speech` raw audio response |

If endpoint is unclear, resolve the model first; resolver prints `MODALITY=` and sometimes `ENDPOINT_HINT=`.

---

### S1 — Resolve model slug

Run:

    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "USER MODEL TEXT"

Examples:

    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "claude sonnet 4.6"
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "opus 4.8"
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "claude sonnet latest"
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "~google/gemini-flash-latest:nitro"
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "sonar pro search"
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "kimi k2"
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "veo 3.1"

Interpret output:

    STATUS=OK
    USE_SLUG=anthropic/claude-sonnet-4.6
    RESOLUTION=...
    NAME=...
    CONTEXT=...
    MAX_OUTPUT=...
    MODALITY=...

Decision:

| Resolver status | Action |
|---|---|
| `STATUS=OK` | Use `USE_SLUG` exactly. |
| `STATUS=UNVERIFIED` | Use only if user supplied exact slug and validation outage is acceptable. |
| `STATUS=AMBIGUOUS` | Stop and ask user / inspect candidates. |
| `STATUS=ERROR` | Stop; do not call OpenRouter. |

Useful resolver commands:

    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list anthropic
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list "~"
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --refresh
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --json "gemini flash latest"

---

### S2 — Apply suffix modifiers only through resolver

Valid suffixes:

| Suffix | Meaning |
|---|---|
| `:nitro` | Fastest provider routing |
| `:floor` | Cheapest provider routing |
| `:free` | Free-tier providers only |
| `:thinking` | Extended reasoning/thinking routing when supported |
| `:extended` | Extended context routing when supported |
| `:exacto` | Quality-first routing for reliability/tool use |
| `:online` | Deprecated; prefer `openrouter:web_search` server tool |

Examples:

    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "claude sonnet 4.6 nitro"
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "gemini flash latest floor"
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "openai/gpt-5.5:exacto"

Use returned `USE_SLUG`, e.g. `anthropic/claude-sonnet-4.6:nitro`.

---

## S3 — Chat/Text API Call

Use this template for text/chat/reasoning models and for server tools.

    import os
    import requests

    OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
    MODEL = "anthropic/claude-sonnet-4.6"  # paste resolver USE_SLUG exactly

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "Your prompt here"}
        ],
        "max_tokens": 16000,
    }

    # Optional provider pinning:
    # data["provider"] = {
    #     "order": ["Anthropic"],
    #     "allow_fallbacks": False,
    #     "require_parameters": True,
    # }

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=300,
    )

    if not resp.ok:
        print(resp.status_code, resp.text)
        resp.raise_for_status()

    result = resp.json()
    choice = result["choices"][0]
    content = choice["message"].get("content")
    finish_reason = choice.get("finish_reason")

    print(content)
    print("finish_reason =", finish_reason)
    print("requested_model =", MODEL)
    print("used_model =", result.get("model"))
    print("usage =", result.get("usage"))

---

## S4 — Verify model used

OpenRouter may route across providers. Also, tilde latest aliases resolve to concrete model versions.

Use this comparison:

    KNOWN_SUFFIXES = {"free", "nitro", "floor", "thinking", "extended", "exacto", "online"}

    def strip_suffix(model_id: str) -> str:
        if ":" in model_id:
            base, suffix = model_id.rsplit(":", 1)
            if suffix in KNOWN_SUFFIXES:
                return base
        return model_id

    requested = MODEL
    used = result.get("model", "")

    if requested.startswith("~"):
        print(f"OK: requested latest alias {requested}; OpenRouter used {used}")
    elif strip_suffix(used) != strip_suffix(requested):
        print(f"WARNING: requested {requested} but OpenRouter used {used}")
    else:
        print(f"OK: model used = {used}")

If exact model identity is critical, pin providers and set `allow_fallbacks: False`.

---

## S5 — Handle truncation

If `finish_reason == "length"`, output was truncated.

Actions:
1. Increase `max_tokens` up to model/provider limit.
2. Ask model to continue.
3. Split the task into chunks.
4. Select a model with larger output capacity.

    if finish_reason == "length":
        print("TRUNCATED: increase max_tokens or continue in a follow-up request.")

---

## S6 — Provider routing / pinning

Optional routing controls:

    # Prefer a provider; allow fallback.
    data["provider"] = {
        "order": ["Anthropic", "AWS Bedrock"],
        "allow_fallbacks": True,
    }

    # Exact backend only; fail instead of fallback.
    data["provider"] = {
        "order": ["Anthropic"],
        "allow_fallbacks": False,
    }

    # Require providers to support all requested parameters/tools.
    data["provider"] = {
        "require_parameters": True,
    }

Common provider names: `"Anthropic"`, `"OpenAI"`, `"Google AI Studio"`, `"Google Vertex"`, `"AWS Bedrock"`, `"Together"`, `"Fireworks"`, `"DeepInfra"`.

For server tools, `require_parameters: True` can prevent routing to providers that ignore required tool-related parameters, but may reduce availability.

---

## S7 — Image generation

Use `/api/v1/chat/completions`.

Resolve model examples:

    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "gpt 5.4 image 2"
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "nano banana pro"
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "seedream 4.5"

Call:

    import base64
    import os
    import re
    import requests

    OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
    MODEL = "openai/gpt-5.4-image-2"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "Generate a cinematic image of a glass city at sunrise."}
        ],
        "modalities": ["image", "text"],
    }

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=600,
    )
    resp.raise_for_status()
    result = resp.json()

    message = result["choices"][0]["message"]
    print(message.get("content"))

    # Save data URL images if present anywhere in JSON.
    text = str(message)
    for i, data_url in enumerate(re.findall(r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+", text)):
        header, b64 = data_url.split(",", 1)
        ext = header.split("/")[1].split(";")[0]
        with open(f"image_{i}.{ext}", "wb") as f:
            f.write(base64.b64decode(b64))

---

## S8 — Video generation

Use `/api/v1/videos`. It is asynchronous.

Resolve model:

    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "veo 3.1"
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "seedance 2.0 fast"

Call:

    import os
    import time
    import requests

    OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
    MODEL = "google/veo-3.1"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    submit = requests.post(
        "https://openrouter.ai/api/v1/videos",
        headers=headers,
        json={
            "model": MODEL,
            "prompt": "A slow aerial shot over snow-covered mountains at sunrise.",
        },
        timeout=120,
    )
    submit.raise_for_status()
    job = submit.json()

    polling_url = job["polling_url"]

    while True:
        status_resp = requests.get(polling_url, headers=headers, timeout=60)
        status_resp.raise_for_status()
        status = status_resp.json()

        if status.get("status") == "completed":
            print("completed")
            for url in status.get("unsigned_urls", []):
                print(url)
            break

        if status.get("status") == "failed":
            raise RuntimeError(status.get("error") or status)

        print("status =", status.get("status"))
        time.sleep(5)

---

## S9 — Speech / TTS

Use `/api/v1/audio/speech`. Response is raw audio, not JSON.

Resolve model:

    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "gemini flash tts"
    python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "gpt audio"

Call:

    import os
    import requests

    OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
    MODEL = "google/gemini-3.1-flash-tts-preview"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    resp = requests.post(
        "https://openrouter.ai/api/v1/audio/speech",
        headers=headers,
        json={
            "model": MODEL,
            "input": "Hello. This is a text to speech test.",
            "voice": "alloy",
            "response_format": "mp3",
        },
        timeout=300,
    )
    resp.raise_for_status()

    with open("speech.mp3", "wb") as f:
        f.write(resp.content)

    print("generation_id =", resp.headers.get("X-Generation-Id"))

---

## S10 — Server tool: `openrouter:web_search`

### When to use

Use when the user asks for:
- Current, recent, or changing information.
- Source-grounded answers and citations.
- Documentation lookup, release notes, pricing, benchmarks, news, regulatory changes, live market/company facts.
- Migration from deprecated `:online` or `plugins: [{"id": "web"}]`.

Do not use for static knowledge unless the user asks for sources or freshness matters.

### Python template

Resolve `MODEL` first. Then add a `tools` array:

    import os
    import requests

    OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
    MODEL = "~openai/gpt-latest"  # resolver USE_SLUG

    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "What were the major AI model releases this week? Cite sources.",
            }
        ],
        "tools": [
            {
                "type": "openrouter:web_search",
                "parameters": {
                    "engine": "auto",
                    "max_results": 5,
                    "max_total_results": 15,
                    "search_context_size": "medium",
                    # "allowed_domains": ["openrouter.ai", "anthropic.com"],
                    # "excluded_domains": ["reddit.com"],
                    # "max_characters": 8000,
                    # "user_location": {
                    #     "type": "approximate",
                    #     "city": "San Francisco",
                    #     "region": "California",
                    #     "country": "US",
                    #     "timezone": "America/Los_Angeles",
                    # },
                },
            }
        ],
    }

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json=data,
        timeout=300,
    )
    resp.raise_for_status()
    result = resp.json()
    print(result["choices"][0]["message"].get("content"))
    print("server_tool_use =", result.get("usage", {}).get("server_tool_use"))

### Key parameters

| Parameter | Values | Use |
|---|---|---|
| `engine` | `auto`, `native`, `exa`, `firecrawl`, `parallel`, `perplexity` | Search backend. `auto` uses native provider search when available, otherwise Exa. |
| `max_results` | 1-25 | Results per search call for non-native engines. |
| `max_total_results` | integer | Caps cumulative results across multiple searches in one request. |
| `search_context_size` | `low`, `medium`, `high` | Controls retrieved context size where supported. |
| `max_characters` | 1-100000 | Exact character cap per result where supported. Overrides `search_context_size`. |
| `allowed_domains` | list of domains | Restrict results to domains. |
| `excluded_domains` | list of domains | Exclude domains. Some engines make allow/exclude mutually exclusive. |
| `user_location` | approximate location object | Bias native provider search geographically. |

### Response structure

The final answer is in:

    result["choices"][0]["message"]["content"]

Tool usage is reported in:

    result["usage"]["server_tool_use"]["web_search_requests"]

Some providers include URL/citation annotations on the assistant message. Always inspect the full message if citations matter:

    print(result["choices"][0]["message"])

### Workflow combinations

| Combination | Pattern |
|---|---|
| Web search only | Top-level `tools: [{"type": "openrouter:web_search"}]` |
| Advisor with search | Top-level advisor whose `parameters.tools` includes web search |
| Subagent with search | Top-level subagent whose `parameters.tools` includes web search |
| Fusion with search | Use `openrouter:fusion`; panel and judge already have web search/fetch enabled |

---

## S11 — Server tool: `openrouter:fusion`

### When to use

Use for:
- Multi-model deliberation.
- Hard research questions.
- Compare/contrast tasks.
- High-stakes planning, policy, architecture, medical/legal/financial analysis with caveats.
- Tasks where surfacing disagreement, blind spots, and unique insights is valuable.

Avoid for simple extraction, short factual answers, or latency-sensitive tasks.

### Python template

Resolve all model slugs in `analysis_models` and `model` before the call.

    import os
    import requests

    OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
    MODEL = "anthropic/claude-sonnet-4.6"  # outer model, resolver USE_SLUG

    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Survey the strongest arguments for and against a carbon tax. Where do experts disagree?",
            }
        ],
        "tools": [
            {
                "type": "openrouter:fusion",
                "parameters": {
                    "analysis_models": [
                        "~anthropic/claude-opus-latest",
                        "~openai/gpt-latest",
                        "~google/gemini-pro-latest",
                    ],
                    "model": "~anthropic/claude-opus-latest",
                    "max_tool_calls": 8,
                    "max_completion_tokens": 12000,
                    "reasoning": {"effort": "medium"},
                    "temperature": 0.2,
                },
            }
        ],
        # Optional: force fusion instead of letting the model decide.
        # "tool_choice": "required",
    }

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json=data,
        timeout=600,
    )
    resp.raise_for_status()
    result = resp.json()
    print(result["choices"][0]["message"].get("content"))
    print("usage =", result.get("usage"))

### Key parameters

| Parameter | Default | Use |
|---|---|---|
| `analysis_models` | Quality preset | 1-8 panel models. Each panel model runs with `openrouter:web_search` and `openrouter:web_fetch` enabled. |
| `model` | Outer request model | Judge model that produces structured analysis JSON. |
| `max_tool_calls` | 8 | Max search/fetch tool-calling steps for each panel model and judge, range 1-16. |
| `max_completion_tokens` | Provider default | Max output tokens including reasoning for inner panel/judge calls. |
| `reasoning` | Provider default | Reasoning config forwarded to panel/judge calls. |
| `temperature` | Provider default | Sampling temperature, 0-2. |

### Tool result structure

The outer model receives the fusion tool result and writes the final answer. Internally, successful fusion returns a structure like:

    {
        "status": "ok",
        "analysis": {
            "consensus": ["..."],
            "contradictions": [
                {"topic": "...", "stances": [{"model": "...", "stance": "..."}]}
            ],
            "partial_coverage": [{"models": ["..."], "point": "..."}],
            "unique_insights": [{"model": "...", "insight": "..."}],
            "blind_spots": ["..."]
        },
        "responses": [
            {"model": "anthropic/claude-opus-4.8", "content": "..."}
        ],
        "failed_models": []
    }

If the judge fails but panel responses succeed, `analysis` may be omitted and `responses` remain available. Hard failures return `status: "error"` with `failure_reason` such as `all_panels_failed`, `insufficient_credits`, `rate_limited`, `fusion_invocation_capped`, or `unexpected_error`.

### Workflow combinations

| Combination | Pattern |
|---|---|
| Fusion only | `tools: [{"type": "openrouter:fusion"}]` |
| Fusion + forced use | Add `tool_choice: "required"` |
| Fusion + custom panel | Resolve and set `parameters.analysis_models` |
| Fusion + search/fetch | Built into panel and judge; no need to add separate nested tools |
| Fusion + advisor | Usually choose one. Use both only for very high-stakes tasks due cost/latency. |

---

## S12 — Server tool: `openrouter:advisor`

### When to use

Use when the main model should consult a stronger or specialized model:
- Before choosing an approach.
- When stuck or uncertain.
- Before finalizing a high-stakes answer.
- For code review, architecture review, security review, scientific critique, or domain expert guidance.

The advisor returns advice; the outer model still writes the final answer.

### Python template

Resolve `MODEL` and every advisor `parameters.model`.

    import os
    import requests

    OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
    MODEL = "openai/gpt-5.4-mini"  # outer model, resolver USE_SLUG

    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Design a concurrent worker pool in Go with graceful shutdown.",
            }
        ],
        "tools": [
            {
                "type": "openrouter:advisor",
                "parameters": {
                    "name": "senior-reviewer",
                    "model": "~anthropic/claude-opus-latest",
                    "instructions": "You are a senior staff engineer. Be decisive and identify pitfalls.",
                    "forward_transcript": False,
                    "tools": [
                        {
                            "type": "openrouter:web_search",
                            "parameters": {"max_results": 3, "max_total_results": 6},
                        }
                    ],
                    "max_tool_calls": 6,
                    "max_completion_tokens": 8000,
                    "reasoning": {"effort": "medium"},
                    "temperature": 0.1,
                },
            }
        ],
        # Optional: force consultation with the first advisor entry.
        # "tool_choice": "required",
    }

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json=data,
        timeout=600,
    )
    resp.raise_for_status()
    result = resp.json()
    print(result["choices"][0]["message"].get("content"))

### Key parameters

| Parameter | Default | Use |
|---|---|---|
| `name` | unnamed default advisor | Optional unique advisor name, 1-64 chars; letters, digits, spaces, underscores, dashes. |
| `model` | Outer request model | Advisor model. If omitted, the executing model may pass a model in the tool call; otherwise falls back to outer model. |
| `tools` | none | Server tools available to advisor. Nested function tools are rejected. Advisor may not list itself. |
| `instructions` | none | System instructions for the advisor. |
| `forward_transcript` | `false` | If true, advisor sees full parent conversation plus prompt. If false, only the prompt. |
| `stream` | `false` | Streams advice only on Responses API; no effect on Chat Completions. |
| `max_tool_calls` | provider default | Max advisor sub-agent tool steps, range 1-25. |
| `max_completion_tokens` | provider default | Max advisor output tokens including reasoning. |
| `reasoning` | provider default | Reasoning config for advisor call. |
| `temperature` | provider default | Sampling temperature, 0-2. |

### Multiple advisors

You may include multiple advisor entries:

    data["tools"] = [
        {
            "type": "openrouter:advisor",
            "parameters": {
                "name": "reviewer",
                "model": "~anthropic/claude-opus-latest",
                "instructions": "Find flaws and risks.",
            },
        },
        {
            "type": "openrouter:advisor",
            "parameters": {
                "name": "architect",
                "model": "~openai/gpt-latest",
                "instructions": "Evaluate scale and system design.",
            },
        },
    ]

Rules:
- At most one advisor entry may omit `name`.
- Names must be unique after trimming.
- `tool_choice: "required"` forces the first advisor entry; forcing a specific named advisor is not yet supported.

### Tool result structure

The outer model sees a result like:

    {
        "status": "ok",
        "model": "anthropic/claude-opus-4.8",
        "advice": "Use a channel-based coordination pattern..."
    }

On failure:

    {
        "status": "error",
        "error": "Advisor call failed: ..."
    }

For cross-request advisor memory, replay the assistant message with advisor tool calls and paired `role: "tool"` result messages exactly as returned by the API.

### Workflow combinations

| Combination | Pattern |
|---|---|
| Strong review | Small/fast outer model + advisor pinned to `~anthropic/claude-opus-latest` or `~openai/gpt-latest` |
| Research advisor | Advisor `parameters.tools` includes `openrouter:web_search` |
| Specialist panel | Multiple named advisors with different instructions |
| Forced review | Add `tool_choice: "required"` |

---

## S13 — Server tool: `openrouter:subagent`

### When to use

Use when the main model can delegate self-contained work to a smaller/faster worker:
- Summarize a document or section.
- Extract structured data.
- Reformat or normalize text.
- Draft boilerplate or tests.
- Perform a focused research subtask with its own web search.
- Process independent chunks.

Do not use when the worker would need unstated parent-conversation context. The worker sees only the delegated `task_description`, so the outer model must include all relevant context and output format.

### Python template

Resolve `MODEL` and `parameters.model`.

    import os
    import requests

    OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
    MODEL = "anthropic/claude-sonnet-4.6"  # outer model, resolver USE_SLUG

    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Audit this release: summarize the changelog, list breaking changes, and draft the announcement.",
            }
        ],
        "tools": [
            {
                "type": "openrouter:subagent",
                "parameters": {
                    "model": "~anthropic/claude-haiku-latest",
                    "instructions": "You are a fast, focused worker. Complete the task exactly as described.",
                    "tools": [
                        {
                            "type": "openrouter:web_search",
                            "parameters": {"engine": "auto", "max_results": 3},
                        }
                    ],
                    "max_tool_calls": 5,
                    "max_completion_tokens": 6000,
                    "reasoning": {"effort": "low"},
                    "temperature": 0.2,
                },
            }
        ],
    }

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json=data,
        timeout=600,
    )
    resp.raise_for_status()
    result = resp.json()
    print(result["choices"][0]["message"].get("content"))

### Key parameters

| Parameter | Default | Use |
|---|---|---|
| `model` | Outer request model | Fixed worker model. The delegating model does not choose it per call. |
| `tools` | none | Server tools available to worker. Nested function tools are rejected. Subagent may not list itself. |
| `instructions` | none | System instructions for worker. |
| `max_tool_calls` | provider default | Accepted for worker tool loops, range 1-25. |
| `max_completion_tokens` | provider default | Max worker output tokens including reasoning. |
| `reasoning` | provider default | Reasoning config for worker. |
| `temperature` | provider default | Sampling temperature, 0-2. |

### Tool-call arguments generated by the model

The model invokes the subagent with:
- `task_name`: short identifier, e.g. `summarize-changelog`.
- `task_description`: complete task instructions, context, inputs, constraints, and expected output format.

### Tool result structure

On success:

    {
        "status": "ok",
        "model": "anthropic/claude-haiku-4.5",
        "task_name": "summarize-changelog",
        "outcome": "Release 2.4 highlights..."
    }

On failure:

    {
        "status": "error",
        "task_name": "summarize-changelog",
        "error": "Subagent call failed: ..."
    }

### Workflow combinations

| Combination | Pattern |
|---|---|
| Cheap delegation | Strong outer model + subagent worker `~anthropic/claude-haiku-latest` |
| Research worker | Subagent `parameters.tools` includes `openrouter:web_search` |
| Chunk processing | Let outer model delegate independent chunks one by one |
| Final synthesis | Outer model integrates worker outcomes into final answer |

---

## Reference files

- `scripts/resolve_model.py` — authoritative resolver. Run before every call.
- `references/model_slugs.md` — quick-reference for common slugs, suffixes, latest aliases, media endpoints, and server tools.
