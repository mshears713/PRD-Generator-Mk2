import json

from llm import call_llm


def analyze(normalized: dict) -> dict:
    system_prompt = (
                    "You are a software architect. Given a normalized system definition, produce a concrete architecture analysis.\n\n"
                    "Output this exact JSON structure:\n"
                    "{\n"
                    '  \"components\": [\n'
                    '    {\"name\": \"Component Name\", \"responsibility\": \"What it does in one sentence\"}\n'
                    "  ],\n"
                    '  \"data_flow\": [\n'
                    '    \"Step 1: User does X -> Y happens\",\n'
                    '    \"Step 2: ...\"\n'
                    "  ],\n"
                    '  \"dependencies\": [\n'
                    '    \"Component A calls Component B for X\"\n'
                    "  ],\n"
                    '  \"risks\": [\n'
                    '    \"Risk description and why it matters\"\n'
                    "  ],\n"
                    '  \"failure_points\": [\"Specific point of failure and impact\"],\n'
                    '  \"minimal_mvp_components\": [\"Smallest set of components to ship v1\"]\n'
                    "}\n\n"
                    "Rules:\n"
                    "- components: 4-8 items, each with a single clear responsibility\n"
                    "- data_flow: 4-7 steps showing how data moves for the primary use case, ordered end-to-end\n"
                    "- dependencies: list all non-obvious inter-component dependencies\n"
                    "- risks: 2-4 realistic technical risks specific to this system\n"
                    "- failure_points: 2-4 places where the flow can break (e.g., 'LLM timeout -> user waits >30s')\n"
                    "- minimal_mvp_components: 3-5 concrete pieces required to launch (name them explicitly)\n"
                    "COMPONENT PRECISION\n"
                    "- Components must map directly to real parts of the system (API layer, frontend UI, database, background worker, file store, etc.)\n"
                    "- Avoid generic components like \"Backend\" — be specific (e.g. \"FastAPI Service\")\n\n"
                    "- Output ONLY valid JSON. No markdown fences."
    )

    try:
        result = call_llm(
            f"System definition:\n{json.dumps(normalized, indent=2)}",
            {
                "agent_name": "analyzer",
                "model": "gpt-4o",
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "system_prompt": system_prompt,
                "expect_json": True,
                "input_data": {"normalized": normalized},
            },
        )
        # Ensure required keys exist even if LLM output is sparse
        result.setdefault("failure_points", [])
        result.setdefault("minimal_mvp_components", [])
        return result
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        raise ValueError(f"Analyzer received invalid JSON from LLM: {e}")
