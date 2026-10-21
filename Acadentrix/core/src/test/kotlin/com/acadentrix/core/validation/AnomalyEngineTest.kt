package com.acadentrix.core.validation

import com.acadentrix.core.model.AdmissionQuota
import com.acadentrix.core.model.AnomalySeverity
import com.acadentrix.core.model.AnomalyType
import com.acadentrix.core.model.Gender
import com.acadentrix.core.model.Institution
import com.acadentrix.core.model.InstitutionType
import com.acadentrix.core.model.ProgramIntake
import com.acadentrix.core.model.Student
import com.acadentrix.core.model.VerificationStatus
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Behaviour of the multi-layer regulatory anomaly engine.
 */
class AnomalyEngineTest {

    // ------------------------------------------------------------ fixtures

    private val institutionA = Institution(
        institutionId = "INST-A",
        name = "Alpha Institute of Technology",
        institutionType = InstitutionType.ENGINEERING,
        state = "Karnataka",
        city = "Bengaluru",
        affiliationUniversity = "Visvesvaraya Technological University",
        approvalYear = 2012,
        naacGrade = "A++"
    )

    private val institutionB = Institution(
        institutionId = "INST-B",
        name = "Beta Institute of Technology",
        institutionType = InstitutionType.ENGINEERING,
        state = "Tamil Nadu",
        city = "Chennai",
        affiliationUniversity = "Anna University",
        approvalYear = 2015,
        naacGrade = "A+"
    )

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

    private val cseAtB = cse.copy(institutionId = "INST-B")

    // APAAR identifiers are exactly 12 digits, so the fixture counter has to
    // start below 1_000_000_000_000.
    private var nextApaar = 900_000_000_000L

    private fun student(
        apaarId: String = nextApaar().toString(),
        institutionId: String = "INST-A",
        programId: String = "BTECH_CSE",
        quota: AdmissionQuota = AdmissionQuota.MERIT,
        nationality: String = "Indian",
        passport: String? = null,
        country: String? = null,
        visa: String? = null,
        enrollmentDate: String = "2024-08-01",
        dateOfBirth: String = "2004-01-01",
        studentName: String = "Test Student ${nextApaar() % 1000}",
        rollNo: String = "ROLL-${nextApaar() % 10000}",
        academicYear: String = "2024-25",
        isActive: Boolean = true
    ) = Student(
        recordId = 0,
        apaarId = apaarId,
        studentName = studentName,
        dateOfBirth = dateOfBirth,
        gender = Gender.MALE,
        institutionId = institutionId,
        programId = programId,
        academicYear = academicYear,
        admissionQuota = quota,
        enrollmentDate = enrollmentDate,
        studentInstituteRollNo = rollNo,
        nationality = nationality,
        passportNumber = passport,
        visaValidity = visa,
        countryOfOrigin = country,
        abcAccountId = null,
        verificationStatus = VerificationStatus.PENDING_REVIEW,
        isActive = isActive,
        photoSeed = 1
    )

    private fun nextApaar(): Long {
        nextApaar += 7
        return nextApaar
    }

    private fun snapshot(
        students: List<Student>,
        programs: List<ProgramIntake> = listOf(cse, cseAtB)
    ) = RegistrySnapshot(
        institutions = listOf(institutionA, institutionB),
        programs = programs,
        students = students
    )

    // --------------------------------------------------------------- tests

    @Test
    fun aCleanRegistryProducesNoAnomalies() {
        val students = (1..20).map { student() }
        val anomalies = AnomalyEngine.evaluate(snapshot(students))
        assertTrue(anomalies.toString(), anomalies.isEmpty())
    }

    @Test
    fun flagsAnIdentifierThatFailsTheSyntacticCheck() {
        val broken = student(apaarId = "123456789012")
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(broken)))
        val invalid = anomalies.filter { it.anomalyType == AnomalyType.INVALID_APAAR_FORMAT }
        assertEquals(1, invalid.size)
        assertEquals(AnomalySeverity.CRITICAL, invalid.first().severity)
    }

    @Test
    fun flagsAnIdentifierEnrolledAtTwoInstitutions() {
        val shared = nextApaar().toString()
        val rows = listOf(
            student(apaarId = shared, institutionId = "INST-A"),
            student(apaarId = shared, institutionId = "INST-B")
        )
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        val duplicates = anomalies.filter { it.anomalyType == AnomalyType.DUPLICATE_CROSS_COLLEGE }
        assertEquals(2, duplicates.size)
        assertTrue(duplicates.all { it.severity == AnomalySeverity.CRITICAL })
        assertEquals(setOf("INST-A", "INST-B"), duplicates.map { it.institutionId }.toSet())
    }

    @Test
    fun treatsASupernumeraryDuplicateAsHighRatherThanCritical() {
        val shared = nextApaar().toString()
        val rows = listOf(
            student(apaarId = shared, institutionId = "INST-A", quota = AdmissionQuota.NRI),
            student(apaarId = shared, institutionId = "INST-B", quota = AdmissionQuota.NRI)
        )
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        val duplicates = anomalies.filter { it.anomalyType == AnomalyType.DUPLICATE_CROSS_COLLEGE }
        assertEquals(2, duplicates.size)
        assertTrue(duplicates.all { it.severity == AnomalySeverity.HIGH })
    }

    @Test
    fun ignoresDuplicatesThatAreNotActive() {
        val shared = nextApaar().toString()
        val rows = listOf(
            student(apaarId = shared, institutionId = "INST-A"),
            student(apaarId = shared, institutionId = "INST-B", isActive = false)
        )
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        assertTrue(anomalies.none { it.anomalyType == AnomalyType.DUPLICATE_CROSS_COLLEGE })
    }

    @Test
    fun flagsRegularEnrolmentBeyondTheSanctionedIntake() {
        val rows = (1..65).map { student() }
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        val breaches = anomalies.filter { it.anomalyType == AnomalyType.EXCESS_APPROVED_INTAKE }
        assertEquals(5, breaches.size)
        assertTrue(breaches.all { it.severity == AnomalySeverity.CRITICAL })
    }

    @Test
    fun doesNotFlagEnrolmentExactlyAtTheSanctionedIntake() {
        val rows = (1..60).map { student() }
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        assertTrue(anomalies.none { it.anomalyType == AnomalyType.EXCESS_APPROVED_INTAKE })
    }

    @Test
    fun flagsTheNriSupernumeraryCeiling() {
        val rows = (1..5).map { student(quota = AdmissionQuota.NRI) }
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        val breaches = anomalies.filter { it.anomalyType == AnomalyType.SUPERNUMERARY_BREACH }
        assertEquals(2, breaches.size)
        assertTrue(breaches.all { it.details.contains("NRI") })
        assertTrue(breaches.all { it.severity == AnomalySeverity.WARNING })
    }

    @Test
    fun escalatesToCriticalWhenTheCapIsExceededByMoreThanTwoSeats() {
        val rows = (1..7).map { student(quota = AdmissionQuota.NRI) }
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        val breaches = anomalies.filter { it.anomalyType == AnomalyType.SUPERNUMERARY_BREACH }
        assertEquals(4, breaches.size)
        assertTrue(breaches.all { it.severity == AnomalySeverity.CRITICAL })
    }

    @Test
    fun sharesOneCeilingBetweenOciAndForeignNationals() {
        // The cap is 9; 6 OCI + 5 FN = 11 combined admissions is a breach even
        // though neither bucket individually exceeds the ceiling.
        val rows = (1..6).map { student(quota = AdmissionQuota.OCI, nationality = "OCI") } +
            (1..5).map { student(quota = AdmissionQuota.FN, nationality = "UAE", passport = "P1", country = "UAE", visa = "2026") }
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        val breaches = anomalies.filter { it.anomalyType == AnomalyType.SUPERNUMERARY_BREACH }
        assertEquals(2, breaches.size)
        assertTrue(breaches.all { it.details.contains("OCI") })
    }

    @Test
    fun flagsTheTuitionFeeWaiverCeiling() {
        val rows = (1..4).map { student(quota = AdmissionQuota.TFW) }
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        val breaches = anomalies.filter { it.anomalyType == AnomalyType.SUPERNUMERARY_BREACH }
        assertEquals(1, breaches.size)
        assertTrue(breaches.first().details.contains("Tuition Fee Waiver"))
    }

    @Test
    fun flagsMissingDocumentationForForeignNationals() {
        val row = student(quota = AdmissionQuota.FN, nationality = "Qatar")
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        val inconsistencies = anomalies.filter { it.anomalyType == AnomalyType.INCONSISTENT_CATEGORY }
        assertEquals(1, inconsistencies.size)
        assertTrue(inconsistencies.first().details.contains("passport"))
        assertTrue(inconsistencies.first().details.contains("country of origin"))
        assertTrue(inconsistencies.first().details.contains("visa"))
    }

    @Test
    fun flagsARegularSeatAgainstANonIndianNationality() {
        val row = student(quota = AdmissionQuota.MERIT, nationality = "Nepal")
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        val inconsistencies = anomalies.filter { it.anomalyType == AnomalyType.INCONSISTENT_CATEGORY }
        assertEquals(1, inconsistencies.size)
        assertTrue(inconsistencies.first().details.contains("non-Indian nationality"))
    }

    @Test
    fun flagsEnrolmentInAProgrammeTheInstitutionCannotOffer() {
        val row = student(programId = "BTECH_CIVIL")
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        val unsanctioned = anomalies.filter { it.anomalyType == AnomalyType.UNSANCTIONED_PROGRAM }
        assertEquals(1, unsanctioned.size)
        assertEquals(AnomalySeverity.CRITICAL, unsanctioned.first().severity)
    }

    @Test
    fun buildsUtilisationSnapshotsForEveryProgramme() {
        val rows = (1..30).map { student() } +
            (1..2).map { student(quota = AdmissionQuota.NRI) } +
            (1..3).map { student(quota = AdmissionQuota.TFW) }
        val snapshots = AnomalyEngine.buildSnapshots(snapshot(rows))
        assertEquals(2, snapshots.size)
        val alpha = snapshots.first { it.program.institutionId == "INST-A" }
        assertEquals(30, alpha.regularEnrolled)
        assertEquals(5, alpha.supernumeraryEnrolled)
        assertEquals(35, alpha.totalEnrolled)
        assertEquals(2, alpha.nriEnrolled)
        assertEquals(3, alpha.tfwEnrolled)
        assertEquals(0, alpha.pmsssEnrolled)
    }

    @Test
    fun reportsOverflowSeparatelyForEveryQuotaBand() {
        val rows = (1..65).map { student() } +
            (1..5).map { student(quota = AdmissionQuota.NRI) }
        val snapshots = AnomalyEngine.buildSnapshots(snapshot(rows))
        val alpha = snapshots.first { it.program.institutionId == "INST-A" }
        assertEquals(5, alpha.regularOverflow)
        assertEquals(2, alpha.nriOverflow)
        assertEquals(0, alpha.tfwOverflow)
        assertEquals(0, alpha.ociFnOverflow)
        assertEquals(0, alpha.pmsssOverflow)
        assertTrue(alpha.hasBreach)
    }

    // ------------------------------------------------- same-institution duplicates

    @Test
    fun flagsTheSameApaarTwiceInsideOneInstitution() {
        val shared = nextApaar().toString()
        val rows = listOf(
            student(apaarId = shared, institutionId = "INST-A"),
            student(apaarId = shared, institutionId = "INST-A")
        )
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        val duplicates = anomalies.filter { it.anomalyType == AnomalyType.DUPLICATE_SAME_INSTITUTION }
        assertEquals(2, duplicates.size)
        assertTrue(duplicates.all { it.institutionId == "INST-A" })
        assertTrue(duplicates.all { it.severity == AnomalySeverity.HIGH })
    }

    @Test
    fun escalatesToCriticalWhenAnInstitutionAdmitstheSameStudentTwiceInDifferentProgrammes() {
        val shared = nextApaar().toString()
        val rows = listOf(
            student(apaarId = shared, institutionId = "INST-A", programId = "BTECH_CSE"),
            student(apaarId = shared, institutionId = "INST-A", programId = "BTECH_ECE")
        )
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        val duplicates = anomalies.filter { it.anomalyType == AnomalyType.DUPLICATE_SAME_INSTITUTION }
        assertEquals(2, duplicates.size)
        assertTrue(duplicates.all { it.severity == AnomalySeverity.CRITICAL })
        assertTrue(duplicates.first().details.contains("different programmes"))
    }

    @Test
    fun ignoresASecondInactiveRowForTheSameStudentInTheSameInstitution() {
        val shared = nextApaar().toString()
        val rows = listOf(
            student(apaarId = shared, institutionId = "INST-A"),
            student(apaarId = shared, institutionId = "INST-A", isActive = false)
        )
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        assertTrue(anomalies.none { it.anomalyType == AnomalyType.DUPLICATE_SAME_INSTITUTION })
    }

    // -------------------------------------------------------- duplicate roll numbers

    @Test
    fun flagsTwoDifferentStudentsSharingAnInstituteRollNumber() {
        val rows = listOf(
            student(rollNo = "CSE-24-001"),
            student(rollNo = "CSE-24-001")
        )
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        val clashes = anomalies.filter { it.anomalyType == AnomalyType.DUPLICATE_ROLL_NUMBER }
        assertEquals(2, clashes.size)
        assertTrue(clashes.all { it.severity == AnomalySeverity.HIGH })
        assertTrue(clashes.first().details.contains("CSE-24-001"))
    }

    @Test
    fun matchesRollNumbersRegardlessOfCase() {
        val rows = listOf(
            student(rollNo = "CSE-24-001"),
            student(rollNo = "cse-24-001")
        )
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        assertTrue(anomalies.any { it.anomalyType == AnomalyType.DUPLICATE_ROLL_NUMBER })
    }

    @Test
    fun doesNotFlagARollNumberReusedByTheSameStudentInAnotherProgramme() {
        val shared = nextApaar().toString()
        val rows = listOf(
            student(apaarId = shared, rollNo = "CSE-24-002"),
            student(apaarId = shared, rollNo = "CSE-24-002", programId = "BTECH_ECE")
        )
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        assertTrue(anomalies.none { it.anomalyType == AnomalyType.DUPLICATE_ROLL_NUMBER })
    }

    @Test
    fun doesNotFlagTheSameRollNumberAtTwoDifferentInstitutions() {
        val rows = listOf(
            student(institutionId = "INST-A", rollNo = "CSE-24-003"),
            student(institutionId = "INST-B", rollNo = "CSE-24-003")
        )
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        assertTrue(anomalies.none { it.anomalyType == AnomalyType.DUPLICATE_ROLL_NUMBER })
    }

    // ----------------------------------------------------------- impossible dates

    @Test
    fun flagsAnEnrolmentDateBeforeTheDateOfBirth() {
        val row = student(dateOfBirth = "2004-01-01", enrollmentDate = "2003-08-01")
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        val impossible = anomalies.filter { it.anomalyType == AnomalyType.IMPOSSIBLE_DATE }
        assertEquals(1, impossible.size)
        assertEquals(AnomalySeverity.CRITICAL, impossible.first().severity)
        assertTrue(impossible.first().details.contains("precedes"))
    }

    @Test
    fun flagsADateOfBirthInTheFuture() {
        val row = student(dateOfBirth = "2099-01-01", enrollmentDate = "2024-08-01")
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        val impossible = anomalies.filter { it.anomalyType == AnomalyType.IMPOSSIBLE_DATE }
        assertEquals(1, impossible.size)
        assertTrue(impossible.first().details.contains("future"))
    }

    @Test
    fun flagsAnEnrolmentDateInTheFuture() {
        val row = student(dateOfBirth = "2004-01-01", enrollmentDate = "2099-08-01")
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        val impossible = anomalies.filter { it.anomalyType == AnomalyType.IMPOSSIBLE_DATE }
        assertEquals(1, impossible.size)
        assertTrue(impossible.first().details.contains("future"))
    }

    @Test
    fun flagsADateThatIsNotACalendarDay() {
        val row = student(dateOfBirth = "2004-02-31", enrollmentDate = "2024-08-01")
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        val impossible = anomalies.filter { it.anomalyType == AnomalyType.IMPOSSIBLE_DATE }
        assertEquals(1, impossible.size)
        assertTrue(impossible.first().details.contains("not a valid calendar date"))
    }

    @Test
    fun flagsAnUnreadableDate() {
        val row = student(dateOfBirth = "not-a-date", enrollmentDate = "2024-08-01")
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        val impossible = anomalies.filter { it.anomalyType == AnomalyType.IMPOSSIBLE_DATE }
        assertEquals(1, impossible.size)
    }

    @Test
    fun flagsAStudentWhoIsImplausiblyYoungToEnrol() {
        val row = student(dateOfBirth = "2015-01-01", enrollmentDate = "2024-08-01")
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        val impossible = anomalies.filter { it.anomalyType == AnomalyType.IMPOSSIBLE_DATE }
        assertEquals(1, impossible.size)
        assertEquals(AnomalySeverity.HIGH, impossible.first().severity)
    }

    @Test
    fun acceptsAPlausibleAgeAndARealLeapDay() {
        val rows = listOf(
            student(dateOfBirth = "2004-01-01", enrollmentDate = "2024-08-01"),
            student(dateOfBirth = "2004-02-29", enrollmentDate = "2024-08-01")
        )
        val anomalies = AnomalyEngine.evaluate(snapshot(rows))
        assertTrue(anomalies.none { it.anomalyType == AnomalyType.IMPOSSIBLE_DATE })
    }

    @Test
    fun readsDatesWrittenInDayFirstOrder() {
        val row = student(dateOfBirth = "01-01-2004", enrollmentDate = "01-08-2024")
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        assertTrue(anomalies.none { it.anomalyType == AnomalyType.IMPOSSIBLE_DATE })
    }

    // -------------------------------------------------------- missing mandatory fields

    @Test
    fun flagsEveryMissingMandatoryFieldInOneFinding() {
        val row = student(
            studentName = "  ",
            dateOfBirth = "",
            rollNo = "",
            academicYear = ""
        )
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        val missing = anomalies.filter { it.anomalyType == AnomalyType.MISSING_REQUIRED_FIELD }
        assertEquals(1, missing.size)
        assertEquals(AnomalySeverity.HIGH, missing.first().severity)
        val details = missing.first().details
        assertTrue(details.contains("student name"))
        assertTrue(details.contains("date of birth"))
        assertTrue(details.contains("institute roll number"))
        assertTrue(details.contains("academic year"))
    }

    @Test
    fun doesNotFlagACompleteRecord() {
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(student())))
        assertTrue(anomalies.none { it.anomalyType == AnomalyType.MISSING_REQUIRED_FIELD })
    }

    // ------------------------------------------------ quota / nationality conflicts

    @Test
    fun flagsAForeignNationalSeatHeldByAnIndianCitizen() {
        val row = student(
            quota = AdmissionQuota.FN,
            nationality = "Indian",
            passport = "P123456",
            country = "India",
            visa = "31-12-2027"
        )
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        val conflicts = anomalies.filter { it.anomalyType == AnomalyType.INCONSISTENT_CATEGORY }
        assertEquals(1, conflicts.size)
        assertEquals(AnomalySeverity.CRITICAL, conflicts.first().severity)
        assertTrue(conflicts.first().details.contains("Indian citizen"))
    }

    @Test
    fun flagsAnNriSeatHeldByAForeignNational() {
        val row = student(quota = AdmissionQuota.NRI, nationality = "Germany")
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        val conflicts = anomalies.filter { it.anomalyType == AnomalyType.INCONSISTENT_CATEGORY }
        assertEquals(1, conflicts.size)
        assertTrue(conflicts.first().details.contains("NRI"))
        assertTrue(conflicts.first().details.contains("Foreign National bucket"))
    }

    @Test
    fun acceptsAnNriSeatHeldByAnIndianNational() {
        val row = student(quota = AdmissionQuota.NRI, nationality = "Indian")
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        assertTrue(anomalies.none { it.anomalyType == AnomalyType.INCONSISTENT_CATEGORY })
    }

    @Test
    fun flagsTuitionFeeWaiverGrantedToAForeignNational() {
        val row = student(quota = AdmissionQuota.TFW, nationality = "Nepal")
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        val conflicts = anomalies.filter { it.anomalyType == AnomalyType.INCONSISTENT_CATEGORY }
        assertEquals(1, conflicts.size)
        assertTrue(conflicts.first().details.contains("Tuition Fee Waiver"))
    }

    @Test
    fun flagsPmsssGrantedToAForeignNational() {
        val row = student(quota = AdmissionQuota.PMSSS, nationality = "Nepal")
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        val conflicts = anomalies.filter { it.anomalyType == AnomalyType.INCONSISTENT_CATEGORY }
        assertEquals(1, conflicts.size)
        assertTrue(conflicts.first().details.contains("PMSSS"))
    }

    @Test
    fun acceptsOciCitizenshipDeclaredAsIndian() {
        val row = student(quota = AdmissionQuota.OCI, nationality = "Indian")
        val anomalies = AnomalyEngine.evaluate(snapshot(listOf(row)))
        assertTrue(anomalies.none { it.anomalyType == AnomalyType.INCONSISTENT_CATEGORY })
    }
}
