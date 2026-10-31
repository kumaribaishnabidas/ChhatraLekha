package com.chhatralekha.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.chhatralekha.core.csv.CsvIngestionReport
import com.chhatralekha.core.csv.CsvIngestionValidator
import com.chhatralekha.core.csv.CsvValidationContext
import com.chhatralekha.core.model.AdmissionQuota
import com.chhatralekha.core.model.Anomaly
import com.chhatralekha.core.model.AnomalySeverity
import com.chhatralekha.core.model.AnomalyType
import com.chhatralekha.core.model.AuditEntry
import com.chhatralekha.core.model.Gender
import com.chhatralekha.core.model.Institution
import com.chhatralekha.core.model.IntakeSnapshot
import com.chhatralekha.core.model.NationalKpis
import com.chhatralekha.core.model.ProgramIntake
import com.chhatralekha.core.model.QuotaDistribution
import com.chhatralekha.core.model.Student
import com.chhatralekha.core.model.UserRole
import com.chhatralekha.core.model.VerificationStatus
import com.chhatralekha.core.security.SealGenerator
import com.chhatralekha.core.validation.AnomalyEngine
import com.chhatralekha.core.validation.ApaarIdValidator
import com.chhatralekha.core.validation.DetectedAnomaly
import com.chhatralekha.core.validation.RegistrySnapshot
import com.chhatralekha.app.data.repository.ApaarRepository
import com.chhatralekha.core.network.ChhatraLekhaApiClient
import com.chhatralekha.core.network.NetworkResult
import com.chhatralekha.core.qr.ApaarQrPayload
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * Filters available on the AICTE anomaly inspector.
 */
enum class AnomalyFilter(val label: String) {
    ALL("All"),
    CRITICAL("Critical"),
    DUPLICATE("Cross-institution"),
    INTAKE("Intake breach"),
    SUPERNUMERARY("Supernumerary"),
    DATA("Data quality")
}

/**
 * The dossier produced by a verification request.
 */
data class VerificationDossier(
    val query: String,
    val found: Boolean,
    val student: Student? = null,
    val institution: Institution? = null,
    val program: ProgramIntake? = null,
    val anomalies: List<Anomaly> = emptyList(),
    val seal: String = "",
    val sealValid: Boolean = false,
    val timestamp: Long = 0L,
    val duplicateInstitutions: List<Institution> = emptyList(),
    val message: String = "",
    val token: String? = null
)

/**
 * Everything the UI needs to render the multi-role portal.
 */
data class ApaarUiState(
    val isLoading: Boolean = true,
    val role: UserRole = UserRole.AICTE_DIRECTORATE,
    val institutions: List<Institution> = emptyList(),
    val programs: List<ProgramIntake> = emptyList(),
    val students: List<Student> = emptyList(),
    val anomalies: List<Anomaly> = emptyList(),
    val auditTrail: List<AuditEntry> = emptyList(),
    val kpis: NationalKpis = NationalKpis.Empty,
    val snapshots: List<IntakeSnapshot> = emptyList(),
    val quotaDistribution: List<QuotaDistribution> = emptyList(),
    val selectedInstitutionId: String = "",
    val selectedStudentApaarId: String = "",
    val anomalyFilter: AnomalyFilter = AnomalyFilter.ALL,
    val registerSearch: String = "",
    val message: String? = null,
    val isWorking: Boolean = false
) {
    val selectedInstitution: Institution?
        get() = institutions.firstOrNull { it.institutionId == selectedInstitutionId }

    val institutionPrograms: List<ProgramIntake>
        get() = programs.filter { it.institutionId == selectedInstitutionId }

    val institutionSnapshots: List<IntakeSnapshot>
        get() = snapshots.filter { it.program.institutionId == selectedInstitutionId }

    val institutionStudents: List<Student>
        get() = students.filter { it.institutionId == selectedInstitutionId && it.isActive }

    /**
     * The student whose APAAR card is being displayed. Falls back to the first
     * active enrolment so the student workspace is never empty.
     */
    val identityStudent: Student?
        get() = students.firstOrNull { it.apaarId == selectedStudentApaarId && it.isActive }
            ?: students.firstOrNull { it.isActive }

    val identityInstitution: Institution?
        get() = identityStudent?.let { student -> institutions.firstOrNull { it.institutionId == student.institutionId } }

    val identityProgram: ProgramIntake?
        get() = identityStudent?.let { student ->
            programs.firstOrNull { it.institutionId == student.institutionId && it.programId == student.programId }
        }

    val identityAnomalies: List<Anomaly>
        get() = identityStudent?.let { student ->
            anomalies.filter { it.studentApaarId == student.apaarId }
        } ?: emptyList()

    val filteredAnomalies: List<Anomaly>
        get() = anomalies.filter { anomaly ->
            when (anomalyFilter) {
                AnomalyFilter.ALL -> true
                AnomalyFilter.CRITICAL -> anomaly.severity == AnomalySeverity.CRITICAL ||
                    anomaly.severity == AnomalySeverity.HIGH
                AnomalyFilter.DUPLICATE -> anomaly.anomalyType == AnomalyType.DUPLICATE_CROSS_COLLEGE
                AnomalyFilter.INTAKE -> anomaly.anomalyType == AnomalyType.EXCESS_APPROVED_INTAKE
                AnomalyFilter.SUPERNUMERARY -> anomaly.anomalyType == AnomalyType.SUPERNUMERARY_BREACH
                AnomalyFilter.DATA -> anomaly.anomalyType == AnomalyType.INVALID_APAAR_FORMAT ||
                    anomaly.anomalyType == AnomalyType.INCONSISTENT_CATEGORY ||
                    anomaly.anomalyType == AnomalyType.UNSANCTIONED_PROGRAM
            }
        }

    val institutionAnomalies: List<Anomaly>
        get() = anomalies.filter { it.institutionId == selectedInstitutionId }

    /**
     * Institutions ranked by the number of open regulatory flags.
     */
    val institutionsByRisk: List<Pair<Institution, Int>>
        get() = institutions.map { institution ->
            institution to anomalies.count { it.institutionId == institution.institutionId }
        }.sortedByDescending { it.second }
}

class ApaarViewModel(private val repository: ApaarRepository) : ViewModel() {

    private val role = MutableStateFlow(UserRole.AICTE_DIRECTORATE)
    private val selectedInstitutionId = MutableStateFlow("")
    private val controls = MutableStateFlow(Controls())

    private data class Controls(
        val anomalyFilter: AnomalyFilter = AnomalyFilter.ALL,
        val registerSearch: String = "",
        val message: String? = null,
        val working: Boolean = false,
        val selectedStudentApaarId: String = ""
    )

    val csvReport = MutableStateFlow<CsvIngestionReport?>(null)
    val csvInput = MutableStateFlow("")
    val verification = MutableStateFlow<VerificationDossier?>(null)
    val manualErrors = MutableStateFlow<Map<String, String>>(emptyMap())

    val uiState: StateFlow<ApaarUiState> = combine(
        repository.registry,
        repository.auditTrail,
        role,
        selectedInstitutionId,
        controls
    ) { registry, audit, currentRole, institutionId, ctrl ->
        buildState(registry, audit, currentRole, institutionId, ctrl)
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = ApaarUiState()
    )

    init {
        viewModelScope.launch {
            controls.update { it.copy(working = true) }
            val seeded = repository.ensureSeeded()
            if (seeded) {
                controls.update {
                    it.copy(message = "National APAAR registry seeded — regulatory anomaly scan complete.")
                }
            }
            controls.update { it.copy(working = false) }
        }
    }

    private fun buildState(
        registry: RegistrySnapshot,
        audit: List<AuditEntry>,
        currentRole: UserRole,
        institutionId: String,
        ctrl: Controls
    ): ApaarUiState {
        val anomalies = AnomalyEngine.evaluate(registry).toDomainAnomalies()
        val snapshots = AnomalyEngine.buildSnapshots(registry)
        val effectiveInstitution = institutionId.ifBlank {
            registry.institutions.firstOrNull()?.institutionId.orEmpty()
        }
        return ApaarUiState(
            isLoading = registry.students.isEmpty(),
            role = currentRole,
            institutions = registry.institutions,
            programs = registry.programs,
            students = registry.students,
            anomalies = anomalies,
            auditTrail = audit,
            kpis = computeKpis(registry, anomalies),
            snapshots = snapshots,
            quotaDistribution = computeQuotaDistribution(registry),
            selectedInstitutionId = effectiveInstitution,
            selectedStudentApaarId = ctrl.selectedStudentApaarId,
            anomalyFilter = ctrl.anomalyFilter,
            registerSearch = ctrl.registerSearch,
            message = ctrl.message,
            isWorking = ctrl.working
        )
    }

    /**
     * Promotes the engine's transient findings into the persistable read model.
     */
    private fun List<DetectedAnomaly>.toDomainAnomalies(): List<Anomaly> =
        mapIndexed { index, detected ->
            Anomaly(
                anomalyId = index.toLong(),
                studentApaarId = detected.studentApaarId,
                institutionId = detected.institutionId,
                programId = detected.programId,
                anomalyType = detected.anomalyType,
                severity = detected.severity,
                details = detected.details,
                timestamp = System.currentTimeMillis()
            )
        }

    private fun computeKpis(registry: RegistrySnapshot, anomalies: List<Anomaly>): NationalKpis {
        val active = registry.students.filter { it.isActive }
        val totalApproved = registry.programs.sumOf { it.approvedIntake }
        val totalEnrolled = active.size
        return NationalKpis(
            institutionCount = registry.institutions.size,
            programmeCount = registry.programs.size,
            totalApprovedIntake = totalApproved,
            totalEnrolled = totalEnrolled,
            flaggedAnomalies = anomalies.size,
            criticalAnomalies = anomalies.count {
                it.severity == AnomalySeverity.CRITICAL || it.severity == AnomalySeverity.HIGH
            },
            supernumeraryEnrolled = active.count { it.admissionQuota.isSupernumerary },
            utilisationPercent = if (totalApproved == 0) 0f else totalEnrolled * 100f / totalApproved
        )
    }

    /**
     * National quota distribution across the five AICTE seat buckets.
     *
     * The OCI and Foreign-National buckets share a single 15% ceiling, so they
     * are reported as one combined band rather than being split arbitrarily.
     */
    private fun computeQuotaDistribution(registry: RegistrySnapshot): List<QuotaDistribution> {
        val active = registry.students.filter { it.isActive }
        val programs = registry.programs

        fun count(predicate: (AdmissionQuota) -> Boolean): Int =
            active.count { predicate(it.admissionQuota) }

        return listOf(
            QuotaDistribution(
                label = "Regular (Merit + Management)",
                enrolled = count { it.isRegular && it != AdmissionQuota.PMSSS },
                sanctioned = programs.sumOf { it.approvedIntake - it.maxPmsss },
                quota = AdmissionQuota.MERIT
            ),
            QuotaDistribution(
                label = "PMSSS Scholarship",
                enrolled = count { it == AdmissionQuota.PMSSS },
                sanctioned = programs.sumOf { it.maxPmsss },
                quota = AdmissionQuota.PMSSS
            ),
            QuotaDistribution(
                label = "NRI Supernumerary",
                enrolled = count { it == AdmissionQuota.NRI },
                sanctioned = programs.sumOf { it.maxSupernumeraryNri },
                quota = AdmissionQuota.NRI
            ),
            QuotaDistribution(
                label = "OCI / Foreign National",
                enrolled = count { it == AdmissionQuota.OCI || it == AdmissionQuota.FN },
                sanctioned = programs.sumOf { it.maxSupernumeraryFnOci },
                quota = AdmissionQuota.OCI
            ),
            QuotaDistribution(
                label = "Tuition Fee Waiver",
                enrolled = count { it == AdmissionQuota.TFW },
                sanctioned = programs.sumOf { it.maxSupernumeraryTfw },
                quota = AdmissionQuota.TFW
            )
        )
    }

    // ------------------------------------------------------------- commands

    fun selectRole(next: UserRole) {
        role.value = next
        verification.value = null
        csvReport.value = null
    }

    fun selectInstitution(id: String) {
        selectedInstitutionId.value = id
        csvReport.value = null
    }

    fun selectStudent(apaarId: String) {
        controls.update { it.copy(selectedStudentApaarId = apaarId) }
    }

    fun setAnomalyFilter(filter: AnomalyFilter) {
        controls.update { it.copy(anomalyFilter = filter) }
    }

    fun setRegisterSearch(query: String) {
        controls.update { it.copy(registerSearch = query) }
    }

    fun dismissMessage() {
        controls.update { it.copy(message = null) }
    }

    fun postMessage(text: String) {
        controls.update { it.copy(message = text) }
    }

    fun updateCsvInput(text: String) {
        csvInput.value = text
        if (text.isBlank()) csvReport.value = null
    }

    fun loadSampleCsv() {
        csvInput.value = CsvIngestionValidator.TEMPLATE
        validateCsv()
    }

    /**
     * Runs the live CSV validator against the current registry state.
     */
    fun validateCsv() {
        val text = csvInput.value
        if (text.isBlank()) {
            csvReport.value = null
            return
        }
        viewModelScope.launch {
            controls.update { it.copy(working = true) }
            val state = uiState.value
            val context = buildValidationContext(state)
            csvReport.value = CsvIngestionValidator.validate(text, context)
            controls.update { it.copy(working = false) }
        }
    }

    private fun buildValidationContext(state: ApaarUiState): CsvValidationContext {
        val institutionId = state.selectedInstitutionId
        val programs = state.programs.filter { it.institutionId == institutionId }
        val students = state.students.filter { it.institutionId == institutionId && it.isActive }
        fun countFor(programId: String, predicate: (Student) -> Boolean): Int =
            students.count { it.programId == programId && predicate(it) }
        return CsvValidationContext(
            programs = programs,
            existingApaarIds = state.students.filter { it.isActive }.map { it.apaarId }.toSet(),
            existingRegularCounts = programs.associate {
                it.programId to countFor(it.programId) { s -> s.admissionQuota.isRegular }
            },
            existingSupernumeraryCounts = programs.associate {
                it.programId to countFor(it.programId) { s -> s.admissionQuota.isSupernumerary }
            },
            existingNriCounts = programs.associate {
                it.programId to countFor(it.programId) { s -> s.admissionQuota == AdmissionQuota.NRI }
            },
            existingOciFnCounts = programs.associate {
                it.programId to countFor(it.programId) {
                    s -> s.admissionQuota == AdmissionQuota.OCI || s.admissionQuota == AdmissionQuota.FN
                }
            },
            existingTfwCounts = programs.associate {
                it.programId to countFor(it.programId) { s -> s.admissionQuota == AdmissionQuota.TFW }
            },
            existingPmsssCounts = programs.associate {
                it.programId to countFor(it.programId) { s -> s.admissionQuota == AdmissionQuota.PMSSS }
            }
        )
    }

    /**
     * Commits the validated batch to the central repository.
     */
    fun commitCsv(onDone: (String) -> Unit) {
        val report = csvReport.value ?: return
        val state = uiState.value
        viewModelScope.launch {
            controls.update { it.copy(working = true) }
            val result = repository.commitBatch(
                rows = report.rows,
                institutionId = state.selectedInstitutionId,
                actor = state.selectedInstitution?.name ?: "Institution Registrar",
                academicYear = "2024-25"
            )
            csvReport.value = null
            csvInput.value = ""
            controls.update { it.copy(working = false) }
            onDone(
                "Committed ${result.committed} enrolments · ${result.skipped} row(s) rejected · " +
                    "${result.totalAnomalies} anomaly record(s) in force."
            )
        }
    }

    /**
     * Validates and stores a manually entered student.
     */
    fun submitManualStudent(
        apaarId: String,
        fullName: String,
        dob: String,
        gender: String,
        rollNo: String,
        programId: String,
        quota: AdmissionQuota,
        nationality: String,
        passportNumber: String,
        countryOfOrigin: String,
        onDone: (String) -> Unit
    ) {
        val state = uiState.value
        val errors = mutableMapOf<String, String>()

        val validation = ApaarIdValidator.validate(apaarId)
        if (!validation.isStructurallyValid) {
            errors["apaar"] = validation.errors.firstOrNull() ?: "Invalid APAAR ID."
        } else if (state.students.any { it.isActive && it.apaarId == validation.normalised }) {
            errors["apaar"] = "This APAAR ID already exists in the national registry."
        }
        if (fullName.isBlank()) errors["name"] = "Full name is mandatory."
        if (!dob.matches(Regex("^\\d{4}-\\d{2}-\\d{2}$"))) errors["dob"] = "Use the yyyy-MM-dd format."
        if (programId.isBlank()) errors["program"] = "Select a sanctioned programme."
        if (quota.requiresForeignDocs && passportNumber.isBlank()) {
            errors["passport"] = "Foreign-national admissions require a passport / document number."
        }

        manualErrors.value = errors
        if (errors.isNotEmpty()) {
            onDone("Resolve the highlighted fields before onboarding.")
            return
        }

        viewModelScope.launch {
            controls.update { it.copy(working = true) }
            val student = Student(
                recordId = 0,
                apaarId = validation.normalised,
                studentName = fullName.trim(),
                dateOfBirth = dob,
                gender = Gender.fromCode(gender) ?: Gender.OTHER,
                institutionId = state.selectedInstitutionId,
                programId = programId,
                academicYear = "2024-25",
                admissionQuota = quota,
                enrollmentDate = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.ENGLISH)
                    .format(java.util.Date()),
                studentInstituteRollNo = rollNo.ifBlank { "AUTO-${validation.normalised.takeLast(4)}" },
                nationality = nationality.ifBlank { "Indian" },
                passportNumber = passportNumber.ifBlank { null },
                visaValidity = null,
                countryOfOrigin = countryOfOrigin.ifBlank { null },
                abcAccountId = null,
                verificationStatus = VerificationStatus.PENDING_REVIEW,
                isActive = true,
                photoSeed = validation.normalised.sumOf { it.digitToInt() } % 6
            )
            val result = repository.addStudent(student, state.selectedInstitution?.name ?: "Registrar")
            controls.update { it.copy(working = false) }
            if (result.committed > 0) {
                onDone("${student.studentName} onboarded — ${result.totalAnomalies} anomaly record(s) in force.")
            } else {
                onDone("Onboarding failed — the record already exists.")
            }
        }
    }

    /**
     * Runs a credential verification for a 12-digit APAAR ID or an institutional
     * roll number and produces the tamper-evident dossier.
     */
    fun verify(query: String) {
        val trimmed = query.trim()
        if (trimmed.isEmpty()) {
            verification.value = VerificationDossier(
                query = trimmed,
                found = false,
                message = "Enter a 12-digit APAAR ID or an institutional roll number."
            )
            return
        }
        viewModelScope.launch {
            controls.update { it.copy(working = true) }

            // Check if query is an opaque token or verification URL
            val parsedQr = ApaarQrPayload.parse(trimmed)
            if (parsedQr?.isTokenPayload == true) {
                val token = parsedQr.token!!
                when (val remoteResult = repository.verifyTokenRemote(token)) {
                    is NetworkResult.Success -> {
                        val data = remoteResult.data
                        verification.value = VerificationDossier(
                            query = trimmed,
                            found = data.valid,
                            sealValid = data.valid,
                            timestamp = System.currentTimeMillis(),
                            message = if (data.valid) {
                                "Credential verified via token: ${data.institution ?: "AICTE"} (${data.programme ?: "Approved"}). Verdict: ${data.verdict}"
                            } else {
                                "Token verification failed: ${data.verdict}. ${data.reason}"
                            }
                        )
                    }
                    is NetworkResult.OfflineFallback -> {
                        verification.value = VerificationDossier(
                            query = trimmed,
                            found = false,
                            timestamp = System.currentTimeMillis(),
                            message = "Backend server unreachable. Token verification requires server access."
                        )
                    }
                    is NetworkResult.Error -> {
                        verification.value = VerificationDossier(
                            query = trimmed,
                            found = false,
                            timestamp = System.currentTimeMillis(),
                            message = "Verification error (HTTP ${remoteResult.statusCode}): ${remoteResult.message}"
                        )
                    }
                }
                controls.update { it.copy(working = false) }
                return@launch
            }

            val state = uiState.value
            val digits = trimmed.filter { it.isDigit() }
            val matches = when {
                trimmed.length == 12 && digits.length == 12 -> state.students.filter {
                    it.isActive && it.apaarId == digits
                }
                else -> listOfNotNull(
                    state.students.firstOrNull { it.studentInstituteRollNo.equals(trimmed, ignoreCase = true) }
                )
            }


            val timestamp = System.currentTimeMillis()
            if (matches.isEmpty()) {
                verification.value = VerificationDossier(
                    query = trimmed,
                    found = false,
                    timestamp = timestamp,
                    message = "No active enrolment was found in the national registry for this identifier."
                )
                repository.recordVerification(
                    actor = "Third-Party Verifier",
                    apaarId = trimmed,
                    outcome = "NOT_FOUND",
                    details = "Verification query returned no matching enrolment."
                )
            } else {
                val student = matches.first()
                val institution = state.institutions.firstOrNull { it.institutionId == student.institutionId }
                val program = state.programs.firstOrNull {
                    it.institutionId == student.institutionId && it.programId == student.programId
                }
                val related = state.anomalies.filter { it.studentApaarId == student.apaarId }
                val seal = SealGenerator.seal(
                    apaarId = student.apaarId,
                    institutionId = student.institutionId,
                    programId = student.programId,
                    academicYear = student.academicYear,
                    enrollmentDate = student.enrollmentDate
                )
                val duplicateInstitutions = matches
                    .map { it.institutionId }
                    .distinct()
                    .mapNotNull { id -> state.institutions.firstOrNull { it.institutionId == id } }
                verification.value = VerificationDossier(
                    query = trimmed,
                    found = true,
                    student = student,
                    institution = institution,
                    program = program,
                    anomalies = related,
                    seal = seal,
                    sealValid = related.none { it.severity == AnomalySeverity.CRITICAL },
                    timestamp = timestamp,
                    duplicateInstitutions = duplicateInstitutions,
                    message = if (related.isEmpty()) {
                        "Credential verified against the AICTE national registry."
                    } else {
                        "Credential located but ${related.size} regulatory flag(s) are open."
                    }
                )
                repository.recordVerification(
                    actor = "Third-Party Verifier",
                    apaarId = student.apaarId,
                    outcome = if (related.isEmpty()) "VERIFIED" else "FLAGGED",
                    details = "Verified ${student.studentName} at ${institution?.name}."
                )
            }
            controls.update { it.copy(working = false) }
        }
    }

    fun clearVerification() {
        verification.value = null
    }

    /**
     * Deterministic sample identifiers used by the "scan QR" demo action.
     */
    fun sampleVerificationQueries(): List<String> {
        val state = uiState.value
        val pool = state.students.filter { it.isActive }
        if (pool.isEmpty()) return emptyList()
        return listOf(
            pool[pool.size / 3].apaarId,
            pool[pool.size / 2].apaarId,
            pool.first().studentInstituteRollNo
        )
    }

    /**

     * Synchronizes local Room database with the remote ChhatraLekha backend.
     */
    fun syncWithServer(baseUrl: String = ChhatraLekhaApiClient.DEFAULT_BASE_URL) {
        viewModelScope.launch {
            controls.update { it.copy(working = true) }
            val summary = repository.syncWithBackend(baseUrl)
            controls.update {
                it.copy(
                    working = false,
                    message = summary.message
                )
            }
        }
    }

    /**
     * Requests an opaque verification token for a student credential.
     */
    suspend fun requestVerificationToken(
        apaarId: String,
        baseUrl: String = ChhatraLekhaApiClient.DEFAULT_BASE_URL
    ): NetworkResult<String> {
        return repository.requestVerificationToken(apaarId, baseUrl)
    }

    companion object {
        fun factory(repository: ApaarRepository): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T =
                    ApaarViewModel(repository) as T
            }
    }
}

/**
 * Small helper so the control state can be mutated atomically.
 */
private inline fun <T> MutableStateFlow<T>.update(transform: (T) -> T) {
    while (true) {
        val current = value
        val next = transform(current)
        if (compareAndSet(current, next)) return
    }
}
