package com.edusync.apaar.data.repository

import com.edusync.apaar.core.csv.CsvStudentRow
import com.edusync.apaar.core.model.AdmissionQuota
import com.edusync.apaar.core.model.Anomaly
import com.edusync.apaar.core.model.AnomalySeverity
import com.edusync.apaar.core.model.AnomalyType
import com.edusync.apaar.core.model.AuditEntry
import com.edusync.apaar.core.model.Gender
import com.edusync.apaar.core.model.Institution
import com.edusync.apaar.core.model.InstitutionType
import com.edusync.apaar.core.model.ProgramIntake
import com.edusync.apaar.core.model.Student
import com.edusync.apaar.core.model.VerificationStatus
import com.edusync.apaar.core.validation.AnomalyEngine
import com.edusync.apaar.core.validation.RegistrySnapshot
import com.edusync.apaar.data.local.ApaarDatabase
import com.edusync.apaar.data.local.SeedData
import com.edusync.apaar.data.local.entity.AnomalyRecordEntity
import com.edusync.apaar.data.local.entity.AuditLogEntity
import com.edusync.apaar.data.local.entity.InstitutionEntity
import com.edusync.apaar.data.local.entity.ProgramIntakeEntity
import com.edusync.apaar.data.local.entity.StudentEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.map

/**
 * Mediates every read and write against the local APAAR registry and keeps the
 * regulatory state (students, anomalies, audit trail) consistent.
 */
class ApaarRepository(private val database: ApaarDatabase) {

    private val institutionDao = database.institutionDao()
    private val programDao = database.programIntakeDao()
    private val studentDao = database.studentDao()
    private val anomalyDao = database.anomalyDao()
    private val auditDao = database.auditLogDao()

    // ------------------------------------------------------------ read model

    val institutions: Flow<List<Institution>> = institutionDao.observeAll().map { rows ->
        rows.map { it.toDomain() }
    }

    val programs: Flow<List<ProgramIntake>> = programDao.observeAll().map { rows ->
        rows.map { it.toDomain() }
    }

    val students: Flow<List<Student>> = studentDao.observeAll().map { rows ->
        rows.map { it.toDomain() }
    }

    val auditTrail: Flow<List<AuditEntry>> = auditDao.observeRecent(300).map { rows ->
        rows.map { it.toDomain() }
    }

    /** The whole registry as one immutable snapshot, ready for the detection engine. */
    val registry: Flow<RegistrySnapshot> = combine(
        institutions,
        programs,
        students
    ) { institutions, programs, students ->
        RegistrySnapshot(institutions, programs, students)
    }

    // --------------------------------------------------------------- seeding

    /**
     * Populates the registry with the seeded pan-India dataset on first launch
     * and recomputes the anomaly state.
     */
    suspend fun ensureSeeded(): Boolean {
        if (institutionDao.count() > 0) return false
        institutionDao.insertAll(SeedData.institutions)
        programDao.insertAll(SeedData.programs())
        studentDao.insertAll(SeedData.students())
        auditDao.insert(
            AuditLogEntity(
                timestamp = System.currentTimeMillis(),
                actor = "AICTE Central Registry",
                action = "INITIAL_SEED",
                subject = "National APAAR Registry",
                details = "Loaded ${SeedData.institutions.size} institutions and ${SeedData.students().size} enrolment records.",
                category = "SYSTEM"
            )
        )
        recomputeAnomalies()
        return true
    }

    // ------------------------------------------------------------ anomalies

    /**
     * Re-runs the four-layer detection engine, persists the findings and refreshes
     * the verification status of every affected student.
     */
    suspend fun recomputeAnomalies(): List<Anomaly> {
        val snapshot = RegistrySnapshot(
            institutions = institutionDao.getAll().map { it.toDomain() },
            programs = programDao.getAll().map { it.toDomain() },
            students = studentDao.getAll().map { it.toDomain() }
        )
        val detected = AnomalyEngine.evaluate(snapshot)
        val timestamp = System.currentTimeMillis()

        anomalyDao.clear()
        anomalyDao.insertAll(
            detected.map { anomaly ->
                AnomalyRecordEntity(
                    studentApaarId = anomaly.studentApaarId,
                    institutionId = anomaly.institutionId,
                    programId = anomaly.programId,
                    anomalyType = anomaly.anomalyType.name,
                    severity = anomaly.severity.name,
                    details = anomaly.details,
                    timestamp = timestamp
                )
            }
        )

        // Reflect the detection result on the student register.
        val flaggedApaar = detected
            .filter { it.severity == AnomalySeverity.CRITICAL || it.severity == AnomalySeverity.HIGH }
            .map { it.studentApaarId }
            .toSet()
        studentDao.getAll().forEach { entity ->
            val status = when {
                entity.apaarId in flaggedApaar -> VerificationStatus.FLAGGED_ANOMALY
                entity.verificationStatus == VerificationStatus.PENDING_REVIEW.name ->
                    VerificationStatus.VERIFIED
                else -> VerificationStatus.from(entity.verificationStatus)
            }
            if (status.name != entity.verificationStatus) {
                studentDao.updateVerificationStatus(entity.recordId, status.name)
            }
        }

        return detected.mapIndexed { index, anomaly ->
            Anomaly(
                anomalyId = index.toLong(),
                studentApaarId = anomaly.studentApaarId,
                institutionId = anomaly.institutionId,
                programId = anomaly.programId,
                anomalyType = anomaly.anomalyType,
                severity = anomaly.severity,
                details = anomaly.details,
                timestamp = timestamp
            )
        }
    }

    // --------------------------------------------------------------- writes

    /**
     * Commits a validated CSV batch to the central repository.
     */
    suspend fun commitBatch(
        rows: List<CsvStudentRow>,
        institutionId: String,
        actor: String,
        academicYear: String
    ): BatchCommitResult {
        val committable = rows.filter { row ->
            row.issues.none { it.severity == com.edusync.apaar.core.csv.RowIssueSeverity.CRITICAL }
        }
        val entities = committable.map { row ->
            StudentEntity(
                apaarId = row.apaarId,
                studentName = row.fullName,
                dateOfBirth = row.dob,
                gender = (Gender.fromCode(row.gender) ?: Gender.OTHER).name,
                institutionId = institutionId,
                programId = row.programCode,
                academicYear = academicYear,
                admissionQuota = (row.quota ?: AdmissionQuota.MERIT).name,
                enrollmentDate = today(),
                studentInstituteRollNo = row.rollNo.ifBlank { "AUTO-${row.apaarId.takeLast(4)}" },
                nationality = row.nationality.ifBlank { "Indian" },
                passportNumber = row.docNumber.ifBlank { null },
                visaValidity = null,
                countryOfOrigin = null,
                abcAccountId = null,
                verificationStatus = VerificationStatus.PENDING_REVIEW.name,
                isActive = true,
                photoSeed = row.apaarId.sumOf { it.digitToInt() } % 6
            )
        }
        val inserted = studentDao.insertAll(entities).count { it > 0 }
        val anomalies = recomputeAnomalies()
        auditDao.insert(
            AuditLogEntity(
                timestamp = System.currentTimeMillis(),
                actor = actor,
                action = "BATCH_COMMIT",
                subject = institutionId,
                details = "Committed $inserted of ${rows.size} CSV rows; ${anomalies.size} anomaly record(s) in force.",
                category = "ADMISSIONS"
            )
        )
        return BatchCommitResult(
            committed = inserted,
            skipped = rows.size - inserted,
            totalAnomalies = anomalies.size
        )
    }

    /**
     * Manually onboards a single student.
     */
    suspend fun addStudent(
        student: Student,
        actor: String
    ): BatchCommitResult {
        val id = studentDao.insert(
            student.copy(recordId = 0).toEntity()
        )
        val anomalies = recomputeAnomalies()
        auditDao.insert(
            AuditLogEntity(
                timestamp = System.currentTimeMillis(),
                actor = actor,
                action = "MANUAL_ADMISSION",
                subject = student.apaarId,
                details = "Onboarded ${student.studentName} into ${student.programId} at ${student.institutionId}.",
                category = "ADMISSIONS"
            )
        )
        return BatchCommitResult(
            committed = if (id > 0) 1 else 0,
            skipped = if (id > 0) 0 else 1,
            totalAnomalies = anomalies.size
        )
    }

    /**
     * Records a verification attempt in the immutable audit trail.
     */
    suspend fun recordVerification(
        actor: String,
        apaarId: String,
        outcome: String,
        details: String
    ) {
        auditDao.insert(
            AuditLogEntity(
                timestamp = System.currentTimeMillis(),
                actor = actor,
                action = "CREDENTIAL_VERIFICATION",
                subject = apaarId,
                details = details,
                category = outcome
            )
        )
    }

    suspend fun logAudit(actor: String, action: String, subject: String, details: String, category: String) {
        auditDao.insert(
            AuditLogEntity(
                timestamp = System.currentTimeMillis(),
                actor = actor,
                action = action,
                subject = subject,
                details = details,
                category = category
            )
        )
    }

    // ------------------------------------------------------------- lookups

    suspend fun findByApaarId(apaarId: String): List<Student> =
        studentDao.getActiveByApaarId(apaarId.filter { it.isDigit() }).map { it.toDomain() }

    suspend fun findByRollNo(rollNo: String): Student? =
        studentDao.getByRollNo(rollNo.trim())?.toDomain()

    suspend fun studentByRecordId(recordId: Long): Student? =
        studentDao.getByRecordId(recordId)?.toDomain()

    suspend fun programsOf(institutionId: String): List<ProgramIntake> =
        programDao.getByInstitution(institutionId).map { it.toDomain() }

    private fun today(): String = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.ENGLISH)
        .format(java.util.Date())
}

data class BatchCommitResult(
    val committed: Int,
    val skipped: Int,
    val totalAnomalies: Int
)

// ------------------------------------------------------------------ mappers

fun InstitutionEntity.toDomain() = Institution(
    institutionId = institutionId,
    name = name,
    institutionType = InstitutionType.from(institutionType),
    state = state,
    city = city,
    affiliationUniversity = affiliationUniversity,
    approvalYear = approvalYear,
    naacGrade = naacGrade
)

fun ProgramIntakeEntity.toDomain() = ProgramIntake(
    programId = programId,
    institutionId = institutionId,
    programName = programName,
    programLevel = programLevel,
    approvedIntake = approvedIntake,
    maxSupernumeraryNri = maxSupernumeraryNri,
    maxSupernumeraryFnOci = maxSupernumeraryFnOci,
    maxSupernumeraryTfw = maxSupernumeraryTfw,
    maxPmsss = maxPmsss
)

fun StudentEntity.toDomain() = Student(
    recordId = recordId,
    apaarId = apaarId,
    studentName = studentName,
    dateOfBirth = dateOfBirth,
    gender = Gender.entries.firstOrNull { it.name == gender } ?: Gender.OTHER,
    institutionId = institutionId,
    programId = programId,
    academicYear = academicYear,
    admissionQuota = AdmissionQuota.entries.firstOrNull { it.name == admissionQuota } ?: AdmissionQuota.MERIT,
    enrollmentDate = enrollmentDate,
    studentInstituteRollNo = studentInstituteRollNo,
    nationality = nationality,
    passportNumber = passportNumber,
    visaValidity = visaValidity,
    countryOfOrigin = countryOfOrigin,
    abcAccountId = abcAccountId,
    verificationStatus = VerificationStatus.from(verificationStatus),
    isActive = isActive,
    photoSeed = photoSeed
)

fun Student.toEntity() = StudentEntity(
    recordId = recordId,
    apaarId = apaarId,
    studentName = studentName,
    dateOfBirth = dateOfBirth,
    gender = gender.name,
    institutionId = institutionId,
    programId = programId,
    academicYear = academicYear,
    admissionQuota = admissionQuota.name,
    enrollmentDate = enrollmentDate,
    studentInstituteRollNo = studentInstituteRollNo,
    nationality = nationality,
    passportNumber = passportNumber,
    visaValidity = visaValidity,
    countryOfOrigin = countryOfOrigin,
    abcAccountId = abcAccountId,
    verificationStatus = verificationStatus.name,
    isActive = isActive,
    photoSeed = photoSeed
)

fun AnomalyRecordEntity.toDomain() = Anomaly(
    anomalyId = anomalyId,
    studentApaarId = studentApaarId,
    institutionId = institutionId,
    programId = programId,
    anomalyType = AnomalyType.from(anomalyType) ?: AnomalyType.INCONSISTENT_CATEGORY,
    severity = AnomalySeverity.from(severity),
    details = details,
    timestamp = timestamp,
    resolved = resolved
)

fun AuditLogEntity.toDomain() = AuditEntry(
    logId = logId,
    timestamp = timestamp,
    actor = actor,
    action = action,
    subject = subject,
    details = details,
    category = category
)
