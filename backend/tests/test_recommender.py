import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PYTEST_RUNNING", "1")

from pipeline.recommender import get_recommendation


def test_recommendation_has_required_fields():
    constraints = {
        "user_scale": "single",
        "auth": "none",
        "execution": "short",
        "app_shape": "ai_core",
        "data": {"types": ["text"], "persistence": "permanent"},
    }
    result = get_recommendation("AI journaling app", constraints)

    for key in (
        "system_understanding",
        "system_type",
        "core_system_logic",
        "key_requirements",
        "scope_boundaries",
        "phased_plan",
        "recommended",
        "rationale",
        "constraint_impact",
        "assumptions",
        "confidence",
    ):
        assert key in result

    rec = result["recommended"]
    for key in ("scope", "backend", "frontend", "apis", "database"):
        assert key in rec

    confidence = result["confidence"]
    assert isinstance(confidence, dict)
    assert 0 <= confidence.get("score", -1) <= 100
    assert isinstance(confidence.get("reason"), str)

    assert isinstance(result["assumptions"], list)
    assert len(result["assumptions"]) > 0
    assert isinstance(result["constraint_impact"], list)
    assert len(result["constraint_impact"]) > 0
