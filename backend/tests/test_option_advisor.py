import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from unittest.mock import patch, MagicMock
from pipeline.option_advisor import get_all_option_advice

FAKE_RECOMMENDED = {
    "scope": "fullstack",
    "backend": "fastapi",
    "frontend": "react",
    "database": "postgres",
}

FAKE_CONSTRAINTS = {
    "user_scale": "small",
    "auth": "none",
    "execution": "short",
    "app_shape": "simple",
    "data": {"types": ["text"], "persistence": "temporary"},
}

FAKE_OPTION_RESULT = {
    "relevant": True,
    "reason": "Fits the project well.",
    "benefits": ["Benefit one", "Benefit two"],
    "drawbacks": ["Drawback one"],
}


def make_openai_response(content: dict):
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps(content)
    return mock


def test_returns_all_four_fields():
    with patch("pipeline.option_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_OPTION_RESULT)
        result = get_all_option_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    for field in ("scope", "backend", "frontend", "database"):
        assert field in result, f"missing field: {field}"


def test_each_field_has_recommended_and_options():
    with patch("pipeline.option_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_OPTION_RESULT)
        result = get_all_option_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    assert result["scope"]["recommended"] == "fullstack"
    assert result["backend"]["recommended"] == "fastapi"
    assert result["frontend"]["recommended"] == "react"
    assert result["database"]["recommended"] == "postgres"
    for field in ("scope", "backend", "frontend", "database"):
        assert "options" in result[field]


def test_scope_has_three_options():
    with patch("pipeline.option_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_OPTION_RESULT)
        result = get_all_option_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    assert set(result["scope"]["options"].keys()) == {"frontend", "backend", "fullstack"}


def test_each_option_has_required_fields():
    with patch("pipeline.option_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_OPTION_RESULT)
        result = get_all_option_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    for field, field_data in result.items():
        for value, option in field_data["options"].items():
            for key in ("relevant", "reason", "benefits", "drawbacks"):
                assert key in option, f"{field}/{value} missing key: {key}"


def test_benefits_and_drawbacks_are_lists():
    with patch("pipeline.option_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_OPTION_RESULT)
        result = get_all_option_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    for field, field_data in result.items():
        for value, option in field_data["options"].items():
            assert isinstance(option["benefits"], list), f"{field}/{value} benefits not a list"
            assert isinstance(option["drawbacks"], list), f"{field}/{value} drawbacks not a list"


def test_fastapi_has_learn_more_url():
    with patch("pipeline.option_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_OPTION_RESULT)
        result = get_all_option_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    assert result["backend"]["options"]["fastapi"]["learn_more_url"] == "https://fastapi.tiangolo.com/"
    assert result["frontend"]["options"]["react"]["learn_more_url"] == "https://react.dev/"
    assert result["scope"]["options"]["fullstack"]["learn_more_url"] is None


def test_empty_constraints_works():
    with patch("pipeline.option_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_OPTION_RESULT)
        result = get_all_option_advice("A todo app", {}, FAKE_RECOMMENDED)
    assert "scope" in result


def test_empty_recommended_uses_unknown():
    with patch("pipeline.option_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_OPTION_RESULT)
        result = get_all_option_advice("A todo app", FAKE_CONSTRAINTS, {})
    assert result["scope"]["recommended"] == ""
