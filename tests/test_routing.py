from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import ap_skill_generator.api as api_mod
from ap_skill_generator.api import _byok_store, _rate_limiter, app, get_engine
from ap_skill_generator.config import Settings
from ap_skill_generator.dependencies import get_settings, reset_settings
from ap_skill_generator.engine import APGenerationEngine
from ap_skill_generator.routing import FreeSampleQuota, ModelRouter
from ap_skill_generator.routing.validation_summary import build_validation_summary, is_usable_status

TEST_SESSION = "00000000-0000-4000-8000-000000000001"


@pytest.fixture
def routed_client():
    _rate_limiter.reset()
    reset_settings()
    _byok_store._entries.clear()
    settings = Settings(
        database_url="sqlite:///:memory:",
        openai_api_key="",
        api_key="",
        apforge_core_api_key="test-core-key",
        apforge_env="production",
        free_sample_size=5,
        free_sample_min_usable=3,
        rate_limit_generate_sample=100,
    )
    engine = APGenerationEngine(settings=settings)
    app.dependency_overrides[get_engine] = lambda: engine
    app.dependency_overrides[get_settings] = lambda: settings
    api_mod._settings = settings
    api_mod._quota = FreeSampleQuota(settings)
    api_mod._router = ModelRouter(
        settings=settings,
        byok_store=_byok_store,
        quota=api_mod._quota,
    )
    client = TestClient(app)
    client.headers.update({"X-APForge-Session": TEST_SESSION})
    yield client, engine, settings
    app.dependency_overrides.clear()
    reset_settings()
    _rate_limiter.reset()
    _byok_store._entries.clear()


def _connect_offline_byok(session_id: str = TEST_SESSION) -> None:
    _byok_store.set(session_id, api_key="")


def test_free_generate_requires_byok(routed_client):
    client, _, _ = routed_client
    response = client.post(
        "/generate",
        json={
            "subject": "ap_precalculus",
            "skill": "limits",
            "difficulty": 2,
            "type": "mcq",
        },
    )
    assert response.status_code == 403


def test_byok_generate_after_connect(routed_client):
    client, _, _ = routed_client
    _connect_offline_byok()
    response = client.post(
        "/generate",
        json={
            "subject": "ap_precalculus",
            "skill": "limits",
            "difficulty": 2,
            "type": "mcq",
        },
    )
    assert response.status_code == 200


def test_sample_marks_consumed_at_three_usable(monkeypatch, routed_client):
    client, engine, settings = routed_client
    statuses = ["accepted", "accepted", "accepted_with_warning", "rejected", "rejected"]
    calls = {"n": 0}

    def fake_generate(self, req, *, route=None, llm_api_key=None, sample_id=None):
        status = statuses[calls["n"]]
        calls["n"] += 1
        return {
            "run_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4()),
            "item": {"metadata": {"model_id": "fake"}},
            "metrics": {},
            "harness": {
                "mode": "warn",
                "status": status,
                "policy_status": status,
                "used_fallback": False,
                "failure_reason_code": "NONE",
                "reasons": [],
                "attempt_count_by_skill": {},
                "repair_classes": [],
            },
        }

    monkeypatch.setattr(APGenerationEngine, "generate", fake_generate)
    response = client.post(
        "/generate/sample",
        json={
            "subject": "ap_precalculus",
            "skill": "limits",
            "difficulty": 2,
            "type": "mcq",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["claim_status"] == "consumed"
    assert body["usable_count"] == 3
    assert api_mod._router.quota.get_status(TEST_SESSION) == "consumed"

    retry = client.post(
        "/generate/sample",
        json={
            "subject": "ap_precalculus",
            "skill": "limits",
            "difficulty": 2,
            "type": "mcq",
        },
    )
    assert retry.status_code == 403


def test_sample_failed_below_threshold(monkeypatch, routed_client):
    client, _, _ = routed_client
    statuses = ["accepted", "rejected", "rejected", "rejected", "rejected"]

    def fake_generate(self, req, *, route=None, llm_api_key=None, sample_id=None):
        idx = fake_generate.counter
        fake_generate.counter += 1
        status = statuses[idx]
        return {
            "run_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4()),
            "item": {},
            "metrics": {},
            "harness": {"status": status, "failure_reason_code": "NONE", "repair_classes": []},
        }

    fake_generate.counter = 0
    monkeypatch.setattr(APGenerationEngine, "generate", fake_generate)
    response = client.post(
        "/generate/sample",
        json={
            "subject": "ap_precalculus",
            "skill": "limits",
            "difficulty": 2,
            "type": "mcq",
        },
    )
    assert response.status_code == 200
    assert response.json()["claim_status"] == "failed"
    assert api_mod._router.free_sample_available(TEST_SESSION) is True


def test_validation_summary_counts_usable():
    items = [
        {"harness": {"status": "accepted", "failure_reason_code": "NONE", "repair_classes": []}, "metrics": {}},
        {"harness": {"status": "fallback", "failure_reason_code": "X", "repair_classes": ["a"]}, "metrics": {}},
    ]
    report = build_validation_summary(items)
    assert report["usable_count"] == 1
    assert is_usable_status("accepted_with_warning")


def test_byok_credentials_reject_empty_key(routed_client):
    client, _, _ = routed_client
    response = client.post("/byok/credentials", json={"api_key": "   "})
    assert response.status_code == 422


def test_quota_concurrent_pending_returns_409(routed_client):
    api_mod._quota.begin_sample(TEST_SESSION, ip_hash="abc")
    with pytest.raises(HTTPException) as exc:
        api_mod._router.resolve_for_sample(TEST_SESSION, ip="127.0.0.1")
    assert exc.value.status_code == 409
