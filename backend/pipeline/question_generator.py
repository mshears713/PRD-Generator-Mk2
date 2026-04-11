from __future__ import annotations

from dataclasses import dataclass


FIXED_QUESTION_IDS = {"for_whom", "accounts", "remember_over_time", "reliability_vs_speed"}


@dataclass(frozen=True)
class _Template:
    id: str
    question: str
    options: list[dict]
    keywords: tuple[str, ...]


def _score(idea_lower: str, keywords: tuple[str, ...]) -> int:
    if not idea_lower:
        return 0
    return sum(1 for k in keywords if k in idea_lower)


def _make_templates() -> list[_Template]:
    # Keep templates closed-ended (no free text), human-friendly, and non-overlapping with fixed questions.
    return [
        _Template(
            id="interaction_style",
            question="How should people interact with it?",
            options=[
                {
                    "label": "Chat-style conversation",
                    "value": "chat",
                    "technical_effect": {
                        "explanation": "Optimizes the system around a conversational flow and quick iterative responses.",
                        "constraint_impacts": [
                            "Sets derived.interaction_mode = chat",
                            "Biases toward an assistant-style UI and state handling",
                        ],
                    },
                },
                {
                    "label": "Fill out a form and get a result",
                    "value": "form",
                    "technical_effect": {
                        "explanation": "Optimizes for a single input → single output flow with minimal UI complexity.",
                        "constraint_impacts": [
                            "Sets derived.interaction_mode = form",
                            "Biases toward a simpler request/response interaction model",
                        ],
                    },
                },
                {
                    "label": "Dashboard with filters and views",
                    "value": "dashboard",
                    "technical_effect": {
                        "explanation": "Pushes the architecture toward structured data and multiple UI states (lists, detail views, filters).",
                        "constraint_impacts": [
                            "Sets derived.interaction_mode = dashboard",
                            "Biases toward richer frontend state and data modeling",
                        ],
                    },
                },
                {
                    "label": "Step-by-step flow",
                    "value": "step",
                    "technical_effect": {
                        "explanation": "Encourages a multi-step workflow where the system tracks progress between steps.",
                        "constraint_impacts": [
                            "Sets derived.interaction_mode = step",
                            "May increase orchestration needs (multi-step workflow)",
                        ],
                    },
                },
            ],
            keywords=(
                "chat",
                "assistant",
                "wizard",
                "step",
                "workflow",
                "dashboard",
                "ui",
                "interface",
                "portal",
            ),
        ),
        _Template(
            id="integration_needs",
            question="Does it need to connect to other tools?",
            options=[
                {
                    "label": "No, it can be standalone",
                    "value": "none",
                    "technical_effect": {
                        "explanation": "Keeps the system simple by avoiding external dependencies and sync logic.",
                        "constraint_impacts": [
                            "Sets derived.integration_level = none",
                            "Avoids integration connectors and external auth flows",
                        ],
                    },
                },
                {
                    "label": "Yes, a couple of common tools",
                    "value": "some",
                    "technical_effect": {
                        "explanation": "Adds a small integration layer while keeping the overall architecture lightweight.",
                        "constraint_impacts": [
                            "Sets derived.integration_level = some",
                            "May require a small adapter layer for 1–2 services",
                        ],
                    },
                },
                {
                    "label": "Yes, a custom API connection",
                    "value": "custom",
                    "technical_effect": {
                        "explanation": "Requires explicit API contracts, error handling, and possibly background sync/retries.",
                        "constraint_impacts": [
                            "Sets derived.integration_level = custom",
                            "May require workflow/orchestration to handle integration reliability",
                        ],
                    },
                },
                {
                    "label": "Yes, lots of integrations",
                    "value": "many",
                    "technical_effect": {
                        "explanation": "Shifts the architecture toward connectors, retries, and observability to keep integrations reliable.",
                        "constraint_impacts": [
                            "Sets derived.integration_level = many",
                            "Often benefits from background processing and orchestration",
                        ],
                    },
                },
            ],
            keywords=("integrate", "integration", "api", "webhook", "slack", "notion", "google", "drive", "zapier"),
        ),
        _Template(
            id="output_type",
            question="What should it produce at the end?",
            options=[
                {
                    "label": "An answer on the screen",
                    "value": "onscreen",
                    "technical_effect": {
                        "explanation": "Optimizes for fast, direct feedback with minimal file handling.",
                        "constraint_impacts": [
                            "Sets derived.output_type = onscreen",
                            "Biases toward synchronous request/response behavior",
                        ],
                    },
                },
                {
                    "label": "A structured report",
                    "value": "report",
                    "technical_effect": {
                        "explanation": "Encourages structured outputs (sections, tables) and more deliberate formatting.",
                        "constraint_impacts": [
                            "Sets derived.output_type = report",
                            "Biases toward schemas/structured output shaping",
                        ],
                    },
                },
                {
                    "label": "A downloadable file",
                    "value": "file_export",
                    "technical_effect": {
                        "explanation": "Introduces file generation/storage concerns (formats, sizes, download links).",
                        "constraint_impacts": [
                            "Sets derived.output_type = file_export",
                            "May require file handling/storage considerations",
                        ],
                    },
                },
                {
                    "label": "An action it takes for me",
                    "value": "action",
                    "technical_effect": {
                        "explanation": "Requires the system to execute steps reliably (retries, idempotency, and auditability).",
                        "constraint_impacts": [
                            "Sets derived.output_type = action",
                            "Often benefits from background execution and orchestration",
                        ],
                    },
                },
            ],
            keywords=("export", "download", "pdf", "csv", "report", "email", "send", "post", "create", "sync"),
        ),
        _Template(
            id="automation_level",
            question="How automated should it be?",
            options=[
                {
                    "label": "Only when I click",
                    "value": "manual",
                    "technical_effect": {
                        "explanation": "Keeps execution simple and user-driven, with fewer background concerns.",
                        "constraint_impacts": [
                            "Sets derived.automation_level = manual",
                            "Avoids schedulers and event-driven processing",
                        ],
                    },
                },
                {
                    "label": "Run on a batch of items",
                    "value": "batch",
                    "technical_effect": {
                        "explanation": "Encourages handling longer runs, progress tracking, and partial failures.",
                        "constraint_impacts": [
                            "Sets derived.automation_level = batch",
                            "May benefit from chunking, retries, and progress reporting",
                        ],
                    },
                },
                {
                    "label": "Run on a schedule",
                    "value": "scheduled",
                    "technical_effect": {
                        "explanation": "Introduces scheduled execution, retries, and background job concerns.",
                        "constraint_impacts": [
                            "Sets derived.automation_level = scheduled",
                            "Often benefits from background execution and orchestration",
                        ],
                    },
                },
                {
                    "label": "Run when something changes",
                    "value": "event",
                    "technical_effect": {
                        "explanation": "Introduces event triggers, reliability, and replay/idempotency considerations.",
                        "constraint_impacts": [
                            "Sets derived.automation_level = event",
                            "Often benefits from background execution and orchestration",
                        ],
                    },
                },
            ],
            keywords=("automate", "automation", "schedule", "cron", "sync", "webhook", "event", "trigger", "monitor"),
        ),
    ]


def generate_dynamic_questions(idea: str) -> list[dict]:
    """
    Deterministically return exactly 2 closed-ended questions influenced by the idea.

    Contract:
    - exactly 2 questions
    - max 4 options per question
    - each option includes technical_effect.explanation + technical_effect.constraint_impacts
    """
    idea_lower = (idea or "").lower()
    templates = _make_templates()

    scored: list[tuple[int, _Template, int]] = [
        (idx, t, _score(idea_lower, t.keywords)) for idx, t in enumerate(templates)
    ]
    scored.sort(key=lambda x: (-x[2], x[0]))

    selected: list[_Template] = []
    for _idx, t, s in scored:
        if s <= 0:
            continue
        if t.id in FIXED_QUESTION_IDS:
            continue
        selected.append(t)
        if len(selected) == 2:
            break

    if len(selected) < 2:
        fallback_order = ["interaction_style", "output_type", "integration_needs", "automation_level"]
        by_id = {t.id: t for t in templates}
        for tid in fallback_order:
            t = by_id.get(tid)
            if not t:
                continue
            if t in selected:
                continue
            selected.append(t)
            if len(selected) == 2:
                break

    result = []
    for t in selected[:2]:
        if t.id in FIXED_QUESTION_IDS:
            continue
        options = t.options[:4]
        result.append({"id": t.id, "question": t.question, "options": options})

    # Hard guarantee.
    if len(result) != 2:
        # Fallback to known-safe templates if anything went wrong.
        by_id = {t.id: t for t in templates}
        a = by_id["interaction_style"]
        b = by_id["output_type"]
        result = [
            {"id": a.id, "question": a.question, "options": a.options[:4]},
            {"id": b.id, "question": b.question, "options": b.options[:4]},
        ]

    return result
