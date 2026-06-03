from __future__ import annotations

from collections import Counter
from typing import Any


USABLE_STATUSES = frozenset({"accepted", "accepted_with_warning"})


def is_usable_status(status: str) -> bool:
    return status in USABLE_STATUSES


def build_validation_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: Counter[str] = Counter()
    failure_reason_codes: list[str] = []
    repair_classes: list[str] = []
    judge_scores: list[dict[str, Any]] = []

    for entry in items:
        harness = entry.get("harness") or {}
        status = harness.get("status", "unknown")
        status_counts[status] += 1
        code = harness.get("failure_reason_code")
        if code and code != "NONE":
            failure_reason_codes.append(code)
        repair_classes.extend(harness.get("repair_classes") or [])
        metrics = entry.get("metrics") or {}
        scores = metrics.get("judge_scores")
        if isinstance(scores, dict):
            judge_scores.append(scores)

    usable_count = sum(1 for entry in items if is_usable_status((entry.get("harness") or {}).get("status", "")))

    return {
        "total": len(items),
        "usable_count": usable_count,
        "status_counts": dict(status_counts),
        "failure_reason_codes": failure_reason_codes,
        "repair_classes": repair_classes,
        "judge_scores": judge_scores,
    }
