import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.api_candidate_selector import select_api_candidates


def _ids(items):
    return [i["id"] for i in items]


def test_testing_flag_includes_blaxel():
    idea = "Task runner with workflow"
    constraints = {"testing": True, "app_shape": "workflow", "data": {"types": ["text"], "persistence": "temporary"}}
    result = select_api_candidates(idea, constraints)
    assert "blaxel" in _ids(result["selected"])


def test_testing_flag_excludes_blaxel_when_false():
    idea = "Task runner with workflow"
    constraints = {"testing": False, "data": {"types": ["text"], "persistence": "temporary"}}
    result = select_api_candidates(idea, constraints)
    assert "blaxel" in _ids(result["rejected"])


def test_ai_core_selects_llm_and_search_when_needed():
    idea = "AI assistant that searches the web for news"
    constraints = {"app_shape": "ai_core", "data": {"types": ["text"], "persistence": "permanent"}, "execution": "realtime"}
    result = select_api_candidates(idea, constraints)
    selected_ids = _ids(result["selected"])
    assert "openrouter" in selected_ids
    assert "tavily" in selected_ids
    # upstash may appear as candidate for cache
    all_ids = _ids(result["selected"]) + _ids(result["candidates"]) + _ids(result["rejected"])
    assert "upstash_redis" in all_ids
