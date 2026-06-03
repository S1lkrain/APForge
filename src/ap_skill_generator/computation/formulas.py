from __future__ import annotations

import statistics
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable, Dict, List, Union

from . import sympy_tools

InputDict = Dict[str, Union[float, int, str, List[float]]]
FormulaFn = Callable[[InputDict], float]

_REQUIRED_INPUTS: dict[str, tuple[str, ...]] = {
    "compound_interest": ("principal", "rate", "time"),
    "simple_interest": ("principal", "rate", "time"),
    "percent_change": ("initial", "final"),
    "exponential_growth": ("initial", "base", "time"),
    "linear_function": ("slope", "x"),
    "slope": ("x1", "y1", "x2", "y2"),
    "mean": ("values",),
    "standard_deviation": ("values",),
    "z_score": ("value", "mean", "sd"),
    "probability_complement": ("p",),
    "derivative_evaluation": ("expression", "variable", "at"),
    "function_substitution": ("expression", "variable", "value"),
    "molarity": ("moles", "volume_L"),
    "dilution": ("C1", "V1", "V2"),
    "stoichiometric_ratio": ("moles_a", "coeff_a", "coeff_b"),
}


def _require(inputs: dict, *keys: str) -> None:
    missing = [key for key in keys if key not in inputs]
    if missing:
        raise ValueError(f"Missing required inputs: {', '.join(missing)}")


def _num(value: float | int | str) -> float:
    return float(value)


def _decimal(value: float | int | str) -> Decimal:
    return Decimal(str(value))


def _round_value(value: float, places: int | None) -> float:
    if places is None:
        return float(value)
    quantizer = Decimal("1").scaleb(-places)
    return float(Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP))


def compound_interest(inputs: dict[str, float | int | str | list[float]]) -> float:
    _require(inputs, "principal", "rate", "time")
    principal = _decimal(inputs["principal"])
    rate = _decimal(inputs["rate"])
    time = _decimal(inputs["time"])
    result = principal * (Decimal("1") + rate) ** time
    return float(result)


def simple_interest(inputs: dict[str, float | int | str | list[float]]) -> float:
    _require(inputs, "principal", "rate", "time")
    principal = _decimal(inputs["principal"])
    rate = _decimal(inputs["rate"])
    time = _decimal(inputs["time"])
    return float(principal * rate * time)


def percent_change(inputs: dict[str, float | int | str | list[float]]) -> float:
    _require(inputs, "initial", "final")
    initial = _num(inputs["initial"])
    final = _num(inputs["final"])
    if initial == 0:
        raise ValueError("initial must be non-zero for percent change")
    return (final - initial) / initial * 100


def exponential_growth(inputs: dict[str, float | int | str | list[float]]) -> float:
    _require(inputs, "initial", "base", "time")
    initial = _num(inputs["initial"])
    base = _num(inputs["base"])
    time = _num(inputs["time"])
    return initial * (base**time)


def linear_function(inputs: dict[str, float | int | str | list[float]]) -> float:
    _require(inputs, "slope", "x")
    slope = _num(inputs["slope"])
    x = _num(inputs["x"])
    intercept = _num(inputs.get("intercept", 0))
    return slope * x + intercept


def slope(inputs: dict[str, float | int | str | list[float]]) -> float:
    _require(inputs, "x1", "y1", "x2", "y2")
    x1 = _num(inputs["x1"])
    y1 = _num(inputs["y1"])
    x2 = _num(inputs["x2"])
    y2 = _num(inputs["y2"])
    if x2 == x1:
        raise ValueError("x2 must differ from x1 for slope")
    return (y2 - y1) / (x2 - x1)


def mean(inputs: dict[str, float | int | str | list[float]]) -> float:
    _require(inputs, "values")
    values = inputs["values"]
    if not isinstance(values, list) or not values:
        raise ValueError("values must be a non-empty list")
    return statistics.mean(float(v) for v in values)


def standard_deviation(inputs: dict[str, float | int | str | list[float]]) -> float:
    _require(inputs, "values")
    values = inputs["values"]
    if not isinstance(values, list) or len(values) < 2:
        raise ValueError("values must be a list with at least 2 entries")
    numeric = [float(v) for v in values]
    sample = bool(inputs.get("sample", False))
    if sample:
        return statistics.stdev(numeric)
    return statistics.pstdev(numeric)


def z_score(inputs: dict[str, float | int | str | list[float]]) -> float:
    _require(inputs, "value", "mean", "sd")
    value = _num(inputs["value"])
    mean_value = _num(inputs["mean"])
    sd = _num(inputs["sd"])
    if sd == 0:
        raise ValueError("sd must be non-zero for z-score")
    return (value - mean_value) / sd


def probability_complement(inputs: dict[str, float | int | str | list[float]]) -> float:
    _require(inputs, "p")
    return 1 - _num(inputs["p"])


def derivative_evaluation(inputs: dict[str, float | int | str | list[float]]) -> float:
    _require(inputs, "expression", "variable", "at")
    expression = str(inputs["expression"])
    variable = str(inputs["variable"])
    at = _num(inputs["at"])
    return sympy_tools.differentiate_and_evaluate(expression, variable, at)


def function_substitution(inputs: dict[str, float | int | str | list[float]]) -> float:
    _require(inputs, "expression", "variable", "value")
    expression = str(inputs["expression"])
    variable = str(inputs["variable"])
    value = _num(inputs["value"])
    return sympy_tools.evaluate_expression(expression, {variable: value})


def molarity(inputs: dict[str, float | int | str | list[float]]) -> float:
    _require(inputs, "moles", "volume_L")
    moles = _num(inputs["moles"])
    volume = _num(inputs["volume_L"])
    if volume == 0:
        raise ValueError("volume_L must be non-zero")
    return moles / volume


def dilution(inputs: dict[str, float | int | str | list[float]]) -> float:
    _require(inputs, "C1", "V1", "V2")
    c1 = _num(inputs["C1"])
    v1 = _num(inputs["V1"])
    v2 = _num(inputs["V2"])
    if v2 == 0:
        raise ValueError("V2 must be non-zero")
    return c1 * v1 / v2


def stoichiometric_ratio(inputs: dict[str, float | int | str | list[float]]) -> float:
    _require(inputs, "moles_a", "coeff_a", "coeff_b")
    moles_a = _num(inputs["moles_a"])
    coeff_a = _num(inputs["coeff_a"])
    coeff_b = _num(inputs["coeff_b"])
    if coeff_a == 0:
        raise ValueError("coeff_a must be non-zero")
    return (moles_a / coeff_a) * coeff_b


FORMULA_REGISTRY: dict[str, FormulaFn] = {
    "compound_interest": compound_interest,
    "simple_interest": simple_interest,
    "percent_change": percent_change,
    "exponential_growth": exponential_growth,
    "linear_function": linear_function,
    "slope": slope,
    "mean": mean,
    "standard_deviation": standard_deviation,
    "z_score": z_score,
    "probability_complement": probability_complement,
    "derivative_evaluation": derivative_evaluation,
    "function_substitution": function_substitution,
    "molarity": molarity,
    "dilution": dilution,
    "stoichiometric_ratio": stoichiometric_ratio,
}


def list_methods() -> list[str]:
    return sorted(FORMULA_REGISTRY.keys())


def evaluate_method(method: str, inputs: dict[str, float | int | str | list[float]], rounding: int | None = 2) -> float:
    if method not in FORMULA_REGISTRY:
        raise ValueError(f"Unknown method: {method}")
    required = _REQUIRED_INPUTS.get(method, ())
    _require(inputs, *required)
    raw = FORMULA_REGISTRY[method](inputs)
    return _round_value(raw, rounding)
