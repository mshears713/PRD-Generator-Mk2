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


def test_recommend_accepts_answers_payload():
    payload = {
        "idea": "A scheduled report exporter",
        "answers": {
            "fixed_answers": {
                "for_whom": "small",
                "accounts": "none",
                "remember_over_time": "temporary",
                "reliability_vs_speed": "reliable",
            },
            "dynamic_answers": {
                "output_type": "file_export",
                "automation_level": "scheduled",
            },
        },
    }
    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recommended" in data
    assert "api_candidates" in data


def test_quick_setup_questions_returns_two_questions():
    response = client.post("/quick-setup/questions", json={"idea": "A Slack bot that exports reports as PDF"})
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert len(data["questions"]) == 2


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
