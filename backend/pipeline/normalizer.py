import json

from llm import call_llm


def _build_stack_constraints(selections: dict) -> list[str]:
    constraints = [
        f"Backend selected: {selections.get('backend', 'none')}",
        f"Frontend selected: {selections.get('frontend', 'none')}",
        f"Database selected: {selections.get('database', 'none')}",
    ]
    apis = selections.get("apis") or []
    if apis:
        constraints.append(f"APIs selected: {', '.join(apis)}")
    return constraints


def _build_stack_io(selections: dict) -> list[str]:
    backend = selections.get("backend", "none")
    frontend = selections.get("frontend", "none")
    database = selections.get("database", "none")

    backend_label = "FastAPI" if backend == "fastapi" else "Node/Express" if backend == "node" else "Backend-less"
    frontend_step = (
        "Step 1: User submits input via frontend UI"
        if frontend != "none"
        else "Step 1: Client sends HTTP request directly to the API"
    )
    steps = [
        frontend_step,
        f"Step 2: {backend_label} endpoint validates request and routes to core logic" if backend != "none" else
        "Step 2: Client-side logic validates input and calls core functions",
        "Step 3: Core logic processes the request deterministically",
    ]
    if database != "none":
        db_label = "Postgres" if database == "postgres" else "Firebase"
        steps.append(f"Step 4: Results persisted in {db_label}")
        steps.append("Step 5: JSON response returned")
    else:
        steps.append("Step 4: JSON response returned (no persistence)")
    return steps


def _build_data_model(selections: dict) -> list[str]:
    database = selections.get("database", "none")
    if database == "none":
        return ["No persistent data stored"]
    if database == "firebase":
        return [
            "Collection: requests {id, payload, created_at}",
            "Collection: results {id, request_id, output, created_at}",
        ]
    # default to postgres style
    return [
        "Table: requests (id, payload, created_at)",
        "Table: results (id, request_id, output, created_at)",
    ]


def _strip_conflicting_assumptions(assumptions: list[str], selections: dict) -> list[str]:
    backend = selections.get("backend", "none")
    frontend = selections.get("frontend", "none")
    database = selections.get("database", "none")

    filtered = []
    for item in assumptions:
        lower = item.lower()
        if frontend == "none" and any(term in lower for term in ["ui", "screen", "frontend", "interface"]):
            continue
        if database == "none" and any(term in lower for term in ["persist", "database", "storage", "db"]):
            continue
        if backend == "none" and any(term in lower for term in ["api", "endpoint", "server", "backend"]):
            continue
        filtered.append(item)
    return filtered or ["Assumptions aligned to provided stack selections"]


def normalize(idea: str, selections: dict) -> dict:
    apis_str = ", ".join(selections["apis"]) if selections["apis"] else "none"
    stack_desc = (
        f"Scope: {selections['scope']}, Backend: {selections['backend']}, "
        f"Frontend: {selections['frontend']}, APIs: {apis_str}, Database: {selections['database']}"
    )

    system_prompt = (
                    "You are a software requirements analyst. Remove vagueness from a product idea "
                    "and produce a clear, unambiguous system definition anchored to the provided stack selections (treat them as hard constraints).\n\n"
                    "Output this exact JSON structure:\n"
                    "{\n"
                    '  "system_name": "Short descriptive name (2-4 words, title case)",\n'
                    '  "purpose": "One precise sentence: what the system does and for whom",\n'
                    '  "core_features": ["concrete feature 1", "concrete feature 2", "..."],\n'
                    '  "user_types": ["user role 1", "user role 2"],\n'
                    '  "input_output": ["Step 1: user input → component → output"],\n'
                    '  "data_model": ["Entity: key fields / storage"],\n'
                    '  "constraints": ["technical constraint derived from stack selections"],\n'
                    '  "assumptions": ["explicit assumption stated as assumption"],\n'
                    '  "unknowns": ["specific open question or missing detail"]\n'
                    "}\n\n"
                    "Rules:\n"
                    "- purpose: specific (bad: 'helps users'; good: 'lets remote teams create, assign, and track tasks with real-time updates').\n"
                    "- core_features: 4-6 capabilities; each describes an action + target + outcome.\n"
                    "- input_output: 3-5 ordered strings showing how a request moves through the system (include interface, component, and response).\n"
                    "- data_model: 2-4 entries naming the main entities with 1-2 key fields; if database=none, state 'No persistent data stored'.\n"
                    "- constraints: derive directly from stack selections (e.g., FastAPI → HTTP JSON API layer; Postgres → relational schema).\n"
                    "- assumptions: 3-5 explicit statements resolving ambiguity (format 'Assuming ...').\n"
                    "- unknowns: 2-4 precise gaps/questions the idea does not answer.\n"
                    "- Use only what the idea implies; do NOT invent complex features beyond the scope.\n"
                    "- Assumptions must not contradict the stack selections.\n"
                    "- Be explicit: avoid verbs like 'handle/support' without describing the behavior.\n\n"
                    "- Output ONLY valid JSON. No markdown fences."
    )

    try:
        result = call_llm(
            f"Idea: {idea}\nStack: {stack_desc}",
            {
                "agent_name": "normalizer",
                "model": "gpt-4o",
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "system_prompt": system_prompt,
                "expect_json": True,
                "input_data": {"idea": idea, "selections": selections},
            },
        )
        # Ensure required fields exist even if LLM omits them
        for key in ("assumptions", "unknowns", "input_output", "data_model", "constraints"):
            result.setdefault(key, [])
        result.setdefault("selected_stack", {})

        return result
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        raise ValueError(f"Normalizer received invalid JSON from LLM: {e}")
