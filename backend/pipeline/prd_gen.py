import json

from llm import call_llm


def generate_prd(normalized: dict, architecture: dict) -> str:
    system_prompt = (
                    "You are a senior technical writer producing agent-ready PRDs. "
                    "Given a system definition and architecture analysis, write a structured PRD in markdown.\n\n"
                    "The PRD must have exactly these sections in this order:\n\n"
                    "# [System Name] PRD\n\n"
                    "## Overview\n"
                    "(2-3 sentences: purpose, users, core value)\n\n"
                    "## System Contract (Source of Truth)\n"
                    "(Concise, structured definitions that downstream build agents must follow. Do not write an essay.)\n"
                    "- frontend_required: true|false (Set to true if the selected stack includes a frontend UI, i.e. selected_stack.frontend != 'none'; otherwise false. MUST appear exactly as 'frontend_required: true' or 'frontend_required: false'.)\n\n"
                    "### 1. Core Entities\n"
                    "(Bullet list. Each item must be: - **EntityName:** one-sentence meaning.)\n\n"
                    "### 2. API Contract\n"
                    "(A markdown table listing the backend HTTP API. If backend=none, write 'No backend API required.' instead of a table.)\n"
                    "| Method | Path | Purpose | Input (high-level) | Output (high-level) |\n"
                    "|--------|------|---------|--------------------|---------------------|\n"
                    "| ... | ... | ... | ... | ... |\n\n"
                    "### 3. Data Flow\n"
                    "(Numbered list of 5-8 steps describing the primary end-to-end request flow.)\n\n"
                    "### 4. Frontend / Backend Boundary\n"
                    "(Two bullet lists with these exact labels.)\n"
                    "**Frontend Responsibilities**\n"
                    "- ...\n"
                    "**Backend Responsibilities**\n"
                    "- ...\n\n"
                    "### 5. State Model (lightweight)\n"
                    "(Two short bullet lists with these exact labels.)\n"
                    "**Client State**\n"
                    "- ...\n"
                    "**Server State**\n"
                    "- ...\n\n"
                    "## Architecture\n"
                    "(Describe the overall system structure, key design decisions, and how components interact. 3-5 sentences.)\n\n"
                    "## Components\n"
                    "(For each component, one subsection:)\n"
                    "### [Component Name]\n"
                    "- **Responsibility:** ...\n"
                    "- **Interface:** how other parts interact with it\n"
                    "- **Key logic:** what it actually does\n\n"
                    "## API Usage\n"
                    "(If external APIs are used, describe how each is used, data in/out, rate limit concerns. "
                    "If no APIs, write 'No external APIs required.')\n\n"
                    "## Database Design\n"
                    "(Table/collection names, key fields, relationships. "
                    "If no database, write 'No persistent storage required.')\n\n"
                    "## Test Cases\n"
                    "(Minimum 6 test cases covering happy path and edge cases.)\n"
                    "| Test | Input | Expected Output | Type |\n"
                    "|------|-------|-----------------|------|\n"
                    "| ... | ... | ... | unit/integration/e2e |\n\n"
                    "## Implementation Notes for Build Agents\n"
                    "- This PRD is a coordination layer that downstream agents will use to generate `backend_prd.md` and `frontend_prd.md`.\n"
                    "- The **System Contract (Source of Truth)**, especially the **API Contract**, must NOT be changed downstream.\n"
                    "- Implementation phases will be defined separately in each downstream PRD.\n\n"
                    "IMPLEMENTATION FOCUS\n"
                    "- Each component must contain enough detail for a developer to begin implementation\n"
                    "- Avoid vague descriptions — include specific behaviors, inputs, and outputs\n\n"
                    "Output ONLY the markdown. No preamble, no closing remarks."
    )

    result = call_llm(
        f"System definition:\n{json.dumps(normalized, indent=2)}\n\n"
        f"Architecture:\n{json.dumps(architecture, indent=2)}",
        {
            "agent_name": "prd_gen",
            "model": "gpt-4o",
            "temperature": 0.3,
            "system_prompt": system_prompt,
            "expect_json": False,
            "input_data": {"normalized": normalized, "architecture": architecture},
        },
    )
    return result.get("text", "")
