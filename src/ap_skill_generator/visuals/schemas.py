"""Visual render-layer schemas.

Future reasoning layer (not MVP): VisualReasoningSpec with supports=[trend_interpretation, ...]
for pedagogical alignment checks separate from rendering.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class NumericChartDataPoint(BaseModel):
    x: float
    y: float


class CategoryChartDataPoint(BaseModel):
    x: str = Field(min_length=1)
    y: float


class _ChartBase(BaseModel):
    type: Literal["chart"] = "chart"
    title: str = Field(min_length=1)
    x_label: str = Field(min_length=1)
    y_label: str = Field(min_length=1)
    caption: str | None = None


class LineChartSpec(_ChartBase):
    chart_type: Literal["line"] = "line"
    data: list[NumericChartDataPoint] = Field(min_length=1)


class ScatterChartSpec(_ChartBase):
    chart_type: Literal["scatter"] = "scatter"
    data: list[NumericChartDataPoint] = Field(min_length=1)


class BarChartSpec(_ChartBase):
    chart_type: Literal["bar"] = "bar"
    data: list[CategoryChartDataPoint] = Field(min_length=1)


VisualSpec = Annotated[
    Union[LineChartSpec, ScatterChartSpec, BarChartSpec],
    Field(discriminator="chart_type"),
]
