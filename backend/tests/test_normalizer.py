import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PYTEST_RUNNING", "1")

from pipeline.normalizer import normalize

SELECTIONS = {
    "scope": "fullstack",
    "backend": "fastapi",
    "frontend": "react",
    "apis": [],
    "database": "postgres",
}


def test_normalize_returns_required_keys():
    result = normalize("A task manager for remote teams", SELECTIONS)
    for key in ["system_name", "purpose", "core_features", "user_types", "constraints", "assumptions_removed"]:
        assert key in result


def test_core_features_is_list():
    result = normalize("anything", SELECTIONS)
    assert isinstance(result["core_features"], list)
    assert len(result["core_features"]) >= 1


def test_purpose_is_nonempty_string():
    result = normalize("anything", SELECTIONS)
    assert isinstance(result["purpose"], str)
    assert len(result["purpose"]) > 10
