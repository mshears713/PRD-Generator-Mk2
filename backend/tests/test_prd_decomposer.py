import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PYTEST_RUNNING", "1")

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


def test_decompose_prds_generates_backend_and_frontend_when_required():
    normalized = _normalized_with_stack(frontend="react", backend="fastapi")
    main_prd = generate_prd(normalized, FAKE_ARCHITECTURE)

    decomposed = decompose_prds(main_prd, normalized, FAKE_ARCHITECTURE)
    assert decomposed["backend_prd"]
    assert decomposed["frontend_prd"]

    for doc in (decomposed["backend_prd"], decomposed["frontend_prd"]):
        assert "## Integration Contract (From Main PRD — Do Not Change Without Updating Main PRD)" in doc
        assert "## Implementation Phases" in doc
        assert "Phase 1" in doc and "Phase 4" in doc
        assert "{{STACKLENS_CORE_ENTITIES}}" not in doc
        assert "{{STACKLENS_API_CONTRACT}}" not in doc
        assert "| Method | Path |" in doc


def test_decompose_prds_omits_frontend_prd_when_frontend_required_false():
    normalized = _normalized_with_stack(frontend="none", backend="fastapi")
    main_prd = generate_prd(normalized, FAKE_ARCHITECTURE)

    decomposed = decompose_prds(main_prd, normalized, FAKE_ARCHITECTURE)
    assert decomposed["backend_prd"]
    assert decomposed["frontend_prd"] is None


def test_decompose_prds_omits_backend_prd_when_no_backend_api_required():
    normalized = _normalized_with_stack(frontend="react", backend="none")
    main_prd = generate_prd(normalized, FAKE_ARCHITECTURE)

    decomposed = decompose_prds(main_prd, normalized, FAKE_ARCHITECTURE)
    assert decomposed["backend_prd"] is None
    assert decomposed["frontend_prd"]
    assert "No backend API required." in decomposed["frontend_prd"]

