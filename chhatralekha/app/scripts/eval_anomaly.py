"""Score the deterministic anomaly engine against a labeled synthetic set.

Run offline, with no network::

    python -m app.scripts.eval_anomaly
    python -m app.scripts.eval_anomaly --write
    python -m app.scripts.eval_anomaly --commit <sha> --write

The unit of evaluation is a case-student / rule pair. A case is an independent
synthetic snapshot; its ``expected`` list names exactly the case students that
the target rule should flag. Only cases assigned to a rule contribute to that
rule's confusion counts. ``review_only`` cases are reported but never scored.

The detector is never modified to improve a score: this module only calls the
existing ``AnomalyEngine`` and normalises its findings.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from app.models.enums import AdmissionQuota, AnomalyType, Gender, InstitutionType
from app.services.anomaly_engine import AnomalyEngine, DetectedAnomaly, RegistrySnapshot

DATASET_PATH = (
    Path(__file__).resolve().parents[1] / "resources" / "anomaly_benchmark.json"
)
REPORT_PATH = (
    Path(__file__).resolve().parents[3] / "docs" / "ai" / "ANOMALY_BENCHMARK.md"
)
VALID_LABELS = frozenset({"positive", "negative", "boundary", "review_only"})


# --------------------------------------------------------------- fixtures


@dataclass(frozen=True)
class BenchmarkInstitution:
    institution_id: str
    name: str
    institution_type: InstitutionType
    state: str
    city: str
    affiliation_university: str
    approval_year: int
    naac_grade: str


@dataclass(frozen=True)
class BenchmarkProgramme:
    program_id: str
    institution_id: str
    program_name: str
    program_level: str
    approved_intake: int
    max_supernumerary_nri: int
    max_supernumerary_fn_oci: int
    max_supernumerary_tfw: int
    max_pmsss: int
    total_sanctioned: int


@dataclass(frozen=True)
class BenchmarkStudent:
    case_id: str
    apaar_id: str
    student_name: str
    date_of_birth: str
    gender: Gender
    institution_id: str
    program_id: str
    academic_year: str
    admission_quota: AdmissionQuota
    enrollment_date: str
    student_institute_roll_no: str
    nationality: str
    passport_number: str | None
    visa_validity: str | None
    country_of_origin: str | None
    is_active: bool


def load_dataset(path: Path | None = None) -> dict[str, Any]:
    """Load and structurally validate the benchmark dataset."""
    source = path or DATASET_PATH
    data = json.loads(source.read_text(encoding="utf-8"))
    _validate_dataset(data)
    return data


def _validate_dataset(data: Any) -> None:
    for key in ("version", "ruleset_id", "fixture_seed", "rules", "defaults", "cases"):
        if key not in data:
            raise ValueError(f"Benchmark dataset is missing '{key}'")

    rules = data["rules"]
    if not isinstance(rules, list) or not rules:
        raise ValueError("Benchmark dataset must define at least one rule")
    rule_ids = [rule["id"] for rule in rules]
    if len(rule_ids) != len(set(rule_ids)):
        raise ValueError("Benchmark rule IDs must be unique")
    known_types = {member.name for member in AnomalyType}
    for rule in rules:
        if rule["anomaly_type"] not in known_types:
            raise ValueError(f"Unknown anomaly type: {rule['anomaly_type']}")

    case_ids: set[str] = set()
    for case in data["cases"]:
        case_id = case["id"]
        if case_id in case_ids:
            raise ValueError(f"Duplicate benchmark case ID: {case_id}")
        case_ids.add(case_id)
        if case["rule"] not in rule_ids:
            raise ValueError(f"Case {case_id} references unknown rule {case['rule']}")
        if case["label"] not in VALID_LABELS:
            raise ValueError(f"Case {case_id} has invalid label {case['label']}")
        students = case.get("students", [])
        student_ids = [student["case_id"] for student in students]
        if len(student_ids) != len(set(student_ids)):
            raise ValueError(f"Case {case_id} has duplicate case student IDs")
        expected = set(case.get("expected", []))
        unknown = expected - set(student_ids)
        if unknown:
            raise ValueError(f"Case {case_id} expects unknown students: {sorted(unknown)}")
        if not students:
            raise ValueError(f"Case {case_id} has no students")


def build_snapshot(
    case: Mapping[str, Any], dataset: Mapping[str, Any]
) -> tuple[RegistrySnapshot, list[BenchmarkStudent]]:
    """Build an independent engine snapshot and its labeled case students."""
    defaults = dataset["defaults"]

    programme_overrides = {
        (item["institution_id"], item["program_id"]): item
        for item in case.get("programs", [])
    }
    programmes = [
        BenchmarkProgramme(
            **{
                **spec,
                **programme_overrides.get(
                    (spec["institution_id"], spec["program_id"]), {}
                ),
            }
        )
        for spec in defaults["programs"]
    ]
    institutions = [
        BenchmarkInstitution(
            **{**spec, "institution_type": InstitutionType[spec["institution_type"]]}
        )
        for spec in defaults["institutions"]
    ]

    students: list[BenchmarkStudent] = []
    for spec in case["students"]:
        merged = {**defaults["student"], **spec}
        case_id = str(merged.pop("case_id"))
        apaar = str(merged.pop("apaar"))
        merged.setdefault("student_institute_roll_no", f"ROLL-{case_id}")
        merged["gender"] = Gender[merged["gender"]]
        merged["admission_quota"] = AdmissionQuota[merged["admission_quota"]]
        students.append(
            BenchmarkStudent(case_id=case_id, apaar_id=apaar, **merged)
        )

    snapshot = RegistrySnapshot(
        institutions=institutions, programs=programmes, students=students
    )
    return snapshot, students


# ---------------------------------------------------------------- scoring


def _finding_signature(finding: DetectedAnomaly) -> tuple[str, str, str]:
    return (
        finding.student_apaar_id,
        finding.institution_id,
        finding.program_id or "",
    )


def _student_signature(student: BenchmarkStudent) -> tuple[str, str, str]:
    return (student.apaar_id, student.institution_id, student.program_id or "")


def resolve_flagged(
    students: Sequence[BenchmarkStudent],
    findings: Sequence[DetectedAnomaly],
    *,
    active_only: bool,
) -> set[str]:
    """Map engine findings back to case students deterministically.

    Findings are emitted in stable group/row order. Each finding consumes the
    next eligible case student with the same (APAAR, institution, programme)
    signature. Duplicate rows intentionally share a signature; the queue
    distinguishes them. Inactive rows are excluded for rules that only inspect
    active enrolments.
    """
    eligible = [student for student in students if student.is_active] if active_only else list(students)
    queues: dict[tuple[str, str, str], list[str]] = {}
    for student in eligible:
        queues.setdefault(_student_signature(student), []).append(student.case_id)

    flagged: set[str] = set()
    for finding in findings:
        queue = queues.get(_finding_signature(finding))
        if queue:
            flagged.add(queue.pop(0))
    return flagged


def compute_metrics(counts: Mapping[str, int]) -> dict[str, float | None]:
    """Compute precision, recall and F1 with explicit zero denominators."""
    tp = counts["tp"]
    fp = counts["fp"]
    fn = counts["fn"]

    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = None
    if (
        precision is not None
        and recall is not None
        and (precision + recall) > 0
    ):
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "precision": round(precision, 4) if precision is not None else None,
        "recall": round(recall, 4) if recall is not None else None,
        "f1": round(f1, 4) if f1 is not None else None,
    }


def score_case(
    case: Mapping[str, Any],
    dataset: Mapping[str, Any],
    rule: Mapping[str, Any],
    engine: AnomalyEngine,
) -> dict[str, Any]:
    """Score one case for one rule at the case-student level."""
    snapshot, students = build_snapshot(case, dataset)
    anomaly_type = AnomalyType[rule["anomaly_type"]]
    findings = [
        finding
        for finding in engine.evaluate(snapshot)
        if finding.anomaly_type is anomaly_type
    ]
    predicted = resolve_flagged(
        students, findings, active_only=bool(rule.get("active_only"))
    )
    expected = set(case.get("expected", []))
    eligible = {
        student.case_id
        for student in students
        if student.is_active or not rule.get("active_only")
    }

    true_positive = expected & predicted
    false_positive = predicted - expected
    false_negative = expected - predicted
    true_negative = eligible - expected - predicted
    return {
        "case_id": case["id"],
        "label": case["label"],
        "expected": sorted(expected),
        "predicted": sorted(predicted),
        "tp": len(true_positive),
        "fp": len(false_positive),
        "fn": len(false_negative),
        "tn": len(true_negative),
        "pairs": len(eligible),
    }


def _git_commit() -> str:
    root = Path(__file__).resolve().parents[3]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return "unavailable"
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def evaluate(
    dataset: Mapping[str, Any],
    engine: AnomalyEngine | None = None,
    *,
    commit: str | None = None,
) -> dict[str, Any]:
    """Evaluate every rule and assemble a machine-readable report."""
    detector = engine or AnomalyEngine()
    latency_by_case: list[float] = []
    rule_reports: list[dict[str, Any]] = []
    review_cases: list[dict[str, Any]] = []
    label_counts: dict[str, int] = {label: 0 for label in sorted(VALID_LABELS)}

    for case in dataset["cases"]:
        label_counts[case["label"]] = label_counts.get(case["label"], 0) + 1

    for rule in dataset["rules"]:
        counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
        scored_pairs = 0
        scored_cases = 0
        for case in dataset["cases"]:
            if case["rule"] != rule["id"]:
                continue
            started = time.perf_counter()
            result = score_case(case, dataset, rule, detector)
            latency_by_case.append((time.perf_counter() - started) * 1000)
            if case["label"] == "review_only":
                review_cases.append(
                    {
                        "case_id": case["id"],
                        "rule": rule["id"],
                        "expected": result["expected"],
                        "predicted": result["predicted"],
                    }
                )
                continue
            for key in counts:
                counts[key] += result[key]
            scored_pairs += result["pairs"]
            scored_cases += 1

        rule_reports.append(
            {
                "id": rule["id"],
                "name": rule["name"],
                "anomaly_type": rule["anomaly_type"],
                "case_count": scored_cases,
                "pairs": scored_pairs,
                **counts,
                **compute_metrics(counts),
            }
        )

    ordered = sorted(latency_by_case)
    p95_index = max(0, int(len(ordered) * 0.95) - 1) if ordered else 0
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit": commit or _git_commit(),
        "dataset_version": dataset["version"],
        "ruleset_id": dataset["ruleset_id"],
        "fixture_seed": dataset["fixture_seed"],
        "unit": dataset["unit_of_evaluation"],
        "case_count": len(dataset["cases"]),
        "label_counts": label_counts,
        "scored_pairs": sum(rule["pairs"] for rule in rule_reports),
        "rules": rule_reports,
        "review_cases": review_cases,
        "latency_p50_ms": round(statistics.median(ordered), 4) if ordered else 0.0,
        "latency_p95_ms": round(ordered[p95_index], 4) if ordered else 0.0,
        "detector_runs": len(latency_by_case),
    }


# -------------------------------------------------------------- rendering


def _format_metric(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.3f}"


def render_markdown(report: Mapping[str, Any]) -> str:
    """Render the Markdown artefact used for the project report."""
    lines = [
        "# ChhatraLekha — Synthetic Anomaly Benchmark",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        f"Detector source commit: `{report['commit']}`",
        "",
        "This report measures **agreement with constructed labels** on fully "
        "synthetic snapshots. It is reproducible offline with "
        "`python -m app.scripts.eval_anomaly`. The detector is unchanged by "
        "this evaluation.",
        "",
        "## Configuration",
        "",
        "| Setting | Value |",
        "| :--- | :--- |",
        f"| Dataset version | {report['dataset_version']} |",
        f"| Ruleset | `{report['ruleset_id']}` |",
        f"| Fixture seed | `{report['fixture_seed']}` |",
        f"| Unit of evaluation | {report['unit']} |",
        f"| Cases | {report['case_count']} |",
        f"| Scored student-rule pairs | {report['scored_pairs']} |",
        f"| Review-only cases (excluded) | {report['label_counts'].get('review_only', 0)} |",
        "",
        "| Case label | Count |",
        "| :--- | ---: |",
    ]
    for label, count in report["label_counts"].items():
        lines.append(f"| {label} | {count} |")
    lines.extend(
        [
            "",
            "## Per-rule results",
            "",
            "| Rule | Check | Pairs | TP | FP | FN | TN | Precision | Recall | F1 |",
            "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for rule in report["rules"]:
        lines.append(
            f"| {rule['id']} | {rule['name']} | {rule['pairs']} | "
            f"{rule['tp']} | {rule['fp']} | {rule['fn']} | {rule['tn']} | "
            f"{_format_metric(rule['precision'])} | "
            f"{_format_metric(rule['recall'])} | {_format_metric(rule['f1'])} |"
        )

    lines.extend(
        [
            "",
            "`N/A` means the metric denominator was zero; it is never silently "
            "reported as zero.",
            "",
            "## Review-only cases (not scored)",
            "",
        ]
    )
    if report["review_cases"]:
        lines.extend(
            [
                "| Case | Rule | Labeled flags | Observed flags |",
                "| :--- | :--- | :--- | :--- |",
            ]
        )
        for item in report["review_cases"]:
            expected = ", ".join(item["expected"]) or "none"
            predicted = ", ".join(item["predicted"]) or "none"
            lines.append(
                f"| {item['case_id']} | {item['rule']} | {expected} | {predicted} |"
            )
    else:
        lines.append("None.")
    lines.extend(
        [
            "",
            "## Timing (machine-specific)",
            "",
            f"Each of the {report['detector_runs']} case evaluations was timed "
            "once with `time.perf_counter()` in this run. "
            f"p50 = {report['latency_p50_ms']:.3f} ms; "
            f"p95 = {report['latency_p95_ms']:.3f} ms. "
            "These numbers describe this machine only and are not a portable "
            "performance guarantee.",
            "",
            "## Method",
            "",
            "- Each case is an independent, fully synthetic snapshot built from "
            "a versioned JSON fixture with one shared student template.",
            "- `case_id` values are unique across the dataset. APAAR IDs are "
            "reused across independent snapshots and are artificial.",
            "- Each case declares the exact case students its target rule "
            "should flag. Cases for other rules do not enter that rule's "
            "confusion counts.",
            "- `positive` cases contribute true positives and false negatives; "
            "`negative` and `boundary` cases contribute true negatives and "
            "false positives. `boundary` cases probe the edge of a rule.",
            "- A finding is mapped back to a case student by its "
            "(APAAR, institution, programme) signature in stable engine order; "
            "inactive rows are excluded for rules that inspect only active "
            "enrolments.",
            "- `review_only` cases document ambiguous scenarios and are never "
            "converted into binary labels.",
            "- Precision = TP/(TP+FP), recall = TP/(TP+FN), "
            "F1 = 2·precision·recall/(precision+recall).",
            "",
            "## Limitations",
            "",
            "- A curated synthetic set measures agreement with its explicit "
            "labels. It does **not** establish detection accuracy on real "
            "student records.",
            "- Full agreement here is expected: the labels encode documented "
            "rule intent on small, unambiguous snapshots. It is a regression "
            "baseline for the rules, not evidence of production readiness.",
            "- A flagged record is a potential inconsistency for authorised "
            "human review, not evidence of fraud and not a conclusion about a "
            "person.",
            "- These results cannot validate legal compliance, official "
            "registry accuracy, or the behaviour of an external government "
            "service.",
            "- The separate school rule pack is intentionally excluded from "
            "the ten-rule denominator.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the Markdown report")
    parser.add_argument("--commit", help="commit SHA to record instead of the current HEAD")
    args = parser.parse_args(argv)

    # Windows consoles default to cp1252; the report contains Unicode symbols.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    report = evaluate(load_dataset(), commit=args.commit)
    rendered = render_markdown(report)
    print(rendered)

    if args.write:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(rendered, encoding="utf-8")
        print(f"Wrote {REPORT_PATH}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
