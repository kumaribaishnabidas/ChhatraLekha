"""The Academic Record Change Impact Detector.

The engine answers one question: *if this correction is applied, what else
might now be wrong?* It is a pure function - no database access, no side
effects - so it can be run as a **preview** before anything is written, and
run again for real when the correction is applied.

The rules are deterministic. No model decides whether a record is valid, and
nothing here ever modifies a linked record: the engine produces findings and
a checklist for an authorised human to work through.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import date
from typing import Any, Iterable, Optional, Sequence

from app.services import apaar_validator
from app.services.policy import QUOTA_TO_BUCKET, Policy

#: The severities, most serious first.
SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}

#: The certainties, most certain first.
CERTAINTY_ORDER = {"confirmed": 0, "suspected": 1, "review_only": 2}

#: The fields that the credential seal commits to. A change to any of them
#: makes every issued seal, QR badge and certificate describe outdated data.
SEAL_BOUND_FIELDS = (
    "apaar_id",
    "institution_id",
    "program_id",
    "academic_year",
    "enrollment_date",
    "student_name",
    "date_of_birth",
    "gender",
    "admission_quota",
    "nationality",
    "student_institute_roll_no",
)

#: The fields a correction may change.
CORRECTABLE_FIELDS = SEAL_BOUND_FIELDS + (
    "contact_email",
    "contact_phone",
    "state_of_domicile",
    "social_category",
    "admission_date",
)

#: The fields that are compared for the intake.
SEAT_FIELDS = ("institution_id", "program_id", "academic_year")


@dataclass
class Finding:
    """One thing that a proposed correction might affect."""

    rule_id: str
    title: str
    explanation: str
    affected_refs: list[str] = dataclass_field(default_factory=list)
    severity: str = "MEDIUM"
    certainty: str = "suspected"
    suggested_action: str = ""
    human_review_required: bool = True
    institution_id: str = ""
    rule_data: dict[str, Any] = dataclass_field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "explanation": self.explanation,
            "affected_refs": list(self.affected_refs),
            "severity": self.severity,
            "certainty": self.certainty,
            "suggested_action": self.suggested_action,
            "human_review_required": self.human_review_required,
            "institution_id": self.institution_id,
            "rule_data": dict(self.rule_data),
        }


@dataclass
class ImpactAssessment:
    """The whole assessment of one proposed correction."""

    student_record_id: str
    changed_fields: list[str] = dataclass_field(default_factory=list)
    findings: list[Finding] = dataclass_field(default_factory=list)

    @property
    def highest_severity(self) -> str:
        """The most serious severity among the findings."""
        if not self.findings:
            return "INFO"
        return min(
            (finding.severity for finding in self.findings),
            key=lambda severity: SEVERITY_ORDER.get(severity, 9),
        )

    @property
    def requires_review(self) -> bool:
        return any(finding.human_review_required for finding in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_record_id": self.student_record_id,
            "changed_fields": list(self.changed_fields),
            "findings": [finding.to_dict() for finding in self.findings],
            "highest_severity": self.highest_severity,
            "requires_review": self.requires_review,
        }


# ------------------------------------------------------------------ helpers


def _ref(document: dict[str, Any]) -> str:
    """The internal reference of a document - never a raw APAAR ID."""
    if document.get("_id") is not None:
        return str(document["_id"])
    return str(document.get("record_id", ""))


def _bucket_of(quota: str) -> str:
    return QUOTA_TO_BUCKET.get(str(quota or "").upper(), "REGULAR")


def _academic_year_of(enrollment_date: str) -> str:
    """The academic year an enrolment date falls in (Indian convention: July-June)."""
    if not enrollment_date:
        return ""
    try:
        parsed = date.fromisoformat(str(enrollment_date)[:10])
    except ValueError:
        return ""
    if parsed.month >= 7:
        return f"{parsed.year}-{str(parsed.year + 1)[-2:]}"
    return f"{parsed.year - 1}-{str(parsed.year)[-2:]}"


def changed_fields(
    current: dict[str, Any], proposed: dict[str, Any]
) -> dict[str, tuple[Any, Any]]:
    """The fields the correction changes, as ``{field: (before, after)}``."""
    changes: dict[str, tuple[Any, Any]] = {}
    for field, after in proposed.items():
        if field not in CORRECTABLE_FIELDS:
            continue
        before = current.get(field)
        if (before or "") == (after or ""):
            continue
        changes[field] = (before, after)
    return changes


def _enrolment_counts(
    students: Sequence[dict[str, Any]],
    institution_id: str,
    program_id: str,
    academic_year: str,
    *,
    exclude_record_ids: Iterable[str] = (),
) -> dict[str, int]:
    """The enrolment of one programme in one year, per seat bucket."""
    excluded = set(exclude_record_ids)
    counts = {"REGULAR": 0, "NRI": 0, "FN_OCI": 0, "TFW": 0, "PMSSS": 0}
    for student in students:
        if str(student.get("_id", "")) in excluded:
            continue
        if not student.get("is_active", True):
            continue
        if student.get("record_status", "ACTIVE") != "ACTIVE":
            continue
        if student.get("institution_id") != institution_id:
            continue
        if student.get("program_id") != program_id:
            continue
        if academic_year and student.get("academic_year") != academic_year:
            continue
        bucket = _bucket_of(student.get("admission_quota", ""))
        counts[bucket] = counts.get(bucket, 0) + 1
        if student.get("admission_quota") == "PMSSS":
            counts["PMSSS"] = counts.get("PMSSS", 0) + 1
    return counts


def _programme_for(
    programs: Sequence[dict[str, Any]], institution_id: str, program_id: str
) -> Optional[dict[str, Any]]:
    for programme in programs:
        if (
            programme.get("institution_id") == institution_id
            and programme.get("program_id") == program_id
        ):
            return programme
    return None


# ------------------------------------------------------------------- rules


def rule_a_identifier_change(
    student: dict[str, Any],
    changes: dict[str, tuple[Any, Any]],
    students: Sequence[dict[str, Any]],
    anomalies: Sequence[dict[str, Any]],
    revoked: Sequence[dict[str, Any]],
) -> list[Finding]:
    """``CIA-A`` - the APAAR identifier changes."""
    if "apaar_id" not in changes:
        return []
    before, after = changes["apaar_id"]
    findings: list[Finding] = []

    validation = apaar_validator.validate(str(after))
    if not validation.is_structurally_valid:
        findings.append(
            Finding(
                rule_id="CIA-A",
                title="The new APAAR ID is not structurally valid",
                explanation=(
                    f"'{after}' does not satisfy the 12-digit registry structure. "
                    + " ".join(validation.errors)
                ),
                affected_refs=[_ref(student)],
                severity="CRITICAL",
                certainty="confirmed",
                suggested_action=(
                    "Do not apply the correction until the identifier matches the "
                    "APAAR card exactly."
                ),
            )
        )
        return findings

    same_institution = [
        other
        for other in students
        if other.get("apaar_id") == after
        and other.get("institution_id") == student.get("institution_id")
        and str(other.get("_id", "")) != str(student.get("_id", ""))
    ]
    other_institution = [
        other
        for other in students
        if other.get("apaar_id") == after
        and other.get("institution_id") != student.get("institution_id")
    ]

    if same_institution:
        findings.append(
            Finding(
                rule_id="CIA-A",
                title="The new APAAR ID is already used in this institution",
                explanation=(
                    f"{len(same_institution)} other record(s) at "
                    f"{student.get('institution_id')} already claim this identifier. "
                    "Two records in one institution with the same identifier is a "
                    "duplicate that has to be resolved before the correction is applied."
                ),
                affected_refs=[_ref(other) for other in same_institution],
                severity="CRITICAL",
                certainty="confirmed",
                suggested_action=(
                    "Check which of the two records is the authoritative admission, "
                    "then withdraw the other through a separate authorised action."
                ),
                institution_id=str(student.get("institution_id", "")),
            )
        )

    if other_institution:
        findings.append(
            Finding(
                rule_id="CIA-A",
                title="The new APAAR ID is also held by another institution",
                explanation=(
                    f"{len(other_institution)} record(s) at "
                    f"{len({o.get('institution_id') for o in other_institution})} other "
                    "institution(s) already claim this identifier. A person enrolled "
                    "at two institutions at once is a **potential conflict that has to "
                    "be reviewed by a person** - it is not, by itself, evidence of "
                    "anything, and it is never treated as fraud by the system."
                ),
                affected_refs=[_ref(other) for other in other_institution],
                severity="HIGH",
                certainty="suspected",
                suggested_action=(
                    "Refer this to the AICTE duplicate-records desk. Ask both "
                    "institutions to confirm the admission before any record is "
                    "withdrawn."
                ),
                institution_id=str(student.get("institution_id", "")),
            )
        )

    stale_anomalies = [
        anomaly
        for anomaly in anomalies
        if anomaly.get("student_apaar_id") == before
    ]
    if stale_anomalies:
        findings.append(
            Finding(
                rule_id="CIA-A",
                title="Existing findings still point at the old identifier",
                explanation=(
                    f"{len(stale_anomalies)} anomaly record(s) reference the previous "
                    "identifier. They have to be re-evaluated against the new one, "
                    "otherwise the review queue keeps a stale reference."
                ),
                affected_refs=[
                    str(anomaly.get("_id", "")) for anomaly in stale_anomalies
                ],
                severity="MEDIUM",
                certainty="confirmed",
                suggested_action=(
                    "Re-run the anomaly engine after the correction and review the "
                    "findings that disappear or change."
                ),
            )
        )

    revoked_for_old = [entry for entry in revoked if entry.get("apaar_id") == before]
    if revoked_for_old:
        findings.append(
            Finding(
                rule_id="CIA-A",
                title="The old identifier is on the revocation list",
                explanation=(
                    f"{len(revoked_for_old)} revocation record(s) exist for the "
                    "previous identifier. The correction does not clear them - a "
                    "revocation is a decision, not a side effect."
                ),
                affected_refs=[str(entry.get("_id", "")) for entry in revoked_for_old],
                severity="HIGH",
                certainty="confirmed",
                suggested_action=(
                    "Ask the officer who revoked the credential whether the "
                    "revocation still applies after the correction."
                ),
            )
        )
    return findings


def rule_b_institution_or_programme_change(
    student: dict[str, Any],
    changes: dict[str, tuple[Any, Any]],
    programs: Sequence[dict[str, Any]],
    students: Sequence[dict[str, Any]],
) -> list[Finding]:
    """``CIA-B`` - the institution or the programme changes."""
    findings: list[Finding] = []
    touches = {"institution_id", "program_id"} & set(changes)
    if not touches:
        return findings

    before_institution = str(student.get("institution_id", ""))
    before_programme = str(student.get("program_id", ""))
    after_institution = str(changes.get("institution_id", (before_institution, before_institution))[1])
    after_programme = str(changes.get("program_id", (before_programme, before_programme))[1])

    destination = _programme_for(programs, after_institution, after_programme)
    if destination is None:
        findings.append(
            Finding(
                rule_id="CIA-B",
                title="The destination programme is not sanctioned for the institution",
                explanation=(
                    f"'{after_programme}' is not an approved programme of "
                    f"{after_institution}. An enrolment in an unsanctioned course "
                    "cannot be regularised."
                ),
                affected_refs=[_ref(student)],
                severity="CRITICAL",
                certainty="confirmed",
                suggested_action=(
                    "Enrol the student in an approved programme, or obtain the AICTE "
                    "approval for the course code first."
                ),
                institution_id=after_institution,
            )
        )
    else:
        findings.append(
            Finding(
                rule_id="CIA-B",
                title="The destination programme's seats have to be recalculated",
                explanation=(
                    f"'{after_programme}' at {after_institution} has "
                    f"{destination.get('approved_intake', 0)} sanctioned seats. Moving "
                    "this enrolment changes both the source and the destination seat "
                    "count, so the intake figures of both programmes have to be "
                    "recalculated."
                ),
                affected_refs=[_ref(student)],
                severity="MEDIUM",
                certainty="confirmed",
                suggested_action=(
                    "Re-run the intake monitoring for the source and the destination "
                    "programme after the correction."
                ),
                institution_id=after_institution,
                rule_data={
                    "source_programme": before_programme,
                    "destination_programme": after_programme,
                    "source_institution": before_institution,
                    "destination_institution": after_institution,
                },
            )
        )

    if before_programme != after_programme or before_institution != after_institution:
        findings.append(
            Finding(
                rule_id="CIA-B",
                title="The seat count of the source programme changes",
                explanation=(
                    f"The enrolment leaves '{before_programme}' at {before_institution}. "
                    "The source programme's utilisation has to be recalculated as well "
                    "as the destination's."
                ),
                affected_refs=[_ref(student)],
                severity="LOW",
                certainty="confirmed",
                suggested_action=(
                    "Re-run the intake monitoring for the source programme."
                ),
                institution_id=before_institution,
            )
        )

    roll_no = str(student.get("student_institute_roll_no", "")).strip().upper()
    if roll_no:
        clashes = [
            other
            for other in students
            if other.get("institution_id") == after_institution
            and str(other.get("student_institute_roll_no", "")).strip().upper() == roll_no
            and str(other.get("_id", "")) != str(student.get("_id", ""))
        ]
        if clashes:
            findings.append(
                Finding(
                    rule_id="CIA-B",
                    title="The roll number is already used at the destination",
                    explanation=(
                        f"Roll number '{roll_no}' is already held by "
                        f"{len(clashes)} other record(s) at {after_institution}. The "
                        "institute's own systems key on the roll number, so this makes "
                        "them ambiguous."
                    ),
                    affected_refs=[_ref(other) for other in clashes],
                    severity="HIGH",
                    certainty="confirmed",
                    suggested_action=(
                        "Ask the destination institution to re-issue a unique roll "
                        "number before the correction is applied."
                    ),
                    institution_id=after_institution,
                )
            )
    return findings


def rule_c_academic_year_change(
    student: dict[str, Any],
    changes: dict[str, tuple[Any, Any]],
    students: Sequence[dict[str, Any]],
    anomalies: Sequence[dict[str, Any]],
) -> list[Finding]:
    """``CIA-C`` - the academic year or the enrolment date changes."""
    findings: list[Finding] = []
    before_year = str(student.get("academic_year", ""))
    after_year = str(changes.get("academic_year", (before_year, before_year))[1])

    if "academic_year" in changes or "enrollment_date" in changes:
        findings.append(
            Finding(
                rule_id="CIA-C",
                title="The enrolment has to be counted in both academic years",
                explanation=(
                    f"The enrolment moves from '{before_year}' to '{after_year}'. The "
                    "intake of both years changes, because an enrolment is counted "
                    "against the year it was made."
                ),
                affected_refs=[_ref(student)],
                severity="MEDIUM",
                certainty="confirmed",
                suggested_action=(
                    "Recalculate the intake of both academic years and check that "
                    "neither year now breaches its sanctioned capacity."
                ),
                institution_id=str(student.get("institution_id", "")),
                rule_data={"old_academic_year": before_year, "new_academic_year": after_year},
            )
        )

    if "enrollment_date" in changes:
        before_date, after_date = changes["enrollment_date"]
        dob = str(student.get("date_of_birth", "")).strip()
        if dob and after_date:
            try:
                born = date.fromisoformat(dob[:10])
                enrolled = date.fromisoformat(str(after_date)[:10])
            except ValueError:
                born = enrolled = None  # type: ignore[assignment]
            if born and enrolled and enrolled < born:
                findings.append(
                    Finding(
                        rule_id="CIA-C",
                        title="The new enrolment date precedes the date of birth",
                        explanation=(
                            f"The proposed enrolment date '{after_date}' is before the "
                            f"date of birth '{dob}'. The record would be impossible."
                        ),
                        affected_refs=[_ref(student)],
                        severity="CRITICAL",
                        certainty="confirmed",
                        suggested_action=(
                            "Correct the enrolment date against the admission "
                            "document."
                        ),
                        institution_id=str(student.get("institution_id", "")),
                    )
                )
        derived = _academic_year_of(str(after_date))
        if derived and after_year and derived != after_year:
            findings.append(
                Finding(
                    rule_id="CIA-C",
                    title="The enrolment date falls in a different academic year",
                    explanation=(
                        f"The enrolment date '{after_date}' falls in the academic year "
                        f"'{derived}', but the record says '{after_year}'. One of the "
                        "two has to be right."
                    ),
                    affected_refs=[_ref(student)],
                    severity="HIGH",
                    certainty="confirmed",
                    suggested_action=(
                        "Ask the institution which value is correct: the enrolment date "
                        "or the academic year."
                    ),
                    institution_id=str(student.get("institution_id", "")),
                )
            )

    year_anomalies = [
        anomaly
        for anomaly in anomalies
        if str(anomaly.get("academic_year", "")) == before_year
        or str(anomaly.get("academic_year", "")) == after_year
    ]
    if year_anomalies and before_year != after_year:
        findings.append(
            Finding(
                rule_id="CIA-C",
                title="Findings tied to the old academic year have to be revisited",
                explanation=(
                    f"{len(year_anomalies)} anomaly record(s) reference the academic "
                    f"year '{before_year}'. The detection engine is re-run after every "
                    "correction, so they will be recalculated - but a reviewer should "
                    "confirm the outcome."
                ),
                affected_refs=[str(anomaly.get("_id", "")) for anomaly in year_anomalies],
                severity="LOW",
                certainty="confirmed",
                suggested_action="Review the recalculated findings after the correction.",
            )
        )
    return findings


def rule_d_quota_change(
    student: dict[str, Any],
    changes: dict[str, tuple[Any, Any]],
    students: Sequence[dict[str, Any]],
    programs: Sequence[dict[str, Any]],
    policy: Policy,
) -> list[Finding]:
    """``CIA-D`` - the quota bucket or the nationality changes."""
    findings: list[Finding] = []
    if not {"admission_quota", "nationality"} & set(changes):
        return findings

    after_quota = str(
        changes.get("admission_quota", (student.get("admission_quota"), student.get("admission_quota")))[1]
    )
    after_nationality = str(
        changes.get("nationality", (student.get("nationality"), student.get("nationality")))[1]
    )
    institution_id = str(student.get("institution_id", ""))
    program_id = str(student.get("program_id", ""))
    academic_year = str(student.get("academic_year", ""))

    programme = _programme_for(programs, institution_id, program_id)
    approved = int((programme or {}).get("approved_intake", 0) or 0)

    bucket = _bucket_of(after_quota)
    if bucket != "REGULAR":
        rule = policy.rule_for(bucket)
        if rule is None or not policy.supports(bucket):
            findings.append(
                Finding(
                    rule_id="CIA-D",
                    title=f"The policy does not define a ceiling for the {bucket} bucket",
                    explanation=(
                        f"The active policy '{policy.policy_id}' does not state a "
                        f"ceiling for the {bucket} seat category, so the platform "
                        "cannot compute the consequence of this change. It is reported "
                        "for a human decision rather than guessed at."
                    ),
                    affected_refs=[_ref(student)],
                    severity="MEDIUM",
                    certainty="review_only",
                    suggested_action=(
                        "Ask the AICTE Directorate to publish the ceiling for this "
                        "category, or apply the correction and have the intake "
                        "reviewed by an officer."
                    ),
                    institution_id=institution_id,
                )
            )
        else:
            cap = rule.cap_for(approved)
            counts = _enrolment_counts(
                students,
                institution_id,
                program_id,
                academic_year,
                exclude_record_ids=[str(student.get("_id", ""))],
            )
            projected = counts.get(bucket, 0) + 1
            if projected > cap:
                findings.append(
                    Finding(
                        rule_id="CIA-D",
                        title=f"The {bucket} ceiling would be exceeded",
                        explanation=(
                            f"Moving this admission into the {after_quota} bucket "
                            f"gives {projected} {bucket} admissions against a ceiling of "
                            f"{cap} ({rule.describe(approved)}), under policy "
                            f"'{policy.policy_id}'."
                        ),
                        affected_refs=[_ref(student)],
                        severity="HIGH",
                        certainty="confirmed",
                        suggested_action=(
                            "Check the ceiling for the academic year and either "
                            "withdraw the admission or obtain the approval that "
                            "allows it."
                        ),
                        institution_id=institution_id,
                        rule_data={
                            "bucket": bucket,
                            "cap": cap,
                            "projected": projected,
                            "policy_id": policy.policy_id,
                        },
                    )
                )

    # Category consistency, exactly as the anomaly engine applies it.
    conflict = _quota_nationality_conflict(after_quota, after_nationality)
    if conflict:
        findings.append(
            Finding(
                rule_id="CIA-D",
                title="The quota bucket and the nationality contradict each other",
                explanation=conflict,
                affected_refs=[_ref(student)],
                severity="CRITICAL" if after_quota == "SUPERNUMERARY_FN" else "HIGH",
                certainty="confirmed",
                suggested_action=(
                    "Ask the institution to correct the quota bucket or attach the "
                    "missing foreign-national documentation."
                ),
                institution_id=institution_id,
            )
        )
    return findings


def _quota_nationality_conflict(quota: str, nationality: str) -> str:
    """The quota / nationality contradiction, or an empty string."""
    if not nationality.strip():
        return ""
    upper = nationality.strip().upper()
    indian = upper in {"INDIAN", "INDIA"} or "INDIAN" in upper or "OCI" in upper

    if quota == "SUPERNUMERARY_FN" and indian:
        return (
            "A foreign-national seat cannot be held by an Indian citizen. The "
            "corrected record declares the nationality as "
            f"'{nationality}'."
        )
    if quota == "SUPERNUMERARY_NRI" and not indian:
        return (
            "The NRI supernumerary is reserved for Indian nationals, so the "
            f"corrected nationality '{nationality}' belongs in a different bucket."
        )
    if quota == "SUPERNUMERARY_TFW" and not indian:
        return (
            "The tuition fee waiver is reserved for Indian nationals, so the "
            f"corrected nationality '{nationality}' is not consistent with it."
        )
    if quota == "PMSSS" and not indian:
        return (
            "The PMSSS scheme is reserved for Indian nationals, so the corrected "
            f"nationality '{nationality}' is not consistent with it."
        )
    if quota in {"REGULAR_MERIT", "MANAGEMENT"} and not indian:
        return (
            "A regular seat is counted against the sanctioned intake for Indian "
            f"domicile students, so the corrected nationality '{nationality}' needs "
            "the institution to confirm it."
        )
    return ""


def rule_e_intake_impact(
    student: dict[str, Any],
    changes: dict[str, tuple[Any, Any]],
    students: Sequence[dict[str, Any]],
    programs: Sequence[dict[str, Any]],
    policy: Policy,
) -> list[Finding]:
    """``CIA-E`` - the correction moves a seat count.

    The comparison is always per institution, programme, academic year and seat
    category. A single global number would be meaningless: two programmes of
    the same institution have different capacities, and two years of the same
    programme are counted separately.
    """
    findings: list[Finding] = []
    if not set(changes) & set(SEAT_FIELDS) and not {"admission_quota", "enrollment_date"} & set(changes):
        return findings

    institution_id = str(
        changes.get("institution_id", (student.get("institution_id"), student.get("institution_id")))[1]
    )
    program_id = str(
        changes.get("program_id", (student.get("program_id"), student.get("program_id")))[1]
    )
    academic_year = str(
        changes.get("academic_year", (student.get("academic_year"), student.get("academic_year")))[1]
    )
    quota = str(
        changes.get("admission_quota", (student.get("admission_quota"), student.get("admission_quota")))[1]
    )

    programme = _programme_for(programs, institution_id, program_id)
    if programme is None:
        return findings

    approved = int(programme.get("approved_intake", 0) or 0)
    counts = _enrolment_counts(
        students,
        institution_id,
        program_id,
        academic_year,
        exclude_record_ids=[str(student.get("_id", ""))],
    )
    bucket = _bucket_of(quota)
    projected_regular = counts.get("REGULAR", 0) + (1 if bucket == "REGULAR" else 0)
    projected_pmsss = counts.get("PMSSS", 0) + (1 if quota == "PMSSS" else 0)

    if projected_regular > approved:
        findings.append(
            Finding(
                rule_id="CIA-E",
                title="The corrected enrolment would exceed the sanctioned intake",
                explanation=(
                    f"'{program_id}' at {institution_id} for {academic_year} would hold "
                    f"{projected_regular} regular enrolments against "
                    f"{approved} sanctioned seats. The comparison is made for this "
                    "institution, programme, academic year and seat category only."
                ),
                affected_refs=[_ref(student)],
                severity="CRITICAL",
                certainty="confirmed",
                suggested_action=(
                    "Refer the programme to the regional office: the excess seat needs "
                    "AICTE approval before it can be regularised."
                ),
                institution_id=institution_id,
                rule_data={
                    "institution_id": institution_id,
                    "program_id": program_id,
                    "academic_year": academic_year,
                    "bucket": "REGULAR",
                    "approved": approved,
                    "projected": projected_regular,
                },
            )
        )

    if quota == "PMSSS":
        rule = policy.rule_for("PMSSS")
        if rule is not None and policy.supports("PMSSS"):
            cap = rule.cap_for(approved)
            if projected_pmsss > cap:
                findings.append(
                    Finding(
                        rule_id="CIA-E",
                        title="The PMSSS ceiling would be exceeded",
                        explanation=(
                            f"The corrected record gives {projected_pmsss} PMSSS "
                            f"admissions against a ceiling of {cap} "
                            f"({rule.describe(approved)}), under policy "
                            f"'{policy.policy_id}'."
                        ),
                        affected_refs=[_ref(student)],
                        severity="HIGH",
                        certainty="confirmed",
                        suggested_action=(
                            "Check the per-course PMSSS ceiling for the academic year."
                        ),
                        institution_id=institution_id,
                        rule_data={
                            "institution_id": institution_id,
                            "program_id": program_id,
                            "academic_year": academic_year,
                            "bucket": "PMSSS",
                            "cap": cap,
                            "projected": projected_pmsss,
                        },
                    )
                )
    return findings


def rule_f_stale_credentials(
    student: dict[str, Any],
    changes: dict[str, tuple[Any, Any]],
    tokens: Sequence[dict[str, Any]],
    seals: Sequence[dict[str, Any]] = (),
) -> list[Finding]:
    """``CIA-F`` - the correction invalidates a credential that was issued.

    The seal commits to the fields in ``SEAL_BOUND_FIELDS``. When one of them
    changes, every badge, certificate and verification token that was issued
    against the old values describes outdated data.
    """
    findings: list[Finding] = []
    touched = sorted(set(changes) & set(SEAL_BOUND_FIELDS))
    if not touched:
        return findings

    affected_tokens = [
        token
        for token in tokens
        if token.get("student_record_id") == str(student.get("_id", ""))
        and not token.get("revoked")
    ]
    if affected_tokens:
        findings.append(
            Finding(
                rule_id="CIA-F",
                title="The verification tokens issued for this record are out of date",
                explanation=(
                    f"{len(affected_tokens)} verification token(s) were issued against "
                    f"the previous values of {', '.join(touched)}. The seal commits to "
                    "those fields, so those tokens now describe outdated data."
                ),
                affected_refs=[str(token.get("_id", "")) for token in affected_tokens],
                severity="HIGH",
                certainty="confirmed",
                suggested_action=(
                    "Mark the tokens as needing reissue and print a fresh QR badge and "
                    "certificate for the student."
                ),
                institution_id=str(student.get("institution_id", "")),
                rule_data={"fields": touched, "tokens": len(affected_tokens)},
            )
        )

    if seals:
        findings.append(
            Finding(
                rule_id="CIA-F",
                title="The sealed credential has to be re-issued",
                explanation=(
                    f"{len(seals)} sealed credential(s) were issued against the "
                    f"previous values of {', '.join(touched)}. A seal is only valid "
                    "for the record it was computed from."
                ),
                affected_refs=[str(seal.get("_id", "")) for seal in seals],
                severity="HIGH",
                certainty="confirmed",
                suggested_action=(
                    "Re-seal the credential and reprint the certificate."
                ),
                institution_id=str(student.get("institution_id", "")),
            )
        )
    return findings


# ------------------------------------------------------------------ engine


def assess(
    student: dict[str, Any],
    proposed: dict[str, Any],
    *,
    students: Sequence[dict[str, Any]],
    programs: Sequence[dict[str, Any]],
    anomalies: Sequence[dict[str, Any]] = (),
    consents: Sequence[dict[str, Any]] = (),
    tokens: Sequence[dict[str, Any]] = (),
    seals: Sequence[dict[str, Any]] = (),
    revoked: Sequence[dict[str, Any]] = (),
    policy: Optional[Policy] = None,
) -> ImpactAssessment:
    """Assess a proposed correction.

    The function is pure: it reads the registry snapshot it is given and
    returns the findings. Nothing is written, and no linked record is
    modified.
    """
    policy = policy or Policy()
    changes = changed_fields(student, proposed)

    assessment = ImpactAssessment(
        student_record_id=str(student.get("_id", "")),
        changed_fields=sorted(changes),
    )
    if not changes:
        return assessment

    assessment.findings += rule_a_identifier_change(
        student, changes, students, anomalies, revoked
    )
    assessment.findings += rule_b_institution_or_programme_change(
        student, changes, programs, students
    )
    assessment.findings += rule_c_academic_year_change(
        student, changes, students, anomalies
    )
    assessment.findings += rule_d_quota_change(student, changes, students, programs, policy)
    assessment.findings += rule_e_intake_impact(student, changes, students, programs, policy)
    assessment.findings += rule_f_stale_credentials(student, changes, tokens, seals)
    return assessment
