import json
from pathlib import Path

from ap_skill_generator.style.pattern_loader import (
    find_pattern,
    get_topic_registry,
    load_patterns,
    load_topic_registry,
)

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "topic_registry.json"


def test_topic_registry_has_nine_primary_topics():
    registry = get_topic_registry()
    assert len(registry["topics"]) == 9


def test_topic_registry_pattern_ids_exist_and_are_unique():
    registry = get_topic_registry()
    patterns = load_patterns()
    pattern_ids = {pattern.id for pattern in patterns}
    registry_ids = [entry["pattern_id"] for entry in registry["topics"]]
    assert len(registry_ids) == len(set(registry_ids))
    assert set(registry_ids).issubset(pattern_ids)


def test_each_primary_slug_resolves_expected_pattern():
    registry = get_topic_registry()
    for entry in registry["topics"]:
        pattern = find_pattern("", entry["slug"])
        assert pattern is not None, f"No pattern for slug {entry['slug']}"
        assert pattern.id == entry["pattern_id"]


def test_legacy_slug_limits_maps_to_rates_of_change():
    pattern = find_pattern("", "limits")
    assert pattern is not None
    assert pattern.id == "rates_of_change_mcq"


def test_legacy_slug_polynomials_maps_to_end_behavior():
    pattern = find_pattern("", "polynomials")
    assert pattern is not None
    assert pattern.id == "polynomial_end_behavior_mcq"


def test_legacy_slug_trigonometry_maps_to_sinusoidal_functions():
    pattern = find_pattern("", "trigonometry")
    assert pattern is not None
    assert pattern.id == "periodic_amplitude_mcq"


def test_registry_json_is_valid():
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    assert data["version"] == 1
    load_topic_registry(REGISTRY_PATH)
