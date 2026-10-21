"""SQLAlchemy models for the EduSynC registry."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import (
    AdmissionQuota,
    AnomalySeverity,
    AnomalyType,
    ConsentChannel,
    ConsentPurpose,
    ConsentStatus,
    Gender,
    InstitutionType,
    SocialCategory,
    VerificationStatus,
)


def enum_values(enum_cls) -> list[str]:
    """Store the enum *value* (the code) rather than the member name."""
    return [member.value for member in enum_cls]


def sa_enum(enum_cls, length: int = 40) -> SAEnum:
    """A portable enum column (VARCHAR + CHECK constraint, no native type)."""
    return SAEnum(
        enum_cls,
        values_callable=enum_values,
        native_enum=False,
        length=length,
        validate_strings=True,
    )


class TimestampMixin:
    """``created_at`` / ``updated_at`` columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


# ------------------------------------------------------------- institutions

class Institution(Base, TimestampMixin):
    """An AICTE-approved institution."""

    __tablename__ = "institutions"

    institution_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_type: Mapped[InstitutionType] = mapped_column(
        sa_enum(InstitutionType), default=InstitutionType.ENGINEERING, nullable=False
    )
    state: Mapped[str] = mapped_column(String(80), default="")
    city: Mapped[str] = mapped_column(String(80), default="")
    affiliation_university: Mapped[str] = mapped_column(String(255), default="")
    approval_year: Mapped[int] = mapped_column(Integer, default=0)
    naac_grade: Mapped[str] = mapped_column(String(16), default="")
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    programs: Mapped[list["ProgramIntake"]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    students: Mapped[list["Student"]] = relationship(back_populates="institution")

    @property
    def location(self) -> str:
        return f"{self.city}, {self.state}"


class ProgramIntake(Base, TimestampMixin):
    """Sanctioned capacity for one programme of one institution."""

    __tablename__ = "program_intakes"
    __table_args__ = (
        UniqueConstraint("institution_id", "program_id", name="uq_program_intake"),
        Index("ix_program_intakes_institution", "institution_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_id: Mapped[str] = mapped_column(String(64), nullable=False)
    institution_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("institutions.institution_id", ondelete="CASCADE"), nullable=False
    )
    program_name: Mapped[str] = mapped_column(String(255), nullable=False)
    program_level: Mapped[str] = mapped_column(String(16), default="UG")
    approved_intake: Mapped[int] = mapped_column(Integer, default=0)
    max_supernumerary_nri: Mapped[int] = mapped_column(Integer, default=0)
    max_supernumerary_fn_oci: Mapped[int] = mapped_column(Integer, default=0)
    max_supernumerary_tfw: Mapped[int] = mapped_column(Integer, default=0)
    max_pmsss: Mapped[int] = mapped_column(Integer, default=0)

    institution: Mapped[Institution] = relationship(back_populates="programs")
    students: Mapped[list["Student"]] = relationship(
        back_populates="program",
        # ``program_id`` alone is not unique across institutions, so the join is
        # stated explicitly over the (institution, programme) pair and the
        # referencing side is annotated with ``foreign()``.
        primaryjoin=(
            "and_(foreign(ProgramIntake.institution_id) == Student.institution_id, "
            "foreign(ProgramIntake.program_id) == Student.program_id)"
        ),
        viewonly=True,
    )

    @property
    def total_sanctioned(self) -> int:
        return (
            self.approved_intake
            + self.max_supernumerary_nri
            + self.max_supernumerary_fn_oci
            + self.max_supernumerary_tfw
            + self.max_pmsss
        )


# ----------------------------------------------------------------- students

class Student(Base, TimestampMixin):
    """A student enrolment record.

    ``apaar_id`` is **indexed but not unique**: the national registry must be
    able to physically store the same APAAR ID claimed by two institutions so
    that the cross-institutional duplicate check can fire. A unique constraint
    would hide the very anomaly we are required to detect.
    """

    __tablename__ = "students"
    __table_args__ = (
        Index("ix_students_apaar_id", "apaar_id"),
        Index("ix_students_institution", "institution_id"),
        Index("ix_students_program", "program_id"),
        Index("ix_students_institution_program", "institution_id", "program_id"),
    )

    record_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    apaar_id: Mapped[str] = mapped_column(String(32), nullable=False)
    student_name: Mapped[str] = mapped_column(String(255), default="")
    date_of_birth: Mapped[str] = mapped_column(String(32), default="")
    gender: Mapped[Gender] = mapped_column(sa_enum(Gender, 4), default=Gender.OTHER)
    institution_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("institutions.institution_id", ondelete="CASCADE"), nullable=False
    )
    program_id: Mapped[str] = mapped_column(String(64), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(16), default="")
    admission_quota: Mapped[AdmissionQuota] = mapped_column(
        sa_enum(AdmissionQuota), default=AdmissionQuota.MERIT
    )
    enrollment_date: Mapped[str] = mapped_column(String(32), default="")
    student_institute_roll_no: Mapped[str] = mapped_column(String(64), default="")
    nationality: Mapped[str] = mapped_column(String(80), default="Indian")
    passport_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    visa_validity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country_of_origin: Mapped[str | None] = mapped_column(String(80), nullable=True)
    abc_account_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        sa_enum(VerificationStatus, 32), default=VerificationStatus.PENDING_REVIEW
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    photo_seed: Mapped[int] = mapped_column(Integer, default=0)

    # -------------------------------------------------- extended record set
    social_category: Mapped[SocialCategory] = mapped_column(
        sa_enum(SocialCategory), default=SocialCategory.GENERAL
    )
    admission_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    state_of_domicile: Mapped[str | None] = mapped_column(String(80), nullable=True)

    institution: Mapped[Institution] = relationship(back_populates="students")
    program: Mapped[ProgramIntake] = relationship(
        back_populates="students",
        primaryjoin=(
            "and_(foreign(ProgramIntake.institution_id) == Student.institution_id, "
            "foreign(ProgramIntake.program_id) == Student.program_id)"
        ),
        viewonly=True,
    )
    consents: Mapped[list["Consent"]] = relationship(
        back_populates="student",
        primaryjoin="foreign(Consent.student_apaar_id) == Student.apaar_id",
        viewonly=True,
    )

    @property
    def initials(self) -> str:
        parts = [part for part in (self.student_name or "").split() if part]
        if not parts:
            return "--"
        return "".join(part[0].upper() for part in parts[:2])

    @property
    def has_contact_details(self) -> bool:
        return bool(self.contact_email or self.contact_phone)

    @property
    def display_date_of_birth(self) -> date | None:
        return _parse_iso_date(self.date_of_birth)


def _parse_iso_date(raw: str | None) -> date | None:
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------- anomalies

class Anomaly(Base):
    """A detected regulatory anomaly."""

    __tablename__ = "anomaly_records"
    __table_args__ = (
        Index("ix_anomalies_student", "student_apaar_id"),
        Index("ix_anomalies_institution", "institution_id"),
        Index("ix_anomalies_type", "anomaly_type"),
    )

    anomaly_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_apaar_id: Mapped[str] = mapped_column(String(32), nullable=False)
    institution_id: Mapped[str] = mapped_column(String(32), default="")
    program_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    anomaly_type: Mapped[AnomalyType] = mapped_column(sa_enum(AnomalyType), nullable=False)
    severity: Mapped[AnomalySeverity] = mapped_column(sa_enum(AnomalySeverity), nullable=False)
    details: Mapped[str] = mapped_column(Text, default="")
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


# ----------------------------------------------------------------- consent

class Consent(Base, TimestampMixin):
    """One purpose-wise consent record in the consent ledger."""

    __tablename__ = "consents"
    __table_args__ = (
        Index("ix_consents_student", "student_apaar_id"),
        Index("ix_consents_purpose", "purpose"),
    )

    consent_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    student_apaar_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    purpose: Mapped[ConsentPurpose] = mapped_column(sa_enum(ConsentPurpose), nullable=False)
    status: Mapped[ConsentStatus] = mapped_column(
        sa_enum(ConsentStatus), default=ConsentStatus.PENDING
    )
    channel: Mapped[ConsentChannel] = mapped_column(
        sa_enum(ConsentChannel), default=ConsentChannel.WEB_PORTAL
    )
    policy_version: Mapped[str] = mapped_column(String(32), default="2024-01")
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    granted_by: Mapped[str] = mapped_column(String(120), default="")
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    student: Mapped[Student] = relationship(
        back_populates="consents",
        primaryjoin="foreign(Consent.student_apaar_id) == Student.apaar_id",
        viewonly=True,
    )

    @property
    def is_active(self) -> bool:
        return self.status == ConsentStatus.GRANTED


# ------------------------------------------------------------------- audit

class AuditLog(Base):
    """Immutable regulatory audit trail.

    ``prev_hash`` and ``hash`` make the trail tamper-evident: every entry
    commits to its predecessor, so removing or editing a row invalidates every
    hash after it.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_timestamp", "timestamp"),)

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actor: Mapped[str] = mapped_column(String(120), default="system")
    actor_role: Mapped[str] = mapped_column(String(40), default="")
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    subject: Mapped[str] = mapped_column(String(120), default="")
    details: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(40), default="SYSTEM")
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prev_hash: Mapped[str] = mapped_column(String(64), default="")
    hash: Mapped[str] = mapped_column(String(64), default="")


# -------------------------------------------------------------------- users

class User(Base, TimestampMixin):
    """A signed-in principal."""

    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    institution_id: Mapped[str | None] = mapped_column(
        String(32),
        ForeignKey("institutions.institution_id", ondelete="SET NULL"),
        nullable=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255), default="")
    pin_salt: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pin_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    institution: Mapped[Institution | None] = relationship()


class ApiKey(Base, TimestampMixin):
    """A machine-to-machine credential for an institutional integration."""

    __tablename__ = "api_keys"

    key_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(120), default="")
    institution_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    role: Mapped[str] = mapped_column(String(40), default="institution_admin")
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    scopes: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RevokedCredential(Base):
    """Credential revocation list (requirement 6)."""

    __tablename__ = "revoked_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    apaar_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, default="")
    revoked_by: Mapped[str] = mapped_column(String(120), default="")
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class InstitutionRiskScore(Base):
    """A computed risk score per institution (innovation layer)."""

    __tablename__ = "institution_risk_scores"
    __table_args__ = (Index("ix_risk_institution", "institution_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    institution_id: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    band: Mapped[str] = mapped_column(String(16), default="LOW")
    critical_count: Mapped[int] = mapped_column(Integer, default=0)
    high_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


def utcnow() -> datetime:
    """Timezone-aware current time."""
    return datetime.now(timezone.utc)
