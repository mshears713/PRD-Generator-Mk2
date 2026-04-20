import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PYTEST_RUNNING", "1")

from pipeline.prd_gen import generate_prd

FAKE_NORMALIZED_FULLSTACK = {
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

FAKE_NORMALIZED_BACKEND_ONLY = {
    "system_name": "RepoValidator",
    "purpose": "Validates repository structure against rules.",
    "core_features": ["Validate repo", "Report violations"],
    "user_types": ["developer"],
    "constraints": ["FastAPI"],
    "assumptions": ["CLI-driven, no UI"],
    "unknowns": [],
    "input_output": ["Step 1: CLI submits repo path → API returns report"],
    "data_model": ["Report: violations, warnings"],
    "selected_stack": {"scope": "backend", "backend": "fastapi", "frontend": "none", "apis": [], "database": "none"},
}

FAKE_ARCHITECTURE = {
    "components": [{"name": "Task API", "responsibility": "CRUD for tasks"}],
    "data_flow": ["Step 1: User creates task → stored in DB"],
    "dependencies": ["Task API uses DB"],
    "risks": ["No rate limiting on API"],
}


def test_generate_prd_returns_string():
    result = generate_prd(FAKE_NORMALIZED_FULLSTACK, FAKE_ARCHITECTURE)
    assert isinstance(result, str)
    assert len(result) > 100


def test_generate_prd_contains_required_sections():
    result = generate_prd(FAKE_NORMALIZED_FULLSTACK, FAKE_ARCHITECTURE)
    required = [
        "## Overview",
        "## System Contract (Source of Truth)",
        "## Architecture",
        "## Components",
        "## Test Cases",
    ]
    for section in required:
        assert section in result, f"Missing required section: {section}"


def test_generate_prd_frontend_required_line_always_present():
    result = generate_prd(FAKE_NORMALIZED_FULLSTACK, FAKE_ARCHITECTURE)
    assert "frontend_required:" in result


def test_generate_prd_frontend_required_true_for_fullstack():
    result = generate_prd(FAKE_NORMALIZED_FULLSTACK, FAKE_ARCHITECTURE)
    assert "frontend_required: true" in result


def test_generate_prd_no_frontend_sections_when_frontend_none():
    result = generate_prd(FAKE_NORMALIZED_BACKEND_ONLY, FAKE_ARCHITECTURE)
    assert "frontend_required: false" in result
    # No standalone frontend section header should appear.
    assert "## Frontend" not in result


def test_generate_prd_legacy_sections_not_required():
    result = generate_prd(FAKE_NORMALIZED_FULLSTACK, FAKE_ARCHITECTURE)
    # These sections were part of the old rigid template and should no longer be required.
    legacy_required = [
        "### 4. Frontend / Backend Boundary",
        "### 5. State Model",
        "## API Usage",
        "## Database Design",
        "## Implementation Notes for Build Agents",
    ]
    # Any of these may or may not appear; the test simply confirms the suite
    # no longer hard-requires them (this test always passes — it documents intent).
    _ = legacy_required  # presence is optional; test documents the contract change
    assert True
