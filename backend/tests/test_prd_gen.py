import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PYTEST_RUNNING", "1")

from pipeline.prd_gen import generate_prd

FAKE_NORMALIZED = {
    "system_name": "TeamTask",
    "purpose": "Lets remote teams track tasks.",
    "core_features": ["Create tasks", "Assign tasks"],
    "user_types": ["admin", "member"],
    "constraints": ["FastAPI"],
    "assumptions_removed": ["vague → specific"],
}

FAKE_ARCHITECTURE = {
    "components": [{"name": "Task API", "responsibility": "CRUD for tasks"}],
    "data_flow": ["Step 1: User creates task → stored in DB"],
    "dependencies": ["Task API uses DB"],
    "risks": ["No rate limiting on API"],
}


def test_generate_prd_returns_string():
    result = generate_prd(FAKE_NORMALIZED, FAKE_ARCHITECTURE)
    assert isinstance(result, str)
    assert len(result) > 100


def test_generate_prd_contains_required_sections():
    result = generate_prd(FAKE_NORMALIZED, FAKE_ARCHITECTURE)
    for section in ["Overview", "Architecture", "Components", "Test Cases"]:
        assert section in result
