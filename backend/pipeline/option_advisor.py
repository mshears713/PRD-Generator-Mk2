import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

from pipeline.recommender import _format_constraints

# All selectable options per field
ALL_OPTIONS = {
    "scope":    ["frontend", "backend", "fullstack"],
    "backend":  ["fastapi", "node", "none"],
    "frontend": ["react", "static", "none"],
    "database": ["postgres", "firebase", "none"],
}

# Human-readable names for LLM prompts
_OPTION_NAMES = {
    "scope":    {"frontend": "Frontend Only", "backend": "Backend Only", "fullstack": "Fullstack"},
    "backend":  {"fastapi": "FastAPI", "node": "Node.js", "none": "No Backend"},
    "frontend": {"react": "React", "static": "Static HTML", "none": "No Frontend"},
    "database": {"postgres": "PostgreSQL", "firebase": "Firebase", "none": "No Database"},
}

# Static learn-more URLs injected after LLM calls (never ask LLM for URLs)
_OPTION_URLS = {
    "scope":    {},
    "backend":  {"fastapi": "https://fastapi.tiangolo.com/", "node": "https://nodejs.org/en/docs"},
    "frontend": {"react": "https://react.dev/"},
    "database": {"postgres": "https://www.postgresql.org/docs/", "firebase": "https://firebase.google.com/docs"},
}


def _evaluate_option(
    client: OpenAI,
    idea: str,
    constraints_block: str,
    stack_context: str,
    field: str,
    value: str,
) -> dict:
    """Single gpt-4o-mini call: evaluate one option for one field."""
    name = _OPTION_NAMES.get(field, {}).get(value, value)

    user_content = (
        f"Project: {idea}\n"
        f"Recommended stack: {stack_context}\n"
    )
    if constraints_block:
        user_content += f"{constraints_block}\n"
    user_content += (
        f"\nEvaluate this option for the project's {field}: {name} ({value})\n\n"
        "Return JSON:\n"
        "{\n"
        '  "relevant": <true|false — is this a reasonable option to consider for this project?>,\n'
        '  "reason": "<one sentence: why this does or does not fit this specific project>",\n'
        '  "benefits": ["<2-3 project-specific benefits>"],\n'
        '  "drawbacks": ["<1-2 project-specific drawbacks>"]\n'
        "}\n\n"
        "Rules:\n"
        "- relevant=false only for options that clearly don't fit (e.g. 'No Backend' for an AI processing tool)\n"
        "- Every benefit and drawback must be specific to THIS project, not generic\n"
        "- Output ONLY valid JSON. No markdown fences. No extra text."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a software architect evaluating technology choices for a specific project. "
                    "Be concise and project-specific."
                ),
            },
            {"role": "user", "content": user_content},
        ],
    )

    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as e:
        raise ValueError(f"option_advisor received invalid JSON for {field}/{value}: {e}")


def _inject_option_urls(architecture: dict) -> dict:
    """Deterministically add learn_more_url to each option (never from the LLM)."""
    for field, field_data in architecture.items():
        for value, option_data in field_data.get("options", {}).items():
            option_data["learn_more_url"] = _OPTION_URLS.get(field, {}).get(value)
    return architecture


def get_all_option_advice(idea: str, constraints: dict, recommended: dict) -> dict:
    """
    Run one gpt-4o-mini call per option in parallel and return per-option advice for
    every selectable field.

    Returns:
        {
            "scope":    {"recommended": "fullstack", "options": {"frontend": {...}, "backend": {...}, "fullstack": {...}}},
            "backend":  {"recommended": "fastapi",   "options": {"fastapi": {...}, "node": {...}, "none": {...}}},
            "frontend": {"recommended": "react",     "options": {...}},
            "database": {"recommended": "postgres",  "options": {...}},
        }
    """
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    constraints_block = _format_constraints(constraints or {})
    stack_context = (
        f"Scope: {recommended.get('scope', 'unknown')}, "
        f"Backend: {recommended.get('backend', 'unknown')}, "
        f"Frontend: {recommended.get('frontend', 'unknown')}, "
        f"Database: {recommended.get('database', 'unknown')}"
    )

    # Build all (field, value) tasks
    tasks = [
        (field, value)
        for field, values in ALL_OPTIONS.items()
        for value in values
    ]

    # Collect results keyed by (field, value)
    raw_results: dict[tuple, dict] = {}

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {
            executor.submit(
                _evaluate_option, client, idea, constraints_block, stack_context, field, value
            ): (field, value)
            for field, value in tasks
        }
        for future in as_completed(futures):
            field, value = futures[future]
            raw_results[(field, value)] = future.result()

    # Assemble into architecture dict
    architecture: dict = {}
    for field, values in ALL_OPTIONS.items():
        architecture[field] = {
            "recommended": recommended.get(field, ""),
            "options": {value: raw_results[(field, value)] for value in values},
        }

    return _inject_option_urls(architecture)
