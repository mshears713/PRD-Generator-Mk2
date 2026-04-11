import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PYTEST_RUNNING", "1")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_recommend_returns_200():
    response = client.post("/recommend", json={"idea": "A task manager"})
    assert response.status_code == 200
    data = response.json()
    assert "system_understanding" in data
    assert "recommended" in data
    assert "architecture" in data
    assert "deployment" in data
    assert "api_candidates" in data
    assert "confidence" in data
    assert "score" in data["confidence"]
    assert "reason" in data["confidence"]


def test_generate_returns_200():
    payload = {
        "idea": "A task manager for remote teams",
        "scope": "fullstack",
        "backend": "fastapi",
        "frontend": "react",
        "apis": ["openrouter"],
        "database": "postgres",
        "api_keys": {"openrouter": "sk-test"},
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "prd" in data
    assert "env" in data
    assert "growth_check" in data


def test_generate_env_contains_openrouter_key():
    payload = {
        "idea": "A task manager for remote teams",
        "scope": "fullstack",
        "backend": "fastapi",
        "frontend": "react",
        "apis": ["openrouter"],
        "database": "postgres",
        "api_keys": {"openrouter": "sk-test"},
    }
    response = client.post("/generate", json=payload)
    assert "OPENROUTER_API_KEY=sk-test" in response.json()["env"]
