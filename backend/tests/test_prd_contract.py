import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PYTEST_RUNNING", "1")

import pytest

from pipeline.prd_contract import (
    backend_required_from_api_contract,
    extract_api_contract_block,
    extract_core_entities_block,
    extract_system_contract_section,
    parse_frontend_required,
    parse_system_contract,
)

# ---------------------------------------------------------------------------
# Fixtures — reusable PRD strings
# ---------------------------------------------------------------------------

FULL_STRUCTURE_CONTRACT = (
    "## System Contract (Source of Truth)\n"
    "- frontend_required: true\n\n"
    "### Core Entities\n"
    "- **Foo:** A thing.\n"
    "- **Bar:** Another thing.\n\n"
    "### API Contract\n"
    "| Method | Path | Purpose | Input (high-level) | Output (high-level) |\n"
    "|--------|------|---------|--------------------|---------------------|\n"
    "| POST | /do | Do | {x} | {y} |\n\n"
    "### Data Flow\n"
    "1. x\n\n"
)

MINIMAL_CONTRACT_ONLY = (
    "## System Contract (Source of Truth)\n"
    "- frontend_required: false\n\n"
)

FULL_PRD = (
    "# Demo PRD\n\n"
    "## Overview\n"
    "x\n\n"
    + FULL_STRUCTURE_CONTRACT
    + "## Architecture\n"
    "y\n"
)

MINIMAL_PRD = (
    "# Minimal PRD\n\n"
    "## Overview\n"
    "Minimal system with no optional subsections.\n\n"
    + MINIMAL_CONTRACT_ONLY
    + "## Architecture\n"
    "Simple architecture.\n\n"
    "## Components\n"
    "- Core module\n\n"
    "## Test Cases\n"
    "- Basic smoke test\n"
)

# ---------------------------------------------------------------------------
# Existing tests — backward-compatible extraction (numbered headings still work)
# ---------------------------------------------------------------------------

def test_extract_system_contract_section_and_frontend_required():
    prd = (
        "# Demo PRD\n\n"
        "## Overview\n"
        "x\n\n"
        "## System Contract (Source of Truth)\n"
        "- frontend_required: true\n\n"
        "### 1. Core Entities\n"
        "- **Foo:** A thing.\n\n"
        "### 2. API Contract\n"
        "| Method | Path | Purpose | Input (high-level) | Output (high-level) |\n"
        "|--------|------|---------|--------------------|---------------------|\n"
        "| POST | /do | Do | {x} | {y} |\n\n"
        "### 3. Data Flow\n"
        "1. x\n\n"
        "## Architecture\n"
        "y\n"
    )
    section = extract_system_contract_section(prd)
    assert "## System Contract (Source of Truth)" in section
    assert parse_frontend_required(section) is True


def test_extract_core_entities_block_numbered():
    contract = (
        "## System Contract (Source of Truth)\n"
        "- frontend_required: false\n\n"
        "### 1. Core Entities\n"
        "- **Foo:** A thing.\n"
        "- **Bar:** Another thing.\n\n"
        "### 2. API Contract\n"
        "No backend API required.\n\n"
        "### 3. Data Flow\n"
        "1. x\n"
    )
    entities = extract_core_entities_block(contract)
    assert entities is not None
    assert "- **Foo:** A thing." in entities
    assert "### 1. Core Entities" not in entities


def test_extract_api_contract_block_none_and_backend_required_false():
    contract = (
        "## System Contract (Source of Truth)\n"
        "- frontend_required: true\n\n"
        "### 1. Core Entities\n"
        "- **Foo:** A thing.\n\n"
        "### 2. API Contract\n"
        "No backend API required.\n\n"
        "### 3. Data Flow\n"
        "1. x\n"
    )
    api_contract = extract_api_contract_block(contract)
    assert api_contract is not None
    assert api_contract["type"] == "none"
    assert api_contract["markdown"] == "No backend API required."
    assert backend_required_from_api_contract(api_contract) is False


def test_extract_api_contract_block_table_and_backend_required_true():
    contract = (
        "## System Contract (Source of Truth)\n"
        "- frontend_required: true\n\n"
        "### 1. Core Entities\n"
        "- **Foo:** A thing.\n\n"
        "### 2. API Contract\n"
        "| Method | Path | Purpose | Input (high-level) | Output (high-level) |\n"
        "|--------|------|---------|--------------------|---------------------|\n"
        "| POST | /do | Do | {x} | {y} |\n\n"
        "### 3. Data Flow\n"
        "1. x\n"
    )
    api_contract = extract_api_contract_block(contract)
    assert api_contract is not None
    assert api_contract["type"] == "table"
    assert "| Method | Path |" in api_contract["markdown"]
    assert backend_required_from_api_contract(api_contract) is True


# ---------------------------------------------------------------------------
# New tests — unnumbered headings
# ---------------------------------------------------------------------------

def test_extract_core_entities_block_unnumbered():
    entities = extract_core_entities_block(FULL_STRUCTURE_CONTRACT)
    assert entities is not None
    assert "- **Foo:** A thing." in entities


def test_extract_api_contract_block_unnumbered_table():
    api_contract = extract_api_contract_block(FULL_STRUCTURE_CONTRACT)
    assert api_contract is not None
    assert api_contract["type"] == "table"
    assert "| POST | /do |" in api_contract["markdown"]


# ---------------------------------------------------------------------------
# New tests — tolerant behavior (optional sections absent → None, not raise)
# ---------------------------------------------------------------------------

def test_extract_core_entities_block_returns_none_when_absent():
    result = extract_core_entities_block(MINIMAL_CONTRACT_ONLY)
    assert result is None


def test_extract_api_contract_block_returns_none_when_absent():
    result = extract_api_contract_block(MINIMAL_CONTRACT_ONLY)
    assert result is None


def test_extract_api_contract_block_returns_none_when_empty_body():
    # Heading present, nothing inside it before the next section.
    contract = (
        "## System Contract (Source of Truth)\n"
        "- frontend_required: false\n\n"
        "### API Contract\n"
        "### Data Flow\n"
        "1. x\n"
    )
    assert extract_api_contract_block(contract) is None


def test_extract_api_contract_block_returns_none_when_content_unrecognized():
    # Heading present but body is neither a table nor the explicit sentinel.
    # This is the runtime error case: LLM wrote prose instead of a table.
    contract = (
        "## System Contract (Source of Truth)\n"
        "- frontend_required: true\n\n"
        "### API Contract\n"
        "TBD — endpoints not yet defined.\n\n"
        "### Data Flow\n"
        "1. x\n"
    )
    result = extract_api_contract_block(contract)
    assert result is None


# ---------------------------------------------------------------------------
# New tests — parse_system_contract() top-level function
# ---------------------------------------------------------------------------

def test_parse_system_contract_full_structure():
    result = parse_system_contract(FULL_PRD)
    assert "## System Contract (Source of Truth)" in result["system_contract_markdown"]
    assert result["frontend_required"] is True
    assert result["core_entities_markdown"] is not None
    assert "- **Foo:**" in result["core_entities_markdown"]
    assert result["api_contract"] is not None
    assert result["api_contract"]["type"] == "table"
    assert result["data_flow_markdown"] is not None
    assert "1. x" in result["data_flow_markdown"]


def test_parse_system_contract_minimal():
    result = parse_system_contract(MINIMAL_PRD)
    assert result["frontend_required"] is False
    assert result["core_entities_markdown"] is None
    assert result["api_contract"] is None
    assert result["data_flow_markdown"] is None


def test_parse_system_contract_raises_on_empty_prd():
    with pytest.raises(ValueError, match="empty"):
        parse_system_contract("")


def test_parse_system_contract_raises_on_missing_section():
    prd_without_contract = "# PRD\n\n## Overview\nNo contract here.\n\n## Architecture\n...\n"
    with pytest.raises(ValueError, match="System Contract"):
        parse_system_contract(prd_without_contract)
