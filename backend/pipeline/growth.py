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
                    '  \"good\": [{\"title\": \"...\", \"detail\": \"...\"}],\n'
                    '  \"warnings\": [{\"title\": \"...\", \"detail\": \"...\"}],\n'
                    '  \"missing\": [{\"title\": \"...\", \"detail\": \"...\"}],\n'
                    '  \"risk_score\": 0,\n'
                    '  \"quick_wins\": [\"max 3 concise, high-impact fixes\"],\n'
                    '  \"blockers\": [\"items that prevent shipping or running\"]\n'
                    "}\n\n"
                    "Rules:\n"
                    '- \"good\": 2–4 items. title = the choice name (e.g. \"FastAPI + async\"). detail = 1–2 sentences explaining why it fits THIS specific system.\n'
                    '- \"warnings\": 1–3 items. title = short concern label. detail = concrete failure mode for this system.\n'
                    '- \"missing\": 1–3 items. Only flag genuinely missing pieces, not nice-to-haves. detail must explain impact.\n'
                    "- \"risk_score\": integer 0–100 (0–30 low risk, 31–70 moderate, 71–100 high). Base it on real issues only.\n"
                    "- \"quick_wins\": max length 3. Each is a specific action for THIS stack (e.g., 'Add request timeout to FastAPI client').\n"
                    "- \"blockers\": only items that currently prevent building or running the system under stated constraints.\n"
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
                "input_data": {"prd": prd, "selections": selections},
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

        return result
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        raise ValueError(f"Growth check received invalid JSON from LLM: {e}")
