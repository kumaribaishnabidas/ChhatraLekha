package com.acadentrix.core.csv

import com.acadentrix.core.model.Anomaly
import com.acadentrix.core.model.AuditEntry
import com.acadentrix.core.model.Student

/**
 * Deterministic CSV writers for the regulatory reports.
 *
 * The student export is deliberately **round-trip compatible** with
 * [CsvIngestion]: the columns written here can be pasted straight back into
 * the batch importer without any column mapping, which is what makes the
 * "export for the regional office, correct it, upload it again" workflow
 * possible.
 *
 * Quoting follows RFC 4180: a field is quoted when it contains a comma, a
 * double quote or a line break, and embedded quotes are doubled.
 */
object CsvExport {

    /** Column order of the student register export. */
    val STUDENT_COLUMNS: List<String> = listOf(
        "APAAR_ID",
        "FULL_NAME",
        "DOB",
        "GENDER",
        "ROLL_NO",
        "PROGRAM_CODE",
        "CATEGORY",
        "NATIONALITY",
        "DOC_NUMBER",
        "SOCIAL_CATEGORY",
        "ADMISSION_DATE",
        "ACADEMIC_YEAR",
        "INSTITUTION_ID",
        "CONTACT_EMAIL",
        "CONTACT_PHONE",
        "STATE_OF_DOMICILE",
        "VERIFICATION_STATUS"
    )

    /** Column order of the anomaly export. */
    val ANOMALY_COLUMNS: List<String> = listOf(
        "APAAR_ID",
        "INSTITUTION_ID",
        "PROGRAM_CODE",
        "ANOMALY_TYPE",
        "SEVERITY",
        "DETAILS",
        "DETECTED_AT"
    )

    /** Column order of the audit-trail export. */
    val AUDIT_COLUMNS: List<String> = listOf(
        "TIMESTAMP",
        "ACTOR",
        "ACTION",
        "SUBJECT",
        "CATEGORY",
        "DETAILS",
        "PREV_HASH",
        "HASH"
    )

    /**
     * Renders the student register as CSV.
     *
     * @param students the rows to write, in the order they should appear.
     * @param includeHeader whether to emit the header line (default `true`).
     */
    fun students(students: List<Student>, includeHeader: Boolean = true): String {
        val lines = mutableListOf<String>()
        if (includeHeader) lines += STUDENT_COLUMNS.joinToString(",")
        students.forEach { student ->
            lines += listOf(
                student.apaarId,
                student.studentName,
                student.dateOfBirth,
                student.gender.code,
                student.studentInstituteRollNo,
                student.programId,
                student.admissionQuota.code,
                student.nationality,
                student.passportNumber.orEmpty(),
                student.socialCategory.code,
                student.admissionDate.orEmpty(),
                student.academicYear,
                student.institutionId,
                student.contactEmail.orEmpty(),
                student.contactPhone.orEmpty(),
                student.stateOfDomicile.orEmpty(),
                student.verificationStatus.name
            ).joinToString(",") { escape(it) }
        }
        return lines.joinToString("\n")
    }

    /**
     * Renders the anomaly register as CSV.
     */
    fun anomalies(anomalies: List<Anomaly>, includeHeader: Boolean = true): String {
        val lines = mutableListOf<String>()
        if (includeHeader) lines += ANOMALY_COLUMNS.joinToString(",")
        anomalies.forEach { anomaly ->
            lines += listOf(
                anomaly.studentApaarId,
                anomaly.institutionId,
                anomaly.programId.orEmpty(),
                anomaly.anomalyType.name,
                anomaly.severity.name,
                anomaly.details,
                anomaly.timestamp.toString()
            ).joinToString(",") { escape(it) }
        }
        return lines.joinToString("\n")
    }

    /**
     * Renders the audit trail as CSV, including the chain hashes that make the
     * trail tamper-evident.
     */
    fun auditTrail(entries: List<AuditEntry>, includeHeader: Boolean = true): String {
        val lines = mutableListOf<String>()
        if (includeHeader) lines += AUDIT_COLUMNS.joinToString(",")
        entries.forEach { entry ->
            lines += listOf(
                entry.timestamp.toString(),
                entry.actor,
                entry.action,
                entry.subject,
                entry.category,
                entry.details,
                entry.prevHash,
                entry.hash
            ).joinToString(",") { escape(it) }
        }
        return lines.joinToString("\n")
    }

    /**
     * Quotes a single CSV field following RFC 4180.
     *
     * Leading/trailing whitespace is preserved because it is part of the
     * value; only separators and quotes force quoting.
     */
    fun escape(value: String?): String {
        val raw = value ?: ""
        val needsQuoting = raw.any { it == ',' || it == '"' || it == '\n' || it == '\r' }
        if (!needsQuoting) return raw
        return "\"" + raw.replace("\"", "\"\"") + "\""
    }
}
