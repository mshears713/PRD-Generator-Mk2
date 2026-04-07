import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from unittest.mock import patch, MagicMock
from pipeline.prd_gen import generate_prd


FAKE_NORMALIZED = {
    "system_name": "TeamTask",
    "purpose": "Lets remote teams track tasks.",
    "core_features": ["Create tasks", "Assign tasks"],
    "user_types": ["admin", "member"],
    "constraints": ["FastAPI"],
    "assumptions_removed": ["vague → specific"],
}

FAKE_ARCHITECTURE = {
    "components": [{"name": "Task API", "responsibility": "CRUD for tasks"}],
    "data_flow": ["Step 1: User creates task → stored in DB"],
    "dependencies": ["Task API uses DB"],
    "risks": ["No rate limiting on API"],
}

FAKE_PRD = """# TeamTask PRD

## Overview
TeamTask helps remote teams track work.

## Architecture
FastAPI backend with React frontend.

## Components
### Task API
- **Responsibility:** CRUD operations for tasks

## API Usage
No external APIs required.

## Database Design
tasks table: id, title, assigned_to, status, created_at

## Test Cases
| Test | Input | Expected Output | Type |
|------|-------|-----------------|------|
| Create task | POST /tasks with title | 201 + task JSON | integration |
"""


def make_openai_response(content: str):
    mock = MagicMock()
    mock.choices[0].message.content = content
    return mock


def test_generate_prd_returns_string():
    with patch("pipeline.prd_gen.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_PRD)
        result = generate_prd(FAKE_NORMALIZED, FAKE_ARCHITECTURE)
    assert isinstance(result, str)
    assert len(result) > 100


def test_generate_prd_contains_required_sections():
    with patch("pipeline.prd_gen.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = make_openai_response(FAKE_PRD)
        result = generate_prd(FAKE_NORMALIZED, FAKE_ARCHITECTURE)
    for section in ["Overview", "Architecture", "Components", "Test Cases"]:
        assert section in result, f"Missing section: {section}"
