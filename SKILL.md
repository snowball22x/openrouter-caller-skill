---
name: openrouter-caller
description: "OpenRouter API calling guide. Use when the user requests to call an AI model via OpenRouter, or when calling models like Claude Sonnet 4.6, Opus 4.7, Perplexity Sonar Pro Search, GPT-5.5, Gemini 2.5 Pro, Llama 4 Maverick, DeepSeek R1, Kimi K2.6, etc. Also handles tilde latest-alias slugs and natural language latest model requests. Covers multimodal generation: image (GPT-5.4 Image 2, Gemini 3.1 Flash Image, Seedream 4.5), video (Veo 3.1, Seedance 2.0), and speech/TTS (Gemini 3.1 Flash TTS). Provides instructions on how to correctly identify and use exact model slugs to avoid fallback to incorrect models."
---

# OpenRouter Caller Skill

OpenRouter uses exact model slugs (e.g., `anthropic/claude-sonnet-4.6`) in the `model` field. **If an invalid or non-existent slug is used, OpenRouter silently falls back to a different model.** This skill ensures the correct slug is always used.

---

## Step 1: Resolve the Model Slug

Use this decision flowchart before every OpenRouter API call:

```
Does the input start with "~" (e.g., "~anthropic/claude-sonnet-latest")?
  YES → It is a tilde latest-alias slug. Use it as-is. Skip to Step 2.

Does the input contain a "/" (e.g., "anthropic/claude-sonnet-4.6")?
  YES → It is already a versioned slug. Use it as-is. Skip to Step 2.

Does the input contain the word "latest" (e.g., "claude sonnet latest")?
  YES → Run the resolver — it will return a tilde slug (e.g., ~anthropic/claude-sonnet-latest).

Is the model in the Common Confusions table in references/model_slugs.md?
  YES → Use the correct slug from that table. Skip to Step 2.
  NO  → Run the resolver script (see below).
```

**Run the resolver** (handles all cases: versioned, tilde/latest-alias, and natural language):
```bash
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "claude sonnet 4.6"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "claude sonnet latest"     # → ~anthropic/claude-sonnet-latest
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "~google/gemini-flash-latest"  # passthrough
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "gemini flash latest"      # → ~google/gemini-flash-latest
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "sonar pro search"
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py "opus 4.7"
```

The script outputs `USE_SLUG=...` — use that exact string as the `model` field.

**If the resolver shows `⚠ AMBIGUOUS`:** The top two candidates are very close in score. Check `references/model_slugs.md` or ask the user to confirm before proceeding.

**Tilde latest-alias slugs** — use when user says "latest" without a version number:
- Always prefixed with `~` (e.g., `~anthropic/claude-sonnet-latest`)
- `anthropic/claude-sonnet-latest` without `~` is **invalid** and will cause an error
- Compatible with all suffix modifiers: `~anthropic/claude-sonnet-latest:nitro`
- See the full list in `references/model_slugs.md` § Tilde Latest-Alias Slugs

**To see all available models (always current):**
```bash
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list anthropic
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --list "~"   # all latest-alias models
python3.11 /home/ubuntu/skills/openrouter-caller/scripts/resolve_model.py --refresh   # force cache refresh
```

**Slug suffixes** — append to any slug when needed:

| Suffix | Effect |
|---|---|
| `:nitro` | Fastest provider (sort by throughput) |
| `:floor` | Cheapest provider (sort by price) |
| `:free` | Free tier only |
| `:thinking` | Extended reasoning / chain-of-thought |
| `:extended` | Extended context window |
| `:exacto` | Quality-first for tool-calling reliability |
| `:online` | **Deprecated** — use `openrouter:web_search` server tool instead |

Example: `anthropic/claude-sonnet-4.6:nitro`

See `references/model_slugs.md` for the full reference including context lengths, max output tokens, and common confusions.

---

## Step 2: Make the API Call

```python
import os, requests

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
}

data = {
    "model": "anthropic/claude-sonnet-4.6",  # MUST be exact resolved slug
    "messages": [
        {"role": "user", "content": "Your prompt here"}
    ],
    "max_tokens": 16000,  # Set high enough — see Step 4 for guidance
}

# Optional: Pin to a specific provider backend to avoid unexpected routing
# data["provider"] = {"order": ["Anthropic"], "allow_fallbacks": False}

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    json=data
)
result = response.json()
```

---

## Step 3: Verify the Model Actually Used

**Always check which model OpenRouter actually used** — it may differ from what was requested if a fallback occurred.

```python
# After getting the response:
used_model = result.get("model", "unknown")
requested_model = data["model"]

if used_model != requested_model:
    print(f"WARNING: Requested '{requested_model}' but OpenRouter used '{used_model}'")
    # Consider retrying, or raising an error if exact model is critical
else:
    print(f"OK: Model used = {used_model}")

content = result["choices"][0]["message"]["content"]
finish_reason = result["choices"][0]["finish_reason"]
```

---

## Step 4: Handle `finish_reason = "length"`

A `finish_reason` of `"length"` means the output was truncated because it hit the `max_tokens` limit. This is **not an error** — it is a truncation signal.

**Solutions:**

1. **Increase `max_tokens`** — check the model's max output in `references/model_slugs.md` and set accordingly:
   ```python
   data["max_tokens"] = 32000  # or higher, up to the model's max output limit
   ```

2. **Detect and retry with chunking** — for long tasks, split into sections:
   ```python
   if finish_reason == "length":
       print("Output truncated. Consider splitting the task into smaller sections.")
       # Re-prompt: "Continue from where you left off..." or split the task
   ```

3. **Use a model with higher output limits** — e.g., `anthropic/claude-sonnet-4.6` supports 128K output vs `anthropic/claude-3.5-haiku`'s 8K.

---

## Step 5: Provider Pinning (Advanced)

By default, OpenRouter load-balances across multiple providers for the same model (e.g., Anthropic direct, Amazon Bedrock, Google Vertex). To pin to a specific backend:

```python
# Pin to Anthropic's own API (avoids Bedrock/Vertex routing)
data["provider"] = {
    "order": ["Anthropic"],
    "allow_fallbacks": False  # Fail rather than fall back to another provider
}

# Pin to multiple providers in priority order
data["provider"] = {
    "order": ["Anthropic", "AWS Bedrock"],
    "allow_fallbacks": True
}

# Require all parameters to be supported (prevents routing to limited providers)
data["provider"] = {
    "require_parameters": True
}
```

Common provider slugs: `"Anthropic"`, `"AWS Bedrock"`, `"Google Vertex"`, `"OpenAI"`, `"Together"`, `"Fireworks"`, `"DeepInfra"`.

---

## Step 6: Multimodal Generation (Image, Video, Speech)

Media generation models use **different endpoints** from the standard chat completions API. See `references/model_slugs.md` § Multimodal Generation for full slug tables and code examples.

### Image Generation
Use the standard `/api/v1/chat/completions` endpoint with `modalities: ["image", "text"]`. The generated image is returned as a base64-encoded data URL in the assistant message content.

```python
data = {
    "model": "openai/gpt-5.4-image-2",  # or google/gemini-3.1-flash-image-preview
    "messages": [{"role": "user", "content": "Generate an image of..."}],
    "modalities": ["image", "text"]
}
```

### Video Generation
Use the dedicated `/api/v1/videos` endpoint. This is **asynchronous** — submit a job, then poll until complete.

```python
import time

# Step 1: Submit
resp = requests.post(
    "https://openrouter.ai/api/v1/videos",
    headers=headers,
    json={"model": "google/veo-3.1", "prompt": "A serene mountain at sunset"}
)
job = resp.json()
polling_url = job["polling_url"]

# Step 2: Poll
while True:
    status = requests.get(polling_url, headers=headers).json()
    if status["status"] == "completed":
        for url in status.get("unsigned_urls", []):
            print(f"Video URL: {url}")
        break
    elif status["status"] == "failed":
        raise RuntimeError(status.get("error"))
    time.sleep(5)
```

### Speech / TTS
Use the OpenAI-compatible `/api/v1/audio/speech` endpoint. The response is a **raw audio stream** (not JSON).

```python
from openai import OpenAI
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)

with client.audio.speech.with_streaming_response.create(
    model="google/gemini-3.1-flash-tts-preview",
    input="Hello! This is a text-to-speech test.",
    voice="alloy"
) as response:
    response.stream_to_file("output.mp3")
```

---

## Reference Files

- `references/model_slugs.md` — Curated slug reference with context lengths, max output tokens, common confusions, suffix documentation, and multimodal generation model tables. **Read this for quick lookups.**
- `scripts/resolve_model.py` — Live resolver that queries the OpenRouter API and fuzzy-matches natural language to exact slugs. **Run this for any model not in the reference.**
