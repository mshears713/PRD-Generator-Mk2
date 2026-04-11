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
