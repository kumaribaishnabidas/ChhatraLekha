package com.edusync.apaar.core.csv

import com.edusync.apaar.core.model.AdmissionQuota
import com.edusync.apaar.core.model.ProgramIntake
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Behaviour of the batch admission CSV reader and live validator.
 */
class CsvIngestionTest {

    private val cse = ProgramIntake(
        programId = "BTECH_CSE",
        institutionId = "INST-A",
        programName = "B.Tech Computer Science & Engineering",
        programLevel = "UG",
        approvedIntake = 60,
        maxSupernumeraryNri = 3,
        maxSupernumeraryFnOci = 9,
        maxSupernumeraryTfw = 3,
        maxPmsss = 6
    )

    private val ece = ProgramIntake(
        programId = "BTECH_ECE",
        institutionId = "INST-A",
        programName = "B.Tech Electronics & Communication",
        programLevel = "UG",
        approvedIntake = 60,
        maxSupernumeraryNri = 3,
        maxSupernumeraryFnOci = 9,
        maxSupernumeraryTfw = 3,
        maxPmsss = 6
    )

    private fun context(
        existingIds: Set<String> = emptySet(),
        regular: Int = 0,
        supernumerary: Int = 0
    ) = CsvValidationContext(
        programs = listOf(cse, ece),
        existingApaarIds = existingIds,
        existingRegularCounts = mapOf("BTECH_CSE" to regular),
        existingSupernumeraryCounts = mapOf("BTECH_CSE" to supernumerary),
        existingNriCounts = mapOf("BTECH_CSE" to 0),
        existingOciFnCounts = mapOf("BTECH_CSE" to 0),
        existingTfwCounts = mapOf("BTECH_CSE" to 0),
        existingPmsssCounts = mapOf("BTECH_CSE" to 0)
    )

    private val header = "APAAR_ID,Full_Name,DOB,Gender,Roll_No,Program_Code,Category,Nationality,Doc_Number"

    // ------------------------------------------------------------- parsing

    @Test
    fun parsesQuotedFieldsAndEmbeddedCommas() {
        val (head, rows) = CsvParser.parse("a,b\n\"x,y\",z")
        assertEquals(listOf("a", "b"), head)
        assertEquals(1, rows.size)
        assertEquals(listOf("x,y", "z"), rows.first())
    }

    @Test
    fun unescapesDoubledQuotes() {
        val (_, rows) = CsvParser.parse("a,b\n\"say \"\"hi\"\"\",z")
        assertEquals("say \"hi\"", rows.first().first())
    }

    @Test
    fun stripsAByteOrderMark() {
        val (head, _) = CsvParser.parse("\uFEFFAPAAR_ID,Full_Name")
        assertEquals("APAAR_ID", head.first())
    }

    @Test
    fun handlesCarriageReturnLineEndings() {
        val (_, rows) = CsvParser.parse("a,b\r\nc,d\r\n")
        assertEquals(1, rows.size)
        assertEquals(listOf("c", "d"), rows.first())
    }

    // ----------------------------------------------------------- validation

    @Test
    fun rejectsAFileWithoutTheMandatoryColumns() {
        val report = CsvIngestionValidator.validate("foo,bar\n1,2", context())
        assertEquals(4, report.headerErrors.size)
        assertTrue(report.headerErrors.any { it.contains("APAAR_ID") })
        assertTrue(report.isEmpty)
    }

    @Test
    fun acceptsThePublishedTemplate() {
        val report = CsvIngestionValidator.validate(CsvIngestionValidator.TEMPLATE, context())
        assertTrue(report.headerErrors.toString(), report.headerErrors.isEmpty())
        assertEquals(4, report.totalRows)
        assertEquals(4, report.validRows)
        assertEquals(0, report.criticalRows)
    }

    @Test
    fun mapsHeaderAliasesOntoTheCanonicalSchema() {
        val csv = "apaar_id,student_name,dob,sex,rollno,program,quota,nationality,passport_no\n" +
            "984210357890,Aakash Verma,2004-03-12,M,CSE-24-010,BTECH_CSE,REGULAR_MERIT,Indian,"
        val report = CsvIngestionValidator.validate(csv, context())
        assertTrue(report.headerErrors.toString(), report.headerErrors.isEmpty())
        assertEquals(1, report.validRows)
    }

    @Test
    fun flagsAnIdentifierThatIsAlreadyInTheRegistry() {
        val csv = "$header\n984210357890,Aakash Verma,2004-03-12,M,CSE-24-010,BTECH_CSE,REGULAR_MERIT,Indian,"
        val report = CsvIngestionValidator.validate(csv, context(existingIds = setOf("984210357890")))
        assertEquals(1, report.criticalRows)
        assertEquals(1, report.duplicateRows)
        assertTrue(report.rows.first().issues.any { it.code == "DUPLICATE" })
    }

    @Test
    fun flagsAnIdentifierDuplicatedInsideTheSameBatch() {
        val csv = "$header\n" +
            "984210357890,Aakash Verma,2004-03-12,M,CSE-24-010,BTECH_CSE,REGULAR_MERIT,Indian,\n" +
            "984210357890,Aakash Verma,2004-03-12,M,CSE-24-011,BTECH_CSE,REGULAR_MERIT,Indian,"
        val report = CsvIngestionValidator.validate(csv, context())
        assertEquals(2, report.criticalRows)
        assertEquals(2, report.duplicateRows)
    }

    @Test
    fun flagsAnUnknownProgrammeCode() {
        val csv = "$header\n984210357890,Aakash Verma,2004-03-12,M,CSE-24-010,BTECH_CIVIL,REGULAR_MERIT,Indian,"
        val report = CsvIngestionValidator.validate(csv, context())
        assertEquals(1, report.criticalRows)
        assertTrue(report.rows.first().issues.any { it.code == "UNKNOWN_PROGRAM" })
        assertTrue(report.unknownPrograms.contains("BTECH_CIVIL"))
    }

    @Test
    fun flagsAnUnknownQuotaCategory() {
        val csv = "$header\n984210357890,Aakash Verma,2004-03-12,M,CSE-24-010,BTECH_CSE,VIP_SEAT,Indian,"
        val report = CsvIngestionValidator.validate(csv, context())
        assertTrue(report.rows.first().issues.any { it.code == "INVALID_CATEGORY" })
    }

    @Test
    fun flagsAnImpossibleDateOfBirth() {
        val csv = "$header\n984210357890,Aakash Verma,2004-02-31,M,CSE-24-010,BTECH_CSE,REGULAR_MERIT,Indian,"
        val report = CsvIngestionValidator.validate(csv, context())
        assertTrue(report.rows.first().issues.any { it.code == "INVALID_DOB" })
    }

    @Test
    fun normalisesAlternativeDateFormats() {
        val csv = "$header\n984210357890,Aakash Verma,12/03/2004,M,CSE-24-010,BTECH_CSE,REGULAR_MERIT,Indian,"
        val report = CsvIngestionValidator.validate(csv, context())
        assertEquals("2004-03-12", report.rows.first().dob)
        assertEquals(1, report.validRows)
    }

    @Test
    fun warnsWhenARegularSeatIsDeclaredAgainstANonIndianNationality() {
        val csv = "$header\n984210357890,Aakash Verma,2004-03-12,M,CSE-24-010,BTECH_CSE,REGULAR_MERIT,Nepal,"
        val report = CsvIngestionValidator.validate(csv, context())
        assertEquals(1, report.warningRows)
        assertEquals(1, report.validRows)
        assertTrue(report.rows.first().issues.any { it.code == "CATEGORY_MISMATCH" })
    }

    @Test
    fun warnsWhenAForeignNationalHasNoDocumentNumber() {
        val csv = "$header\n984210357890,Zaid Abdullah,2003-07-15,M,CSE-24-012,BTECH_CSE,SUPERNUMERARY_FN,Oman,"
        val report = CsvIngestionValidator.validate(csv, context())
        assertTrue(report.rows.first().issues.any { it.code == "MISSING_PASSPORT" })
        assertEquals(1, report.validRows)
    }

    @Test
    fun warnsWhenTheLuhnAdvisoryFails() {
        var candidate = "984210357890"
        var attempts = 0
        while (com.edusync.apaar.core.validation.ApaarIdValidator.luhnValid(candidate) && attempts < 12) {
            candidate = candidate.dropLast(1) + ((candidate.last().digitToInt() + 1) % 10).toString()
            attempts++
        }
        val csv = "$header\n$candidate,Aakash Verma,2004-03-12,M,CSE-24-010,BTECH_CSE,REGULAR_MERIT,Indian,"
        val report = CsvIngestionValidator.validate(csv, context())
        assertEquals(1, report.warningRows)
        assertTrue(report.rows.first().issues.any { it.code == "LUHN_ADVISORY" })
        assertEquals(1, report.validRows)
    }

    @Test
    fun projectsTheRegularIntakeImpactOfABatch() {
        val csv = (1..3).joinToString("\n") { index ->
            "98421035789$index,Aakash Verma$index,2004-03-12,M,CSE-24-01$index,BTECH_CSE,REGULAR_MERIT,Indian,"
        }
        val report = CsvIngestionValidator.validate("$header\n$csv", context(regular = 58))
        val impact = report.programImpacts.single()
        assertEquals(58, impact.existingRegular)
        assertEquals(3, impact.incomingRegular)
        assertEquals(61, impact.projectedRegular)
        assertEquals(1, impact.regularOverflow)
        assertTrue(impact.capMessages.any { it.contains("Regular intake breach") })
    }

    @Test
    fun projectsTheSupernumeraryImpactOfABatch() {
        val csv = (1..4).joinToString("\n") { index ->
            "98421035789$index,Aakash Verma$index,2004-03-12,M,CSE-24-01$index,BTECH_CSE,SUPERNUMERARY_NRI,Indian,"
        }
        val report = CsvIngestionValidator.validate("$header\n$csv", context())
        val impact = report.programImpacts.single()
        assertEquals(4, impact.incomingSupernumerary)
        assertTrue(impact.capMessages.any { it.contains("NRI supernumerary ceiling exceeded") })
    }

    @Test
    fun excludesBlockedRowsFromTheCommittedSet() {
        val csv = "$header\n" +
            "984210357890,Aakash Verma,2004-03-12,M,CSE-24-010,BTECH_CSE,REGULAR_MERIT,Indian,\n" +
            "984210357891,Bad Row,not-a-date,M,CSE-24-011,BTECH_CIVIL,REGULAR_MERIT,Indian,"
        val report = CsvIngestionValidator.validate(csv, context())
        assertEquals(1, report.committableRows.size)
        assertEquals("984210357890", report.committableRows.first().apaarId)
    }

    @Test
    fun resolvesTheQuotaBucketForEveryRow() {
        val csv = "$header\n984210357890,Aakash Verma,2004-03-12,M,CSE-24-010,BTECH_CSE,SUPERNUMERARY_TFW,Indian,"
        val report = CsvIngestionValidator.validate(csv, context())
        assertEquals(AdmissionQuota.TFW, report.rows.first().quota)
    }

    @Test
    fun reportsAnEmptyFileWithoutCrashing() {
        val report = CsvIngestionValidator.validate("", context())
        assertTrue(report.headerErrors.isNotEmpty())
        assertTrue(report.isEmpty)
        assertFalse(report.rows.isNotEmpty())
    }
}
