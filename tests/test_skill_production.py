from pathlib import Path

import pytest

from ap_skill_generator.schema import GenerateRequest, GeneratedItem, Metadata, QuestionType, Subject
from ap_skill_generator.skill_production.compiler import compile_generation_prompt
from ap_skill_generator.skill_production.evaluators import run_basic_evaluators
from ap_skill_generator.skill_production.registry import get, list_skills, resolve_skill_id
from ap_skill_generator.skill_production.skill_spec import load_skill_spec
from ap_skill_generator.skills import QuestionSkill


class FakeProvider:
    def __init__(self, payloads):
        self.payloads = payloads
        self.i = 0

    def complete_json(self, *, system_prompt: str, user_prompt: str):
        payload = self.payloads[self.i]
        self.i += 1
        return payload, "fake-model"


def _specs_root() -> Path:
    return Path(__file__).resolve().parents[1] / "skill_specs"


def test_load_experimental_interpretation_yaml():
    path = _specs_root() / "ap_biology" / "experimental_interpretation.yaml"
    spec = load_skill_spec(path)
    assert spec.skill_id == "ap_biology.experimental_interpretation"
    assert spec.status.value == "draft"
    assert len(spec.question_archetypes) >= 2
    assert len(spec.core_reasoning.reasoning_steps) >= 3


def test_registry_get_by_full_id_and_alias():
    spec = get("ap_biology.experimental_interpretation")
    assert spec is not None
    assert spec.metadata.display_name == "Experimental Interpretation"

    alias_spec = get("experimental_interpretation")
    assert alias_spec is not None
    assert alias_spec.skill_id == "ap_biology.experimental_interpretation"

    assert resolve_skill_id("unknown-skill") is None


def test_list_bio_skills():
    skills = list_skills("ap_biology")
    assert len(skills) == 5
    assert "ap_biology.graph_interpretation" in skills


def test_compile_generation_prompt_includes_reasoning_and_archetypes():
    spec = get("ap_biology.experimental_interpretation")
    req = GenerateRequest(
        subject=Subject.AP_BIOLOGY,
        skill="ap_biology.experimental_interpretation",
        difficulty=3,
        type=QuestionType.MCQ,
    )
    prompt = compile_generation_prompt(spec, req)
    assert "ap_biology.experimental_interpretation" in prompt
    assert "Reasoning steps the item must require" in prompt
    assert "Which group serves as the control" in prompt
    assert "correlation_causation_swap" in prompt
    assert '"question": "..."' in prompt


def test_question_skill_uses_compiled_prompt_for_bio_skill():
    provider = FakeProvider(
        [
            {
                "question": "Researchers measured enzyme activity at two temperatures. Which group is the control?",
                "choices": ["A. 4 C", "B. 25 C", "C. 37 C", "D. 50 C"],
            }
        ]
    )
    skill = QuestionSkill(provider)
    req = GenerateRequest(
        subject=Subject.AP_BIOLOGY,
        skill="ap_biology.experimental_interpretation",
        difficulty=3,
        type=QuestionType.MCQ,
    )
    draft, _, repaired, attempts, _ = skill.run(req)
    assert "control" in draft["question"].lower() or "Researchers" in draft["question"]
    assert len(draft["choices"]) == 4
    assert repaired is False
    assert attempts == 1


def test_question_skill_uses_compiled_prompt_for_precalc_skill():
    provider = FakeProvider(
        [
            {
                "question": "The graph of f is shown. What is the average rate of change over [0, 4]?",
                "choices": ["A. -2", "B. 0", "C. 1", "D. 3"],
            }
        ]
    )
    skill = QuestionSkill(provider)
    req = GenerateRequest(
        subject=Subject.AP_PRECALCULUS,
        skill="rates-of-change",
        difficulty=2,
        type=QuestionType.MCQ,
    )
    draft, _, repaired, attempts, _ = skill.run(req)
    assert "rate of change" in draft["question"].lower()
    assert len(draft["choices"]) == 4
    assert repaired is False
    assert attempts == 1


def test_compile_generation_prompt_for_precalc_rates_of_change():
    spec = get("rates-of-change")
    req = GenerateRequest(
        subject=Subject.AP_PRECALCULUS,
        skill="rates-of-change",
        difficulty=2,
        type=QuestionType.MCQ,
    )
    prompt = compile_generation_prompt(spec, req)
    assert "ap_precalculus.rates_of_change" in prompt
    assert "value_vs_rate_confusion" in prompt
    assert "average rate of change" in prompt.lower()


def test_evaluator_schema_break():
    spec = get("ap_biology.experimental_interpretation")
    item = GeneratedItem.model_construct(
        question="x" * 15,
        choices=["A. one", "B. two"],
        answer="A",
        explanation="x" * 15,
        metadata=Metadata(
            subject=Subject.AP_BIOLOGY,
            skill="ap_biology.experimental_interpretation",
            difficulty=2,
            type=QuestionType.MCQ,
        ),
    )
    result = run_basic_evaluators(item, spec)
    assert result.passed is False
    assert "schema_break" in result.failure_tags


def test_evaluator_answer_mismatch():
    spec = get("ap_biology.experimental_interpretation")
    item = GeneratedItem(
        question="In an experiment, enzyme activity was measured at two pH levels. Which conclusion is supported?",
        choices=["A. pH 7 is optimal", "B. pH 5 is optimal", "C. No difference", "D. Activity decreases"],
        answer="A",
        explanation="The data show pH 7 had highest activity, so the correct answer is B because pH 5 was lower.",
        metadata=Metadata(
            subject=Subject.AP_BIOLOGY,
            skill="ap_biology.experimental_interpretation",
            difficulty=2,
            type=QuestionType.MCQ,
        ),
    )
    result = run_basic_evaluators(item, spec)
    assert result.passed is False
    assert "answer_mismatch" in result.failure_tags


def test_evaluator_ambiguity_with_provider():
    spec = get("ap_biology.experimental_interpretation")
    item = GeneratedItem(
        question="Based on Figure 1 showing enzyme rates at two temperatures, which conclusion is supported?",
        choices=["A. Rate increases", "B. Rate decreases", "C. No change", "D. Cannot determine"],
        answer="A",
        explanation="Figure 1 shows higher rates at 37 C, supporting answer A.",
        metadata=Metadata(
            subject=Subject.AP_BIOLOGY,
            skill="ap_biology.experimental_interpretation",
            difficulty=2,
            type=QuestionType.MCQ,
        ),
    )
    provider = FakeProvider([{"ambiguous": True, "rationale": "Two choices are defensible."}])
    result = run_basic_evaluators(item, spec, provider)
    assert "ambiguous_question" in result.failure_tags


def test_all_bio_skill_specs_load():
    for skill_id in list_skills("ap_biology"):
        spec = get(skill_id)
        assert spec is not None
        assert spec.subject == "ap_biology"
        assert spec.question_archetypes


def test_all_precalc_skill_specs_load():
    skills = list_skills("ap_precalculus")
    assert len(skills) == 9
    for skill_id in skills:
        spec = get(skill_id)
        assert spec is not None
        assert spec.subject == "ap_precalculus"
        assert spec.question_archetypes


def test_exponential_growth_computation_config_loads():
    spec = get("ap_precalculus.exponential_growth")
    assert spec.computation is not None
    assert spec.computation.enabled is True


def test_compile_generation_prompt_includes_computation_error_models():
    spec = get("ap_precalculus.exponential_growth")
    req = GenerateRequest(
        subject=Subject.AP_PRECALCULUS,
        skill="ap_precalculus.exponential_growth",
        difficulty=3,
        type=QuestionType.MCQ,
    )
    prompt = compile_generation_prompt(spec, req)
    assert "Allowed error model IDs:" in prompt
    assert "simple_interest_instead_of_compound" in prompt
    assert "Required error models" in prompt
    assert "sign_error" in prompt
    assert "Do NOT include computed numeric answers" in prompt


def test_precalc_legacy_slug_aliases_resolve():
    assert resolve_skill_id("rates-of-change") == "ap_precalculus.rates_of_change"
    assert resolve_skill_id("log-expressions") == "ap_precalculus.logarithmic_expressions"
    assert resolve_skill_id("regression") == "ap_precalculus.data_modeling"
