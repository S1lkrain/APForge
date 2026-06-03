from __future__ import annotations

from typing import Any

from pydantic import TypeAdapter, ValidationError

from .schemas import BarChartSpec, LineChartSpec, ScatterChartSpec, VisualSpec

_VISUAL_ADAPTER = TypeAdapter(VisualSpec)


def validate_visual(raw: dict[str, Any] | None) -> LineChartSpec | ScatterChartSpec | BarChartSpec | None:
    if raw is None:
        return None
    return _VISUAL_ADAPTER.validate_python(raw)


def validate_visual_required(
    raw: dict[str, Any] | None,
    *,
    required: bool,
) -> LineChartSpec | ScatterChartSpec | BarChartSpec | None:
    if raw is None:
        if required:
            raise ValueError("Required visual is missing")
        return None
    try:
        return validate_visual(raw)
    except ValidationError as exc:
        if required:
            raise ValueError(f"Required visual is invalid: {exc}") from exc
        raise
