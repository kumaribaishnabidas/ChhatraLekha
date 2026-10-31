"""Verification against the versioned canonical rule test fixtures.

Both backend and mobile validator implementations use this shared fixture
to prevent divergence between server-side and offline client validation rules.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.models.enums import AdmissionQuota
from app.services import apaar_validator
from app.services.anomaly_engine import (
    quota_nationality_conflict,
)

FIXTURES_PATH = Path(__file__).resolve().parent.parent / "app" / "resources" / "rule_test_fixtures.json"


def _load_fixtures() -> dict:
    with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_shared_fixtures_file_exists_and_versioned():
    assert FIXTURES_PATH.is_file(), f"Fixture file not found at {FIXTURES_PATH}"
    fixtures = _load_fixtures()
    assert fixtures.get("version") == "1.0.0"
    assert fixtures.get("ruleset_id") == "CHHATRALEKHA_RULES_2026_V1"
    assert "apaar_validation_cases" in fixtures
    assert "anomaly_rule_vectors" in fixtures


def test_canonical_apaar_validation_vectors():
    fixtures = _load_fixtures()
    cases = fixtures["apaar_validation_cases"]
    assert len(cases) >= 10

    for case in cases:
        case_id = case["id"]
        raw_input = case["input"]
        expected_valid = case["expected_valid"]

        res = apaar_validator.validate(raw_input)
        if expected_valid:
            assert res.is_structurally_valid, (
                f"Case '{case_id}' ({case['description']}) was expected to be valid, "
                f"but failed with errors: {res.errors}"
            )
            if "expected_normalised" in case:
                assert res.normalised == case["expected_normalised"], (
                    f"Case '{case_id}' expected normalised {case['expected_normalised']} "
                    f"got {res.normalised}"
                )
        else:
            assert not res.is_structurally_valid, (
                f"Case '{case_id}' ({case['description']}) was expected to be invalid, but passed."
            )
            if "error_keyword" in case:
                keyword = case["error_keyword"].lower()
                has_keyword = any(keyword in err.lower() for err in res.errors)
                assert has_keyword, (
                    f"Case '{case_id}' expected error containing '{keyword}', got errors: {res.errors}"
                )


def test_canonical_anomaly_rule_vectors():
    fixtures = _load_fixtures()
    vectors = fixtures["anomaly_rule_vectors"]

    for rule_vector in vectors:
        rule_id = rule_vector["rule_id"]
        for tc in rule_vector["test_cases"]:
            desc = tc["description"]
            expected_anomaly = tc["expected_anomaly"]

            if rule_id == "RULE-QUOTA-NATIONALITY":
                nationality = tc["nationality"]
                quota = AdmissionQuota.from_code(tc["admission_quota"])
                assert quota is not None, f"Unknown quota code: {tc['admission_quota']}"
                conflict = quota_nationality_conflict(quota, nationality)
                if expected_anomaly:
                    assert conflict is not None, (
                        f"Expected anomaly for {desc}, but none detected."
                    )
                else:
                    assert conflict is None, (
                        f"Expected no anomaly for {desc}, but detected: {conflict}"
                    )
