from ap_skill_generator.config import Settings
from ap_skill_generator.engine import APGenerationEngine
from ap_skill_generator.providers import OFFLINE_MODEL_ID
from ap_skill_generator.schema import GenerateRequest, QuestionType, Subject


class FakeProvider:
    def reset_token_usage(self):
        pass

    def pop_token_usage(self):
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

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
            {
                "explanation": "Slope is the coefficient of x, which is 2.",
            },
            "fake-model",
        )


def test_engine_generate_and_query():
    settings = Settings(database_url="sqlite:///:memory:")
    engine = APGenerationEngine(settings=settings)
    engine.provider = FakeProvider()
    engine.question_skill.provider = engine.provider
    engine.answer_skill.provider = engine.provider
    engine.explanation_skill.provider = engine.provider

    req = GenerateRequest(
        subject=Subject.AP_PRECALCULUS,
        skill="linear-functions",
        difficulty=2,
        type=QuestionType.MCQ,
    )
    result = engine.generate(req)
    assert "run_id" in result

    rows = engine.query_items(subject="ap_precalculus")
    assert len(rows) == 1
    assert rows[0]["answer"] == "B"


def test_engine_generate_with_empty_api_key_uses_offline_stub():
    settings = Settings(
        database_url="sqlite:///:memory:",
        openai_api_key="",
    )
    engine = APGenerationEngine(settings=settings)
    req = GenerateRequest(
        subject=Subject.AP_PRECALCULUS,
        skill="linear-functions",
        difficulty=2,
        type=QuestionType.MCQ,
    )
    result = engine.generate(req)
    assert result["item"]["metadata"]["model_id"] == OFFLINE_MODEL_ID
    assert result["item"]["answer"] == "B"
