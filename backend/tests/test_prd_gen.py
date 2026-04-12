import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PYTEST_RUNNING", "1")

from pipeline.prd_gen import generate_prd

FAKE_NORMALIZED = {
    "system_name": "TeamTask",
    "purpose": "Lets remote teams track tasks.",
    "core_features": ["Create tasks", "Assign tasks"],
    "user_types": ["admin", "member"],
    "constraints": ["FastAPI"],
    "assumptions": ["Assuming single-user load"],
    "unknowns": ["Latency expectations unspecified"],
    "input_output": ["Step 1: User submits task → API stores it"],
    "data_model": ["Task: id, title"],
    "selected_stack": {"scope": "fullstack", "backend": "fastapi", "frontend": "react", "apis": [], "database": "none"},
}

FAKE_ARCHITECTURE = {
    "components": [{"name": "Task API", "responsibility": "CRUD for tasks"}],
    "data_flow": ["Step 1: User creates task → stored in DB"],
    "dependencies": ["Task API uses DB"],
    "risks": ["No rate limiting on API"],
}


def test_generate_prd_returns_string():
    result = generate_prd(FAKE_NORMALIZED, FAKE_ARCHITECTURE)
    assert isinstance(result, str)
    assert len(result) > 100


def test_generate_prd_contains_required_sections():
    result = generate_prd(FAKE_NORMALIZED, FAKE_ARCHITECTURE)
    required = [
        "## Overview",
        "## System Contract (Source of Truth)",
        "### 1. Core Entities",
        "### 2. API Contract",
        "### 3. Data Flow",
        "### 4. Frontend / Backend Boundary",
        "### 5. State Model (lightweight)",
        "## Architecture",
        "## Components",
        "## API Usage",
        "## Database Design",
        "## Test Cases",
        "## Implementation Notes for Build Agents",
    ]
    for section in required:
        assert section in result

    assert "frontend_required: true" in result

    # Ensure predictable ordering for downstream parsing.
    ordered = [
        "## Overview",
        "## System Contract (Source of Truth)",
        "## Architecture",
        "## Components",
        "## API Usage",
        "## Database Design",
        "## Test Cases",
        "## Implementation Notes for Build Agents",
    ]
    positions = [result.find(h) for h in ordered]
    assert all(p >= 0 for p in positions)
    assert positions == sorted(positions)
