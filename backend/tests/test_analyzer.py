import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PYTEST_RUNNING", "1")

from pipeline.analyzer import analyze

FAKE_NORMALIZED = {
    "system_name": "TeamTask",
    "purpose": "Lets remote teams track tasks.",
    "core_features": ["Create tasks", "Assign tasks"],
    "user_types": ["admin", "member"],
    "constraints": ["FastAPI"],
    "assumptions": ["Assuming single-user load"],
    "unknowns": ["Scaling not specified"],
    "input_output": ["Step 1: User submits task → API stores it"],
    "data_model": ["Task: id, title"],
}


def test_analyze_returns_required_keys():
    result = analyze(FAKE_NORMALIZED)
    for key in ["components", "data_flow", "dependencies", "risks", "failure_points", "minimal_mvp_components"]:
        assert key in result


def test_components_are_list_of_dicts():
    result = analyze(FAKE_NORMALIZED)
    assert isinstance(result["components"], list)
    assert len(result["components"]) >= 1
    assert "name" in result["components"][0]
    assert "responsibility" in result["components"][0]


def test_data_flow_is_list_of_strings():
    result = analyze(FAKE_NORMALIZED)
    assert isinstance(result["data_flow"], list)
    assert all(isinstance(s, str) for s in result["data_flow"])


def test_failure_points_and_mvp_components_lists():
    result = analyze(FAKE_NORMALIZED)
    assert isinstance(result["failure_points"], list)
    assert isinstance(result["minimal_mvp_components"], list)
    assert len(result["minimal_mvp_components"]) >= 1
