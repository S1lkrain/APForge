from __future__ import annotations

from .prompts import (
    PROMPT_VERSION,
    answer_skill_prompt,
    explanation_skill_prompt,
    question_skill_prompt,
    system_prompt,
    typed_repair_prompt,
)
from .providers import LLMProvider
from .schema import GenerateRequest, GeneratedItem, Metadata, QuestionType


class SkillValidationError(RuntimeError):
    pass

_MCQ_ANSWERS = {"A", "B", "C", "D"}


class QuestionSkill:
    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def run(self, req: GenerateRequest, max_repair_attempts: int = 2) -> tuple[dict, str, bool, int, list[str]]:
        payload, model_id = self.provider.complete_json(
            system_prompt=system_prompt(),
            user_prompt=question_skill_prompt(req),
        )
        repaired = False
        repair_classes: list[str] = []
        attempts = 1
        try:
            draft = self._parse(payload)
            self._validate_draft(draft, req)
        except Exception as first_error:  # noqa: BLE001
            repaired = True
            latest_error: Exception = first_error
            latest_payload = payload
            for _ in range(max_repair_attempts):
                attempts += 1
                error_class = self._classify_error(str(latest_error))
                repair_classes.append(error_class)
                repaired_payload, model_id = self.provider.complete_json(
                    system_prompt=system_prompt(),
                    user_prompt=typed_repair_prompt(error_class, latest_payload, str(latest_error)),
                )
                try:
                    draft = self._parse(repaired_payload)
                    self._validate_draft(draft, req)
                    return draft, model_id, repaired, attempts, repair_classes
                except Exception as second_error:  # noqa: BLE001
                    latest_error = second_error
                    latest_payload = repaired_payload
            raise SkillValidationError(str(latest_error)) from latest_error
        return draft, model_id, repaired, attempts, repair_classes

    @staticmethod
    def _parse(payload: dict) -> dict:
        return {
            "question": payload["question"],
            "choices": payload.get("choices", []),
        }

    @staticmethod
    def _validate_draft(draft: dict, req: GenerateRequest) -> None:
        if len(draft["question"]) < 10:
            raise SkillValidationError("Question draft must be at least 10 characters")
        if req.type.value == "mcq" and len(draft["choices"]) != 4:
            raise SkillValidationError("MCQ draft requires exactly 4 choices")

    @staticmethod
    def _classify_error(error_text: str) -> str:
        lower = error_text.lower()
        if "choice" in lower or "mcq" in lower:
            return "option_repair"
        if "question" in lower or "keyerror" in lower:
            return "schema_repair"
        return "schema_repair"


class AnswerSkill:
    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def run(self, req: GenerateRequest, question: str, choices: list[str], max_attempts: int = 2) -> tuple[str, str, int]:
        latest_error = None
        for attempt in range(1, max_attempts + 1):
            payload, model_id = self.provider.complete_json(
                system_prompt=system_prompt(),
                user_prompt=answer_skill_prompt(req, question, choices),
            )
            answer = payload.get("answer", "").strip()
            if not answer:
                latest_error = "Answer skill returned empty answer"
                continue
            if req.type == QuestionType.MCQ and answer.upper() not in _MCQ_ANSWERS:
                latest_error = f"MCQ answer must be one of A/B/C/D, got: {answer!r}"
                continue
            if req.type == QuestionType.FRQ and len(answer) < 3:
                latest_error = "FRQ answer must be at least 3 characters"
                continue
            return answer, model_id, attempt
        raise SkillValidationError(str(latest_error))


class ExplanationSkill:
    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def run(self, req: GenerateRequest, question: str, answer: str, max_attempts: int = 2) -> tuple[str, str, int]:
        latest_error = None
        for attempt in range(1, max_attempts + 1):
            payload, model_id = self.provider.complete_json(
                system_prompt=system_prompt(),
                user_prompt=explanation_skill_prompt(req, question, answer),
            )
            explanation = payload.get("explanation", "").strip()
            if len(explanation) >= 10:
                return explanation, model_id, attempt
            latest_error = "Explanation skill returned too-short explanation"
        raise SkillValidationError(str(latest_error))


def compose_item(
    *,
    req: GenerateRequest,
    question: str,
    choices: list[str],
    answer: str,
    explanation: str,
    model_id: str,
    harness_version: str = "v1",
    policy_version: str = "v1",
    prompt_pack_version: str = "v1",
    constraint_profile: str = "default_profile",
) -> GeneratedItem:
    metadata = Metadata(
        subject=req.subject,
        skill=req.skill,
        difficulty=req.difficulty,
        type=req.type,
        locale=req.locale,
        prompt_version=PROMPT_VERSION,
        model_id=model_id,
        harness_version=harness_version,
        policy_version=policy_version,
        prompt_pack_version=prompt_pack_version,
        constraint_profile=constraint_profile,
    )
    return GeneratedItem(
        question=question,
        choices=choices,
        answer=answer,
        explanation=explanation,
        metadata=metadata,
    )
