from pipeline.backend_prd_gen import generate_backend_prd
from pipeline.frontend_prd_gen import generate_frontend_prd
from pipeline.prd_contract import (
    backend_required_from_api_contract,
    parse_system_contract,
)


def decompose_prds(main_prd: str, normalized: dict, architecture: dict) -> dict:
    # Hard-fails if PRD is empty or System Contract section is missing.
    parsed = parse_system_contract(main_prd)

    frontend_required = parsed["frontend_required"]

    api_contract = parsed["api_contract"]
    if api_contract is not None:
        backend_required = backend_required_from_api_contract(api_contract)
    else:
        # No API Contract subsection — fall back to stack selection.
        stack = (normalized or {}).get("selected_stack") or {}
        backend_required = (stack.get("backend") or "none") != "none"

    # Coerce None → "" so sub-generators always receive strings.
    core_entities_markdown = parsed["core_entities_markdown"] or ""
    api_contract_markdown = (api_contract or {}).get("markdown") or ""

    backend_prd = None
    if backend_required:
        backend_prd = generate_backend_prd(
            main_prd,
            normalized,
            architecture,
            core_entities_markdown=core_entities_markdown,
            api_contract_markdown=api_contract_markdown,
        )

    frontend_prd = None
    if frontend_required:
        frontend_prd = generate_frontend_prd(
            main_prd,
            normalized,
            architecture,
            core_entities_markdown=core_entities_markdown,
            api_contract_markdown=api_contract_markdown,
        )

    return {"backend_prd": backend_prd, "frontend_prd": frontend_prd}
