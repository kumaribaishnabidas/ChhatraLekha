package com.acadentrix.app.core.validation

import com.acadentrix.app.core.model.AdmissionQuota
import com.acadentrix.app.core.model.AnomalySeverity
import com.acadentrix.app.core.model.AnomalyType
import com.acadentrix.app.core.model.Institution
import com.acadentrix.app.core.model.IntakeSnapshot
import com.acadentrix.app.core.model.ProgramIntake
import com.acadentrix.app.core.model.Student

/**
 * A point-in-time view of the whole national registry, used by the detection engine.
 */
data class RegistrySnapshot(
    val institutions: List<Institution> = emptyList(),
    val programs: List<ProgramIntake> = emptyList(),
    val students: List<Student> = emptyList()
)

/**
 * An anomaly detected by the engine, before it is persisted with a row id.
 */
data class DetectedAnomaly(
    val studentApaarId: String,
    val institutionId: String,
    val programId: String?,
    val anomalyType: AnomalyType,
    val severity: AnomalySeverity,
    val details: String
)

/**
 * Multi-layer anomaly detection engine.
 *
 * Four discrete regulatory checks are executed over the registry snapshot:
 *  1. APAAR syntactic check — 12-digit structure and non-triviality.
 *  2. Intake breach check — regular enrolment against sanctioned capacity.
 *  3. Supernumerary ceiling check — NRI / OCI+FN / TFW / PMSSS caps.
 *  4. Cross-institutional multi-enrolment — one APAAR, many institutions.
 *
 * A fifth, softer check covers documentary consistency for foreign nationals
 * and quota/nationality contradictions.
 */
object AnomalyEngine {

    /** Severity is escalated to CRITICAL once a cap is exceeded by more than two seats. */
    private const val ESCALATION_THRESHOLD = 2

    fun evaluate(snapshot: RegistrySnapshot): List<DetectedAnomaly> {
        val anomalies = mutableListOf<DetectedAnomaly>()
        anomalies += detectInvalidApaarFormat(snapshot)
        anomalies += detectCrossInstitutionDuplicates(snapshot)
        anomalies += detectIntakeBreaches(snapshot)
        anomalies += detectSupernumeraryBreaches(snapshot)
        anomalies += detectInconsistencies(snapshot)
        anomalies += detectUnsanctionedProgrammes(snapshot)
        return anomalies
    }

    /**
     * A student may only be mapped to a programme code that the institution
     * actually holds approval for. Enrolment in an unregistered course code is a
     * data-integrity violation in its own right.
     */
    private fun detectUnsanctionedProgrammes(snapshot: RegistrySnapshot): List<DetectedAnomaly> {
        val sanctioned = snapshot.programs
            .map { it.institutionId to it.programId }
            .toSet()
        return snapshot.students.mapNotNull { student ->
            if ((student.institutionId to student.programId) in sanctioned) return@mapNotNull null
            DetectedAnomaly(
                studentApaarId = student.apaarId,
                institutionId = student.institutionId,
                programId = student.programId,
                anomalyType = AnomalyType.UNSANCTIONED_PROGRAM,
                severity = AnomalySeverity.CRITICAL,
                details = "Programme code '${student.programId}' is not approved for institution " +
                    "${student.institutionId}. The enrolment cannot be regularised."
            )
        }
    }

    // ------------------------------------------------------------------ 1

    private fun detectInvalidApaarFormat(snapshot: RegistrySnapshot): List<DetectedAnomaly> =
        snapshot.students.mapNotNull { student ->
            val validation = ApaarIdValidator.validate(student.apaarId)
            if (validation.isStructurallyValid) return@mapNotNull null
            DetectedAnomaly(
                studentApaarId = student.apaarId,
                institutionId = student.institutionId,
                programId = student.programId,
                anomalyType = AnomalyType.INVALID_APAAR_FORMAT,
                severity = AnomalySeverity.CRITICAL,
                details = validation.errors.firstOrNull()
                    ?: "APAAR ID '${student.apaarId}' does not conform to the 12-digit registry structure."
            )
        }

    // ------------------------------------------------------------------ 2

    private fun detectCrossInstitutionDuplicates(snapshot: RegistrySnapshot): List<DetectedAnomaly> {
        val active = snapshot.students.filter { it.isActive }
        return active.groupBy { it.apaarId }
            .filter { (_, rows) -> rows.map { it.institutionId }.distinct().size > 1 }
            .flatMap { (apaarId, rows) ->
                val institutionNames = rows.map { it.institutionId }.distinct()
                val regularHits = rows.count { it.admissionQuota.isRegular }
                val severity = if (regularHits >= 2) AnomalySeverity.CRITICAL else AnomalySeverity.HIGH
                rows.map { row ->
                    DetectedAnomaly(
                        studentApaarId = apaarId,
                        institutionId = row.institutionId,
                        programId = row.programId,
                        anomalyType = AnomalyType.DUPLICATE_CROSS_COLLEGE,
                        severity = severity,
                        details = "APAAR ID is concurrently active across ${institutionNames.size} institutions " +
                            "(${institutionNames.joinToString(", ")}). One person cannot hold concurrent " +
                            "regular full-time AICTE admissions."
                    )
                }
            }
    }

    // ------------------------------------------------------------------ 3

    private fun detectIntakeBreaches(snapshot: RegistrySnapshot): List<DetectedAnomaly> {
        val out = mutableListOf<DetectedAnomaly>()
        snapshot.programs.forEach { program ->
            val regular = snapshot.students
                .filter {
                    it.isActive &&
                        it.institutionId == program.institutionId &&
                        it.programId == program.programId &&
                        it.admissionQuota.isRegular
                }
                .sortedWith(compareBy({ it.enrollmentDate }, { it.apaarId }))

            val overflow = regular.size - program.approvedIntake
            if (overflow > 0) {
                regular.drop(program.approvedIntake).forEach { student ->
                    out += DetectedAnomaly(
                        studentApaarId = student.apaarId,
                        institutionId = program.institutionId,
                        programId = program.programId,
                        anomalyType = AnomalyType.EXCESS_APPROVED_INTAKE,
                        severity = AnomalySeverity.CRITICAL,
                        details = "${program.programName} is over-admitted by $overflow seat(s): " +
                            "${regular.size} regular enrolments against a sanctioned intake of " +
                            "${program.approvedIntake}."
                    )
                }
            }
        }
        return out
    }

    // ------------------------------------------------------------------ 4

    private fun detectSupernumeraryBreaches(snapshot: RegistrySnapshot): List<DetectedAnomaly> {
        val out = mutableListOf<DetectedAnomaly>()
        snapshot.programs.forEach { program ->
            val bucket = snapshot.students.filter {
                it.isActive &&
                    it.institutionId == program.institutionId &&
                    it.programId == program.programId
            }

            fun flag(
                rows: List<Student>,
                cap: Int,
                basis: String,
                citation: String
            ) {
                val overflow = rows.size - cap
                if (overflow <= 0) return
                val severity = if (overflow > ESCALATION_THRESHOLD) AnomalySeverity.CRITICAL else AnomalySeverity.WARNING
                rows.drop(cap).forEach { student ->
                    out += DetectedAnomaly(
                        studentApaarId = student.apaarId,
                        institutionId = program.institutionId,
                        programId = program.programId,
                        anomalyType = AnomalyType.SUPERNUMERARY_BREACH,
                        severity = severity,
                        details = "$basis cap exceeded for ${program.programName}: ${rows.size} admitted against " +
                            "a ceiling of $cap ($citation)."
                    )
                }
            }

            flag(
                rows = bucket.filter { it.admissionQuota == AdmissionQuota.NRI },
                cap = program.maxSupernumeraryNri,
                basis = "NRI supernumerary",
                citation = "AICTE APH — max 5% of sanctioned intake"
            )
            flag(
                rows = bucket.filter {
                    it.admissionQuota == AdmissionQuota.OCI || it.admissionQuota == AdmissionQuota.FN
                },
                cap = program.maxSupernumeraryFnOci,
                basis = "OCI / Foreign National supernumerary",
                citation = "AICTE APH — max 15% of sanctioned intake"
            )
            flag(
                rows = bucket.filter { it.admissionQuota == AdmissionQuota.TFW },
                cap = program.maxSupernumeraryTfw,
                basis = "Tuition Fee Waiver supernumerary",
                citation = "AICTE APH — max 5% of sanctioned intake"
            )
            flag(
                rows = bucket.filter { it.admissionQuota == AdmissionQuota.PMSSS },
                cap = program.maxPmsss,
                basis = "PMSSS",
                citation = "AICTE APH — capped per course / institute"
            )
        }
        return out
    }

    // ------------------------------------------------------------------ 5

    private fun detectInconsistencies(snapshot: RegistrySnapshot): List<DetectedAnomaly> {
        val out = mutableListOf<DetectedAnomaly>()
        snapshot.students.forEach { student ->
            val nationality = student.nationality.trim()
            val missing = mutableListOf<String>()

            if (student.admissionQuota == AdmissionQuota.FN) {
                if (student.passportNumber.isNullOrBlank()) missing += "passport number"
                if (student.countryOfOrigin.isNullOrBlank()) missing += "country of origin"
                if (student.visaValidity.isNullOrBlank()) missing += "student visa validity"
            }
            if (student.admissionQuota == AdmissionQuota.OCI && nationality.isNotBlank() &&
                !nationality.equals("Indian", ignoreCase = true) &&
                !nationality.contains("OCI", ignoreCase = true)
            ) {
                missing += "OCI nationality declaration"
            }

            if (missing.isNotEmpty()) {
                out += DetectedAnomaly(
                    studentApaarId = student.apaarId,
                    institutionId = student.institutionId,
                    programId = student.programId,
                    anomalyType = AnomalyType.INCONSISTENT_CATEGORY,
                    severity = AnomalySeverity.WARNING,
                    details = "Missing or contradictory documentation for ${student.admissionQuota.label}: " +
                        missing.joinToString(", ") + "."
                )
            } else if (student.admissionQuota.isRegular &&
                nationality.isNotBlank() &&
                !nationality.equals("Indian", ignoreCase = true)
            ) {
                out += DetectedAnomaly(
                    studentApaarId = student.apaarId,
                    institutionId = student.institutionId,
                    programId = student.programId,
                    anomalyType = AnomalyType.INCONSISTENT_CATEGORY,
                    severity = AnomalySeverity.WARNING,
                    details = "Quota category '${student.admissionQuota.label}' was declared against a " +
                        "non-Indian nationality ($nationality)."
                )
            }
        }
        return out
    }

    // ------------------------------------------------------------ helpers

    /**
     * Builds the real-time utilisation snapshot for every programme in the registry.
     */
    fun buildSnapshots(snapshot: RegistrySnapshot): List<IntakeSnapshot> {
        val active = snapshot.students.filter { it.isActive }
        return snapshot.programs.map { program ->
            val rows = active.filter {
                it.institutionId == program.institutionId && it.programId == program.programId
            }
            IntakeSnapshot(
                program = program,
                regularEnrolled = rows.count { it.admissionQuota.isRegular },
                supernumeraryEnrolled = rows.count { it.admissionQuota.isSupernumerary },
                totalEnrolled = rows.size,
                nriEnrolled = rows.count { it.admissionQuota == AdmissionQuota.NRI },
                ociFnEnrolled = rows.count {
                    it.admissionQuota == AdmissionQuota.OCI || it.admissionQuota == AdmissionQuota.FN
                },
                tfwEnrolled = rows.count { it.admissionQuota == AdmissionQuota.TFW },
                pmsssEnrolled = rows.count { it.admissionQuota == AdmissionQuota.PMSSS }
            )
        }
    }
}
