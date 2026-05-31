#!/usr/bin/env python3.11
"""
OpenRouter model slug resolver for AI agents.

Contract:
  - Input: exact slug, tilde latest alias, or natural-language model name.
  - Output: machine-readable lines; use USE_SLUG only when STATUS=OK or STATUS=UNVERIFIED.
  - STATUS=AMBIGUOUS means ask/confirm before calling.
  - STATUS=ERROR means do not call.

No third-party dependencies.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import time
import urllib.request
from typing import Any, Dict, Iterable, List, Optional, Tuple

API_URL = "https://openrouter.ai/api/v1/models"
CACHE_TTL_SECONDS = 4 * 60 * 60
TIMEOUT_SECONDS = 20

KNOWN_SUFFIXES = {"free", "nitro", "floor", "thinking", "extended", "exacto", "online"}
STOPWORDS = {
    "model", "models", "the", "a", "an", "use", "call", "via", "on", "openrouter",
    "ai", "llm", "please", "with", "and", "for", "to", "run", "using",
}
VARIANT_TOKENS = {
    "mini", "nano", "pro", "fast", "high", "preview", "search", "reasoning", "deep",
    "research", "lite", "codex", "image", "audio", "tts", "free", "distill",
    "customtools", "thinking", "extended", "instruct", "chat", "omni", "vl",
}
AMBIGUITY_MIN_GAP = 14
AMBIGUITY_RATIO = 0.12
MIN_ACCEPT_SCORE = 45

RAW_EXACT_ALIASES: Dict[str, str] = {
    # Anthropic
    "claude sonnet 4.6": "anthropic/claude-sonnet-4.6",
    "sonnet 4.6": "anthropic/claude-sonnet-4.6",
    "claude sonnet 4.5": "anthropic/claude-sonnet-4.5",
    "sonnet 4.5": "anthropic/claude-sonnet-4.5",
    "claude opus 4.8": "anthropic/claude-opus-4.8",
    "opus 4.8": "anthropic/claude-opus-4.8",
    "claude opus 4.8 fast": "anthropic/claude-opus-4.8-fast",
    "opus 4.8 fast": "anthropic/claude-opus-4.8-fast",
    "claude opus 4.7": "anthropic/claude-opus-4.7",
    "opus 4.7": "anthropic/claude-opus-4.7",
    "claude haiku 4.5": "anthropic/claude-haiku-4.5",
    "haiku 4.5": "anthropic/claude-haiku-4.5",

    # Perplexity
    "sonar pro search": "perplexity/sonar-pro-search",
    "perplexity sonar pro search": "perplexity/sonar-pro-search",
    "sonar deep research": "perplexity/sonar-deep-research",
    "sonar reasoning pro": "perplexity/sonar-reasoning-pro",
    "sonar pro": "perplexity/sonar-pro",
    "sonar": "perplexity/sonar",

    # OpenAI
    "gpt 5.5": "openai/gpt-5.5",
    "gpt 5.5 pro": "openai/gpt-5.5-pro",
    "gpt 5.4": "openai/gpt-5.4",
    "gpt 5.4 pro": "openai/gpt-5.4-pro",
    "gpt 5.4 mini": "openai/gpt-5.4-mini",
    "gpt 5.4 nano": "openai/gpt-5.4-nano",
    "gpt 5.4 image 2": "openai/gpt-5.4-image-2",
    "gpt image": "openai/gpt-5-image",
    "gpt 5 image": "openai/gpt-5-image",
    "gpt 5 image mini": "openai/gpt-5-image-mini",
    "gpt 4.1": "openai/gpt-4.1",
    "o4 mini": "openai/o4-mini",
    "o4 mini high": "openai/o4-mini-high",
    "o3": "openai/o3",
    "o3 pro": "openai/o3-pro",
    "gpt audio": "openai/gpt-audio",
    "gpt audio mini": "openai/gpt-audio-mini",

    # Google
    "gemini 3.5 flash": "google/gemini-3.5-flash",
    "gemini 3.1 pro": "google/gemini-3.1-pro-preview",
    "gemini 3.1 pro preview": "google/gemini-3.1-pro-preview",
    "gemini 3.1 flash lite": "google/gemini-3.1-flash-lite",
    "gemini 3.1 flash lite preview": "google/gemini-3.1-flash-lite-preview",
    "gemini 3.1 flash image": "google/gemini-3.1-flash-image-preview",
    "gemini 2.5 pro": "google/gemini-2.5-pro",
    "gemini 2.5 flash": "google/gemini-2.5-flash",
    "gemini 2.5 flash lite": "google/gemini-2.5-flash-lite",
    "gemini 2.5 flash image": "google/gemini-2.5-flash-image",
    "nano banana": "google/gemini-2.5-flash-image",
    "nano banana pro": "google/gemini-3-pro-image-preview",
    "nano banana 2": "google/gemini-3.1-flash-image-preview",

    # Meta / DeepSeek / Kimi
    "llama 4 maverick": "meta-llama/llama-4-maverick",
    "llama 4 scout": "meta-llama/llama-4-scout",
    "deepseek r1": "deepseek/deepseek-r1-0528",
    "deepseek r1 0528": "deepseek/deepseek-r1-0528",
    "deepseek v4": "deepseek/deepseek-v4-pro",
    "deepseek v4 pro": "deepseek/deepseek-v4-pro",
    "deepseek v4 flash": "deepseek/deepseek-v4-flash",
    "kimi k2": "moonshotai/kimi-k2.6",
    "kimi k2.6": "moonshotai/kimi-k2.6",
    "kimi k2.5": "moonshotai/kimi-k2.5",
    "kimi k2 thinking": "moonshotai/kimi-k2-thinking",

    # Mistral / xAI / media
    "mistral large": "mistralai/mistral-large-2512",
    "mistral large 2512": "mistralai/mistral-large-2512",
    "mistral medium 3.5": "mistralai/mistral-medium-3-5",
    "mistral small": "mistralai/mistral-small-2603",
    "devstral medium": "mistralai/devstral-medium",
    "grok 4.3": "x-ai/grok-4.3",
    "grok 4.20": "x-ai/grok-4.20",
    "grok 4.20 multi agent": "x-ai/grok-4.20-multi-agent",
    "veo 3.1": "google/veo-3.1",
    "veo 3.1 fast": "google/veo-3.1-fast",
    "seedance 2.0": "bytedance/seedance-2.0",
    "seedance 2.0 fast": "bytedance/seedance-2.0-fast",
    "seedream 4.5": "bytedance-seed/seedream-4.5",
    "gemini tts": "google/gemini-3.1-flash-tts-preview",
    "gemini flash tts": "google/gemini-3.1-flash-tts-preview",
}

RAW_LATEST_ALIASES: Dict[str, str] = {
    "claude sonnet latest": "~anthropic/claude-sonnet-latest",
    "sonnet latest": "~anthropic/claude-sonnet-latest",
    "claude opus latest": "~anthropic/claude-opus-latest",
    "opus latest": "~anthropic/claude-opus-latest",
    "claude haiku latest": "~anthropic/claude-haiku-latest",
    "haiku latest": "~anthropic/claude-haiku-latest",
    "gemini flash latest": "~google/gemini-flash-latest",
    "gemini pro latest": "~google/gemini-pro-latest",
    "gpt latest": "~openai/gpt-latest",
    "openai gpt latest": "~openai/gpt-latest",
    "gpt mini latest": "~openai/gpt-mini-latest",
    "kimi latest": "~moonshotai/kimi-latest",
}

STATIC_MODELS: List[Dict[str, Any]] = [
    # Tilde latest aliases
    {"id": "~anthropic/claude-sonnet-latest", "name": "Anthropic Claude Sonnet Latest", "context_length": 1000000, "modality": "text+image+file->text"},
    {"id": "~anthropic/claude-opus-latest", "name": "Anthropic Claude Opus Latest", "context_length": 1000000, "modality": "text+image+file->text"},
    {"id": "~anthropic/claude-haiku-latest", "name": "Anthropic Claude Haiku Latest", "context_length": 200000, "modality": "text+image+file->text"},
    {"id": "~google/gemini-flash-latest", "name": "Google Gemini Flash Latest", "context_length": 1048576, "modality": "text+image+file+audio+video->text"},
    {"id": "~google/gemini-pro-latest", "name": "Google Gemini Pro Latest", "context_length": 1048576, "modality": "text+image+file+audio+video->text"},
    {"id": "~openai/gpt-latest", "name": "OpenAI GPT Latest", "context_length": 1050000, "modality": "text+image+file->text"},
    {"id": "~openai/gpt-mini-latest", "name": "OpenAI GPT Mini Latest", "context_length": 400000, "modality": "text+image+file->text"},
    {"id": "~moonshotai/kimi-latest", "name": "MoonshotAI Kimi Latest", "context_length": 262144, "modality": "text+image->text"},

    # Curated live chat/image/audio models used as offline fallback
    {"id": "anthropic/claude-sonnet-4.6", "name": "Anthropic: Claude Sonnet 4.6", "context_length": 1000000, "modality": "text+image+file->text"},
    {"id": "anthropic/claude-opus-4.8", "name": "Anthropic: Claude Opus 4.8", "context_length": 1000000, "modality": "text+image+file->text"},
    {"id": "anthropic/claude-opus-4.8-fast", "name": "Anthropic: Claude Opus 4.8 (Fast)", "context_length": 1000000, "modality": "text+image+file->text"},
    {"id": "anthropic/claude-opus-4.7", "name": "Anthropic: Claude Opus 4.7", "context_length": 1000000, "modality": "text+image+file->text"},
    {"id": "anthropic/claude-haiku-4.5", "name": "Anthropic: Claude Haiku 4.5", "context_length": 200000, "modality": "text+image+file->text"},

    {"id": "perplexity/sonar-pro-search", "name": "Perplexity: Sonar Pro Search", "context_length": 200000, "modality": "text+image->text"},
    {"id": "perplexity/sonar-pro", "name": "Perplexity: Sonar Pro", "context_length": 200000, "modality": "text+image->text"},
    {"id": "perplexity/sonar-reasoning-pro", "name": "Perplexity: Sonar Reasoning Pro", "context_length": 128000, "modality": "text+image->text"},
    {"id": "perplexity/sonar-deep-research", "name": "Perplexity: Sonar Deep Research", "context_length": 128000, "modality": "text->text"},

    {"id": "openai/gpt-5.5", "name": "OpenAI: GPT-5.5", "context_length": 1050000, "modality": "text+image+file->text"},
    {"id": "openai/gpt-5.5-pro", "name": "OpenAI: GPT-5.5 Pro", "context_length": 1050000, "modality": "text+image+file->text"},
    {"id": "openai/gpt-5.4-image-2", "name": "OpenAI: GPT-5.4 Image 2", "context_length": 272000, "modality": "text+image+file->text+image"},
    {"id": "openai/gpt-4.1", "name": "OpenAI: GPT-4.1", "context_length": 1047576, "modality": "text+image+file->text"},
    {"id": "openai/o4-mini", "name": "OpenAI: o4 Mini", "context_length": 200000, "modality": "text+image+file->text"},
    {"id": "openai/o3", "name": "OpenAI: o3", "context_length": 200000, "modality": "text+image+file->text"},
    {"id": "openai/gpt-audio", "name": "OpenAI: GPT Audio", "context_length": 128000, "modality": "text+audio->text+audio"},
    {"id": "openai/gpt-audio-mini", "name": "OpenAI: GPT Audio Mini", "context_length": 128000, "modality": "text+audio->text+audio"},

    {"id": "google/gemini-3.5-flash", "name": "Google: Gemini 3.5 Flash", "context_length": 1048576, "modality": "text+image+file+audio+video->text"},
    {"id": "google/gemini-3.1-pro-preview", "name": "Google: Gemini 3.1 Pro Preview", "context_length": 1048576, "modality": "text+image+file+audio+video->text"},
    {"id": "google/gemini-3.1-flash-lite", "name": "Google: Gemini 3.1 Flash Lite", "context_length": 1048576, "modality": "text+image+file+audio+video->text"},
    {"id": "google/gemini-3.1-flash-image-preview", "name": "Google: Nano Banana 2 (Gemini 3.1 Flash Image Preview)", "context_length": 131072, "modality": "text+image->text+image"},
    {"id": "google/gemini-3-pro-image-preview", "name": "Google: Nano Banana Pro (Gemini 3 Pro Image Preview)", "context_length": 65536, "modality": "text+image->text+image"},
    {"id": "google/gemini-2.5-pro", "name": "Google: Gemini 2.5 Pro", "context_length": 1048576, "modality": "text+image+file+audio+video->text"},
    {"id": "google/gemini-2.5-flash", "name": "Google: Gemini 2.5 Flash", "context_length": 1048576, "modality": "text+image+file+audio+video->text"},
    {"id": "google/gemini-2.5-flash-image", "name": "Google: Nano Banana (Gemini 2.5 Flash Image)", "context_length": 32768, "modality": "text+image->text+image"},

    {"id": "meta-llama/llama-4-maverick", "name": "Meta: Llama 4 Maverick", "context_length": 1048576, "modality": "text+image->text"},
    {"id": "meta-llama/llama-4-scout", "name": "Meta: Llama 4 Scout", "context_length": 10000000, "modality": "text+image->text"},

    {"id": "deepseek/deepseek-r1-0528", "name": "DeepSeek: R1 0528", "context_length": 163840, "modality": "text->text"},
    {"id": "deepseek/deepseek-v4-pro", "name": "DeepSeek: DeepSeek V4 Pro", "context_length": 1048576, "modality": "text->text"},
    {"id": "deepseek/deepseek-v4-flash", "name": "DeepSeek: DeepSeek V4 Flash", "context_length": 1048576, "modality": "text->text"},

    {"id": "moonshotai/kimi-k2.6", "name": "MoonshotAI: Kimi K2.6", "context_length": 262144, "modality": "text+image->text"},
    {"id": "moonshotai/kimi-k2-thinking", "name": "MoonshotAI: Kimi K2 Thinking", "context_length": 262144, "modality": "text->text"},

    {"id": "mistralai/mistral-large-2512", "name": "Mistral: Mistral Large 3 2512", "context_length": 262144, "modality": "text+image+file->text"},
    {"id": "mistralai/mistral-medium-3-5", "name": "Mistral: Mistral Medium 3.5", "context_length": 262144, "modality": "text+image+file->text"},
    {"id": "mistralai/mistral-small-2603", "name": "Mistral: Mistral Small 4", "context_length": 262144, "modality": "text+image->text"},

    # Media endpoints not guaranteed to appear in /models
    {"id": "google/veo-3.1", "name": "Google: Veo 3.1", "context_length": None, "modality": "text->video", "endpoint": "videos"},
    {"id": "google/veo-3.1-fast", "name": "Google: Veo 3.1 Fast", "context_length": None, "modality": "text->video", "endpoint": "videos"},
    {"id": "bytedance/seedance-2.0", "name": "ByteDance: Seedance 2.0", "context_length": None, "modality": "text->video", "endpoint": "videos"},
    {"id": "bytedance/seedance-2.0-fast", "name": "ByteDance: Seedance 2.0 Fast", "context_length": None, "modality": "text->video", "endpoint": "videos"},
    {"id": "bytedance-seed/seedream-4.5", "name": "ByteDance Seed: Seedream 4.5", "context_length": None, "modality": "text+image->image"},
    {"id": "google/gemini-3.1-flash-tts-preview", "name": "Google: Gemini 3.1 Flash TTS Preview", "context_length": None, "modality": "text->audio", "endpoint": "audio/speech"},
]


def simple_key(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r":(" + "|".join(sorted(KNOWN_SUFFIXES)) + r")\b", r" \1", text)
    text = re.sub(r"([a-z])(?=\d)", r"\1 ", text)
    text = re.sub(r"(?<=\d)(?=[a-z])", " ", text)
    text = re.sub(r"[^a-z0-9.]+", " ", text)
    return " ".join(t for t in text.split() if t not in STOPWORDS)


EXACT_ALIASES = {simple_key(k): v for k, v in RAW_EXACT_ALIASES.items()}
LATEST_ALIASES = {simple_key(k): v for k, v in RAW_LATEST_ALIASES.items()}


def tokenize(text: str, remove_stop: bool = True, expand_decimals: bool = True) -> List[str]:
    text = text.lower().replace("_", "-")
    text = re.sub(r"([a-z])(?=\d)", r"\1 ", text)
    text = re.sub(r"(?<=\d)(?=[a-z])", " ", text)
    raw = re.findall(r"\d+\.\d+|\d{4}-\d{2}-\d{2}|\d+|[a-z]+", text)
    out: List[str] = []
    for tok in raw:
        if remove_stop and tok in STOPWORDS:
            continue
        out.append(tok)
        if expand_decimals and re.fullmatch(r"\d+\.\d+", tok):
            out.extend(tok.split("."))
    return out


def canonical(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def strip_model_suffix(model_id: str) -> Tuple[str, Optional[str]]:
    if ":" in model_id:
        base, suffix = model_id.rsplit(":", 1)
        if suffix.lower() in KNOWN_SUFFIXES:
            return base, suffix.lower()
    return model_id, None


def apply_suffix(model_id: str, suffix: Optional[str]) -> str:
    if not suffix:
        return model_id
    base, old = strip_model_suffix(model_id)
    if old == suffix:
        return model_id
    return f"{base}:{suffix}"


def parse_slug_like(text: str) -> Optional[Tuple[str, Optional[str]]]:
    t = text.strip()
    m = re.fullmatch(r"(~?[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)(?::([A-Za-z][A-Za-z0-9_-]*))?", t)
    if not m:
        return None
    base, suffix = m.group(1), m.group(2)
    return base, suffix.lower() if suffix else None


def cache_file() -> str:
    home = os.path.expanduser("~")
    if home and home != "~":
        return os.path.join(home, ".cache", "openrouter-caller", "models.json")
    return "/tmp/openrouter-caller-models.json"


def read_cache() -> Optional[Dict[str, Any]]:
    try:
        with open(cache_file(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def write_cache(models: List[Dict[str, Any]]) -> None:
    path = cache_file()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"fetched_at": time.time(), "models": models}, f)
    except Exception:
        pass


def fetch_live_models() -> List[Dict[str, Any]]:
    headers = {"User-Agent": "openrouter-caller-resolver/2.0"}
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(API_URL, headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    data = payload.get("data")
    if not isinstance(data, list):
        raise RuntimeError("OpenRouter /models response did not contain a data list")
    return data


def merge_models(primary: Iterable[Dict[str, Any]], extras: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for source_name, seq in (("live", primary), ("static", extras)):
        for m in seq:
            mid = m.get("id")
            if not mid:
                continue
            item = dict(m)
            item.setdefault("name", mid)
            item.setdefault("context_length", None)
            item.setdefault("modality", "")
            item.setdefault("_source", source_name)
            if mid not in merged:
                merged[mid] = item
            elif source_name == "live":
                merged[mid].update(item)
                merged[mid]["_source"] = "live"
    return list(merged.values())


def load_models(force_refresh: bool = False, offline: bool = False) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    cache = read_cache()
    cache_fresh = bool(cache and (time.time() - float(cache.get("fetched_at", 0))) < CACHE_TTL_SECONDS)

    if offline:
        cached_models = cache.get("models", []) if cache else []
        return merge_models(cached_models, STATIC_MODELS), {"live_ok": False, "cache_used": bool(cache), "source": "offline"}

    if cache_fresh and not force_refresh:
        return merge_models(cache.get("models", []), STATIC_MODELS), {"live_ok": False, "cache_used": True, "source": "fresh_cache"}

    try:
        live = fetch_live_models()
        write_cache(live)
        return merge_models(live, STATIC_MODELS), {"live_ok": True, "cache_used": False, "source": "live"}
    except Exception as e:
        cached_models = cache.get("models", []) if cache else []
        return merge_models(cached_models, STATIC_MODELS), {"live_ok": False, "cache_used": bool(cache), "source": "cache_or_static", "error": str(e)}


def extract_suffix(query: str) -> Tuple[str, Optional[str]]:
    pattern = r":(" + "|".join(sorted(KNOWN_SUFFIXES)) + r")\b"
    m = re.search(pattern, query.lower())
    if m:
        suffix = m.group(1)
        cleaned = re.sub(pattern, " ", query, flags=re.IGNORECASE)
        return cleaned, suffix

    raw_key = simple_key(query)
    if raw_key in EXACT_ALIASES and raw_key.endswith("thinking"):
        return query, None

    toks = tokenize(query, remove_stop=False, expand_decimals=False)
    suffix: Optional[str] = None
    if toks:
        last = toks[-1]
        if last in {"nitro", "floor", "exacto", "online"}:
            suffix = last
        elif last == "free" or ("free" in toks and "tier" in toks):
            suffix = "free"
        elif last == "extended" or ("extended" in toks and "context" in toks):
            suffix = "extended"
        elif last == "thinking" or ("thinking" in toks and "mode" in toks):
            suffix = "thinking"

    if suffix:
        cleaned = " ".join(t for t in toks if t != suffix and not (suffix == "free" and t == "tier"))
        return cleaned, suffix
    return query, None


def model_max_output(m: Dict[str, Any]) -> Any:
    top = m.get("top_provider") if isinstance(m.get("top_provider"), dict) else {}
    return (
        m.get("max_completion_tokens")
        or m.get("max_output_tokens")
        or top.get("max_completion_tokens")
        or m.get("max_output")
        or "?"
    )


def model_fields(m: Dict[str, Any]) -> Tuple[str, Optional[str], str, str, str]:
    mid = m.get("id", "")
    base, suffix = strip_model_suffix(mid)
    tail = base.split("/", 1)[1] if "/" in base else base
    provider = base.split("/", 1)[0].lstrip("~") if "/" in base else ""
    name = str(m.get("name") or "")
    return base, suffix, tail, provider, name


def score_model(query: str, model: Dict[str, Any], requested_suffix: Optional[str] = None, latest_mode: bool = False) -> int:
    q_tokens = tokenize(query)
    if latest_mode:
        q_tokens = [t for t in q_tokens if t != "latest"]
    if not q_tokens:
        return 0

    mid = model.get("id", "")
    base, suffix, tail, provider, name = model_fields(model)
    id_text = base.lower().lstrip("~")
    tail_text = tail.lower()
    name_text = name.lower()

    full_tokens = set(tokenize(id_text + " " + name_text, remove_stop=False))
    tail_tokens = set(tokenize(tail_text, remove_stop=False))
    name_tokens = set(tokenize(name_text, remove_stop=False))

    score = 0
    matched = 0
    for tok in q_tokens:
        hit = False
        if tok in tail_tokens:
            score += 22
            hit = True
        elif tok in full_tokens:
            score += 16
            hit = True
        elif tok in name_tokens:
            score += 12
            hit = True
        elif len(tok) >= 3 and (tok in tail_text or tok in name_text or tok in id_text):
            score += 7
            hit = True

        if hit:
            matched += 1
        else:
            score -= 14

    q_can = canonical(" ".join(q_tokens))
    tail_can = canonical(tail_text)
    id_can = canonical(id_text)
    name_can = canonical(name_text)

    if q_can == tail_can:
        score += 180
    elif q_can == id_can:
        score += 160
    elif q_can == name_can:
        score += 140
    elif q_can and (q_can in tail_can or q_can in id_can or q_can in name_can):
        score += 70

    if matched == len(q_tokens):
        score += 25

    score += int(45 * difflib.SequenceMatcher(None, q_can, tail_can).ratio())

    q_set = set(q_tokens)
    candidate_tokens = tokenize(tail_text, remove_stop=False, expand_decimals=False)
    for t in candidate_tokens:
        if t in VARIANT_TOKENS and t not in q_set:
            score -= 22

    if suffix:
        if requested_suffix == suffix:
            score += 80
        elif not requested_suffix:
            score -= 45

    if requested_suffix and not suffix:
        score += 5

    if "preview" in candidate_tokens and "preview" not in q_set:
        score -= 20

    if provider == "openrouter" and not ({"openrouter", "auto", "free"} & q_set):
        score -= 60

    if latest_mode:
        score += 40 if mid.startswith("~") else -50

    return score


def rank(query: str, models: List[Dict[str, Any]], requested_suffix: Optional[str] = None, latest_mode: bool = False, top_n: int = 8) -> List[Dict[str, Any]]:
    candidates = [m for m in models if (m.get("id", "").startswith("~") if latest_mode else True)]
    scored: List[Dict[str, Any]] = []
    for m in candidates:
        s = score_model(query, m, requested_suffix, latest_mode)
        if s > 0:
            item = dict(m)
            item["_score"] = s
            item["_use_slug"] = apply_suffix(item["id"], requested_suffix)
            scored.append(item)
    scored.sort(key=lambda x: (-int(x["_score"]), x.get("id", "")))
    return scored[:top_n]


def is_ambiguous(results: List[Dict[str, Any]]) -> bool:
    if len(results) < 2:
        return False
    top = int(results[0]["_score"])
    second = int(results[1]["_score"])
    gap = top - second
    return gap <= max(AMBIGUITY_MIN_GAP, int(top * AMBIGUITY_RATIO))


def find_model(model_id: str, models: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for m in models:
        if m.get("id") == model_id:
            return m
    return None


def resolve(query: str, models: List[Dict[str, Any]], meta: Dict[str, Any], top_n: int = 8) -> Dict[str, Any]:
    query = query.strip()
    if not query:
        return {"status": "ERROR", "error": "empty_query"}

    parsed = parse_slug_like(query)
    ids = {m.get("id") for m in models}

    if parsed:
        base, suffix = parsed
        if suffix and suffix not in KNOWN_SUFFIXES:
            return {
                "status": "ERROR",
                "error": "unknown_suffix",
                "message": f"Unknown suffix :{suffix}. Known: {', '.join(sorted(KNOWN_SUFFIXES))}",
            }

        full = apply_suffix(base, suffix)

        if full in ids or (base in ids and (suffix in KNOWN_SUFFIXES or suffix is None)):
            m = find_model(full, models) or find_model(base, models) or {"id": full, "name": full}
            return {"status": "OK", "resolution": "validated_slug", "use_slug": full, "model": m, "warnings": []}

        if not base.startswith("~") and base.endswith("-latest") and ("~" + base) in ids:
            corrected = apply_suffix("~" + base, suffix)
            m = find_model("~" + base, models) or {"id": corrected, "name": corrected}
            return {
                "status": "OK",
                "resolution": "corrected_tilde_latest",
                "use_slug": corrected,
                "model": m,
                "warnings": ["Added required '~' prefix for OpenRouter latest-alias slug."],
            }

        if not meta.get("live_ok") and not meta.get("cache_used"):
            return {
                "status": "UNVERIFIED",
                "resolution": "slug_passthrough_no_live_models",
                "use_slug": full,
                "model": {"id": full, "name": full},
                "warnings": ["Could not fetch/validate model list; exact-looking slug passed through unverified."],
            }

        suggestions = rank(base.replace("/", " "), models, suffix, latest_mode=False, top_n=5)
        return {
            "status": "ERROR",
            "error": "invalid_slug",
            "message": f"Slug is not in the current OpenRouter model list: {full}",
            "candidates": suggestions,
        }

    raw_key = simple_key(query)
    if raw_key in EXACT_ALIASES:
        slug = EXACT_ALIASES[raw_key]
        m = find_model(slug, models) or {"id": slug, "name": slug}
        return {"status": "OK", "resolution": "curated_alias", "use_slug": slug, "model": m, "warnings": []}

    if raw_key in LATEST_ALIASES:
        slug = LATEST_ALIASES[raw_key]
        m = find_model(slug, models) or {"id": slug, "name": slug}
        return {
            "status": "OK",
            "resolution": "curated_latest_alias",
            "use_slug": slug,
            "model": m,
            "warnings": ["Tilde latest-alias: target model may change over time."],
        }

    cleaned_query, requested_suffix = extract_suffix(query)
    clean_key = simple_key(cleaned_query)

    if clean_key in EXACT_ALIASES:
        slug = apply_suffix(EXACT_ALIASES[clean_key], requested_suffix)
        base, _ = strip_model_suffix(slug)
        m = find_model(base, models) or {"id": slug, "name": slug}
        warnings = []
        if requested_suffix == "online":
            warnings.append(":online is deprecated; prefer OpenRouter web_search tooling when available.")
        return {"status": "OK", "resolution": "curated_alias_plus_suffix", "use_slug": slug, "model": m, "warnings": warnings}

    if clean_key in LATEST_ALIASES:
        slug = apply_suffix(LATEST_ALIASES[clean_key], requested_suffix)
        base, _ = strip_model_suffix(slug)
        m = find_model(base, models) or {"id": slug, "name": slug}
        warnings = ["Tilde latest-alias: target model may change over time."]
        if requested_suffix == "online":
            warnings.append(":online is deprecated; prefer OpenRouter web_search tooling when available.")
        return {"status": "OK", "resolution": "curated_latest_alias_plus_suffix", "use_slug": slug, "model": m, "warnings": warnings}

    latest_mode = "latest" in tokenize(query, remove_stop=False, expand_decimals=False)
    results = rank(cleaned_query, models, requested_suffix, latest_mode=latest_mode, top_n=top_n)

    if not results or int(results[0]["_score"]) < MIN_ACCEPT_SCORE:
        return {
            "status": "ERROR",
            "error": "no_confident_match",
            "message": f"No confident model match for: {query}",
            "candidates": results,
        }

    warnings: List[str] = []
    if requested_suffix == "online":
        warnings.append(":online is deprecated; prefer OpenRouter web_search tooling when available.")
    if latest_mode and results[0].get("id", "").startswith("~"):
        warnings.append("Tilde latest-alias: target model may change over time.")

    status = "AMBIGUOUS" if is_ambiguous(results) else "OK"
    return {
        "status": status,
        "resolution": "fuzzy_latest" if latest_mode else "fuzzy",
        "use_slug": results[0]["_use_slug"],
        "model": results[0],
        "candidates": results,
        "warnings": warnings,
    }


def emit_text(res: Dict[str, Any], meta: Dict[str, Any]) -> int:
    status = res.get("status")
    print(f"STATUS={status}")

    if meta.get("error"):
        print(f"MODEL_LIST_WARNING={meta['error']}")

    if status in {"OK", "UNVERIFIED", "AMBIGUOUS"}:
        print(f"USE_SLUG={res.get('use_slug')}")
        print(f"RESOLUTION={res.get('resolution')}")
        m = res.get("model") or {}
        print(f"NAME={m.get('name', '?')}")
        print(f"CONTEXT={m.get('context_length', '?')}")
        print(f"MAX_OUTPUT={model_max_output(m)}")
        print(f"MODALITY={m.get('modality', '?')}")
        endpoint = m.get("endpoint")
        if endpoint:
            print(f"ENDPOINT_HINT={endpoint}")
        for w in res.get("warnings", []):
            print(f"WARNING={w}")
        if status == "AMBIGUOUS":
            print("ACTION=Confirm with the user or inspect candidates before making the API call.")
    else:
        print(f"ERROR={res.get('error', 'unknown_error')}")
        if res.get("message"):
            print(f"MESSAGE={res['message']}")

    candidates = res.get("candidates") or []
    if candidates:
        print("CANDIDATES=")
        for m in candidates[:8]:
            print(
                f"  {m.get('_use_slug', m.get('id'))}\t"
                f"score={m.get('_score', '?')}\t"
                f"name={m.get('name', '?')}\t"
                f"ctx={m.get('context_length', '?')}"
            )

    return 0 if status in {"OK", "UNVERIFIED"} else (2 if status == "AMBIGUOUS" else 1)


def emit_json(res: Dict[str, Any], meta: Dict[str, Any]) -> int:
    def slim_model(m: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": m.get("id"),
            "use_slug": m.get("_use_slug", m.get("id")),
            "name": m.get("name"),
            "context_length": m.get("context_length"),
            "max_output": model_max_output(m),
            "modality": m.get("modality"),
            "endpoint": m.get("endpoint"),
            "score": m.get("_score"),
        }

    out = {k: v for k, v in res.items() if k not in {"model", "candidates"}}
    out["model"] = slim_model(res.get("model") or {})
    out["candidates"] = [slim_model(m) for m in (res.get("candidates") or [])]
    out["model_list"] = meta

    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if res.get("status") in {"OK", "UNVERIFIED"} else (2 if res.get("status") == "AMBIGUOUS" else 1)


def list_models(models: List[Dict[str, Any]], filt: str) -> None:
    f = (filt or "").lower().strip()
    rows = []

    for m in models:
        mid = m.get("id", "")
        name = str(m.get("name", ""))
        if f == "~":
            ok = mid.startswith("~")
        elif f:
            ok = mid.lower().startswith(f + "/") or f in mid.lower() or f in name.lower()
        else:
            ok = True
        if ok:
            rows.append(m)

    rows.sort(key=lambda x: x.get("id", ""))
    for m in rows:
        print(
            f"{m.get('id',''):68s} "
            f"ctx={str(m.get('context_length','?')):>8s} "
            f"out={str(model_max_output(m)):>8s} "
            f"{m.get('modality','')}"
        )
    print(f"TOTAL={len(rows)}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve OpenRouter model names to exact slugs.")
    parser.add_argument("query", nargs="*", help="model slug or natural-language model name")
    parser.add_argument("--list", nargs="?", const="", metavar="FILTER", help="list models; FILTER can be provider, substring, or ~")
    parser.add_argument("--refresh", action="store_true", help="force refresh live model cache")
    parser.add_argument("--offline", action="store_true", help="use cache/static data only")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--top", type=int, default=8, help="number of candidates to show")
    args = parser.parse_args(argv)

    query_text = " ".join(args.query).strip()
    force_for_exact_slug = bool(query_text and parse_slug_like(query_text))

    models, meta = load_models(
        force_refresh=args.refresh or force_for_exact_slug,
        offline=args.offline,
    )

    if args.refresh and args.list is None and not args.query:
        print(f"STATUS=OK\nMESSAGE=Model cache refreshed/loaded. SOURCE={meta.get('source')} COUNT={len(models)}")
        if meta.get("error"):
            print(f"WARNING={meta['error']}")
        return 0

    if args.list is not None:
        list_models(models, args.list)
        return 0

    if not query_text:
        parser.print_help(sys.stderr)
        return 1

    res = resolve(query_text, models, meta, top_n=max(2, args.top))
    return emit_json(res, meta) if args.json else emit_text(res, meta)


if __name__ == "__main__":
    raise SystemExit(main())