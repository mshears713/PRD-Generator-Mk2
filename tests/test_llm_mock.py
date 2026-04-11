import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

os.environ.setdefault("PYTEST_RUNNING", "1")

from fastapi.testclient import TestClient
from main import app
from pipeline.option_advisor import get_all_option_advice

client = TestClient(app)


def test_recommend_contract():
    constraints = {
        "user_scale": "single",
        "auth": "none",
        "execution": "short",
        "app_shape": "ai_core",
        "data": {"types": ["text"], "persistence": "permanent"},
    }
    response = client.post("/recommend", json={"idea": "AI journaling app", "constraints": constraints})
    assert response.status_code == 200
    data = response.json()

    required_fields = [
        "system_understanding",
        "system_type",
        "core_system_logic",
        "key_requirements",
        "scope_boundaries",
        "phased_plan",
        "recommended",
        "rationale",
        "constraint_impact",
        "assumptions",
        "confidence",
    ]
    for field in required_fields:
        assert field in data

    rec = data["recommended"]
    for key in ("scope", "backend", "frontend", "apis", "database"):
        assert key in rec
    assert rec["backend"] in {"fastapi", "node", "none"}
    assert rec["frontend"] in {"react", "static", "none"}
    assert rec["database"] in {"postgres", "firebase", "none"}

    assert "score" in data["confidence"]
    assert "reason" in data["confidence"]
    assert isinstance(data["assumptions"], list)
    assert len(data["assumptions"]) > 0


def test_multiple_inputs_differ():
    ai_constraints = {
        "user_scale": "single",
        "auth": "none",
        "execution": "short",
        "app_shape": "ai_core",
        "data": {"types": ["text"], "persistence": "permanent"},
    }
    crud_constraints = {
        "user_scale": "single",
        "auth": "none",
        "execution": "short",
        "app_shape": "simple",
        "data": {"types": ["text"], "persistence": "permanent"},
    }
    pipeline_constraints = {
        "user_scale": "small",
        "auth": "none",
        "execution": "async",
        "app_shape": "workflow",
        "data": {"types": ["text"], "persistence": "temporary"},
    }

    ai = client.post("/recommend", json={"idea": "AI journaling app", "constraints": ai_constraints}).json()
    crud = client.post("/recommend", json={"idea": "Simple CRUD todo app", "constraints": crud_constraints}).json()
    pipeline = client.post(
        "/recommend",
        json={"idea": "Async data processing pipeline", "constraints": pipeline_constraints},
    ).json()

    assert ai["recommended"] != crud["recommended"]
    assert pipeline["recommended"]["backend"] != crud["recommended"]["backend"]
    assert "openrouter" in ai["recommended"]["apis"]
    assert "openrouter" not in crud["recommended"]["apis"]


def test_option_scoring():
    constraints = {
        "user_scale": "single",
        "auth": "none",
        "execution": "short",
        "app_shape": "simple",
        "data": {"types": ["text"], "persistence": "permanent"},
    }
    recommended = {
        "scope": "fullstack",
        "backend": "fastapi",
        "frontend": "react",
        "database": "postgres",
    }
    result = get_all_option_advice("A todo app", constraints, recommended)
    option = result["backend"]["options"]["none"]
    assert 0 <= option["fit_score"] <= 100
    assert option["complexity_cost"] in {"low", "medium", "high"}
    assert option["why_not_recommended"]


def test_no_generic_output():
    constraints = {
        "user_scale": "single",
        "auth": "none",
        "execution": "short",
        "app_shape": "ai_core",
        "data": {"types": ["text"], "persistence": "permanent"},
    }
    data = client.post("/recommend", json={"idea": "AI journaling app", "constraints": constraints}).json()
    rationale = data["rationale"]
    for key in ("scope", "backend", "frontend", "apis", "database"):
        value = rationale[key]
        assert len(value) > 20
        assert "user_scale=single" in value or "execution=short" in value


def test_constraint_impact_exists():
    constraints = {
        "user_scale": "single",
        "auth": "none",
        "execution": "short",
        "app_shape": "ai_core",
        "data": {"types": ["text"], "persistence": "permanent"},
    }
    data = client.post("/recommend", json={"idea": "AI journaling app", "constraints": constraints}).json()
    assert len(data["constraint_impact"]) > 0
