package com.acadentrix.app.ui.screens.student

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AccountBalance
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.Info
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.acadentrix.core.qr.ApaarQrPayload
import com.acadentrix.core.qr.QrEncoder
import com.acadentrix.core.model.Student
import com.acadentrix.core.security.SealGenerator
import com.acadentrix.core.validation.ApaarIdValidator
import com.acadentrix.app.ui.components.ApaarCard
import com.acadentrix.app.ui.components.DetailRow
import com.acadentrix.app.ui.components.DropdownSelector
import com.acadentrix.app.ui.components.EduSynCMark
import com.acadentrix.app.ui.components.EduSynCPlate
import com.acadentrix.app.ui.components.EmptyState
import com.acadentrix.app.ui.components.InfoBanner
import com.acadentrix.app.ui.components.QrCodeView
import com.acadentrix.app.ui.components.SearchField
import com.acadentrix.app.ui.components.SectionHeader
import com.acadentrix.app.ui.components.StatusPill
import com.acadentrix.app.ui.components.StudentAvatar
import com.acadentrix.app.ui.components.Tone
import com.acadentrix.app.ui.components.VerificationBadge
import com.acadentrix.app.ui.theme.ApaarTheme
import com.acadentrix.app.ui.theme.NavyDeep
import com.acadentrix.app.ui.theme.NavyPrimary
import com.acadentrix.app.ui.theme.Saffron
import com.acadentrix.app.ui.viewmodel.ApaarViewModel

/**
 * The degree-awarding body's bonafide / enrolment certificate.
 *
 * Unlike the digital identity card this document is a *paper-equivalent*
 * instrument: it carries a certificate number, the full enrolment assertions,
 * the degree-awording body's affiliation, a scannable QR badge and the
 * tamper-evident seal so that a physical print-out can be re-verified offline.
 */
@Composable
fun DegreeCertificateScreen(viewModel: ApaarViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val colors = ApaarTheme.colors

    var search by remember { mutableStateOf("") }

    val student = state.identityStudent
    val candidates = remember(search, state.students.size) {
        state.students
            .filter { it.isActive }
            .filter {
                val query = search.trim()
                query.isEmpty() ||
                    it.studentName.contains(query, ignoreCase = true) ||
                    it.apaarId.contains(query, ignoreCase = true)
            }
            .take(40)
    }

    // Derived at the function scope — see the note in [ApaarCardScreen] about
    // non-local returns inside a LazyColumn content lambda.
    val institution = state.identityInstitution
    val program = state.identityProgram
    val seal = remember(student) {
        student?.let {
            SealGenerator.seal(
                apaarId = it.apaarId,
                institutionId = it.institutionId,
                programId = it.programId,
                academicYear = it.academicYear,
                enrollmentDate = it.enrollmentDate
            )
        }
    }
    val certificateNumber = remember(student, seal) {
        student?.let {
            "AICTE/APAAR/${it.academicYear}/${it.apaarId.takeLast(4)}/${seal.orEmpty().take(6)}"
        }
    }
    val payload = remember(student, seal) {
        student?.let {
            ApaarQrPayload.build(
                apaarId = it.apaarId,
                institutionId = it.institutionId,
                programId = it.programId,
                seal = seal.orEmpty(),
                timestamp = System.currentTimeMillis()
            )
        }
    }
    val matrix = remember(payload) { payload?.let { QrEncoder.encode(it) } }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(14.dp),
        verticalArrangement = Arrangement.spacedBy(13.dp)
    ) {
        item {
            Column {
                Text(
                    text = "DEGREE-AWARDING BODY",
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.saffron,
                    letterSpacing = 1.1.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Bonafide Certificate",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(Modifier.height(3.dp))
                Text(
                    text = "A verifiable enrolment instrument. The certificate number, QR badge and " +
                        "cryptographic seal bind the document to the AICTE national APAAR registry.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        item {
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(14.dp)) {
                    SectionHeader(
                        title = "Certificate holder",
                        subtitle = "Select an enrolment to issue the certificate against"
                    )
                    Spacer(Modifier.height(10.dp))
                    SearchField(
                        value = search,
                        onValueChange = { search = it },
                        placeholder = "Search by name or APAAR ID…"
                    )
                    Spacer(Modifier.height(10.dp))
                    DropdownSelector(
                        label = "Enrolment",
                        options = candidates,
                        selected = student,
                        onSelect = { viewModel.selectStudent(it.apaarId) },
                        itemLabel = { "${it.studentName} · ${ApaarIdValidator.format(it.apaarId)}" }
                    )
                }
            }
        }

        if (student == null) {
            item {
                EmptyState(
                    title = "No enrolment available",
                    message = "The national registry has no active enrolment to certify.",
                    icon = Icons.Filled.Info
                )
            }
            return@LazyColumn
        }

        val flags = state.identityAnomalies
        val certificateMatrix = matrix
        val certificateSeal = seal.orEmpty()
        val certificateRef = certificateNumber.orEmpty()

        item {
            CertificateSheet(
                certificateNumber = certificateRef,
                studentName = student.studentName,
                initials = student.initials,
                photoSeed = student.photoSeed,
                apaarId = student.apaarId,
                institutionName = institution?.name ?: student.institutionId,
                institutionId = student.institutionId,
                institutionType = institution?.institutionType?.label.orEmpty(),
                institutionLocation = institution?.location.orEmpty(),
                naacGrade = institution?.naacGrade.orEmpty(),
                approvalYear = institution?.approvalYear?.toString().orEmpty(),
                affiliatingBody = institution?.affiliationUniversity.orEmpty(),
                programName = program?.programName ?: student.programId,
                programLevel = program?.programLevel.orEmpty(),
                programCode = student.programId,
                academicYear = student.academicYear,
                dateOfBirth = student.dateOfBirth,
                gender = student.gender.label,
                nationality = student.nationality,
                quota = student.admissionQuota.label,
                rollNo = student.studentInstituteRollNo,
                enrollmentDate = student.enrollmentDate,
                abcAccountId = student.abcAccountId,
                matrix = certificateMatrix,
                seal = certificateSeal,
                issuedAt = System.currentTimeMillis(),
                flagged = flags.isNotEmpty()
            )
        }

        item {
            SealVerificationPanel(
                seal = certificateSeal,
                student = student,
                flags = flags.size
            )
        }

        item {
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(15.dp)) {
                    SectionHeader(
                        title = "Verification instructions",
                        subtitle = "How a third party confirms this certificate"
                    )
                    Spacer(Modifier.height(8.dp))
                    Instruction(1, "Scan the QR badge or key in the 12-digit APAAR ID.")
                    Instruction(2, "The verifier resolves the enrolment in the AICTE national registry.")
                    Instruction(
                        3,
                        "The registry recomputes the SHA-256 seal and compares it with the seal " +
                            "printed on this certificate — any mismatch means the document has been altered."
                    )
                    Instruction(4, "Open regulatory flags on the enrolment are disclosed to the verifier.")
                }
            }
        }

        item {
            Text(
                text = "Generated by the AICTE APAAR national registry. This certificate is issued for " +
                    "demonstration and conforms to the APAAR verification contract " +
                    "(apaar.aicte-india.gov.in/verify).",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.outline
            )
        }
    }
}

/**
 * The printable certificate sheet.
 */
@Composable
private fun CertificateSheet(
    certificateNumber: String,
    studentName: String,
    initials: String,
    photoSeed: Int,
    apaarId: String,
    institutionName: String,
    institutionId: String,
    institutionType: String,
    institutionLocation: String,
    naacGrade: String,
    approvalYear: String,
    affiliatingBody: String,
    programName: String,
    programLevel: String,
    programCode: String,
    academicYear: String,
    dateOfBirth: String,
    gender: String,
    nationality: String,
    quota: String,
    rollNo: String,
    enrollmentDate: String,
    abcAccountId: String?,
    matrix: QrEncoder.QrMatrix?,
    seal: String,
    issuedAt: Long,
    flagged: Boolean
) {
    val colors = ApaarTheme.colors

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(4.dp))
            .background(Color.White)
            .border(3.dp, NavyDeep, RoundedCornerShape(4.dp))
            .padding(16.dp)
    ) {
        // ---------------------------------------------------------- letterhead
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(Brush.horizontalGradient(listOf(NavyDeep, NavyPrimary)))
                .padding(horizontal = 12.dp, vertical = 10.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(30.dp)
                        .clip(RoundedCornerShape(9.dp))
                        .background(Color.White.copy(alpha = 0.14f))
                        .border(1.dp, Saffron.copy(alpha = 0.6f), RoundedCornerShape(9.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        Icons.Filled.AccountBalance,
                        contentDescription = null,
                        tint = Saffron,
                        modifier = Modifier.size(17.dp)
                    )
                }
                Spacer(Modifier.width(9.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION",
                        style = MaterialTheme.typography.labelSmall,
                        color = Color.White,
                        letterSpacing = 0.8.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "National APAAR Registry · Academic Bank of Credits",
                        style = MaterialTheme.typography.labelSmall,
                        color = Color.White.copy(alpha = 0.75f)
                    )
                }
                Spacer(Modifier.width(8.dp))
                EduSynCPlate(markSize = 15.dp, platePadding = 4.dp, radius = 7.dp)
            }
        }

        Spacer(Modifier.height(14.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.Top
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "CERTIFICATE OF ENROLMENT",
                    style = MaterialTheme.typography.titleLarge,
                    color = NavyDeep,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 0.6.sp
                )
                Text(
                    text = "Issued under the AICTE Academic Identification Programme",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color(0xFF5A6470)
                )
            }
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = "CERTIFICATE NO.",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color(0xFF5A6470),
                    letterSpacing = 0.6.sp
                )
                Text(
                    text = certificateNumber,
                    style = MaterialTheme.typography.labelSmall,
                    color = NavyDeep,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.End
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "ISSUED ${SealGenerator.formatTimestamp(issuedAt)}",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color(0xFF5A6470)
                )
            }
        }

        Spacer(Modifier.height(12.dp))

        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(2.dp)
                .background(Saffron)
        )

        Spacer(Modifier.height(12.dp))

        // ------------------------------------------------------------- body
        Text(
            text = "This is to certify that",
            style = MaterialTheme.typography.bodyMedium,
            color = Color(0xFF333A42)
        )
        Spacer(Modifier.height(4.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            StudentAvatar(
                initials = initials,
                seed = photoSeed,
                size = 46.dp
            )
            Spacer(Modifier.width(11.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = studentName,
                    style = MaterialTheme.typography.headlineSmall,
                    color = NavyDeep,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "APAAR ID ${ApaarIdValidator.formatWithSeparator(apaarId)}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = NavyPrimary,
                    fontFamily = FontFamily.Monospace
                )
            }
        }
        Spacer(Modifier.height(8.dp))
        Text(
            text = "is duly admitted and enrolled at $institutionName ($institutionId), an " +
                "AICTE-approved institution, in the programme $programName ($programCode) for the " +
                "academic year $academicYear under the $quota category.",
            style = MaterialTheme.typography.bodyMedium,
            color = Color(0xFF333A42)
        )
        Spacer(Modifier.height(10.dp))
        Text(
            text = "The above enrolment is recorded in the AICTE National Academic Account Registry " +
                "(APAAR) and is verifiable through the seal and QR badge affixed below.",
            style = MaterialTheme.typography.bodySmall,
            color = Color(0xFF5A6470)
        )

        Spacer(Modifier.height(14.dp))

        // --------------------------------------------------------- particulars
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, Color(0xFFD5DAE0), RoundedCornerShape(10.dp))
                .padding(horizontal = 12.dp, vertical = 8.dp)
        ) {
            Particular("Name of student", studentName)
            Particular("Date of birth", dateOfBirth)
            Particular("Gender", gender)
            Particular("Nationality", nationality)
            Particular("Programme", programName)
            if (programLevel.isNotBlank()) Particular("Programme level", programLevel)
            Particular("Academic year", academicYear)
            Particular("Institute roll no.", rollNo)
            Particular("Date of enrolment", enrollmentDate)
            Particular("Category of admission", quota)
            if (abcAccountId != null) Particular("ABC account", abcAccountId)
            Particular("Issuing institution", institutionName)
            if (institutionType.isNotBlank()) Particular("Institution type", institutionType)
            if (institutionLocation.isNotBlank()) Particular("Institution location", institutionLocation)
            if (naacGrade.isNotBlank()) Particular("NAAC grade", naacGrade)
            if (approvalYear.isNotBlank()) Particular("AICTE approval year", approvalYear)
            if (affiliatingBody.isNotBlank()) Particular("Degree-awarding body", affiliatingBody)
        }

        Spacer(Modifier.height(14.dp))

        // -------------------------------------------------------- seal + QR
        Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "CRYPTOGRAPHIC SEAL (SHA-256 / 128-bit)",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color(0xFF5A6470),
                    letterSpacing = 0.6.sp
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = seal.chunked(8).joinToString("\n"),
                    style = MaterialTheme.typography.labelSmall,
                    color = NavyDeep,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(8.dp))
                StatusPill(
                    text = if (flagged) "ISSUED WITH REGULATORY FLAGS" else "REGISTRY RECORD CLEAN",
                    container = if (flagged) Color(0xFFFDECEA) else Color(0xFFE7F4E8),
                    content = if (flagged) Color(0xFFB71C1C) else Color(0xFF1B5E20)
                )
                Spacer(Modifier.height(8.dp))
                Text(
                    text = "Verify at apaar.aicte-india.gov.in/verify",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color(0xFF5A6470)
                )
            }
            Spacer(Modifier.width(12.dp))
            if (matrix != null) {
                QrCodeView(matrix = matrix, size = 112.dp, darkColor = Color.Black)
            }
        }

        Spacer(Modifier.height(12.dp))

        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(1.dp)
                .background(Color(0xFFD5DAE0))
        )

        Spacer(Modifier.height(10.dp))

        // ------------------------------------------------------- signatures
        Row(modifier = Modifier.fillMaxWidth()) {
            SignatureBlock(
                role = "Registrar",
                organisation = institutionName,
                modifier = Modifier.weight(1f)
            )
            SignatureBlock(
                role = "Controller of Examinations",
                organisation = affiliatingBody.ifBlank { institutionName },
                modifier = Modifier.weight(1f)
            )
        }

        Spacer(Modifier.height(10.dp))

        Text(
            text = "This certificate is electronically generated. It is valid only when the seal " +
                "recomputes to the same value at the AICTE national registry.",
            style = MaterialTheme.typography.labelSmall,
            color = Color(0xFF7A828B),
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(Modifier.height(12.dp))

        // ------------------------------------------------------- brand footer
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically
        ) {
            EduSynCMark(size = 18.dp)
            Spacer(Modifier.width(7.dp))
            Text(
                text = "EDUSYNC",
                style = MaterialTheme.typography.labelSmall,
                color = NavyDeep,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.2.sp
            )
            Text(
                text = "  ·  APAAR ID platform",
                style = MaterialTheme.typography.labelSmall,
                color = Color(0xFF7A828B),
                letterSpacing = 0.4.sp
            )
        }
    }
}

/**
 * A single line of the certificate particulars table.
 */
@Composable
private fun Particular(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 3.dp),
        verticalAlignment = Alignment.Top
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = Color(0xFF5A6470),
            modifier = Modifier.width(148.dp)
        )
        Text(
            text = value,
            style = MaterialTheme.typography.labelSmall,
            color = Color(0xFF1F262E),
            fontWeight = FontWeight.Medium,
            modifier = Modifier.weight(1f)
        )
    }
}

/**
 * A signature block on the certificate footer.
 */
@Composable
private fun SignatureBlock(role: String, organisation: String, modifier: Modifier = Modifier) {
    Column(modifier = modifier, horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = "_________________________",
            style = MaterialTheme.typography.labelSmall,
            color = Color(0xFF5A6470)
        )
        Spacer(Modifier.height(3.dp))
        Text(
            text = role,
            style = MaterialTheme.typography.labelSmall,
            color = NavyDeep,
            fontWeight = FontWeight.Bold,
            textAlign = TextAlign.Center,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis
        )
        Text(
            text = organisation,
            style = MaterialTheme.typography.labelSmall,
            color = Color(0xFF7A828B),
            textAlign = TextAlign.Center,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis
        )
    }
}

/**
 * The seal integrity panel — recomputes the digest and reports the outcome.
 */
@Composable
private fun SealVerificationPanel(
    seal: String,
    student: Student,
    flags: Int
) {
    val colors = ApaarTheme.colors
    val matches = remember(seal, student) {
        SealGenerator.verify(
            presented = seal,
            apaarId = student.apaarId,
            institutionId = student.institutionId,
            programId = student.programId,
            academicYear = student.academicYear,
            enrollmentDate = student.enrollmentDate
        )
    }

    ApaarCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(15.dp)) {
            SectionHeader(
                title = "Seal integrity",
                subtitle = "Locally recomputed against the canonical credential string"
            )
            Spacer(Modifier.height(10.dp))

            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(34.dp)
                        .clip(RoundedCornerShape(11.dp))
                        .background(if (matches) colors.successContainer else colors.criticalContainer),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        if (matches) Icons.Filled.CheckCircle else Icons.Filled.Error,
                        contentDescription = null,
                        tint = if (matches) colors.onSuccessContainer else colors.onCriticalContainer,
                        modifier = Modifier.size(19.dp)
                    )
                }
                Spacer(Modifier.width(10.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = if (matches) "Seal verified locally" else "Seal mismatch detected",
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Text(
                        text = if (matches) {
                            "The printed digest matches the registry record exactly."
                        } else {
                            "The printed digest does not match the registry record."
                        },
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            Spacer(Modifier.height(10.dp))
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(1.dp)
                    .background(colors.divider)
            )
            Spacer(Modifier.height(6.dp))

            DetailRow("Canonical input", "APAAR|${student.apaarId}|${student.institutionId}|${student.programId}|${student.academicYear}|${student.enrollmentDate}", mono = true)
            DetailRow("Digest", seal, mono = true)
            DetailRow("Digest length", "${seal.length} hex characters")
            DetailRow("Open registry flags", flags.toString(), valueColor = if (flags > 0) colors.critical else colors.success)

            Spacer(Modifier.height(6.dp))
            InfoBanner(
                title = "Verification contract",
                message = "An independent verifier recomputes this digest from the registry record. " +
                    "The Luhn check-digit on the APAAR ID is advisory and never blocks issuance.",
                tone = Tone.INFO
            )
        }
    }
}

/**
 * A numbered instruction row.
 */
@Composable
private fun Instruction(index: Int, text: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 5.dp),
        verticalAlignment = Alignment.Top
    ) {
        Box(
            modifier = Modifier
                .size(19.dp)
                .clip(RoundedCornerShape(6.dp))
                .background(NavyDeep),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = index.toString(),
                style = MaterialTheme.typography.labelSmall,
                color = Color.White,
                fontWeight = FontWeight.Bold
            )
        }
        Spacer(Modifier.width(9.dp))
        Text(
            text = text,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.weight(1f)
        )
    }
}
