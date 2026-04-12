from pipeline.backend_prd_gen import generate_backend_prd
from pipeline.frontend_prd_gen import generate_frontend_prd
from pipeline.prd_contract import (
    backend_required_from_api_contract,
    extract_api_contract_block,
    extract_core_entities_block,
    extract_system_contract_section,
    parse_frontend_required,
)


def decompose_prds(main_prd: str, normalized: dict, architecture: dict) -> dict:
    contract_section = extract_system_contract_section(main_prd)

    try:
        frontend_required = parse_frontend_required(contract_section)
    except ValueError:
        stack = (normalized or {}).get("selected_stack") or {}
        frontend_required = (stack.get("frontend") or "none") != "none"

    core_entities_markdown = extract_core_entities_block(contract_section)
    api_contract = extract_api_contract_block(contract_section)
    api_contract_markdown = api_contract.get("markdown") or ""

    try:
        backend_required = backend_required_from_api_contract(api_contract)
    except ValueError:
        stack = (normalized or {}).get("selected_stack") or {}
        backend_required = (stack.get("backend") or "none") != "none"

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

