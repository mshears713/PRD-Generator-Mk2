import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.answer_mapper import map_answers_to_constraints


def test_fixed_answers_map_to_constraints():
    mapped = map_answers_to_constraints(
        "A personal journal",
        fixed_answers={
            "for_whom": "single",
            "accounts": "none",
            "remember_over_time": "permanent",
            "reliability_vs_speed": "balanced",
        },
        dynamic_answers={},
    )
    constraints = mapped["constraints"]
    assert constraints["user_scale"] == "single"
    assert constraints["auth"] == "none"
    assert constraints["data"]["persistence"] == "permanent"
    assert constraints["execution"] == "short"


def test_dynamic_answers_populate_derived_and_can_adjust_constraints():
    mapped = map_answers_to_constraints(
        "Export reports and run nightly",
        fixed_answers={},
        dynamic_answers={
            "interaction_style": "step",
            "integration_needs": "many",
            "output_type": "file_export",
            "automation_level": "scheduled",
        },
    )
    constraints = mapped["constraints"]
    derived = mapped["derived"]

    assert derived["interaction_mode"] == "step"
    assert derived["integration_level"] == "many"
    assert derived["output_type"] == "file_export"
    assert derived["automation_level"] == "scheduled"

    assert "files" in constraints["data"]["types"]
    assert constraints["execution"] == "async"
    assert constraints["app_shape"] == "workflow"


def test_unknown_dynamic_answers_are_ignored():
    mapped = map_answers_to_constraints(
        "Anything",
        fixed_answers={},
        dynamic_answers={"unknown_question": "whatever", "output_type": "onscreen"},
    )
    derived = mapped["derived"]
    assert "unknown_question" not in derived
    assert derived["output_type"] == "onscreen"

