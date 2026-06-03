from __future__ import annotations

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class CalculationSpec(BaseModel):
    method: str
    inputs: Dict[str, Union[float, int, str, List[float]]]
    rounding: Optional[int] = 2
    tolerance: Optional[float] = None


class DistractorSpec(BaseModel):
    error_model: str
    why_wrong: str


class DistractorMetadata(BaseModel):
    value: float
    error_model: str
    why_wrong: str


class CalculationResult(BaseModel):
    verified_answer: Optional[float]
    method: str
    success: bool
    error: Optional[str] = None


class VerificationResult(BaseModel):
    verified: bool
    failure_tags: List[str] = Field(default_factory=list)
    verification_notes: str = ""
    expected_answer: Optional[float] = None
