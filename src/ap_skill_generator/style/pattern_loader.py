from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import StylePattern

_PATTERNS: List[StylePattern] = []
_SKILL_ALIASES: Dict[str, str] = {}
_TOPIC_REGISTRY: dict[str, Any] | None = None


def _data_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "data"


def _patterns_dir() -> Path:
    return _data_dir() / "style_patterns" / "mcq"


def _topic_registry_path() -> Path:
    return _data_dir() / "topic_registry.json"


def _normalize(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def load_topic_registry(registry_path: Optional[Path] = None) -> dict[str, Any]:
    global _TOPIC_REGISTRY
    path = registry_path or _topic_registry_path()
    if not path.is_file():
        _TOPIC_REGISTRY = {"version": 1, "topics": []}
        return _TOPIC_REGISTRY

    _TOPIC_REGISTRY = json.loads(path.read_text(encoding="utf-8"))
    return _TOPIC_REGISTRY


def get_topic_registry() -> dict[str, Any]:
    if _TOPIC_REGISTRY is None:
        load_topic_registry()
    return _TOPIC_REGISTRY or {"version": 1, "topics": []}


def _build_skill_aliases(patterns: List[StylePattern]) -> Dict[str, str]:
    registry = get_topic_registry()
    pattern_by_id = {pattern.id: pattern for pattern in patterns}
    aliases: Dict[str, str] = {}

    for entry in registry.get("topics", []):
        pattern_id = entry.get("pattern_id")
        pattern = pattern_by_id.get(pattern_id)
        if pattern is None:
            continue
        target_skill = pattern.skill
        slugs = [entry.get("slug", "")] + list(entry.get("legacy_slugs", []))
        for slug in slugs:
            if not slug:
                continue
            aliases[_normalize(slug)] = target_skill

    return aliases


def _refresh_skill_aliases(patterns: Optional[List[StylePattern]] = None) -> None:
    global _SKILL_ALIASES
    resolved = patterns if patterns is not None else get_all_patterns()
    _SKILL_ALIASES = _build_skill_aliases(resolved)


def _resolve_skill(skill: str) -> str:
    if not _SKILL_ALIASES:
        if not _PATTERNS:
            load_patterns()
        else:
            _refresh_skill_aliases(_PATTERNS)
    key = _normalize(skill)
    return _SKILL_ALIASES.get(key, skill)


def load_patterns(patterns_dir: Optional[Path] = None) -> List[StylePattern]:
    global _PATTERNS
    if _TOPIC_REGISTRY is None:
        load_topic_registry()

    directory = patterns_dir or _patterns_dir()
    loaded: List[StylePattern] = []
    if not directory.is_dir():
        _PATTERNS = loaded
        _refresh_skill_aliases(loaded)
        return loaded

    for path in sorted(directory.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        loaded.append(StylePattern.model_validate(data))

    _PATTERNS = loaded
    _refresh_skill_aliases(loaded)
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
