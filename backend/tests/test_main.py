import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["OPENAI_API_KEY"] = "test-key"

from unittest.mock import patch
from fastapi.testclient import TestClient


FAKE_RECOMMENDATION = {
    "system_understanding": "A task manager for remote teams.",
    "recommended": {
        "scope": "fullstack",
        "backend": "fastapi",
        "frontend": "react",
        "apis": [],
        "database": "postgres",
    },
    "confidence": 0.85,
}

FAKE_ADVICE = {
    "architecture": {
        "scope": {"choice": "fullstack", "reason_for_recommendation": "test", "benefits": [], "drawbacks": []},
        "backend": {"choice": "fastapi", "reason_for_recommendation": "test", "benefits": [], "drawbacks": []},
        "frontend": {"choice": "react", "reason_for_recommendation": "test", "benefits": [], "drawbacks": []},
        "database": {"choice": "postgres", "reason_for_recommendation": "test", "benefits": [], "drawbacks": []},
    },
    "deployment": [
        {"name": "Render", "value": "render", "recommended": True, "benefits": [], "drawbacks": [], "sponsored": True,
         "sponsor_info": {"why_use": [], "bonus": ""}},
        {"name": "AWS", "value": "aws", "recommended": False, "benefits": [], "drawbacks": [], "sponsored": False},
        {"name": "Self-hosted", "value": "self", "recommended": False, "benefits": [], "drawbacks": [], "sponsored": False},
    ],
}

FAKE_OPTION_ADVICE = {
    "scope": {
        "recommended": "fullstack",
        "options": {
            "frontend": {"fit_score": 75, "relevant": False, "reason": "No UI needed.", "benefits": ["Simple"], "drawbacks": ["No interface"], "learn_more_url": None},
            "backend":  {"fit_score": 75, "relevant": True,  "reason": "API only.",    "benefits": ["Clean API"], "drawbacks": ["No UI"],       "learn_more_url": None},
            "fullstack":{"fit_score": 75, "relevant": True,  "reason": "Full control.","benefits": ["End-to-end"],"drawbacks": ["More work"],   "learn_more_url": None},
        },
    },
    "backend": {
        "recommended": "fastapi",
        "options": {
            "fastapi": {"fit_score": 75, "relevant": True,  "reason": "Python fits.", "benefits": ["Async"], "drawbacks": ["GIL"],          "learn_more_url": "https://fastapi.tiangolo.com/"},
            "node":    {"fit_score": 75, "relevant": True,  "reason": "Alternative.", "benefits": ["npm"],   "drawbacks": ["Less Python"],  "learn_more_url": "https://nodejs.org/en/docs"},
            "none":    {"fit_score": 75, "relevant": False, "reason": "Needs server.","benefits": ["Simple"],"drawbacks": ["No backend"],   "learn_more_url": None},
        },
    },
    "frontend": {
        "recommended": "react",
        "options": {
            "react":   {"fit_score": 75, "relevant": True,  "reason": "Rich UI.",     "benefits": ["Components"], "drawbacks": ["Bundle size"], "learn_more_url": "https://react.dev/"},
            "static":  {"fit_score": 75, "relevant": True,  "reason": "Lightweight.", "benefits": ["Fast"],       "drawbacks": ["No state"],   "learn_more_url": None},
            "none":    {"fit_score": 75, "relevant": False, "reason": "Needs UI.",    "benefits": ["Headless"],   "drawbacks": ["No UI"],      "learn_more_url": None},
        },
    },
    "database": {
        "recommended": "postgres",
        "options": {
            "postgres": {"fit_score": 75, "relevant": True,  "reason": "Reliable.",    "benefits": ["ACID"], "drawbacks": ["Migrations"], "learn_more_url": "https://www.postgresql.org/docs/"},
            "firebase": {"fit_score": 75, "relevant": False, "reason": "Overkill.",    "benefits": ["RT sync"], "drawbacks": ["Lock-in"], "learn_more_url": "https://firebase.google.com/docs"},
            "none":     {"fit_score": 75, "relevant": False, "reason": "Needs storage.","benefits": ["Simple"],  "drawbacks": ["No persist"],"learn_more_url": None},
        },
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
        with patch("main.get_context_advice", return_value=FAKE_ADVICE):
            with patch("main.get_all_option_advice", return_value=FAKE_OPTION_ADVICE):
                client = get_client()
                response = client.post("/recommend", json={"idea": "A task manager"})
    assert response.status_code == 200
    data = response.json()
    assert "system_understanding" in data
    assert "recommended" in data
    assert "architecture" in data
    assert "deployment" in data
    assert "confidence" in data


def test_generate_returns_200():
    with (
        patch("main.normalize", return_value={"system_name": "TeamTask", "purpose": "test"}),
        patch("main.analyze", return_value={"components": [], "data_flow": [], "dependencies": [], "risks": []}),
        patch("main.generate_prd", return_value="# PRD\n## Overview\ntest\n## Architecture\nx\n## Components\nx\n## API Usage\nx\n## Database Design\nx\n## Test Cases\nx"),
        patch("main.generate_growth_check", return_value={"good": [{"title": "FastAPI", "detail": "Fits well"}], "warnings": [{"title": "Cold starts", "detail": "May delay first request"}], "missing": [{"title": "Rate limiting", "detail": "Needed for external APIs"}]}),
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
        patch("main.generate_growth_check", return_value={"good": [{"title": "FastAPI", "detail": "Fits well"}], "warnings": [], "missing": []}),
    ):
        client = get_client()
        response = client.post("/generate", json=GENERATE_PAYLOAD)
    assert "OPENROUTER_API_KEY=sk-test" in response.json()["env"]


def test_recommend_returns_architecture_and_deployment():
    with patch("main.get_recommendation", return_value=FAKE_RECOMMENDATION):
        with patch("main.get_context_advice", return_value=FAKE_ADVICE):
            with patch("main.get_all_option_advice", return_value=FAKE_OPTION_ADVICE):
                client = get_client()
                response = client.post("/recommend", json={"idea": "A task manager"})
    data = response.json()
    assert "architecture" in data
    assert "deployment" in data
    assert len(data["deployment"]) == 3


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
