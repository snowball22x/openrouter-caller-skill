---
name: openrouter-caller
description: "Call OpenRouter models safely. Use when a user asks to call an AI model through OpenRouter or names models such as Claude Sonnet/Opus/Haiku, GPT, Gemini, Perplexity Sonar, Llama, DeepSeek, Kimi, Mistral, Grok, image/video/TTS models, tilde latest aliases, or natural-language latest model requests. Resolves exact model slugs, tilde slugs, natural language names, and suffix modifiers before API calls."
---

# OpenRouter Caller Skill

OpenRouter calls require exact `model` slugs. Do **not** guess slugs. Always resolve and validate first.

## Hard Rules

1. **Always run the resolver before an API call**, even if the input looks like an exact slug.
2. Use `USE_SLUG=...` only when:
   - `STATUS=OK`, or
   - `STATUS=UNVERIFIED` and the user explicitly supplied an exact-looking slug and validation was unavailable.
3. If `STATUS=AMBIGUOUS`: **do not call**. Ask the user to choose or inspect candidates.
4. If `STATUS=ERROR`: **do not call**. Fix the model request first.
5. If the user says “latest” without a version, prefer a tilde latest alias such as `~anthropic/claude-sonnet-latest`.
6. Never invent non-tilde latest slugs such as `anthropic/claude-sonnet-latest`; run the resolver.

---

## State Machine

### S0 — Determine endpoint family

| User task | Endpoint |
|---|---|
| Text/chat/reasoning/tool calling/search model output | `/api/v1/chat/completions` |
| Image generation/editing | `/api/v1/chat/completions` with `modalities: ["image", "text"]` |
| Video generation | `/api/v1/videos` async submit+poll |
| Text-to-speech / speech generation | `/api/v1/audio/speech` raw audio response |

If endpoint is unclear, resolve the model first; resolver prints `MODALITY=` and sometimes `ENDPOINT_HINT=`.

---

### S1 — Resolve model slug

Run:

```bash
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "USER MODEL TEXT"
```

Examples:

```bash
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "claude sonnet 4.6"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "opus 4.7"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "claude sonnet latest"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "~google/gemini-flash-latest:nitro"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "sonar pro search"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "kimi k2"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "veo 3.1"
```

Interpret output:

```text
STATUS=OK
USE_SLUG=anthropic/claude-sonnet-4.6
RESOLUTION=...
NAME=...
CONTEXT=...
MAX_OUTPUT=...
MODALITY=...
```

Decision:

| Resolver status | Action |
|---|---|
| `STATUS=OK` | Use `USE_SLUG` exactly. |
| `STATUS=UNVERIFIED` | Use only if user supplied exact slug and validation outage is acceptable. |
| `STATUS=AMBIGUOUS` | Stop and ask user / inspect candidates. |
| `STATUS=ERROR` | Stop; do not call OpenRouter. |

Useful resolver commands:

```bash
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list anthropic
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list "~"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --refresh
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --json "gemini flash latest"
```

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
| `:online` | Deprecated; prefer OpenRouter web search tooling when available |

Examples:

```bash
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "claude sonnet 4.6 nitro"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "gemini flash latest floor"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "openai/gpt-5.5:exacto"
```

Use returned `USE_SLUG`, e.g. `anthropic/claude-sonnet-4.6:nitro`.

---

## S3 — Chat/Text API Call

Use this template for text/chat/reasoning models.

```python
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
```

---

## S4 — Verify model used

OpenRouter may route across providers. Also, tilde latest aliases resolve to concrete model versions.

Use this comparison:

```python
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
```

If exact model identity is critical, pin providers and set `allow_fallbacks: False`.

---

## S5 — Handle truncation

If `finish_reason == "length"`, output was truncated.

Actions:
1. Increase `max_tokens` up to model/provider limit.
2. Ask model to continue.
3. Split the task into chunks.
4. Select a model with larger output capacity.

```python
if finish_reason == "length":
    print("TRUNCATED: increase max_tokens or continue in a follow-up request.")
```

---

## S6 — Provider routing / pinning

Optional routing controls:

```python
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
```

Common provider names: `"Anthropic"`, `"OpenAI"`, `"Google AI Studio"`, `"Google Vertex"`, `"AWS Bedrock"`, `"Together"`, `"Fireworks"`, `"DeepInfra"`.

---

## S7 — Image generation

Use `/api/v1/chat/completions`.

Resolve model examples:

```bash
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "gpt 5.4 image 2"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "nano banana pro"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "seedream 4.5"
```

Call:

```python
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
```

---

## S8 — Video generation

Use `/api/v1/videos`. It is asynchronous.

Resolve model:

```bash
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "veo 3.1"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "seedance 2.0 fast"
```

Call:

```python
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
```

---

## S9 — Speech / TTS

Use `/api/v1/audio/speech`. Response is raw audio, not JSON.

Resolve model:

```bash
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "gemini flash tts"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "gpt audio"
```

Call:

```python
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
```

---

## Reference files

- `scripts/resolve_model.py` — authoritative resolver. Run before every call.
- `references/model_slugs.md` — quick-reference for common slugs, suffixes, latest aliases, and media endpoints.