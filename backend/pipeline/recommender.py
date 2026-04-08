import json
import os
from openai import OpenAI


def get_recommendation(idea: str) -> dict:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a software architecture advisor. Given a raw idea, analyze it and output JSON.\n\n"
                    "Output this exact structure:\n"
                    "{\n"
                    '  "summary": "1-2 sentence plain-language description of what the system does",\n'
                    '  "recommended": {\n'
                    '    "scope": "fullstack",\n'
                    '    "backend": "fastapi",\n'
                    '    "frontend": "react",\n'
                    '    "apis": [],\n'
                    '    "database": "postgres"\n'
                    "  }\n"
                    "}\n\n"
                    "Rules:\n"
                    "- scope: one of: frontend, backend, fullstack\n"
                    "- backend: one of: fastapi, node, none\n"
                    "- frontend: one of: react, static, none\n"
                    "- apis: array, elements must be from: openrouter, tavily — only include if clearly needed\n"
                    "- database: one of: postgres, firebase, none\n"
                    "- Default to fullstack + fastapi + react + postgres for most web app ideas.\n"
                    "- Only include openrouter if the app clearly needs LLM/AI features.\n"
                    "- Only include tavily if the app clearly needs web search.\n"
                    "- Output ONLY valid JSON. No markdown fences."
                ),
            },
            {"role": "user", "content": f"Idea: {idea}"},
        ],
    )

    try:
        return json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Recommender received invalid JSON from LLM: {e}")
