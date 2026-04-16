import json

from llm import call_llm


def generate_prd(normalized: dict, architecture: dict) -> str:
    system_prompt = (
                    "You are a senior technical writer producing grounded PRDs. "
                    "Given a normalized system definition and architecture analysis, write a structured PRD in markdown.\n\n"
                    "SYSTEM TYPE AWARENESS\n"
                    "- The system may be a backend service, CLI tool, background worker, pipeline system, sandbox executor, or fullstack app.\n"
                    "- Infer system type from normalized definition and architecture components.\n"
                    "- Do NOT assume a frontend exists unless selected_stack.frontend != 'none'.\n\n"
                    "NO INVENTION RULE\n"
                    "- Do NOT introduce a frontend, backend type, APIs, or database unless explicitly present in selected_stack or architecture.components.\n"
                    "- If details are missing, state uncertainty explicitly and do not fill gaps with defaults.\n\n"
                    "GROUNDING RULE\n"
                    "- Every section must be derived from normalized.system definition, analyzer.components, and analyzer.data_flow.\n"
                    "- If a detail is absent from those sources, do not invent it.\n\n"
                    "EXECUTION MODEL PRIORITY\n"
                    "- Prioritize how the system runs: where computation happens, what triggers execution, and how data flows internally.\n"
                    "- Do not center UI layout or generic request/response wrappers unless they are core to the system.\n\n"
                    "STRUCTURE RULES\n"
                    "- Produce a structured PRD in markdown.\n"
                    "- The structure must adapt to the inferred system type.\n"
                    "- Minimum required sections: Overview, System Contract (Source of Truth), Architecture, Components, Test Cases.\n"
                    "- Optional sections (include only if relevant): API Contract (only if backend exposes endpoints), Frontend (only if frontend exists), State Model (only if state is meaningful), External Integrations / API Usage (only if APIs are used).\n"
                    "- Do not include sections that are not justified by the system.\n"
                    "- Do not enforce a fixed section order beyond keeping the document readable.\n\n"
                    "CONDITIONAL BEHAVIOR\n"
                    "- If selected_stack.frontend == 'none', do not include frontend-related sections.\n"
                    "- If selected_stack.backend == 'none', do not include API Contract or backend-specific sections.\n"
                    "- If selected_stack.database == 'none', explicitly state no persistent storage.\n"
                    "- In System Contract, always include: frontend_required: true|false based on selected_stack.frontend.\n\n"
                    "IMPLEMENTATION FOCUS\n"
                    "- Keep each section implementation-ready and specific.\n"
                    "- Describe responsibilities, interfaces, and key logic using only grounded facts.\n"
                    "- Avoid vague wording.\n\n"
                    "Output ONLY markdown. No preamble or closing remarks."
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
