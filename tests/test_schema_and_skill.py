import pytest
from pydantic import ValidationError

from ap_skill_generator.schema import GenerateRequest, GeneratedItem, Metadata, QuestionType, Subject
from ap_skill_generator.skills import AnswerSkill, QuestionSkill, SkillValidationError


class FakeProvider:
    def __init__(self, payloads):
        self.payloads = payloads
        self.i = 0

    def complete_json(self, *, system_prompt: str, user_prompt: str):
        payload = self.payloads[self.i]
        self.i += 1
        return payload, "fake-model"

    def pop_token_usage(self):
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def test_schema_mcq_rejects_wrong_choice_count():
    with pytest.raises(ValidationError):
        GeneratedItem(
            question="x" * 15,
            choices=["A", "B"],
            answer="A",
            explanation="x" * 15,
            metadata=Metadata(
                subject=Subject.AP_PRECALCULUS,
                skill="functions",
                difficulty=2,
                type=QuestionType.MCQ,
            ),
        )


def test_question_skill_mcq_success():
    provider = FakeProvider(
        [
            {
                "question": "If f(x)=x^2, what is f(3)?",
                "choices": ["A. 3", "B. 6", "C. 9", "D. 12"],
            }
        ]
    )
    skill = QuestionSkill(provider)
    req = GenerateRequest(
        subject=Subject.AP_PRECALCULUS,
        skill="functions",
        difficulty=2,
        type=QuestionType.MCQ,
    )
    item, model_id, repaired, attempts, repair_classes = skill.run(req)
    assert item["question"].startswith("If f(x)")
    assert model_id == "fake-model"
    assert repaired is False
    assert attempts == 1
    assert repair_classes == []


def test_question_skill_repair_loop():
    provider = FakeProvider(
        [
            {
                "question": "Bad payload",
                "choices": ["A", "B"],
                "answer": "A",
                "explanation": "Too short",
            },
            {
                "question": "If x approaches 2, what is x+3?",
                "choices": ["A. 3", "B. 4", "C. 5", "D. 6"],
            },
        ]
    )
    skill = QuestionSkill(provider)
    req = GenerateRequest(
        subject=Subject.AP_PRECALCULUS,
        skill="limits",
        difficulty=3,
        type=QuestionType.MCQ,
    )
    item, _, repaired, attempts, repair_classes = skill.run(req)
    assert repaired is True
    assert item["choices"][2].startswith("C.")
    assert attempts >= 2
    assert repair_classes


def test_answer_skill_rejects_invalid_mcq_letter():
    provider = FakeProvider([{"answer": "E"}, {"answer": "B"}])
    skill = AnswerSkill(provider)
    req = GenerateRequest(
        subject=Subject.AP_PRECALCULUS,
        skill="limits",
        difficulty=2,
        type=QuestionType.MCQ,
    )
    answer, model_id, attempts = skill.run(req, "What is 2+2?", ["A. 3", "B. 4", "C. 5", "D. 6"])
    assert answer == "B"
    assert attempts == 2
