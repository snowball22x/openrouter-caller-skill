#!/usr/bin/env python3.11
"""
OpenRouter Model Slug Resolver
Resolves natural language model names or partial slugs to exact OpenRouter model IDs.

Features:
  - Exact-slug passthrough: if input already looks like a valid slug, returns it immediately
  - Tilde-slug support: handles ~provider/model-latest always-latest alias slugs
  - Suffix-aware scoring: penalizes :free/:nitro/:floor/:thinking/:extended/:exacto/:online
    unless the user explicitly requested them
  - Ambiguity warning: alerts when top two candidates are close in score
  - Dynamic model coverage: fetches live model list from OpenRouter API (cached 6h)
  - Provider listing: list all models by provider

Usage:
    python3.11 resolve_model.py "claude sonnet 4.6"
    python3.11 resolve_model.py "opus 4.7"
    python3.11 resolve_model.py "perplexity sonar pro search"
    python3.11 resolve_model.py "gpt-4.1"
    python3.11 resolve_model.py "anthropic/claude-sonnet-4.6"     # exact slug passthrough
    python3.11 resolve_model.py "~anthropic/claude-sonnet-latest" # tilde slug passthrough
    python3.11 resolve_model.py "claude sonnet latest"            # resolves to tilde slug
    python3.11 resolve_model.py "gemini flash latest"             # resolves to tilde slug
    python3.11 resolve_model.py --list anthropic                  # list all models by provider
    python3.11 resolve_model.py --list ~                          # list all tilde/latest-alias models
    python3.11 resolve_model.py --refresh                         # force-refresh model cache
"""

import os
import sys
import json
import re
import urllib.request
import time

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
CACHE_FILE = os.path.join(os.path.dirname(__file__), ".model_cache.json")
CACHE_TTL_HOURS = 6

# All known slug suffixes — these are routing modifiers, NOT part of the base model name
KNOWN_SUFFIXES = {
    "free",      # Free tier access, may have rate limits
    "nitro",     # Sort by throughput (fastest provider)
    "floor",     # Sort by price (cheapest provider)
    "thinking",  # Extended reasoning / chain-of-thought mode
    "extended",  # Extended context window
    "exacto",    # Quality-first provider sorting (best for tool-calling)
    "online",    # DEPRECATED: real-time web search (use openrouter:web_search server tool instead)
}

# Suffix penalty when user did NOT explicitly request the suffix
SUFFIX_PENALTY = 30

# Ambiguity threshold: warn if top-2 scores are within this fraction of the best score
# e.g. 0.25 means warn if second-best is within 25% of best score
AMBIGUITY_RATIO = 0.25
# Minimum absolute gap below which we always warn (for very low scores)
AMBIGUITY_MIN_GAP = 8


def fetch_models(force_refresh=False):
    """Fetch models from OpenRouter API, with local file cache."""
    if not force_refresh and os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            cached = json.load(f)
        age_hours = (time.time() - cached.get("fetched_at", 0)) / 3600
        if age_hours < CACHE_TTL_HOURS:
            return cached["models"]

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    models = data.get("data", [])

    with open(CACHE_FILE, "w") as f:
        json.dump({"fetched_at": time.time(), "models": models}, f)

    return models


def parse_slug(text):
    """
    Detect if input is already a valid OpenRouter slug (provider/model-name[:suffix]).
    Also handles tilde-prefixed latest-alias slugs (~provider/model-latest).
    Returns (base_slug, suffix) or (None, None).
    """
    t = text.strip()
    # Match tilde-prefixed latest-alias slugs: ~provider/model-latest
    m = re.match(r'^(~[a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+)(?::([a-zA-Z]+))?$', t)
    if m:
        return m.group(1), m.group(2)
    # Match standard slugs: provider/model-name[:suffix]
    m = re.match(r'^([a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+)(?::([a-zA-Z]+))?$', t)
    if m:
        return m.group(1), m.group(2)
    return None, None


def normalize(text):
    """Lowercase, strip punctuation, return token list."""
    return re.sub(r"[^a-z0-9]", " ", text.lower()).split()


def extract_suffix_from_query(query_tokens):
    """
    Check if any known suffix was explicitly mentioned in the query.
    Returns (clean_tokens, requested_suffix or None).
    """
    for suffix in KNOWN_SUFFIXES:
        if suffix in query_tokens:
            clean = [t for t in query_tokens if t != suffix]
            return clean, suffix
    return query_tokens, None


def score_match(query_tokens, requested_suffix, model):
    """
    Score how well a query matches a model. Higher = better.
    query_tokens: tokens WITHOUT the suffix
    requested_suffix: the suffix user explicitly asked for (or None)
    """
    raw_id = model["id"]  # e.g. "anthropic/claude-sonnet-4.6:free"
    model_name = model.get("name", "").lower()

    # Split base slug and model suffix
    if ":" in raw_id:
        base_id, model_suffix = raw_id.rsplit(":", 1)
    else:
        base_id, model_suffix = raw_id, None

    base_id_lower = base_id.lower()
    combined = base_id_lower + " " + model_name

    score = 0
    matched = 0

    for token in query_tokens:
        if token in combined:
            score += 10
            matched += 1
        if token in base_id_lower:
            score += 5  # bonus for matching in the slug specifically

    # Exact base slug match (ignoring suffix) is highest priority
    query_joined = "".join(query_tokens)
    id_clean = re.sub(r"[^a-z0-9]", "", base_id_lower)
    if query_joined == id_clean:
        score += 1000

    # Penalize if not all tokens matched
    if matched < len(query_tokens):
        score -= (len(query_tokens) - matched) * 8

    # Penalize models that have MORE tokens than the query (e.g. gpt-4.1-mini when user said gpt-4.1)
    # This rewards the most specific match without extra sub-versions
    model_id_tokens = normalize(base_id_lower)
    extra_tokens = len(model_id_tokens) - len(query_tokens)
    if extra_tokens > 0 and matched == len(query_tokens):
        score -= extra_tokens * 4

    # Suffix handling:
    if model_suffix:
        if requested_suffix and model_suffix.lower() == requested_suffix.lower():
            # User explicitly asked for this suffix — reward it
            score += 50
        elif not requested_suffix:
            # User did NOT ask for a suffix — penalize suffixed variants
            score -= SUFFIX_PENALTY

    return score


def resolve(query, models, top_n=5):
    """Return top N matching models for a query string."""
    query_tokens, requested_suffix = extract_suffix_from_query(normalize(query))
    scored = [(score_match(query_tokens, requested_suffix, m), m) for m in models]
    scored.sort(key=lambda x: -x[0])
    results = [(s, m) for s, m in scored[:top_n] if s > 0]
    return results, requested_suffix


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: resolve_model.py <query>  OR  resolve_model.py --list [provider]")
        sys.exit(1)

    # Handle --refresh
    if args[0] == "--refresh":
        fetch_models(force_refresh=True)
        print("Model cache refreshed.")
        return

    # Handle --list
    if args[0] == "--list":
        models = fetch_models()
        provider = args[1].lower() if len(args) > 1 else None
        if provider == "~":
            # Special case: list all tilde/latest-alias models
            # Tilde slugs look like ~anthropic/claude-sonnet-latest (start with ~)
            filtered = [m for m in models if m["id"].startswith("~")]
            if not filtered:
                # Fallback: search for 'latest' in id
                filtered = [m for m in models if "latest" in m["id"].lower()]
        elif provider:
            filtered = [m for m in models if m["id"].lower().startswith(provider + "/")]
        else:
            filtered = list(models)
        filtered.sort(key=lambda m: m["id"])
        for m in filtered:
            ctx = m.get("context_length", "?")
            print(f"{m['id']:65s}  ctx={ctx}")
        print(f"\nTotal: {len(filtered)} models")
        return

    query = " ".join(args)

    # --- Exact slug passthrough (including tilde slugs) ---
    base_slug, suffix = parse_slug(query)
    if base_slug:
        full_slug = f"{base_slug}:{suffix}" if suffix else base_slug
        is_tilde = full_slug.startswith("~")
        label = "Tilde latest-alias slug" if is_tilde else "Exact slug"
        print(f"\n{label} detected — using as-is:")
        print(f"  Slug : {full_slug}")
        if is_tilde:
            print(f"  Note : This is an always-latest alias. It will always route to the"
                  f" current latest version of this model family.")
        print(f"\nUSE_SLUG={full_slug}")
        return

    # --- Check if user is asking for a latest-alias in natural language ---
    # e.g. "claude sonnet latest", "gemini flash latest", "kimi latest"
    query_lower = query.lower().strip()
    if "latest" in query_lower:
        try:
            models_for_tilde = fetch_models()
        except Exception:
            models_for_tilde = []
        tilde_models = [m for m in models_for_tilde if m["id"].startswith("~")]
        if tilde_models:
            # Score tilde models against the query (minus the word 'latest')
            query_no_latest = query_lower.replace("latest", "").strip()
            query_tokens_tilde = normalize(query_no_latest)
            best_tilde = None
            best_tilde_score = -1
            for m in tilde_models:
                # Score against the tilde slug (strip the ~ and -latest for matching)
                slug_clean = m["id"].lstrip("~").lower().replace("-latest", "")
                slug_tokens = normalize(slug_clean)
                score = 0
                matched = 0
                for tok in query_tokens_tilde:
                    if tok in slug_clean:
                        score += 10
                        matched += 1
                # Penalize slugs with more tokens than the query (prefer exact-length match)
                extra = len(slug_tokens) - len(query_tokens_tilde)
                if extra > 0 and matched == len(query_tokens_tilde):
                    score -= extra * 4
                if score > best_tilde_score:
                    best_tilde_score = score
                    best_tilde = m
            if best_tilde and best_tilde_score > 0:
                print(f"\nLatest-alias match:")
                print(f"  Slug : {best_tilde['id']}")
                print(f"  Name : {best_tilde['name']}")
                print(f"  Note : Always-latest alias — routes to current latest version.")
                if best_tilde.get("context_length"):
                    print(f"  Context: {best_tilde['context_length']:,} tokens")
                print(f"\nOther tilde models available (run --list ~ to see all):")
                for m in tilde_models:
                    if m["id"] != best_tilde["id"]:
                        print(f"  {m['id']}")
                print(f"\nUSE_SLUG={best_tilde['id']}")
                return

    # --- Fuzzy resolution ---
    try:
        models = fetch_models()
    except Exception as e:
        print(f"Warning: Could not fetch live models ({e}). Trying cached data...")
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE) as f:
                cached = json.load(f)
            models = cached.get("models", [])
        else:
            print("No cached model data available. Run --refresh to populate cache.")
            sys.exit(1)

    results, requested_suffix = resolve(query, models)

    if not results:
        print(f"No matches found for: {query}")
        print("Try: python3.11 resolve_model.py --list  to see all available models")
        sys.exit(1)

    best_score, best_model = results[0]

    # Ambiguity warning — relative to score magnitude
    ambiguous = False
    if len(results) > 1:
        second_score = results[1][0]
        gap = best_score - second_score
        threshold = max(AMBIGUITY_MIN_GAP, best_score * AMBIGUITY_RATIO)
        if gap <= threshold:
            ambiguous = True

    print(f"\nBest match:")
    print(f"  Slug : {best_model['id']}")
    print(f"  Name : {best_model['name']}")
    print(f"  Score: {best_score}")
    if best_model.get("context_length"):
        print(f"  Context: {best_model['context_length']:,} tokens")

    if ambiguous:
        print(f"\n  ⚠  AMBIGUOUS — top candidates are close in score. Verify before use.")

    if len(results) > 1:
        print(f"\nOther candidates:")
        threshold = max(AMBIGUITY_MIN_GAP, best_score * AMBIGUITY_RATIO)
        for score, m in results[1:]:
            gap_to_best = best_score - score
            flag = " \u2190 close match" if gap_to_best <= threshold else ""
            print(f"  {m['id']:65s}  (score {score}){flag}")

    # If user asked for a suffix but best match doesn't have it, suggest appending
    if requested_suffix and ":" not in best_model["id"]:
        suggested = f"{best_model['id']}:{requested_suffix}"
        print(f"\n  ℹ  You requested :{requested_suffix} — suggested slug: {suggested}")
        print(f"\nUSE_SLUG={suggested}")
    else:
        print(f"\nUSE_SLUG={best_model['id']}")


if __name__ == "__main__":
    main()
