from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Literal

from ..computation.verifier import verify_answer
from ..evaluation import item_passes_schema
from ..providers import LLMProvider
from ..schema import GeneratedItem, QuestionType
from ..visuals import check_visual_semantics, validate_visual
from .skill_spec import SkillSpec

FailureTag = Literal[
    "schema_break",
    "answer_mismatch",
    "ambiguous_question",
    "weak_distractor",
    "non_ap_style",
    "computation_mismatch",
    "unverifiable_calculation",
    "unrealistic_distractor",
    "missing_visual",
    "invalid_visual_spec",
    "visual_not_referenced",
    "chart_data_too_sparse",
    "non_monotonic_x",
    "duplicate_categories",
    "insufficient_variance",
]

_EXPLANATION_ANSWER_PATTERNS = [
    re.compile(r"\bcorrect answer is\s+([A-D])\b", re.IGNORECASE),
    re.compile(r"\banswer is\s+([A-D])\b", re.IGNORECASE),
    re.compile(r"\boption\s+([A-D])\b(?:\s+is|\s+correct)", re.IGNORECASE),
    re.compile(r"\bchoice\s+([A-D])\b(?:\s+is|\s+correct)", re.IGNORECASE),
    re.compile(r"\btherefore,?\s+([A-D])\b", re.IGNORECASE),
]

_AP_STYLE_MARKERS = (
    "figure",
    "table",
    "experiment",
    "data",
    "results",
    "hypothesis",
    "control",
    "variable",
    "graph",
)


@dataclass
class EvalResult:
    passed: bool
    failure_tags: list[str] = field(default_factory=list)
    rationale: str = ""


def _check_schema(item: GeneratedItem) -> list[str]:
    if item_passes_schema(item):
        return []
    return ["schema_break"]


def _check_answer_consistency(item: GeneratedItem) -> list[str]:
    if item.metadata.type != QuestionType.MCQ:
        return []

    answer = item.answer.strip().upper()
    if answer not in {"A", "B", "C", "D"}:
        return ["answer_mismatch"]

    explanation = item.explanation
    for pattern in _EXPLANATION_ANSWER_PATTERNS:
        match = pattern.search(explanation)
        if match and match.group(1).upper() != answer:
            return ["answer_mismatch"]
    return []


def _check_weak_distractors(item: GeneratedItem, spec: SkillSpec) -> list[str]:
    if item.calculation_required:
        return []
    if item.metadata.type != QuestionType.MCQ or not spec.distractor_patterns:
        return []

    answer = item.answer.strip().upper()
    wrong_choices = []
    for choice in item.choices:
        letter = choice.strip()[:1].upper()
        if letter and letter != answer:
            wrong_choices.append(choice.lower())

    if not wrong_choices:
        return ["weak_distractor"]

    keywords: set[str] = set()
    for pattern in spec.distractor_patterns:
        keywords.add(pattern.id.replace("_", " "))
        for token in re.findall(r"[a-z]{4,}", pattern.failure_mode.lower()):
            keywords.add(token)
        for hint in pattern.generation_hints:
            for token in re.findall(r"[a-z]{4,}", hint.lower()):
                keywords.add(token)

    for choice_text in wrong_choices:
        if any(keyword in choice_text for keyword in keywords):
            return []
    return ["weak_distractor"]


def _check_ap_style(item: GeneratedItem, spec: SkillSpec) -> list[str]:
    if item.calculation_required:
        return []
    question_lower = item.question.lower()
    if any(marker in question_lower for marker in _AP_STYLE_MARKERS):
        return []

    requires_data = any(
        any(token in stem.lower() for token in ("figure", "table", "data", "results", "graph"))
        for archetype in spec.question_archetypes
        for stem in archetype.stem_patterns
    )
    if requires_data:
        return ["non_ap_style"]
    return []


def _check_ambiguity(item: GeneratedItem, provider: LLMProvider | None) -> list[str]:
    if item.metadata.type != QuestionType.MCQ or provider is None:
        return []

    prompt = (
        "Evaluate whether this MCQ has exactly one defensible correct answer.\n"
        f"Question: {item.question}\n"
        f"Choices: {json.dumps(item.choices)}\n"
        f"Labeled answer: {item.answer}\n"
        'Return JSON only: {"ambiguous": true|false, "rationale": "..."}'
    )
    try:
        payload, _ = provider.complete_json(system_prompt="You are a strict MCQ reviewer.", user_prompt=prompt)
    except Exception:  # noqa: BLE001
        return []

    if payload.get("ambiguous") is True:
        return ["ambiguous_question"]
    return []


def _check_computation(item: GeneratedItem) -> list[str]:
    if not item.calculation_required:
        return []
    result = verify_answer(item)
    return result.failure_tags


def _check_visual(item: GeneratedItem, spec: SkillSpec) -> list[str]:
    if spec.visual is None or not spec.visual.enabled:
        return []

    tags: list[str] = []
    visual = item.visual

    if spec.visual.required and visual is None:
        return ["missing_visual"]

    if visual is None:
        return []

    try:
        validated = validate_visual(visual.model_dump())
    except Exception:  # noqa: BLE001
        return ["invalid_visual_spec"]

    if validated is None:
        return ["invalid_visual_spec"]

    allowed_types = spec.visual.allowed_chart_types
    if allowed_types and validated.chart_type not in allowed_types:
        tags.append("invalid_visual_spec")

    if len(validated.data) < 2:
        tags.append("chart_data_too_sparse")

    if not validated.title.strip() or not validated.x_label.strip() or not validated.y_label.strip():
        tags.append("invalid_visual_spec")

    question_lower = item.question.lower()
    if not any(marker in question_lower for marker in _AP_STYLE_MARKERS):
        tags.append("visual_not_referenced")

    tags.extend(check_visual_semantics(validated))
    return list(dict.fromkeys(tags))


def run_basic_evaluators(
    item: GeneratedItem,
    spec: SkillSpec | None,
    provider: LLMProvider | None = None,
) -> EvalResult:
    if spec is None:
        return EvalResult(passed=True, rationale="no SkillSpec loaded")

    tags: list[str] = []
    tags.extend(_check_schema(item))
    tags.extend(_check_computation(item))
    tags.extend(_check_answer_consistency(item))
    tags.extend(_check_weak_distractors(item, spec))
    tags.extend(_check_ap_style(item, spec))
    tags.extend(_check_visual(item, spec))
    tags.extend(_check_ambiguity(item, provider))

    unique_tags = list(dict.fromkeys(tags))
    passed = len(unique_tags) == 0
    rationale = "all basic evaluators passed" if passed else f"failed: {', '.join(unique_tags)}"
    return EvalResult(passed=passed, failure_tags=unique_tags, rationale=rationale)
