#!/usr/bin/env python3.11
"""
Reusable OpenRouter image caller.

CLI:
  python3.11 call_image.py --model SLUG --prompt "..." [--save-dir DIR] [--json-output]

No third-party dependencies. Imports local resolve_model.py only.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Iterable, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import resolve_model  # type: ignore  # local file


API_URL = "https://openrouter.ai/api/v1/chat/completions"
KNOWN_SUFFIXES = {"free", "nitro", "floor", "thinking", "extended", "exacto", "online"}


class OpenRouterImageError(RuntimeError):
    pass


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


def strip_suffix(model_id: str) -> str:
    if ":" in model_id:
        base, suffix = model_id.rsplit(":", 1)
        if suffix in KNOWN_SUFFIXES:
            return base
    return model_id


def resolve_or_exit(model_text: str) -> str:
    models, meta = resolve_model.load_models(
        force_refresh=bool(resolve_model.parse_slug_like(model_text)),
        offline=False,
    )
    res = resolve_model.resolve(model_text, models, meta, top_n=8)
    status = res.get("status")
    if status not in {"OK", "UNVERIFIED"}:
        eprint(f"ERROR: could not resolve model: {model_text}")
        eprint(f"STATUS={status}")
        if res.get("message"):
            eprint(f"MESSAGE={res['message']}")
        if res.get("candidates"):
            eprint("CANDIDATES:")
            for m in res["candidates"][:8]:
                eprint(f"  {m.get('_use_slug', m.get('id'))}\tscore={m.get('_score')}\tname={m.get('name')}")
        raise SystemExit(2 if status == "AMBIGUOUS" else 1)
    for w in res.get("warnings", []):
        eprint(f"WARNING={w}")
    return str(res["use_slug"])


def openrouter_headers() -> Dict[str, str]:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise OpenRouterImageError("OPENROUTER_API_KEY is not set")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if os.environ.get("OPENROUTER_HTTP_REFERER"):
        headers["HTTP-Referer"] = os.environ["OPENROUTER_HTTP_REFERER"]
    if os.environ.get("OPENROUTER_APP_TITLE"):
        headers["X-Title"] = os.environ["OPENROUTER_APP_TITLE"]
    return headers


def post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        raise OpenRouterImageError(f"HTTP {exc.code}: {err}") from exc
    except urllib.error.URLError as exc:
        raise OpenRouterImageError(f"Network error: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise OpenRouterImageError(f"Invalid JSON response: {exc}") from exc


def iter_strings(obj: Any) -> Iterable[str]:
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from iter_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_strings(v)


def save_data_url(data_url: str, save_dir: str, index: int) -> str:
    header, b64 = data_url.split(",", 1)
    match = re.match(r"data:image/([^;]+);base64", header)
    ext = match.group(1).lower() if match else "png"
    if ext == "jpeg":
        ext = "jpg"
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, f"image_{index}.{ext}")
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64))
    return path


def download_image_url(url: str, save_dir: str, index: int) -> str:
    os.makedirs(save_dir, exist_ok=True)
    ext = "png"
    m = re.search(r"\.(png|jpg|jpeg|webp)(?:\?|$)", url, re.IGNORECASE)
    if m:
        ext = "jpg" if m.group(1).lower() == "jpeg" else m.group(1).lower()
    path = os.path.join(save_dir, f"image_url_{index}.{ext}")
    with urllib.request.urlopen(url, timeout=120) as resp:
        data = resp.read()
    with open(path, "wb") as f:
        f.write(data)
    return path


def save_images(result: Dict[str, Any], save_dir: str) -> List[str]:
    text = "\n".join(iter_strings(result))
    data_urls = re.findall(r"data:image/[^;]+;base64,[A-Za-z0-9+/=\s]+", text)
    paths: List[str] = []
    for i, data_url in enumerate(data_urls):
        data_url = re.sub(r"\s+", "", data_url)
        paths.append(save_data_url(data_url, save_dir, i))

    image_urls = re.findall(r"https?://[^\s\"')]+?\.(?:png|jpg|jpeg|webp)(?:\?[^\s\"')]+)?", text, flags=re.IGNORECASE)
    for i, url in enumerate(image_urls):
        try:
            paths.append(download_image_url(url, save_dir, i))
        except Exception as exc:
            eprint(f"WARNING: could not download image URL {url}: {exc}")
    return paths


def print_summary(result: Dict[str, Any], requested_model: str, stream: Any) -> None:
    choices = result.get("choices") or []
    choice = choices[0] if choices else {}
    finish_reason = choice.get("finish_reason")
    used_model = result.get("model", "")
    print(f"finish_reason = {finish_reason}", file=stream)
    print(f"requested_model = {requested_model}", file=stream)
    print(f"used_model = {used_model}", file=stream)
    print(f"usage = {json.dumps(result.get('usage'), ensure_ascii=False)}", file=stream)

    if requested_model.startswith("~"):
        print(f"OK: requested latest alias {requested_model}; OpenRouter used {used_model}", file=stream)
    elif used_model and strip_suffix(str(used_model)) != strip_suffix(requested_model):
        print(f"WARNING: requested {requested_model} but OpenRouter used {used_model}", file=stream)
    elif used_model:
        print(f"OK: model used = {used_model}", file=stream)
    if finish_reason == "length":
        print("TRUNCATED: increase output budget or simplify prompt.", file=stream)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Call OpenRouter image generation safely.")
    parser.add_argument("--model", required=True, help="Exact slug or model text; resolver is always run first")
    parser.add_argument("--prompt", required=True, help="Image prompt")
    parser.add_argument("--save-dir", default=".", help="Directory for saved images")
    parser.add_argument("--json-output", action="store_true", help="Print full response JSON to stdout; summary to stderr")
    parser.add_argument("--timeout", type=int, default=900)
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        model = resolve_or_exit(args.model)
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": args.prompt}],
            "modalities": ["image", "text"],
        }
        result = post_json(API_URL, openrouter_headers(), payload, timeout=args.timeout)

        saved = save_images(result, args.save_dir)
        message = ((result.get("choices") or [{}])[0].get("message") or {})
        content = message.get("content")

        if args.json_output:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            for path in saved:
                print(f"saved_image = {path}", file=sys.stderr)
            print_summary(result, model, stream=sys.stderr)
        else:
            if content:
                print(content if isinstance(content, str) else json.dumps(content, indent=2, ensure_ascii=False))
            for path in saved:
                print(f"saved_image = {path}")
            if not saved:
                print("WARNING: no data URL or image URL found in response")
            print_summary(result, model, stream=sys.stdout)

        choices = result.get("choices") or []
        if choices and choices[0].get("finish_reason") == "length":
            return 3
        return 0

    except KeyboardInterrupt:
        eprint("ERROR: interrupted")
        return 130
    except OpenRouterImageError as exc:
        eprint(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
