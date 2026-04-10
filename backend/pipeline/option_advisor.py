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
        '  "fit_score": <integer 0-100 based on the scoring rubric>,\n'
        '  "relevant": <true if fit_score >= 20, false if fit_score < 20>,\n'
        '  "reason": "<one sentence: why this does or does not fit this specific project>",\n'
        '  "benefits": ["<2-3 project-specific benefits>"],\n'
        '  "drawbacks": ["<1-2 project-specific drawbacks>"]\n'
        "}\n"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a software architect evaluating technology choices for a specific project.\n\n"
                    "Your job is to determine how well a given option fits THIS specific system.\n\n"
                    "Be concise, decisive, and project-specific.\n\n"
                    "---\n\n"
                    "EVALUATION RULES\n\n"
                    "1. Fit score (0–100)\n"
                    "- 90–100: Excellent fit — aligns cleanly with constraints and system behavior\n"
                    "- 70–89: Strong fit — good choice with minor tradeoffs\n"
                    "- 40–69: Acceptable — works, but not ideal\n"
                    "- 20–39: Weak fit — significant mismatch\n"
                    "- 0–19: Poor fit — should not be used\n\n"
                    "2. Relevance\n"
                    "- If fit_score < 20 → relevant = false\n"
                    "- Otherwise → relevant = true\n\n"
                    "3. No generic statements\n"
                    "BAD: \"React is popular\"\n"
                    "GOOD: \"React helps manage dynamic UI state for this multi-step workflow interface\"\n\n"
                    "4. Tie reasoning to:\n"
                    "- user scale\n"
                    "- data types\n"
                    "- execution model\n"
                    "- app shape\n"
                    "- recommended stack context\n\n"
                    "5. Be honest\n"
                    "- Do not inflate scores\n"
                    "- If something is a bad fit, score it low\n\n"
                    "---\n\n"
                    "IMPORTANT\n\n"
                    "- \"relevant\" must match the fit_score rule (< 20 → false, otherwise → true)\n"
                    "- benefits/drawbacks must be specific to THIS system\n"
                    "- do not restate the option — explain its effect on the system\n"
                    "- Output ONLY valid JSON. No markdown. No extra text."
                ),
            },
            {"role": "user", "content": user_content},
        ],
    )

    try:
        result = json.loads(response.choices[0].message.content)
        result.setdefault("fit_score", 50)
        result["relevant"] = result["fit_score"] >= 20
        return result
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
