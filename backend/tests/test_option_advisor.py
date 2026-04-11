import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PYTEST_RUNNING", "1")

from pipeline.option_advisor import get_all_option_advice

FAKE_RECOMMENDED = {
    "scope": "fullstack",
    "backend": "fastapi",
    "frontend": "react",
    "database": "postgres",
}

FAKE_CONSTRAINTS = {
    "user_scale": "single",
    "auth": "none",
    "execution": "short",
    "app_shape": "simple",
    "data": {"types": ["text"], "persistence": "permanent"},
}


def test_option_advisor_structure():
    result = get_all_option_advice("A todo app", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    for field in ("scope", "backend", "frontend", "database"):
        assert field in result
        assert "recommended" in result[field]
        assert "options" in result[field]


def test_each_option_has_required_fields():
    result = get_all_option_advice("A todo app", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    for field, field_data in result.items():
        for value, option in field_data["options"].items():
            for key in (
                "fit_score",
                "confidence",
                "complexity_cost",
                "reason",
                "benefits",
                "drawbacks",
                "why_not_recommended",
            ):
                assert key in option, f"{field}/{value} missing key: {key}"


def test_why_not_recommended_enforced_when_low_score():
    result = get_all_option_advice("A todo app", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    none_backend = result["backend"]["options"]["none"]
    assert none_backend["fit_score"] < 70
    assert none_backend["why_not_recommended"]
