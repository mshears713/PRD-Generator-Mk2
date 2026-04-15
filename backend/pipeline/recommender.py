import json

from llm import call_llm
from pipeline.api_candidate_selector import select_api_candidates


def _format_constraints(constraints: dict, derived: dict | None = None) -> str:
    """Convert a constraints dict into a plain-English block for the LLM prompt."""
    constraints = constraints or {}
    derived = derived or {}

    lines: list[str] = []

    system_lines = ["System constraints (treat these as hard requirements, not suggestions):"]

    user_scale = constraints.get("user_scale")
    if user_scale == "single":
        system_lines.append("- Single user only — avoid multi-tenant architecture, shared state, or concurrency complexity")
    elif user_scale == "small":
        system_lines.append("- Small group (10–100 users) — lightweight auth and storage, no need for horizontal scaling")
    elif user_scale == "large":
        system_lines.append("- Larger audience (100+ users) — design for concurrency, consider CDN and caching")

    auth = constraints.get("auth")
    if auth == "none":
        system_lines.append("- No authentication — skip login, accounts, sessions entirely")
    elif auth == "simple":
        system_lines.append("- Simple auth only (email/magic link) — no OAuth, no social login")
    elif auth == "oauth":
        system_lines.append("- Social login required (Google OAuth or similar)")

    data = constraints.get("data") or {}
    types = data.get("types") or []
    if types and types != ["none"]:
        readable = [t for t in types if t != "none"]
        if readable:
            system_lines.append(f"- Data types needed: {', '.join(readable)}")
    elif "none" in types:
        system_lines.append("- No persistent storage — stateless, ephemeral tool")

    persistence = data.get("persistence")
    if persistence == "temporary":
        system_lines.append("- Temporary storage only — data does not need to survive sessions")
    elif persistence == "permanent":
        system_lines.append("- Long-term persistent storage required — data must be durable")

    execution = constraints.get("execution")
    if execution == "realtime":
        system_lines.append("- Real-time response required — instant feedback, no background jobs")
    elif execution == "short":
        system_lines.append("- Short processing acceptable (a few seconds) — synchronous API calls are fine")
    elif execution == "async":
        system_lines.append("- Background/async execution — include job queue or worker pattern")

    app_shape = constraints.get("app_shape")
    if app_shape == "simple":
        system_lines.append("- Simple tool shape: single input → single output — keep architecture minimal")
    elif app_shape == "ai_core":
        system_lines.append("- AI-powered core: LLM or ML is the primary logic, not just a helper")
    elif app_shape == "workflow":
        system_lines.append("- Multi-step workflow: include orchestration, pipeline stages, or agent logic")

    testing = constraints.get("testing")
    if testing is True:
        system_lines.append("- Testing support requested — include platform-assisted testing when relevant")

    derived_lines = []
    for key in ("interaction_mode", "integration_level", "output_type", "automation_level"):
        value = derived.get(key)
        if value:
            derived_lines.append(f"- {key}={value}")

    if len(system_lines) > 1:
        lines.extend(system_lines)

    if derived_lines:
        if lines:
            lines.append("")
        lines.append("Derived context (treat these as hard requirements):")
        lines.extend(derived_lines)

    return "\n".join(lines)


def _detect_keywords(text: str, keywords: list[str]) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(k in lowered for k in keywords)


def _build_decision_scaffold(idea: str, constraints: dict) -> dict:
    """Return a minimal scaffold without pre-imposed architecture forcing."""
    return {
        "note": "No pre-imposed architectural constraints. Model must decide based on idea and constraints."
    }


def _enforce_stack_consistency(recommended: dict, scaffold: dict) -> dict:
    """No-op: preserve model-selected stack values as-is."""
    return recommended or {}


def _compute_confidence(scaffold: dict) -> dict:
    assumptions = scaffold.get("assumptions", [])
    missing = len(assumptions)
    score = 85
    if missing >= 5:
        score = 55
    elif missing >= 3:
        score = 65
    elif missing >= 1:
        score = 75

    reason = (
        "High because constraints map directly to a straightforward architecture."
        if score >= 80
        else "Medium because some constraints are unspecified and require assumptions."
        if score >= 65
        else "Lower because multiple constraints are missing, so key assumptions were required."
    )
    return {"score": score, "reason": reason}


def get_recommendation(
    idea: str,
    constraints: dict = None,
    derived: dict | None = None,
    feedback: str | None = None,
) -> dict:
    working_idea = idea or ""
    feedback = (feedback or "").strip()
    if feedback:
        working_idea = f"{working_idea}\n\nUser feedback:\n{feedback}"

    constraints_block = _format_constraints(constraints or {}, derived=derived)
    scaffold = _build_decision_scaffold(working_idea, constraints or {})
    user_content = f"Idea: {working_idea}"
    if constraints_block:
        user_content = f"{constraints_block}\n\nIdea: {working_idea}"
    scaffold_block = (
        "Decision scaffold:\n"
        f"- {scaffold.get('note', 'No pre-imposed architectural constraints.')}\n"
    )
    user_content = f"{scaffold_block}\n\n{user_content}"

    system_prompt = (
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
                    "- Do not say things like \"this is scalable\", \"flexible\", \"modern\", or \"commonly used\".\n"
                    "- Explain choices in terms of how the system behaves.\n\n"
                    "5. Internal consistency\n"
                    "- All chosen components must logically work together.\n"
                    "- Do not produce invalid combinations unless strongly justified.\n"
                    "- Ensure the system could realistically be built as described.\n\n"
                    "6. Anti-generic enforcement\n"
                    "- Each rationale field must reference at least one concrete project detail.\n"
                    "- Each rationale field must mention a constraint or derived requirement.\n"
                    "- Reject generic filler or restating the option name.\n\n"
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
                    "CONSTRAINT IMPACT REQUIREMENTS\n\n"
                    "- You must output a constraint_impact list.\n"
                    "- Every provided constraint must appear at least once.\n"
                    "- Each impact must describe how it changes a design decision.\n\n"
                    "ASSUMPTIONS\n\n"
                    "- Provide explicit assumptions for any missing constraint info.\n\n"
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
                    '  "constraint_impact": [\n'
                    '    {"constraint": "execution=async", "impact": "requires background job handling, influences backend choice"}\n'
                    "  ],\n"
                    '  "assumptions": ["Assuming single-user usage with no concurrent load"],\n'
                    '  "confidence": {"score": 0, "reason": "Explain why this score fits"}\n'
                    "}\n\n"
                    "---\n\n"
                    "STACK RULES\n\n"
                    "- scope: frontend | backend | fullstack\n"
                    "- backend: fastapi | node | none\n"
                    "- frontend: react | static | none\n"
                    "- apis: choose only APIs/tools that directly support a core requirement; prefer the curated registry options provided in the scaffold context.\n"
                    "- database: postgres | firebase | none\n\n"
                    "---\n\n"
                    "IMPORTANT\n\n"
                    "- scope_boundaries must be concrete and specific\n"
                    "- Constraints override defaults (e.g. auth=none → no auth anywhere)\n"
                    "- Use the decision scaffold to limit choices; do not invent options outside it\n"
                    "- The system must be internally consistent\n"
                    "- Output ONLY valid JSON. No markdown. No extra text."
    )

    try:
        result = call_llm(
            user_content,
            {
                "agent_name": "recommender",
                "model": "gpt-4o",
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "system_prompt": system_prompt,
                "expect_json": True,
                "input_data": {"idea": idea, "constraints": constraints or {}, "scaffold": scaffold},
            },
        )
        result["recommended"] = _enforce_stack_consistency(result.get("recommended", {}), scaffold)
        if not result.get("assumptions"):
            result["assumptions"] = scaffold.get("assumptions", [])
        confidence = result.get("confidence")
        if not isinstance(confidence, dict) or "score" not in confidence:
            result["confidence"] = _compute_confidence(scaffold)
        else:
            score = confidence.get("score", 0)
            if isinstance(score, (int, float)):
                score = max(0, min(100, int(score)))
            else:
                score = 0
            reason = confidence.get("reason") or _compute_confidence(scaffold)["reason"]
            result["confidence"] = {"score": score, "reason": reason}
        # API candidate selection (registry-driven, deterministic)
        api_candidates = select_api_candidates(idea, constraints or {})
        result["api_candidates"] = api_candidates
        selected_api_ids = [item["id"] for item in api_candidates.get("selected", [])]

        # Build concise API rationale from selector
        selected_names = [item.get("name", item["id"]) for item in api_candidates.get("selected", [])]
        rejected_names = [item.get("name", item["id"]) for item in api_candidates.get("rejected", []) if item.get("status") == "rejected"]
        constraint_hint = constraints or {}
        hint_parts = []
        if constraint_hint.get("user_scale"):
            hint_parts.append(f"user_scale={constraint_hint['user_scale']}")
        execution = constraint_hint.get("execution")
        if execution:
            hint_parts.append(f"execution={execution}")
        rationale_text = "APIs chosen for " + (", ".join(hint_parts) or "project signals")
        rationale_text += ". Selected: " + (", ".join(selected_names) or "none")
        if rejected_names:
            rationale_text += f". Not chosen: {', '.join(rejected_names[:3])}."
        if "rationale" not in result:
            result["rationale"] = {}
        result["rationale"]["apis"] = rationale_text

        return result
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Recommender received invalid JSON from LLM: {e}")
