import re


_H2_SYSTEM_CONTRACT_RE = re.compile(r"^##\s+System Contract\s+\(Source of Truth\)\s*$", re.MULTILINE)
_H3_CORE_ENTITIES_RE = re.compile(r"^###\s+1\.\s+Core Entities\s*$", re.MULTILINE)
_H3_API_CONTRACT_RE = re.compile(r"^###\s+2\.\s+API Contract\s*$", re.MULTILINE)
_H3_DATA_FLOW_RE = re.compile(r"^###\s+3\.\s+Data Flow\s*$", re.MULTILINE)
_H2_NEXT_SECTION_RE = re.compile(r"^##\s+", re.MULTILINE)


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

    match = re.search(r"^- frontend_required:\s*(true|false)\s*$", contract_section, re.IGNORECASE | re.MULTILINE)
    if not match:
        raise ValueError("System Contract missing '- frontend_required: true|false' line.")
    return match.group(1).lower() == "true"


def _extract_between_headings(text: str, start_re: re.Pattern, end_re: re.Pattern) -> str:
    start_match = start_re.search(text)
    if not start_match:
        raise ValueError(f"Missing expected heading: {start_re.pattern}")

    end_match = end_re.search(text, start_match.end())
    if not end_match:
        raise ValueError(f"Missing expected heading: {end_re.pattern}")

    body = text[start_match.end() : end_match.start()]
    return body.strip() + "\n" if body.strip() else ""


def extract_core_entities_block(contract_section: str) -> str:
    return _extract_between_headings(contract_section, _H3_CORE_ENTITIES_RE, _H3_API_CONTRACT_RE)


def extract_api_contract_block(contract_section: str) -> dict:
    if not contract_section:
        raise ValueError("System Contract section is empty; cannot extract API Contract.")

    api_body = _extract_between_headings(contract_section, _H3_API_CONTRACT_RE, _H3_DATA_FLOW_RE)
    if re.search(r"No backend API required\.?", api_body, re.IGNORECASE):
        return {"type": "none", "markdown": "No backend API required."}

    lines = [ln.rstrip("\n") for ln in api_body.splitlines()]
    header_idx = None
    for i, ln in enumerate(lines):
        if re.match(r"^\|\s*Method\s*\|\s*Path\s*\|", ln):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("API Contract table not found and 'No backend API required.' not present.")

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
