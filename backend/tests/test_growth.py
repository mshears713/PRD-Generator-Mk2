import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from unittest.mock import patch, MagicMock
from pipeline.growth import generate_growth_check


FAKE_PRD = "# TeamTask PRD\n## Overview\nA task manager.\n## Test Cases\n| Test | Input | Expected | Type |\n|------|-------|----------|------|\n| create | POST | 201 | integration |"

SELECTIONS = {
    "scope": "fullstack",
    "backend": "fastapi",
    "frontend": "react",
    "apis": [],
    "database": "postgres",
}

FAKE_GROWTH = """## Growth Check

### ✅ Good Choices
- **FastAPI + React:** Proven fullstack combination with strong ecosystem support.
- **PostgreSQL:** Reliable relational database well-suited for task management data.

### ⚠️ Warnings
- **No authentication:** The PRD does not define an auth mechanism — tasks will be publicly writable.

### ❌ Missing Components
- **Rate limiting:** No rate limiting on the API means the endpoint is open to abuse.
"""


def make_openai_response(content: str):
    mock = MagicMock()
    mock.choices[0].message.content = content
    return mock


def test_growth_check_returns_string():
    with patch("pipeline.growth.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_GROWTH)
        result = generate_growth_check(FAKE_PRD, SELECTIONS)
    assert isinstance(result, str)
    assert len(result) > 50


def test_growth_check_contains_indicators():
    with patch("pipeline.growth.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_GROWTH)
        result = generate_growth_check(FAKE_PRD, SELECTIONS)
    assert "✅" in result
    assert "⚠️" in result
    assert "❌" in result


def test_growth_check_with_apis_in_selections():
    selections_with_apis = {
        "scope": "fullstack",
        "backend": "fastapi",
        "frontend": "react",
        "apis": ["openrouter", "tavily"],
        "database": "postgres",
    }
    with patch("pipeline.growth.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_GROWTH)
        result = generate_growth_check(FAKE_PRD, selections_with_apis)
    assert isinstance(result, str)
    assert len(result) > 50
