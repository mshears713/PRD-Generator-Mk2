import json

from llm import call_llm


def generate_growth_check(prd: str, selections: dict) -> dict:
    apis_str = ", ".join(selections["apis"]) if selections["apis"] else "none"
    stack_desc = (
        f"Scope: {selections['scope']}, Backend: {selections['backend']}, "
        f"Frontend: {selections['frontend']}, APIs: {apis_str}, Database: {selections['database']}"
    )

    system_prompt = (
                    "You are a senior software architect reviewing a project blueprint.\n"
                    "Produce a structured Growth Check as JSON with exactly this shape:\n"
                    "{\n"
                    '  "good": [{"title": "...", "detail": "..."}],\n'
                    '  "warnings": [{"title": "...", "detail": "..."}],\n'
                    '  "missing": [{"title": "...", "detail": "..."}]\n'
                    "}\n\n"
                    "Rules:\n"
                    '- "good": 2–4 items. title = the choice name (e.g. "FastAPI + async"). detail = 1–2 sentences explaining why it fits THIS specific system.\n'
                    '- "warnings": 1–3 items. title = short concern label. detail = concrete failure mode for this system.\n'
                    '- "missing": 1–3 items. title = missing piece. detail = what it is and why this system needs it. Only flag genuinely missing pieces, not nice-to-haves.\n'
                    "- Be specific to THIS system, not generic advice.\n"
                    "CONTEXT AWARENESS\n"
                    "- If the system design shows signs of uncertainty or weak assumptions, reflect that in warnings\n"
                    "- Prioritize identifying real failure modes over generic concerns\n\n"
                    "- Output ONLY the JSON object. No preamble, no markdown."
    )

    try:
        return call_llm(
            f"Stack selections: {stack_desc}\n\nPRD:\n{prd}",
            {
                "agent_name": "growth",
                "model": "gpt-4o",
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "system_prompt": system_prompt,
                "expect_json": True,
                "input_data": {"prd": prd, "selections": selections},
            },
        )
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        raise ValueError(f"Growth check received invalid JSON from LLM: {e}")
