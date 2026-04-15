import json

from llm import call_llm


STACK_UI_TERMS = ["ui", "interface", "screen", "page", "frontend", "react"]
STACK_DB_TERMS = ["db", "database", "persist", "storage", "postgres", "firebase", "table", "collection", "record"]
STACK_API_TERMS = ["api", "endpoint", "server", "backend", "fastapi", "node", "express"]


def check_stack_consistency(selections: dict, normalized_output: dict) -> list[str]:
    """Detect obvious mismatches between selected stack and normalized description."""
    issues = []
    frontend = (selections.get("frontend") or "none").lower()
    backend = (selections.get("backend") or "none").lower()
    database = (selections.get("database") or "none").lower()

    features = " ".join(normalized_output.get("core_features") or [])
    io = " ".join(normalized_output.get("input_output") or [])
    data_model = " ".join(normalized_output.get("data_model") or [])
    constraints = " ".join(normalized_output.get("constraints") or [])
    combined = " ".join([features, io, data_model, constraints]).lower()

    if frontend == "none" and any(term in combined for term in STACK_UI_TERMS):
        issues.append("Frontend set to none but UI/Frontend elements appear in normalized output.")

    if database == "none" and any(term in combined for term in STACK_DB_TERMS):
        issues.append("Database set to none but persistence/database elements appear in normalized output.")

    if backend == "none" and any(term in combined for term in STACK_API_TERMS):
        issues.append("Backend set to none but API/backend elements appear in normalized output.")

    if backend == "node" and "fastapi" in combined:
        issues.append("Backend selection is Node but normalized output references FastAPI.")

    if backend == "fastapi" and "node" in combined:
        issues.append("Backend selection is FastAPI but normalized output references Node.")

    return issues


def generate_growth_check(prd: str, selections: dict, normalized: dict | None = None) -> dict:
    apis_str = ", ".join(selections["apis"]) if selections["apis"] else "none"
    stack_desc = (
        f"Scope: {selections['scope']}, Backend: {selections['backend']}, "
        f"Frontend: {selections['frontend']}, APIs: {apis_str}, Database: {selections['database']}"
    )

    system_prompt = (
                    "You are a senior software architect reviewing a project blueprint.\n"
                    "Produce a structured Growth Check as JSON with exactly this shape:\n"
                    "{\n"
                    '  \"good\": [{\"title\": \"...\", \"detail\": \"...\"}],\n'
                    '  \"warnings\": [{\"title\": \"...\", \"detail\": \"...\"}],\n'
                    '  \"missing\": [{\"title\": \"...\", \"detail\": \"...\"}],\n'
                    '  \"risk_score\": 0,\n'
                    '  \"quick_wins\": [\"max 3 concise, high-impact fixes\"],\n'
                    '  \"blockers\": [\"items that prevent shipping or running\"],\n'
                    '  \"consistency_issues\": [\"stack/description mismatches\"]\n'
                    "}\n\n"
                    "Rules:\n"
                    '- \"good\": 2–4 items. title = the choice name (e.g. \"FastAPI + async\"). detail = 1–2 sentences explaining why it fits THIS specific system.\n'
                    '- \"warnings\": 1–3 items. title = short concern label. detail = concrete failure mode for this system.\n'
                    '- \"missing\": 1–3 items. Only flag genuinely missing pieces, not nice-to-haves. detail must explain impact.\n'
                    "- \"risk_score\": integer 0–100 (0–30 low risk, 31–70 moderate, 71–100 high). Base it on real issues only.\n"
                    "- \"quick_wins\": max length 3. Each is a specific action for THIS stack (e.g., 'Add request timeout to FastAPI client').\n"
                    "- \"blockers\": only items that currently prevent building or running the system under stated constraints.\n"
                    "- \"consistency_issues\": list of detected mismatches between selected stack and described behavior.\n"
                    "- Respect constraints: if user_scale=single, don't suggest scalability work. If database=none, don't demand persistence.\n"
                    "- Be specific to THIS system, not generic advice.\n"
                    "CONTEXT AWARENESS\n"
                    "- If the system design shows signs of uncertainty or weak assumptions, reflect that in warnings\n"
                    "- Prioritize identifying real failure modes over generic concerns\n\n"
                    "- Output ONLY the JSON object. No preamble, no markdown."
    )

    try:
        result = call_llm(
            f"Stack selections: {stack_desc}\n\nPRD:\n{prd}",
            {
                "agent_name": "growth",
                "model": "gpt-4o",
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "system_prompt": system_prompt,
                "expect_json": True,
                "input_data": {"prd": prd, "selections": selections, "normalized": normalized or {}},
            },
        )
        risk_score = result.get("risk_score", 50)
        try:
            risk_score = int(risk_score)
        except (TypeError, ValueError):
            risk_score = 50
        result["risk_score"] = max(0, min(100, risk_score))

        quick_wins = result.get("quick_wins") or []
        result["quick_wins"] = list(quick_wins)[:3]

        blockers = result.get("blockers") or []
        result["blockers"] = list(blockers)

        # Ensure required list fields exist even if the LLM omitted them
        for key in ("good", "warnings", "missing"):
            if key not in result or not isinstance(result[key], list):
                result[key] = []

        # Consistency issues
        result["consistency_issues"] = check_stack_consistency(selections, normalized or {})

        return result
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        raise ValueError(f"Growth check received invalid JSON from LLM: {e}")
