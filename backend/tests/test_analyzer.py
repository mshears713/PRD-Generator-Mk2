import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from unittest.mock import patch, MagicMock
from pipeline.analyzer import analyze


FAKE_NORMALIZED = {
    "system_name": "TeamTask",
    "purpose": "Lets remote teams track tasks.",
    "core_features": ["Create tasks", "Assign tasks"],
    "user_types": ["admin", "member"],
    "constraints": ["FastAPI"],
    "assumptions_removed": ["vague → specific"],
}

FAKE_ARCHITECTURE = {
    "components": [
        {"name": "Task API", "responsibility": "CRUD operations for tasks"},
        {"name": "Auth Service", "responsibility": "User authentication and sessions"},
    ],
    "data_flow": [
        "Step 1: User submits task → API validates and stores in DB",
        "Step 2: Assigned user notified via WebSocket",
    ],
    "dependencies": [
        "Task API depends on Auth Service for user identity"
    ],
    "risks": [
        "WebSocket connections may not scale without a message broker"
    ],
}


def make_openai_response(content: dict):
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps(content)
    return mock


def test_analyze_returns_required_keys():
    with patch("pipeline.analyzer.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ARCHITECTURE)
        result = analyze(FAKE_NORMALIZED)
    for key in ["components", "data_flow", "dependencies", "risks"]:
        assert key in result, f"Missing key: {key}"


def test_components_are_list_of_dicts():
    with patch("pipeline.analyzer.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ARCHITECTURE)
        result = analyze(FAKE_NORMALIZED)
    assert isinstance(result["components"], list)
    assert len(result["components"]) >= 1
    assert "name" in result["components"][0]
    assert "responsibility" in result["components"][0]


def test_data_flow_is_list_of_strings():
    with patch("pipeline.analyzer.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ARCHITECTURE)
        result = analyze(FAKE_NORMALIZED)
    assert isinstance(result["data_flow"], list)
    assert all(isinstance(s, str) for s in result["data_flow"])
