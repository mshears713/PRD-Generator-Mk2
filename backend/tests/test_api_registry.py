import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.api_registry import get_registry, get_by_category


def test_registry_loads_and_has_required_fields():
    registry = get_registry()
    assert len(registry) >= 1
    required = {
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
    for entry in registry:
        assert required.issubset(entry.keys())


def test_categories_filter():
    ai_entries = get_by_category("ai_inference")
    assert ai_entries
    for entry in ai_entries:
        assert entry["category"] == "ai_inference"
