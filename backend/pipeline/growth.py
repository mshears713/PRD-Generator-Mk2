import os
from openai import OpenAI


def generate_growth_check(prd: str, selections: dict) -> str:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    apis_str = ", ".join(selections["apis"]) if selections["apis"] else "none"
    stack_desc = (
        f"Scope: {selections['scope']}, Backend: {selections['backend']}, "
        f"Frontend: {selections['frontend']}, APIs: {apis_str}, Database: {selections['database']}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior software architect reviewing a project blueprint. "
                    "Produce a Growth Check — a concise, honest evaluation of the stack and design choices.\n\n"
                    "Format your output in markdown exactly like this:\n\n"
                    "## Growth Check\n\n"
                    "### ✅ Good Choices\n"
                    "- **[Choice]:** [Why it's a good fit for this specific system]\n"
                    "(2-4 items)\n\n"
                    "### ⚠️ Warnings\n"
                    "- **[Concern]:** [What could go wrong and why]\n"
                    "(1-3 items)\n\n"
                    "### ❌ Missing Components\n"
                    "- **[Missing thing]:** [What it is and why this system needs it]\n"
                    "(1-3 items — only flag genuinely missing pieces, not nice-to-haves)\n\n"
                    "Rules:\n"
                    "- Be specific to THIS system, not generic advice\n"
                    "- ✅ items explain WHY this choice fits (not just 'FastAPI is fast')\n"
                    "- ⚠️ items name concrete failure modes\n"
                    "- ❌ items flag things actually missing (auth if users exist, rate limiting if external APIs used)\n"
                    "- Output ONLY the markdown. No preamble."
                ),
            },
            {
                "role": "user",
                "content": f"Stack selections: {stack_desc}\n\nPRD:\n{prd}",
            },
        ],
    )

    return response.choices[0].message.content
