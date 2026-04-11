import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("PYTEST_RUNNING", "1")

from pipeline.growth import generate_growth_check

FAKE_SELECTIONS = {
    "scope": "fullstack",
    "backend": "fastapi",
    "frontend": "react",
    "apis": [],
    "database": "postgres",
}


def test_returns_structured_dict():
    result = generate_growth_check("# PRD\ntest", FAKE_SELECTIONS, {})
    assert isinstance(result, dict)
    assert "good" in result
    assert "warnings" in result
    assert "missing" in result
    assert "risk_score" in result
    assert "quick_wins" in result
    assert "blockers" in result
    assert "consistency_issues" in result


def test_good_items_have_title_and_detail():
    result = generate_growth_check("# PRD\ntest", FAKE_SELECTIONS, {})
    for item in result["good"]:
        assert "title" in item
        assert "detail" in item


def test_warnings_and_missing_have_title_and_detail():
    result = generate_growth_check("# PRD\ntest", FAKE_SELECTIONS, {})
    for section in ("warnings", "missing"):
        for item in result[section]:
            assert "title" in item
            assert "detail" in item


def test_all_sections_are_lists():
    result = generate_growth_check("# PRD\ntest", FAKE_SELECTIONS, {})
    assert isinstance(result["good"], list)
    assert isinstance(result["warnings"], list)
    assert isinstance(result["missing"], list)
    assert isinstance(result["quick_wins"], list)
    assert len(result["quick_wins"]) <= 3
    assert isinstance(result["blockers"], list)
    assert isinstance(result["consistency_issues"], list)


def test_growth_respects_database_override():
    firebase = {**FAKE_SELECTIONS, "database": "firebase"}
    result = generate_growth_check("# PRD\ntest", firebase, {})
    warning_text = " ".join(item["detail"] for item in result["warnings"])
    assert "Firebase" in warning_text
