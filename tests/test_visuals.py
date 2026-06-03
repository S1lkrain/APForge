from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ap_skill_generator.schema import GenerateRequest, GeneratedItem, Metadata, QuestionType, Subject
from ap_skill_generator.skill_production.compiler import compile_generation_prompt
from ap_skill_generator.skill_production.evaluators import run_basic_evaluators
from ap_skill_generator.skill_production.registry import get
from ap_skill_generator.skills import QuestionSkill, SkillValidationError
from ap_skill_generator.visuals import check_visual_semantics, validate_visual
from ap_skill_generator.visuals.schemas import LineChartSpec


def _fixtures_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "visual_failures"


def _make_item(**overrides) -> GeneratedItem:
    defaults = {
        "question": "Based on the graph, which conclusion is best supported by the data?",
        "choices": ["A. One", "B. Two", "C. Three", "D. Four"],
        "answer": "A",
        "explanation": "The graph shows an upward trend supporting answer A.",
        "metadata": Metadata(
            subject=Subject.AP_BIOLOGY,
            skill="ap_biology.graph_interpretation",
            difficulty=2,
            type=QuestionType.MCQ,
        ),
    }
    defaults.update(overrides)
    return GeneratedItem(**defaults)


def test_line_chart_with_numeric_x_parses():
    spec = validate_visual(
        {
            "type": "chart",
            "chart_type": "line",
            "title": "Activity",
            "x_label": "Time",
            "y_label": "Rate",
            "data": [{"x": 0, "y": 1}, {"x": 1, "y": 2}],
        }
    )
    assert isinstance(spec, LineChartSpec)
    assert spec.data[0].x == 0.0


def test_bar_chart_rejects_numeric_x():
    with pytest.raises(ValidationError):
        validate_visual(
            {
                "type": "chart",
                "chart_type": "bar",
                "title": "Groups",
                "x_label": "Group",
                "y_label": "Count",
                "data": [{"x": 1, "y": 2}, {"x": 2, "y": 3}],
            }
        )


def test_line_chart_rejects_string_x():
    with pytest.raises(ValidationError):
        validate_visual(
            {
                "type": "chart",
                "chart_type": "line",
                "title": "Trend",
                "x_label": "Time",
                "y_label": "Value",
                "data": [{"x": "a", "y": 1}, {"x": "b", "y": 2}],
            }
        )


def test_invalid_chart_type_fails():
    with pytest.raises(ValidationError):
        validate_visual(
            {
                "type": "chart",
                "chart_type": "pie",
                "title": "Bad",
                "x_label": "X",
                "y_label": "Y",
                "data": [{"x": 0, "y": 1}],
            }
        )


def test_graph_interpretation_prompt_includes_visual_contract():
    spec = get("ap_biology.graph_interpretation")
    req = GenerateRequest(
        subject=Subject.AP_BIOLOGY,
        skill="ap_biology.graph_interpretation",
        difficulty=3,
        type=QuestionType.MCQ,
    )
    prompt = compile_generation_prompt(spec, req)
    assert "Visual contract" in prompt
    assert '"visual":' in prompt
    assert spec.visual is not None
    assert spec.visual.enabled is True


def test_required_visual_missing_raises():
    req = GenerateRequest(
        subject=Subject.AP_BIOLOGY,
        skill="ap_biology.graph_interpretation",
        difficulty=3,
        type=QuestionType.MCQ,
    )
    draft = {
        "question": "Which conclusion is best supported by the data in the graph?",
        "choices": ["A. One", "B. Two", "C. Three", "D. Four"],
        "calculation_required": False,
    }
    with pytest.raises(SkillValidationError, match="Required visual is missing"):
        QuestionSkill._validate_draft(draft, req)


def test_generated_item_without_visual_backward_compatible():
    item = _make_item()
    assert item.visual is None


def test_evaluator_sparse_chart():
    spec = get("ap_biology.graph_interpretation")
    visual = validate_visual(
        {
            "type": "chart",
            "chart_type": "line",
            "title": "T",
            "x_label": "X",
            "y_label": "Y",
            "data": [{"x": 0, "y": 1}],
        }
    )
    item = _make_item(visual=visual)
    result = run_basic_evaluators(item, spec)
    assert "chart_data_too_sparse" in result.failure_tags


def test_evaluator_non_monotonic_line():
    spec = get("ap_biology.graph_interpretation")
    visual = validate_visual(
        {
            "type": "chart",
            "chart_type": "line",
            "title": "T",
            "x_label": "X",
            "y_label": "Y",
            "data": [{"x": 10, "y": 1}, {"x": 5, "y": 2}],
        }
    )
    item = _make_item(visual=visual)
    result = run_basic_evaluators(item, spec)
    assert "non_monotonic_x" in result.failure_tags


def test_evaluator_duplicate_bar_categories():
    spec = get("ap_biology.graph_interpretation")
    visual = validate_visual(
        {
            "type": "chart",
            "chart_type": "bar",
            "title": "T",
            "x_label": "Group",
            "y_label": "Y",
            "data": [{"x": "A", "y": 1}, {"x": "A", "y": 2}],
        }
    )
    item = _make_item(visual=visual)
    result = run_basic_evaluators(item, spec)
    assert "duplicate_categories" in result.failure_tags


def test_evaluator_collapsed_scatter():
    spec = get("ap_biology.graph_interpretation")
    visual = validate_visual(
        {
            "type": "chart",
            "chart_type": "scatter",
            "title": "T",
            "x_label": "X",
            "y_label": "Y",
            "data": [{"x": 1, "y": 2}, {"x": 1, "y": 2}],
        }
    )
    item = _make_item(visual=visual)
    result = run_basic_evaluators(item, spec)
    assert "insufficient_variance" in result.failure_tags


def test_evaluator_visual_not_referenced():
    spec = get("ap_biology.graph_interpretation")
    visual = validate_visual(
        {
            "type": "chart",
            "chart_type": "line",
            "title": "T",
            "x_label": "X",
            "y_label": "Y",
            "data": [{"x": 0, "y": 1}, {"x": 1, "y": 2}],
        }
    )
    item = _make_item(
        question="Which conclusion is best supported?",
        visual=visual,
    )
    result = run_basic_evaluators(item, spec)
    assert "visual_not_referenced" in result.failure_tags


def test_evaluator_missing_required_visual():
    spec = get("ap_biology.graph_interpretation")
    item = _make_item()
    result = run_basic_evaluators(item, spec)
    assert "missing_visual" in result.failure_tags


@pytest.mark.parametrize(
    "fixture_name",
    [
        "sparse_chart.json",
        "duplicate_x_bar.json",
        "non_monotonic_line.json",
        "visual_not_referenced.json",
        "collapsed_scatter.json",
    ],
)
def test_visual_failure_corpus_fixtures(fixture_name: str):
    spec = get("ap_biology.graph_interpretation")
    payload = json.loads((_fixtures_dir() / fixture_name).read_text(encoding="utf-8"))
    visual = validate_visual(payload["visual"]) if payload.get("visual") else None
    item = _make_item(
        question=payload["question"],
        choices=payload["choices"],
        answer=payload["answer"],
        explanation=payload["explanation"],
        visual=visual,
    )
    result = run_basic_evaluators(item, spec)
    for tag in payload["expected_tags"]:
        assert tag in result.failure_tags, f"{fixture_name}: expected {tag} in {result.failure_tags}"


def test_check_visual_semantics_line():
    spec = validate_visual(
        {
            "type": "chart",
            "chart_type": "line",
            "title": "T",
            "x_label": "X",
            "y_label": "Y",
            "data": [{"x": 0, "y": 1}, {"x": 1, "y": 2}],
        }
    )
    assert check_visual_semantics(spec) == []
