import json
import re

from llm import call_llm


CORE_ENTITIES_PLACEHOLDER = "{{STACKLENS_CORE_ENTITIES}}"
API_CONTRACT_PLACEHOLDER = "{{STACKLENS_API_CONTRACT}}"


def _inject_contract(markdown: str, core_entities_markdown: str, api_contract_markdown: str) -> str:
    if markdown.count(CORE_ENTITIES_PLACEHOLDER) != 1:
        raise ValueError("Frontend PRD template must include {{STACKLENS_CORE_ENTITIES}} exactly once.")
    if markdown.count(API_CONTRACT_PLACEHOLDER) != 2:
        raise ValueError("Frontend PRD template must include {{STACKLENS_API_CONTRACT}} exactly twice.")

    if re.search(r"^\|\s*Method\s*\|\s*Path\s*\|", markdown, re.MULTILINE):
        raise ValueError("Frontend PRD must not include an API table; use {{STACKLENS_API_CONTRACT}} placeholders only.")
    if re.search(r"No backend API required\.", markdown, re.IGNORECASE):
        raise ValueError("Frontend PRD must not restate API contract text; use {{STACKLENS_API_CONTRACT}} placeholders only.")

    injected = markdown.replace(CORE_ENTITIES_PLACEHOLDER, (core_entities_markdown or "").strip() + "\n")
    injected = injected.replace(API_CONTRACT_PLACEHOLDER, (api_contract_markdown or "").strip() + "\n")

    if CORE_ENTITIES_PLACEHOLDER in injected or API_CONTRACT_PLACEHOLDER in injected:
        raise ValueError("Frontend PRD contract placeholders were not fully replaced.")
    return injected


def generate_frontend_prd(
    main_prd: str,
    normalized: dict,
    architecture: dict,
    *,
    core_entities_markdown: str,
    api_contract_markdown: str,
) -> str:
    system_name = (normalized or {}).get("system_name") or "System"

    system_prompt = (
        "You are a senior frontend engineer writing an implementation-ready Frontend PRD.\n"
        "You are given a main PRD that contains the source-of-truth system contract.\n\n"
        "CRITICAL RULES\n"
        "- Do NOT invent new endpoints or change endpoint shapes.\n"
        "- Do NOT include any API Contract markdown table or endpoint table yourself.\n"
        "- Do NOT restate entities from the main PRD.\n"
        "- You MUST use placeholders exactly as instructed so the system can inject the source-of-truth contract.\n"
        "- Keep the document practical and concise; avoid generic filler.\n"
        "- Respect StackLens's linear guided flow philosophy.\n"
        "- For each phase, include 2-4 concrete bullets describing what to build and how to verify it.\n"
        "- Do not rewrite the full project overview; focus on UI behavior and integration.\n\n"
        "OUTPUT FORMAT\n"
        "Return markdown with EXACTLY these headings in this order:\n"
        f"# {system_name} Frontend PRD\n"
        "## Purpose\n"
        "## Responsibilities\n"
        "## Integration Contract (From Main PRD — Do Not Change Without Updating Main PRD)\n"
        "### Core Entities\n"
        f"{CORE_ENTITIES_PLACEHOLDER}\n"
        "### API Contract\n"
        f"{API_CONTRACT_PLACEHOLDER}\n"
        "## Views / Screens\n"
        "## User Flow\n"
        "## Components\n"
        "## State Model\n"
        "## API Usage (Must match API Contract)\n"
        f"{API_CONTRACT_PLACEHOLDER}\n"
        "## UX / Loading / Error Handling\n"
        "## Out of Scope\n"
        "## Implementation Phases\n\n"
        "Implementation Phases must include exactly 4 phases with these names:\n"
        "- Phase 1 — App shell and primary flow\n"
        "- Phase 2 — API wiring and state handling\n"
        "- Phase 3 — Output rendering and UX polish\n"
        "- Phase 4 — Edge handling and cleanup\n\n"
        "Phase writing rules:\n"
        "- Each phase must be independently buildable.\n"
        "- Include the specific screens/components introduced per phase.\n"
        "- Include minimal acceptance checks per phase (e.g., 'submit shows loading; success renders result; error shows retry').\n\n"
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
            "agent_name": "frontend_prd_gen",
            "model": "gpt-4o",
            "temperature": 0.3,
            "system_prompt": system_prompt,
            "expect_json": False,
            "input_data": {"main_prd": main_prd, "normalized": normalized, "architecture": architecture},
        },
    )

    text = (result.get("text") or "").strip() + "\n"
    return _inject_contract(text, core_entities_markdown, api_contract_markdown)
