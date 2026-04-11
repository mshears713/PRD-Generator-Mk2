import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PYTEST_RUNNING", "1")

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


def test_returns_architecture_and_deployment():
    result = get_context_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    assert "architecture" in result
    assert "deployment" in result


def test_architecture_has_all_stack_keys():
    result = get_context_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    arch = result["architecture"]
    for key in ("scope", "backend", "frontend", "database"):
        assert key in arch
        assert "benefits" in arch[key]
        assert "drawbacks" in arch[key]
        assert isinstance(arch[key]["benefits"], list)
        assert isinstance(arch[key]["drawbacks"], list)


def test_deployment_has_three_options_and_one_recommended():
    result = get_context_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    assert len(result["deployment"]) == 3
    recommended = [d for d in result["deployment"] if d.get("recommended")]
    assert len(recommended) == 1


def test_architecture_has_learn_more_urls():
    result = get_context_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    arch = result["architecture"]
    assert arch["backend"]["learn_more_url"] == "https://fastapi.tiangolo.com/"
    assert arch["frontend"]["learn_more_url"] == "https://react.dev/"
    assert arch["database"]["learn_more_url"] == "https://www.postgresql.org/docs/"
    assert arch["scope"]["learn_more_url"] is None


def test_deployment_has_learn_more_urls():
    result = get_context_advice("An AI writing tool", FAKE_CONSTRAINTS, FAKE_RECOMMENDED)
    dep_map = {d["value"]: d for d in result["deployment"]}
    assert dep_map["render"]["learn_more_url"] == "https://render.com/docs"
    assert dep_map["aws"]["learn_more_url"] == "https://docs.aws.amazon.com/"
    assert dep_map["self"]["learn_more_url"] is None
