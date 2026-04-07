import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from pipeline.recommender import get_recommendation


FAKE_RESPONSE = {
    "summary": "A task management platform where remote teams create, assign, and track tasks in real time.",
    "recommended": {
        "scope": "fullstack",
        "backend": "fastapi",
        "frontend": "react",
        "apis": [],
        "database": "postgres",
    },
}


def make_openai_response(content: dict):
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps(content)
    return mock


def test_returns_summary_and_recommended():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("A task manager for remote teams")
    assert "summary" in result
    assert "recommended" in result


def test_recommended_has_required_keys():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("anything")
    rec = result["recommended"]
    assert "scope" in rec
    assert "backend" in rec
    assert "frontend" in rec
    assert "apis" in rec
    assert "database" in rec


def test_apis_is_list():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("anything")
    assert isinstance(result["recommended"]["apis"], list)


def test_summary_is_nonempty_string():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("anything")
    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 0
