from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class StylePattern(BaseModel):
    id: str
    unit: str
    skill: str
    question_type: str
    style_summary: str
    representation: List[str]
    cognitive_action: List[str]
    wording_patterns: List[str]
    distractor_patterns: List[str]
    notes: Optional[str] = None
