#!/usr/bin/env python3.11
"""
Reusable OpenRouter chat caller.

CLI:
  python3.11 call_chat.py --model SLUG --prompt "..." [--max-tokens N]
      [--tools web_search,advisor,subagent,fusion]
      [--reasoning-effort none|minimal|low|medium|high|xhigh|max]
      [--system "..."] [--json-output]

No third-party dependencies. Imports local resolve_model.py only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import resolve_model  # type: ignore  # local file


API_URL = "https://openrouter.ai/api/v1/chat/completions"
KNOWN_SUFFIXES = {"free", "nitro", "floor", "thinking", "extended", "exacto", "online"}
EFFORT_TIERS = ("none", "minimal", "low", "medium", "high", "xhigh", "max")

BUDGETS_ANTHROPIC = {
    "none": 0,
    "minimal": 1024,
    "low": 2048,
    "medium": 8192,
    "high": 16000,
    "xhigh": 32000,
    "max": 64000,
}
BUDGETS_GEMINI = {
    "none": 0,
    "minimal": 512,
    "low": 1024,
    "medium": 4096,
    "high": 8192,
    "xhigh": 16384,
    "max": 32768,
}
BUDGETS_QWEN = {
    "none": 0,
    "minimal": 1024,
    "low": 2048,
    "medium": 8192,
    "high": 16000,
    "xhigh": 32000,
    "max": 64000,
}


class OpenRouterCallError(RuntimeError):
    pass


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


def strip_suffix(model_id: str) -> str:
    if ":" in model_id:
        base, suffix = model_id.rsplit(":", 1)
        if suffix in KNOWN_SUFFIXES:
            return base
    return model_id


def resolve_or_exit(model_text: str, purpose: str = "model") -> str:
    models, meta = resolve_model.load_models(
        force_refresh=bool(resolve_model.parse_slug_like(model_text)),
        offline=False,
    )
    res = resolve_model.resolve(model_text, models, meta, top_n=8)
    status = res.get("status")
    if status not in {"OK", "UNVERIFIED"}:
        eprint(f"ERROR: could not resolve {purpose}: {model_text}")
        eprint(f"STATUS={status}")
        if res.get("message"):
            eprint(f"MESSAGE={res['message']}")
        if res.get("candidates"):
            eprint("CANDIDATES:")
            for m in res["candidates"][:8]:
                eprint(f"  {m.get('_use_slug', m.get('id'))}\tscore={m.get('_score')}\tname={m.get('name')}")
        raise SystemExit(2 if status == "AMBIGUOUS" else 1)
    if status == "UNVERIFIED" and not resolve_model.parse_slug_like(model_text):
        eprint(f"ERROR: non-exact {purpose} resolved as UNVERIFIED; refusing to call.")
        raise SystemExit(1)
    for w in res.get("warnings", []):
        eprint(f"WARNING[{purpose}]={w}")
    return str(res["use_slug"])


def post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8")
            return json.loads(text)
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        raise OpenRouterCallError(f"HTTP {exc.code}: {err}") from exc
    except urllib.error.URLError as exc:
        raise OpenRouterCallError(f"Network error: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise OpenRouterCallError(f"Invalid JSON response: {exc}") from exc


def openrouter_headers() -> Dict[str, str]:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise OpenRouterCallError("OPENROUTER_API_KEY is not set")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if os.environ.get("OPENROUTER_HTTP_REFERER"):
        headers["HTTP-Referer"] = os.environ["OPENROUTER_HTTP_REFERER"]
    if os.environ.get("OPENROUTER_APP_TITLE"):
        headers["X-Title"] = os.environ["OPENROUTER_APP_TITLE"]
    return headers


def clamp_budget_for_max_tokens(budget: int, max_tokens: int, family: str) -> int:
    if budget <= 0:
        return budget
    if max_tokens > budget:
        return budget
    clamped = max(1, max_tokens - 1024)
    if family == "anthropic":
        clamped = max(1024, clamped)
    eprint(f"WARNING: reasoning budget {budget} >= max_tokens {max_tokens}; clamped to {clamped}")
    return clamped


def effort_low_medium_high(tier: str) -> str:
    if tier in {"none", "minimal", "low"}:
        return "low"
    if tier == "medium":
        return "medium"
    return "high"


def effort_gemini3(tier: str) -> str:
    if tier == "none":
        return "minimal"
    if tier in {"minimal", "low", "medium", "high"}:
        return tier
    return "high"


def effort_anthropic_adaptive(tier: str) -> str:
    if tier in {"minimal", "low"}:
        return "low"
    if tier == "medium":
        return "medium"
    if tier == "max":
        return "max"
    return "high"


def effort_deepseek_v4(tier: str) -> str:
    return "xhigh" if tier in {"xhigh", "max"} else "high"


def is_anthropic_adaptive(model: str) -> bool:
    base = strip_suffix(model)
    if base.startswith("~anthropic/"):
        return True
    return any(
        marker in base
        for marker in (
            "claude-sonnet-5",
            "claude-fable-5",
            "claude-opus-4.8",
            "claude-opus-4.7",
            "claude-opus-4.6",
            "claude-sonnet-4.6",
        )
    )


def build_reasoning_payload(model: str, tier: Optional[str], max_tokens: int) -> Dict[str, Any]:
    """
    OpenRouter-normalized reasoning mapper.

    Verified provider-native equivalents:
      - OpenAI: reasoning.effort
      - Anthropic older: thinking.budget_tokens; OpenRouter sends reasoning.max_tokens
      - Anthropic 4.6+/4.7+/4.8+/Sonnet5/Fable5: adaptive thinking; OpenRouter sends reasoning.effort
      - Gemini 2.5: thinkingBudget; OpenRouter sends reasoning.max_tokens
      - Gemini 3.x/3.5: thinkingLevel; OpenRouter sends reasoning.effort
      - DeepSeek V4: thinking.type + reasoning_effort high/max; OpenRouter sends reasoning.effort high/xhigh
      - Kimi K2.x: thinking.type enabled/disabled; OpenRouter sends reasoning where exposed
    """
    if not tier:
        return {}
    if tier not in EFFORT_TIERS:
        raise OpenRouterCallError(f"Invalid reasoning effort {tier}; choose one of {', '.join(EFFORT_TIERS)}")

    base = strip_suffix(model)
    provider = base.split("/", 1)[0].lstrip("~") if "/" in base else ""
    tail = base.split("/", 1)[1] if "/" in base else base

    if tier == "none":
        if provider == "google" and tail.startswith("gemini-2.5"):
            return {"reasoning": {"max_tokens": 0}}
        return {}

    if provider == "openai":
        if tail.startswith("o") or tail.startswith("gpt-5"):
            return {"reasoning": {"effort": effort_low_medium_high(tier)}}
        return {}

    if provider == "anthropic":
        if is_anthropic_adaptive(base):
            return {"reasoning": {"effort": effort_anthropic_adaptive(tier)}}
        budget = clamp_budget_for_max_tokens(BUDGETS_ANTHROPIC[tier], max_tokens, "anthropic")
        return {"reasoning": {"max_tokens": budget}}

    if provider == "google" and tail.startswith("gemini-"):
        if tail.startswith(("gemini-3", "gemini-3.1", "gemini-3.5")):
            return {"reasoning": {"effort": effort_gemini3(tier)}}
        if tail.startswith("gemini-2.5"):
            budget = BUDGETS_GEMINI[tier]
            return {"reasoning": {"max_tokens": budget}}
        return {}

    if provider == "deepseek":
        if "v4" in tail:
            return {"reasoning": {"effort": effort_deepseek_v4(tier)}}
        if "r1" in tail:
            return {"reasoning": {"effort": effort_low_medium_high(tier)}}
        return {}

    if provider == "moonshotai" and tail.startswith("kimi-k2"):
        mapped = "xhigh" if tier == "max" else tier
        if mapped == "minimal":
            mapped = "low"
        return {"reasoning": {"effort": mapped}}

    if provider == "qwen" and ("thinking" in tail or tail in {"qwen-plus-2025-07-28"}):
        budget = clamp_budget_for_max_tokens(BUDGETS_QWEN[tier], max_tokens, "qwen")
        return {"reasoning": {"max_tokens": budget}}

    if provider == "x-ai" and tail.startswith("grok"):
        mapped = "xhigh" if tier == "max" else tier
        return {"reasoning": {"effort": mapped}}

    return {}


def make_web_search_tool() -> Dict[str, Any]:
    return {
        "type": "openrouter:web_search",
        "parameters": {
            "engine": "auto",
            "max_results": 5,
            "max_total_results": 15,
            "search_context_size": "medium",
        },
    }


def make_advisor_tool(reasoning_effort: str) -> Dict[str, Any]:
    advisor_model = resolve_or_exit("~anthropic/claude-opus-latest", "advisor model")
    return {
        "type": "openrouter:advisor",
        "parameters": {
            "name": "senior-reviewer",
            "model": advisor_model,
            "instructions": "You are a senior expert reviewer. Be concise, decisive, and identify pitfalls.",
            "forward_transcript": False,
            "max_tool_calls": 6,
            "max_completion_tokens": 8000,
            "reasoning": {"effort": effort_anthropic_adaptive(reasoning_effort if reasoning_effort != "none" else "medium")},
            "temperature": 0.1,
        },
    }


def make_subagent_tool() -> Dict[str, Any]:
    worker_model = resolve_or_exit("~anthropic/claude-haiku-latest", "subagent model")
    return {
        "type": "openrouter:subagent",
        "parameters": {
            "model": worker_model,
            "instructions": "You are a fast, focused worker. Complete delegated tasks exactly as specified.",
            "max_tool_calls": 5,
            "max_completion_tokens": 6000,
            "reasoning": {"effort": "low"},
            "temperature": 0.2,
        },
    }


def make_fusion_tool(reasoning_effort: str) -> Dict[str, Any]:
    analysis_models = [
        resolve_or_exit("~anthropic/claude-sonnet-latest", "fusion analysis model"),
        resolve_or_exit("~openai/gpt-latest", "fusion analysis model"),
        resolve_or_exit("~google/gemini-pro-latest", "fusion analysis model"),
    ]
    judge_model = resolve_or_exit("~anthropic/claude-opus-latest", "fusion judge model")
    return {
        "type": "openrouter:fusion",
        "parameters": {
            "analysis_models": analysis_models,
            "model": judge_model,
            "max_tool_calls": 8,
            "max_completion_tokens": 12000,
            "reasoning": {"effort": reasoning_effort if reasoning_effort in {"low", "medium", "high"} else "medium"},
            "temperature": 0.2,
        },
    }


def build_tools(tools_arg: str, reasoning_effort: str) -> List[Dict[str, Any]]:
    if not tools_arg.strip():
        return []
    requested = [t.strip().lower() for t in tools_arg.split(",") if t.strip()]
    out: List[Dict[str, Any]] = []
    for tool in requested:
        if tool == "web_search":
            out.append(make_web_search_tool())
        elif tool == "advisor":
            out.append(make_advisor_tool(reasoning_effort))
        elif tool == "subagent":
            out.append(make_subagent_tool())
        elif tool == "fusion":
            out.append(make_fusion_tool(reasoning_effort))
        else:
            raise OpenRouterCallError(f"Unknown tool '{tool}'. Use comma list of: web_search,advisor,subagent,fusion")
    return out


def extract_content(result: Dict[str, Any]) -> Any:
    choices = result.get("choices") or []
    if not choices:
        return None
    message = choices[0].get("message") or {}
    return message.get("content", message)


def print_summary(result: Dict[str, Any], requested_model: str, stream: Any) -> None:
    choices = result.get("choices") or []
    choice = choices[0] if choices else {}
    finish_reason = choice.get("finish_reason")
    used_model = result.get("model", "")
    print(f"finish_reason = {finish_reason}", file=stream)
    print(f"requested_model = {requested_model}", file=stream)
    print(f"used_model = {used_model}", file=stream)
    print(f"usage = {json.dumps(result.get('usage'), ensure_ascii=False)}", file=stream)

    requested_base = strip_suffix(requested_model)
    used_base = strip_suffix(str(used_model))
    if requested_model.startswith("~"):
        print(f"OK: requested latest alias {requested_model}; OpenRouter used {used_model}", file=stream)
    elif used_model and requested_base != used_base:
        print(f"WARNING: requested {requested_model} but OpenRouter used {used_model}", file=stream)
    elif used_model:
        print(f"OK: model used = {used_model}", file=stream)
    if finish_reason == "length":
        print("TRUNCATED: increase --max-tokens or continue in a follow-up request.", file=stream)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Call OpenRouter chat/completions safely.")
    parser.add_argument("--model", required=True, help="Exact slug or model text; resolver is always run first")
    parser.add_argument("--prompt", required=True, help="User prompt")
    parser.add_argument("--system", help="Optional system prompt")
    parser.add_argument("--max-tokens", type=int, default=16000, help="max_tokens for completion")
    parser.add_argument("--tools", default="", help="Comma list: web_search,advisor,subagent,fusion")
    parser.add_argument("--reasoning-effort", choices=EFFORT_TIERS, default="medium")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--json-output", action="store_true", help="Print full response JSON to stdout; summary to stderr")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--tool-choice-required", action="store_true", help="Force tool use with tool_choice=required")
    parser.add_argument("--provider-json", help="Optional JSON object for OpenRouter provider routing")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        model = resolve_or_exit(args.model, "request model")

        messages: List[Dict[str, str]] = []
        if args.system:
            messages.append({"role": "system", "content": args.system})
        messages.append({"role": "user", "content": args.prompt})

        data: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": args.max_tokens,
        }

        data.update(build_reasoning_payload(model, args.reasoning_effort, args.max_tokens))

        if args.temperature is not None:
            data["temperature"] = args.temperature

        tools = build_tools(args.tools, args.reasoning_effort)
        if tools:
            data["tools"] = tools
            if args.tool_choice_required:
                data["tool_choice"] = "required"

        if args.provider_json:
            try:
                data["provider"] = json.loads(args.provider_json)
            except json.JSONDecodeError as exc:
                raise OpenRouterCallError(f"--provider-json is not valid JSON: {exc}") from exc

        result = post_json(API_URL, openrouter_headers(), data, timeout=args.timeout)

        if args.json_output:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print_summary(result, model, stream=sys.stderr)
        else:
            content = extract_content(result)
            if isinstance(content, str):
                print(content)
            else:
                print(json.dumps(content, indent=2, ensure_ascii=False))
            print_summary(result, model, stream=sys.stdout)

        choices = result.get("choices") or []
        if choices and choices[0].get("finish_reason") == "length":
            return 3
        return 0

    except KeyboardInterrupt:
        eprint("ERROR: interrupted")
        return 130
    except OpenRouterCallError as exc:
        eprint(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
