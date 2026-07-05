#!/usr/bin/env python3.11
"""
OpenRouter model slug resolver for AI agents.

Contract:
  - Input: exact slug, tilde latest alias, or natural-language model name.
  - Output: machine-readable lines.
  - Use USE_SLUG only when STATUS=OK, or STATUS=UNVERIFIED for an exact-looking
    user-supplied slug when validation is unavailable.
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
    "ai", "llm", "please", "with", "and", "for", "to", "run", "using", "latest",
}
VARIANT_TOKENS = {
    "mini", "nano", "pro", "fast", "high", "preview", "search", "reasoning", "deep",
    "research", "lite", "codex", "image", "audio", "tts", "free", "distill",
    "customtools", "custom", "tools", "thinking", "extended", "instruct", "chat",
    "omni", "vl", "max", "plus", "flash", "scout", "maverick", "fable", "haiku",
    "opus", "sonnet", "turbo", "safeguard", "vision", "code", "multi", "agent",
}
AMBIGUITY_MIN_GAP = 14
AMBIGUITY_RATIO = 0.12
MIN_ACCEPT_SCORE = 45


def fm(
    model_id: str,
    name: str,
    ctx: Optional[int] = None,
    out: Optional[int] = None,
    modality: str = "text->text",
    endpoint: Optional[str] = None,
) -> Dict[str, Any]:
    item: Dict[str, Any] = {
        "id": model_id,
        "name": name,
        "context_length": ctx,
        "modality": modality,
    }
    if out is not None:
        item["max_completion_tokens"] = out
    if endpoint:
        item["endpoint"] = endpoint
    return item


# Confirmed slugs served through non-chat or hybrid media endpoints.
KNOWN_MEDIA_SLUGS: Dict[str, str] = {
    "openai/gpt-image-2": "images",
    "openai/gpt-image-1": "images",
    "openai/gpt-image-1-mini": "images",
    "openai/gpt-5.4-image-2": "chat_or_images",
    "google/gemini-3-pro-image": "images",
    "google/gemini-3-pro-image-preview": "images",
    "google/gemini-3.1-flash-image": "images",
    "google/gemini-3.1-flash-image-preview": "images",
    "google/gemini-3.1-flash-lite-image": "images",
    "google/gemini-2.5-flash-image": "images",
    "bytedance-seed/seedream-4.5": "images",
    "google/veo-3.1": "videos",
    "google/veo-3.1-fast": "videos",
    "bytedance/seedance-2.0": "videos",
    "bytedance/seedance-2.0-fast": "videos",
    "google/gemini-3.1-flash-tts-preview": "audio/speech",
}

# Static fallback is curated, not exhaustive. Live /models is authoritative.
FALLBACK_MODELS: List[Dict[str, Any]] = [
    fm("~anthropic/claude-sonnet-latest", "Anthropic: Claude Sonnet Latest", 1000000, 128000, "text+image+file->text"),
    fm("~anthropic/claude-opus-latest", "Anthropic: Claude Opus Latest", 1000000, 128000, "text+image+file->text"),
    fm("~anthropic/claude-haiku-latest", "Anthropic: Claude Haiku Latest", 200000, 64000, "text+image+file->text"),
    fm("~anthropic/claude-fable-latest", "Anthropic: Claude Fable Latest", 1000000, 128000, "text+image+file->text"),
    fm("~google/gemini-flash-latest", "Google: Gemini Flash Latest", 1048576, 65536, "text+image+file+audio+video->text"),
    fm("~google/gemini-pro-latest", "Google: Gemini Pro Latest", 1048576, 65536, "text+image+file+audio+video->text"),
    fm("~openai/gpt-latest", "OpenAI: GPT Latest", 1050000, 128000, "text+image+file->text"),
    fm("~openai/gpt-mini-latest", "OpenAI: GPT Mini Latest", 400000, 128000, "text+image+file->text"),
    fm("~moonshotai/kimi-latest", "MoonshotAI: Kimi Latest", 262144, 262144, "text+image->text"),

    fm("anthropic/claude-sonnet-5", "Anthropic: Claude Sonnet 5", 1000000, 128000, "text+image+file->text"),
    fm("anthropic/claude-fable-5", "Anthropic: Claude Fable 5", 1000000, 128000, "text+image+file->text"),
    fm("anthropic/claude-sonnet-4.6", "Anthropic: Claude Sonnet 4.6", 1000000, 128000, "text+image+file->text"),
    fm("anthropic/claude-sonnet-4.5", "Anthropic: Claude Sonnet 4.5", 1000000, 64000, "text+image+file->text"),
    fm("anthropic/claude-opus-4.8", "Anthropic: Claude Opus 4.8", 1000000, 128000, "text+image+file->text"),
    fm("anthropic/claude-opus-4.8-fast", "Anthropic: Claude Opus 4.8 Fast", 1000000, 128000, "text+image+file->text"),
    fm("anthropic/claude-haiku-4.5", "Anthropic: Claude Haiku 4.5", 200000, 64000, "text+image+file->text"),

    fm("openai/gpt-5.5", "OpenAI: GPT-5.5", 1050000, 128000, "text+image+file->text"),
    fm("openai/gpt-5.5-pro", "OpenAI: GPT-5.5 Pro", 1050000, 128000, "text+image+file->text"),
    fm("openai/gpt-5.4", "OpenAI: GPT-5.4", 1050000, 128000, "text+image+file->text"),
    fm("openai/gpt-5.4-pro", "OpenAI: GPT-5.4 Pro", 1050000, 128000, "text+image+file->text"),
    fm("openai/gpt-5.4-mini", "OpenAI: GPT-5.4 Mini", 400000, 128000, "text+image+file->text"),
    fm("openai/gpt-5.4-nano", "OpenAI: GPT-5.4 Nano", 400000, 128000, "text+image+file->text"),
    fm("openai/gpt-5.3-chat", "OpenAI: GPT-5.3 Chat", 128000, 16384, "text+image+file->text"),
    fm("openai/gpt-5.3-codex", "OpenAI: GPT-5.3 Codex", 400000, 128000, "text+image->text"),
    fm("openai/gpt-5", "OpenAI: GPT-5", 400000, 128000, "text+image+file->text"),
    fm("openai/gpt-5-chat", "OpenAI: GPT-5 Chat", 128000, 16384, "text+image+file->text"),
    fm("openai/gpt-5-pro", "OpenAI: GPT-5 Pro", 400000, 128000, "text+image+file->text"),
    fm("openai/gpt-5-mini", "OpenAI: GPT-5 Mini", 400000, 128000, "text+image+file->text"),
    fm("openai/gpt-5-codex", "OpenAI: GPT-5 Codex", 400000, 128000, "text+image->text"),
    fm("openai/gpt-chat-latest", "OpenAI: GPT Chat Latest", 400000, 128000, "text+image+file->text"),
    fm("openai/gpt-4.1", "OpenAI: GPT-4.1", 1047576, None, "text+image+file->text"),
    fm("openai/gpt-4.1-mini", "OpenAI: GPT-4.1 Mini", 1047576, 32768, "text+image+file->text"),
    fm("openai/o1", "OpenAI: o1", 200000, 100000, "text+image+file->text"),
    fm("openai/o1-pro", "OpenAI: o1 Pro", 200000, 100000, "text+image+file->text"),
    fm("openai/o3", "OpenAI: o3", 200000, 100000, "text+image+file->text"),
    fm("openai/o3-pro", "OpenAI: o3 Pro", 200000, 100000, "text+image+file->text"),
    fm("openai/o4-mini", "OpenAI: o4 Mini", 200000, 100000, "text+image+file->text"),
    fm("openai/gpt-audio", "OpenAI: GPT Audio", 128000, 16384, "text+audio->text+audio"),
    fm("openai/gpt-audio-mini", "OpenAI: GPT Audio Mini", 128000, 16384, "text+audio->text+audio"),

    fm("google/gemini-3.5-flash", "Google: Gemini 3.5 Flash", 1048576, 65536, "text+image+file+audio+video->text"),
    fm("google/gemini-3.1-pro-preview", "Google: Gemini 3.1 Pro Preview", 1048576, 65536, "text+image+file+audio+video->text"),
    fm("google/gemini-3.1-flash-lite", "Google: Gemini 3.1 Flash Lite", 1048576, 65536, "text+image+file+audio+video->text"),
    fm("google/gemini-3-flash-preview", "Google: Gemini 3 Flash Preview", 1048576, 65535, "text+image+file+audio+video->text"),
    fm("google/gemini-2.5-pro", "Google: Gemini 2.5 Pro", 1048576, 65536, "text+image+file+audio+video->text"),
    fm("google/gemini-2.5-flash", "Google: Gemini 2.5 Flash", 1048576, 65535, "text+image+file+audio+video->text"),
    fm("google/gemini-2.5-flash-lite", "Google: Gemini 2.5 Flash Lite", 1048576, 65535, "text+image+file+audio+video->text"),
    fm("google/lyria-3-pro-preview", "Google: Lyria 3 Pro Preview", 1048576, 65536, "text+image->text+audio"),
    fm("google/lyria-3-clip-preview", "Google: Lyria 3 Clip Preview", 1048576, 65536, "text+image->text+audio"),

    fm("perplexity/sonar-pro-search", "Perplexity: Sonar Pro Search", 200000, 8000, "text+image->text"),
    fm("perplexity/sonar-pro", "Perplexity: Sonar Pro", 200000, 8000, "text+image->text"),
    fm("perplexity/sonar-reasoning-pro", "Perplexity: Sonar Reasoning Pro", 128000, None, "text+image->text"),
    fm("perplexity/sonar-deep-research", "Perplexity: Sonar Deep Research", 128000, None, "text->text"),
    fm("perplexity/sonar", "Perplexity: Sonar", 127072, None, "text+image->text"),

    fm("meta-llama/llama-4-maverick", "Meta: Llama 4 Maverick", 1048576, 16384, "text+image->text"),
    fm("meta-llama/llama-4-scout", "Meta: Llama 4 Scout", 10000000, 16384, "text+image->text"),
    fm("meta-llama/llama-3.3-70b-instruct", "Meta: Llama 3.3 70B Instruct", 131072, 16384, "text->text"),

    fm("deepseek/deepseek-v4-pro", "DeepSeek: V4 Pro", 1048576, 384000, "text->text"),
    fm("deepseek/deepseek-v4-flash", "DeepSeek: V4 Flash", 1048576, None, "text->text"),
    fm("deepseek/deepseek-v3.2", "DeepSeek: V3.2", 131072, 64000, "text->text"),
    fm("deepseek/deepseek-r1-0528", "DeepSeek: R1 0528", 163840, 32768, "text->text"),
    fm("deepseek/deepseek-r1", "DeepSeek: R1", 163840, 16000, "text->text"),

    fm("moonshotai/kimi-k2.7-code", "MoonshotAI: Kimi K2.7 Code", 262144, 16384, "text+image->text"),
    fm("moonshotai/kimi-k2.6", "MoonshotAI: Kimi K2.6", 262144, 262144, "text+image->text"),
    fm("moonshotai/kimi-k2-thinking", "MoonshotAI: Kimi K2 Thinking", 262144, 100352, "text->text"),

    fm("mistralai/mistral-large-2512", "Mistral: Mistral Large 3 2512", 262144, None, "text+image+file->text"),
    fm("mistralai/mistral-medium-3-5", "Mistral: Mistral Medium 3.5", 262144, None, "text+image+file->text"),
    fm("mistralai/devstral-2512", "Mistral: Devstral 2 2512", 262144, None, "text+file->text"),
    fm("mistralai/codestral-2508", "Mistral: Codestral 2508", 256000, None, "text+file->text"),
    fm("mistralai/voxtral-small-24b-2507", "Mistral: Voxtral Small 24B 2507", 32000, None, "text+file+audio->text"),

    fm("x-ai/grok-4.3", "xAI: Grok 4.3", 1000000, None, "text+image+file->text"),
    fm("x-ai/grok-4.20", "xAI: Grok 4.20", 2000000, None, "text+image+file->text"),
    fm("x-ai/grok-4.20-multi-agent", "xAI: Grok 4.20 Multi-Agent", 2000000, None, "text+image+file->text"),

    fm("qwen/qwen3.7-max", "Qwen: Qwen3.7 Max", 1000000, 65536, "text->text"),
    fm("qwen/qwen3.7-plus", "Qwen: Qwen3.7 Plus", 1000000, 65536, "text+image->text"),
    fm("qwen/qwen3-coder", "Qwen: Qwen3 Coder", 1048576, 65536, "text->text"),
    fm("qwen/qwen3-coder:free", "Qwen: Qwen3 Coder Free", 1048576, 262000, "text->text"),
    fm("qwen/qwen3-max-thinking", "Qwen: Qwen3 Max Thinking", 262144, 32768, "text->text"),
    fm("qwen/qwen-plus-2025-07-28:thinking", "Qwen: Qwen Plus 0728 Thinking", 1000000, 32768, "text->text"),

    fm("cohere/north-mini-code:free", "Cohere: North Mini Code Free", 256000, 64000, "text->text"),
    fm("sakana/fugu-ultra", "Sakana: Fugu Ultra", 1000000, 128000, "text+image->text"),
    fm("z-ai/glm-5.2", "Z.ai: GLM 5.2", 1048576, 131072, "text->text"),
    fm("nvidia/nemotron-3-ultra-550b-a55b", "NVIDIA: Nemotron 3 Ultra", 1000000, 16384, "text->text"),
    fm("poolside/laguna-xs-2.1", "Poolside: Laguna XS 2.1", 262144, 32768, "text->text"),
    fm("openrouter/auto", "OpenRouter: Auto Router", 2000000, None, "text+image+file->text"),
    fm("openrouter/free", "OpenRouter: Free Models Router", 200000, None, "text->text"),
    fm("openrouter/fusion", "OpenRouter: Fusion Router", 1000000, None, "text->text"),
    fm("openrouter/pareto-code", "OpenRouter: Pareto Code Router", 2000000, None, "text->text"),

    fm("openai/gpt-image-2", "OpenAI: GPT Image 2", None, None, "text+image->image", "images"),
    fm("openai/gpt-5.4-image-2", "OpenAI: GPT-5.4 Image 2", 272000, 128000, "text+image+file->text+image", "chat_or_images"),
    fm("google/gemini-3-pro-image", "Google: Nano Banana Pro", 65536, 32768, "text+image->image", "images"),
    fm("google/gemini-3.1-flash-image", "Google: Nano Banana 2", 131072, 32768, "text+image->image", "images"),
    fm("google/gemini-3.1-flash-lite-image", "Google: Nano Banana 2 Lite", 65536, 66000, "text+image->image", "images"),
    fm("google/gemini-2.5-flash-image", "Google: Nano Banana", 32768, 32768, "text+image->image", "images"),
    fm("bytedance-seed/seedream-4.5", "ByteDance Seed: Seedream 4.5", None, None, "text+image->image", "images"),
    fm("google/veo-3.1", "Google: Veo 3.1", None, None, "text->video", "videos"),
    fm("google/veo-3.1-fast", "Google: Veo 3.1 Fast", None, None, "text->video", "videos"),
    fm("bytedance/seedance-2.0", "ByteDance: Seedance 2.0", None, None, "text->video", "videos"),
    fm("bytedance/seedance-2.0-fast", "ByteDance: Seedance 2.0 Fast", None, None, "text->video", "videos"),
    fm("google/gemini-3.1-flash-tts-preview", "Google: Gemini 3.1 Flash TTS Preview", None, None, "text->audio", "audio/speech"),
]

TILDE_MODELS: List[str] = [
    "~anthropic/claude-sonnet-latest",
    "~anthropic/claude-opus-latest",
    "~anthropic/claude-haiku-latest",
    "~anthropic/claude-fable-latest",
    "~google/gemini-flash-latest",
    "~google/gemini-pro-latest",
    "~openai/gpt-latest",
    "~openai/gpt-mini-latest",
    "~moonshotai/kimi-latest",
]

CURATED_ALIASES: Dict[str, str] = {
    "claude sonnet latest": "~anthropic/claude-sonnet-latest",
    "latest sonnet": "~anthropic/claude-sonnet-latest",
    "sonnet latest": "~anthropic/claude-sonnet-latest",
    "claude opus latest": "~anthropic/claude-opus-latest",
    "opus latest": "~anthropic/claude-opus-latest",
    "claude haiku latest": "~anthropic/claude-haiku-latest",
    "haiku latest": "~anthropic/claude-haiku-latest",
    "claude fable latest": "~anthropic/claude-fable-latest",
    "fable latest": "~anthropic/claude-fable-latest",
    "gemini flash latest": "~google/gemini-flash-latest",
    "gemini pro latest": "~google/gemini-pro-latest",
    "gpt latest": "~openai/gpt-latest",
    "gpt mini latest": "~openai/gpt-mini-latest",
    "kimi latest": "~moonshotai/kimi-latest",

    "claude sonnet 5": "anthropic/claude-sonnet-5",
    "sonnet 5": "anthropic/claude-sonnet-5",
    "claude fable 5": "anthropic/claude-fable-5",
    "fable 5": "anthropic/claude-fable-5",
    "claude mythos": "anthropic/claude-fable-5",
    "claude opus 4.8": "anthropic/claude-opus-4.8",
    "opus 4.8": "anthropic/claude-opus-4.8",
    "opus fast": "anthropic/claude-opus-4.8-fast",
    "claude sonnet 4.6": "anthropic/claude-sonnet-4.6",
    "sonnet 4.6": "anthropic/claude-sonnet-4.6",
    "claude haiku 4.5": "anthropic/claude-haiku-4.5",
    "haiku 4.5": "anthropic/claude-haiku-4.5",

    "gpt 5.5": "openai/gpt-5.5",
    "gpt 5.5 pro": "openai/gpt-5.5-pro",
    "gpt 5.4": "openai/gpt-5.4",
    "gpt 5.4 pro": "openai/gpt-5.4-pro",
    "gpt 5.4 mini": "openai/gpt-5.4-mini",
    "gpt 5.4 image 2": "openai/gpt-5.4-image-2",
    "gpt 5": "openai/gpt-5",
    "gpt 5 chat": "openai/gpt-5-chat",
    "gpt 5 pro": "openai/gpt-5-pro",
    "gpt 5 mini": "openai/gpt-5-mini",
    "gpt codex": "openai/gpt-5-codex",
    "gpt chat latest": "openai/gpt-chat-latest",
    "chatgpt latest": "openai/gpt-chat-latest",
    "gpt 4.1": "openai/gpt-4.1",
    "gpt 4.1 mini": "openai/gpt-4.1-mini",
    "o1": "openai/o1",
    "o1 pro": "openai/o1-pro",
    "o3": "openai/o3",
    "o3 pro": "openai/o3-pro",
    "o4 mini": "openai/o4-mini",
    "gpt audio": "openai/gpt-audio",
    "gpt audio mini": "openai/gpt-audio-mini",
    "gpt image 2": "openai/gpt-image-2",
    "openai gpt image 2": "openai/gpt-image-2",

    "gemini 3.5 flash": "google/gemini-3.5-flash",
    "gemini 3.1 pro": "google/gemini-3.1-pro-preview",
    "gemini 3.1 pro preview": "google/gemini-3.1-pro-preview",
    "gemini 3.1 flash lite": "google/gemini-3.1-flash-lite",
    "gemini 3 flash": "google/gemini-3-flash-preview",
    "gemini 2.5 pro": "google/gemini-2.5-pro",
    "gemini 2.5 flash": "google/gemini-2.5-flash",
    "gemini 2.5 flash lite": "google/gemini-2.5-flash-lite",
    "nano banana pro": "google/gemini-3-pro-image",
    "gemini 3 pro image": "google/gemini-3-pro-image",
    "nano banana 2": "google/gemini-3.1-flash-image",
    "gemini 3.1 flash image": "google/gemini-3.1-flash-image",
    "nano banana 2 lite": "google/gemini-3.1-flash-lite-image",
    "nano banana": "google/gemini-2.5-flash-image",
    "lyria": "google/lyria-3-pro-preview",
    "lyria pro": "google/lyria-3-pro-preview",
    "lyria clip": "google/lyria-3-clip-preview",
    "music generation": "google/lyria-3-pro-preview",

    "sonar": "perplexity/sonar",
    "sonar pro": "perplexity/sonar-pro",
    "sonar pro search": "perplexity/sonar-pro-search",
    "sonar deep research": "perplexity/sonar-deep-research",
    "sonar reasoning pro": "perplexity/sonar-reasoning-pro",

    "llama 4 maverick": "meta-llama/llama-4-maverick",
    "llama 4 scout": "meta-llama/llama-4-scout",
    "llama 3.3 70b": "meta-llama/llama-3.3-70b-instruct",

    "deepseek v4 pro": "deepseek/deepseek-v4-pro",
    "deepseek v4 flash": "deepseek/deepseek-v4-flash",
    "deepseek v4": "deepseek/deepseek-v4-pro",
    "deepseek v3.2": "deepseek/deepseek-v3.2",
    "deepseek r1": "deepseek/deepseek-r1-0528",
    "deepseek r1 0528": "deepseek/deepseek-r1-0528",

    "kimi": "moonshotai/kimi-k2.6",
    "kimi k2": "moonshotai/kimi-k2.6",
    "kimi k2.6": "moonshotai/kimi-k2.6",
    "kimi code": "moonshotai/kimi-k2.7-code",
    "kimi k2.7 code": "moonshotai/kimi-k2.7-code",
    "kimi thinking": "moonshotai/kimi-k2-thinking",

    "mistral large": "mistralai/mistral-large-2512",
    "mistral medium": "mistralai/mistral-medium-3-5",
    "mistral medium 3.5": "mistralai/mistral-medium-3-5",
    "devstral": "mistralai/devstral-2512",
    "codestral": "mistralai/codestral-2508",
    "voxtral": "mistralai/voxtral-small-24b-2507",

    "grok 4.3": "x-ai/grok-4.3",
    "grok 4.20": "x-ai/grok-4.20",
    "grok 4.20 multi agent": "x-ai/grok-4.20-multi-agent",
    "grok multi agent": "x-ai/grok-4.20-multi-agent",

    "qwen 3.7 max": "qwen/qwen3.7-max",
    "qwen max latest": "qwen/qwen3.7-max",
    "qwen 3.7 plus": "qwen/qwen3.7-plus",
    "qwen plus latest": "qwen/qwen3.7-plus",
    "qwen coder": "qwen/qwen3-coder",
    "qwen coder free": "qwen/qwen3-coder:free",
    "qwen max thinking": "qwen/qwen3-max-thinking",

    "fugu": "sakana/fugu-ultra",
    "fugu ultra": "sakana/fugu-ultra",
    "glm 5.2": "z-ai/glm-5.2",
    "nemotron 3 ultra": "nvidia/nemotron-3-ultra-550b-a55b",
    "laguna xs 2.1": "poolside/laguna-xs-2.1",
    "laguna xs2": "poolside/laguna-xs-2.1",

    "auto": "openrouter/auto",
    "openrouter auto": "openrouter/auto",
    "free router": "openrouter/free",
    "fusion": "openrouter/fusion",
    "pareto code": "openrouter/pareto-code",

    "seedream": "bytedance-seed/seedream-4.5",
    "seedream 4.5": "bytedance-seed/seedream-4.5",
    "veo 3.1": "google/veo-3.1",
    "veo 3.1 fast": "google/veo-3.1-fast",
    "seedance 2": "bytedance/seedance-2.0",
    "seedance 2 fast": "bytedance/seedance-2.0-fast",
    "gemini tts": "google/gemini-3.1-flash-tts-preview",
}

KNOWN_NOT_LIVE_RAW: Dict[str, str] = {
    "anthropic/claude-sonnet-latest": "Use ~anthropic/claude-sonnet-latest (tilde prefix required)",
    "anthropic/claude-opus-latest": "Use ~anthropic/claude-opus-latest (tilde prefix required)",
    "anthropic/claude-haiku-latest": "Use ~anthropic/claude-haiku-latest (tilde prefix required)",
    "anthropic/claude-fable-latest": "Use ~anthropic/claude-fable-latest (tilde prefix required)",
    "google/gemini-flash-latest": "Use ~google/gemini-flash-latest (tilde prefix required)",
    "google/gemini-pro-latest": "Use ~google/gemini-pro-latest (tilde prefix required)",
    "openai/gpt-latest": "Use ~openai/gpt-latest (tilde prefix required)",
}


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


def simple_key(text: str) -> str:
    return " ".join(tokenize(text, remove_stop=True, expand_decimals=True))


def canonical(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


EXACT_ALIASES = {simple_key(k): v for k, v in CURATED_ALIASES.items()}
LATEST_ALIASES = {simple_key(m.split("/", 1)[1].replace("-", " ").replace(".", " ")): m for m in TILDE_MODELS}
KNOWN_NOT_LIVE = {simple_key(k): v for k, v in KNOWN_NOT_LIVE_RAW.items()}


def split_suffix_chain(suffix: Optional[str]) -> List[str]:
    if not suffix:
        return []
    return [s.lower() for s in suffix.split(":") if s]


def split_model_suffixes(model_id: str) -> Tuple[str, List[str]]:
    parts = model_id.split(":")
    if len(parts) == 1:
        return model_id, []
    suffixes = [p.lower() for p in parts[1:]]
    if all(s in KNOWN_SUFFIXES for s in suffixes):
        return parts[0], suffixes
    return model_id, []


def strip_model_suffix(model_id: str) -> Tuple[str, Optional[str]]:
    base, suffixes = split_model_suffixes(model_id)
    return base, ":".join(suffixes) if suffixes else None


def apply_suffix(model_id: str, suffix: Optional[str]) -> str:
    requested = split_suffix_chain(suffix)
    if not requested:
        return model_id
    base, existing = split_model_suffixes(model_id)
    suffixes = existing[:]
    for s in requested:
        if s not in suffixes:
            suffixes.append(s)
    return base + "".join(f":{s}" for s in suffixes)


def parse_slug_like(text: str) -> Optional[Tuple[str, Optional[str]]]:
    t = text.strip()
    m = re.fullmatch(r"(~?[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)((?::[A-Za-z][A-Za-z0-9_-]*)*)", t)
    if not m:
        return None
    raw_suffix = m.group(2).lstrip(":")
    return m.group(1), raw_suffix.replace(":", ":").lower() if raw_suffix else None


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
    try:
        path = cache_file()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"fetched_at": time.time(), "models": models}, f)
    except Exception:
        pass


def fetch_live_models() -> List[Dict[str, Any]]:
    headers = {"User-Agent": "openrouter-caller-resolver/4.1"}
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


def normalize_model(m: Dict[str, Any], source_name: str) -> Dict[str, Any]:
    item = dict(m)
    item.setdefault("name", item.get("id", ""))
    item.setdefault("context_length", None)
    if not item.get("modality") and isinstance(item.get("architecture"), dict):
        item["modality"] = item["architecture"].get("modality", "")
    item.setdefault("modality", "")
    item.setdefault("_source", source_name)
    return item


def merge_models(primary: Iterable[Dict[str, Any]], extras: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    primary_list = list(primary)
    merged: Dict[str, Dict[str, Any]] = {}
    for m in primary_list:
        mid = m.get("id")
        if mid:
            merged[mid] = normalize_model(m, "live_or_cache")

    # When live/cache data exists, only add static media exceptions.
    include_all_static = not bool(primary_list)
    for m in extras:
        mid = m.get("id")
        if not mid:
            continue
        if include_all_static or mid in KNOWN_MEDIA_SLUGS:
            merged.setdefault(mid, normalize_model(m, "static"))
    return list(merged.values())


def load_models(force_refresh: bool = False, offline: bool = False) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    cache = read_cache()
    cache_fresh = bool(cache and (time.time() - float(cache.get("fetched_at", 0))) < CACHE_TTL_SECONDS)

    if offline:
        cached = cache.get("models", []) if cache else []
        return merge_models(cached, FALLBACK_MODELS), {"live_ok": False, "cache_used": bool(cache), "source": "offline"}

    if cache_fresh and not force_refresh:
        return merge_models(cache.get("models", []), FALLBACK_MODELS), {"live_ok": False, "cache_used": True, "source": "fresh_cache"}

    try:
        live = fetch_live_models()
        write_cache(live)
        return merge_models(live, FALLBACK_MODELS), {"live_ok": True, "cache_used": False, "source": "live"}
    except Exception as e:
        cached = cache.get("models", []) if cache else []
        return merge_models(cached, FALLBACK_MODELS), {
            "live_ok": False,
            "cache_used": bool(cache),
            "source": "cache_or_static",
            "error": str(e),
        }


def extract_suffix(query: str) -> Tuple[str, Optional[str]]:
    pattern = r":(" + "|".join(sorted(KNOWN_SUFFIXES)) + r")\b"
    matches = re.findall(pattern, query.lower())
    if matches:
        cleaned = re.sub(pattern, " ", query, flags=re.IGNORECASE)
        return cleaned, ":".join(matches)

    raw_key = simple_key(query)
    if raw_key in EXACT_ALIASES:
        return query, None

    toks = tokenize(query, remove_stop=False, expand_decimals=False)
    if not toks:
        return query, None
    suffix: Optional[str] = None
    last = toks[-1]
    if last in KNOWN_SUFFIXES:
        suffix = last
    elif "free" in toks and "tier" in toks:
        suffix = "free"
    elif "extended" in toks and "context" in toks:
        suffix = "extended"
    elif "thinking" in toks and "mode" in toks:
        suffix = "thinking"
    if suffix:
        cleaned = " ".join(t for t in toks if t != suffix and not (suffix == "free" and t == "tier"))
        return cleaned, suffix
    return query, None


def model_max_output(m: Dict[str, Any]) -> Any:
    top = m.get("top_provider") if isinstance(m.get("top_provider"), dict) else {}
    for key in ("max_completion_tokens", "max_output_tokens", "max_output"):
        if key in m and m[key] is not None:
            return m[key]
    for key in ("max_completion_tokens", "max_output_tokens"):
        if key in top and top[key] is not None:
            return top[key]
    return "?"


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
        else:
            score -= 14
        if hit:
            matched += 1

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
            score -= 18

    q_decimals = {t for t in q_tokens if re.fullmatch(r"\d+\.\d+", t)}
    cand_decimals = {t for t in candidate_tokens if re.fullmatch(r"\d+\.\d+", t)}
    if q_decimals and cand_decimals and q_decimals.isdisjoint(cand_decimals):
        score -= 80

    requested_suffixes = set(split_suffix_chain(requested_suffix))
    candidate_suffixes = set(split_suffix_chain(suffix))
    if candidate_suffixes:
        if requested_suffixes and requested_suffixes.issubset(candidate_suffixes):
            score += 80
        elif not requested_suffixes:
            score -= 45
    if requested_suffixes and not candidate_suffixes:
        score += 5

    if "preview" in candidate_tokens and "preview" not in q_set:
        score -= 12
    if provider == "openrouter" and not ({"openrouter", "auto", "free", "fusion", "router", "pareto"} & q_set):
        score -= 60
    if latest_mode:
        score += 60 if mid.startswith("~") else -70

    return score


def rank(
    query: str,
    models: List[Dict[str, Any]],
    requested_suffix: Optional[str] = None,
    latest_mode: bool = False,
    top_n: int = 8,
) -> List[Dict[str, Any]]:
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
    return (top - second) <= max(AMBIGUITY_MIN_GAP, int(top * AMBIGUITY_RATIO))


def find_model(model_id: str, models: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for m in models:
        if m.get("id") == model_id:
            return m
    return None


def suffixes_valid(suffix: Optional[str]) -> bool:
    return all(s in KNOWN_SUFFIXES for s in split_suffix_chain(suffix))


def online_warning(suffix: Optional[str]) -> List[str]:
    return [":online is deprecated; prefer OpenRouter web_search tooling when available."] if "online" in split_suffix_chain(suffix) else []


def resolve(query: str, models: List[Dict[str, Any]], meta: Dict[str, Any], top_n: int = 8) -> Dict[str, Any]:
    query = query.strip()
    if not query:
        return {"status": "ERROR", "error": "empty_query"}

    parsed = parse_slug_like(query)
    ids = {m.get("id") for m in models}

    if parsed:
        base, suffix = parsed
        if not suffixes_valid(suffix):
            return {
                "status": "ERROR",
                "error": "unknown_suffix",
                "message": f"Unknown suffix in :{suffix}. Known: {', '.join(sorted(KNOWN_SUFFIXES))}",
            }

        full = apply_suffix(base, suffix)
        full_model = find_model(full, models)
        base_model = find_model(base, models)
        if full_model or base_model:
            m = full_model or base_model or {"id": full, "name": full}
            warnings = online_warning(suffix)
            if full.startswith("~"):
                warnings.append("Tilde latest-alias: target model may change over time.")
            return {"status": "OK", "resolution": "validated_slug", "use_slug": full, "model": m, "warnings": warnings}

        if base in KNOWN_MEDIA_SLUGS:
            endpoint = KNOWN_MEDIA_SLUGS[base]
            m = {"id": full, "name": full, "endpoint": endpoint}
            warnings = [f"Media-endpoint model: use /api/v1/{endpoint} (not /api/v1/chat/completions)."]
            warnings.extend(online_warning(suffix))
            return {"status": "OK", "resolution": "known_media_slug", "use_slug": full, "model": m, "warnings": warnings}

        if not base.startswith("~") and base.endswith("-latest") and ("~" + base) in ids:
            corrected = apply_suffix("~" + base, suffix)
            m = find_model("~" + base, models) or {"id": corrected, "name": corrected}
            return {
                "status": "OK",
                "resolution": "corrected_tilde_latest",
                "use_slug": corrected,
                "model": m,
                "warnings": ["Added required '~' prefix for OpenRouter latest-alias slug."] + online_warning(suffix),
            }

        if not meta.get("live_ok") and not meta.get("cache_used"):
            return {
                "status": "UNVERIFIED",
                "resolution": "slug_passthrough_no_live_models",
                "use_slug": full,
                "model": {"id": full, "name": full},
                "warnings": ["Could not fetch/validate model list; exact-looking slug passed through unverified."] + online_warning(suffix),
            }

        return {
            "status": "ERROR",
            "error": "invalid_slug",
            "message": f"Slug is not in the current OpenRouter model list: {full}",
            "candidates": rank(base.replace("/", " "), models, suffix, latest_mode=False, top_n=5),
        }

    raw_key = simple_key(query)
    if raw_key in KNOWN_NOT_LIVE:
        return {"status": "ERROR", "error": "known_not_live", "message": KNOWN_NOT_LIVE[raw_key], "candidates": []}

    if raw_key in EXACT_ALIASES:
        slug = EXACT_ALIASES[raw_key]
        m = find_model(slug, models) or {"id": slug, "name": slug, "endpoint": KNOWN_MEDIA_SLUGS.get(slug)}
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

    if clean_key in KNOWN_NOT_LIVE:
        return {"status": "ERROR", "error": "known_not_live", "message": KNOWN_NOT_LIVE[clean_key], "candidates": []}

    if clean_key in EXACT_ALIASES:
        slug = apply_suffix(EXACT_ALIASES[clean_key], requested_suffix)
        base, _ = strip_model_suffix(slug)
        m = find_model(slug, models) or find_model(base, models) or {"id": slug, "name": slug, "endpoint": KNOWN_MEDIA_SLUGS.get(base)}
        return {
            "status": "OK",
            "resolution": "curated_alias_plus_suffix",
            "use_slug": slug,
            "model": m,
            "warnings": online_warning(requested_suffix),
        }

    if clean_key in LATEST_ALIASES:
        slug = apply_suffix(LATEST_ALIASES[clean_key], requested_suffix)
        base, _ = strip_model_suffix(slug)
        m = find_model(base, models) or {"id": slug, "name": slug}
        return {
            "status": "OK",
            "resolution": "curated_latest_alias_plus_suffix",
            "use_slug": slug,
            "model": m,
            "warnings": ["Tilde latest-alias: target model may change over time."] + online_warning(requested_suffix),
        }

    latest_mode = "latest" in tokenize(query, remove_stop=False, expand_decimals=False)
    results = rank(cleaned_query, models, requested_suffix, latest_mode=latest_mode, top_n=top_n)

    if not results or int(results[0]["_score"]) < MIN_ACCEPT_SCORE:
        return {
            "status": "ERROR",
            "error": "no_confident_match",
            "message": f"No confident model match for: {query}",
            "candidates": results,
        }

    warnings = online_warning(requested_suffix)
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
        if m.get("endpoint"):
            print(f"ENDPOINT_HINT={m.get('endpoint')}")
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
            "reasoning": m.get("reasoning"),
            "supported_parameters": m.get("supported_parameters"),
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
            f"{m.get('id',''):72s} "
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
    models, meta = load_models(force_refresh=args.refresh or force_for_exact_slug, offline=args.offline)

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
