package com.acadentrix.app.data.repository

import com.acadentrix.core.csv.CsvStudentRow
import com.acadentrix.core.model.AdmissionQuota
import com.acadentrix.core.model.Anomaly
import com.acadentrix.core.model.AnomalySeverity
import com.acadentrix.core.model.AnomalyType
import com.acadentrix.core.model.AuditEntry
import com.acadentrix.core.model.Gender
import com.acadentrix.core.model.Institution
import com.acadentrix.core.model.InstitutionType
import com.acadentrix.core.model.ProgramIntake
import com.acadentrix.core.model.Student
import com.acadentrix.core.model.VerificationStatus
import com.acadentrix.core.validation.AnomalyEngine
import com.acadentrix.core.validation.RegistrySnapshot
import com.acadentrix.app.data.local.ApaarDatabase
import com.acadentrix.app.data.local.SeedData
import com.acadentrix.app.data.local.entity.AnomalyRecordEntity
import com.acadentrix.app.data.local.entity.AuditLogEntity
import com.acadentrix.app.data.local.entity.InstitutionEntity
import com.acadentrix.app.data.local.entity.ProgramIntakeEntity
import com.acadentrix.app.data.local.entity.StudentEntity
import com.acadentrix.core.network.ChhatraLekhaApiClient
import com.acadentrix.core.network.NetworkResult
import com.acadentrix.core.network.RemoteStudentDto
import com.acadentrix.core.network.RemoteTokenVerification
import com.acadentrix.core.network.SyncManager
import com.acadentrix.core.network.SyncSummary
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext

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
            row.issues.none { it.severity == com.acadentrix.core.csv.RowIssueSeverity.CRITICAL }
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

    private val apiClient = ChhatraLekhaApiClient()
    private val syncManager = SyncManager(apiClient)

    /**
     * Synchronizes local Room database with the remote ChhatraLekha FastAPI server.
     * Keeps Room as the authoritative local persistence layer and gracefully
     * handles offline mode and conflicts.
     */
    suspend fun syncWithBackend(
        baseUrl: String = ChhatraLekhaApiClient.DEFAULT_BASE_URL,
        authToken: String? = null
    ): SyncSummary = withContext(Dispatchers.IO) {
        val localEntities = studentDao.getAll()
        val localDtos = localEntities.map { entity ->
            RemoteStudentDto(
                recordId = entity.recordId.toString(),
                apaarId = entity.apaarId,
                studentName = entity.studentName,
                dateOfBirth = entity.dateOfBirth,
                gender = entity.gender,
                institutionId = entity.institutionId,
                programId = entity.programId,
                academicYear = entity.academicYear,
                admissionQuota = entity.admissionQuota,
                enrollmentDate = entity.enrollmentDate,
                studentInstituteRollNo = entity.studentInstituteRollNo,
                nationality = entity.nationality,
                passportNumber = entity.passportNumber,
                visaValidity = entity.visaValidity,
                countryOfOrigin = entity.countryOfOrigin,
                verificationStatus = entity.verificationStatus,
                isActive = entity.isActive
            )
        }

        val summary = syncManager.performSync(
            baseUrl = baseUrl,
            authToken = authToken,
            localStudents = localDtos
        )

        // If records were pulled, insert non-duplicates into Room
        if (!summary.isOffline && summary.pulledCount > 0) {
            val remoteResult = apiClient.fetchStudents(authToken, limit = 100, baseUrl = baseUrl)
            if (remoteResult is NetworkResult.Success) {
                val existingApaarIds = localEntities.map { it.apaarId }.toSet()
                val toInsert = remoteResult.data
                    .filter { it.apaarId !in existingApaarIds }
                    .map { dto ->
                        StudentEntity(
                            apaarId = dto.apaarId,
                            studentName = dto.studentName,
                            dateOfBirth = dto.dateOfBirth,
                            gender = dto.gender,
                            institutionId = dto.institutionId,
                            programId = dto.programId,
                            academicYear = dto.academicYear,
                            admissionQuota = dto.admissionQuota,
                            enrollmentDate = dto.enrollmentDate,
                            studentInstituteRollNo = dto.studentInstituteRollNo,
                            nationality = dto.nationality,
                            passportNumber = dto.passportNumber,
                            visaValidity = dto.visaValidity,
                            countryOfOrigin = dto.countryOfOrigin,
                            abcAccountId = null,
                            verificationStatus = dto.verificationStatus,
                            isActive = dto.isActive,
                            photoSeed = dto.apaarId.filter { it.isDigit() }.sumOf { it.digitToInt() } % 6
                        )
                    }
                if (toInsert.isNotEmpty()) {
                    studentDao.insertAll(toInsert)
                    recomputeAnomalies()
                }
            }
        }

        auditDao.insert(
            AuditLogEntity(
                timestamp = System.currentTimeMillis(),
                actor = "Android Sync Client",
                action = if (summary.isOffline) "SYNC_OFFLINE" else "SYNC_COMPLETED",
                subject = "National APAAR Registry",
                details = summary.message,
                category = if (summary.isOffline) "OFFLINE" else "SYNC"
            )
        )

        summary
    }

    /**
     * Verifies an opaque token online via the API, falling back gracefully if offline.
     */
    suspend fun verifyTokenRemote(
        token: String,
        baseUrl: String = ChhatraLekhaApiClient.DEFAULT_BASE_URL
    ): NetworkResult<RemoteTokenVerification> = withContext(Dispatchers.IO) {
        apiClient.verifyToken(token, baseUrl)
    }

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
