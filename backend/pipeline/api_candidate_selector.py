from __future__ import annotations

import re
from typing import Iterable

from data.api_registry import get_by_category, get_by_id, get_registry


def _detect(text: str, keywords: Iterable[str]) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(k in lowered for k in keywords)


def _signals(idea: str, constraints: dict) -> dict:
    data = constraints.get("data") or {}
    types = data.get("types") or []
    persistence = data.get("persistence")
    app_shape = constraints.get("app_shape")
    execution = constraints.get("execution")
    auth = constraints.get("auth")

    ai_core = app_shape == "ai_core" or _detect(
        idea, ["ai", "llm", "assistant", "chatbot", "generate", "summarize", "classify", "rag"]
    )
    multimodal = _detect(idea, ["image", "video", "audio", "vision", "multimodal"]) or "files" in types
    needs_search = _detect(idea, ["search", "news", "web", "latest", "crawl"])
    needs_maps = _detect(idea, ["map", "geocode", "geospatial", "location", "route", "gps"]) or "geo" in types
    needs_browser = _detect(idea, ["scrape", "browser", "puppeteer", "playwright", "selenium", "headless"])
    needs_docs = _detect(idea, ["doc", "notion", "slack", "google doc", "drive", "collaboration", "workspace"])

    persistent = persistence == "permanent"
    has_data = (types and types != ["none"]) or persistent
    needs_cache = execution == "realtime" or ai_core

    testing_required = constraints.get("testing") is True

    return {
        "ai_core": ai_core,
        "multimodal": multimodal,
        "needs_search": needs_search,
        "needs_maps": needs_maps,
        "needs_browser": needs_browser,
        "needs_docs": needs_docs,
        "persistent": persistent,
        "has_data": has_data,
        "needs_cache": needs_cache,
        "testing_required": testing_required,
        "user_scale": constraints.get("user_scale"),
        "auth": auth,
        "execution": execution,
    }


def _shape(item: dict, status: str, reason: str, why_not: str | None = None, recommended: bool = False) -> dict:
    return {
        "id": item["id"],
        "name": item["name"],
        "category": item["category"],
        "status": status,
        "recommended": recommended,
        "reason": reason,
        "why_not": why_not,
        "sponsored": item.get("sponsored", False),
        "sponsor_note": item.get("sponsor_note"),
        "summary": item.get("summary"),
        "best_for": item.get("best_for", []),
        "avoid_when": item.get("avoid_when", []),
        "tags": item.get("tags", []),
        "complexity": item.get("complexity"),
        "backend_required": item.get("backend_required"),
        "common_pairings": item.get("common_pairings", []),
    }


def _cap(items: list[dict], limit: int) -> list[dict]:
    return items[:limit] if limit and limit > 0 else items


def _pick_database(signals: dict) -> tuple[list[dict], list[dict]]:
    """Return (selected, optional) for database category."""
    entries = {item["id"]: item for item in get_by_category("database")}
    selected: list[dict] = []
    optional: list[dict] = []

    user_scale = signals.get("user_scale")
    persistent = signals.get("persistent")
    needs_cache = signals.get("needs_cache")

    if persistent:
        if user_scale in {"single", "small"} and "supabase" in entries:
            primary = entries["supabase"]
            alt = entries.get("postgres")
        else:
            primary = entries.get("postgres")
            alt = entries.get("supabase")
        if primary:
            selected.append(primary)
        if alt:
            optional.append(alt)
        if needs_cache and entries.get("upstash_redis"):
            optional.append(entries["upstash_redis"])
        if entries.get("firebase"):
            optional.append(entries["firebase"])
    else:
        if needs_cache and entries.get("upstash_redis"):
            selected.append(entries["upstash_redis"])
        elif entries.get("firebase") and user_scale in {"single", "small", None}:
            selected.append(entries["firebase"])
        if entries.get("postgres"):
            optional.append(entries["postgres"])
        if entries.get("supabase"):
            optional.append(entries["supabase"])

    return selected, optional


def select_api_candidates(idea: str, constraints: dict | None = None, max_per_category: int = 3, max_total: int = 10) -> dict:
    constraints = constraints or {}
    signals = _signals(idea, constraints)
    registry = {item["id"]: item for item in get_registry()}

    selected: list[dict] = []
    candidates: list[dict] = []
    rejected: list[dict] = []
    seen: set[str] = set()

    def add(item: dict, status: str, reason: str, why_not: str | None = None, recommended: bool = False):
        if not item or item["id"] in seen:
            return
        seen.add(item["id"])
        payload = _shape(item, status=status, reason=reason, why_not=why_not, recommended=recommended)
        if status == "selected":
            selected.append(payload)
        elif status == "candidate":
            candidates.append(payload)
        else:
            rejected.append(payload)

    # ai inference
    if signals["ai_core"]:
        for item_id in ("openrouter", "openai", "anthropic"):
            item = registry.get(item_id)
            if not item:
                continue
            if item_id == "openrouter":
                add(item, "selected", "LLM is core; OpenRouter keeps model choice flexible.", recommended=True)
            else:
                add(item, "candidate", "LLM required; useful alternative provider for coverage.")
        if signals["multimodal"] and registry.get("replicate"):
            add(registry["replicate"], "candidate", "Multimodal or image/audio generation implied.")
    else:
        for item_id in ("openrouter", "openai", "anthropic", "replicate"):
            item = registry.get(item_id)
            if item:
                add(item, "rejected", "LLM inference not core to this project.", why_not="No AI-core requirement detected")

    # research search
    if signals["needs_search"]:
        if registry.get("tavily"):
            add(registry["tavily"], "selected", "Project mentions web/news search; Tavily gives structured results.", recommended=True)
        for item_id in ("serpapi", "brave_search"):
            item = registry.get(item_id)
            if item:
                add(item, "candidate", "Search is relevant; keep as backup/alternate index.")
    else:
        for item_id in ("tavily", "serpapi", "brave_search"):
            item = registry.get(item_id)
            if item:
                add(item, "rejected", "No external web search requirement detected.", why_not="needs_search=false")

    # maps
    if signals["needs_maps"]:
        if registry.get("mapbox"):
            add(registry["mapbox"], "selected", "Maps/geocoding appear in idea; Mapbox for styled tiles.", recommended=True)
        if registry.get("google_maps_platform"):
            add(registry["google_maps_platform"], "candidate", "Places/routing data available if needed.")
    else:
        for item_id in ("mapbox", "google_maps_platform"):
            item = registry.get(item_id)
            if item:
                add(item, "rejected", "Mapping not indicated.")

    # database
    if signals["has_data"] or signals["needs_cache"]:
        db_selected, db_optional = _pick_database(signals)
        for item in _cap(db_selected, max_per_category):
            add(item, "selected", "Data/storage needs require this database tier.", recommended=True)
        for item in _cap(db_optional, max_per_category):
            add(item, "candidate", "Viable database depending on final data shape.")
    else:
        for item_id in ("postgres", "supabase", "upstash_redis", "firebase"):
            item = registry.get(item_id)
            if item:
                add(item, "rejected", "No persistent storage or caching required.")

    # testing
    blaxel = registry.get("blaxel")
    if blaxel:
        if signals["testing_required"]:
            add(blaxel, "selected", "User requested testing support; Blaxel is the hosted option.", recommended=True)
        else:
            add(blaxel, "rejected", "Testing support not requested.", why_not="testing=false")

    # automation browser
    if signals["needs_browser"]:
        if registry.get("playwright"):
            add(registry["playwright"], "selected", "Browser automation implied; Playwright is deterministic.", recommended=True)
        if registry.get("browserbase"):
            add(registry["browserbase"], "candidate", "Hosted browser sessions if scaling headless usage.")
    else:
        for item_id in ("playwright", "browserbase"):
            item = registry.get(item_id)
            if item:
                add(item, "rejected", "No browser automation requirement detected.")

    # docs + collaboration
    if signals["needs_docs"]:
        if _detect(idea, ["google", "workspace", "drive"]):
            primary = registry.get("google_docs_drive")
            secondary = registry.get("notion_api")
        else:
            primary = registry.get("notion_api")
            secondary = registry.get("google_docs_drive")
        if primary:
            add(primary, "selected", "Docs/collaboration noted; fits content workspace.", recommended=True)
        if secondary:
            add(secondary, "candidate", "Alternate docs surface if team uses it.")
        if registry.get("slack_api"):
            add(registry["slack_api"], "candidate", "Notifications or chat ops channel if needed.")
    else:
        for item_id in ("notion_api", "slack_api", "google_docs_drive"):
            item = registry.get(item_id)
            if item:
                add(item, "rejected", "Docs/collaboration not required.")

    # apply caps
    selected = _cap(selected, max_total)
    candidates = _cap(candidates, max_total)
    rejected = _cap(rejected, max_total * 2)

    return {
        "selected": selected,
        "candidates": candidates,
        "rejected": rejected,
    }
