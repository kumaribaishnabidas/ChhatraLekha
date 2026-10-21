package com.acadentrix.app.core.validation

import com.acadentrix.app.core.model.AdmissionQuota
import com.acadentrix.app.core.model.AnomalySeverity
import com.acadentrix.app.core.model.AnomalyType
import com.acadentrix.app.core.model.Gender
import com.acadentrix.app.core.model.Institution
import com.acadentrix.app.core.model.InstitutionType
import com.acadentrix.app.core.model.ProgramIntake
import com.acadentrix.app.core.model.Student
import com.acadentrix.app.core.model.VerificationStatus
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
        isActive: Boolean = true
    ) = Student(
        recordId = 0,
        apaarId = apaarId,
        studentName = "Test Student ${nextApaar() % 1000}",
        dateOfBirth = "2004-01-01",
        gender = Gender.MALE,
        institutionId = institutionId,
        programId = programId,
        academicYear = "2024-25",
        admissionQuota = quota,
        enrollmentDate = enrollmentDate,
        studentInstituteRollNo = "ROLL-${nextApaar() % 10000}",
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
}
