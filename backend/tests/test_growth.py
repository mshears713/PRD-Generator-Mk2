import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from unittest.mock import patch, MagicMock
from pipeline.growth import generate_growth_check

FAKE_SELECTIONS = {
    "scope": "fullstack", "backend": "fastapi",
    "frontend": "react", "apis": [], "database": "postgres",
}

FAKE_GROWTH = {
    "good": [{"title": "FastAPI async", "detail": "Handles non-blocking AI calls without thread overhead."}],
    "warnings": [{"title": "Cold starts", "detail": "Render free tier sleeps after 15 min inactivity."}],
    "missing": [{"title": "Rate limiting", "detail": "External API calls need throttling to avoid cost spikes."}],
}

def make_openai_response(content: dict):
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps(content)
    return mock

def test_returns_structured_dict():
    with patch("pipeline.growth.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_GROWTH)
        result = generate_growth_check("# PRD\ntest", FAKE_SELECTIONS)
    assert isinstance(result, dict)
    assert "good" in result
    assert "warnings" in result
    assert "missing" in result

def test_good_items_have_title_and_detail():
    with patch("pipeline.growth.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_GROWTH)
        result = generate_growth_check("# PRD\ntest", FAKE_SELECTIONS)
    for item in result["good"]:
        assert "title" in item
        assert "detail" in item

def test_warnings_and_missing_have_title_and_detail():
    with patch("pipeline.growth.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_GROWTH)
        result = generate_growth_check("# PRD\ntest", FAKE_SELECTIONS)
    for section in ("warnings", "missing"):
        for item in result[section]:
            assert "title" in item
            assert "detail" in item

def test_all_sections_are_lists():
    with patch("pipeline.growth.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_GROWTH)
        result = generate_growth_check("# PRD\ntest", FAKE_SELECTIONS)
    assert isinstance(result["good"], list)
    assert isinstance(result["warnings"], list)
    assert isinstance(result["missing"], list)

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
        result = generate_growth_check("# PRD\ntest", selections_with_apis)
    assert isinstance(result, dict)
    assert "good" in result
