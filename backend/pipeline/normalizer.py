import json
import os
from openai import OpenAI


def normalize(idea: str, selections: dict) -> dict:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    apis_str = ", ".join(selections["apis"]) if selections["apis"] else "none"
    stack_desc = (
        f"Scope: {selections['scope']}, Backend: {selections['backend']}, "
        f"Frontend: {selections['frontend']}, APIs: {apis_str}, Database: {selections['database']}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
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
                    "- Output ONLY valid JSON. No markdown fences."
                ),
            },
            {"role": "user", "content": f"Idea: {idea}\nStack: {stack_desc}"},
        ],
    )

    return json.loads(response.choices[0].message.content)
