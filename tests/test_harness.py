from ap_skill_generator.harness import HarnessPolicy, decide_policy


def _policy(**overrides) -> HarnessPolicy:
    base = {
        "harness_version": "v1",
        "policy_version": "v1",
        "prompt_pack_version": "v1",
        "mode": "warn",
        "retry_budgets": {},
        "thresholds": {
            "schema_score_min": 100,
            "compliance_score_min": 98,
            "consistency_score_min": 95,
            "pedagogy_score_min": 70,
        },
        "hard_fail_rules": {"schema_invalid": True, "compliance_below_threshold": True},
        "soft_fail_rules": {"consistency_below_threshold": True, "pedagogy_below_threshold": True},
        "allow_one_soft_retry": True,
    }
    base.update(overrides)
    return HarnessPolicy(**base)


def test_hard_fail_rules_can_disable_schema_rejection():
    policy = _policy(hard_fail_rules={"schema_invalid": False, "compliance_below_threshold": True})
    decision = decide_policy(
        {"schema_score": 0, "compliance_score": 100, "consistency_score": 100, "pedagogy_score": 100},
        policy,
    )
    assert decision.status != "rejected"
    assert "SCHEMA_INVALID" not in decision.reasons


def test_soft_fail_rules_can_disable_pedagogy_warning():
    policy = _policy(soft_fail_rules={"consistency_below_threshold": True, "pedagogy_below_threshold": False})
    decision = decide_policy(
        {"schema_score": 100, "compliance_score": 100, "consistency_score": 100, "pedagogy_score": 40},
        policy,
    )
    assert decision.status == "accepted"
    assert decision.soft_fail is False
