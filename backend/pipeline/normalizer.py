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
                    "and produce a clear, unambiguous system definition anchored to the provided stack selections (treat them as hard constraints).\n\n"
                    "Output this exact JSON structure:\n"
                    "{\n"
                    '  "system_name": "Short descriptive name (2-4 words, title case)",\n'
                    '  "purpose": "One precise sentence: what the system does and for whom",\n'
                    '  "core_features": ["concrete feature 1", "concrete feature 2", "..."],\n'
                    '  "user_types": ["user role 1", "user role 2"],\n'
                    '  "input_output": ["Step 1: user input → component → output"],\n'
                    '  "data_model": ["Entity: key fields / storage"],\n'
                    '  "constraints": ["technical constraint derived from stack selections"],\n'
                    '  "assumptions": ["explicit assumption stated as assumption"],\n'
                    '  "unknowns": ["specific open question or missing detail"]\n'
                    "}\n\n"
                    "Rules:\n"
                    "- purpose: specific (bad: 'helps users'; good: 'lets remote teams create, assign, and track tasks with real-time updates').\n"
                    "- core_features: 4-6 capabilities; each describes an action + target + outcome.\n"
                    "- input_output: 3-5 ordered strings showing how a request moves through the system (include interface, component, and response).\n"
                    "- data_model: 2-4 entries naming the main entities with 1-2 key fields; if database=none, state 'No persistent data stored'.\n"
                    "- constraints: derive directly from stack selections (e.g., FastAPI → HTTP JSON API layer; Postgres → relational schema).\n"
                    "- assumptions: 3-5 explicit statements resolving ambiguity (format 'Assuming ...').\n"
                    "- unknowns: 2-4 precise gaps/questions the idea does not answer.\n"
                    "- Use only what the idea implies; do NOT invent complex features beyond the scope.\n"
                    "- Be explicit: avoid verbs like 'handle/support' without describing the behavior.\n\n"
                    "- Output ONLY valid JSON. No markdown fences."
    )

    try:
        result = call_llm(
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
        # Ensure required fields exist even if LLM omits them
        for key in ("assumptions", "unknowns", "input_output", "data_model", "constraints"):
            result.setdefault(key, [])
        return result
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        raise ValueError(f"Normalizer received invalid JSON from LLM: {e}")
