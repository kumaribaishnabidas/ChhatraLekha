package com.acadentrix.app.ui.screens.student

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Badge
import androidx.compose.material.icons.filled.Cached
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Warning
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
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.acadentrix.core.qr.ApaarQrPayload
import com.acadentrix.core.qr.QrEncoder
import com.acadentrix.core.security.SealGenerator
import com.acadentrix.core.validation.ApaarIdValidator
import com.acadentrix.app.ui.components.ApaarCard
import com.acadentrix.app.ui.components.DropdownSelector
import com.acadentrix.app.ui.components.EmptyState
import com.acadentrix.app.ui.components.InfoBanner
import com.acadentrix.app.ui.components.QrCodeView
import com.acadentrix.app.ui.components.SearchField
import com.acadentrix.app.ui.components.SectionHeader
import com.acadentrix.app.ui.components.StatusPill
import com.acadentrix.app.ui.components.StudentAvatar
import com.acadentrix.app.ui.components.Tone
import com.acadentrix.app.ui.theme.ApaarTheme
import com.acadentrix.app.ui.theme.NavyDeep
import com.acadentrix.app.ui.theme.NavyPrimary
import com.acadentrix.app.ui.theme.Saffron
import com.acadentrix.app.ui.viewmodel.ApaarViewModel

/**
 * The APAAR Digital Academic Identity Card.
 */
@Composable
fun ApaarCardScreen(viewModel: ApaarViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val colors = ApaarTheme.colors

    var search by remember { mutableStateOf("") }
    var flipped by remember { mutableStateOf(false) }
    val rotation by animateFloatAsState(
        targetValue = if (flipped) 180f else 0f,
        animationSpec = tween(620),
        label = "cardFlip"
    )

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

    // The credential artefacts are derived at the function scope. They must not
    // be computed inside the LazyColumn content lambda because a non-local
    // return in that lambda prevents the compiler from treating the remainder
    // of the lambda as a composable context.
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
                    text = "STUDENT / DEGREE-AWARDING BODY",
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.saffron,
                    letterSpacing = 1.1.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "APAAR Digital Identity Card",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(Modifier.height(3.dp))
                Text(
                    text = "One national academic identifier, cryptographically sealed and verifiable " +
                        "by any AICTE-approved institution or employer.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        item {
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(14.dp)) {
                    SectionHeader(
                        title = "Cardholder",
                        subtitle = "Search the national registry to preview an issued card"
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
                    message = "The national registry has no active enrolment to display.",
                    icon = Icons.Filled.Info
                )
            }
            return@LazyColumn
        }

        item {
            val cardMatrix = matrix
            val cardSeal = seal.orEmpty()
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .graphicsLayer {
                        rotationY = rotation
                        cameraDistance = 14f * density
                    }
                    .clip(RoundedCornerShape(20.dp))
                    .clickable { flipped = !flipped }
            ) {
                if (rotation <= 90f) {
                    CardFront(
                        name = student.studentName,
                        apaarId = student.apaarId,
                        programme = program?.programName ?: student.programId,
                        institution = institution?.name ?: student.institutionId,
                        institutionId = student.institutionId,
                        rollNo = student.studentInstituteRollNo,
                        academicYear = student.academicYear,
                        photoSeed = student.photoSeed,
                        initials = student.initials,
                        supernumerary = student.admissionQuota.isSupernumerary
                    )
                } else if (cardMatrix != null) {
                    CardBack(
                        matrix = cardMatrix,
                        seal = cardSeal,
                        abcAccountId = student.abcAccountId,
                        quota = student.admissionQuota.label,
                        nationality = student.nationality,
                        passport = student.passportNumber,
                        enrollmentDate = student.enrollmentDate
                    )
                }
            }
        }

        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center
            ) {
                StatusPill(
                    text = if (flipped) "Tap the card to return to the front" else "Tap the card to flip",
                    container = MaterialTheme.colorScheme.surfaceContainerHigh,
                    content = MaterialTheme.colorScheme.onSurfaceVariant,
                    icon = Icons.Filled.Cached
                )
            }
        }

        val flags = state.identityAnomalies
        if (flags.isNotEmpty()) {
            item {
                InfoBanner(
                    title = "${flags.size} regulatory flag(s) on this credential",
                    message = flags.joinToString(" · ") { it.anomalyType.shortLabel },
                    tone = Tone.CRITICAL
                )
            }
        }

        item {
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(15.dp)) {
                    SectionHeader(
                        title = "Credential assertions",
                        subtitle = "Data attested by the issuing institution and the AICTE registry"
                    )
                    Spacer(Modifier.height(10.dp))
                    Assertion("APAAR identifier", ApaarIdValidator.formatWithSeparator(student.apaarId), true)
                    Assertion("Holder", student.studentName)
                    Assertion("Issuing institution", institution?.name ?: student.institutionId)
                    Assertion("Programme", program?.programName ?: student.programId)
                    Assertion("Academic year", student.academicYear)
                    Assertion("Date of birth", student.dateOfBirth)
                    Assertion("Admission category", student.admissionQuota.label)
                    Assertion("Nationality", student.nationality)
                    Assertion("Enrolment date", student.enrollmentDate)
                    Assertion("Seal (SHA-256 / 32)", seal.orEmpty(), true)
                }
            }
        }

        item {
            Text(
                text = "This card is issued by the AICTE national APAAR registry. The QR payload carries a " +
                    "tamper-evident seal; any alteration of the underlying enrolment changes the seal and " +
                    "is detected during third-party verification.",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.outline
            )
        }
    }
}

/**
 * The front face of the APAAR card.
 */
@Composable
private fun CardFront(
    name: String,
    apaarId: String,
    programme: String,
    institution: String,
    institutionId: String,
    rollNo: String,
    academicYear: String,
    photoSeed: Int,
    initials: String,
    supernumerary: Boolean
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Brush.verticalGradient(listOf(NavyDeep, NavyPrimary, NavyDeep)))
            .padding(18.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(Color.White.copy(alpha = 0.13f))
                    .border(1.dp, Saffron.copy(alpha = 0.6f), RoundedCornerShape(12.dp)),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Filled.Badge, contentDescription = null, tint = Saffron, modifier = Modifier.size(22.dp))
            }
            Spacer(Modifier.width(11.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "APAAR",
                    style = MaterialTheme.typography.titleMedium,
                    color = Color.White,
                    letterSpacing = 2.4.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "ACADEMIC IDENTITY CARD · AICTE",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.White.copy(alpha = 0.72f),
                    letterSpacing = 0.6.sp
                )
            }
            if (supernumerary) {
                StatusPill(
                    text = "SUPER",
                    container = Saffron.copy(alpha = 0.2f),
                    content = Saffron
                )
            }
        }

        Spacer(Modifier.height(18.dp))

        Row(verticalAlignment = Alignment.CenterVertically) {
            StudentAvatar(
                initials = initials,
                seed = photoSeed,
                size = 58.dp
            )
            Spacer(Modifier.width(14.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = name,
                    style = MaterialTheme.typography.titleLarge,
                    color = Color.White,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                Spacer(Modifier.height(3.dp))
                Text(
                    text = programme,
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.White.copy(alpha = 0.78f),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Text(
                    text = institution,
                    style = MaterialTheme.typography.labelSmall,
                    color = Saffron,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }

        Spacer(Modifier.height(18.dp))

        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(1.dp)
                .background(Color.White.copy(alpha = 0.18f))
        )

        Spacer(Modifier.height(14.dp))

        Row {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "APAAR ID",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.White.copy(alpha = 0.6f),
                    letterSpacing = 0.8.sp
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = ApaarIdValidator.formatWithSeparator(apaarId),
                    style = MaterialTheme.typography.titleMedium,
                    color = Color.White,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 1.sp
                )
            }
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "ROLL NO",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.White.copy(alpha = 0.6f),
                    letterSpacing = 0.8.sp
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = rollNo,
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.White,
                    fontFamily = FontFamily.Monospace
                )
            }
        }

        Spacer(Modifier.height(12.dp))
        Text(
            text = "AICTE PID $institutionId · AY $academicYear",
            style = MaterialTheme.typography.labelSmall,
            color = Color.White.copy(alpha = 0.6f)
        )
    }
}

/**
 * The reverse face of the APAAR card — QR badge and cryptographic seal.
 */
@Composable
private fun CardBack(
    matrix: QrEncoder.QrMatrix,
    seal: String,
    abcAccountId: String?,
    quota: String,
    nationality: String,
    passport: String?,
    enrollmentDate: String
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                Brush.verticalGradient(
                    listOf(
                        MaterialTheme.colorScheme.surfaceContainerHigh,
                        MaterialTheme.colorScheme.surface
                    )
                )
            )
            .padding(18.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "VERIFIABLE CREDENTIAL",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            letterSpacing = 1.4.sp
        )
        Spacer(Modifier.height(12.dp))
        QrCodeView(matrix = matrix, size = 178.dp, backgroundColor = Color.White)
        Spacer(Modifier.height(12.dp))
        Text(
            text = "SCAN TO VERIFY AT apaar.aicte-india.gov.in",
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )
        Spacer(Modifier.height(10.dp))
        Text(
            text = seal.chunked(4).joinToString(" "),
            style = MaterialTheme.typography.labelSmall,
            color = NavyPrimary,
            fontFamily = FontFamily.Monospace,
            textAlign = TextAlign.Center
        )
        Spacer(Modifier.height(14.dp))
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(1.dp)
                .background(MaterialTheme.colorScheme.outlineVariant)
        )
        Spacer(Modifier.height(12.dp))
        BackRow("Admission category", quota)
        BackRow("Nationality", nationality)
        passport?.let { BackRow("Passport", it) }
        BackRow("Enrolment date", enrollmentDate)
        abcAccountId?.let { BackRow("ABC account", it) }
    }
}

@Composable
private fun BackRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 3.dp)
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.width(120.dp)
        )
        Text(
            text = value,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurface,
            fontWeight = FontWeight.Medium,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis
        )
    }
}

/**
 * A labelled assertion line on the credential summary card.
 */
@Composable
private fun Assertion(label: String, value: String, mono: Boolean = false) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 5.dp),
        verticalAlignment = Alignment.Top
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.width(136.dp)
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface,
            fontWeight = FontWeight.Medium,
            fontFamily = if (mono) FontFamily.Monospace else FontFamily.SansSerif,
            modifier = Modifier.weight(1f)
        )
    }
}
