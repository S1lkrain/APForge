from __future__ import annotations

from .computation.error_models import list_error_models
from .computation.schemas import CalculationSpec, DistractorMetadata, DistractorSpec
from .prompts import (
    PROMPT_VERSION,
    answer_skill_prompt,
    explanation_skill_prompt,
    question_skill_prompt,
    system_prompt,
    typed_repair_prompt,
)
from .providers import LLMProvider
from .routing.types import SampleLoopContext
from .schema import GenerateRequest, GeneratedItem, Metadata, QuestionType
from .skill_production.compiler import compile_generation_prompt
from .skill_production.registry import get as get_skill_spec
from .style.pattern_loader import find_pattern
from .style.prompt_builder import build_style_prompt
from .visuals import validate_visual
from .visuals.schemas import BarChartSpec, LineChartSpec, ScatterChartSpec


class SkillValidationError(RuntimeError):
    pass

_MCQ_ANSWERS = {"A", "B", "C", "D"}


class QuestionSkill:
    def __init__(self, provider: LLMProvider):
        self.provider = provider

    @staticmethod
    def _build_user_prompt(
        req: GenerateRequest,
        *,
        sample_context: SampleLoopContext | None = None,
    ) -> str:
        spec = get_skill_spec(req.skill)
        if spec is not None:
            base = compile_generation_prompt(spec, req)
        else:
            base = QuestionSkill._legacy_prompt(req)
        if sample_context is None:
            return base
        variation = (
            f"\n\nThis is item {sample_context.item_index} of {sample_context.sample_size} "
            f"in a sample set. Use a distinct scenario, numeric values, and correct-answer "
            f"letter from prior items. Variation seed: {sample_context.variation_seed}."
        )
        return f"{base}{variation}"

    @staticmethod
    def _legacy_prompt(req: GenerateRequest) -> str:
        user_prompt = question_skill_prompt(req)
        if req.type != QuestionType.MCQ:
            return user_prompt
        pattern = find_pattern(unit="", skill=req.skill)
        if pattern is None:
            return user_prompt
        return f"{user_prompt}\n\n{build_style_prompt(pattern)}"

    def run(
        self,
        req: GenerateRequest,
        max_repair_attempts: int = 2,
        *,
        sample_context: SampleLoopContext | None = None,
    ) -> tuple[dict, str, bool, int, list[str]]:
        payload, model_id = self.provider.complete_json(
            system_prompt=system_prompt(),
            user_prompt=self._build_user_prompt(req, sample_context=sample_context),
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
        draft: dict = {
            "question": payload["question"],
            "choices": payload.get("choices", []),
            "calculation_required": bool(payload.get("calculation_required", False)),
        }
        if payload.get("calculation_spec") is not None:
            draft["calculation_spec"] = CalculationSpec.model_validate(payload["calculation_spec"])
        if payload.get("distractor_specs") is not None:
            draft["distractor_specs"] = [
                DistractorSpec.model_validate(entry) for entry in payload["distractor_specs"]
            ]
        if payload.get("visual") is not None:
            draft["visual"] = validate_visual(payload["visual"])
        return draft

    @staticmethod
    def _validate_draft(draft: dict, req: GenerateRequest) -> None:
        if len(draft["question"]) < 10:
            raise SkillValidationError("Question draft must be at least 10 characters")

        spec = get_skill_spec(req.skill)
        computation_enabled = (
            spec is not None
            and spec.computation is not None
            and spec.computation.enabled
        )

        if computation_enabled:
            if not draft.get("calculation_required"):
                raise SkillValidationError("Computation-enabled skill requires calculation_required=true")
            calc_spec = draft.get("calculation_spec")
            if calc_spec is None:
                raise SkillValidationError("Computation-enabled skill requires calculation_spec")
            allowed_methods = spec.computation.allowed_methods
            if allowed_methods and calc_spec.method not in allowed_methods:
                raise SkillValidationError(
                    f"calculation_spec.method must be one of {allowed_methods}, got: {calc_spec.method!r}"
                )
            distractor_specs = draft.get("distractor_specs", [])
            if len(distractor_specs) != 3:
                raise SkillValidationError("Computation-enabled skill requires exactly 3 distractor_specs")
            known_error_models = set(list_error_models())
            for distractor_spec in distractor_specs:
                if distractor_spec.error_model not in known_error_models:
                    raise SkillValidationError(
                        f"Unknown error_model {distractor_spec.error_model!r}; "
                        f"must be one of: {sorted(known_error_models)}"
                    )
            required_models = spec.computation.required_distractor_models
            if required_models:
                provided_models = {distractor_spec.error_model for distractor_spec in distractor_specs}
                missing = [model for model in required_models if model not in provided_models]
                if missing:
                    raise SkillValidationError(
                        f"distractor_specs must include required error models: {missing}"
                    )
            return

        spec = get_skill_spec(req.skill)
        visual_enabled = spec is not None and spec.visual is not None and spec.visual.enabled
        if visual_enabled:
            visual = draft.get("visual")
            if spec.visual.required and visual is None:
                raise SkillValidationError("Required visual is missing")
            if visual is not None:
                allowed_types = spec.visual.allowed_chart_types
                if allowed_types and visual.chart_type not in allowed_types:
                    raise SkillValidationError(
                        f"chart_type must be one of {allowed_types}, got: {visual.chart_type!r}"
                    )

        if req.type.value == "mcq" and len(draft["choices"]) != 4:
            raise SkillValidationError("MCQ draft requires exactly 4 choices")

    @staticmethod
    def _classify_error(error_text: str) -> str:
        lower = error_text.lower()
        if "choice" in lower or "mcq" in lower:
            return "option_repair"
        if "question" in lower or "keyerror" in lower:
            return "schema_repair"
        if "visual" in lower or "chart" in lower:
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
    calculation_required: bool = False,
    calculation_spec: CalculationSpec | None = None,
    verified: bool | None = None,
    verification_notes: str | None = None,
    distractor_metadata: list[DistractorMetadata] | None = None,
    verified_answer: float | None = None,
    visual: LineChartSpec | ScatterChartSpec | BarChartSpec | None = None,
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
        calculation_required=calculation_required,
        calculation_spec=calculation_spec,
        verified=verified,
        verification_notes=verification_notes,
        distractor_metadata=distractor_metadata or [],
        verified_answer=verified_answer,
        visual=visual,
    )
