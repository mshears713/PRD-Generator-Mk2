import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.question_generator import FIXED_QUESTION_IDS, generate_dynamic_questions


def test_generate_dynamic_questions_returns_two_valid_questions():
    questions = generate_dynamic_questions("An automation that exports a CSV report to Google Drive on a schedule")
    assert isinstance(questions, list)
    assert len(questions) == 2

    ids = set()
    for q in questions:
        assert isinstance(q, dict)
        assert "id" in q and isinstance(q["id"], str)
        assert q["id"] not in FIXED_QUESTION_IDS
        assert q["id"] not in ids
        ids.add(q["id"])

        assert "question" in q and isinstance(q["question"], str) and q["question"].strip()
        assert "options" in q and isinstance(q["options"], list)
        assert 2 <= len(q["options"]) <= 4

        for opt in q["options"]:
            assert isinstance(opt, dict)
            assert isinstance(opt.get("label"), str) and opt["label"].strip()
            assert isinstance(opt.get("value"), str) and opt["value"].strip()
            te = opt.get("technical_effect") or {}
            assert isinstance(te.get("explanation"), str) and te["explanation"].strip()
            impacts = te.get("constraint_impacts")
            assert isinstance(impacts, list)
            assert len(impacts) > 0
            assert all(isinstance(i, str) and i.strip() for i in impacts)


def test_generate_dynamic_questions_always_returns_exactly_two():
    for idea in ["", "A simple landing page", "AI chatbot", "Slack integration", "Scheduled sync"]:
        questions = generate_dynamic_questions(idea)
        assert len(questions) == 2

