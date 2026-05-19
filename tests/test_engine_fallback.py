from unittest.mock import patch

from ap_skill_generator.engine import APGenerationEngine
from ap_skill_generator.evaluation import JudgeResult
from ap_skill_generator.harness import PolicyDecision
from ap_skill_generator.schema import GenerateRequest, QuestionType, Subject


class FakeProvider:
    def complete_json(self, *, system_prompt: str, user_prompt: str):
        if '"question": "...",' in user_prompt:
            return (
                {
                    "question": "What is the slope of y=2x+1?",
                    "choices": ["A. 1", "B. 2", "C. -2", "D. 0"],
                },
                "fake-model",
            )
        if '{"answer": "..."}' in user_prompt:
            return ({"answer": "B"}, "fake-model")
        return (
            {"explanation": "Slope is the coefficient of x, which is 2 for y=2x+1."},
            "fake-model",
        )

    def reset_token_usage(self):
        pass

    def pop_token_usage(self):
        return {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3}


def test_rejected_policy_uses_fallback_status(memory_settings):
    engine = APGenerationEngine(settings=memory_settings)
    engine.provider = FakeProvider()
    engine.question_skill.provider = engine.provider
    engine.answer_skill.provider = engine.provider
    engine.explanation_skill.provider = engine.provider

    rejected = PolicyDecision(
        status="rejected",
        failure_reason_code="COMPLIANCE_LOW",
        hard_fail=True,
        soft_fail=False,
        reasons=["COMPLIANCE_LOW"],
    )
    judge = JudgeResult(
        schema_score=100,
        consistency_score=100,
        pedagogy_score=100,
        compliance_score=100,
        overall_decision="pass",
        rationale="ok",
    )

    with patch("ap_skill_generator.engine.judge_item", return_value=judge), patch(
        "ap_skill_generator.engine.decide_policy",
        return_value=rejected,
    ):
        result = engine.generate(
            GenerateRequest(
                subject=Subject.AP_PRECALCULUS,
                skill="limits",
                difficulty=2,
                type=QuestionType.MCQ,
            )
        )

    assert result["harness"]["status"] == "fallback"
    assert result["harness"]["used_fallback"] is True
    assert "[Fallback]" in result["item"]["question"]

    result = engine.query_items()
    assert result["items"][0]["final_status"] == "fallback"
