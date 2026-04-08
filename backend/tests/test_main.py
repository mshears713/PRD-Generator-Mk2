import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["OPENAI_API_KEY"] = "test-key"

from unittest.mock import patch
from fastapi.testclient import TestClient


FAKE_RECOMMENDATION = {
    "summary": "A task manager for remote teams.",
    "recommended": {
        "scope": "fullstack",
        "backend": "fastapi",
        "frontend": "react",
        "apis": [],
        "database": "postgres",
    },
}

GENERATE_PAYLOAD = {
    "idea": "A task manager for remote teams",
    "scope": "fullstack",
    "backend": "fastapi",
    "frontend": "react",
    "apis": ["openrouter"],
    "database": "postgres",
    "api_keys": {"openrouter": "sk-test"},
}


def get_client():
    from main import app
    return TestClient(app)


def test_recommend_returns_200():
    with patch("main.get_recommendation", return_value=FAKE_RECOMMENDATION):
        client = get_client()
        response = client.post("/recommend", json={"idea": "A task manager"})
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "recommended" in data


def test_generate_returns_200():
    with (
        patch("main.normalize", return_value={"system_name": "TeamTask", "purpose": "test"}),
        patch("main.analyze", return_value={"components": [], "data_flow": [], "dependencies": [], "risks": []}),
        patch("main.generate_prd", return_value="# PRD\n## Overview\ntest\n## Architecture\nx\n## Components\nx\n## API Usage\nx\n## Database Design\nx\n## Test Cases\nx"),
        patch("main.generate_growth_check", return_value="## Growth Check\n✅ good\n⚠️ warn\n❌ missing"),
    ):
        client = get_client()
        response = client.post("/generate", json=GENERATE_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert "prd" in data
    assert "env" in data
    assert "growth_check" in data


def test_generate_env_contains_openrouter_key():
    with (
        patch("main.normalize", return_value={}),
        patch("main.analyze", return_value={}),
        patch("main.generate_prd", return_value="# PRD"),
        patch("main.generate_growth_check", return_value="## Growth Check\n✅ good"),
    ):
        client = get_client()
        response = client.post("/generate", json=GENERATE_PAYLOAD)
    assert "OPENROUTER_API_KEY=sk-test" in response.json()["env"]


def test_recommend_missing_openai_key_returns_500():
    with patch("main.os.getenv", return_value=None):
        client = get_client()
        response = client.post("/recommend", json={"idea": "test"})
    assert response.status_code == 500


def test_generate_missing_openai_key_returns_500():
    with patch("main.os.getenv", return_value=None):
        client = get_client()
        response = client.post("/generate", json=GENERATE_PAYLOAD)
    assert response.status_code == 500
