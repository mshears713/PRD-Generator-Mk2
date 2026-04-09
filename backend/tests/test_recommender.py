import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from pipeline.recommender import get_recommendation

os.environ.setdefault("OPENAI_API_KEY", "test-key")

FAKE_RESPONSE = {
    "system_understanding": "A task management platform where remote teams create, assign, and track tasks in real time. Data flows from the React frontend through a FastAPI backend, where it is validated and written to PostgreSQL. All operations are synchronous and results are immediately visible to the requesting user. Task records are stored persistently and queryable across sessions.",
    "system_type": "CRUD web app",
    "core_system_logic": "Users create tasks, assign them to teammates, and track status changes stored in a relational database.",
    "key_requirements": [
        "User authentication and team workspaces",
        "Real-time task updates",
        "Persistent task storage",
    ],
    "scope_boundaries": ["Single-user tool only", "No real-time collaboration", "Text input/output only"],
    "phased_plan": [
        "Phase 1: Core — task creation, assignment, and status board",
        "Phase 2: Team accounts and workspace isolation",
        "Phase 3: Notifications and activity feed",
    ],
    "recommended": {
        "scope": "fullstack",
        "backend": "fastapi",
        "frontend": "react",
        "apis": [],
        "database": "postgres",
    },
    "rationale": {
        "scope": "fullstack — both a UI and an API layer are needed",
        "backend": "FastAPI handles async updates and is easy to prototype with",
        "frontend": "React's component model suits a dynamic task board with live updates",
        "apis": "No external APIs required; all data is internal",
        "database": "PostgreSQL suits structured relational task/user data",
    },
}


def make_openai_response(content: dict):
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps(content)
    return mock


def test_returns_system_understanding_and_recommended():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("A task manager for remote teams")
    assert "system_understanding" in result
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


def test_system_understanding_is_nonempty_string():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("anything")
    assert isinstance(result["system_understanding"], str)
    assert len(result["system_understanding"]) > 0


def test_returns_system_type():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("anything")
    assert "system_type" in result
    assert isinstance(result["system_type"], str)
    assert len(result["system_type"]) > 0


def test_returns_key_requirements_as_list():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("anything")
    assert "key_requirements" in result
    assert isinstance(result["key_requirements"], list)
    assert len(result["key_requirements"]) >= 1


def test_returns_rationale_with_required_keys():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("anything")
    assert "rationale" in result
    rat = result["rationale"]
    for key in ("scope", "backend", "frontend", "apis", "database"):
        assert key in rat, f"rationale missing key: {key}"
        assert isinstance(rat[key], str)


def test_returns_core_system_logic():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("anything")
    assert "core_system_logic" in result
    assert isinstance(result["core_system_logic"], str)
    assert len(result["core_system_logic"]) > 0


def test_returns_scope_boundaries():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("anything")
    assert "scope_boundaries" in result
    assert isinstance(result["scope_boundaries"], list)
    assert len(result["scope_boundaries"]) > 0


def test_returns_phased_plan_as_list():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("anything")
    assert "phased_plan" in result
    assert isinstance(result["phased_plan"], list)
    assert len(result["phased_plan"]) >= 1


def test_constraints_are_injected_into_prompt():
    """Verify constraints appear in the user message sent to the LLM."""
    constraints = {
        "user_scale": "single",
        "auth": "none",
        "execution": "async",
        "app_shape": "workflow",
        "data": {"types": ["text"], "persistence": "permanent"},
    }
    with patch("pipeline.recommender.OpenAI") as MockClient:
        mock_create = MockClient.return_value.chat.completions.create
        mock_create.return_value = make_openai_response(FAKE_RESPONSE)
        get_recommendation("a workflow tool", constraints)
    call_kwargs = mock_create.call_args
    messages = call_kwargs[1]["messages"] if call_kwargs[1] else call_kwargs[0][0]
    # find the user message
    user_msg = next(m["content"] for m in messages if m["role"] == "user")
    assert "Single user only" in user_msg
    assert "No authentication" in user_msg
    assert "Background/async" in user_msg


def test_empty_constraints_still_works():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("anything", {})
    assert "system_understanding" in result


def test_none_constraints_still_works():
    with patch("pipeline.recommender.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_RESPONSE)
        result = get_recommendation("anything", None)
    assert "system_understanding" in result
