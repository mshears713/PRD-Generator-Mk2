import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.prd_quality import check_prd_quality


GOOD_MAIN_PRD = """
# System PRD

## Overview
When the user submits a request, the system processes it and returns a result.

## System Contract
- frontend_required: true

## Data Flow
Step 1: User submits input via the frontend.
Step 2: API layer validates and routes the request.
Step 3: Core service transforms the payload.

## Components
### API Layer
Receives HTTP requests from clients and returns JSON responses.

### Core Service
Processes the validated input and returns structured output.

## Out of Scope
- Multi-tenant support
- Advanced analytics
"""

GOOD_BACKEND_PRD = """
# System Backend PRD

## Purpose
Implement the backend API.

## Responsibilities
- Accept input payloads and return processed results.

## Architecture
- API layer receives requests (Input: JSON body) and returns responses (Output: JSON).
- Core service executes the main workflow (Processing: validates and transforms input).

## Implementation Phases
### Phase 1 — Backend skeleton and contracts
- Scaffold FastAPI app; POST /generate returns 200 with empty result.

### Phase 2 — Core request flow and business logic
- Wire core service; POST /generate returns 200 with {result: string}.
"""


def test_passes_with_sufficient_prd():
    result = check_prd_quality(GOOD_MAIN_PRD, GOOD_BACKEND_PRD)
    assert result["passed"] is True
    assert result["warnings"] == []
    assert "passed" in result["summary"].lower()


_NO_TRIGGER_MAIN_PRD = """
# System PRD

## Overview
The system processes payloads and returns results.

## System Contract
- frontend_required: true

## Data Flow
Step 1: The API layer receives the payload.
Step 2: Core service transforms the payload.

## Components
### API Layer
Handles HTTP requests and returns JSON responses.

## Out of Scope
- Multi-tenant support
"""


def test_warns_on_missing_trigger():
    result = check_prd_quality(_NO_TRIGGER_MAIN_PRD, GOOD_BACKEND_PRD)
    trigger_warnings = [w for w in result["warnings"] if "trigger" in w.lower()]
    assert len(trigger_warnings) == 1


def test_warns_on_missing_flow():
    prd = "\n".join(
        line for line in GOOD_MAIN_PRD.splitlines()
        if not line.strip().lower().startswith("step")
        and "flow" not in line.lower()
        and "data flow" not in line.lower()
    )
    result = check_prd_quality(prd, GOOD_BACKEND_PRD)
    flow_warnings = [w for w in result["warnings"] if "flow" in w.lower()]
    assert len(flow_warnings) == 1


def test_warns_on_missing_constraints():
    prd = GOOD_MAIN_PRD.replace("## Out of Scope\n- Multi-tenant support\n- Advanced analytics", "")
    result = check_prd_quality(prd, GOOD_BACKEND_PRD)
    constraint_warnings = [w for w in result["warnings"] if "constraint" in w.lower() or "scope" in w.lower()]
    assert len(constraint_warnings) == 1


def test_warns_on_shallow_backend_prd():
    shallow = "# System Backend PRD\n## Purpose\nDo stuff.\n"
    result = check_prd_quality(GOOD_MAIN_PRD, shallow)
    assert not result["passed"]
    assert len(result["warnings"]) >= 2  # missing IO, processing, phases


def test_no_backend_prd_skips_backend_checks():
    result = check_prd_quality(GOOD_MAIN_PRD, None)
    backend_warnings = [w for w in result["warnings"] if "backend" in w.lower()]
    assert backend_warnings == []


def test_returns_expected_shape():
    result = check_prd_quality(GOOD_MAIN_PRD, GOOD_BACKEND_PRD)
    assert "passed" in result
    assert "warnings" in result
    assert "summary" in result
    assert isinstance(result["passed"], bool)
    assert isinstance(result["warnings"], list)
    assert isinstance(result["summary"], str)
