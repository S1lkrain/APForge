from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, replace
from logging import getLogger

from .computation.calculator import assemble_computation_mcq
from .computation.verifier import verify_answer
from .config import Settings
from .evaluation import evaluate_item, judge_item
from .harness import decide_policy, get_constraint_profile, load_policy
from .logging_utils import RequestLoggerAdapter
from .providers import OpenAICompatibleProvider
from .routing.router import build_provider
from .routing.types import ResolvedRoute, SampleLoopContext
from .routing.validation_summary import build_validation_summary, is_usable_status
from .schema import GenerateRequest
from .skill_production.evaluators import run_basic_evaluators
from .skill_production.registry import get as get_skill_spec
from .skills import AnswerSkill, ExplanationSkill, QuestionSkill, SkillValidationError, compose_item
from .storage import Storage


@dataclass
class APGenerationEngine:
    settings: Settings | None = None

    def __post_init__(self) -> None:
        self.settings = self.settings or Settings()
        self.storage = Storage(self.settings.database_url)
        self.provider = OpenAICompatibleProvider(self.settings)
        self.question_skill = QuestionSkill(self.provider)
        self.answer_skill = AnswerSkill(self.provider)
        self.explanation_skill = ExplanationSkill(self.provider)
        self.harness_policy = load_policy()
        self._logger = getLogger(__name__)

    def generate(
        self,
        req: GenerateRequest,
        *,
        route: ResolvedRoute | None = None,
        llm_api_key: str | None = None,
        sample_id: str | None = None,
    ) -> dict:
        request_id = str(uuid.uuid4())
        logger = RequestLoggerAdapter(self._logger, {"request_id": request_id})
        start = time.perf_counter()

        limits = None
        if route is not None:
            provider = build_provider(route.provider_kind, route.provider_settings)
            question_skill = QuestionSkill(provider)
            answer_skill = AnswerSkill(provider)
            explanation_skill = ExplanationSkill(provider)
            limits = route.limits
        else:
            override_key = (llm_api_key or "").strip()
            if override_key:
                provider = OpenAICompatibleProvider(
                    replace(self.settings, openai_api_key=override_key)
                )
                question_skill = QuestionSkill(provider)
                answer_skill = AnswerSkill(provider)
                explanation_skill = ExplanationSkill(provider)
            else:
                provider = self.provider
                question_skill = self.question_skill
                answer_skill = self.answer_skill
                explanation_skill = self.explanation_skill

        provider.reset_token_usage()
        retry_budget = self.harness_policy.retry_budgets
        default_repair = retry_budget.get("repair", retry_budget.get("question", 2))
        question_repair_budget = default_repair if limits is None else limits.max_repair
        question_draft, q_model_id, repaired, q_attempts, repair_classes = question_skill.run(
            req,
            max_repair_attempts=question_repair_budget,
            sample_context=route.sample_context if route else None,
        )

        computation_required = bool(question_draft.get("calculation_required"))
        calculation_spec = question_draft.get("calculation_spec")
        distractor_metadata = []
        verified_answer = None
        verification_notes = None
        verified = None

        if computation_required:
            distractor_specs = question_draft.get("distractor_specs", [])
            choices, answer, distractor_metadata, calc_result = assemble_computation_mcq(
                calculation_spec,
                distractor_specs,
            )
            verified_answer = calc_result.verified_answer
            a_model_id = q_model_id
            a_attempts = 0
        else:
            answer, a_model_id, a_attempts = answer_skill.run(
                req,
                question_draft["question"],
                question_draft["choices"],
                max_attempts=retry_budget.get("answer", 2),
            )
            choices = question_draft["choices"]

        explanation, e_model_id, e_attempts = explanation_skill.run(
            req,
            question_draft["question"],
            answer,
            max_attempts=retry_budget.get("explanation", 2),
        )
        model_id = e_model_id or a_model_id or q_model_id
        constraint_profile = get_constraint_profile(req.type.value)
        visual = question_draft.get("visual")

        if computation_required:
            preview_item = compose_item(
                req=req,
                question=question_draft["question"],
                choices=choices,
                answer=answer,
                explanation=explanation,
                model_id=model_id,
                harness_version=self.harness_policy.harness_version,
                policy_version=self.harness_policy.policy_version,
                prompt_pack_version=self.harness_policy.prompt_pack_version,
                constraint_profile=constraint_profile,
                calculation_required=True,
                calculation_spec=calculation_spec,
                distractor_metadata=distractor_metadata,
                verified_answer=verified_answer,
                visual=visual,
            )
            verification = verify_answer(preview_item)
            verified = verification.verified
            verification_notes = verification.verification_notes
            if not verification.verified:
                raise SkillValidationError(verification.verification_notes)

        item = compose_item(
            req=req,
            question=question_draft["question"],
            choices=choices,
            answer=answer,
            explanation=explanation,
            model_id=model_id,
            harness_version=self.harness_policy.harness_version,
            policy_version=self.harness_policy.policy_version,
            prompt_pack_version=self.harness_policy.prompt_pack_version,
            constraint_profile=constraint_profile,
            calculation_required=computation_required,
            calculation_spec=calculation_spec if computation_required else None,
            verified=verified,
            verification_notes=verification_notes,
            distractor_metadata=distractor_metadata if computation_required else [],
            verified_answer=verified_answer,
            visual=visual,
        )
        judge = judge_item(item)
        decision = decide_policy(judge.model_dump(), self.harness_policy)
        policy_rejection_reasons = list(decision.reasons)

        allow_soft_retry = limits is None or limits.allow_soft_retry
        if (
            decision.soft_fail
            and allow_soft_retry
            and self.harness_policy.allow_one_soft_retry
            and decision.status != "accepted"
        ):
            explanation, e_model_id, e_attempts_retry = explanation_skill.run(
                req,
                question_draft["question"],
                answer,
                max_attempts=1,
            )
            e_attempts += e_attempts_retry
            model_id = e_model_id or model_id
            item = compose_item(
                req=req,
                question=question_draft["question"],
                choices=choices,
                answer=answer,
                explanation=explanation,
                model_id=model_id,
                harness_version=self.harness_policy.harness_version,
                policy_version=self.harness_policy.policy_version,
                prompt_pack_version=self.harness_policy.prompt_pack_version,
                constraint_profile=constraint_profile,
                calculation_required=computation_required,
                calculation_spec=calculation_spec if computation_required else None,
                verified=verified,
                verification_notes=verification_notes,
                distractor_metadata=distractor_metadata if computation_required else [],
                verified_answer=verified_answer,
                visual=visual,
            )
            judge = judge_item(item)
            decision = decide_policy(judge.model_dump(), self.harness_policy)
            policy_rejection_reasons = list(decision.reasons)

        used_fallback = False
        final_status = decision.status
        failure_reason_code = decision.failure_reason_code
        allow_fallback = limits is None or limits.allow_policy_fallback
        if decision.status == "rejected" and allow_fallback:
            item = self._fallback_item(req, model_id)
            judge = judge_item(item)
            used_fallback = True
            final_status = "fallback"
            failure_reason_code = decision.failure_reason_code or "FALLBACK_PLACEHOLDER"
        elif decision.status == "rejected":
            final_status = "rejected"

        latency_ms = int((time.perf_counter() - start) * 1000)
        token_usage = provider.pop_token_usage()
        attempt_count_by_skill = {
            "question": q_attempts,
            "answer": a_attempts,
            "explanation": e_attempts,
            "repair": len(repair_classes),
        }
        run_id = self.storage.save_generation(
            request_id=request_id,
            req=req,
            item=item,
            model_id=model_id,
            latency_ms=latency_ms,
            repaired=repaired,
            harness_version=self.harness_policy.harness_version,
            policy_version=self.harness_policy.policy_version,
            prompt_pack_version=self.harness_policy.prompt_pack_version,
            gate_mode=self.harness_policy.mode,
            final_status=final_status,
            failure_reason_code=failure_reason_code,
            attempt_count_by_skill=attempt_count_by_skill,
            token_usage=token_usage,
            sample_id=sample_id,
        )
        eval_result = evaluate_item(item, judge_result=judge)
        skill_spec = get_skill_spec(req.skill)
        basic_eval = run_basic_evaluators(item, skill_spec, provider)
        if skill_spec is not None:
            eval_result["failure_tags"] = basic_eval.failure_tags
            eval_result["basic_eval_passed"] = basic_eval.passed
            eval_result["basic_eval_rationale"] = basic_eval.rationale
            judge_scores = dict(eval_result.get("judge_scores", {}))
            judge_scores["failure_tags"] = basic_eval.failure_tags
            eval_result["judge_scores"] = judge_scores
        self.storage.save_eval(run_id=run_id, eval_data=eval_result)
        logger.info(
            "generation completed",
            extra={
                "request_id": request_id,
                "run_id": run_id,
                "latency_ms": latency_ms,
                "repaired": repaired,
                "final_status": final_status,
            },
        )
        return {
            "run_id": run_id,
            "request_id": request_id,
            "item": item.model_dump(),
            "metrics": eval_result,
            "harness": {
                "mode": self.harness_policy.mode,
                "status": final_status,
                "policy_status": decision.status,
                "used_fallback": used_fallback,
                "failure_reason_code": failure_reason_code,
                "reasons": policy_rejection_reasons,
                "attempt_count_by_skill": attempt_count_by_skill,
                "repair_classes": repair_classes,
                "failure_tags": basic_eval.failure_tags if skill_spec is not None else [],
            },
        }

    def generate_sample(
        self,
        req: GenerateRequest,
        *,
        route: ResolvedRoute,
        sample_id: str,
        sample_size: int,
    ) -> dict:
        results: list[dict] = []
        for item_index in range(1, sample_size + 1):
            variation_seed = f"{sample_id}:{item_index}"
            item_route = replace(
                route,
                sample_context=SampleLoopContext(
                    sample_id=sample_id,
                    item_index=item_index,
                    sample_size=sample_size,
                    variation_seed=variation_seed,
                ),
            )
            loop_difficulty = min(5, max(1, req.difficulty + (item_index % 2)))
            loop_req = req.model_copy(update={"difficulty": loop_difficulty})
            try:
                result = self.generate(
                    loop_req,
                    route=item_route,
                    sample_id=sample_id,
                )
                results.append(result)
            except SkillValidationError:
                continue
            except Exception:  # noqa: BLE001
                continue

        usable_count = sum(1 for r in results if is_usable_status(r["harness"]["status"]))
        return {
            "sample_id": sample_id,
            "items": results,
            "usable_count": usable_count,
            "validation_report": build_validation_summary(results),
        }

    def query_items(
        self,
        *,
        run_id: str | None = None,
        sample_id: str | None = None,
        subject: str | None = None,
        skill: str | None = None,
        difficulty: int | None = None,
        item_type: str | None = None,
        status: str | None = None,
        q: str | None = None,
        quality_min: float | None = None,
        quality_max: float | None = None,
        has_quality: bool | None = None,
        sort: str = "newest",
        page: int = 1,
        page_size: int = 10,
    ) -> dict:
        return self.storage.list_items(
            run_id=run_id,
            sample_id=sample_id,
            subject=subject,
            skill=skill,
            difficulty=difficulty,
            item_type=item_type,
            status=status,
            q=q,
            quality_min=quality_min,
            quality_max=quality_max,
            has_quality=has_quality,
            sort=sort,
            page=page,
            page_size=page_size,
        )

    def delete_item(self, run_id: str) -> bool:
        return self.storage.delete_run(run_id)

    def get_dashboard_stats(self) -> dict:
        return self.storage.get_dashboard_stats()

    def _fallback_item(self, req: GenerateRequest, model_id: str):
        question = f"[Fallback] Build an AP-style {req.type.value.upper()} item for skill: {req.skill}."
        choices = ["A. 1", "B. 2", "C. 3", "D. 4"] if req.type.value == "mcq" else []
        answer = "A" if req.type.value == "mcq" else "Use a concise model answer."
        explanation = (
            "This is a fallback placeholder item returned because the harness policy rejected "
            "the generated output. Regenerate or adjust policy thresholds for a full item."
        )
        return compose_item(
            req=req,
            question=question,
            choices=choices,
            answer=answer,
            explanation=explanation,
            model_id=model_id,
            harness_version=self.harness_policy.harness_version,
            policy_version=self.harness_policy.policy_version,
            prompt_pack_version=self.harness_policy.prompt_pack_version,
            constraint_profile=get_constraint_profile(req.type.value),
        )
