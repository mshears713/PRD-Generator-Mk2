import json
import os
from typing import Any

from openai import OpenAI

from config import USE_FAKE_LLM


AI_KEYWORDS = {"ai", "llm", "assistant", "chatbot", "summarize", "generate", "classify"}
UI_KEYWORDS = {"dashboard", "ui", "interface", "frontend", "web app", "website", "portal", "browser", "mobile"}
PERSISTENCE_KEYWORDS = {"journal", "journaling", "todo", "task", "note", "notes", "crm", "inventory"}
WORKFLOW_KEYWORDS = {"workflow", "pipeline", "multi-step", "orchestration", "agent", "async"}


def _detect_keywords(text: str, keywords: set[str]) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(k in lowered for k in keywords)


def _constraint_value(constraints: dict, key: str, default: Any = None) -> Any:
    if not constraints:
        return default
    return constraints.get(key, default)


def _constraint_summary(constraints: dict) -> str:
    if not constraints:
        return "constraints=default"
    parts = []
    for key in ("user_scale", "auth", "execution", "app_shape"):
        value = constraints.get(key)
        if value:
            parts.append(f"{key}={value}")
    data = constraints.get("data") or {}
    persistence = data.get("persistence")
    if persistence:
        parts.append(f"data.persistence={persistence}")
    return ", ".join(parts) or "constraints=default"


def _constraints_to_impact(constraints: dict) -> list[dict]:
    impacts = []
    if not constraints:
        return impacts

    user_scale = constraints.get("user_scale")
    if user_scale:
        impacts.append(
            {
                "constraint": f"user_scale={user_scale}",
                "impact": "drives how much concurrency and operational overhead the system should support",
            }
        )

    auth = constraints.get("auth")
    if auth:
        impacts.append(
            {
                "constraint": f"auth={auth}",
                "impact": "influences whether backend auth flows and session handling are required",
            }
        )

    data = constraints.get("data") or {}
    persistence = data.get("persistence")
    if persistence:
        impacts.append(
            {
                "constraint": f"data.persistence={persistence}",
                "impact": "determines whether a durable database is needed for long-term storage",
            }
        )

    execution = constraints.get("execution")
    if execution:
        impacts.append(
            {
                "constraint": f"execution={execution}",
                "impact": "shapes whether synchronous APIs or background jobs are required",
            }
        )

    app_shape = constraints.get("app_shape")
    if app_shape:
        impacts.append(
            {
                "constraint": f"app_shape={app_shape}",
                "impact": "sets the expected interaction model and orchestration complexity",
            }
        )

    return impacts


def _assumptions_from_constraints(constraints: dict) -> list[str]:
    assumptions = []
    if not constraints.get("user_scale"):
        assumptions.append("Assuming single-user usage with minimal concurrent load")
    if not constraints.get("auth"):
        assumptions.append("Assuming no authentication unless later required")
    data = constraints.get("data") or {}
    if not data.get("persistence"):
        assumptions.append("Assuming no long-term storage unless explicitly required")
    if not constraints.get("execution"):
        assumptions.append("Assuming synchronous processing unless async is specified")
    if not constraints.get("app_shape"):
        assumptions.append("Assuming a simple single-step tool unless a workflow is specified")
    if not assumptions:
        assumptions.append("All constraints provided; assuming they are final")
    return assumptions


def _requires_backend(constraints: dict, idea: str) -> bool:
    data = constraints.get("data") or {}
    persistence = data.get("persistence")
    execution = constraints.get("execution")
    auth = constraints.get("auth")
    app_shape = constraints.get("app_shape")

    if persistence == "permanent":
        return True
    if auth in {"simple", "oauth"}:
        return True
    if execution == "async":
        return True
    if app_shape in {"ai_core", "workflow"}:
        return True
    if _detect_keywords(idea, AI_KEYWORDS | WORKFLOW_KEYWORDS):
        return True
    return False


def _fake_recommender(input_data: dict) -> dict:
    idea = input_data.get("idea", "")
    constraints = input_data.get("constraints") or {}
    scaffold = input_data.get("scaffold") or {}

    user_scale = _constraint_value(constraints, "user_scale", "single")
    auth = _constraint_value(constraints, "auth")
    data = constraints.get("data") or {}
    persistence = data.get("persistence")
    execution = _constraint_value(constraints, "execution")
    app_shape = _constraint_value(constraints, "app_shape")

    ai_core = app_shape == "ai_core" or _detect_keywords(idea, AI_KEYWORDS)
    workflow = app_shape == "workflow" or _detect_keywords(idea, WORKFLOW_KEYWORDS)
    ui_needed = _detect_keywords(idea, UI_KEYWORDS) or app_shape in {"simple", "workflow"}
    requires_backend = _requires_backend(constraints, idea)

    recommended = {
        "scope": scaffold.get("preferred", {}).get("scope", "fullstack"),
        "backend": scaffold.get("preferred", {}).get("backend", "fastapi"),
        "frontend": scaffold.get("preferred", {}).get("frontend", "react"),
        "apis": scaffold.get("preferred", {}).get("apis", []),
        "database": scaffold.get("preferred", {}).get("database", "none"),
    }

    if ai_core and "openrouter" not in recommended["apis"]:
        recommended["apis"].append("openrouter")

    if persistence == "permanent" or _detect_keywords(idea, PERSISTENCE_KEYWORDS):
        recommended["database"] = "postgres"

    if user_scale == "single":
        recommended["backend"] = "fastapi"
    elif execution == "async" or workflow:
        recommended["backend"] = "node"

    if not requires_backend:
        recommended["backend"] = "none"

    if ui_needed and recommended["backend"] != "none":
        recommended["frontend"] = "react"
    elif ui_needed:
        recommended["frontend"] = "static"
    else:
        recommended["frontend"] = "none"

    if recommended["backend"] != "none" and recommended["frontend"] != "none":
        recommended["scope"] = "fullstack"
    elif recommended["backend"] != "none":
        recommended["scope"] = "backend"
    else:
        recommended["scope"] = "frontend"

    if recommended["database"] not in {"postgres", "firebase", "none"}:
        recommended["database"] = "none"

    constraint_impact = scaffold.get("constraint_impact") or _constraints_to_impact(constraints)
    if not constraint_impact:
        constraint_impact = [
            {
                "constraint": "assumption=default",
                "impact": "defaults applied because constraints were not fully specified",
            }
        ]

    assumptions = scaffold.get("assumptions") or _assumptions_from_constraints(constraints)

    missing = len([a for a in assumptions if "Assuming" in a])
    score = max(50, 90 - (missing * 8))
    confidence = {
        "score": score,
        "reason": "Confidence reflects how many constraint details were assumed versus explicitly provided.",
    }

    constraint_ref = _constraint_summary(constraints)
    system_type = "AI assistant" if ai_core else "Automation tool" if workflow else "CRUD web app"

    rationale = {
        "scope": f"Chosen scope aligns with {constraint_ref} and keeps the build aligned to the required system shape.",
        "backend": f"Backend selection fits {constraint_ref} and supports the required execution path without excess overhead.",
        "frontend": f"Frontend choice reflects {constraint_ref} and the needed user interaction surface for this idea.",
        "apis": f"API selection mirrors {constraint_ref} and only includes services required by the core workflow.",
        "database": f"Database choice matches {constraint_ref} and the persistence needs implied by the idea.",
    }

    return {
        "system_understanding": (
            f"The system serves users working on '{idea}' with {constraint_ref}. "
            "Inputs enter through a simple UI or API, are processed by the core service, and return immediate results. "
            "Computation runs on the backend when needed, with storage determined by persistence needs. "
            "The flow stays focused on the primary use case and avoids extra infrastructure not required by the constraints."
        ),
        "system_type": system_type,
        "core_system_logic": (
            "Core logic ingests the primary user input, applies the main transformation or workflow, "
            "and returns a structured response with any stored state updated if persistence is required."
        ),
        "key_requirements": [
            "Deterministic handling of the primary user workflow",
            "Clear API boundaries between input, processing, and output",
            "Constraint-aligned data storage and retrieval",
        ],
        "scope_boundaries": [
            "In scope: the primary workflow for the stated idea",
            "Out of scope: advanced analytics or multi-tenant scaling beyond the stated constraints",
            "Out of scope: complex integrations unless explicitly required",
        ],
        "phased_plan": [
            "Phase 1: Core — build the primary workflow and minimal data model",
            "Phase 2: Harden — add validation, monitoring, and edge case handling",
            "Phase 3: Extend — optional integrations or workflow enhancements",
        ],
        "recommended": recommended,
        "rationale": rationale,
        "constraint_impact": constraint_impact,
        "assumptions": assumptions,
        "confidence": confidence,
    }


def _fake_option_advisor(input_data: dict) -> dict:
    idea = input_data.get("idea", "")
    constraints = input_data.get("constraints") or {}
    field = input_data.get("field")
    value = input_data.get("value")
    recommended = input_data.get("recommended") or {}

    user_scale = _constraint_value(constraints, "user_scale", "single")
    app_shape = _constraint_value(constraints, "app_shape")
    execution = _constraint_value(constraints, "execution")
    data = constraints.get("data") or {}
    persistence = data.get("persistence")

    requires_backend = _requires_backend(constraints, idea)
    ui_needed = _detect_keywords(idea, UI_KEYWORDS) or app_shape in {"simple", "workflow"}
    requires_persistence = persistence == "permanent" or _detect_keywords(idea, PERSISTENCE_KEYWORDS)

    fit_score = 60

    if field == "backend":
        if value == "fastapi":
            fit_score = 92 if user_scale == "single" else 82
            if app_shape == "ai_core":
                fit_score += 3
        elif value == "node":
            fit_score = 70 if app_shape == "simple" else 80
            if execution == "async":
                fit_score = max(fit_score, 86)
        else:
            fit_score = 30 if requires_backend else 85

    elif field == "database":
        if value == "postgres":
            fit_score = 88 if requires_persistence else 45
        elif value == "firebase":
            fit_score = 70 if user_scale in {"single", "small"} and requires_persistence else 50
        else:
            fit_score = 25 if requires_persistence else 80

    elif field == "frontend":
        if value == "react":
            fit_score = 85 if ui_needed else 60
        elif value == "static":
            fit_score = 80 if ui_needed and app_shape == "simple" else 65
        else:
            fit_score = 30 if ui_needed else 82

    elif field == "scope":
        if value == recommended.get("scope"):
            fit_score = 88
        elif value == "fullstack" and recommended.get("scope") != "fullstack":
            fit_score = 65
        else:
            fit_score = 72

    fit_score = max(0, min(100, int(fit_score)))

    complexity_map = {
        "scope": {"frontend": "low", "backend": "medium", "fullstack": "high"},
        "backend": {"none": "low", "fastapi": "medium", "node": "medium"},
        "frontend": {"none": "low", "static": "low", "react": "medium"},
        "database": {"none": "low", "firebase": "medium", "postgres": "high"},
    }
    complexity_cost = complexity_map.get(field, {}).get(value, "medium")

    constraint_ref = _constraint_summary(constraints)
    reason = (
        f"This option fits the project because {constraint_ref} and the system behavior implied by '{idea}'."
    )

    benefits = [
        f"Aligns with {constraint_ref} while keeping the workflow focused",
        "Keeps implementation overhead proportional to the stated requirements",
    ]

    drawbacks = [
        "May require extra effort if the project scope expands beyond current constraints.",
    ]

    why_not = None
    if fit_score < 70:
        why_not = "Score below 70 because it conflicts with the stated constraints or required execution model."

    confidence = max(50, min(95, 60 + int((fit_score - 50) * 0.4)))

    return {
        "fit_score": fit_score,
        "confidence": confidence,
        "complexity_cost": complexity_cost,
        "reason": reason,
        "benefits": benefits,
        "drawbacks": drawbacks,
        "why_not_recommended": why_not,
    }


def _fake_context_advisor(input_data: dict) -> dict:
    constraints = input_data.get("constraints") or {}
    recommended = input_data.get("recommended") or {}
    constraint_ref = _constraint_summary(constraints)

    architecture = {}
    for field in ("scope", "backend", "frontend", "database"):
        choice = recommended.get(field, "none")
        architecture[field] = {
            "choice": choice,
            "reason_for_recommendation": f"Chosen because {constraint_ref} and it matches the core system needs.",
            "benefits": [
                f"Supports {constraint_ref} without adding unnecessary overhead",
                "Keeps delivery focused on the primary workflow",
            ],
            "drawbacks": [
                "May require adjustments if constraints change significantly.",
            ],
        }

    deployment = [
        {
            "name": "Render",
            "value": "render",
            "recommended": True,
            "reason_for_recommendation": "Best fit for fast delivery with minimal infrastructure overhead.",
            "benefits": ["Quick setup for a small team", "Easy scaling for early usage"],
            "drawbacks": ["Limited deep infrastructure control compared to AWS"],
            "sponsored": True,
            "sponsor_info": {
                "why_use": ["Simple deployment for the current scope", "Costs align with early-stage usage"],
                "bonus": "Free tier + simple scaling",
            },
        },
        {
            "name": "AWS",
            "value": "aws",
            "recommended": False,
            "reason_for_recommendation": "Overkill for the current constraints and scope.",
            "benefits": ["High flexibility for large-scale needs"],
            "drawbacks": ["More configuration and operational overhead"],
            "sponsored": False,
        },
        {
            "name": "Self-hosted",
            "value": "self",
            "recommended": False,
            "reason_for_recommendation": "Adds maintenance burden without clear benefit at this scale.",
            "benefits": ["Full control over environment"],
            "drawbacks": ["Requires ongoing ops work"],
            "sponsored": False,
        },
    ]

    return {"architecture": architecture, "deployment": deployment}


def _fake_normalizer(input_data: dict) -> dict:
    idea = input_data.get("idea", "")
    selections = input_data.get("selections") or {}
    system_name = "".join(word.capitalize() for word in idea.split()[:3]) or "Project"
    backend = selections.get("backend", "none")
    database = selections.get("database", "none")
    has_db = database != "none"
    io_flow = [
        "Step 1: User submits text input via frontend",
        f"Step 2: {backend.capitalize() if backend != 'none' else 'Backend'} endpoint validates request and calls core logic",
        "Step 3: Core logic processes input deterministically",
        f"Step 4: {'Result stored in Postgres and ' if has_db else ''}response returned as JSON",
    ]
    data_model = [
        "Request: id, user_input, created_at",
    ]
    if has_db:
        data_model.append("Result: id, request_id, output, created_at (stored in Postgres)")
    else:
        data_model.append("Result: transient in-memory output only")

    return {
        "system_name": system_name,
        "purpose": f"Provide a concrete implementation of '{idea}' for the target users.",
        "core_features": [
            "Primary user workflow", "Structured input validation", "Deterministic output formatting", "Basic error handling"
        ],
        "user_types": ["Primary user"],
        "input_output": io_flow,
        "data_model": data_model,
        "constraints": [
            f"Backend: {backend} defines API layer",
            f"Database: {database} selected",
            f"Frontend: {selections.get('frontend', 'none')} for user input",
        ],
        "assumptions": [
            "Assuming text-based user input only",
            "Assuming single-user concurrency",
            "Assuming no authentication unless added later",
        ],
        "unknowns": [
            "Scaling expectations not provided",
            "Latency budget unspecified",
        ],
    }


def _fake_analyzer(input_data: dict) -> dict:
    return {
        "components": [
            {"name": "API Layer", "responsibility": "Handles incoming requests and returns responses"},
            {"name": "Core Service", "responsibility": "Executes the main business logic"},
            {"name": "Data Store", "responsibility": "Persists system state when required"},
            {"name": "UI Layer", "responsibility": "Collects user input and renders results"},
        ],
        "data_flow": [
            "Step 1: User submits input via UI or API",
            "Step 2: Core service processes the input",
            "Step 3: Results are returned and stored if needed",
        ],
        "dependencies": ["API Layer calls Core Service for processing"],
        "risks": ["Ambiguous requirements could lead to rework", "Scaling assumptions may need revision"],
        "failure_points": [
            "API layer returns 500 if downstream LLM/logic errors",
            "Database unavailable leads to failed persistence (if enabled)",
        ],
        "minimal_mvp_components": [
            "FastAPI endpoint for primary action",
            "Core processing function",
            "Result persistence or in-memory store",
            "Basic UI or API client for submission",
        ],
    }


def _fake_prd_gen(input_data: dict) -> dict:
    normalized = input_data.get("normalized") or {}
    system_name = normalized.get("system_name", "System")
    content = (
        f"# {system_name} PRD\n\n"
        "## Overview\n"
        "This PRD defines the core workflow, users, and technical approach for the system. "
        "It focuses on delivering the primary value quickly with clear constraints.\n\n"
        "## Architecture\n"
        "The system uses a simple API + service layer, with optional persistence where required. "
        "Components are intentionally minimal to keep delivery fast and focused.\n\n"
        "## Components\n"
        "### API Layer\n"
        "- **Responsibility:** Receive requests and return responses\n"
        "- **Interface:** HTTP endpoints\n"
        "- **Key logic:** Validation, routing, and response formatting\n\n"
        "### Core Service\n"
        "- **Responsibility:** Execute the main business workflow\n"
        "- **Interface:** Internal service calls\n"
        "- **Key logic:** Transformation and orchestration\n\n"
        "## API Usage\n"
        "No external APIs required.\n\n"
        "## Database Design\n"
        "No persistent storage required.\n\n"
        "## Test Cases\n"
        "| Test | Input | Expected Output | Type |\n"
        "|------|-------|-----------------|------|\n"
        "| Basic flow | Valid input | Successful response | unit |\n"
        "| Validation | Missing field | Error response | unit |\n"
        "| Edge case | Large payload | Graceful handling | integration |\n"
        "| Retry | Transient issue | Successful retry | integration |\n"
        "| Security | Invalid auth | Access denied | e2e |\n"
        "| Performance | High load | Acceptable latency | e2e |\n"
    )
    return {"text": content}


def _fake_growth(input_data: dict) -> dict:
    return {
        "good": [
            {"title": "Clear core flow", "detail": "The system focuses on a single primary workflow, reducing complexity."},
            {"title": "Constraint-aligned stack", "detail": "The chosen stack maps cleanly to the execution model."},
        ],
        "warnings": [
            {"title": "Assumption risk", "detail": "Some constraints are assumed; confirm them before scaling."},
        ],
        "missing": [
            {"title": "Monitoring", "detail": "Add basic logging/metrics to detect failures early."},
        ],
        "risk_score": 45,
        "quick_wins": [
            "Add request/response logging to FastAPI",
            "Set 30s timeout around external calls",
        ],
        "blockers": [],
    }


def fake_llm_response(agent_name: str, input_data: dict) -> dict:
    if agent_name == "recommender":
        return _fake_recommender(input_data)
    if agent_name == "option_advisor":
        return _fake_option_advisor(input_data)
    if agent_name == "context_advisor":
        return _fake_context_advisor(input_data)
    if agent_name == "normalizer":
        return _fake_normalizer(input_data)
    if agent_name == "analyzer":
        return _fake_analyzer(input_data)
    if agent_name == "prd_gen":
        return _fake_prd_gen(input_data)
    if agent_name == "growth":
        return _fake_growth(input_data)
    raise ValueError(f"No fake LLM implementation for agent: {agent_name}")


def call_llm(prompt: str, schema: dict) -> dict:
    agent_name = schema.get("agent_name", "unknown")
    input_data = schema.get("input_data") or {}

    if USE_FAKE_LLM:
        return fake_llm_response(agent_name, input_data)

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    messages = []
    system_prompt = schema.get("system_prompt")
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    kwargs = {
        "model": schema.get("model", "gpt-4o"),
        "temperature": schema.get("temperature", 0.3),
        "messages": messages,
    }
    response_format = schema.get("response_format")
    if response_format is not None:
        kwargs["response_format"] = response_format

    response = client.chat.completions.create(**kwargs)

    content = response.choices[0].message.content
    if schema.get("expect_json", True):
        return json.loads(content)
    return {"text": content}
