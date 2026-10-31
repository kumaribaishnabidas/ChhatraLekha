"""Enumerations shared by the models, the services and the API schemas."""

from __future__ import annotations

from enum import Enum


class InstitutionCategory(str, Enum):
    """Broad institutional category."""

    SCHOOL = "SCHOOL"
    COLLEGE = "COLLEGE"

    @property
    def label(self) -> str:
        return {
            InstitutionCategory.SCHOOL: "School (K-12)",
            InstitutionCategory.COLLEGE: "Higher Education / College",
        }[self]


class EducationLevel(str, Enum):
    """Education levels spanning primary to higher education."""

    PRE_PRIMARY = "PRE_PRIMARY"
    PRIMARY = "PRIMARY"
    UPPER_PRIMARY = "UPPER_PRIMARY"
    SECONDARY = "SECONDARY"
    SENIOR_SECONDARY = "SENIOR_SECONDARY"
    DIPLOMA_VOCATIONAL = "DIPLOMA_VOCATIONAL"
    UNDERGRADUATE = "UNDERGRADUATE"
    POSTGRADUATE = "POSTGRADUATE"
    DOCTORAL = "DOCTORAL"

    @property
    def label(self) -> str:
        return {
            EducationLevel.PRE_PRIMARY: "Pre-Primary",
            EducationLevel.PRIMARY: "Primary (Grades 1-5)",
            EducationLevel.UPPER_PRIMARY: "Upper Primary / Middle (Grades 6-8)",
            EducationLevel.SECONDARY: "Secondary (Grades 9-10)",
            EducationLevel.SENIOR_SECONDARY: "Senior Secondary (Grades 11-12)",
            EducationLevel.DIPLOMA_VOCATIONAL: "Diploma / Vocational / ITI",
            EducationLevel.UNDERGRADUATE: "Undergraduate (UG)",
            EducationLevel.POSTGRADUATE: "Postgraduate (PG)",
            EducationLevel.DOCTORAL: "Doctoral / Research",
        }[self]


class InstitutionKind(str, Enum):
    """Specific kind of academic institution."""

    SCHOOL = "SCHOOL"
    JUNIOR_COLLEGE = "JUNIOR_COLLEGE"
    SENIOR_SECONDARY_SCHOOL = "SENIOR_SECONDARY_SCHOOL"
    COLLEGE = "COLLEGE"
    UNIVERSITY = "UNIVERSITY"
    POLYTECHNIC = "POLYTECHNIC"
    VOCATIONAL_ITI = "VOCATIONAL_ITI"
    ENGINEERING = "ENGINEERING"
    MANAGEMENT = "MANAGEMENT"

    @property
    def label(self) -> str:
        return {
            InstitutionKind.SCHOOL: "School (K-10)",
            InstitutionKind.JUNIOR_COLLEGE: "Junior College (11-12)",
            InstitutionKind.SENIOR_SECONDARY_SCHOOL: "Senior Secondary School (K-12)",
            InstitutionKind.COLLEGE: "Higher Education College",
            InstitutionKind.UNIVERSITY: "University / Deemed University",
            InstitutionKind.POLYTECHNIC: "Polytechnic Institute",
            InstitutionKind.VOCATIONAL_ITI: "Industrial Training Institute (ITI)",
            InstitutionKind.ENGINEERING: "Engineering Institution",
            InstitutionKind.MANAGEMENT: "Management Institution",
        }[self]


class ManagementType(str, Enum):
    """Ownership/management model of the institution."""

    GOVERNMENT = "GOVERNMENT"
    GOVERNMENT_AIDED = "GOVERNMENT_AIDED"
    PRIVATE_UNAIDED = "PRIVATE_UNAIDED"
    CENTRAL_GOVERNMENT = "CENTRAL_GOVERNMENT"
    OTHER = "OTHER"


class SchoolStream(str, Enum):
    """Senior secondary academic stream."""

    GENERAL = "GENERAL"
    SCIENCE = "SCIENCE"
    COMMERCE = "COMMERCE"
    ARTS_HUMANITIES = "ARTS_HUMANITIES"
    VOCATIONAL = "VOCATIONAL"


class CredentialType(str, Enum):
    """Type of academic credential issued or verified."""

    REPORT_CARD = "REPORT_CARD"
    TRANSFER_CERTIFICATE = "TRANSFER_CERTIFICATE"
    BONAFIDE_CERTIFICATE = "BONAFIDE_CERTIFICATE"
    MIGRATION_CERTIFICATE = "MIGRATION_CERTIFICATE"
    MARKSHEET = "MARKSHEET"
    PASSING_CERTIFICATE = "PASSING_CERTIFICATE"
    PROVISIONAL_CERTIFICATE = "PROVISIONAL_CERTIFICATE"
    DEGREE_CERTIFICATE = "DEGREE_CERTIFICATE"
    TRANSCRIPT = "TRANSCRIPT"


class TransitionEventType(str, Enum):
    """Academic lifecycle transitions."""

    ADMISSION = "ADMISSION"
    PROMOTION = "PROMOTION"
    TRANSFER = "TRANSFER"
    MIGRATION = "MIGRATION"
    DROPOUT = "DROPOUT"
    REENTRY = "REENTRY"
    GRADUATION = "GRADUATION"


class IdentifierScheme(str, Enum):
    """Standard institutional identifier registry schemes."""

    UDISE_PLUS = "UDISE_PLUS"
    AISHE = "AISHE"
    AICTE = "AICTE"
    BOARD_AFFILIATION = "BOARD_AFFILIATION"
    INTERNAL = "INTERNAL"


class RulePackType(str, Enum):
    """Regulatory validation rule pack bound to an institution."""

    TECHNICAL_HIGHER_ED = "technical_higher_ed"
    SCHOOL_BASIC = "school_basic"
    UNIVERSITY_GENERAL = "university_general"


class InstitutionType(str, Enum):
    ENGINEERING = "ENGINEERING"
    MANAGEMENT = "MANAGEMENT"
    POLYTECHNIC = "POLYTECHNIC"
    SCHOOL = "SCHOOL"
    COLLEGE = "COLLEGE"
    K12 = "K12"

    @property
    def label(self) -> str:
        return {
            InstitutionType.ENGINEERING: "Engineering & Technology",
            InstitutionType.MANAGEMENT: "Management / PGDM",
            InstitutionType.POLYTECHNIC: "Polytechnic / Diploma",
            InstitutionType.SCHOOL: "School Education",
            InstitutionType.COLLEGE: "Higher Education College",
            InstitutionType.K12: "K-12 School",
        }[self]


class InstitutionVerificationStatus(str, Enum):
    """Verification/review state of an onboarded institution."""

    PENDING_REVIEW = "PENDING_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class AttendanceMode(str, Enum):
    """Whether attendance is taken once daily or per class period/session."""

    DAILY = "DAILY"
    PERIOD_WISE = "PERIOD_WISE"


class AttendanceStatus(str, Enum):
    """Attendance state for a student in a session."""

    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"


class AssessmentStatus(str, Enum):
    """Lifecycle state of an examination or assessment."""

    DRAFT = "DRAFT"
    MODERATED = "MODERATED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class AnnouncementPriority(str, Enum):
    """Urgency level of a published notice."""

    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TargetAudienceScope(str, Enum):
    """Scope target for an announcement."""

    ALL = "ALL"
    CLASS = "CLASS"
    SECTION = "SECTION"
    PROGRAMME = "PROGRAMME"
    BATCH = "BATCH"
    ROLE = "ROLE"


class GuardianRelationshipType(str, Enum):
    """Relationship of an authorised guardian to a student."""

    FATHER = "FATHER"
    MOTHER = "MOTHER"
    LEGAL_GUARDIAN = "LEGAL_GUARDIAN"
    OTHER = "OTHER"


class GuardianVerificationStatus(str, Enum):
    """Institution approval status of a parent/guardian relationship."""

    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


class Gender(str, Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"

    @property
    def label(self) -> str:
        return {Gender.MALE: "Male", Gender.FEMALE: "Female", Gender.OTHER: "Other"}[self]

    @classmethod
    def from_code(cls, raw: str | None) -> "Gender | None":
        if not raw:
            return None
        key = raw.strip().upper()
        for member in cls:
            if member.value == key or member.name == key:
                return member
        return {
            "MALE": cls.MALE,
            "FEMALE": cls.FEMALE,
            "OTHER": cls.OTHER,
            "TRANSGENDER": cls.OTHER,
            "P": cls.OTHER,
        }.get(key)


class AdmissionQuota(str, Enum):
    """Admission quota bucket.

    Regular buckets consume the sanctioned AICTE intake; supernumerary
    buckets consume the separately capped PH seats. PMSSS is a reserved
    category that still consumes a sanctioned seat but is additionally capped
    per course.
    """

    MERIT = "REGULAR_MERIT"
    MANAGEMENT = "MANAGEMENT"
    NRI = "SUPERNUMERARY_NRI"
    OCI = "SUPERNUMERARY_OCI"
    FN = "SUPERNUMERARY_FN"
    TFW = "SUPERNUMERARY_TFW"
    PMSSS = "PMSSS"

    @property
    def label(self) -> str:
        return {
            AdmissionQuota.MERIT: "Merit (Regular Seat)",
            AdmissionQuota.MANAGEMENT: "Management Quota (Regular)",
            AdmissionQuota.NRI: "NRI Supernumerary",
            AdmissionQuota.OCI: "OCI Supernumerary",
            AdmissionQuota.FN: "Foreign National",
            AdmissionQuota.TFW: "Tuition Fee Waiver",
            AdmissionQuota.PMSSS: "PMSSS Scholarship",
        }[self]

    @property
    def short_label(self) -> str:
        return {
            AdmissionQuota.MERIT: "Merit",
            AdmissionQuota.MANAGEMENT: "Mgmt",
            AdmissionQuota.NRI: "NRI",
            AdmissionQuota.OCI: "OCI",
            AdmissionQuota.FN: "FN",
            AdmissionQuota.TFW: "TFW",
            AdmissionQuota.PMSSS: "PMSSS",
        }[self]

    @property
    def is_supernumerary(self) -> bool:
        return self in {
            AdmissionQuota.NRI,
            AdmissionQuota.OCI,
            AdmissionQuota.FN,
            AdmissionQuota.TFW,
        }

    @property
    def is_regular(self) -> bool:
        return not self.is_supernumerary

    @property
    def requires_foreign_docs(self) -> bool:
        return self in {AdmissionQuota.NRI, AdmissionQuota.OCI, AdmissionQuota.FN}

    @classmethod
    def from_code(cls, raw: str | None) -> "AdmissionQuota | None":
        if not raw:
            return None
        key = raw.strip().upper().replace("-", "_").replace(" ", "_")
        for member in cls:
            if member.value == key or member.name == key:
                return member
        return {
            "REGULAR": cls.MERIT,
            "GENERAL": cls.MERIT,
            "GEN": cls.MERIT,
            "UR": cls.MERIT,
            "OPEN": cls.MERIT,
            "MGMT": cls.MANAGEMENT,
            "MANAGEMENT_QUOTA": cls.MANAGEMENT,
            "NRI_SUPERNUMERARY": cls.NRI,
            "SUPERNUMERARY_NRI": cls.NRI,
            "OCI_SUPERNUMERARY": cls.OCI,
            "FOREIGN_NATIONAL": cls.FN,
            "FOREIGN": cls.FN,
            "TUITION_FEE_WAIVER": cls.TFW,
        }.get(key)


class SocialCategory(str, Enum):
    GENERAL = "GENERAL"
    EWS = "EWS"
    OBC = "OBC"
    SC = "SC"
    ST = "ST"
    OBC_OTHER = "OBC_OTHER"
    NOT_APPLICABLE = "NA"

    @property
    def label(self) -> str:
        return {
            SocialCategory.GENERAL: "General",
            SocialCategory.EWS: "EWS (Reserved)",
            SocialCategory.OBC: "OBC (Reserved)",
            SocialCategory.SC: "SC (Reserved)",
            SocialCategory.ST: "ST (Reserved)",
            SocialCategory.OBC_OTHER: "Other Backward Classes",
            SocialCategory.NOT_APPLICABLE: "Not Applicable",
        }[self]

    @property
    def is_reserved(self) -> bool:
        return self in {
            SocialCategory.EWS,
            SocialCategory.OBC,
            SocialCategory.SC,
            SocialCategory.ST,
            SocialCategory.OBC_OTHER,
        }

    @classmethod
    def from_code(cls, raw: str | None) -> "SocialCategory | None":
        if not raw:
            return None
        key = raw.strip().upper().replace("-", "_").replace(" ", "_")
        for member in cls:
            if member.value == key or member.name == key:
                return member
        return {
            "GEN": cls.GENERAL,
            "UR": cls.GENERAL,
            "OPEN": cls.GENERAL,
            "OBC_NCL": cls.OBC,
            "BACKWARD": cls.OBC,
        }.get(key)


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    FLAGGED_ANOMALY = "FLAGGED_ANOMALY"
    PENDING_REVIEW = "PENDING_REVIEW"

    @property
    def label(self) -> str:
        return {
            VerificationStatus.VERIFIED: "Verified",
            VerificationStatus.FLAGGED_ANOMALY: "Flagged Anomaly",
            VerificationStatus.PENDING_REVIEW: "Pending Review",
        }[self]

    @classmethod
    def from_code(cls, raw: str | None) -> "VerificationStatus":
        """Parse a stored status, defaulting to pending review."""
        if not raw:
            return cls.PENDING_REVIEW
        for member in cls:
            if member.value == str(raw).strip().upper() or member.name == str(raw).strip().upper():
                return member
        return cls.PENDING_REVIEW


class AnomalyType(str, Enum):
    EXCESS_APPROVED_INTAKE = "EXCESS_APPROVED_INTAKE"
    DUPLICATE_CROSS_COLLEGE = "DUPLICATE_CROSS_COLLEGE"
    DUPLICATE_SAME_INSTITUTION = "DUPLICATE_SAME_INSTITUTION"
    DUPLICATE_ROLL_NUMBER = "DUPLICATE_ROLL_NUMBER"
    INVALID_APAAR_FORMAT = "INVALID_APAAR_FORMAT"
    SUPERNUMERARY_BREACH = "SUPERNUMERARY_BREACH"
    INCONSISTENT_CATEGORY = "INCONSISTENT_CATEGORY"
    IMPOSSIBLE_DATE = "IMPOSSIBLE_DATE"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    UNSANCTIONED_PROGRAM = "UNSANCTIONED_PROGRAM"

    # School & General Education Rule Pack types:
    MINOR_GUARDIAN_REQUIRED = "MINOR_GUARDIAN_REQUIRED"
    INVALID_AGE_FOR_GRADE = "INVALID_AGE_FOR_GRADE"
    DUPLICATE_SCHOOL_ENROLMENT = "DUPLICATE_SCHOOL_ENROLMENT"
    SECTION_CAPACITY_EXCEEDED = "SECTION_CAPACITY_EXCEEDED"
    PROMOTION_WITHOUT_RESULT = "PROMOTION_WITHOUT_RESULT"
    MISSING_UDISE_CODE = "MISSING_UDISE_CODE"

    @property
    def label(self) -> str:
        return {
            AnomalyType.EXCESS_APPROVED_INTAKE: "Excess Approved Intake",
            AnomalyType.DUPLICATE_CROSS_COLLEGE: "Duplicate Cross-Institution",
            AnomalyType.DUPLICATE_SAME_INSTITUTION: "Duplicate Within Institution",
            AnomalyType.DUPLICATE_ROLL_NUMBER: "Duplicate Roll Number",
            AnomalyType.INVALID_APAAR_FORMAT: "Invalid APAAR Format",
            AnomalyType.SUPERNUMERARY_BREACH: "Supernumerary Breach",
            AnomalyType.INCONSISTENT_CATEGORY: "Inconsistent Category Data",
            AnomalyType.IMPOSSIBLE_DATE: "Impossible Date",
            AnomalyType.MISSING_REQUIRED_FIELD: "Missing Mandatory Field",
            AnomalyType.UNSANCTIONED_PROGRAM: "Unsanctioned Programme",
            AnomalyType.MINOR_GUARDIAN_REQUIRED: "Guardian Information Missing for Minor",
            AnomalyType.INVALID_AGE_FOR_GRADE: "Incompatible Age for Grade / Class",
            AnomalyType.DUPLICATE_SCHOOL_ENROLMENT: "Concurrent Multi-School Enrolment",
            AnomalyType.SECTION_CAPACITY_EXCEEDED: "Class Section Capacity Exceeded",
            AnomalyType.PROMOTION_WITHOUT_RESULT: "Grade Promotion Without Result",
            AnomalyType.MISSING_UDISE_CODE: "Missing UDISE+ School Code",
        }[self]

    @property
    def short_label(self) -> str:
        return {
            AnomalyType.EXCESS_APPROVED_INTAKE: "Over-admission",
            AnomalyType.DUPLICATE_CROSS_COLLEGE: "Cross-enrolment",
            AnomalyType.DUPLICATE_SAME_INSTITUTION: "Duplicate record",
            AnomalyType.DUPLICATE_ROLL_NUMBER: "Duplicate roll no.",
            AnomalyType.INVALID_APAAR_FORMAT: "Invalid APAAR",
            AnomalyType.SUPERNUMERARY_BREACH: "Supernumerary cap",
            AnomalyType.INCONSISTENT_CATEGORY: "Data inconsistency",
            AnomalyType.IMPOSSIBLE_DATE: "Date conflict",
            AnomalyType.MISSING_REQUIRED_FIELD: "Incomplete record",
            AnomalyType.UNSANCTIONED_PROGRAM: "Unregistered course",
            AnomalyType.MINOR_GUARDIAN_REQUIRED: "Minor guardian missing",
            AnomalyType.INVALID_AGE_FOR_GRADE: "Age-grade mismatch",
            AnomalyType.DUPLICATE_SCHOOL_ENROLMENT: "School cross-enrolment",
            AnomalyType.SECTION_CAPACITY_EXCEEDED: "Section capacity breach",
            AnomalyType.PROMOTION_WITHOUT_RESULT: "Unverified promotion",
            AnomalyType.MISSING_UDISE_CODE: "UDISE+ missing",
        }[self]


class AnomalySeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    WARNING = "WARNING"
    INFO = "INFO"

    @property
    def label(self) -> str:
        return {
            AnomalySeverity.CRITICAL: "Critical",
            AnomalySeverity.HIGH: "High",
            AnomalySeverity.WARNING: "Warning",
            AnomalySeverity.INFO: "Info",
        }[self]

    @property
    def rank(self) -> int:
        return {
            AnomalySeverity.CRITICAL: 0,
            AnomalySeverity.HIGH: 1,
            AnomalySeverity.WARNING: 2,
            AnomalySeverity.INFO: 3,
        }[self]


class ConsentPurpose(str, Enum):
    CREDENTIAL_VERIFICATION = "CREDENTIAL_VERIFICATION"
    DATA_SHARING_WITH_EMPLOYER = "DATA_SHARING_WITH_EMPLOYER"
    ANALYTICS_AND_REPORTING = "ANALYTICS_AND_REPORTING"
    RESEARCH = "RESEARCH"
    MARKETING = "MARKETING"

    @property
    def label(self) -> str:
        return {
            ConsentPurpose.CREDENTIAL_VERIFICATION: "Credential verification",
            ConsentPurpose.DATA_SHARING_WITH_EMPLOYER: "Employer data sharing",
            ConsentPurpose.ANALYTICS_AND_REPORTING: "Analytics and reporting",
            ConsentPurpose.RESEARCH: "Research",
            ConsentPurpose.MARKETING: "Marketing and outreach",
        }[self]

    @property
    def requires_explicit_consent(self) -> bool:
        return self is not ConsentPurpose.ANALYTICS_AND_REPORTING


class ConsentStatus(str, Enum):
    GRANTED = "GRANTED"
    REVOKED = "REVOKED"
    PENDING = "PENDING"

    @property
    def label(self) -> str:
        return {
            ConsentStatus.GRANTED: "Granted",
            ConsentStatus.REVOKED: "Revoked",
            ConsentStatus.PENDING: "Pending",
        }[self]


class ConsentChannel(str, Enum):
    MOBILE_APP = "MOBILE_APP"
    WEB_PORTAL = "WEB_PORTAL"
    PAPER_FORM = "PAPER_FORM"
    VERIFIER_KIOSK = "VERIFIER_KIOSK"
    ADMIN_OVERRIDE = "ADMIN_OVERRIDE"

    @property
    def label(self) -> str:
        return {
            ConsentChannel.MOBILE_APP: "Mobile app",
            ConsentChannel.WEB_PORTAL: "Web portal",
            ConsentChannel.PAPER_FORM: "Signed paper form",
            ConsentChannel.VERIFIER_KIOSK: "Verifier kiosk",
            ConsentChannel.ADMIN_OVERRIDE: "Administrative override",
        }[self]


class QuotaBasis(str, Enum):
    NRI = "NRI"
    OCI_FN = "OCI_FN"
    TFW = "TFW"
    PMSSS = "PMSSS"

    @property
    def citation(self) -> str:
        return {
            QuotaBasis.NRI: "AICTE APH - max 5% of sanctioned intake",
            QuotaBasis.OCI_FN: "AICTE APH - max 15% of sanctioned intake",
            QuotaBasis.TFW: "AICTE APH - max 5% of sanctioned intake",
            QuotaBasis.PMSSS: "AICTE APH - capped per course / institute",
        }[self]


class StudentLifecycleState(str, Enum):
    ADMITTED = "ADMITTED"
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    TRANSFERRED = "TRANSFERRED"
    GRADUATED = "GRADUATED"
    WITHDRAWN = "WITHDRAWN"

    @property
    def label(self) -> str:
        return {
            StudentLifecycleState.ADMITTED: "Admitted",
            StudentLifecycleState.ACTIVE: "Active Enrolment",
            StudentLifecycleState.ON_LEAVE: "On Leave / Sabbatical",
            StudentLifecycleState.TRANSFERRED: "Transferred Out",
            StudentLifecycleState.GRADUATED: "Graduated / Completed",
            StudentLifecycleState.WITHDRAWN: "Withdrawn / Cancelled",
        }[self]


class TransferStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

    @property
    def label(self) -> str:
        return {
            TransferStatus.SUBMITTED: "Submitted",
            TransferStatus.IN_REVIEW: "In Review",
            TransferStatus.APPROVED: "Approved & Transferred",
            TransferStatus.REJECTED: "Rejected",
            TransferStatus.CANCELLED: "Cancelled",
        }[self]
