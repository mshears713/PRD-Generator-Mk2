import json
import os
from typing import Iterable

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "api_registry.json")

_REQUIRED_FIELDS = {
    "id",
    "name",
    "category",
    "summary",
    "best_for",
    "avoid_when",
    "complexity",
    "tags",
    "common_pairings",
    "recommended_when",
    "sponsored",
    "sponsor_note",
    "beginner_friendly",
    "backend_required",
}

_APPROVED_CATEGORIES = {
    "ai_inference",
    "research_search",
    "maps",
    "database",
    "testing",
    "automation_browser",
    "docs_collaboration",
}

_cache: list[dict] | None = None


def _load() -> list[dict]:
    global _cache
    if _cache is not None:
        return _cache
    if not os.path.exists(REGISTRY_PATH):
        raise FileNotFoundError(f"API registry not found at {REGISTRY_PATH}")
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("API registry must be a list of entries")

    normalized: list[dict] = []
    seen_ids: set[str] = set()
    for entry in data:
        if not _REQUIRED_FIELDS.issubset(entry.keys()):
            missing = _REQUIRED_FIELDS - set(entry.keys())
            raise ValueError(f"Registry entry missing fields {missing}: {entry}")
        if entry["category"] not in _APPROVED_CATEGORIES:
            raise ValueError(f"Invalid category {entry['category']} for {entry['id']}")
        if entry["id"] in seen_ids:
            raise ValueError(f"Duplicate id in registry: {entry['id']}")
        seen_ids.add(entry["id"])
        normalized.append(entry)

    _cache = normalized
    return normalized


def get_registry() -> list[dict]:
    return list(_load())


def get_by_category(category: str) -> list[dict]:
    return [item for item in _load() if item.get("category") == category]


def get_by_id(item_id: str) -> dict | None:
    for item in _load():
        if item.get("id") == item_id:
            return item
    return None


def filter_categories(categories: Iterable[str]) -> list[dict]:
    cats = set(categories)
    return [item for item in _load() if item.get("category") in cats]
