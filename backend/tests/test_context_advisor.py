import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from unittest.mock import patch, MagicMock
from pipeline.context_advisor import get_context_advice

FAKE_RECOMMENDED = {
    "scope": "fullstack",
    "backend": "fastapi",
    "frontend": "react",
    "database": "postgres",
    "apis": [],
}

FAKE_CONSTRAINTS = {
    "user_scale": "single",
    "auth": "none",
    "execution": "short",
    "app_shape": "ai_core",
    "data": {"types": ["text"], "persistence": "permanent"},
}

FAKE_ADVICE = {
    "architecture": {
        "scope": {
            "choice": "fullstack",
            "reason_for_recommendation": "Your AI tool needs both a UI layer and a backend for Python AI processing.",
            "benefits": [
                "Keeps AI logic server-side where Python libraries are available",
                "Clean separation between result display and processing",
            ],
            "drawbacks": ["Two deployment targets to manage"],
        },
        "backend": {
            "choice": "fastapi",
            "reason_for_recommendation": "FastAPI's async support suits non-blocking AI API calls for a single user.",
            "benefits": [
                "Native async lets AI calls run without blocking the response",
                "Direct access to Python ML and AI libraries",
            ],
            "drawbacks": ["Not the best choice if real-time WebSocket streaming is added later"],
        },
        "frontend": {
            "choice": "react",
            "reason_for_recommendation": "React handles the interactive result display your single-user tool needs.",
            "benefits": [
                "Easy to build dynamic, stateful result views",
                "Component model maps cleanly to your tool's steps",
            ],
            "drawbacks": ["Bundle overhead is minor for a single-user tool but still present"],
        },
        "database": {
            "choice": "postgres",
            "reason_for_recommendation": "PostgreSQL handles persistent text results reliably for long-term access.",
            "benefits": [
                "Reliable long-term storage for saved AI outputs",
                "Easy to query and filter history by date or type",
            ],
            "drawbacks": ["Schema migrations required as output structure evolves"],
        },
    },
    "deployment": [
        {
            "name": "Render",
            "value": "render",
            "recommended": True,
            "reason_for_recommendation": "Single-user tool gets full value from Render's fast iteration cycle and free tier.",
            "benefits": [
                "Auto-deploy on push means you ship faster during development",
                "Free tier comfortably handles single-user load",
            ],
            "drawbacks": ["Cold starts after inactivity may delay the first request"],
            "sponsored": True,
            "sponsor_info": {
                "why_use": [
                    "Zero-config FastAPI deployment with automatic builds",
                    "Managed PostgreSQL available on the same platform",
                ],
                "bonus": "Free tier + simple scaling",
            },
        },
        {
            "name": "AWS",
            "value": "aws",
            "recommended": False,
            "reason_for_recommendation": "Overkill for a single-user AI tool at this stage — setup cost outweighs benefit.",
            "benefits": ["Can scale to large audiences if the tool grows"],
            "drawbacks": [
                "Configuration overhead significantly slows down early development",
                "Cost complexity for a single-user prototype",
            ],
            "sponsored": False,
        },
        {
            "name": "Self-hosted",
            "value": "self",
            "recommended": False,
            "reason_for_recommendation": "Viable if you have a VPS and want zero cold starts, but adds maintenance burden.",
            "benefits": ["No cold starts", "Full control over environment and cost"],
            "drawbacks": [
                "Manual SSL, process management, and backups",
                "Slower to set up than Render for a first deployment",
            ],
            "sponsored": False,
        },
    ],
}


def make_openai_response(content: dict):
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps(content)
    return mock


def test_returns_architecture_and_deployment():
    with patch("pipeline.context_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ADVICE)
        result = get_context_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    assert "architecture" in result
    assert "deployment" in result


def test_architecture_has_all_stack_keys():
    with patch("pipeline.context_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ADVICE)
        result = get_context_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    arch = result["architecture"]
    for key in ("scope", "backend", "frontend", "database"):
        assert key in arch, f"architecture missing key: {key}"
        assert "benefits" in arch[key], f"{key} missing benefits"
        assert "drawbacks" in arch[key], f"{key} missing drawbacks"
        assert isinstance(arch[key]["benefits"], list)
        assert isinstance(arch[key]["drawbacks"], list)


def test_architecture_has_reason_for_recommendation():
    with patch("pipeline.context_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ADVICE)
        result = get_context_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    for key in ("scope", "backend", "frontend", "database"):
        assert "reason_for_recommendation" in result["architecture"][key]
        assert len(result["architecture"][key]["reason_for_recommendation"]) > 0


def test_deployment_has_three_options():
    with patch("pipeline.context_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ADVICE)
        result = get_context_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    assert len(result["deployment"]) == 3


def test_exactly_one_deployment_recommended():
    with patch("pipeline.context_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ADVICE)
        result = get_context_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    recommended = [d for d in result["deployment"] if d.get("recommended")]
    assert len(recommended) == 1


def test_deployment_values_are_correct():
    with patch("pipeline.context_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ADVICE)
        result = get_context_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    values = {d["value"] for d in result["deployment"]}
    assert values == {"render", "aws", "self"}


def test_sponsored_option_has_sponsor_info():
    with patch("pipeline.context_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ADVICE)
        result = get_context_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    sponsored = [d for d in result["deployment"] if d.get("sponsored")]
    assert len(sponsored) >= 1
    for s in sponsored:
        assert "sponsor_info" in s
        assert "why_use" in s["sponsor_info"]
        assert isinstance(s["sponsor_info"]["why_use"], list)
        assert "bonus" in s["sponsor_info"]


def test_each_deployment_has_required_fields():
    with patch("pipeline.context_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ADVICE)
        result = get_context_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    for opt in result["deployment"]:
        for field in ("name", "value", "recommended", "benefits", "drawbacks", "reason_for_recommendation"):
            assert field in opt, f"deployment option missing field: {field}"


def test_empty_constraints_works():
    with patch("pipeline.context_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ADVICE)
        result = get_context_advice("anything", {}, FAKE_RECOMMENDED)
    assert "architecture" in result


def test_empty_recommended_works():
    with patch("pipeline.context_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ADVICE)
        result = get_context_advice("anything", FAKE_CONSTRAINTS, {})
    assert "deployment" in result


def test_architecture_has_learn_more_urls():
    with patch("pipeline.context_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ADVICE)
        result = get_context_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    arch = result["architecture"]
    assert arch["backend"]["learn_more_url"] == "https://fastapi.tiangolo.com/"
    assert arch["frontend"]["learn_more_url"] == "https://react.dev/"
    assert arch["database"]["learn_more_url"] == "https://www.postgresql.org/docs/"
    assert arch["scope"]["learn_more_url"] is None


def test_deployment_has_learn_more_urls():
    with patch("pipeline.context_advisor.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_ADVICE)
        result = get_context_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    dep_map = {d["value"]: d for d in result["deployment"]}
    assert dep_map["render"]["learn_more_url"] == "https://render.com/docs"
    assert dep_map["aws"]["learn_more_url"] == "https://docs.aws.amazon.com/"
    assert dep_map["self"]["learn_more_url"] is None
