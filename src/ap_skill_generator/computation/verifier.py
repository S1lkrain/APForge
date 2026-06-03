from __future__ import annotations

import re

from ..schema import GeneratedItem
from .calculator import calculate
from .error_models import apply_error_model
from .schemas import CalculationSpec, VerificationResult

_CHOICE_VALUE_PATTERN = re.compile(r"^[A-D]\.\s*(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)", re.IGNORECASE)
_DEFAULT_TOLERANCE = 0.01


def extract_choice_value(choice: str) -> float | None:
    match = _CHOICE_VALUE_PATTERN.match(choice.strip())
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _tolerance(spec: CalculationSpec) -> float:
    if spec.tolerance is not None:
        return spec.tolerance
    if spec.rounding is not None and spec.rounding >= 0:
        return 10 ** (-spec.rounding) / 2
    return _DEFAULT_TOLERANCE


def _values_close(left: float, right: float, tolerance: float) -> bool:
    return abs(left - right) <= tolerance


def verify_answer(item: GeneratedItem) -> VerificationResult:
    if not item.calculation_required:
        return VerificationResult(
            verified=True,
            verification_notes="calculation not required",
        )

    if item.calculation_spec is None:
        return VerificationResult(
            verified=False,
            failure_tags=["unverifiable_calculation"],
            verification_notes="calculation_required but calculation_spec is missing",
        )

    spec = item.calculation_spec
    calc_result = calculate(spec)
    if not calc_result.success or calc_result.verified_answer is None:
        return VerificationResult(
            verified=False,
            failure_tags=["unverifiable_calculation"],
            verification_notes=calc_result.error or "calculation failed during verification",
        )

    expected = calc_result.verified_answer
    tolerance = _tolerance(spec)
    failure_tags: list[str] = []

    if item.verified_answer is not None and not _values_close(item.verified_answer, expected, tolerance):
        failure_tags.append("computation_mismatch")

    choice_values: dict[str, float] = {}
    for choice in item.choices:
        letter = choice.strip()[:1].upper()
        value = extract_choice_value(choice)
        if value is None:
            return VerificationResult(
                verified=False,
                failure_tags=["unverifiable_calculation"],
                verification_notes=f"could not parse numeric value from choice: {choice!r}",
                expected_answer=expected,
            )
        choice_values[letter] = value

    answer = item.answer.strip().upper()
    if answer not in choice_values:
        failure_tags.append("computation_mismatch")
    elif not _values_close(choice_values[answer], expected, tolerance):
        failure_tags.append("computation_mismatch")

    if len(set(choice_values.values())) < len(choice_values):
        failure_tags.append("unrealistic_distractor")

    if any(_values_close(value, expected, tolerance) for letter, value in choice_values.items() if letter != answer):
        failure_tags.append("unrealistic_distractor")

    for metadata in item.distractor_metadata:
        try:
            expected_wrong = apply_error_model(metadata.error_model, spec, expected)
        except Exception:  # noqa: BLE001
            failure_tags.append("unverifiable_calculation")
            continue
        if not _values_close(metadata.value, expected_wrong, tolerance):
            failure_tags.append("computation_mismatch")
        if _values_close(metadata.value, expected, tolerance):
            failure_tags.append("unrealistic_distractor")

    unique_tags = list(dict.fromkeys(failure_tags))
    verified = len(unique_tags) == 0
    notes = "computation verified" if verified else f"verification failed: {', '.join(unique_tags)}"
    return VerificationResult(
        verified=verified,
        failure_tags=unique_tags,
        verification_notes=notes,
        expected_answer=expected,
    )
