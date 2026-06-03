from __future__ import annotations

from typing import Callable

from .formulas import _round_value, evaluate_method
from .schemas import CalculationSpec

ErrorModelFn = Callable[[CalculationSpec, float], float]


def _num(value: float | int | str) -> float:
    return float(value)


def sign_error(_spec: CalculationSpec, verified_answer: float) -> float:
    return -verified_answer


def forgot_exponent(spec: CalculationSpec, verified_answer: float) -> float:
    if spec.method in {"compound_interest", "exponential_growth"}:
        inputs = dict(spec.inputs)
        if "time" in inputs:
            inputs["time"] = 1
            return evaluate_method(spec.method, inputs, spec.rounding)
    return verified_answer * 0.5


def swapped_fraction(spec: CalculationSpec, verified_answer: float) -> float:
    if spec.method == "percent_change":
        initial = _num(spec.inputs["initial"])
        final = _num(spec.inputs["final"])
        if final == 0:
            return verified_answer
        return (initial - final) / final * 100
    if verified_answer != 0:
        return 1 / verified_answer
    return verified_answer + 1


def early_rounding(spec: CalculationSpec, verified_answer: float) -> float:
    places = max((spec.rounding or 2) - 1, 0)
    factor = 10**places
    return round(verified_answer * factor) / factor


def arithmetic_slip(_spec: CalculationSpec, verified_answer: float) -> float:
    magnitude = max(abs(verified_answer) * 0.05, 1)
    return verified_answer + magnitude


def simple_interest_instead_of_compound(spec: CalculationSpec, _verified_answer: float) -> float:
    if spec.method == "compound_interest":
        principal = _num(spec.inputs["principal"])
        interest = evaluate_method("simple_interest", spec.inputs, spec.rounding)
        return principal + interest
    if spec.method == "exponential_growth":
        initial = _num(spec.inputs.get("initial", spec.inputs.get("principal", 0)))
        rate = _num(spec.inputs.get("rate", _num(spec.inputs.get("base", 1)) - 1))
        time = _num(spec.inputs.get("time", 1))
        return initial + initial * rate * time
    principal = _num(spec.inputs.get("principal", 0))
    interest = evaluate_method("simple_interest", spec.inputs, spec.rounding)
    return principal + interest


def wrong_denominator(spec: CalculationSpec, verified_answer: float) -> float:
    if spec.method == "mean" and isinstance(spec.inputs.get("values"), list):
        values = [float(v) for v in spec.inputs["values"]]
        if len(values) > 1:
            return sum(values) / (len(values) - 1)
    return verified_answer * 1.1


def population_vs_sample_sd(spec: CalculationSpec, verified_answer: float) -> float:
    if spec.method == "standard_deviation" and isinstance(spec.inputs.get("values"), list):
        flipped = dict(spec.inputs)
        flipped["sample"] = not bool(spec.inputs.get("sample", False))
        return evaluate_method("standard_deviation", flipped, spec.rounding)
    return verified_answer * 1.05


def forgot_chain_rule(spec: CalculationSpec, verified_answer: float) -> float:
    if spec.method == "derivative_evaluation":
        expression = str(spec.inputs.get("expression", "x"))
        variable = str(spec.inputs.get("variable", "x"))
        at = _num(spec.inputs.get("at", 0))
        from . import sympy_tools

        return sympy_tools.evaluate_expression(expression, {variable: at})
    return verified_answer


def derivative_sign_error(_spec: CalculationSpec, verified_answer: float) -> float:
    return -verified_answer


def incorrect_substitution(spec: CalculationSpec, verified_answer: float) -> float:
    if spec.method == "function_substitution":
        value = _num(spec.inputs.get("value", 0))
        return value
    return verified_answer * 0.9


def unit_conversion_error(spec: CalculationSpec, verified_answer: float) -> float:
    if spec.method == "molarity":
        return verified_answer * 1000
    if spec.method == "dilution":
        return verified_answer * 10
    return verified_answer * 100


def stoichiometric_ratio_error(spec: CalculationSpec, verified_answer: float) -> float:
    if spec.method == "stoichiometric_ratio":
        moles_a = _num(spec.inputs["moles_a"])
        coeff_a = _num(spec.inputs["coeff_a"])
        coeff_b = _num(spec.inputs["coeff_b"])
        if coeff_b == 0:
            return verified_answer
        return (moles_a / coeff_b) * coeff_a
    return verified_answer * 1.25


ERROR_MODEL_REGISTRY: dict[str, ErrorModelFn] = {
    "sign_error": sign_error,
    "forgot_exponent": forgot_exponent,
    "swapped_fraction": swapped_fraction,
    "early_rounding": early_rounding,
    "arithmetic_slip": arithmetic_slip,
    "simple_interest_instead_of_compound": simple_interest_instead_of_compound,
    "wrong_denominator": wrong_denominator,
    "population_vs_sample_sd": population_vs_sample_sd,
    "forgot_chain_rule": forgot_chain_rule,
    "derivative_sign_error": derivative_sign_error,
    "incorrect_substitution": incorrect_substitution,
    "unit_conversion_error": unit_conversion_error,
    "stoichiometric_ratio_error": stoichiometric_ratio_error,
}


def list_error_models() -> list[str]:
    return sorted(ERROR_MODEL_REGISTRY.keys())


def apply_error_model(name: str, spec: CalculationSpec, verified_answer: float) -> float:
    if name not in ERROR_MODEL_REGISTRY:
        raise ValueError(f"Unknown error model: {name}")
    value = ERROR_MODEL_REGISTRY[name](spec, verified_answer)
    return _round_value(value, spec.rounding)
