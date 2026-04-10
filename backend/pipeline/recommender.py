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
                    "You are a senior software architect helping a builder quickly arrive at a clear, practical system design.\n\n"
                    "This is not a brainstorming task. You must make decisions.\n\n"
                    "---\n\n"
                    "CRITICAL RULES\n\n"
                    "1. Constraints are HARD REQUIREMENTS\n"
                    "- You must apply them directly.\n"
                    "- You are not allowed to ignore or reinterpret them.\n"
                    "- Every constraint must influence at least one part of the system design.\n\n"
                    "2. Be decisive\n"
                    "- Choose ONE architecture.\n"
                    "- Do not present multiple equal options.\n"
                    "- Do not hedge with \"it depends\".\n"
                    "- If tradeoffs exist, choose and briefly justify.\n\n"
                    "3. Prefer the simplest system that works\n"
                    "- Avoid unnecessary complexity.\n"
                    "- Do not introduce microservices, queues, or extra infra unless required by constraints.\n\n"
                    "4. No generic reasoning\n"
                    "- Every statement must tie to THIS system.\n"
                    "- Do not say things like \"this is scalable\" or \"commonly used\".\n"
                    "- Explain choices in terms of how the system behaves.\n\n"
                    "5. Internal consistency\n"
                    "- All chosen components must logically work together.\n"
                    "- Do not produce invalid combinations unless strongly justified.\n"
                    "- Ensure the system could realistically be built as described.\n\n"
                    "---\n\n"
                    "YOUR TASK\n\n"
                    "Given the idea and constraints:\n\n"
                    "1. Form a clear mental model of the system\n"
                    "2. Decide the architecture (scope, backend, frontend, APIs, database)\n"
                    "3. Explain how the system actually works (data flow, execution, storage)\n"
                    "4. Define what is explicitly IN and OUT of scope\n"
                    "5. Provide a phased plan for building\n\n"
                    "---\n\n"
                    "SYSTEM UNDERSTANDING REQUIREMENTS\n\n"
                    "The system_understanding must:\n"
                    "- Clearly state who uses the system and for what\n"
                    "- Describe how data enters, is processed, and returns\n"
                    "- Specify where computation happens (browser, server, background job)\n"
                    "- State whether data is stored and how long (temporary vs permanent)\n"
                    "- Reflect ALL relevant constraints (execution model, data types, scale)\n\n"
                    "Avoid vague descriptions. This should read like a system walkthrough.\n\n"
                    "---\n\n"
                    "RATIONALE REQUIREMENTS\n\n"
                    "Each rationale field must:\n"
                    "- Explain WHY the choice fits THIS system\n"
                    "- Reference constraints, data flow, or execution model\n"
                    "- Not restate the choice\n\n"
                    "---\n\n"
                    "CONFIDENCE\n\n"
                    "You must output a confidence score between 0 and 1.\n\n"
                    "High confidence (0.8–1.0):\n"
                    "- Idea is clear\n"
                    "- Constraints align cleanly\n"
                    "- Architecture is straightforward\n\n"
                    "Medium confidence (0.5–0.7):\n"
                    "- Some ambiguity in idea\n"
                    "- Tradeoffs between multiple reasonable approaches\n\n"
                    "Low confidence (<0.5):\n"
                    "- Missing critical details\n"
                    "- Conflicting constraints\n"
                    "- Architecture assumptions required\n\n"
                    "---\n\n"
                    "OUTPUT THIS EXACT JSON STRUCTURE:\n\n"
                    "{\n"
                    '  "system_understanding": "4-6 sentences describing how the system works in practice",\n'
                    '  "system_type": "short label: CRUD web app | AI assistant | data dashboard | automation tool | etc.",\n'
                    '  "core_system_logic": "1-2 sentences describing the core engine of the system",\n'
                    '  "key_requirements": ["3-6 concrete technical requirements derived from idea + constraints"],\n'
                    '  "scope_boundaries": ["3-5 concise in/out-of-scope statements"],\n'
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
                    '    "scope": "why this scope fits THIS system",\n'
                    '    "backend": "why this backend fits THIS system",\n'
                    '    "frontend": "why this frontend fits THIS system",\n'
                    '    "apis": "why APIs are included or not",\n'
                    '    "database": "why this database choice fits THIS system"\n'
                    "  },\n"
                    '  "confidence": 0.0\n'
                    "}\n\n"
                    "---\n\n"
                    "STACK RULES\n\n"
                    "- scope: frontend | backend | fullstack\n"
                    "- backend: fastapi | node | none\n"
                    "- frontend: react | static | none\n"
                    "- apis: include 'openrouter' ONLY if LLM is core to the system\n"
                    "- apis: include 'tavily' ONLY if web search is required\n"
                    "- database: postgres | firebase | none\n\n"
                    "---\n\n"
                    "IMPORTANT\n\n"
                    "- scope_boundaries must be concrete and specific\n"
                    "- Constraints override defaults (e.g. auth=none → no auth anywhere)\n"
                    "- The system must be internally consistent\n"
                    "- Output ONLY valid JSON. No markdown. No extra text."
                ),
            },
            {"role": "user", "content": user_content},
        ],
    )

    try:
        return json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Recommender received invalid JSON from LLM: {e}")
