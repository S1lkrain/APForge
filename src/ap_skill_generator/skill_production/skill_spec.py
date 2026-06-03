from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class SkillStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"


class SkillMetadata(BaseModel):
    display_name: str


class CoreReasoning(BaseModel):
    summary: str
    cognitive_actions: list[str] = Field(default_factory=list)
    reasoning_steps: list[str] = Field(min_length=1)
    anti_patterns: list[str] = Field(default_factory=list)


class QuestionArchetype(BaseModel):
    id: str
    description: str
    stem_patterns: list[str] = Field(min_length=1)
    formats: list[Literal["mcq"]] = Field(default_factory=lambda: ["mcq"])


class DistractorPattern(BaseModel):
    id: str
    description: str
    failure_mode: str
    generation_hints: list[str] = Field(default_factory=list)


class PromptConstraints(BaseModel):
    generation_rules: list[str] = Field(default_factory=list)
    forbidden_content: list[str] = Field(default_factory=list)


class ComputationConfig(BaseModel):
    enabled: bool = False
    allowed_methods: list[str] = Field(default_factory=list)
    required_distractor_models: list[str] = Field(default_factory=list)


class VisualConfig(BaseModel):
    enabled: bool = False
    required: bool = False
    allowed_chart_types: list[str] = Field(default_factory=list)


class SkillSpec(BaseModel):
    skill_id: str = Field(min_length=1)
    status: SkillStatus
    subject: str
    category: str
    metadata: SkillMetadata
    core_reasoning: CoreReasoning
    question_archetypes: list[QuestionArchetype] = Field(min_length=1)
    distractor_patterns: list[DistractorPattern] = Field(default_factory=list)
    prompt_constraints: PromptConstraints = Field(default_factory=PromptConstraints)
    computation: ComputationConfig | None = None
    visual: VisualConfig | None = None


def load_skill_spec(path: Path) -> SkillSpec:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return SkillSpec.model_validate(raw)
