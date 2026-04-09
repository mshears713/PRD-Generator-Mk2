import json
import os
from openai import OpenAI


def _format_constraints(constraints: dict) -> str:
    """Convert a constraints dict into a plain-English block for the LLM prompt."""
    if not constraints:
        return ""

    lines = ["System constraints (treat these as hard requirements, not suggestions):"]

    user_scale = constraints.get("user_scale")
    if user_scale == "single":
        lines.append("- Single user only — avoid multi-tenant architecture, shared state, or concurrency complexity")
    elif user_scale == "small":
        lines.append("- Small group (10–100 users) — lightweight auth and storage, no need for horizontal scaling")
    elif user_scale == "large":
        lines.append("- Larger audience (100+ users) — design for concurrency, consider CDN and caching")

    auth = constraints.get("auth")
    if auth == "none":
        lines.append("- No authentication — skip login, accounts, sessions entirely")
    elif auth == "simple":
        lines.append("- Simple auth only (email/magic link) — no OAuth, no social login")
    elif auth == "oauth":
        lines.append("- Social login required (Google OAuth or similar)")

    data = constraints.get("data") or {}
    types = data.get("types") or []
    if types and types != ["none"]:
        readable = [t for t in types if t != "none"]
        if readable:
            lines.append(f"- Data types needed: {', '.join(readable)}")
    elif "none" in types:
        lines.append("- No persistent storage — stateless, ephemeral tool")

    persistence = data.get("persistence")
    if persistence == "temporary":
        lines.append("- Temporary storage only — data does not need to survive sessions")
    elif persistence == "permanent":
        lines.append("- Long-term persistent storage required — data must be durable")

    execution = constraints.get("execution")
    if execution == "realtime":
        lines.append("- Real-time response required — instant feedback, no background jobs")
    elif execution == "short":
        lines.append("- Short processing acceptable (a few seconds) — synchronous API calls are fine")
    elif execution == "async":
        lines.append("- Background/async execution — include job queue or worker pattern")

    app_shape = constraints.get("app_shape")
    if app_shape == "simple":
        lines.append("- Simple tool shape: single input → single output — keep architecture minimal")
    elif app_shape == "ai_core":
        lines.append("- AI-powered core: LLM or ML is the primary logic, not just a helper")
    elif app_shape == "workflow":
        lines.append("- Multi-step workflow: include orchestration, pipeline stages, or agent logic")

    return "\n".join(lines)


def get_recommendation(idea: str, constraints: dict = None) -> dict:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    constraints_block = _format_constraints(constraints or {})
    user_content = f"Idea: {idea}"
    if constraints_block:
        user_content = f"{constraints_block}\n\nIdea: {idea}"

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior software architect helping a non-expert choose a strong, practical system design.\n\n"
                    "If system constraints are provided, they are HARD REQUIREMENTS. Apply them directly — do not offer alternatives.\n\n"
                    "Your job:\n"
                    "1. Interpret the idea and constraints together\n"
                    "2. Commit to ONE recommended architecture — be decisive\n"
                    "3. Explain your reasoning clearly\n"
                    "4. Define clear scope boundaries (what's in, what's out)\n"
                    "5. Propose a phased build plan\n\n"
                    "Output this EXACT JSON structure:\n"
                    "{\n"
                    '  "system_understanding": "4-6 sentences that must cover: (1) what the system does and for whom, (2) how data flows through it, (3) where processing happens (browser, server, or background job), and (4) whether data is stored persistently — reflect any constraints that were provided (e.g. async execution, file handling, single-user scope)",\n'
                    '  "system_type": "short label: CRUD web app | AI assistant | data dashboard | automation tool | etc.",\n'
                    '  "core_system_logic": "1-2 sentences: what the system actually does under the hood — the engine",\n'
                    '  "key_requirements": ["3-6 concrete technical requirements inferred from idea + constraints"],\n'
                    '  "scope_boundaries": ["concise boundary note 1", "concise boundary note 2", ...],\n'
                    '  "phased_plan": [\n'
                    '    "Phase 1: Core — <what to build first>",\n'
                    '    "Phase 2: <next increment>",\n'
                    '    "Phase 3: <optional extensions>"\n'
                    "  ],\n"
                    '  "recommended": {\n'
                    '    "scope": "frontend | backend | fullstack",\n'
                    '    "backend": "fastapi | node | none",\n'
                    '    "frontend": "react | static | none",\n'
                    '    "apis": [],\n'
                    '    "database": "postgres | firebase | none"\n'
                    "  },\n"
                    '  "rationale": {\n'
                    '    "scope": "why this scope given the constraints",\n'
                    '    "backend": "why this backend",\n'
                    '    "frontend": "why this frontend",\n'
                    '    "apis": "why APIs were included or excluded",\n'
                    '    "database": "why this database choice fits"\n'
                    "  }\n"
                    "}\n\n"
                    "Stack rules:\n"
                    "- scope: frontend | backend | fullstack\n"
                    "- backend: fastapi | node | none\n"
                    "- frontend: react | static | none\n"
                    "- apis: only 'openrouter' if LLM is core, only 'tavily' if web search is needed\n"
                    "- database: postgres | firebase | none\n\n"
                    "Important:\n"
                    "- scope_boundaries: array of 3–5 strings, each a short sentence stating one in-scope or out-of-scope boundary\n"
                    "- Constraints override defaults — if auth=none, do not include auth in any field\n"
                    "- Be decisive and specific — no 'it depends' without a clear recommendation\n"
                    "- Output ONLY valid JSON. No markdown fences."
                ),
            },
            {"role": "user", "content": user_content},
        ],
    )

    try:
        return json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Recommender received invalid JSON from LLM: {e}")
