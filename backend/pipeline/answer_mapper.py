from __future__ import annotations


AI_KEYWORDS = {"ai", "llm", "assistant", "chatbot", "summarize", "generate", "classify", "rag"}


def _detect_keywords(text: str, keywords: set[str]) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(k in lowered for k in keywords)


def _add_type(types_list: list[str], value: str) -> None:
    if value not in types_list:
        types_list.append(value)


def map_answers_to_constraints(idea: str, fixed_answers: dict, dynamic_answers: dict) -> dict:
    """
    Convert user-facing Quick Setup answers into the existing constraints schema,
    plus a derived context object to influence downstream reasoning.

    Returns:
        {
            "constraints": {...existing schema...},
            "derived": {...internal flags...}
        }
    """
    fixed_answers = fixed_answers or {}
    dynamic_answers = dynamic_answers or {}

    constraints = {
        "user_scale": "small",
        "auth": "none",
        "data": {"types": [], "persistence": "temporary"},
        "execution": "short",
        "app_shape": "simple",
        "testing": False,
    }
    derived: dict = {}

    # Fixed mappings
    for_whom = fixed_answers.get("for_whom")
    if for_whom in {"single", "small", "large"}:
        constraints["user_scale"] = for_whom

    accounts = fixed_answers.get("accounts")
    if accounts in {"none", "simple", "oauth"}:
        constraints["auth"] = accounts

    remember = fixed_answers.get("remember_over_time")
    if remember in {"temporary", "permanent"}:
        constraints["data"]["persistence"] = remember

    reliability = fixed_answers.get("reliability_vs_speed")
    if reliability in {"fast", "balanced", "reliable"}:
        if reliability == "reliable":
            constraints["execution"] = "async"
        else:
            constraints["execution"] = "short"

    # Dynamic mappings
    interaction = dynamic_answers.get("interaction_style")
    if interaction in {"chat", "form", "dashboard", "step"}:
        derived["interaction_mode"] = interaction
        if interaction == "step":
            if constraints.get("app_shape") != "ai_core":
                constraints["app_shape"] = "workflow"
        if interaction == "chat" and _detect_keywords(idea or "", AI_KEYWORDS):
            constraints["app_shape"] = "ai_core"

    integration = dynamic_answers.get("integration_needs")
    if integration in {"none", "some", "custom", "many"}:
        derived["integration_level"] = integration
        if integration in {"custom", "many"}:
            if constraints.get("app_shape") != "ai_core":
                constraints["app_shape"] = "workflow"

    output_type = dynamic_answers.get("output_type")
    if output_type in {"onscreen", "report", "file_export", "action"}:
        derived["output_type"] = output_type
        if output_type == "file_export":
            _add_type(constraints["data"]["types"], "files")
        else:
            _add_type(constraints["data"]["types"], "text")
        if output_type == "action":
            constraints["app_shape"] = "workflow"
            constraints["execution"] = "async"

    automation = dynamic_answers.get("automation_level")
    if automation in {"manual", "batch", "scheduled", "event"}:
        derived["automation_level"] = automation
        if automation in {"scheduled", "event"}:
            constraints["execution"] = "async"
            constraints["app_shape"] = "workflow"

    return {"constraints": constraints, "derived": derived}

