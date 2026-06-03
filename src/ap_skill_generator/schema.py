from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .computation.schemas import CalculationSpec, DistractorMetadata
from .visuals.schemas import BarChartSpec, LineChartSpec, ScatterChartSpec


SCHEMA_VERSION = "1.0.0"


class QuestionType(str, Enum):
    MCQ = "mcq"
    FRQ = "frq"


class Subject(str, Enum):
    AP_PRECALCULUS = "ap_precalculus"
    AP_BIOLOGY = "ap_biology"


class Metadata(BaseModel):
    subject: Subject
    skill: str = Field(min_length=1, max_length=120)
    difficulty: int = Field(ge=1, le=5)
    type: QuestionType
    locale: str = Field(default="en-US")
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    prompt_version: str = Field(default="v1")
    model_id: str | None = None
    harness_version: str = Field(default="v1")
    policy_version: str = Field(default="v1")
    prompt_pack_version: str = Field(default="v1")
    constraint_profile: str = Field(default="default_profile")


class GeneratedItem(BaseModel):
    question: str = Field(min_length=10)
    choices: list[str] = Field(default_factory=list)
    answer: str = Field(min_length=1)
    explanation: str = Field(min_length=10)
    metadata: Metadata
    calculation_required: bool = False
    calculation_spec: CalculationSpec | None = None
    verified: bool | None = None
    verification_notes: str | None = None
    distractor_metadata: list[DistractorMetadata] = Field(default_factory=list)
    verified_answer: float | None = None
    visual: LineChartSpec | ScatterChartSpec | BarChartSpec | None = None

    @model_validator(mode="after")
    def validate_mcq_choices(self) -> "GeneratedItem":
        if self.metadata.type == QuestionType.MCQ and len(self.choices) != 4:
            raise ValueError("MCQ requires exactly 4 choices")
        return self


class GenerateRequest(BaseModel):
    subject: Subject
    skill: str = Field(min_length=1, max_length=120)
    difficulty: int = Field(ge=1, le=5)
    type: QuestionType
    locale: str = Field(default="en-US")
