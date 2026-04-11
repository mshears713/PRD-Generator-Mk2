import json

from llm import call_llm


def normalize(idea: str, selections: dict) -> dict:
    apis_str = ", ".join(selections["apis"]) if selections["apis"] else "none"
    stack_desc = (
        f"Scope: {selections['scope']}, Backend: {selections['backend']}, "
        f"Frontend: {selections['frontend']}, APIs: {apis_str}, Database: {selections['database']}"
    )

    system_prompt = (
                    "You are a software requirements analyst. Remove vagueness from a product idea "
                    "and produce a clear, unambiguous system definition.\n\n"
                    "Output this exact JSON structure:\n"
                    "{\n"
                    '  "system_name": "Short descriptive name (2-4 words, title case)",\n'
                    '  "purpose": "One precise sentence: what the system does and for whom",\n'
                    '  "core_features": ["concrete feature 1", "concrete feature 2", "..."],\n'
                    '  "user_types": ["user role 1", "user role 2"],\n'
                    '  "constraints": ["technical constraint from stack"],\n'
                    '  "assumptions_removed": ["vague phrase → specific replacement"]\n'
                    "}\n\n"
                    "Rules:\n"
                    "- purpose: specific (bad: 'helps users'; good: 'lets remote teams create, assign, and track tasks with real-time updates')\n"
                    "- core_features: 4-6 items, each a concrete capability\n"
                    "- constraints: derive from the stack (e.g. 'FastAPI backend requires Python 3.10+')\n"
                    "- assumptions_removed: min 2 items showing how you clarified vague language\n"
                    "CLARITY REQUIREMENT\n"
                    "- Replace all vague terms with concrete system behavior\n"
                    "- If the idea is ambiguous, make a reasonable assumption and state it clearly\n"
                    "- Avoid phrases like \"manage\", \"handle\", \"support\" without specifying how\n\n"
                    "- Output ONLY valid JSON. No markdown fences."
    )

    try:
        return call_llm(
            f"Idea: {idea}\nStack: {stack_desc}",
            {
                "agent_name": "normalizer",
                "model": "gpt-4o",
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "system_prompt": system_prompt,
                "expect_json": True,
                "input_data": {"idea": idea, "selections": selections},
            },
        )
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        raise ValueError(f"Normalizer received invalid JSON from LLM: {e}")
