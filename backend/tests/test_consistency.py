import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PYTEST_RUNNING", "1")

from pipeline.growth import check_stack_consistency


def test_detects_frontend_none_with_ui_features():
    selections = {"frontend": "none", "backend": "fastapi", "database": "postgres", "apis": [], "scope": "backend"}
    normalized = {
        "core_features": ["User submits via web UI", "Process data"],
        "input_output": ["Step 1: User fills form in UI"],
        "data_model": ["No persistent data stored"],
        "constraints": [],
    }

    issues = check_stack_consistency(selections, normalized)
    assert any("Frontend set to none" in issue for issue in issues)
