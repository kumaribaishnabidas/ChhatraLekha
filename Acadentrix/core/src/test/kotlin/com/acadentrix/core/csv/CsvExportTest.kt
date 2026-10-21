package com.acadentrix.core.csv

import com.acadentrix.core.model.AdmissionQuota
import com.acadentrix.core.model.Anomaly
import com.acadentrix.core.model.AnomalySeverity
import com.acadentrix.core.model.AnomalyType
import com.acadentrix.core.model.AuditEntry
import com.acadentrix.core.model.Gender
import com.acadentrix.core.model.SocialCategory
import com.acadentrix.core.model.Student
import com.acadentrix.core.model.VerificationStatus
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Behaviour of the regulatory CSV writers.
 */
class CsvExportTest {

    private fun student(
        apaarId: String = "984210357890",
        name: String = "Asha Ramesh Iyer",
        programId: String = "BTECH_CSE",
        quota: AdmissionQuota = AdmissionQuota.MERIT,
        rollNo: String = "CSE-042",
        socialCategory: SocialCategory = SocialCategory.GENERAL,
        contactEmail: String? = "asha.iyer@example.in",
        contactPhone: String? = "+91 98450 11223",
        admissionDate: String? = "2024-08-01",
        domicile: String? = "Karnataka"
    ) = Student(
        recordId = 1L,
        apaarId = apaarId,
        studentName = name,
        dateOfBirth = "2005-04-17",
        gender = Gender.FEMALE,
        institutionId = "INST-0421",
        programId = programId,
        academicYear = "2024-25",
        admissionQuota = quota,
        enrollmentDate = "2024-08-01",
        studentInstituteRollNo = rollNo,
        nationality = "Indian",
        passportNumber = null,
        visaValidity = null,
        countryOfOrigin = null,
        abcAccountId = "abc-1",
        verificationStatus = VerificationStatus.VERIFIED,
        socialCategory = socialCategory,
        admissionDate = admissionDate,
        contactEmail = contactEmail,
        contactPhone = contactPhone,
        stateOfDomicile = domicile
    )

    // ------------------------------------------------------------- students

    @Test
    fun writesTheDocumentedHeader() {
        val csv = CsvExport.students(listOf(student()))
        val header = csv.lineSequence().first()
        assertEquals(CsvExport.STUDENT_COLUMNS.joinToString(","), header)
    }

    @Test
    fun writesEveryExtendedColumn() {
        val csv = CsvExport.students(listOf(student(socialCategory = SocialCategory.OBC)))
        val row = csv.lineSequence().drop(1).first().split(",")
        val index = CsvExport.STUDENT_COLUMNS.withIndex().associate { (i, name) -> name to i }
        assertEquals("984210357890", row[index.getValue("APAAR_ID")])
        assertEquals("Asha Ramesh Iyer", row[index.getValue("FULL_NAME")])
        assertEquals("BTECH_CSE", row[index.getValue("PROGRAM_CODE")])
        assertEquals("REGULAR_MERIT", row[index.getValue("CATEGORY")])
        assertEquals("OBC", row[index.getValue("SOCIAL_CATEGORY")])
        assertEquals("2024-08-01", row[index.getValue("ADMISSION_DATE")])
        assertEquals("asha.iyer@example.in", row[index.getValue("CONTACT_EMAIL")])
        assertEquals("+91 98450 11223", row[index.getValue("CONTACT_PHONE")])
        assertEquals("Karnataka", row[index.getValue("STATE_OF_DOMICILE")])
        assertEquals("2024-25", row[index.getValue("ACADEMIC_YEAR")])
        assertEquals("VERIFIED", row[index.getValue("VERIFICATION_STATUS")])
    }

    @Test
    fun writesABlankCellForMissingOptionalValues() {
        val csv = CsvExport.students(
            listOf(student(contactEmail = null, contactPhone = null, admissionDate = null, domicile = null))
        )
        val row = csv.lineSequence().drop(1).first().split(",")
        val index = CsvExport.STUDENT_COLUMNS.withIndex().associate { (i, name) -> name to i }
        assertEquals("", row[index.getValue("CONTACT_EMAIL")])
        assertEquals("", row[index.getValue("CONTACT_PHONE")])
        assertEquals("", row[index.getValue("ADMISSION_DATE")])
        assertEquals("", row[index.getValue("STATE_OF_DOMICILE")])
    }

    @Test
    fun quotesFieldsThatContainASeparator() {
        val csv = CsvExport.students(listOf(student(name = "Iyer, Asha Ramesh")))
        assertTrue(csv.contains("\"Iyer, Asha Ramesh\""))
    }

    @Test
    fun doublesEmbeddedQuotes() {
        assertEquals("\"He said \"\"hi\"\"\"", CsvExport.escape("He said \"hi\""))
    }

    @Test
    fun leavesOrdinaryFieldsUnquoted() {
        assertEquals("BTECH_CSE", CsvExport.escape("BTECH_CSE"))
    }

    @Test
    fun quotesFieldsThatContainALineBreak() {
        assertEquals("\"line1\nline2\"", CsvExport.escape("line1\nline2"))
    }

    @Test
    fun canOmitTheHeader() {
        val csv = CsvExport.students(listOf(student()), includeHeader = false)
        assertEquals(1, csv.lineSequence().count())
        assertTrue(csv.startsWith("984210357890"))
    }

    @Test
    fun writesAnEmptyBodyForNoStudents() {
        val csv = CsvExport.students(emptyList())
        assertEquals(CsvExport.STUDENT_COLUMNS.joinToString(","), csv)
    }

    // ------------------------------------------------------- round trip

    @Test
    fun theExportCanBeFedStraightBackIntoTheImporter() {
        val original = student()
        val csv = CsvExport.students(listOf(original))
        val report = CsvIngestionValidator.validate(
            text = csv,
            context = CsvValidationContext(
                programs = listOf(
                    com.acadentrix.core.model.ProgramIntake(
                        programId = "BTECH_CSE",
                        institutionId = "INST-0421",
                        programName = "B.Tech CSE",
                        programLevel = "UG",
                        approvedIntake = 60,
                        maxSupernumeraryNri = 3,
                        maxSupernumeraryFnOci = 9,
                        maxSupernumeraryTfw = 3,
                        maxPmsss = 6
                    )
                ),
                existingApaarIds = emptySet(),
                existingRegularCounts = emptyMap(),
                existingSupernumeraryCounts = emptyMap(),
                existingNriCounts = emptyMap(),
                existingOciFnCounts = emptyMap(),
                existingTfwCounts = emptyMap(),
                existingPmsssCounts = emptyMap()
            )
        )
        assertTrue(report.headerErrors.toString(), report.headerErrors.isEmpty())
        val row = report.rows.single()
        assertEquals(original.apaarId, row.apaarId)
        assertEquals(original.studentName, row.fullName)
        assertEquals(original.dateOfBirth, row.dob)
        assertEquals(original.programId, row.programCode)
        assertEquals(original.studentInstituteRollNo, row.rollNo)
        assertEquals(original.nationality, row.nationality)
        assertEquals(original.admissionQuota, row.quota)
    }

    // ----------------------------------------------------------- anomalies

    @Test
    fun writesTheAnomalyRegister() {
        val anomaly = Anomaly(
            anomalyId = 7L,
            studentApaarId = "984210357890",
            institutionId = "INST-0421",
            programId = "BTECH_CSE",
            anomalyType = AnomalyType.EXCESS_APPROVED_INTAKE,
            severity = AnomalySeverity.CRITICAL,
            details = "Regular enrolment 62 exceeds the sanctioned 60.",
            timestamp = 1_726_000_000_000L
        )
        val csv = CsvExport.anomalies(listOf(anomaly))
        val lines = csv.lineSequence().toList()
        assertEquals(CsvExport.ANOMALY_COLUMNS.joinToString(","), lines[0])
        assertTrue(lines[1].contains("EXCESS_APPROVED_INTAKE"))
        assertTrue(lines[1].contains("CRITICAL"))
        assertTrue(lines[1].contains("1726000000000"))
    }

    @Test
    fun writesTheAuditTrailWithItsChainHashes() {
        val entry = AuditEntry(
            logId = 1L,
            timestamp = 1_726_000_000_000L,
            actor = "AICTE Central Registry",
            action = "BATCH_COMMIT",
            subject = "INST-0421",
            details = "Committed 42 rows.",
            category = "ADMISSIONS",
            prevHash = "aa".repeat(32),
            hash = "bb".repeat(32)
        )
        val csv = CsvExport.auditTrail(listOf(entry))
        val lines = csv.lineSequence().toList()
        assertEquals(CsvExport.AUDIT_COLUMNS.joinToString(","), lines[0])
        assertTrue(lines[1].contains("aa".repeat(32)))
        assertTrue(lines[1].contains("bb".repeat(32)))
    }

    @Test
    fun writesAProgramCodeWithACommaWithoutBreakingTheColumnCount() {
        val csv = CsvExport.students(listOf(student(programId = "BTECH_CSE,OLD")))
        val lines = csv.lineSequence().toList()
        assertEquals(2, lines.size)
        assertTrue(lines[1].contains("\"BTECH_CSE,OLD\""))
    }
}
