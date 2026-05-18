from ap_skill_generator.schema import GenerateRequest, QuestionType, Subject
from ap_skill_generator.skills import QuestionSkill
from ap_skill_generator.style.pattern_loader import find_pattern, get_all_patterns, load_patterns
from ap_skill_generator.style.prompt_builder import build_style_prompt


def test_load_patterns_reads_mcq_json_files():
    patterns = load_patterns()
    assert len(patterns) >= 9
    ids = {pattern.id for pattern in patterns}
    assert "periodic_amplitude_mcq" in ids
    assert "polynomial_end_behavior_mcq" in ids
    assert "data_modeling_regression_mcq" in ids


def test_find_pattern_matches_skill_case_insensitively():
    pattern = find_pattern("", "sinusoidal functions")
    assert pattern is not None
    assert pattern.id == "periodic_amplitude_mcq"


def test_find_pattern_resolves_api_slug_aliases():
    pattern = find_pattern("", "limits")
    assert pattern is not None
    assert pattern.id == "rates_of_change_mcq"


def test_find_pattern_resolves_linear_functions_slug():
    pattern = find_pattern("", "linear-functions")
    assert pattern is not None
    assert pattern.id == "rates_of_change_mcq"


def test_find_pattern_respects_unit_when_provided():
    pattern = find_pattern("Trigonometric and Polar Functions", "Sinusoidal Functions")
    assert pattern is not None
    assert pattern.unit == "Trigonometric and Polar Functions"


def test_build_style_prompt_includes_wording_and_distractors():
    pattern = find_pattern("", "End Behavior")
    assert pattern is not None
    prompt = build_style_prompt(pattern)
    assert "which of the following statements is true" in prompt
    assert "degree parity confusion" in prompt


def test_question_skill_appends_style_prompt_for_matching_skill():
    captured_prompts = []

    class CapturingProvider:
        def complete_json(self, *, system_prompt: str, user_prompt: str):
            captured_prompts.append(user_prompt)
            return (
                {
                    "question": "Which of the following best represents the amplitude?",
                    "choices": ["A. 1", "B. 2", "C. 3", "D. 4"],
                },
                "fake-model",
            )

    skill = QuestionSkill(CapturingProvider())
    req = GenerateRequest(
        subject=Subject.AP_PRECALCULUS,
        skill="sinusoidal-functions",
        difficulty=3,
        type=QuestionType.MCQ,
    )
    skill.run(req)
    assert len(captured_prompts) == 1
    assert "AP-style MCQ guidance" in captured_prompts[0]
    assert "amplitude period confusion" in captured_prompts[0]


def test_question_skill_continues_without_pattern():
    captured_prompts = []

    class CapturingProvider:
        def complete_json(self, *, system_prompt: str, user_prompt: str):
            captured_prompts.append(user_prompt)
            return (
                {
                    "question": "What is the value of sin(0)?",
                    "choices": ["A. 0", "B. 1", "C. -1", "D. 2"],
                },
                "fake-model",
            )

    skill = QuestionSkill(CapturingProvider())
    req = GenerateRequest(
        subject=Subject.AP_PRECALCULUS,
        skill="unmapped-skill",
        difficulty=2,
        type=QuestionType.MCQ,
    )
    draft, _, repaired, _, _ = skill.run(req)
    assert draft["question"].startswith("What is the value")
    assert "AP-style MCQ guidance" not in captured_prompts[0]
    assert repaired is False
