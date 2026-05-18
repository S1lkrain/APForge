from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .schema import StylePattern

_PATTERNS: List[StylePattern] = []

# Maps API slugs and informal names to pattern `skill` fields.
_SKILL_ALIASES = {
    "amplitudeandperiod": "Sinusoidal Functions",
    "amplitudeandperiodmcq": "Sinusoidal Functions",
    "sinusoidalfunctions": "Sinusoidal Functions",
    "sinusoidalmodeling": "Sinusoidal Function Context and Data Modeling",
    "limits": "Rates of Change",
    "ratesofchange": "Rates of Change",
    "linearfunctions": "Rates of Change",
    "exponentialgrowth": "Exponential Growth and Decay",
    "exponentialdecay": "Exponential Growth and Decay",
    "rationalfunctions": "Asymptotes",
    "asymptotes": "Asymptotes",
    "logarithms": "Logarithmic Expressions",
    "logexpressions": "Logarithmic Expressions",
    "polar": "Polar Function Graphs",
    "polarfunctions": "Polar Function Graphs",
    "regression": "Competing Function Model Validation",
    "datamodeling": "Competing Function Model Validation",
    "endbehavior": "End Behavior",
}


def _patterns_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "style_patterns" / "mcq"


def _normalize(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _resolve_skill(skill: str) -> str:
    key = _normalize(skill)
    return _SKILL_ALIASES.get(key, skill)


def load_patterns(patterns_dir: Optional[Path] = None) -> List[StylePattern]:
    global _PATTERNS
    directory = patterns_dir or _patterns_dir()
    loaded: List[StylePattern] = []
    if not directory.is_dir():
        _PATTERNS = loaded
        return loaded

    for path in sorted(directory.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        loaded.append(StylePattern.model_validate(data))

    _PATTERNS = loaded
    return loaded


def get_all_patterns() -> List[StylePattern]:
    if not _PATTERNS:
        load_patterns()
    return list(_PATTERNS)


def find_pattern(unit: str, skill: str) -> Optional[StylePattern]:
    patterns = get_all_patterns()
    unit_key = _normalize(unit)
    skill_key = _normalize(_resolve_skill(skill))
    for pattern in patterns:
        if skill_key != _normalize(pattern.skill):
            continue
        if unit_key and unit_key != _normalize(pattern.unit):
            continue
        return pattern
    return None
