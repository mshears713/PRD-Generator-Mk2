import json

from llm import call_llm


def generate_backend_prd(main_prd: str, normalized: dict, architecture: dict) -> str:
    system_name = (normalized or {}).get("system_name") or "System"

    system_prompt = (
        "You are a senior software engineer writing an implementation-ready Backend PRD.\n"
        "You receive a main PRD, a normalized system definition, and an architecture analysis.\n"
        "Your job is to expand the main PRD into backend-specific implementation detail.\n\n"
        "CRITICAL RULES\n"
        "- Ground every decision in the main PRD. Do NOT invent requirements.\n"
        "- Be concrete: name endpoints, models, and components by their actual paths/names.\n"
        "- Keep the document practical; avoid generic filler.\n"
        "- For each implementation phase, include 2-4 concrete bullets describing what to build and how to verify it.\n\n"
        "OUTPUT FORMAT\n"
        "Return markdown with EXACTLY these headings in this order:\n"
        f"# {system_name} Backend PRD\n"
        "## Purpose\n"
        "## Responsibilities\n"
        "## Architecture\n"
        "## Endpoints\n"
        "## Data / Models\n"
        "## External Integrations\n"
        "## Validation / Error Handling\n"
        "## Testing Strategy\n"
        "## Out of Scope\n"
        "## Implementation Phases\n\n"
        "Implementation Phases must include exactly 4 phases with these names:\n"
        "- Phase 1 — Backend skeleton and contracts\n"
        "- Phase 2 — Core request flow and business logic\n"
        "- Phase 3 — External integrations and data handling\n"
        "- Phase 4 — Validation, tests, and polish\n\n"
        "Only output the markdown. No preamble, no closing remarks."
    )

    result = call_llm(
        "Main PRD (source of truth):\n"
        f"{main_prd}\n\n"
        "Normalized system definition:\n"
        f"{json.dumps(normalized or {}, indent=2)}\n\n"
        "Architecture analysis:\n"
        f"{json.dumps(architecture or {}, indent=2)}\n",
        {
            "agent_name": "backend_prd_standalone",
            "model": "gpt-4o",
            "temperature": 0.3,
            "system_prompt": system_prompt,
            "expect_json": False,
            "input_data": {"main_prd": main_prd, "normalized": normalized, "architecture": architecture},
        },
    )

    return (result.get("text") or "").strip() + "\n"
