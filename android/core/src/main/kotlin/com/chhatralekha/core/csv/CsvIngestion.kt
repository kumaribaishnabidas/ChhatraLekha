package com.chhatralekha.core.csv

import com.chhatralekha.core.model.AdmissionQuota
import com.chhatralekha.core.model.AnomalySeverity
import com.chhatralekha.core.model.ProgramIntake
import com.chhatralekha.core.validation.ApaarIdValidator

/**
 * Severity of a single validation issue found on a CSV row.
 */
enum class RowIssueSeverity { CRITICAL, WARNING }

/**
 * One issue detected on an ingested row.
 */
data class RowIssue(
    val code: String,
    val severity: RowIssueSeverity,
    val message: String
)

/**
 * A parsed CSV row together with its validation outcome.
 */
data class CsvStudentRow(
    val lineNumber: Int,
    val apaarId: String,
    val fullName: String,
    val dob: String,
    val gender: String,
    val rollNo: String,
    val programCode: String,
    val category: String,
    val nationality: String,
    val docNumber: String,
    val raw: String,
    val issues: List<RowIssue>
) {
    val criticalIssues: List<RowIssue> get() = issues.filter { it.severity == RowIssueSeverity.CRITICAL }
    val warningIssues: List<RowIssue> get() = issues.filter { it.severity == RowIssueSeverity.WARNING }
    val isBlocked: Boolean get() = criticalIssues.isNotEmpty()
    val isClean: Boolean get() = issues.isEmpty()
    val quota: AdmissionQuota? get() = AdmissionQuota.fromCode(category)
}

/**
 * Programme-level seat impact produced by an incoming batch.
 */
data class ProgramImpact(
    val programCode: String,
    val programName: String,
    val approvedIntake: Int,
    val existingRegular: Int,
    val incomingRegular: Int,
    val existingSupernumerary: Int,
    val incomingSupernumerary: Int,
    val capMessages: List<String>
) {
    val projectedRegular: Int get() = existingRegular + incomingRegular
    val projectedTotal: Int get() = projectedRegular + existingSupernumerary + incomingSupernumerary
    val regularOverflow: Int get() = (projectedRegular - approvedIntake).coerceAtLeast(0)
}

/**
 * Full outcome of a batch ingestion preview.
 */
data class CsvIngestionReport(
    val rows: List<CsvStudentRow> = emptyList(),
    val headerErrors: List<String> = emptyList(),
    val programImpacts: List<ProgramImpact> = emptyList(),
    val unknownPrograms: List<String> = emptyList()
) {
    val totalRows: Int get() = rows.size
    val validRows: Int get() = rows.count { it.issues.none { i -> i.severity == RowIssueSeverity.CRITICAL } }
    val cleanRows: Int get() = rows.count { it.isClean }
    val criticalRows: Int get() = rows.count { it.issues.any { i -> i.severity == RowIssueSeverity.CRITICAL } }
    val warningRows: Int get() = rows.count { it.warningIssues.isNotEmpty() && it.criticalIssues.isEmpty() }
    val duplicateRows: Int get() = rows.count { row -> row.issues.any { it.code == "DUPLICATE" } }
    val committableRows: List<CsvStudentRow>
        get() = rows.filter { row -> row.issues.none { i -> i.severity == RowIssueSeverity.CRITICAL } }
    val isEmpty: Boolean get() = rows.isEmpty()
}

/**
 * Context required to validate an incoming batch against the live registry.
 */
data class CsvValidationContext(
    val programs: List<ProgramIntake>,
    val existingApaarIds: Set<String>,
    val existingRegularCounts: Map<String, Int>,
    val existingSupernumeraryCounts: Map<String, Int>,
    val existingNriCounts: Map<String, Int>,
    val existingOciFnCounts: Map<String, Int>,
    val existingTfwCounts: Map<String, Int>,
    val existingPmsssCounts: Map<String, Int>
) {
    companion object {
        fun empty() = CsvValidationContext(emptyList(), emptySet(), emptyMap(), emptyMap(), emptyMap(), emptyMap(), emptyMap(), emptyMap())
    }
}

/**
 * Minimal RFC-4180 style CSV reader that tolerates quoted fields, escaped quotes
 * and BOM-prefixed files.
 */
object CsvParser {

    fun parse(text: String): Pair<List<String>, List<List<String>>> {
        val clean = text.removePrefix("\uFEFF")
        val records = mutableListOf<List<String>>()
        var current = mutableListOf<String>()
        val field = StringBuilder()
        var inQuotes = false
        var index = 0

        fun commitField() {
            current.add(field.toString())
            field.setLength(0)
        }

        fun commitRecord() {
            commitField()
            if (current.any { it.isNotBlank() } || current.size > 1) records.add(current)
            current = mutableListOf()
        }

        while (index < clean.length) {
            val ch = clean[index]
            when {
                inQuotes && ch == '"' && index + 1 < clean.length && clean[index + 1] == '"' -> {
                    field.append('"'); index++
                }
                ch == '"' -> inQuotes = !inQuotes
                !inQuotes && ch == ',' -> commitField()
                !inQuotes && (ch == '\n' || ch == '\r') -> {
                    if (ch == '\r' && index + 1 < clean.length && clean[index + 1] == '\n') index++
                    commitRecord()
                }
                else -> field.append(ch)
            }
            index++
        }
        if (field.isNotEmpty() || current.isNotEmpty()) commitRecord()
        return (records.firstOrNull() ?: emptyList()) to records.drop(1)
    }
}

/**
 * Live validator for the AICTE batch admission CSV schema.
 */
object CsvIngestionValidator {

    const val TEMPLATE = """APAAR_ID,Full_Name,DOB,Gender,Roll_No,Program_Code,Category,Nationality,Doc_Number
984210357890,Aakash Verma,2004-03-12,Male,CSE-24-010,BTECH_CSE,REGULAR_MERIT,Indian,
984210357891,Sanya Kapoor,2005-01-20,Female,CSE-24-011,BTECH_CSE,SUPERNUMERARY_TFW,Indian,
984210357892,Zaid Abdullah,2003-07-15,Male,CSE-24-012,BTECH_CSE,SUPERNUMERARY_FN,Oman,OM-8921045
984210357893,Ananya Joshi,2004-11-02,Female,ECE-24-008,BTECH_ECE,REGULAR_MERIT,Indian,"""

    private val aliases = mapOf(
        "apaar_id" to "APAAR_ID",
        "apaarid" to "APAAR_ID",
        "apaar" to "APAAR_ID",
        "full_name" to "FULL_NAME",
        "name" to "FULL_NAME",
        "student_name" to "FULL_NAME",
        "dob" to "DOB",
        "date_of_birth" to "DOB",
        "gender" to "GENDER",
        "sex" to "GENDER",
        "roll_no" to "ROLL_NO",
        "rollno" to "ROLL_NO",
        "institute_roll_no" to "ROLL_NO",
        "program_code" to "PROGRAM_CODE",
        "program" to "PROGRAM_CODE",
        "category" to "CATEGORY",
        "quota" to "CATEGORY",
        "admission_quota" to "CATEGORY",
        "nationality" to "NATIONALITY",
        "doc_number" to "DOC_NUMBER",
        "passport_no" to "DOC_NUMBER",
        "document_number" to "DOC_NUMBER"
    )

    private val requiredColumns = listOf("APAAR_ID", "FULL_NAME", "PROGRAM_CODE", "CATEGORY")

    fun validate(text: String, context: CsvValidationContext): CsvIngestionReport {
        val (headerRow, dataRows) = CsvParser.parse(text)
        val headerErrors = mutableListOf<String>()
        if (headerRow.isEmpty()) {
            return CsvIngestionReport(headerErrors = listOf("No header row found. Paste a CSV starting with the column header line."))
        }

        val headerIndex = mutableMapOf<String, Int>()
        headerRow.forEachIndexed { index, raw ->
            val canonical = aliases[raw.trim().lowercase().replace(" ", "_")] ?: raw.trim().uppercase()
            headerIndex[canonical] = index
        }
        requiredColumns.forEach { column ->
            if (!headerIndex.containsKey(column)) {
                headerErrors += "Missing mandatory column '$column'."
            }
        }
        if (headerErrors.isNotEmpty()) {
            return CsvIngestionReport(headerErrors = headerErrors)
        }

        val programsByCode = context.programs.associateBy { it.programId.uppercase() }
        val rows = mutableListOf<CsvStudentRow>()

        dataRows.forEachIndexed { rowIndex, fields ->
            val lineNumber = rowIndex + 2
            fun value(column: String): String = headerIndex[column]?.let { fields.getOrNull(it)?.trim() }.orEmpty()

            val apaarId = value("APAAR_ID")
            val fullName = value("FULL_NAME")
            val dob = value("DOB")
            val gender = value("GENDER")
            val rollNo = value("ROLL_NO")
            val programCode = value("PROGRAM_CODE").uppercase()
            val category = value("CATEGORY")
            val nationality = value("NATIONALITY")
            val docNumber = value("DOC_NUMBER")

            val issues = mutableListOf<RowIssue>()

            val validation = ApaarIdValidator.validate(apaarId)
            if (!validation.isStructurallyValid) {
                issues += RowIssue(
                    "INVALID_APAAR",
                    RowIssueSeverity.CRITICAL,
                    validation.errors.firstOrNull() ?: "Invalid APAAR ID."
                )
            } else {
                if (!validation.isChecksumValid) {
                    issues += RowIssue(
                        "LUHN_ADVISORY",
                        RowIssueSeverity.WARNING,
                        "Luhn check-digit advisory: checksum does not match (non-blocking)."
                    )
                }
                if (apaarId in context.existingApaarIds) {
                    issues += RowIssue(
                        "DUPLICATE",
                        RowIssueSeverity.CRITICAL,
                        "APAAR ID is already enrolled in the national registry."
                    )
                }
            }

            if (fullName.isBlank()) {
                issues += RowIssue("MISSING_NAME", RowIssueSeverity.CRITICAL, "Full name is mandatory.")
            }

            val normalisedDob = normaliseDate(dob)
            if (normalisedDob == null) {
                issues += RowIssue(
                    "INVALID_DOB",
                    RowIssueSeverity.CRITICAL,
                    "Date of birth must be a valid calendar date (yyyy-MM-dd)."
                )
            }

            if (gender.isNotBlank() && com.chhatralekha.core.model.Gender.fromCode(gender) == null) {
                issues += RowIssue("INVALID_GENDER", RowIssueSeverity.WARNING, "Unrecognised gender value '$gender'.")
            }

            val quota = AdmissionQuota.fromCode(category)
            if (quota == null) {
                issues += RowIssue(
                    "INVALID_CATEGORY",
                    RowIssueSeverity.CRITICAL,
                    "Unknown quota category '$category'."
                )
            }

            val program = programsByCode[programCode]
            if (program == null) {
                issues += RowIssue(
                    "UNKNOWN_PROGRAM",
                    RowIssueSeverity.CRITICAL,
                    "Programme code '$programCode' is not sanctioned for this institution."
                )
            }

            if (quota != null && quota.requiresForeignDocs) {
                if (quota == AdmissionQuota.FN && docNumber.isBlank()) {
                    issues += RowIssue(
                        "MISSING_PASSPORT",
                        RowIssueSeverity.WARNING,
                        "Foreign National admission without a passport / document number."
                    )
                }
                if (nationality.isNotBlank() && !nationality.equals("Indian", ignoreCase = true)) {
                    // legitimate for FN / NRI
                }
            } else if (quota != null && quota.isRegular && nationality.isNotBlank() &&
                !nationality.equals("Indian", ignoreCase = true)
            ) {
                issues += RowIssue(
                    "CATEGORY_MISMATCH",
                    RowIssueSeverity.WARNING,
                    "Regular-seat quota declared against a non-Indian nationality ($nationality)."
                )
            }

            rows += CsvStudentRow(
                lineNumber = lineNumber,
                apaarId = apaarId,
                fullName = fullName,
                dob = normalisedDob ?: dob,
                gender = gender,
                rollNo = rollNo,
                programCode = programCode,
                category = category,
                nationality = nationality,
                docNumber = docNumber,
                raw = fields.joinToString(","),
                issues = issues
            )
        }

        // An identifier repeated inside the same batch blocks *every* row that
        // carries it: there is no way to tell which of the copies is the
        // authoritative admission, so none of them may be committed.
        val batchCounts = rows.map { it.apaarId }
            .filter { it.isNotBlank() }
            .groupingBy { it }
            .eachCount()
        val resolvedRows = rows.map { row ->
            if (row.apaarId.isNotBlank() && (batchCounts[row.apaarId] ?: 0) > 1) {
                row.copy(
                    issues = row.issues + RowIssue(
                        "DUPLICATE",
                        RowIssueSeverity.CRITICAL,
                        "APAAR ID is duplicated inside this batch."
                    )
                )
            } else {
                row
            }
        }

        val impacts = computeImpacts(resolvedRows, context)
        val unknown = resolvedRows.map { it.programCode }.filter { it.isNotBlank() && programsByCode[it] == null }.distinct()

        return CsvIngestionReport(
            rows = resolvedRows,
            headerErrors = emptyList(),
            programImpacts = impacts,
            unknownPrograms = unknown
        )
    }

    private fun computeImpacts(rows: List<CsvStudentRow>, context: CsvValidationContext): List<ProgramImpact> {
        val committable = rows.filter { row -> row.issues.none { i -> i.severity == RowIssueSeverity.CRITICAL } }
        val byProgram = committable.groupBy { it.programCode.uppercase() }
        return byProgram.mapNotNull { (code, programRows) ->
            val program = context.programs.firstOrNull { it.programId.uppercase() == code } ?: return@mapNotNull null
            val incomingRegular = programRows.count { it.quota?.isRegular == true }
            val incomingSuper = programRows.count { it.quota?.isSupernumerary == true }
            val existingRegular = context.existingRegularCounts[program.programId] ?: 0
            val existingSuper = context.existingSupernumeraryCounts[program.programId] ?: 0

            val incomingNri = programRows.count { it.quota == AdmissionQuota.NRI }
            val incomingOciFn = programRows.count {
                it.quota == AdmissionQuota.OCI || it.quota == AdmissionQuota.FN
            }
            val incomingTfw = programRows.count { it.quota == AdmissionQuota.TFW }
            val incomingPmsss = programRows.count { it.quota == AdmissionQuota.PMSSS }

            val messages = mutableListOf<String>()
            val projectedRegular = existingRegular + incomingRegular
            if (projectedRegular > program.approvedIntake) {
                messages += "Regular intake breach: $projectedRegular projected against ${program.approvedIntake} sanctioned seats."
            }
            val nriTotal = (context.existingNriCounts[program.programId] ?: 0) + incomingNri
            if (nriTotal > program.maxSupernumeraryNri) {
                messages += "NRI supernumerary ceiling exceeded: $nriTotal against ${program.maxSupernumeraryNri} (5% rule)."
            }
            val ociFnTotal = (context.existingOciFnCounts[program.programId] ?: 0) + incomingOciFn
            if (ociFnTotal > program.maxSupernumeraryFnOci) {
                messages += "OCI / FN supernumerary ceiling exceeded: $ociFnTotal against ${program.maxSupernumeraryFnOci} (15% rule)."
            }
            val tfwTotal = (context.existingTfwCounts[program.programId] ?: 0) + incomingTfw
            if (tfwTotal > program.maxSupernumeraryTfw) {
                messages += "TFW supernumerary ceiling exceeded: $tfwTotal against ${program.maxSupernumeraryTfw} (5% rule)."
            }
            val pmsssTotal = (context.existingPmsssCounts[program.programId] ?: 0) + incomingPmsss
            if (pmsssTotal > program.maxPmsss) {
                messages += "PMSSS ceiling exceeded: $pmsssTotal against ${program.maxPmsss}."
            }

            ProgramImpact(
                programCode = code,
                programName = program.programName,
                approvedIntake = program.approvedIntake,
                existingRegular = existingRegular,
                incomingRegular = incomingRegular,
                existingSupernumerary = existingSuper,
                incomingSupernumerary = incomingSuper,
                capMessages = messages
            )
        }
    }

    private fun normaliseDate(raw: String): String? {
        val value = raw.trim()
        if (value.isEmpty()) return null
        val parts = value.split("-", "/", ".").map { it.trim() }
        if (parts.size != 3) return null
        if (parts[0].length == 4) {
            // yyyy-mm-dd
            val year = parts[0].toIntOrNull() ?: return null
            val month = parts[1].toIntOrNull() ?: return null
            val day = parts[2].toIntOrNull() ?: return null
            return if (isValidDate(year, month, day)) "%04d-%02d-%02d".format(year, month, day) else null
        }
        // dd-mm-yyyy
        val day = parts[0].toIntOrNull() ?: return null
        val month = parts[1].toIntOrNull() ?: return null
        val year = parts[2].toIntOrNull() ?: return null
        val fullYear = if (year < 100) 2000 + year else year
        return if (isValidDate(fullYear, month, day)) "%04d-%02d-%02d".format(fullYear, month, day) else null
    }

    private fun isValidDate(year: Int, month: Int, day: Int): Boolean {
        if (year !in 1950..currentYear() || month !in 1..12) return false
        val maxDay = when (month) {
            1, 3, 5, 7, 8, 10, 12 -> 31
            4, 6, 9, 11 -> 30
            else -> if (isLeap(year)) 29 else 28
        }
        return day in 1..maxDay
    }

    private fun isLeap(year: Int): Boolean = (year % 4 == 0 && year % 100 != 0) || year % 400 == 0

    private fun currentYear(): Int = java.util.Calendar.getInstance().get(java.util.Calendar.YEAR)
}

/**
 * Converts an anomaly severity into the corresponding row-issue severity.
 */
fun AnomalySeverity.toRowSeverity(): RowIssueSeverity = when (this) {
    AnomalySeverity.CRITICAL, AnomalySeverity.HIGH -> RowIssueSeverity.CRITICAL
    else -> RowIssueSeverity.WARNING
}
