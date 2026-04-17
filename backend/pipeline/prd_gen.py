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
                "- Structure must adapt to the system.\n\n"

                "Minimum required sections:\n"
                "- Overview\n"
                "- System Contract (Source of Truth)\n"
                "- Architecture\n"
                "- Components\n"
                "- Test Cases\n\n"

                "Optional sections (include ONLY if relevant):\n"
                "- API Contract (only if backend exposes endpoints)\n"
                "- Frontend (only if frontend exists)\n"
                "- State Model (only if state is meaningful)\n"
                "- External Integrations / API Usage (only if APIs are used)\n\n"

                "- Do NOT include sections that are not justified by the system.\n"
                "- Do NOT enforce a fixed section order beyond readability.\n\n"

                "---\n"
                "CONDITIONAL RULES\n"
                "---\n"

                "- If selected_stack.frontend == 'none':\n"
                "  → Do NOT include frontend sections\n"

                "- If selected_stack.backend == 'none':\n"
                "  → Do NOT include API sections\n"

                "- If selected_stack.database == 'none':\n"
                "  → Explicitly state no persistent storage\n\n"

                "- In System Contract, always include:\n"
                "  frontend_required: true|false based on selected_stack.frontend\n\n"

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
