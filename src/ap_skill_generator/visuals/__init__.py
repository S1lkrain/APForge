"""Structured visual specs for APForge reasoning artifacts.

MVP: LLM-sourced chart data via QuestionSkill draft.
Future: CalculationSpec.visualize -> calculator/verifier -> verified data points -> VisualSpec.
"""

from .schemas import (
    BarChartSpec,
    CategoryChartDataPoint,
    LineChartSpec,
    NumericChartDataPoint,
    ScatterChartSpec,
    VisualSpec,
)
from .validator import validate_visual, validate_visual_required
from .visual_semantics import check_visual_semantics

__all__ = [
    "BarChartSpec",
    "CategoryChartDataPoint",
    "LineChartSpec",
    "NumericChartDataPoint",
    "ScatterChartSpec",
    "VisualSpec",
    "check_visual_semantics",
    "validate_visual",
    "validate_visual_required",
]
