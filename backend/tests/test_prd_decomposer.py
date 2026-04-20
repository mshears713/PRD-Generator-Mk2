import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PYTEST_RUNNING", "1")

import pytest

from pipeline.prd_decomposer import decompose_prds
from pipeline.prd_gen import generate_prd


def _normalized_with_stack(*, frontend: str, backend: str) -> dict:
    return {
        "system_name": "TeamTask",
        "purpose": "Lets remote teams track tasks.",
        "core_features": ["Create tasks", "Assign tasks"],
        "user_types": ["admin", "member"],
        "constraints": [],
        "assumptions": [],
        "unknowns": [],
        "input_output": [],
        "data_model": [],
        "selected_stack": {"scope": "fullstack", "backend": backend, "frontend": frontend, "apis": [], "database": "none"},
    }


FAKE_ARCHITECTURE = {
    "components": [{"name": "Task API", "responsibility": "CRUD for tasks"}],
    "data_flow": ["Step 1: User creates task → stored in DB"],
    "dependencies": ["Task API uses DB"],
    "risks": ["No rate limiting on API"],
}


# ---------------------------------------------------------------------------
# Case A — Fullstack: both sub-PRDs generated
# ---------------------------------------------------------------------------

def test_decompose_prds_generates_backend_and_frontend_when_required():
    normalized = _normalized_with_stack(frontend="react", backend="fastapi")
    main_prd = generate_prd(normalized, FAKE_ARCHITECTURE)

    decomposed = decompose_prds(main_prd, normalized, FAKE_ARCHITECTURE)
    assert decomposed["backend_prd"]
    assert decomposed["frontend_prd"]

    # Placeholders must be fully replaced — no raw template tokens remain.
    for doc in (decomposed["backend_prd"], decomposed["frontend_prd"]):
        assert "{{STACKLENS_CORE_ENTITIES}}" not in doc
        assert "{{STACKLENS_API_CONTRACT}}" not in doc


# ---------------------------------------------------------------------------
# Case B — Backend-only: only backend PRD generated
# ---------------------------------------------------------------------------

def test_decompose_prds_omits_frontend_prd_when_frontend_required_false():
    normalized = _normalized_with_stack(frontend="none", backend="fastapi")
    main_prd = generate_prd(normalized, FAKE_ARCHITECTURE)

    decomposed = decompose_prds(main_prd, normalized, FAKE_ARCHITECTURE)
    assert decomposed["backend_prd"]
    assert decomposed["frontend_prd"] is None


# ---------------------------------------------------------------------------
# Case C — Frontend-only (no backend API): only frontend PRD generated
# ---------------------------------------------------------------------------

def test_decompose_prds_omits_backend_prd_when_no_backend_api_required():
    normalized = _normalized_with_stack(frontend="react", backend="none")
    main_prd = generate_prd(normalized, FAKE_ARCHITECTURE)

    decomposed = decompose_prds(main_prd, normalized, FAKE_ARCHITECTURE)
    assert decomposed["backend_prd"] is None
    assert decomposed["frontend_prd"]
    assert "No backend API required." in decomposed["frontend_prd"]


# ---------------------------------------------------------------------------
# Case D — Minimal contract only (no optional subsections)
# ---------------------------------------------------------------------------

_MINIMAL_PRD = (
    "# Minimal System PRD\n\n"
    "## Overview\n"
    "A backend-only CLI tool with no frontend.\n\n"
    "## System Contract (Source of Truth)\n"
    "- frontend_required: false\n\n"
    "## Architecture\n"
    "Single-process CLI.\n\n"
    "## Components\n"
    "- CLI Runner\n\n"
    "## Test Cases\n"
    "- Smoke test\n"
)

_NORMALIZED_BACKEND = _normalized_with_stack(frontend="none", backend="fastapi")


def test_decompose_prds_minimal_contract_uses_stack_fallback():
    """Decomposition must succeed even when optional subsections are absent."""
    decomposed = decompose_prds(_MINIMAL_PRD, _NORMALIZED_BACKEND, FAKE_ARCHITECTURE)
    # backend is required per stack fallback (fastapi != none), frontend is not required
    assert decomposed["backend_prd"] is not None
    assert decomposed["frontend_prd"] is None


def test_decompose_prds_minimal_contract_no_placeholders_remain():
    decomposed = decompose_prds(_MINIMAL_PRD, _NORMALIZED_BACKEND, FAKE_ARCHITECTURE)
    doc = decomposed["backend_prd"]
    assert "{{STACKLENS_CORE_ENTITIES}}" not in doc
    assert "{{STACKLENS_API_CONTRACT}}" not in doc


# ---------------------------------------------------------------------------
# Case E — Missing System Contract: hard fail with clear error
# ---------------------------------------------------------------------------

_PRD_WITHOUT_CONTRACT = (
    "# Broken PRD\n\n"
    "## Overview\n"
    "This PRD has no System Contract section.\n\n"
    "## Architecture\n"
    "...\n"
)


def test_decompose_prds_raises_when_system_contract_missing():
    with pytest.raises(ValueError, match="System Contract"):
        decompose_prds(_PRD_WITHOUT_CONTRACT, _NORMALIZED_BACKEND, FAKE_ARCHITECTURE)
