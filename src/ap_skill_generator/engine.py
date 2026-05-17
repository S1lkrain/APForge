from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from logging import getLogger

from .config import Settings
from .evaluation import evaluate_item, judge_item
from .harness import decide_policy, get_constraint_profile, load_policy
from .logging_utils import RequestLoggerAdapter
from .providers import OpenAICompatibleProvider
from .schema import GenerateRequest
from .skills import AnswerSkill, ExplanationSkill, QuestionSkill, compose_item
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

    def generate(self, req: GenerateRequest) -> dict:
        request_id = str(uuid.uuid4())
        logger = RequestLoggerAdapter(self._logger, {"request_id": request_id})
        start = time.perf_counter()
        self.provider.reset_token_usage()
        retry_budget = self.harness_policy.retry_budgets
        question_repair_budget = retry_budget.get(
            "repair",
            retry_budget.get("question", 2),
        )
        question_draft, q_model_id, repaired, q_attempts, repair_classes = self.question_skill.run(
            req,
            max_repair_attempts=question_repair_budget,
        )
        answer, a_model_id, a_attempts = self.answer_skill.run(
            req,
            question_draft["question"],
            question_draft["choices"],
            max_attempts=retry_budget.get("answer", 2),
        )
        explanation, e_model_id, e_attempts = self.explanation_skill.run(
            req,
            question_draft["question"],
            answer,
            max_attempts=retry_budget.get("explanation", 2),
        )
        model_id = e_model_id or a_model_id or q_model_id
        constraint_profile = get_constraint_profile(req.type.value)
        item = compose_item(
            req=req,
            question=question_draft["question"],
            choices=question_draft["choices"],
            answer=answer,
            explanation=explanation,
            model_id=model_id,
            harness_version=self.harness_policy.harness_version,
            policy_version=self.harness_policy.policy_version,
            prompt_pack_version=self.harness_policy.prompt_pack_version,
            constraint_profile=constraint_profile,
        )
        judge = judge_item(item)
        decision = decide_policy(judge.model_dump(), self.harness_policy)
        policy_rejection_reasons = list(decision.reasons)

        # one controlled soft-retry path for explainability/consistency.
        if decision.soft_fail and self.harness_policy.allow_one_soft_retry and decision.status != "accepted":
            explanation, e_model_id, e_attempts_retry = self.explanation_skill.run(
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
                choices=question_draft["choices"],
                answer=answer,
                explanation=explanation,
                model_id=model_id,
                harness_version=self.harness_policy.harness_version,
                policy_version=self.harness_policy.policy_version,
                prompt_pack_version=self.harness_policy.prompt_pack_version,
                constraint_profile=constraint_profile,
            )
            judge = judge_item(item)
            decision = decide_policy(judge.model_dump(), self.harness_policy)
            policy_rejection_reasons = list(decision.reasons)

        used_fallback = False
        final_status = decision.status
        failure_reason_code = decision.failure_reason_code
        if decision.status == "rejected":
            item = self._fallback_item(req, model_id)
            judge = judge_item(item)
            used_fallback = True
            final_status = "fallback"
            failure_reason_code = decision.failure_reason_code or "FALLBACK_PLACEHOLDER"

        latency_ms = int((time.perf_counter() - start) * 1000)
        token_usage = self.provider.pop_token_usage()
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
        )
        eval_result = evaluate_item(item, judge_result=judge)
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
            },
        }

    def query_items(self, *, subject: str | None = None, skill: str | None = None, difficulty: int | None = None) -> list[dict]:
        return self.storage.list_items(subject=subject, skill=skill, difficulty=difficulty)

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
