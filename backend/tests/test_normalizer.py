import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from unittest.mock import patch, MagicMock
from pipeline.normalizer import normalize


FAKE_NORMALIZED = {
    "system_name": "TeamTask",
    "purpose": "Lets remote teams create, assign, and track tasks with real-time updates.",
    "core_features": ["Create tasks", "Assign to users", "Track status", "Real-time updates"],
    "user_types": ["admin", "team member"],
    "constraints": ["FastAPI backend requires Python 3.10+", "React frontend requires Node 18+"],
    "assumptions_removed": ["'real-time' → WebSocket-based live updates", "'remote teams' → multi-user with role-based access"],
}

SELECTIONS = {
    "scope": "fullstack",
    "backend": "fastapi",
    "frontend": "react",
    "apis": [],
    "database": "postgres",
}


def make_openai_response(content: dict):
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps(content)
    return mock


def test_normalize_returns_required_keys():
    with patch("pipeline.normalizer.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_NORMALIZED)
        result = normalize("A task manager for remote teams", SELECTIONS)
    for key in ["system_name", "purpose", "core_features", "user_types", "constraints", "assumptions_removed"]:
        assert key in result, f"Missing key: {key}"


def test_core_features_is_list():
    with patch("pipeline.normalizer.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_NORMALIZED)
        result = normalize("anything", SELECTIONS)
    assert isinstance(result["core_features"], list)
    assert len(result["core_features"]) >= 1


def test_purpose_is_nonempty_string():
    with patch("pipeline.normalizer.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_NORMALIZED)
        result = normalize("anything", SELECTIONS)
    assert isinstance(result["purpose"], str)
    assert len(result["purpose"]) > 10
