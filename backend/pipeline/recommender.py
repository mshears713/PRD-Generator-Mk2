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


def _detect_keywords(text: str, keywords: list[str]) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(k in lowered for k in keywords)


def _build_decision_scaffold(idea: str, constraints: dict) -> dict:
    """Build a deterministic, constraint-driven scaffold to bias the LLM."""
    constraints = constraints or {}
    idea_text = idea or ""

    user_scale = constraints.get("user_scale")
    auth = constraints.get("auth")
    data = constraints.get("data") or {}
    types = data.get("types") or []
    persistence = data.get("persistence")
    execution = constraints.get("execution")
    app_shape = constraints.get("app_shape")

    has_persistent_data = persistence == "permanent"
    has_any_data = (types and types != ["none"]) or has_persistent_data
    no_data = ("none" in types) or (not types and not has_persistent_data)

    async_exec = execution == "async"
    realtime_exec = execution == "realtime"
    short_exec = execution == "short"

    ai_core = app_shape == "ai_core" or _detect_keywords(
        idea_text,
        ["ai", "llm", "assistant", "chatbot", "summarize", "generate", "classify"],
    )
    workflow = app_shape == "workflow" or _detect_keywords(
        idea_text, ["workflow", "pipeline", "multi-step", "orchestration", "agent"]
    )
    simple = app_shape == "simple"

    auth_required = auth in {"simple", "oauth"}
    oauth_required = auth == "oauth"

    ui_needed = _detect_keywords(
        idea_text,
        [
            "dashboard",
            "ui",
            "interface",
            "frontend",
            "web app",
            "website",
            "portal",
            "browser",
            "mobile",
            "admin panel",
            "client portal",
        ],
    )

    api_or_service = _detect_keywords(
        idea_text, ["api", "webhook", "integration", "automation", "service"]
    )

    requires_backend = bool(
        ai_core
        or workflow
        or async_exec
        or auth_required
        or has_persistent_data
        or has_any_data
        or api_or_service
    )
    requires_frontend = bool(ui_needed or (simple and not api_or_service))

    # Allowed/required stack choices
    allowed_backend = ["fastapi", "node"] if requires_backend else ["none"]
    allowed_frontend = ["react", "static"] if requires_frontend else ["none"]
    if requires_backend and requires_frontend:
        allowed_scope = ["fullstack"]
    elif requires_backend:
        allowed_scope = ["backend"]
    elif requires_frontend:
        allowed_scope = ["frontend"]
    else:
        allowed_scope = ["frontend"]
        allowed_frontend = ["static"]

    if has_persistent_data:
        allowed_database = ["postgres", "firebase"]
    else:
        allowed_database = ["none"]

    llm_core = ai_core
    needs_search = _detect_keywords(
        idea_text, ["search the web", "web search", "latest", "news", "crawl", "scrape"]
    )
    required_apis = []
    if llm_core:
        required_apis.append("openrouter")
    if needs_search:
        required_apis.append("tavily")

    # Preferred defaults within allowed choices
    preferred_backend = "fastapi" if "fastapi" in allowed_backend else allowed_backend[0]
    if requires_backend and not ai_core and realtime_exec and "node" in allowed_backend:
        preferred_backend = "node"

    if "react" in allowed_frontend and not (simple and no_data and not auth_required):
        preferred_frontend = "react"
    else:
        preferred_frontend = allowed_frontend[0]

    if has_persistent_data:
        if realtime_exec and user_scale in {"single", "small"} and "firebase" in allowed_database:
            preferred_database = "firebase"
        else:
            preferred_database = "postgres"
    else:
        preferred_database = "none"

    if allowed_scope == ["fullstack"]:
        preferred_scope = "fullstack"
    elif allowed_scope == ["backend"]:
        preferred_scope = "backend"
    else:
        preferred_scope = "frontend"

    constraint_impact = []
    if user_scale:
        if user_scale == "single":
            constraint_impact.append(
                {
                    "constraint": "user_scale=single",
                    "impact": "bias toward a single-instance deployment and minimal concurrency handling",
                }
            )
        elif user_scale == "small":
            constraint_impact.append(
                {
                    "constraint": "user_scale=small",
                    "impact": "use lightweight auth and storage without horizontal scaling requirements",
                }
            )
        elif user_scale == "large":
            constraint_impact.append(
                {
                    "constraint": "user_scale=large",
                    "impact": "requires a server-backed architecture with durable storage and concurrency planning",
                }
            )

    if auth:
        if auth == "none":
            constraint_impact.append(
                {
                    "constraint": "auth=none",
                    "impact": "exclude login/session flows and any user account storage",
                }
            )
        elif auth == "simple":
            constraint_impact.append(
                {
                    "constraint": "auth=simple",
                    "impact": "requires basic auth handling, which implies a backend component",
                }
            )
        elif auth == "oauth":
            constraint_impact.append(
                {
                    "constraint": "auth=oauth",
                    "impact": "requires OAuth token handling and callback endpoints on the backend",
                }
            )

    if types:
        if "none" in types:
            constraint_impact.append(
                {
                    "constraint": "data.types=none",
                    "impact": "avoid persistent storage and keep the system stateless",
                }
            )
        else:
            constraint_impact.append(
                {
                    "constraint": f"data.types={','.join([t for t in types if t != 'none'])}",
                    "impact": "system must accept and validate the specified input data types",
                }
            )

    if persistence:
        if persistence == "temporary":
            constraint_impact.append(
                {
                    "constraint": "data.persistence=temporary",
                    "impact": "avoid long-term storage and prefer in-memory or short-lived data handling",
                }
            )
        elif persistence == "permanent":
            constraint_impact.append(
                {
                    "constraint": "data.persistence=permanent",
                    "impact": "requires a durable database for long-term storage",
                }
            )

    if execution:
        if execution == "realtime":
            constraint_impact.append(
                {
                    "constraint": "execution=realtime",
                    "impact": "optimize for synchronous request/response with immediate feedback",
                }
            )
        elif execution == "short":
            constraint_impact.append(
                {
                    "constraint": "execution=short",
                    "impact": "keep processing within a short synchronous request window",
                }
            )
        elif execution == "async":
            constraint_impact.append(
                {
                    "constraint": "execution=async",
                    "impact": "requires background job handling and influences backend choice",
                }
            )

    if app_shape:
        if app_shape == "simple":
            constraint_impact.append(
                {
                    "constraint": "app_shape=simple",
                    "impact": "favor a minimal interface and a single-step interaction flow",
                }
            )
        elif app_shape == "ai_core":
            constraint_impact.append(
                {
                    "constraint": "app_shape=ai_core",
                    "impact": "LLM logic is primary, so include an LLM API and server-side orchestration",
                }
            )
        elif app_shape == "workflow":
            constraint_impact.append(
                {
                    "constraint": "app_shape=workflow",
                    "impact": "multi-step orchestration requires backend coordination between stages",
                }
            )

    assumptions = []
    if not user_scale:
        assumptions.append("Assuming single-user usage with no concurrent load requirements")
    if not auth:
        assumptions.append("Assuming no authentication unless later required")
    if not types:
        assumptions.append("Assuming text-only input/output unless other data types are specified")
    if not persistence:
        assumptions.append("Assuming no long-term storage unless explicitly required")
    if not execution:
        assumptions.append("Assuming synchronous processing unless async is specified")
    if not app_shape:
        assumptions.append("Assuming a simple single-step tool unless a workflow is specified")

    return {
        "allowed": {
            "scope": allowed_scope,
            "backend": allowed_backend,
            "frontend": allowed_frontend,
            "database": allowed_database,
            "apis": required_apis,
        },
        "preferred": {
            "scope": preferred_scope,
            "backend": preferred_backend,
            "frontend": preferred_frontend,
            "database": preferred_database,
            "apis": required_apis,
        },
        "derived_requirements": {
            "requires_backend": requires_backend,
            "requires_frontend": requires_frontend,
            "llm_core": llm_core,
            "needs_search": needs_search,
            "oauth_required": oauth_required,
        },
        "constraint_impact": constraint_impact,
        "assumptions": assumptions,
    }


def _enforce_stack_consistency(recommended: dict, scaffold: dict) -> dict:
    allowed = scaffold.get("allowed", {})
    preferred = scaffold.get("preferred", {})
    rec = recommended or {}

    scope_allowed = allowed.get("scope", [])
    backend_allowed = allowed.get("backend", [])
    frontend_allowed = allowed.get("frontend", [])
    database_allowed = allowed.get("database", [])
    required_apis = allowed.get("apis", [])

    def _pick(value: str, options: list[str], fallback: str) -> str:
        if value in options:
            return value
        return fallback

    scope = _pick(rec.get("scope"), scope_allowed, preferred.get("scope"))
    backend = _pick(rec.get("backend"), backend_allowed, preferred.get("backend"))
    frontend = _pick(rec.get("frontend"), frontend_allowed, preferred.get("frontend"))
    database = _pick(rec.get("database"), database_allowed, preferred.get("database"))

    if scope == "backend":
        frontend = "none"
    elif scope == "frontend":
        backend = "none"
    elif scope == "fullstack":
        backend = _pick(backend, ["fastapi", "node"], preferred.get("backend"))
        frontend = _pick(frontend, ["react", "static"], preferred.get("frontend"))

    apis = rec.get("apis") or []
    apis = [api for api in apis if api in {"openrouter", "tavily"}]
    for api in required_apis:
        if api not in apis:
            apis.append(api)

    return {
        "scope": scope,
        "backend": backend,
        "frontend": frontend,
        "apis": apis,
        "database": database,
    }


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


def get_recommendation(idea: str, constraints: dict = None) -> dict:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    constraints_block = _format_constraints(constraints or {})
    scaffold = _build_decision_scaffold(idea, constraints or {})
    user_content = f"Idea: {idea}"
    if constraints_block:
        user_content = f"{constraints_block}\n\nIdea: {idea}"
    scaffold_block = (
        "Decision scaffold (use this to make deterministic, constraint-driven choices):\n"
        f"- Allowed scope: {', '.join(scaffold['allowed']['scope'])}\n"
        f"- Allowed backend: {', '.join(scaffold['allowed']['backend'])}\n"
        f"- Allowed frontend: {', '.join(scaffold['allowed']['frontend'])}\n"
        f"- Allowed database: {', '.join(scaffold['allowed']['database'])}\n"
        f"- Required APIs (if any): {', '.join(scaffold['allowed']['apis']) or 'none'}\n"
        f"- Preferred defaults: scope={scaffold['preferred']['scope']}, "
        f"backend={scaffold['preferred']['backend']}, "
        f"frontend={scaffold['preferred']['frontend']}, "
        f"database={scaffold['preferred']['database']}\n"
        f"- Derived requirements: {scaffold['derived_requirements']}\n"
    )
    user_content = f"{scaffold_block}\n\n{user_content}"

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
                    "- apis: include 'openrouter' ONLY if LLM is core to the system\n"
                    "- apis: include 'tavily' ONLY if web search is required\n"
                    "- database: postgres | firebase | none\n\n"
                    "---\n\n"
                    "IMPORTANT\n\n"
                    "- scope_boundaries must be concrete and specific\n"
                    "- Constraints override defaults (e.g. auth=none → no auth anywhere)\n"
                    "- Use the decision scaffold to limit choices; do not invent options outside it\n"
                    "- The system must be internally consistent\n"
                    "- Output ONLY valid JSON. No markdown. No extra text."
                ),
            },
            {"role": "user", "content": user_content},
        ],
    )

    try:
        result = json.loads(response.choices[0].message.content)
        result["recommended"] = _enforce_stack_consistency(result.get("recommended", {}), scaffold)
        result["constraint_impact"] = scaffold.get("constraint_impact", [])
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
        return result
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Recommender received invalid JSON from LLM: {e}")
