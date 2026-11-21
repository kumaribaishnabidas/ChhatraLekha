"""Tests for the reproducible synthetic anomaly benchmark."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from tempfile import mkstemp

import pytest

from app.models.enums import AnomalySeverity, AnomalyType
from app.scripts.eval_anomaly import (
    DATASET_PATH,
    build_snapshot,
    compute_metrics,
    evaluate,
    load_dataset,
    render_markdown,
    resolve_flagged,
    score_case,
)
from app.services.anomaly_engine import AnomalyEngine, DetectedAnomaly


def _mini_dataset() -> dict:
    """A minimal independent dataset for focused unit tests."""
    return {
        "version": "test",
        "ruleset_id": "TEST_RULES",
        "fixture_seed": "test-seed",
        "unit_of_evaluation": "case student / rule pair",
        "rules": [
            {
                "id": "R01",
                "anomaly_type": "INVALID_APAAR_FORMAT",
                "name": "Test rule",
                "active_only": False,
            }
        ],
        "defaults": {
            "institutions": [
                {
                    "institution_id": "INST-T",
                    "name": "Test Institute",
                    "institution_type": "ENGINEERING",
                    "state": "Karnataka",
                    "city": "Bengaluru",
                    "affiliation_university": "Test University",
                    "approval_year": 2012,
                    "naac_grade": "A",
                }
            ],
            "programs": [
                {
                    "program_id": "PROG-T",
                    "institution_id": "INST-T",
                    "program_name": "Test Programme",
                    "program_level": "UG",
                    "approved_intake": 60,
                    "max_supernumerary_nri": 3,
                    "max_supernumerary_fn_oci": 9,
                    "max_supernumerary_tfw": 3,
                    "max_pmsss": 6,
                    "total_sanctioned": 81,
                }
            ],
            "student": {
                "student_name": "Synthetic Student",
                "date_of_birth": "2004-03-12",
                "gender": "MALE",
                "institution_id": "INST-T",
                "program_id": "PROG-T",
                "academic_year": "2024-25",
                "admission_quota": "MERIT",
                "enrollment_date": "2024-08-01",
                "nationality": "Indian",
                "passport_number": None,
                "visa_validity": None,
                "country_of_origin": None,
                "is_active": True,
            },
        },
        "cases": [],
    }


def test_dataset_file_exists_and_loads():
    assert DATASET_PATH.is_file()
    dataset = load_dataset()

    assert len(dataset["rules"]) == 10
    assert len(dataset["cases"]) >= 40
    assert {rule["anomaly_type"] for rule in dataset["rules"]} == {
        member.name for member in AnomalyType if member.name not in {
            "MINOR_GUARDIAN_REQUIRED",
            "INVALID_AGE_FOR_GRADE",
            "DUPLICATE_SCHOOL_ENROLMENT",
            "SECTION_CAPACITY_EXCEEDED",
            "PROMOTION_WITHOUT_RESULT",
            "MISSING_UDISE_CODE",
        }
    }


def test_every_rule_has_positive_and_negative_coverage():
    dataset = load_dataset()
    for rule in dataset["rules"]:
        labels = {
            case["label"] for case in dataset["cases"] if case["rule"] == rule["id"]
        }
        assert "positive" in labels, rule["id"]
        assert "negative" in labels or "boundary" in labels, rule["id"]


def test_case_identifiers_are_unique():
    dataset = load_dataset()
    case_ids = [case["id"] for case in dataset["cases"]]
    assert len(case_ids) == len(set(case_ids))


def test_repository_dataset_matches_labels():
    report = evaluate(load_dataset(), commit="test")

    assert report["scored_pairs"] > 0
    for rule in report["rules"]:
        assert rule["fp"] == 0, rule["id"]
        assert rule["fn"] == 0, rule["id"]
        assert rule["precision"] == 1.0, rule["id"]
        assert rule["recall"] == 1.0, rule["id"]
        assert rule["f1"] == 1.0, rule["id"]


def test_repeated_runs_are_deterministic():
    dataset = load_dataset()

    def stable(raw: dict) -> dict:
        return {
            key: value
            for key, value in raw.items()
            if key not in {"generated_at", "latency_p50_ms", "latency_p95_ms"}
        }

    assert stable(evaluate(dataset, commit="test")) == stable(
        evaluate(dataset, commit="test")
    )


def test_compute_metrics_handles_zero_denominators():
    empty = compute_metrics({"tp": 0, "fp": 0, "fn": 0, "tn": 5})
    assert empty == {"precision": None, "recall": None, "f1": None}

    no_false_positives = compute_metrics({"tp": 1, "fp": 0, "fn": 1, "tn": 0})
    assert no_false_positives["precision"] == 1.0
    assert no_false_positives["recall"] == 0.5
    assert no_false_positives["f1"] == 0.6667

    no_true_positives = compute_metrics({"tp": 0, "fp": 1, "fn": 0, "tn": 0})
    assert no_true_positives["precision"] == 0.0
    assert no_true_positives["recall"] is None
    assert no_true_positives["f1"] is None


def test_compute_metrics_known_balance():
    metrics = compute_metrics({"tp": 3, "fp": 1, "fn": 1, "tn": 5})
    assert metrics == {"precision": 0.75, "recall": 0.75, "f1": 0.75}


def test_build_snapshot_does_not_share_programme_state():
    dataset = _mini_dataset()
    dataset["cases"] = [
        {
            "id": "C1",
            "rule": "R01",
            "label": "negative",
            "programs": [{"program_id": "PROG-T", "institution_id": "INST-T", "approved_intake": 1}],
            "students": [{"case_id": "S1", "apaar": "984210350001"}],
            "expected": [],
        },
        {
            "id": "C2",
            "rule": "R01",
            "label": "negative",
            "students": [{"case_id": "S1", "apaar": "984210350002"}],
            "expected": [],
        },
    ]

    first, _ = build_snapshot(dataset["cases"][0], dataset)
    second, _ = build_snapshot(dataset["cases"][1], dataset)

    assert first.programs[0].approved_intake == 1
    assert second.programs[0].approved_intake == 60


def test_resolve_flagged_uses_queue_for_duplicate_signatures():
    dataset = _mini_dataset()
    dataset["cases"] = [
        {
            "id": "C1",
            "rule": "R01",
            "label": "positive",
            "students": [
                {"case_id": "S1", "apaar": "984210350010"},
                {"case_id": "S2", "apaar": "984210350010"},
            ],
            "expected": ["S1", "S2"],
        }
    ]
    _, students = build_snapshot(dataset["cases"][0], dataset)
    findings = [
        DetectedAnomaly(
            student_apaar_id="984210350010",
            institution_id="INST-T",
            program_id="PROG-T",
            anomaly_type=AnomalyType.INVALID_APAAR_FORMAT,
            severity=AnomalySeverity.CRITICAL,
            details="",
        )
        for _ in range(2)
    ]

    assert resolve_flagged(students, findings, active_only=False) == {"S1", "S2"}


def test_resolve_flagged_excludes_inactive_rows_for_active_only_rules():
    dataset = _mini_dataset()
    dataset["cases"] = [
        {
            "id": "C1",
            "rule": "R01",
            "label": "negative",
            "students": [
                {"case_id": "S1", "apaar": "984210350011"},
                {"case_id": "S2", "apaar": "984210350011", "is_active": False},
            ],
            "expected": [],
        }
    ]
    _, students = build_snapshot(dataset["cases"][0], dataset)
    finding = DetectedAnomaly(
        student_apaar_id="984210350011",
        institution_id="INST-T",
        program_id="PROG-T",
        anomaly_type=AnomalyType.INVALID_APAAR_FORMAT,
        severity=AnomalySeverity.CRITICAL,
        details="",
    )

    assert resolve_flagged(students, [finding], active_only=True) == {"S1"}


def test_score_case_reports_false_positives_and_false_negatives():
    dataset = _mini_dataset()
    dataset["cases"] = [
        {
            "id": "C1",
            "rule": "R01",
            "label": "positive",
            "students": [{"case_id": "S1", "apaar": "12345"}],
            "expected": ["S1"],
        },
        {
            "id": "C2",
            "rule": "R01",
            "label": "negative",
            "students": [{"case_id": "S1", "apaar": "984210350001"}],
            "expected": [],
        },
    ]
    rule = dataset["rules"][0]
    engine = AnomalyEngine()

    first = score_case(dataset["cases"][0], dataset, rule, engine)
    second = score_case(dataset["cases"][1], dataset, rule, engine)

    assert (first["tp"], first["fp"], first["fn"], first["tn"]) == (1, 0, 0, 0)
    assert (second["tp"], second["fp"], second["fn"], second["tn"]) == (0, 0, 0, 1)

    wrong_labels = copy.deepcopy(dataset)
    wrong_labels["cases"][0]["expected"] = []
    wrong_labels["cases"][1]["expected"] = ["S1"]
    missed = score_case(wrong_labels["cases"][0], wrong_labels, rule, engine)
    spurious = score_case(wrong_labels["cases"][1], wrong_labels, rule, engine)
    assert (missed["tp"], missed["fp"], missed["fn"]) == (0, 1, 0)
    assert (spurious["tp"], spurious["fp"], spurious["fn"]) == (0, 0, 1)


def test_validation_rejects_unknown_rule_and_unknown_expected_student():
    broken = _mini_dataset()
    broken["cases"] = [
        {
            "id": "C1",
            "rule": "R99",
            "label": "positive",
            "students": [{"case_id": "S1", "apaar": "12345"}],
            "expected": ["S1"],
        }
    ]
    with pytest.raises(ValueError, match="unknown rule"):
        load_dataset(_write_dataset(broken))

    broken["cases"][0]["rule"] = "R01"
    broken["cases"][0]["expected"] = ["S9"]
    with pytest.raises(ValueError, match="unknown students"):
        load_dataset(_write_dataset(broken))


def _write_dataset(dataset: dict, path: Path | None = None) -> Path:
    handle, name = mkstemp(suffix=".json")
    os.close(handle)
    target = path or Path(name)
    target.write_text(json.dumps(dataset), encoding="utf-8")
    return target


def test_render_markdown_contains_metrics_and_limitations():
    report = evaluate(load_dataset(), commit="test")
    markdown = render_markdown(report)

    assert "Synthetic Anomaly Benchmark" in markdown
    assert "Per-rule results" in markdown
    assert "N/A" in markdown
    assert "does **not** establish detection accuracy" in markdown
    assert "Review-only cases" in markdown
    assert "R10" in markdown
