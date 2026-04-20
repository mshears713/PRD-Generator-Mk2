import json
import re

from llm import call_llm


CORE_ENTITIES_PLACEHOLDER = "{{STACKLENS_CORE_ENTITIES}}"
API_CONTRACT_PLACEHOLDER = "{{STACKLENS_API_CONTRACT}}"


def _inject_contract(markdown: str, core_entities_markdown: str, api_contract_markdown: str) -> str:
    if markdown.count(CORE_ENTITIES_PLACEHOLDER) != 1:
        raise ValueError("Backend PRD template must include {{STACKLENS_CORE_ENTITIES}} exactly once.")
    if markdown.count(API_CONTRACT_PLACEHOLDER) != 2:
        raise ValueError("Backend PRD template must include {{STACKLENS_API_CONTRACT}} exactly twice.")

    if re.search(r"^\|\s*Method\s*\|\s*Path\s*\|", markdown, re.MULTILINE):
        raise ValueError("Backend PRD must not include an API table; use {{STACKLENS_API_CONTRACT}} placeholders only.")
    if re.search(r"No backend API required\.", markdown, re.IGNORECASE):
        raise ValueError("Backend PRD must not restate API contract text; use {{STACKLENS_API_CONTRACT}} placeholders only.")

    injected = markdown.replace(CORE_ENTITIES_PLACEHOLDER, (core_entities_markdown or "").strip() + "\n")
    injected = injected.replace(API_CONTRACT_PLACEHOLDER, (api_contract_markdown or "").strip() + "\n")

    if CORE_ENTITIES_PLACEHOLDER in injected or API_CONTRACT_PLACEHOLDER in injected:
        raise ValueError("Backend PRD contract placeholders were not fully replaced.")
    return injected


def generate_backend_prd(
    main_prd: str,
    normalized: dict,
    architecture: dict,
    *,
    core_entities_markdown: str,
    api_contract_markdown: str,
) -> str:
    system_name = (normalized or {}).get("system_name") or "System"

    system_prompt = (
        "You are a senior software engineer writing an implementation-ready Backend PRD.\n"
        "You are given a main PRD that contains the source-of-truth system contract.\n\n"
        "CRITICAL RULES\n"
        "- Do NOT invent new endpoints or change endpoint shapes.\n"
        "- Do NOT include any API Contract markdown table or endpoint table yourself.\n"
        "- Do NOT restate entities from the main PRD.\n"
        "- You MUST use placeholders exactly as instructed so the system can inject the source-of-truth contract.\n"
        "- Keep the document practical and concise; avoid generic filler.\n"
        "- Reference the main PRD only as needed; do not copy the full overview.\n\n"
        "COMPONENT SPECIFICATION\n"
        "For each major component or service you describe, include enough detail for a coding agent to plan its implementation:\n"
        "  - Input: what data or signals it receives\n"
        "  - Output: what data or result it returns\n"
        "  - Processing: what transformation or operation it performs, in concrete terms\n"
        "  - Failure: only when a failure mode is materially relevant (e.g., external dependency unavailable)\n"
        "Omit sub-fields that genuinely do not apply to a given component.\n\n"
        "IMPLEMENTATION PHASES\n"
        "Implementation Phases must include exactly 4 phases with these names:\n"
        "- Phase 1 — Backend skeleton and contracts\n"
        "- Phase 2 — Core request flow and business logic\n"
        "- Phase 3 — External integrations and data handling\n"
        "- Phase 4 — Validation, tests, and polish\n\n"
        "For each phase, include 2-4 concrete bullets that specify:\n"
        "  - What gets built (name the specific endpoints, models, services, or components implemented)\n"
        "  - What visible behavior proves the phase is complete (e.g., 'POST /generate returns 200 with {result: string}')\n"
        "Each phase must be independently buildable. Do NOT introduce endpoints or models beyond those in the main PRD.\n\n"
        "OUTPUT FORMAT\n"
        "Return markdown with EXACTLY these headings in this order:\n"
        f"# {system_name} Backend PRD\n"
        "## Purpose\n"
        "## Responsibilities\n"
        "## Integration Contract (From Main PRD — Do Not Change Without Updating Main PRD)\n"
        "### Core Entities\n"
        f"{CORE_ENTITIES_PLACEHOLDER}\n"
        "### API Contract\n"
        f"{API_CONTRACT_PLACEHOLDER}\n"
        "## Architecture\n"
        "## Endpoints (Must match API Contract)\n"
        f"{API_CONTRACT_PLACEHOLDER}\n"
        "## Data / Models\n"
        "## External Integrations\n"
        "## Validation / Error Handling\n"
        "## Testing Strategy\n"
        "## Out of Scope\n"
        "## Implementation Phases\n\n"
        "Only output the markdown. No preamble, no closing remarks."
        
        "MANDATORY COMPONENT SPECIFICATION"
        

    "For every component, you MUST include:"

    "- Input: what data it receives
    "- Output: what data it produces
    "- Processing: what transformation it performs

        "Do NOT describe components abstractly."

"A component description is incomplete if it only states responsibility."
    )

    result = call_llm(
        "Main PRD (source of truth):\n"
        f"{main_prd}\n\n"
        "Normalized system definition:\n"
        f"{json.dumps(normalized or {}, indent=2)}\n\n"
        "Architecture analysis:\n"
        f"{json.dumps(architecture or {}, indent=2)}\n",
        {
            "agent_name": "backend_prd_gen",
            "model": "gpt-4o",
            "temperature": 0.3,
            "system_prompt": system_prompt,
            "expect_json": False,
            "input_data": {"main_prd": main_prd, "normalized": normalized, "architecture": architecture},
        },
    )

    text = (result.get("text") or "").strip() + "\n"
    return _inject_contract(text, core_entities_markdown, api_contract_markdown)
