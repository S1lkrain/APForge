from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class HarnessPolicy:
    harness_version: str
    policy_version: str
    prompt_pack_version: str
    mode: str
    retry_budgets: Dict[str, int]
    thresholds: Dict[str, int]
    hard_fail_rules: Dict[str, bool]
    soft_fail_rules: Dict[str, bool]
    allow_one_soft_retry: bool


@dataclass
class PolicyDecision:
    status: str
    failure_reason_code: str
    hard_fail: bool
    soft_fail: bool
    reasons: List[str]


def load_policy() -> HarnessPolicy:
    policy_path = Path(__file__).resolve().parents[2] / "config" / "policy.json"
    data = json.loads(policy_path.read_text(encoding="utf-8"))
    return HarnessPolicy(
        harness_version=data["harness_version"],
        policy_version=data["policy_version"],
        prompt_pack_version=data["prompt_pack_version"],
        mode=data["mode"],
        retry_budgets=data["retry_budgets"],
        thresholds=data["thresholds"],
        hard_fail_rules=data["hard_fail_rules"],
        soft_fail_rules=data["soft_fail_rules"],
        allow_one_soft_retry=data["allow_one_soft_retry"],
    )


def decide_policy(judge_scores: Dict[str, Any], policy: HarnessPolicy) -> PolicyDecision:
    reasons: List[str] = []
    hard_fail = False
    soft_fail = False

    if (
        judge_scores["schema_score"] < policy.thresholds["schema_score_min"]
        and policy.hard_fail_rules.get("schema_invalid", True)
    ):
        reasons.append("SCHEMA_INVALID")
        hard_fail = True
    if (
        judge_scores["compliance_score"] < policy.thresholds["compliance_score_min"]
        and policy.hard_fail_rules.get("compliance_below_threshold", True)
    ):
        reasons.append("COMPLIANCE_LOW")
        hard_fail = True
    if (
        judge_scores["consistency_score"] < policy.thresholds["consistency_score_min"]
        and policy.soft_fail_rules.get("consistency_below_threshold", True)
    ):
        reasons.append("CONSISTENCY_LOW")
        soft_fail = True
    if (
        judge_scores["pedagogy_score"] < policy.thresholds["pedagogy_score_min"]
        and policy.soft_fail_rules.get("pedagogy_below_threshold", True)
    ):
        reasons.append("PEDAGOGY_LOW")
        soft_fail = True

    if policy.mode == "shadow":
        status = "accepted_with_warning" if (hard_fail or soft_fail) else "accepted"
        return PolicyDecision(status=status, failure_reason_code="NONE", hard_fail=hard_fail, soft_fail=soft_fail, reasons=reasons)
    if policy.mode == "warn":
        if hard_fail:
            return PolicyDecision(
                status="rejected",
                failure_reason_code=reasons[0] if reasons else "POLICY_FAIL",
                hard_fail=True,
                soft_fail=soft_fail,
                reasons=reasons,
            )
        status = "accepted_with_warning" if soft_fail else "accepted"
        return PolicyDecision(status=status, failure_reason_code="NONE", hard_fail=False, soft_fail=soft_fail, reasons=reasons)

    # enforce mode
    if hard_fail or soft_fail:
        return PolicyDecision(
            status="rejected",
            failure_reason_code=reasons[0] if reasons else "POLICY_FAIL",
            hard_fail=hard_fail,
            soft_fail=soft_fail,
            reasons=reasons,
        )
    return PolicyDecision(status="accepted", failure_reason_code="NONE", hard_fail=False, soft_fail=False, reasons=[])


def get_constraint_profile(item_type: str) -> str:
    if item_type == "mcq":
        return "mcq_profile"
    if item_type == "frq":
        return "frq_profile"
    return "default_profile"
