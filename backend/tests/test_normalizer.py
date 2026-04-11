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
    for key in [
        "system_name",
        "purpose",
        "core_features",
        "user_types",
        "constraints",
        "assumptions",
        "unknowns",
        "input_output",
        "data_model",
    ]:
        assert key in result


def test_core_features_is_list():
    result = normalize("anything", SELECTIONS)
    assert isinstance(result["core_features"], list)
    assert len(result["core_features"]) >= 1


def test_purpose_is_nonempty_string():
    result = normalize("anything", SELECTIONS)
    assert isinstance(result["purpose"], str)
    assert len(result["purpose"]) > 10


def test_assumptions_and_unknowns_present():
    result = normalize("anything", SELECTIONS)
    assert isinstance(result["assumptions"], list)
    assert len(result["assumptions"]) >= 1
    assert isinstance(result["unknowns"], list)
    assert len(result["unknowns"]) >= 1


def test_input_output_and_data_model_lists():
    result = normalize("anything", SELECTIONS)
    assert isinstance(result["input_output"], list)
    assert len(result["input_output"]) >= 1
    assert isinstance(result["data_model"], list)
    assert len(result["data_model"]) >= 1
