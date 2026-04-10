import json
import os
from openai import OpenAI
from pipeline.recommender import _format_constraints

# Static documentation URLs — injected after the LLM call to avoid hallucination.
# The LLM is never asked to produce URLs; we map them deterministically here.
_LEARN_MORE_URLS = {
    "scope": {},                                              # no canonical docs page
    "backend": {
        "fastapi": "https://fastapi.tiangolo.com/",
        "node":    "https://nodejs.org/en/docs",
    },
    "frontend": {
        "react":  "https://react.dev/",
    },
    "database": {
        "postgres": "https://www.postgresql.org/docs/",
        "firebase": "https://firebase.google.com/docs",
    },
    "deployment": {
        "render": "https://render.com/docs",
        "aws":    "https://docs.aws.amazon.com/",
    },
}


def _inject_urls(result: dict) -> dict:
    """Add learn_more_url to every architecture component and deployment option."""
    arch = result.get("architecture", {})
    for field in ("scope", "backend", "frontend", "database"):
        if field in arch:
            choice = arch[field].get("choice", "")
            arch[field]["learn_more_url"] = _LEARN_MORE_URLS.get(field, {}).get(choice)

    for dep in result.get("deployment", []):
        dep["learn_more_url"] = _LEARN_MORE_URLS["deployment"].get(dep.get("value", ""))

    return result


def get_context_advice(idea: str, constraints: dict, recommended: dict) -> dict:
    """
    Given an idea, constraints, and the chosen tech stack, generate context-specific
    benefits/drawbacks for each architecture choice and all three deployment options.

    Returns:
        {
            "architecture": { "scope": {...}, "backend": {...}, "frontend": {...}, "database": {...} },
            "deployment":   [ { Render }, { AWS }, { Self-hosted } ]
        }
    """
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    constraints_block = _format_constraints(constraints or {})
    stack_summary = (
        f"Scope: {recommended.get('scope', 'unknown')}, "
        f"Backend: {recommended.get('backend', 'unknown')}, "
        f"Frontend: {recommended.get('frontend', 'unknown')}, "
        f"Database: {recommended.get('database', 'unknown')}, "
        f"APIs: {', '.join(recommended.get('apis', [])) or 'none'}"
    )

    user_content = f"Project idea: {idea}\n\nChosen stack: {stack_summary}"
    if constraints_block:
        user_content += f"\n\n{constraints_block}"

    system_prompt = (
        "You are a software architect writing a concise, project-specific tradeoff analysis.\n\n"
        "CRITICAL: Every benefit and drawback must be specific to THIS project — no generic statements.\n\n"
        "BAD: 'FastAPI is fast'\n"
        "GOOD: 'FastAPI's async support lets your AI calls run without blocking the response queue'\n\n"
        "Tie every point to the user scale, data types, execution model, and app shape from the constraints.\n\n"
        "Output this EXACT JSON structure:\n"
        "{\n"
        '  "architecture": {\n'
        '    "scope": {\n'
        '      "choice": "<the chosen value>",\n'
        '      "reason_for_recommendation": "<one sentence: why this fits the project>",\n'
        '      "benefits": ["<2-3 project-specific benefits>"],\n'
        '      "drawbacks": ["<1-2 project-specific drawbacks>"]\n'
        '    },\n'
        '    "backend": { "choice": "...", "reason_for_recommendation": "...", "benefits": [...], "drawbacks": [...] },\n'
        '    "frontend": { "choice": "...", "reason_for_recommendation": "...", "benefits": [...], "drawbacks": [...] },\n'
        '    "database": { "choice": "...", "reason_for_recommendation": "...", "benefits": [...], "drawbacks": [...] }\n'
        '  },\n'
        '  "deployment": [\n'
        '    {\n'
        '      "name": "Render",\n'
        '      "value": "render",\n'
        '      "recommended": <true|false>,\n'
        '      "reason_for_recommendation": "<one sentence>",\n'
        '      "benefits": ["<2-3 project-specific benefits>"],\n'
        '      "drawbacks": ["<1-2 project-specific drawbacks>"],\n'
        '      "sponsored": true,\n'
        '      "sponsor_info": {\n'
        '        "why_use": ["<project-specific reason>", "<project-specific reason>"],\n'
        '        "bonus": "Free tier + simple scaling"\n'
        '      }\n'
        '    },\n'
        '    {\n'
        '      "name": "AWS",\n'
        '      "value": "aws",\n'
        '      "recommended": <true|false>,\n'
        '      "reason_for_recommendation": "<one sentence>",\n'
        '      "benefits": ["..."],\n'
        '      "drawbacks": ["..."],\n'
        '      "sponsored": false\n'
        '    },\n'
        '    {\n'
        '      "name": "Self-hosted",\n'
        '      "value": "self",\n'
        '      "recommended": <true|false>,\n'
        '      "reason_for_recommendation": "<one sentence>",\n'
        '      "benefits": ["..."],\n'
        '      "drawbacks": ["..."],\n'
        '      "sponsored": false\n'
        '    }\n'
        '  ]\n'
        '}\n\n'
        "Deployment recommendation rules (pick exactly ONE):\n"
        "- Single user OR simple/fast build OR prototype → Render recommended\n"
        "- Large audience (100+) OR complex infra requirements → AWS recommended\n"
        "- Maximum control OR cost-sensitive at sustained scale → Self-hosted recommended\n"
        "- When unclear, default to Render\n\n"
        "Exactly ONE deployment option must have \"recommended\": true. The others must be false.\n"
        "PROJECT-SPECIFIC REQUIREMENT\n\n"
        "Every benefit and drawback must reference at least one of:\n"
        "- user scale\n"
        "- execution model\n"
        "- data persistence\n"
        "- system complexity\n\n"
        "If a statement could apply to any project, it is invalid.\n\n"
        "Output ONLY valid JSON. No markdown fences. No extra text."
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )

    try:
        result = json.loads(response.choices[0].message.content)
        return _inject_urls(result)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Context advisor received invalid JSON from LLM: {e}")
