from __future__ import annotations

from .schemas import BarChartSpec, LineChartSpec, ScatterChartSpec

SemanticIssue = str


def check_line_monotonic_x(spec: LineChartSpec) -> SemanticIssue | None:
    xs = [point.x for point in spec.data]
    if len(xs) < 2:
        return None
    for prev, curr in zip(xs, xs[1:]):
        if curr <= prev:
            return "non_monotonic_x"
    return None


def check_bar_unique_categories(spec: BarChartSpec) -> SemanticIssue | None:
    labels = [point.x for point in spec.data]
    if len(labels) != len(set(labels)):
        return "duplicate_categories"
    return None


def check_scatter_variance(spec: ScatterChartSpec) -> SemanticIssue | None:
    if len(spec.data) < 2:
        return None
    xs = {point.x for point in spec.data}
    ys = {point.y for point in spec.data}
    if len(xs) == 1 and len(ys) == 1:
        return "insufficient_variance"
    return None


def check_visual_semantics(
    spec: LineChartSpec | ScatterChartSpec | BarChartSpec,
) -> list[SemanticIssue]:
    if isinstance(spec, LineChartSpec):
        issue = check_line_monotonic_x(spec)
        return [issue] if issue else []
    if isinstance(spec, BarChartSpec):
        issue = check_bar_unique_categories(spec)
        return [issue] if issue else []
    if isinstance(spec, ScatterChartSpec):
        issue = check_scatter_variance(spec)
        return [issue] if issue else []
    return []
