import re


_H2_SYSTEM_CONTRACT_RE = re.compile(r"^##\s+System Contract\s+\(Source of Truth\)\s*$", re.MULTILINE)
# Match with or without a numeric prefix (e.g. "### Core Entities" or "### 1. Core Entities")
_H3_CORE_ENTITIES_RE = re.compile(r"^###\s+(?:\d+\.\s+)?Core Entities\s*$", re.MULTILINE)
_H3_API_CONTRACT_RE = re.compile(r"^###\s+(?:\d+\.\s+)?API Contract\s*$", re.MULTILINE)
_H3_DATA_FLOW_RE = re.compile(r"^###\s+(?:\d+\.\s+)?Data Flow\s*$", re.MULTILINE)
_H2_NEXT_SECTION_RE = re.compile(r"^##\s+", re.MULTILINE)
_H3_ANY_RE = re.compile(r"^###\s+", re.MULTILINE)


def extract_system_contract_section(main_prd: str) -> str:
    if not main_prd:
        raise ValueError("Main PRD is empty; cannot extract System Contract section.")

    match = _H2_SYSTEM_CONTRACT_RE.search(main_prd)
    if not match:
        raise ValueError("Main PRD missing '## System Contract (Source of Truth)' section.")

    start = match.start()
    remainder = main_prd[start:]
    next_match = _H2_NEXT_SECTION_RE.search(remainder, 1)
    if not next_match:
        return remainder.strip() + "\n"
    return remainder[: next_match.start()].strip() + "\n"


def parse_frontend_required(contract_section: str) -> bool:
    if not contract_section:
        raise ValueError("System Contract section is empty; cannot parse frontend_required.")

    match = re.search(r"^-\s*frontend_required:\s*(true|false)\s*$", contract_section, re.IGNORECASE | re.MULTILINE)
    if not match:
        raise ValueError("System Contract missing '- frontend_required: true|false' line.")
    return match.group(1).lower() == "true"


def _extract_after_heading(text: str, start_re: re.Pattern, end_res: list) -> str | None:
    """Extract text after start_re up to the first matching end pattern, or None if start absent."""
    start_match = start_re.search(text)
    if not start_match:
        return None

    search_from = start_match.end()
    end_pos = None
    for end_re in end_res:
        m = end_re.search(text, search_from)
        if m and (end_pos is None or m.start() < end_pos):
            end_pos = m.start()

    body = text[search_from:end_pos] if end_pos is not None else text[search_from:]
    stripped = body.strip()
    return (stripped + "\n") if stripped else ""


def extract_core_entities_block(contract_section: str) -> str | None:
    """Return the Core Entities block body, or None if the heading is absent."""
    return _extract_after_heading(
        contract_section,
        _H3_CORE_ENTITIES_RE,
        [_H3_API_CONTRACT_RE, _H3_DATA_FLOW_RE, _H2_NEXT_SECTION_RE],
    )


def extract_api_contract_block(contract_section: str) -> dict | None:
    """Return a parsed API contract dict, or None if the heading is absent."""
    if not contract_section:
        raise ValueError("System Contract section is empty; cannot extract API Contract.")

    api_body = _extract_after_heading(
        contract_section,
        _H3_API_CONTRACT_RE,
        [_H3_DATA_FLOW_RE, _H2_NEXT_SECTION_RE, _H3_ANY_RE],
    )
    if api_body is None:
        return None

    if re.search(r"No backend API required\.?", api_body, re.IGNORECASE):
        return {"type": "none", "markdown": "No backend API required."}

    lines = [ln.rstrip("\n") for ln in api_body.splitlines()]
    header_idx = None
    for i, ln in enumerate(lines):
        if re.match(r"^\|\s*Method\s*\|\s*Path\s*\|", ln):
            header_idx = i
            break

    if header_idx is None:
        # Heading present but content is neither a table nor the "no backend" sentinel.
        # Treat as absent so the decomposer can apply its stack fallback.
        return None

    table_lines = []
    for ln in lines[header_idx:]:
        if not ln.strip():
            break
        if not ln.lstrip().startswith("|"):
            break
        table_lines.append(ln)

    if len(table_lines) < 2:
        raise ValueError("API Contract table appears malformed (expected header + separator).")

    return {"type": "table", "markdown": "\n".join(table_lines).strip() + "\n"}


def backend_required_from_api_contract(api_contract: dict) -> bool:
    if not api_contract or not isinstance(api_contract, dict):
        raise ValueError("api_contract must be a dict with keys {type, markdown}.")
    return api_contract.get("type") != "none"


def parse_system_contract(main_prd: str) -> dict:
    """Parse the System Contract section and return a normalized result dict.

    Returns:
        {
            "system_contract_markdown": str,
            "frontend_required": bool,
            "core_entities_markdown": str | None,
            "api_contract": {"type": "none"|"table", "markdown": str} | None,
            "data_flow_markdown": str | None,
        }

    Raises ValueError if main_prd is empty, the System Contract section is missing,
    or frontend_required cannot be determined.
    """
    contract_section = extract_system_contract_section(main_prd)
    frontend_required = parse_frontend_required(contract_section)
    core_entities_markdown = extract_core_entities_block(contract_section)
    api_contract = extract_api_contract_block(contract_section)
    data_flow_markdown = _extract_after_heading(
        contract_section,
        _H3_DATA_FLOW_RE,
        [_H2_NEXT_SECTION_RE, _H3_ANY_RE],
    )
    return {
        "system_contract_markdown": contract_section,
        "frontend_required": frontend_required,
        "core_entities_markdown": core_entities_markdown,
        "api_contract": api_contract,
        "data_flow_markdown": data_flow_markdown,
    }
