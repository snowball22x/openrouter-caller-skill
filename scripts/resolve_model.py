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
    "opus", "sonnet", "turbo", "safeguard", "vision", "code",
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


# Static fallback is intentionally curated, not exhaustive. Live /models is authoritative.
FALLBACK_MODELS: List[Dict[str, Any]] = [
    # Tilde latest aliases visible in the supplied live table.
    fm("~anthropic/claude-sonnet-latest", "Anthropic Claude Sonnet Latest", 1000000, 128000, "text+image+file->text"),
    fm("~anthropic/claude-opus-latest", "Anthropic Claude Opus Latest", 1000000, 128000, "text+image+file->text"),
    fm("~anthropic/claude-haiku-latest", "Anthropic Claude Haiku Latest", 200000, 64000, "text+image+file->text"),
    fm("~anthropic/claude-fable-latest", "Anthropic Claude Fable Latest", 1000000, 128000, "text+image+file->text"),
    fm("~google/gemini-flash-latest", "Google Gemini Flash Latest", 1048576, 65536, "text+image+file+audio+video->text"),
    fm("~google/gemini-pro-latest", "Google Gemini Pro Latest", 1048576, 65536, "text+image+file+audio+video->text"),
    fm("~openai/gpt-latest", "OpenAI GPT Latest", 1050000, 128000, "text+image+file->text"),
    fm("~openai/gpt-mini-latest", "OpenAI GPT Mini Latest", 400000, 128000, "text+image+file->text"),
    fm("~moonshotai/kimi-latest", "MoonshotAI Kimi Latest", 262144, 262144, "text+image->text"),

    # Anthropic.
    fm("anthropic/claude-sonnet-5", "Anthropic: Claude Sonnet 5", 1000000, 128000, "text+image+file->text"),
    fm("anthropic/claude-fable-5", "Anthropic: Claude Fable 5", 1000000, 128000, "text+image+file->text"),
    fm("anthropic/claude-sonnet-4.6", "Anthropic: Claude Sonnet 4.6", 1000000, 128000, "text+image+file->text"),
    fm("anthropic/claude-sonnet-4.5", "Anthropic: Claude Sonnet 4.5", 1000000, 64000, "text+image+file->text"),
    fm("anthropic/claude-sonnet-4", "Anthropic: Claude Sonnet 4", 1000000, 64000, "text+image+file->text"),
    fm("anthropic/claude-opus-4.8", "Anthropic: Claude Opus 4.8", 1000000, 128000, "text+image+file->text"),
    fm("anthropic/claude-opus-4.8-fast", "Anthropic: Claude Opus 4.8 Fast", 1000000, 128000, "text+image+file->text"),
    fm("anthropic/claude-opus-4.7", "Anthropic: Claude Opus 4.7", 1000000, 128000, "text+image+file->text"),
    fm("anthropic/claude-opus-4.7-fast", "Anthropic: Claude Opus 4.7 Fast", 1000000, 128000, "text+image+file->text"),
    fm("anthropic/claude-opus-4.6", "Anthropic: Claude Opus 4.6", 1000000, 128000, "text+image+file->text"),
    fm("anthropic/claude-opus-4.5", "Anthropic: Claude Opus 4.5", 200000, 64000, "text+image+file->text"),
    fm("anthropic/claude-opus-4.1", "Anthropic: Claude Opus 4.1", 200000, 32000, "text+image+file->text"),
    fm("anthropic/claude-opus-4", "Anthropic: Claude Opus 4", 200000, 32000, "text+image+file->text"),
    fm("anthropic/claude-haiku-4.5", "Anthropic: Claude Haiku 4.5", 200000, 64000, "text+image+file->text"),
    fm("anthropic/claude-3-haiku", "Anthropic: Claude 3 Haiku", 200000, 4096, "text+image->text"),

    # OpenAI.
    fm("openai/gpt-5.5", "OpenAI: GPT-5.5", 1050000, 128000, "text+image+file->text"),
    fm("openai/gpt-5.5-pro", "OpenAI: GPT-5.5 Pro", 1050000, 128000, "text+image+file->text"),
    fm("openai/gpt-5.4", "OpenAI: GPT-5.4", 1050000, 128000, "text+image+file->text"),
    fm("openai/gpt-5.4-pro", "OpenAI: GPT-5.4 Pro", 1050000, 128000, "text+image+file->text"),
    fm("openai/gpt-5.4-mini", "OpenAI: GPT-5.4 Mini", 400000, 128000, "text+image+file->text"),
    fm("openai/gpt-5.4-nano", "OpenAI: GPT-5.4 Nano", 400000, 128000, "text+image+file->text"),
    fm("openai/gpt-5.4-image-2", "OpenAI: GPT-5.4 Image 2", 272000, 128000, "text+image+file->text+image"),
    fm("openai/gpt-5.3-chat", "OpenAI: GPT-5.3 Chat", 128000, 16384, "text+image+file->text"),
    fm("openai/gpt-5.3-codex", "OpenAI: GPT-5.3 Codex", 400000, 128000, "text+image->text"),
    fm("openai/gpt-5.2", "OpenAI: GPT-5.2", 400000, 128000, "text+image+file->text"),
    fm("openai/gpt-5.2-chat", "OpenAI: GPT-5.2 Chat", 128000, 16384, "text+image+file->text"),
    fm("openai/gpt-5.2-pro", "OpenAI: GPT-5.2 Pro", 400000, 128000, "text+image+file->text"),
    fm("openai/gpt-5.2-codex", "OpenAI: GPT-5.2 Codex", 400000, 128000, "text+image->text"),
    fm("openai/gpt-5.1", "OpenAI: GPT-5.1", 400000, 128000, "text+image+file->text"),
    fm("openai/gpt-5.1-chat", "OpenAI: GPT-5.1 Chat", 128000, 32000, "text+image+file->text"),
    fm("openai/gpt-5.1-codex", "OpenAI: GPT-5.1 Codex", 400000, 128000, "text+image->text"),
    fm("openai/gpt-5.1-codex-max", "OpenAI: GPT-5.1 Codex Max", 400000, 128000, "text+image->text"),
    fm("openai/gpt-5.1-codex-mini", "OpenAI: GPT-5.1 Codex Mini", 400000, 100000, "text+image->text"),
    fm("openai/gpt-5", "OpenAI: GPT-5", 400000, 128000, "text+image+file->text"),
    fm("openai/gpt-5-chat", "OpenAI: GPT-5 Chat", 128000, 16384, "text+image+file->text"),
    fm("openai/gpt-5-pro", "OpenAI: GPT-5 Pro", 400000, 128000, "text+image+file->text"),
    fm("openai/gpt-5-mini", "OpenAI: GPT-5 Mini", 400000, 128000, "text+image+file->text"),
    fm("openai/gpt-5-nano", "OpenAI: GPT-5 Nano", 400000, None, "text+image+file->text"),
    fm("openai/gpt-5-codex", "OpenAI: GPT-5 Codex", 400000, 128000, "text+image->text"),
    fm("openai/gpt-5-image", "OpenAI: GPT-5 Image", 400000, 128000, "text+image+file->text+image"),
    fm("openai/gpt-5-image-mini", "OpenAI: GPT-5 Image Mini", 400000, 128000, "text+image+file->text+image"),
    fm("openai/gpt-chat-latest", "OpenAI: GPT Chat Latest", 400000, 128000, "text+image+file->text"),
    fm("openai/gpt-4.1", "OpenAI: GPT-4.1", 1047576, None, "text+image+file->text"),
    fm("openai/gpt-4.1-mini", "OpenAI: GPT-4.1 Mini", 1047576, 32768, "text+image+file->text"),
    fm("openai/gpt-4.1-nano", "OpenAI: GPT-4.1 Nano", 1047576, 32768, "text+image+file->text"),
    fm("openai/o1", "OpenAI: o1", 200000, 100000, "text+image+file->text"),
    fm("openai/o1-pro", "OpenAI: o1 Pro", 200000, 100000, "text+image+file->text"),
    fm("openai/o3", "OpenAI: o3", 200000, 100000, "text+image+file->text"),
    fm("openai/o3-pro", "OpenAI: o3 Pro", 200000, 100000, "text+image+file->text"),
    fm("openai/o3-mini", "OpenAI: o3 Mini", 200000, 100000, "text+file->text"),
    fm("openai/o3-mini-high", "OpenAI: o3 Mini High", 200000, 100000, "text+file->text"),
    fm("openai/o3-deep-research", "OpenAI: o3 Deep Research", 200000, 100000, "text+image+file->text"),
    fm("openai/o4-mini", "OpenAI: o4 Mini", 200000, 100000, "text+image+file->text"),
    fm("openai/o4-mini-high", "OpenAI: o4 Mini High", 200000, 100000, "text+image+file->text"),
    fm("openai/o4-mini-deep-research", "OpenAI: o4 Mini Deep Research", 200000, 100000, "text+image+file->text"),
    fm("openai/gpt-audio", "OpenAI: GPT Audio", 128000, 16384, "text+audio->text+audio"),
    fm("openai/gpt-audio-mini", "OpenAI: GPT Audio Mini", 128000, 16384, "text+audio->text+audio"),

    # Google Gemini/media.
    fm("google/gemini-3.5-flash", "Google: Gemini 3.5 Flash", 1048576, 65536, "text+image+file+audio+video->text"),
    fm("google/gemini-3.1-pro-preview", "Google: Gemini 3.1 Pro Preview", 1048576, 65536, "text+image+file+audio+video->text"),
    fm("google/gemini-3.1-pro-preview-customtools", "Google: Gemini 3.1 Pro Preview Custom Tools", 1048756, 65536, "text+image+file+audio+video->text"),
    fm("google/gemini-3.1-flash-lite", "Google: Gemini 3.1 Flash Lite", 1048576, 65536, "text+image+file+audio+video->text"),
    fm("google/gemini-3.1-flash-lite-preview", "Google: Gemini 3.1 Flash Lite Preview", 1048576, 65536, "text+image+file+audio+video->text"),
    fm("google/gemini-3-flash-preview", "Google: Gemini 3 Flash Preview", 1048576, 65535, "text+image+file+audio+video->text"),
    fm("google/gemini-3.1-flash-image", "Google: Nano Banana 2 (Gemini 3.1 Flash Image)", 131072, 32768, "text+image->text+image"),
    fm("google/gemini-3.1-flash-image-preview", "Google: Nano Banana 2 (Gemini 3.1 Flash Image Preview)", 131072, 32768, "text+image->text+image"),
    fm("google/gemini-3.1-flash-lite-image", "Google: Nano Banana 2 Lite (Gemini 3.1 Flash Lite Image)", 65536, 66000, "text+image->text+image"),
    fm("google/gemini-3-pro-image", "Google: Nano Banana Pro (Gemini 3 Pro Image)", 65536, 32768, "text+image->text+image"),
    fm("google/gemini-3-pro-image-preview", "Google: Nano Banana Pro (Gemini 3 Pro Image Preview)", 65536, 32768, "text+image->text+image"),
    fm("google/gemini-2.5-pro", "Google: Gemini 2.5 Pro", 1048576, 65536, "text+image+file+audio+video->text"),
    fm("google/gemini-2.5-pro-preview", "Google: Gemini 2.5 Pro Preview", 1048576, 65536, "text+image+file+audio->text"),
    fm("google/gemini-2.5-flash", "Google: Gemini 2.5 Flash", 1048576, 65535, "text+image+file+audio+video->text"),
    fm("google/gemini-2.5-flash-lite", "Google: Gemini 2.5 Flash Lite", 1048576, 65535, "text+image+file+audio+video->text"),
    fm("google/gemini-2.5-flash-image", "Google: Nano Banana (Gemini 2.5 Flash Image)", 32768, 32768, "text+image->text+image"),
    fm("google/lyria-3-pro-preview", "Google: Lyria 3 Pro Preview", 1048576, 65536, "text+image->text+audio"),
    fm("google/lyria-3-clip-preview", "Google: Lyria 3 Clip Preview", 1048576, 65536, "text+image->text+audio"),

    # Perplexity.
    fm("perplexity/sonar-pro-search", "Perplexity: Sonar Pro Search", 200000, 8000, "text+image->text"),
    fm("perplexity/sonar-pro", "Perplexity: Sonar Pro", 200000, 8000, "text+image->text"),
    fm("perplexity/sonar-reasoning-pro", "Perplexity: Sonar Reasoning Pro", 128000, None, "text+image->text"),
    fm("perplexity/sonar-deep-research", "Perplexity: Sonar Deep Research", 128000, None, "text->text"),
    fm("perplexity/sonar", "Perplexity: Sonar", 127072, None, "text+image->text"),

    # Open/open-weight and specialists.
    fm("meta-llama/llama-4-maverick", "Meta: Llama 4 Maverick", 1048576, 16384, "text+image->text"),
    fm("meta-llama/llama-4-scout", "Meta: Llama 4 Scout", 10000000, 16384, "text+image->text"),
    fm("meta-llama/llama-guard-4-12b", "Meta: Llama Guard 4 12B", 163840, 16384, "text+image->text"),
    fm("meta-llama/llama-3.3-70b-instruct", "Meta: Llama 3.3 70B Instruct", 131072, 16384, "text->text"),
    fm("meta-llama/llama-3.3-70b-instruct:free", "Meta: Llama 3.3 70B Instruct Free", 131072, None, "text->text"),

    fm("deepseek/deepseek-chat", "DeepSeek: Chat", 131072, 16000, "text->text"),
    fm("deepseek/deepseek-chat-v3-0324", "DeepSeek: Chat V3 0324", 163840, 16384, "text->text"),
    fm("deepseek/deepseek-chat-v3.1", "DeepSeek: Chat V3.1", 163840, 32768, "text->text"),
    fm("deepseek/deepseek-v3.1-terminus", "DeepSeek: V3.1 Terminus", 163840, 32768, "text->text"),
    fm("deepseek/deepseek-v3.2", "DeepSeek: V3.2", 131072, 64000, "text->text"),
    fm("deepseek/deepseek-v3.2-exp", "DeepSeek: V3.2 Exp", 163840, 65536, "text->text"),
    fm("deepseek/deepseek-r1", "DeepSeek: R1", 163840, 16000, "text->text"),
    fm("deepseek/deepseek-r1-0528", "DeepSeek: R1 0528", 163840, 32768, "text->text"),
    fm("deepseek/deepseek-r1-distill-llama-70b", "DeepSeek: R1 Distill Llama 70B", 128000, 8192, "text->text"),
    fm("deepseek/deepseek-v4-pro", "DeepSeek: V4 Pro", 1048576, 384000, "text->text"),
    fm("deepseek/deepseek-v4-flash", "DeepSeek: V4 Flash", 1048576, None, "text->text"),

    fm("moonshotai/kimi-k2.7-code", "MoonshotAI: Kimi K2.7 Code", 262144, 16384, "text+image->text"),
    fm("moonshotai/kimi-k2.6", "MoonshotAI: Kimi K2.6", 262144, 262144, "text+image->text"),
    fm("moonshotai/kimi-k2.5", "MoonshotAI: Kimi K2.5", 262144, None, "text+image->text"),
    fm("moonshotai/kimi-k2-thinking", "MoonshotAI: Kimi K2 Thinking", 262144, 100352, "text->text"),
    fm("moonshotai/kimi-k2-0905", "MoonshotAI: Kimi K2 0905", 262144, 100352, "text->text"),
    fm("moonshotai/kimi-k2", "MoonshotAI: Kimi K2 0711", 131072, 100352, "text->text"),

    fm("mistralai/mistral-large-2512", "Mistral: Mistral Large 3 2512", 262144, None, "text+image+file->text"),
    fm("mistralai/mistral-large", "Mistral: Mistral Large", 128000, None, "text+file->text"),
    fm("mistralai/mistral-medium-3-5", "Mistral: Mistral Medium 3.5", 262144, None, "text+image+file->text"),
    fm("mistralai/mistral-medium-3.1", "Mistral: Mistral Medium 3.1", 131072, None, "text+image+file->text"),
    fm("mistralai/mistral-medium-3", "Mistral: Mistral Medium 3", 131072, None, "text+image+file->text"),
    fm("mistralai/mistral-small-2603", "Mistral: Mistral Small 4", 262144, None, "text+image->text"),
    fm("mistralai/mistral-small-3.2-24b-instruct", "Mistral: Mistral Small 3.2 24B", 128000, 16384, "text+image->text"),
    fm("mistralai/devstral-2512", "Mistral: Devstral 2 2512", 262144, None, "text+file->text"),
    fm("mistralai/codestral-2508", "Mistral: Codestral 2508", 256000, None, "text+file->text"),
    fm("mistralai/voxtral-small-24b-2507", "Mistral: Voxtral Small 24B 2507", 32000, None, "text+file+audio->text"),

    fm("x-ai/grok-4.3", "xAI: Grok 4.3", 1000000, None, "text+image+file->text"),
    fm("x-ai/grok-4.20", "xAI: Grok 4.20", 2000000, None, "text+image+file->text"),
    fm("x-ai/grok-4.20-multi-agent", "xAI: Grok 4.20 Multi-Agent", 2000000, None, "text+image+file->text"),
    fm("x-ai/grok-build-0.1", "xAI: Grok Build 0.1", 256000, None, "text+image->text"),

    fm("qwen/qwen3.7-max", "Qwen: Qwen3.7 Max", 1000000, 65536, "text->text"),
    fm("qwen/qwen3.7-plus", "Qwen: Qwen3.7 Plus", 1000000, 65536, "text+image->text"),
    fm("qwen/qwen3.6-flash", "Qwen: Qwen3.6 Flash", 1000000, 65536, "text+image+video->text"),
    fm("qwen/qwen3.6-plus", "Qwen: Qwen3.6 Plus", 1000000, 65536, "text+image+video->text"),
    fm("qwen/qwen3.5-plus-20260420", "Qwen: Qwen3.5 Plus 2026-04-20", 1000000, 65536, "text+image+video->text"),
    fm("qwen/qwen3-max", "Qwen: Qwen3 Max", 262144, 32768, "text->text"),
    fm("qwen/qwen3-max-thinking", "Qwen: Qwen3 Max Thinking", 262144, 32768, "text->text"),
    fm("qwen/qwen3-coder", "Qwen: Qwen3 Coder", 1048576, 65536, "text->text"),
    fm("qwen/qwen3-coder-plus", "Qwen: Qwen3 Coder Plus", 1000000, 65536, "text->text"),
    fm("qwen/qwen3-coder-flash", "Qwen: Qwen3 Coder Flash", 1000000, 65536, "text->text"),
    fm("qwen/qwen3-coder-next", "Qwen: Qwen3 Coder Next", 262144, 262144, "text->text"),
    fm("qwen/qwen3-coder:free", "Qwen: Qwen3 Coder Free", 1048576, 262000, "text->text"),
    fm("qwen/qwen-plus", "Qwen: Qwen Plus", 1000000, 32768, "text->text"),
    fm("qwen/qwen-plus-2025-07-28", "Qwen: Qwen Plus 0728", 1000000, 32768, "text->text"),
    fm("qwen/qwen-plus-2025-07-28:thinking", "Qwen: Qwen Plus 0728 Thinking", 1000000, 32768, "text->text"),

    fm("cohere/north-mini-code:free", "Cohere: North Mini Code Free", 256000, 64000, "text->text"),
    fm("openrouter/auto", "OpenRouter: Auto Router", 2000000, None, "text+image+file->text"),
    fm("openrouter/free", "OpenRouter: Free Models Router", 200000, None, "text->text"),
    fm("openrouter/fusion", "OpenRouter: Fusion Router", 1000000, None, "text->text"),
    fm("openrouter/pareto-code", "OpenRouter: Pareto Code Router", 2000000, None, "text->text"),

    # Media endpoints not guaranteed in /models.
    fm("google/veo-3.1", "Google: Veo 3.1", None, None, "text->video", "videos"),
    fm("google/veo-3.1-fast", "Google: Veo 3.1 Fast", None, None, "text->video", "videos"),
    fm("bytedance/seedance-2.0", "ByteDance: Seedance 2.0", None, None, "text->video", "videos"),
    fm("bytedance/seedance-2.0-fast", "ByteDance: Seedance 2.0 Fast", None, None, "text->video", "videos"),
    fm("bytedance-seed/seedream-4.5", "ByteDance Seed: Seedream 4.5", None, None, "text+image->image"),
    fm("google/gemini-3.1-flash-tts-preview", "Google: Gemini 3.1 Flash TTS Preview", None, None, "text->audio", "audio/speech"),
]

CURATED_ALIASES: Dict[str, str] = {
    # Anthropic.
    "claude sonnet 5": "anthropic/claude-sonnet-5",
    "sonnet 5": "anthropic/claude-sonnet-5",
    "claude fable 5": "anthropic/claude-fable-5",
    "fable 5": "anthropic/claude-fable-5",
    "claude sonnet 4.6": "anthropic/claude-sonnet-4.6",
    "sonnet 4.6": "anthropic/claude-sonnet-4.6",
    "claude sonnet 4.5": "anthropic/claude-sonnet-4.5",
    "sonnet 4.5": "anthropic/claude-sonnet-4.5",
    "claude sonnet 4": "anthropic/claude-sonnet-4",
    "sonnet 4": "anthropic/claude-sonnet-4",
    "claude opus 4.8": "anthropic/claude-opus-4.8",
    "opus 4.8": "anthropic/claude-opus-4.8",
    "claude opus 4.8 fast": "anthropic/claude-opus-4.8-fast",
    "opus 4.8 fast": "anthropic/claude-opus-4.8-fast",
    "claude opus 4.7": "anthropic/claude-opus-4.7",
    "opus 4.7": "anthropic/claude-opus-4.7",
    "claude opus 4.7 fast": "anthropic/claude-opus-4.7-fast",
    "opus 4.7 fast": "anthropic/claude-opus-4.7-fast",
    "claude opus 4.6": "anthropic/claude-opus-4.6",
    "opus 4.6": "anthropic/claude-opus-4.6",
    "claude opus 4.5": "anthropic/claude-opus-4.5",
    "opus 4.5": "anthropic/claude-opus-4.5",
    "claude opus 4.1": "anthropic/claude-opus-4.1",
    "opus 4.1": "anthropic/claude-opus-4.1",
    "claude opus 4": "anthropic/claude-opus-4",
    "opus 4": "anthropic/claude-opus-4",
    "claude haiku 4.5": "anthropic/claude-haiku-4.5",
    "haiku 4.5": "anthropic/claude-haiku-4.5",
    "claude 3 haiku": "anthropic/claude-3-haiku",

    # OpenAI.
    "gpt 5.5": "openai/gpt-5.5",
    "gpt 5.5 pro": "openai/gpt-5.5-pro",
    "gpt 5.4": "openai/gpt-5.4",
    "gpt 5.4 pro": "openai/gpt-5.4-pro",
    "gpt 5.4 mini": "openai/gpt-5.4-mini",
    "gpt 5.4 nano": "openai/gpt-5.4-nano",
    "gpt 5.4 image 2": "openai/gpt-5.4-image-2",
    "gpt 5.3 chat": "openai/gpt-5.3-chat",
    "gpt 5.3 codex": "openai/gpt-5.3-codex",
    "gpt 5.2": "openai/gpt-5.2",
    "gpt 5.2 chat": "openai/gpt-5.2-chat",
    "gpt 5.2 pro": "openai/gpt-5.2-pro",
    "gpt 5.2 codex": "openai/gpt-5.2-codex",
    "gpt 5.1": "openai/gpt-5.1",
    "gpt 5.1 chat": "openai/gpt-5.1-chat",
    "gpt 5.1 codex": "openai/gpt-5.1-codex",
    "gpt 5.1 codex max": "openai/gpt-5.1-codex-max",
    "gpt 5.1 codex mini": "openai/gpt-5.1-codex-mini",
    "gpt 5": "openai/gpt-5",
    "gpt 5 chat": "openai/gpt-5-chat",
    "gpt 5 pro": "openai/gpt-5-pro",
    "gpt 5 mini": "openai/gpt-5-mini",
    "gpt 5 nano": "openai/gpt-5-nano",
    "gpt 5 codex": "openai/gpt-5-codex",
    "gpt 5 image": "openai/gpt-5-image",
    "gpt image": "openai/gpt-5-image",
    "gpt 5 image mini": "openai/gpt-5-image-mini",
    "gpt chat latest": "openai/gpt-chat-latest",
    "gpt 4.1": "openai/gpt-4.1",
    "gpt 4.1 mini": "openai/gpt-4.1-mini",
    "gpt 4.1 nano": "openai/gpt-4.1-nano",
    "o1": "openai/o1",
    "o1 pro": "openai/o1-pro",
    "o3": "openai/o3",
    "o3 pro": "openai/o3-pro",
    "o3 mini": "openai/o3-mini",
    "o3 mini high": "openai/o3-mini-high",
    "o3 deep research": "openai/o3-deep-research",
    "o4 mini": "openai/o4-mini",
    "o4 mini high": "openai/o4-mini-high",
    "o4 mini deep research": "openai/o4-mini-deep-research",
    "gpt audio": "openai/gpt-audio",
    "gpt audio mini": "openai/gpt-audio-mini",

    # Google.
    "gemini 3.5 flash": "google/gemini-3.5-flash",
    "gemini 3.1 pro": "google/gemini-3.1-pro-preview",
    "gemini 3.1 pro preview": "google/gemini-3.1-pro-preview",
    "gemini 3.1 pro custom tools": "google/gemini-3.1-pro-preview-customtools",
    "gemini 3.1 flash lite": "google/gemini-3.1-flash-lite",
    "gemini 3.1 flash lite preview": "google/gemini-3.1-flash-lite-preview",
    "gemini 3.1 flash image": "google/gemini-3.1-flash-image",
    "gemini 3.1 flash image preview": "google/gemini-3.1-flash-image-preview",
    "gemini 3.1 flash lite image": "google/gemini-3.1-flash-lite-image",
    "gemini 3 flash preview": "google/gemini-3-flash-preview",
    "gemini 2.5 pro": "google/gemini-2.5-pro",
    "gemini 2.5 pro preview": "google/gemini-2.5-pro-preview",
    "gemini 2.5 flash": "google/gemini-2.5-flash",
    "gemini 2.5 flash lite": "google/gemini-2.5-flash-lite",
    "gemini 2.5 flash image": "google/gemini-2.5-flash-image",
    "nano banana": "google/gemini-2.5-flash-image",
    "nano banana pro": "google/gemini-3-pro-image",
    "nano banana pro preview": "google/gemini-3-pro-image-preview",
    "nano banana 2": "google/gemini-3.1-flash-image",
    "nano banana 2 preview": "google/gemini-3.1-flash-image-preview",
    "nano banana 2 lite": "google/gemini-3.1-flash-lite-image",
    "lyria 3 pro": "google/lyria-3-pro-preview",
    "lyria 3 clip": "google/lyria-3-clip-preview",

    # Perplexity.
    "sonar pro search": "perplexity/sonar-pro-search",
    "perplexity sonar pro search": "perplexity/sonar-pro-search",
    "sonar deep research": "perplexity/sonar-deep-research",
    "sonar reasoning pro": "perplexity/sonar-reasoning-pro",
    "sonar pro": "perplexity/sonar-pro",
    "sonar": "perplexity/sonar",

    # Meta / DeepSeek / Kimi.
    "llama 4 maverick": "meta-llama/llama-4-maverick",
    "llama 4 scout": "meta-llama/llama-4-scout",
    "llama guard 4": "meta-llama/llama-guard-4-12b",
    "llama 3.3 70b": "meta-llama/llama-3.3-70b-instruct",
    "deepseek chat": "deepseek/deepseek-chat",
    "deepseek v3": "deepseek/deepseek-chat",
    "deepseek v3 0324": "deepseek/deepseek-chat-v3-0324",
    "deepseek v3.1": "deepseek/deepseek-chat-v3.1",
    "deepseek v3.1 terminus": "deepseek/deepseek-v3.1-terminus",
    "deepseek v3.2": "deepseek/deepseek-v3.2",
    "deepseek v3.2 exp": "deepseek/deepseek-v3.2-exp",
    "deepseek r1": "deepseek/deepseek-r1-0528",
    "deepseek r1 0528": "deepseek/deepseek-r1-0528",
    "deepseek r1 distill llama 70b": "deepseek/deepseek-r1-distill-llama-70b",
    "deepseek v4": "deepseek/deepseek-v4-pro",
    "deepseek v4 pro": "deepseek/deepseek-v4-pro",
    "deepseek v4 flash": "deepseek/deepseek-v4-flash",
    "kimi k2": "moonshotai/kimi-k2.6",
    "kimi k2.7 code": "moonshotai/kimi-k2.7-code",
    "kimi k2 code": "moonshotai/kimi-k2.7-code",
    "kimi k2.6": "moonshotai/kimi-k2.6",
    "kimi k2.5": "moonshotai/kimi-k2.5",
    "kimi k2 thinking": "moonshotai/kimi-k2-thinking",
    "kimi thinking": "moonshotai/kimi-k2-thinking",

    # Mistral / xAI / Qwen / routers.
    "mistral large": "mistralai/mistral-large-2512",
    "mistral large 2512": "mistralai/mistral-large-2512",
    "mistral medium 3.5": "mistralai/mistral-medium-3-5",
    "mistral medium 3.1": "mistralai/mistral-medium-3.1",
    "mistral medium 3": "mistralai/mistral-medium-3",
    "mistral small": "mistralai/mistral-small-2603",
    "mistral small 2603": "mistralai/mistral-small-2603",
    "mistral small 3.2": "mistralai/mistral-small-3.2-24b-instruct",
    "devstral": "mistralai/devstral-2512",
    "devstral 2512": "mistralai/devstral-2512",
    "devstral medium": "mistralai/devstral-2512",
    "codestral": "mistralai/codestral-2508",
    "voxtral small": "mistralai/voxtral-small-24b-2507",
    "grok 4.3": "x-ai/grok-4.3",
    "grok 4.20": "x-ai/grok-4.20",
    "grok 4.20 multi agent": "x-ai/grok-4.20-multi-agent",
    "grok build": "x-ai/grok-build-0.1",
    "qwen 3.7 max": "qwen/qwen3.7-max",
    "qwen3.7 max": "qwen/qwen3.7-max",
    "qwen 3.7 plus": "qwen/qwen3.7-plus",
    "qwen3.7 plus": "qwen/qwen3.7-plus",
    "qwen 3.6 flash": "qwen/qwen3.6-flash",
    "qwen 3.6 plus": "qwen/qwen3.6-plus",
    "qwen 3 max": "qwen/qwen3-max",
    "qwen3 max": "qwen/qwen3-max",
    "qwen max thinking": "qwen/qwen3-max-thinking",
    "qwen 3 coder": "qwen/qwen3-coder",
    "qwen3 coder": "qwen/qwen3-coder",
    "qwen coder": "qwen/qwen3-coder",
    "qwen coder plus": "qwen/qwen3-coder-plus",
    "qwen coder flash": "qwen/qwen3-coder-flash",
    "qwen coder next": "qwen/qwen3-coder-next",
    "qwen plus": "qwen/qwen-plus",
    "qwen plus thinking": "qwen/qwen-plus-2025-07-28:thinking",
    "north mini code": "cohere/north-mini-code:free",
    "openrouter auto": "openrouter/auto",
    "auto router": "openrouter/auto",
    "openrouter free": "openrouter/free",
    "free router": "openrouter/free",
    "openrouter fusion": "openrouter/fusion",
    "fusion router": "openrouter/fusion",
    "pareto code": "openrouter/pareto-code",

    # Media endpoints.
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
    "claude fable latest": "~anthropic/claude-fable-latest",
    "fable latest": "~anthropic/claude-fable-latest",
    "gemini flash latest": "~google/gemini-flash-latest",
    "gemini pro latest": "~google/gemini-pro-latest",
    "gpt latest": "~openai/gpt-latest",
    "openai gpt latest": "~openai/gpt-latest",
    "gpt mini latest": "~openai/gpt-mini-latest",
    "openai gpt mini latest": "~openai/gpt-mini-latest",
    "kimi latest": "~moonshotai/kimi-latest",
}

KNOWN_NOT_LIVE_RAW: Dict[str, str] = {
    "claude 3.7": "Claude 3.7 is not in the supplied live OpenRouter list. Choose Claude 4.x/5 or a tilde latest alias.",
    "claude 3.7 sonnet": "Claude 3.7 Sonnet is not in the supplied live OpenRouter list. Use Claude Sonnet 4.6/5 or a tilde latest alias.",
    "claude sonnet 3.7": "Claude 3.7 Sonnet is not in the supplied live OpenRouter list. Use Claude Sonnet 4.6/5 or a tilde latest alias.",
    "sonnet 3.7": "Claude 3.7 Sonnet is not in the supplied live OpenRouter list. Use Claude Sonnet 4.6/5 or a tilde latest alias.",
    "deepseek r2": "DeepSeek R2 is not in the supplied live OpenRouter list. Current DeepSeek choices include R1 0528, V3.2, V4 Flash, and V4 Pro.",
    "grok 3": "Grok 3 is not in the supplied live OpenRouter list. Current xAI choices include Grok 4.3 and Grok 4.20.",
    "xai grok 3": "Grok 3 is not in the supplied live OpenRouter list. Current xAI choices include Grok 4.3 and Grok 4.20.",
    "x ai grok 3": "Grok 3 is not in the supplied live OpenRouter list. Current xAI choices include Grok 4.3 and Grok 4.20.",
}


def simple_key(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r":(" + "|".join(sorted(KNOWN_SUFFIXES)) + r")\b", r" \1", text)
    text = re.sub(r"([a-z])(?=\d)", r"\1 ", text)
    text = re.sub(r"(?<=\d)(?=[a-z])", " ", text)
    text = re.sub(r"[^a-z0-9.]+", " ", text)
    return " ".join(t for t in text.split() if t not in STOPWORDS)


EXACT_ALIASES = {simple_key(k): v for k, v in CURATED_ALIASES.items()}
LATEST_ALIASES = {simple_key(k): v for k, v in RAW_LATEST_ALIASES.items()}
KNOWN_NOT_LIVE = {simple_key(k): v for k, v in KNOWN_NOT_LIVE_RAW.items()}


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
    return m.group(1), (m.group(2).lower() if m.group(2) else None)


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
    headers = {"User-Agent": "openrouter-caller-resolver/4.0"}
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
    merged: Dict[str, Dict[str, Any]] = {}
    for source_name, seq in (("live", primary), ("static", extras)):
        for m in seq:
            mid = m.get("id")
            if not mid:
                continue
            item = normalize_model(m, source_name)
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
        return merge_models(cached_models, FALLBACK_MODELS), {"live_ok": False, "cache_used": bool(cache), "source": "offline"}

    if cache_fresh and not force_refresh:
        return merge_models(cache.get("models", []), FALLBACK_MODELS), {"live_ok": False, "cache_used": True, "source": "fresh_cache"}

    try:
        live = fetch_live_models()
        write_cache(live)
        return merge_models(live, FALLBACK_MODELS), {"live_ok": True, "cache_used": False, "source": "live"}
    except Exception as e:
        cached_models = cache.get("models", []) if cache else []
        return merge_models(cached_models, FALLBACK_MODELS), {
            "live_ok": False,
            "cache_used": bool(cache),
            "source": "cache_or_static",
            "error": str(e),
        }


def extract_suffix(query: str) -> Tuple[str, Optional[str]]:
    pattern = r":(" + "|".join(sorted(KNOWN_SUFFIXES)) + r")\b"
    m = re.search(pattern, query.lower())
    if m:
        suffix = m.group(1)
        cleaned = re.sub(pattern, " ", query, flags=re.IGNORECASE)
        return cleaned, suffix

    raw_key = simple_key(query)
    if raw_key in EXACT_ALIASES:
        return query, None

    toks = tokenize(query, remove_stop=False, expand_decimals=False)
    if not toks:
        return query, None
    suffix: Optional[str] = None
    last = toks[-1]
    if last in {"nitro", "floor", "exacto", "online", "free", "extended", "thinking"}:
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

    if suffix:
        if requested_suffix == suffix:
            score += 80
        elif not requested_suffix:
            score -= 45
    if requested_suffix and not suffix:
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

    if raw_key in KNOWN_NOT_LIVE:
        return {
            "status": "ERROR",
            "error": "known_not_live",
            "message": KNOWN_NOT_LIVE[raw_key],
            "candidates": [],
        }

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

    if clean_key in KNOWN_NOT_LIVE:
        return {
            "status": "ERROR",
            "error": "known_not_live",
            "message": KNOWN_NOT_LIVE[clean_key],
            "candidates": [],
        }

    if clean_key in EXACT_ALIASES:
        slug = apply_suffix(EXACT_ALIASES[clean_key], requested_suffix)
        base, _ = strip_model_suffix(slug)
        m = find_model(slug, models) or find_model(base, models) or {"id": slug, "name": slug}
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
