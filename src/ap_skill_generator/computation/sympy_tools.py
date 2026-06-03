from __future__ import annotations

from sympy import Symbol, simplify, sympify


def evaluate_expression(expr: str, symbols: dict[str, float | int]) -> float:
    sym_map = {name: Symbol(name) for name in symbols}
    parsed = sympify(expr, locals=sym_map)
    result = parsed.subs({sym_map[name]: value for name, value in symbols.items()})
    return float(result.evalf())


def differentiate(expr: str, variable: str) -> str:
    sym = Symbol(variable)
    parsed = sympify(expr, locals={variable: sym})
    return str(simplify(parsed.diff(sym)))


def differentiate_and_evaluate(expr: str, variable: str, at: float | int) -> float:
    derivative_expr = differentiate(expr, variable)
    return evaluate_expression(derivative_expr, {variable: at})


def simplify_expression(expr: str) -> str:
    return str(simplify(sympify(expr)))
