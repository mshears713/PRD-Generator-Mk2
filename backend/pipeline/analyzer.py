import json
import os
from openai import OpenAI


def analyze(normalized: dict) -> dict:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a software architect. Given a normalized system definition, produce a concrete architecture analysis.\n\n"
                    "Output this exact JSON structure:\n"
                    "{\n"
                    '  "components": [\n'
                    '    {"name": "Component Name", "responsibility": "What it does in one sentence"}\n'
                    "  ],\n"
                    '  "data_flow": [\n'
                    '    "Step 1: User does X -> Y happens",\n'
                    '    "Step 2: ..."\n'
                    "  ],\n"
                    '  "dependencies": [\n'
                    '    "Component A calls Component B for X"\n'
                    "  ],\n"
                    '  "risks": [\n'
                    '    "Risk description and why it matters"\n'
                    "  ]\n"
                    "}\n\n"
                    "Rules:\n"
                    "- components: 4-8 items, each with a single clear responsibility\n"
                    "- data_flow: 3-6 steps showing how data moves for the primary use case\n"
                    "- dependencies: list all non-obvious inter-component dependencies\n"
                    "- risks: 2-4 realistic technical risks specific to this system\n"
                    "- Output ONLY valid JSON. No markdown fences."
                ),
            },
            {"role": "user", "content": f"System definition:\n{json.dumps(normalized, indent=2)}"},
        ],
    )

    return json.loads(response.choices[0].message.content)
