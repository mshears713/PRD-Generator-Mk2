import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PYTEST_RUNNING", "1")

from pipeline.prd_contract import (
    backend_required_from_api_contract,
    extract_api_contract_block,
    extract_core_entities_block,
    extract_system_contract_section,
    parse_frontend_required,
)


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


def test_extract_core_entities_block():
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
    assert api_contract["type"] == "table"
    assert "| Method | Path |" in api_contract["markdown"]
    assert backend_required_from_api_contract(api_contract) is True

