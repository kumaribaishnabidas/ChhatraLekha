package com.chhatralekha.core.model

/**
 * Read-model of an AICTE-approved institution.
 */
data class Institution(
    val institutionId: String,
    val name: String,
    val institutionType: InstitutionType,
    val state: String,
    val city: String,
    val affiliationUniversity: String,
    val approvalYear: Int,
    val naacGrade: String
) {
    val displayId: String get() = institutionId
    val location: String get() = "$city, $state"
}

/**
 * A programme offered by an institution together with its AICTE sanctioned capacity.
 */
data class ProgramIntake(
    val programId: String,
    val institutionId: String,
    val programName: String,
    val programLevel: String,
    val approvedIntake: Int,
    val maxSupernumeraryNri: Int,
    val maxSupernumeraryFnOci: Int,
    val maxSupernumeraryTfw: Int,
    val maxPmsss: Int
) {
    val totalSanctioned: Int get() = approvedIntake + maxSupernumeraryNri + maxSupernumeraryFnOci + maxSupernumeraryTfw + maxPmsss
}

/**
 * A student enrolment record held against an institution and programme.
 */
data class Student(
    val recordId: Long,
    val apaarId: String,
    val studentName: String,
    val dateOfBirth: String,
    val gender: Gender,
    val institutionId: String,
    val programId: String,
    val academicYear: String,
    val admissionQuota: AdmissionQuota,
    val enrollmentDate: String,
    val studentInstituteRollNo: String,
    val nationality: String,
    val passportNumber: String?,
    val visaValidity: String?,
    val countryOfOrigin: String?,
    val abcAccountId: String?,
    val verificationStatus: VerificationStatus,
    val isActive: Boolean = true,
    val photoSeed: Int = 0,
    // ---------------------------------------------------- extended record set
    /** Social category (General / OBC / SC / ST / EWS) declared at admission. */
    val socialCategory: SocialCategory = SocialCategory.GENERAL,
    /** Date the admission was formally granted, ISO-8601 (`yyyy-MM-dd`). */
    val admissionDate: String? = null,
    /** Contact e-mail captured for verification notices. */
    val contactEmail: String? = null,
    /** Contact mobile number captured for verification notices. */
    val contactPhone: String? = null,
    /** State of domicile at the time of admission. */
    val stateOfDomicile: String? = null
) {
    val initials: String
        get() = studentName.trim().split(" ")
            .filter { it.isNotBlank() }
            .take(2)
            .joinToString("") { it.first().uppercase() }
            .ifEmpty { "--" }

    /** True when the record carries enough contact data to reach the student. */
    val hasContactDetails: Boolean
        get() = !contactEmail.isNullOrBlank() || !contactPhone.isNullOrBlank()
}

/**
 * A single detected regulatory anomaly.
 */
data class Anomaly(
    val anomalyId: Long,
    val studentApaarId: String,
    val institutionId: String,
    val programId: String?,
    val anomalyType: AnomalyType,
    val severity: AnomalySeverity,
    val details: String,
    val timestamp: Long,
    val resolved: Boolean = false
)

/**
 * Immutable audit trail entry.
 *
 * [prevHash] and [hash] make the trail tamper-evident: every entry commits to
 * its predecessor, so removing or editing a row invalidates every hash after it.
 */
data class AuditEntry(
    val logId: Long,
    val timestamp: Long,
    val actor: String,
    val action: String,
    val subject: String,
    val details: String,
    val category: String,
    val prevHash: String = "",
    val hash: String = ""
)

/**
 * One consent record in the consent ledger.
 *
 * Consent is modelled per purpose rather than as a single flag because the
 * Digital Personal Data Protection Act requires purpose-wise, revocable and
 * evidenced consent.
 */
data class ConsentRecord(
    val consentId: String,
    val studentApaarId: String,
    val purpose: ConsentPurpose,
    val status: ConsentStatus,
    val channel: ConsentChannel,
    val policyVersion: String,
    val recordedAt: Long,
    val revokedAt: Long? = null,
    val evidence: String? = null
) {
    val isActive: Boolean get() = status == ConsentStatus.GRANTED
}

/**
 * A signed-in account on the portal.
 *
 * The app authenticates locally: the PIN is never stored, only a PBKDF2 hash
 * of it together with a per-account salt.
 */
data class UserAccount(
    val accountId: String,
    val displayName: String,
    val role: UserRole,
    val institutionId: String? = null,
    val email: String? = null,
    val pinSalt: String,
    val pinHash: String,
    val isActive: Boolean = true
)

/**
 * Real-time utilisation of one programme's sanctioned capacity.
 */
data class IntakeSnapshot(
    val program: ProgramIntake,
    val regularEnrolled: Int,
    val supernumeraryEnrolled: Int,
    val totalEnrolled: Int,
    val nriEnrolled: Int,
    val ociFnEnrolled: Int,
    val tfwEnrolled: Int,
    val pmsssEnrolled: Int
) {
    val regularUtilisation: Float
        get() = if (program.approvedIntake == 0) 0f else regularEnrolled.toFloat() / program.approvedIntake
    val overallUtilisation: Float
        get() = if (program.totalSanctioned == 0) 0f else totalEnrolled.toFloat() / program.totalSanctioned

    val regularOverflow: Int get() = (regularEnrolled - program.approvedIntake).coerceAtLeast(0)
    val nriOverflow: Int get() = (nriEnrolled - program.maxSupernumeraryNri).coerceAtLeast(0)
    val ociFnOverflow: Int get() = (ociFnEnrolled - program.maxSupernumeraryFnOci).coerceAtLeast(0)
    val tfwOverflow: Int get() = (tfwEnrolled - program.maxSupernumeraryTfw).coerceAtLeast(0)
    val pmsssOverflow: Int get() = (pmsssEnrolled - program.maxPmsss).coerceAtLeast(0)

    val hasBreach: Boolean
        get() = regularOverflow > 0 || nriOverflow > 0 || ociFnOverflow > 0 || tfwOverflow > 0 || pmsssOverflow > 0
}

/**
 * Pan-India headline numbers for the AICTE Directorate dashboard.
 */
data class NationalKpis(
    val institutionCount: Int,
    val programmeCount: Int,
    val totalApprovedIntake: Int,
    val totalEnrolled: Int,
    val flaggedAnomalies: Int,
    val criticalAnomalies: Int,
    val supernumeraryEnrolled: Int,
    val utilisationPercent: Float
) {
    companion object {
        val Empty = NationalKpis(0, 0, 0, 0, 0, 0, 0, 0f)
    }
}

/**
 * Aggregate quota distribution across the whole country (used for the charts).
 */
data class QuotaDistribution(
    val label: String,
    val enrolled: Int,
    val sanctioned: Int,
    val quota: AdmissionQuota?
) {
    val utilisation: Float
        get() = if (sanctioned <= 0) 0f else (enrolled.toFloat() / sanctioned).coerceAtMost(1.35f)
}
