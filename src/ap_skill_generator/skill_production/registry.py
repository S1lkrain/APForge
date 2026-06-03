from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .skill_spec import SkillSpec, load_skill_spec

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SPECS_DIR = _PROJECT_ROOT / "skill_specs"

SKILL_REGISTRY: dict[str, Path] = {
    "ap_biology.experimental_interpretation": _SPECS_DIR / "ap_biology" / "experimental_interpretation.yaml",
    "ap_biology.graph_interpretation": _SPECS_DIR / "ap_biology" / "graph_interpretation.yaml",
    "ap_biology.variable_analysis": _SPECS_DIR / "ap_biology" / "variable_analysis.yaml",
    "ap_biology.evidence_reasoning": _SPECS_DIR / "ap_biology" / "evidence_reasoning.yaml",
    "ap_biology.prediction_reasoning": _SPECS_DIR / "ap_biology" / "prediction_reasoning.yaml",
    "ap_precalculus.rates_of_change": _SPECS_DIR / "ap_precalculus" / "rates_of_change.yaml",
    "ap_precalculus.end_behavior": _SPECS_DIR / "ap_precalculus" / "end_behavior.yaml",
    "ap_precalculus.asymptotes": _SPECS_DIR / "ap_precalculus" / "asymptotes.yaml",
    "ap_precalculus.exponential_growth": _SPECS_DIR / "ap_precalculus" / "exponential_growth.yaml",
    "ap_precalculus.logarithmic_expressions": _SPECS_DIR / "ap_precalculus" / "logarithmic_expressions.yaml",
    "ap_precalculus.sinusoidal_functions": _SPECS_DIR / "ap_precalculus" / "sinusoidal_functions.yaml",
    "ap_precalculus.sinusoidal_modeling": _SPECS_DIR / "ap_precalculus" / "sinusoidal_modeling.yaml",
    "ap_precalculus.polar_functions": _SPECS_DIR / "ap_precalculus" / "polar_functions.yaml",
    "ap_precalculus.data_modeling": _SPECS_DIR / "ap_precalculus" / "data_modeling.yaml",
}

SKILL_ALIASES: dict[str, str] = {
    "experimental_interpretation": "ap_biology.experimental_interpretation",
    "graph_interpretation": "ap_biology.graph_interpretation",
    "variable_analysis": "ap_biology.variable_analysis",
    "evidence_reasoning": "ap_biology.evidence_reasoning",
    "prediction_reasoning": "ap_biology.prediction_reasoning",
    "rates_of_change": "ap_precalculus.rates_of_change",
    "rates-of-change": "ap_precalculus.rates_of_change",
    "limits": "ap_precalculus.rates_of_change",
    "linear-functions": "ap_precalculus.rates_of_change",
    "end_behavior": "ap_precalculus.end_behavior",
    "end-behavior": "ap_precalculus.end_behavior",
    "polynomials": "ap_precalculus.end_behavior",
    "asymptotes": "ap_precalculus.asymptotes",
    "rational-functions": "ap_precalculus.asymptotes",
    "exponential_growth": "ap_precalculus.exponential_growth",
    "exponential-growth": "ap_precalculus.exponential_growth",
    "exponential-functions": "ap_precalculus.exponential_growth",
    "exponential-decay": "ap_precalculus.exponential_growth",
    "logarithmic_expressions": "ap_precalculus.logarithmic_expressions",
    "logarithms": "ap_precalculus.logarithmic_expressions",
    "log-expressions": "ap_precalculus.logarithmic_expressions",
    "sinusoidal_functions": "ap_precalculus.sinusoidal_functions",
    "sinusoidal-functions": "ap_precalculus.sinusoidal_functions",
    "trigonometry": "ap_precalculus.sinusoidal_functions",
    "amplitude-and-period": "ap_precalculus.sinusoidal_functions",
    "sinusoidal_modeling": "ap_precalculus.sinusoidal_modeling",
    "sinusoidal-modeling": "ap_precalculus.sinusoidal_modeling",
    "polar_functions": "ap_precalculus.polar_functions",
    "polar-functions": "ap_precalculus.polar_functions",
    "polar": "ap_precalculus.polar_functions",
    "data_modeling": "ap_precalculus.data_modeling",
    "data-modeling": "ap_precalculus.data_modeling",
    "regression": "ap_precalculus.data_modeling",
}


def resolve_skill_id(skill: str) -> str | None:
    if skill in SKILL_REGISTRY:
        return skill
    if skill in SKILL_ALIASES:
        return SKILL_ALIASES[skill]
    return None


@lru_cache(maxsize=32)
def _load_cached(skill_id: str) -> SkillSpec:
    path = SKILL_REGISTRY[skill_id]
    return load_skill_spec(path)


def get(skill: str) -> SkillSpec | None:
    skill_id = resolve_skill_id(skill)
    if skill_id is None:
        return None
    return _load_cached(skill_id)


def list_skills(subject: str | None = None) -> list[str]:
    if subject is None:
        return sorted(SKILL_REGISTRY.keys())
    prefix = f"{subject}."
    return sorted(skill_id for skill_id in SKILL_REGISTRY if skill_id.startswith(prefix))
