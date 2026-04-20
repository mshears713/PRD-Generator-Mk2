import json

from llm import call_llm


def generate_prd(normalized: dict, architecture: dict) -> str:
    system_prompt = (

                "You are a senior technical writer producing grounded, implementation-ready PRDs.\n\n"

                "Given a normalized system definition and architecture analysis, write a structured PRD in markdown.\n\n"

                "---\n"
                "CORE PRINCIPLES\n"
                "---\n"

                "SYSTEM TYPE AWARENESS\n"
                "- The system may be a backend service, CLI tool, background worker, pipeline system, sandbox executor, or fullstack app.\n"
                "- Infer system type from normalized definition and architecture components.\n"
                "- Do NOT assume a frontend exists unless selected_stack.frontend != 'none'.\n\n"

                "NO INVENTION RULE\n"
                "- Do NOT introduce a frontend, backend type, APIs, or database unless explicitly present in:\n"
                "  - selected_stack OR\n"
                "  - architecture.components\n"
                "- If information is missing, reflect uncertainty instead of filling gaps.\n\n"

                "GROUNDING RULE\n"
                "- Every section must be derived from:\n"
                "  - normalized system definition\n"
                "  - analyzer components\n"
                "  - analyzer data_flow\n"
                "- If a detail is not present in those, DO NOT invent it.\n\n"

                "EXECUTION MODEL PRIORITY\n"
                "- Focus on how the system actually runs:\n"
                "  - what triggers execution\n"
                "  - where computation happens\n"
                "  - how data flows internally\n"
                "- Do NOT default to UI or request/response framing unless it is central.\n\n"

                "---\n"
                "STRUCTURE RULES\n"
                "---\n"

                "- Produce a structured PRD in markdown.\n"
                "- Structure must adapt to the system. Do NOT apply a fixed template.\n\n"

                "Required sections (always present, in any order that aids readability):\n"
                "  ## Overview\n"
                "  ## System Contract (Source of Truth)\n"
                "  ## Architecture\n"
                "  ## Components\n"
                "  ## Test Cases\n\n"

                "System Contract rules:\n"
                "- Always include exactly one line: '- frontend_required: true' or '- frontend_required: false'\n"
                "- Add subsections (Core Entities, API Contract, Data Flow) ONLY when the system warrants them.\n"
                "- Do NOT number subsections (no '### 1.', '### 2.'). Use plain '### Core Entities' etc.\n"
                "- Do NOT inflate the System Contract with boilerplate or coordination-layer text.\n\n"

                "Optional sections (include ONLY when grounded in the system):\n"
                "- Any API-facing section — only if backend exposes HTTP endpoints\n"
                "- Any frontend section — only if frontend exists in selected_stack\n"
                "- Any state or database section — only if state or persistence is part of the system\n"
                "- Any external integrations section — only if third-party APIs are used\n\n"

                "- Do NOT include '## API Usage', '## Database Design', '## Implementation Notes for Build Agents',\n"
                "  '### Frontend / Backend Boundary', or '### State Model' unless clearly justified.\n"
                "- Do NOT enforce a fixed section order beyond readability.\n\n"

                "---\n"
                "CONDITIONAL RULES\n"
                "---\n"

                "- If selected_stack.frontend == 'none':\n"
                "  → Do NOT include frontend sections\n"
                "  → Set frontend_required: false in System Contract\n\n"

                "- If selected_stack.backend == 'none':\n"
                "  → Do NOT include API sections\n"
                "  → If System Contract has an API Contract subsection, write 'No backend API required.' only\n\n"

                "- If selected_stack.database == 'none':\n"
                "  → Explicitly state no persistent storage\n\n"

                "---\n"
                "IMPLEMENTATION FOCUS\n"
                "---\n"

                "- Each component must contain:\n"
                "  - Responsibility\n"
                "  - Interface\n"
                "  - Key logic\n"

                "- Be specific and concrete\n"
                "- Avoid vague or generic descriptions\n\n"

                "---\n"

                "Output ONLY the markdown. No preamble. No closing remarks."
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
