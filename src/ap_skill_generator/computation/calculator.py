from __future__ import annotations

from .error_models import apply_error_model
from .formulas import evaluate_method, list_methods
from .schemas import CalculationResult, CalculationSpec, DistractorMetadata, DistractorSpec

_CHOICE_LETTERS = ("A", "B", "C", "D")
_DEFAULT_TOLERANCE = 0.01


def calculate(spec: CalculationSpec) -> CalculationResult:
    try:
        verified_answer = evaluate_method(spec.method, spec.inputs, spec.rounding)
    except Exception as exc:  # noqa: BLE001
        return CalculationResult(
            verified_answer=None,
            method=spec.method,
            success=False,
            error=str(exc),
        )
    return CalculationResult(
        verified_answer=verified_answer,
        method=spec.method,
        success=True,
    )


def _format_choice(letter: str, value: float, rounding: int | None) -> str:
    if rounding is None:
        return f"{letter}. {value}"
    return f"{letter}. {value:.{rounding}f}"


def assemble_computation_mcq(
    spec: CalculationSpec,
    distractor_specs: list[DistractorSpec],
    *,
    shuffle: bool = False,
) -> tuple[list[str], str, list[DistractorMetadata], CalculationResult]:
    if len(distractor_specs) != 3:
        raise ValueError("assemble_computation_mcq requires exactly 3 distractor_specs")

    calc_result = calculate(spec)
    if not calc_result.success or calc_result.verified_answer is None:
        raise ValueError(calc_result.error or "Calculation failed")

    verified_answer = calc_result.verified_answer
    distractor_metadata: list[DistractorMetadata] = []
    distractor_values: list[float] = []

    for distractor_spec in distractor_specs:
        try:
            value = apply_error_model(distractor_spec.error_model, spec, verified_answer)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Error model {distractor_spec.error_model!r} failed: {exc}") from exc
        if abs(value - verified_answer) < _tolerance(spec):
            raise ValueError(f"Error model {distractor_spec.error_model!r} produced the correct answer")
        if any(abs(value - existing) < _tolerance(spec) for existing in distractor_values):
            raise ValueError(f"Error model {distractor_spec.error_model!r} produced a duplicate distractor")
        distractor_values.append(value)
        distractor_metadata.append(
            DistractorMetadata(
                value=value,
                error_model=distractor_spec.error_model,
                why_wrong=distractor_spec.why_wrong,
            )
        )

    option_values = [verified_answer, *distractor_values]
    if shuffle:
        raise NotImplementedError("shuffle is not supported in MVP")

    choices: list[str] = []
    answer_letter = "A"
    for index, letter in enumerate(_CHOICE_LETTERS):
        value = option_values[index]
        choices.append(_format_choice(letter, value, spec.rounding))
        if index == 0:
            answer_letter = letter

    return choices, answer_letter, distractor_metadata, calc_result


def _tolerance(spec: CalculationSpec) -> float:
    if spec.tolerance is not None:
        return spec.tolerance
    if spec.rounding is not None and spec.rounding >= 0:
        return 10 ** (-spec.rounding) / 2
    return _DEFAULT_TOLERANCE


__all__ = ["assemble_computation_mcq", "calculate", "list_methods"]
