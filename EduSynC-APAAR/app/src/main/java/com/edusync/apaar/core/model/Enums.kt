package com.edusync.apaar.core.model

/**
 * The four personas that drive the multi-role APAAR portal.
 */
enum class UserRole(
    val label: String,
    val shortLabel: String,
    val tagline: String,
    val iconKey: String
) {
    AICTE_DIRECTORATE(
        label = "AICTE Central Directorate",
        shortLabel = "Directorate",
        tagline = "National intake monitoring, quota compliance & anomaly audit",
        iconKey = "directorate"
    ),
    INSTITUTION(
        label = "AICTE-Approved Institution",
        shortLabel = "Institution",
        tagline = "Department-wise intake quota, batch CSV onboarding & student register",
        iconKey = "institution"
    ),
    VERIFIER(
        label = "Third-Party Verifier / Employer",
        shortLabel = "Verifier",
        tagline = "Instant APAAR credential & bonafide verification",
        iconKey = "verifier"
    ),
    STUDENT(
        label = "Student / Degree-Awarding Body",
        shortLabel = "Student",
        tagline = "Digital APAAR academic identity card, QR seal & ABC linkage",
        iconKey = "student"
    )
}

/**
 * Nature of the institution as classified by AICTE for approval.
 */
enum class InstitutionType(val label: String, val shortLabel: String) {
    ENGINEERING("Engineering & Technology", "Engineering"),
    MANAGEMENT("Management / PGDM", "Management"),
    POLYTECHNIC("Polytechnic / Diploma", "Polytechnic");

    companion object {
        fun from(raw: String?): InstitutionType = entries.firstOrNull {
            it.name.equals(raw, ignoreCase = true)
        } ?: ENGINEERING
    }
}

/**
 * Admission quota bucket. Regular buckets consume the sanctioned AICTE intake,
 * supernumerary buckets consume the separately capped PH seats.
 */
enum class AdmissionQuota(
    val code: String,
    val label: String,
    val shortLabel: String,
    val isSupernumerary: Boolean,
    val isRegular: Boolean,
    val requiresForeignDocs: Boolean
) {
    MERIT("REGULAR_MERIT", "Merit (Regular Seat)", "Merit", false, true, false),
    MANAGEMENT("MANAGEMENT", "Management Quota (Regular)", "Mgmt", false, true, false),
    NRI("SUPERNUMERARY_NRI", "NRI Supernumerary", "NRI", true, false, true),
    OCI("SUPERNUMERARY_OCI", "OCI Supernumerary", "OCI", true, false, true),
    FN("SUPERNUMERARY_FN", "Foreign National", "FN", true, false, true),
    TFW("SUPERNUMERARY_TFW", "Tuition Fee Waiver", "TFW", true, false, false),
    // PMSSS is a reserved category that still consumes a sanctioned seat, but is
    // additionally capped per course by the AICTE Approval Process Handbook.
    PMSSS("PMSSS", "PMSSS Scholarship", "PMSSS", false, true, false);

    companion object {
        fun fromCode(raw: String?): AdmissionQuota? {
            if (raw.isNullOrBlank()) return null
            val key = raw.trim().uppercase().replace('-', '_').replace(' ', '_')
            entries.firstOrNull { it.code == key }?.let { return it }
            entries.firstOrNull { it.name == key }?.let { return it }
            return when (key) {
                "REGULAR", "GENERAL", "GEN", "UR", "OPEN" -> MERIT
                "MGMT", "MANAGEMENT_QUOTA" -> MANAGEMENT
                "NRI_SUPERNUMERARY", "SUPERNUMERARY_NRI" -> NRI
                "OCI_SUPERNUMERARY" -> OCI
                "FN", "FOREIGN_NATIONAL", "FOREIGN" -> FN
                "TFW", "TUITION_FEE_WAIVER" -> TFW
                else -> null
            }
        }
    }
}

enum class Gender(val code: String, val label: String) {
    MALE("M", "Male"),
    FEMALE("F", "Female"),
    OTHER("O", "Other");

    companion object {
        fun fromCode(raw: String?): Gender? {
            if (raw.isNullOrBlank()) return null
            val key = raw.trim().uppercase()
            entries.firstOrNull { it.code == key || it.name == key }?.let { return it }
            return when (key) {
                "MALE" -> MALE
                "FEMALE" -> FEMALE
                "OTHER", "TRANSGENDER", "P" -> OTHER
                else -> null
            }
        }
    }
}

enum class VerificationStatus(val label: String) {
    VERIFIED("Verified"),
    FLAGGED_ANOMALY("Flagged Anomaly"),
    PENDING_REVIEW("Pending Review");

    companion object {
        fun from(raw: String?): VerificationStatus = entries.firstOrNull {
            it.name.equals(raw, ignoreCase = true)
        } ?: PENDING_REVIEW
    }
}

/**
 * The five anomaly families executed by the multi-layer detection engine.
 */
enum class AnomalyType(val label: String, val shortLabel: String, val description: String) {
    EXCESS_APPROVED_INTAKE(
        "Excess Approved Intake",
        "Over-admission",
        "Total regular enrolment exceeds the AICTE sanctioned intake for the programme."
    ),
    DUPLICATE_CROSS_COLLEGE(
        "Duplicate Cross-Institution",
        "Cross-enrolment",
        "The same APAAR ID is concurrently active in more than one AICTE-approved institution."
    ),
    INVALID_APAAR_FORMAT(
        "Invalid APAAR Format",
        "Invalid APAAR",
        "The APAAR ID fails the 12-digit structural / non-triviality checks."
    ),
    SUPERNUMERARY_BREACH(
        "Supernumerary Breach",
        "Supernumerary cap",
        "A supernumerary bucket exceeds the AICTE Approval Process Handbook ceiling."
    ),
    INCONSISTENT_CATEGORY(
        "Inconsistent Category Data",
        "Data inconsistency",
        "Category, nationality or foreign-national documentation is incomplete or contradictory."
    ),
    UNSANCTIONED_PROGRAM(
        "Unsanctioned Programme",
        "Unregistered course",
        "The student is enrolled in a programme code that the institution is not approved to offer."
    );

    companion object {
        fun from(raw: String?): AnomalyType? =
            entries.firstOrNull { it.name.equals(raw, ignoreCase = true) }
    }
}

enum class AnomalySeverity(val label: String, val rank: Int) {
    CRITICAL("Critical", 0),
    HIGH("High", 1),
    WARNING("Warning", 2),
    INFO("Info", 3);

    companion object {
        fun from(raw: String?): AnomalySeverity = entries.firstOrNull {
            it.name.equals(raw, ignoreCase = true)
        } ?: WARNING
    }
}

/**
 * Regulatory basis quoted alongside a supernumerary ceiling.
 */
enum class QuotaBasis(val label: String, val citation: String) {
    NRI("NRI seats", "AICTE APH — max 5% of sanctioned intake"),
    OCI_FN("OCI / Foreign National seats", "AICTE APH — max 15% of sanctioned intake"),
    TFW("Tuition Fee Waiver seats", "AICTE APH — max 5% of sanctioned intake"),
    PMSSS("PMSSS seats", "AICTE APH — capped per course / institute")
}
