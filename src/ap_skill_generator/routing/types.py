from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..config import Settings

UserMode = Literal["free", "byok"]


@dataclass(frozen=True)
class GenerationLimits:
    max_repair: int
    allow_policy_fallback: bool
    allow_soft_retry: bool


@dataclass(frozen=True)
class SampleLoopContext:
    sample_id: str
    item_index: int
    sample_size: int
    variation_seed: str


@dataclass(frozen=True)
class ResolvedRoute:
    mode: UserMode
    provider_kind: str
    provider_settings: Settings
    limits: GenerationLimits
    sample_context: SampleLoopContext | None = None
