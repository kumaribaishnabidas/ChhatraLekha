package com.chhatralekha.core.validation

import com.chhatralekha.core.model.AdmissionQuota
import com.chhatralekha.core.model.AnomalySeverity
import com.chhatralekha.core.model.AnomalyType
import com.chhatralekha.core.model.Institution
import com.chhatralekha.core.model.IntakeSnapshot
import com.chhatralekha.core.model.ProgramIntake
import com.chhatralekha.core.model.Student

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
 * Ten discrete checks are executed over the registry snapshot:
 *  1. APAAR syntactic check — 12-digit structure and non-triviality.
 *  2. Cross-institutional multi-enrolment — one APAAR, many institutions.
 *  3. Same-institution duplicate — one APAAR, twice in a single institution.
 *  4. Duplicate institute roll number within one institution.
 *  5. Intake breach check — regular enrolment against sanctioned capacity.
 *  6. Supernumerary ceiling check — NRI / OCI+FN / TFW / PMSSS caps.
 *  7. Documentary consistency for foreign nationals and quota contradictions.
 *  8. Impossible dates — unparseable, future, or enrolment before birth.
 *  9. Missing mandatory fields.
 * 10. Unsanctioned programme — enrolment in a course the institute may not run.
 *
 * The first four layers are *identity* checks (who is this student, and is the
 * same student admitted twice), layers five and six are *capacity* checks, and
 * layers seven to ten are *data-integrity* checks. Every rule is a pure
 * function of the snapshot, so the mobile app and the server always reach the
 * same verdict for the same data.
 */
object AnomalyEngine {

    /** Severity is escalated to CRITICAL once a cap is exceeded by more than two seats. */
    private const val ESCALATION_THRESHOLD = 2

    /** No student can plausibly enrol before this age. */
    private const val MINIMUM_ENROLMENT_AGE = 15

    /** The earliest birth year that can be real for a student in the registry. */
    private const val EARLIEST_PLAUSIBLE_BIRTH_YEAR = 1900

    fun evaluate(snapshot: RegistrySnapshot): List<DetectedAnomaly> {
        val anomalies = mutableListOf<DetectedAnomaly>()
        anomalies += detectInvalidApaarFormat(snapshot)
        anomalies += detectCrossInstitutionDuplicates(snapshot)
        anomalies += detectSameInstitutionDuplicates(snapshot)
        anomalies += detectDuplicateRollNumbers(snapshot)
        anomalies += detectIntakeBreaches(snapshot)
        anomalies += detectSupernumeraryBreaches(snapshot)
        anomalies += detectInconsistencies(snapshot)
        anomalies += detectImpossibleDates(snapshot)
        anomalies += detectMissingRequiredFields(snapshot)
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

    /**
     * The same APAAR ID must not appear twice inside one institution either.
     *
     * The cross-institution rule catches a student who is admitted by two
     * colleges; this rule catches the other half of the problem — one college
     * importing the same row twice, or admitting the same person to two
     * programmes of its own. The second case is the more common data-entry
     * accident and inflates every intake and utilisation figure.
     */
    private fun detectSameInstitutionDuplicates(snapshot: RegistrySnapshot): List<DetectedAnomaly> {
        val active = snapshot.students.filter { it.isActive }
        return active.groupBy { it.institutionId to it.apaarId }
            .filter { (_, rows) -> rows.size > 1 }
            .flatMap { (key, rows) ->
                val (institutionId, apaarId) = key
                val programmeCount = rows.map { it.programId }.distinct().size
                val severity = if (programmeCount > 1) AnomalySeverity.CRITICAL else AnomalySeverity.HIGH
                rows.map { row ->
                    DetectedAnomaly(
                        studentApaarId = apaarId,
                        institutionId = institutionId,
                        programId = row.programId,
                        anomalyType = AnomalyType.DUPLICATE_SAME_INSTITUTION,
                        severity = severity,
                        details = if (programmeCount > 1) {
                            "APAAR ID is enrolled ${rows.size} times inside institution $institutionId " +
                                "across $programmeCount different programmes. A single student cannot hold " +
                                "two AICTE admissions in the same institute."
                        } else {
                            "APAAR ID appears ${rows.size} times inside institution $institutionId for the " +
                                "same programme '${row.programId}'. The row has been imported more than once."
                        }
                    )
                }
            }
    }

    // ------------------------------------------------------------------ 4

    /**
     * Institute roll numbers must be unique within an institution.
     *
     * A roll number is the key an institute uses to find a student on its own
     * internal systems, so two different students sharing one makes the
     * institute's own records ambiguous.
     */
    private fun detectDuplicateRollNumbers(snapshot: RegistrySnapshot): List<DetectedAnomaly> {
        val active = snapshot.students.filter { it.isActive && it.studentInstituteRollNo.isNotBlank() }
        return active.groupBy { it.institutionId to it.studentInstituteRollNo.trim().uppercase() }
            .filter { (_, rows) -> rows.map { it.apaarId }.distinct().size > 1 }
            .flatMap { (_, rows) ->
                val rollNo = rows.first().studentInstituteRollNo.trim()
                val institutionId = rows.first().institutionId
                val students = rows.map { it.apaarId }.distinct()
                rows.map { row ->
                    DetectedAnomaly(
                        studentApaarId = row.apaarId,
                        institutionId = institutionId,
                        programId = row.programId,
                        anomalyType = AnomalyType.DUPLICATE_ROLL_NUMBER,
                        severity = AnomalySeverity.HIGH,
                        details = "Institute roll number '$rollNo' is held by ${students.size} different " +
                            "students in institution $institutionId (${students.joinToString(", ")}). " +
                            "Institute roll numbers must be unique within an institution."
                    )
                }
            }
    }

    // ------------------------------------------------------------------ 5

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

    // ------------------------------------------------------------------ 6

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

    // ------------------------------------------------------------------ 7

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
            }

            // Quota / nationality contradictions. Each AICTE quota bucket carries
            // its own nationality premise, so a mismatch means the bucket itself
            // was entered wrongly rather than merely undocumented.
            val contradiction = quotaNationalityConflict(student.admissionQuota, nationality)
            if (contradiction != null) {
                out += DetectedAnomaly(
                    studentApaarId = student.apaarId,
                    institutionId = student.institutionId,
                    programId = student.programId,
                    anomalyType = AnomalyType.INCONSISTENT_CATEGORY,
                    severity = if (student.admissionQuota == AdmissionQuota.FN) {
                        AnomalySeverity.CRITICAL
                    } else {
                        AnomalySeverity.HIGH
                    },
                    details = contradiction
                )
            }
        }
        return out
    }

    /**
     * Returns a description of the quota / nationality contradiction, or null
     * when the pair is coherent.
     *
     * * `FN` (Foreign National) must not be an Indian national.
     * * `NRI` is by definition an Indian national — the seat exists for Indian
     *   citizens studying abroad, so a foreign nationality under an NRI bucket
     *   is a mis-bucketed foreign national.
     * * `OCI` (Overseas Citizen of India) is an Indian national.
     * * `TFW` and `PMSSS` are Government of India entitlements reserved for
     *   Indian students.
     */
    private fun quotaNationalityConflict(quota: AdmissionQuota, nationality: String): String? {
        if (nationality.isBlank()) return null
        val indian = isIndianNationality(nationality)
        return when (quota) {
            AdmissionQuota.FN ->
                if (indian) {
                    "Quota category 'Foreign National' was declared against the Indian nationality " +
                        "'$nationality'. A foreign-national seat cannot be held by an Indian citizen."
                } else {
                    null
                }

            AdmissionQuota.NRI ->
                if (!indian) {
                    "Quota category 'NRI Supernumerary' was declared against the non-Indian " +
                        "nationality '$nationality'. NRI seats are reserved for Indian nationals, so " +
                        "this admission belongs in the Foreign National bucket."
                } else {
                    null
                }

            AdmissionQuota.TFW ->
                if (!indian) {
                    "Tuition Fee Waiver was granted to a student of nationality '$nationality'. The " +
                        "TFW supernumerary is reserved for Indian nationals."
                } else {
                    null
                }

            AdmissionQuota.PMSSS ->
                if (!indian) {
                    "PMSSS scholarship was granted to a student of nationality '$nationality'. The PMSSS " +
                        "scheme is reserved for Indian nationals."
                } else {
                    null
                }

            AdmissionQuota.OCI -> null

            AdmissionQuota.MERIT, AdmissionQuota.MANAGEMENT ->
                if (!indian) {
                    "Regular-seat quota category '${quota.label}' was declared against a non-Indian " +
                        "nationality ($nationality)."
                } else {
                    null
                }
        }
    }

    /** True when the declared nationality denotes an Indian national. */
    private fun isIndianNationality(nationality: String): Boolean {
        val value = nationality.trim()
        return value.equals("Indian", ignoreCase = true) ||
            value.equals("India", ignoreCase = true) ||
            value.contains("Indian", ignoreCase = true) ||
            value.contains("OCI", ignoreCase = true)
    }

    // ------------------------------------------------------------------ 8

    /**
     * Dates that cannot be true.
     *
     * A record with an enrolment date before the student's date of birth, a
     * date in the future, or a date that is not a real calendar day is not a
     * regulatory breach, but it makes every enrolment statistic built on the
     * record unreliable.
     */
    private fun detectImpossibleDates(snapshot: RegistrySnapshot): List<DetectedAnomaly> {
        val out = mutableListOf<DetectedAnomaly>()
        val currentYear = java.util.Calendar.getInstance().get(java.util.Calendar.YEAR)

        snapshot.students.forEach { student ->
            val dobRaw = student.dateOfBirth.trim()
            val enrollmentRaw = student.enrollmentDate.trim()

            val dob = if (dobRaw.isBlank()) null else parseDate(dobRaw)
            val enrollment = if (enrollmentRaw.isBlank()) null else parseDate(enrollmentRaw)
            var dobPlausible = true

            fun flag(details: String, severity: AnomalySeverity) {
                out += DetectedAnomaly(
                    studentApaarId = student.apaarId,
                    institutionId = student.institutionId,
                    programId = student.programId,
                    anomalyType = AnomalyType.IMPOSSIBLE_DATE,
                    severity = severity,
                    details = details
                )
            }

            if (dobRaw.isNotBlank() && dob == null) {
                flag(
                    "Date of birth '$dobRaw' is not a valid calendar date.",
                    AnomalySeverity.CRITICAL
                )
                dobPlausible = false
            } else if (dob != null) {
                if (dob.year > currentYear) {
                    flag(
                        "Date of birth '$dobRaw' is in the future (${dob.year}).",
                        AnomalySeverity.CRITICAL
                    )
                    dobPlausible = false
                } else if (dob.year < EARLIEST_PLAUSIBLE_BIRTH_YEAR) {
                    flag(
                        "Date of birth '$dobRaw' is not a plausible birth year for an enrolled student.",
                        AnomalySeverity.CRITICAL
                    )
                    dobPlausible = false
                }
            }

            if (enrollmentRaw.isNotBlank() && enrollment == null) {
                flag(
                    "Enrolment date '$enrollmentRaw' is not a valid calendar date.",
                    AnomalySeverity.CRITICAL
                )
            } else if (enrollment != null) {
                if (enrollment.year > currentYear) {
                    flag(
                        "Enrolment date '$enrollmentRaw' is in the future (${enrollment.year}).",
                        AnomalySeverity.CRITICAL
                    )
                }
                // The comparisons below are only meaningful once the date of
                // birth itself has been shown to be plausible.
                if (dob != null && dobPlausible && enrollment.isBefore(dob)) {
                    flag(
                        "Enrolment date '$enrollmentRaw' precedes the date of birth '$dobRaw'.",
                        AnomalySeverity.CRITICAL
                    )
                } else if (dob != null && dobPlausible) {
                    val age = ageInYears(dob, enrollment)
                    if (age in 0 until MINIMUM_ENROLMENT_AGE) {
                        flag(
                            "Student was $age year(s) old at enrolment on '$enrollmentRaw', which is below " +
                                "the plausible minimum of $MINIMUM_ENROLMENT_AGE years.",
                            AnomalySeverity.HIGH
                        )
                    }
                }
            }
        }
        return out
    }

    // ------------------------------------------------------------------ 9

    /**
     * Mandatory fields that an AICTE-approved institution must record.
     *
     * A row with a blank programme, academic year, roll number, name or date
     * of birth cannot be counted towards any sanctioned seat and blocks the
     * institution from issuing a verifiable credential.
     */
    private fun detectMissingRequiredFields(snapshot: RegistrySnapshot): List<DetectedAnomaly> {
        val out = mutableListOf<DetectedAnomaly>()
        snapshot.students.forEach { student ->
            val missing = buildList {
                if (student.studentName.isBlank()) add("student name")
                if (student.dateOfBirth.isBlank()) add("date of birth")
                if (student.studentInstituteRollNo.isBlank()) add("institute roll number")
                if (student.programId.isBlank()) add("programme code")
                if (student.institutionId.isBlank()) add("institution id")
                if (student.academicYear.isBlank()) add("academic year")
                if (student.enrollmentDate.isBlank()) add("enrolment date")
                if (student.nationality.isBlank()) add("nationality")
            }
            if (missing.isEmpty()) return@forEach
            out += DetectedAnomaly(
                studentApaarId = student.apaarId,
                institutionId = student.institutionId,
                programId = student.programId,
                anomalyType = AnomalyType.MISSING_REQUIRED_FIELD,
                severity = AnomalySeverity.HIGH,
                details = "Mandatory field(s) missing from the enrolment record: " +
                    missing.joinToString(", ") + "."
            )
        }
        return out
    }

    // ------------------------------------------------------------ helpers

    /** A parsed calendar date. */
    private data class ParsedDate(val year: Int, val month: Int, val day: Int) {
        fun isBefore(other: ParsedDate): Boolean =
            when {
                year != other.year -> year < other.year
                month != other.month -> month < other.month
                else -> day < other.day
            }
    }

    /**
     * Parses a date written as `yyyy-MM-dd` (the registry format) or
     * `dd-MM-yyyy` (the format used on visa documents).
     */
    private fun parseDate(raw: String): ParsedDate? {
        val value = raw.trim()
        val parts = value.split('-', '/', '.')
        if (parts.size != 3) return null
        val numbers = parts.map { it.trim().toIntOrNull() ?: return null }
        val (year, month, day) = if (numbers[0] > 31) {
            Triple(numbers[0], numbers[1], numbers[2])
        } else {
            Triple(numbers[2], numbers[1], numbers[0])
        }
        if (year !in 1000..9999 || month !in 1..12 || day !in 1..31) return null
        if (day > daysInMonth(year, month)) return null
        return ParsedDate(year, month, day)
    }

    private fun daysInMonth(year: Int, month: Int): Int = when (month) {
        1, 3, 5, 7, 8, 10, 12 -> 31
        4, 6, 9, 11 -> 30
        else -> if (isLeapYear(year)) 29 else 28
    }

    private fun isLeapYear(year: Int): Boolean =
        (year % 4 == 0 && year % 100 != 0) || year % 400 == 0

    private fun ageInYears(dob: ParsedDate, at: ParsedDate): Int {
        var age = at.year - dob.year
        if (at.month < dob.month || (at.month == dob.month && at.day < dob.day)) age--
        return age
    }

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
