package com.edusync.apaar.ui.screens.verifier

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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.QrCodeScanner
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Verified
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.edusync.apaar.core.model.AnomalySeverity
import com.edusync.apaar.core.qr.ApaarQrPayload
import com.edusync.apaar.core.qr.QrEncoder
import com.edusync.apaar.core.security.SealGenerator
import com.edusync.apaar.core.validation.ApaarIdValidator
import com.edusync.apaar.ui.components.ApaarCard
import com.edusync.apaar.ui.components.DetailRow
import com.edusync.apaar.ui.components.EmptyState
import com.edusync.apaar.ui.components.InfoBanner
import com.edusync.apaar.ui.components.QrCodeView
import com.edusync.apaar.ui.components.SectionHeader
import com.edusync.apaar.ui.components.SeverityBadge
import com.edusync.apaar.ui.components.StatusPill
import com.edusync.apaar.ui.components.StudentAvatar
import com.edusync.apaar.ui.components.Tone
import com.edusync.apaar.ui.theme.ApaarTheme
import com.edusync.apaar.ui.viewmodel.ApaarViewModel
import com.edusync.apaar.ui.viewmodel.VerificationDossier

/**
 * Third-party verifier / employer workspace.
 */
@Composable
fun VerifierScreen(viewModel: ApaarViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val dossier by viewModel.verification.collectAsState()
    val colors = ApaarTheme.colors

    var query by remember { mutableStateOf("") }
    val samples = remember(state.students.size) { viewModel.sampleVerificationQueries() }

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
                    text = "CREDENTIAL VERIFICATION",
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.saffron,
                    letterSpacing = 1.2.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Bonafide Credential Check",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(Modifier.height(3.dp))
                Text(
                    text = "Scan an APAAR QR badge or enter a 12-digit APAAR ID / institutional roll number. " +
                        "The dossier below is drawn from the AICTE national registry in real time.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        item {
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(14.dp)) {
                    OutlinedTextField(
                        value = query,
                        onValueChange = { query = it },
                        modifier = Modifier.fillMaxWidth(),
                        placeholder = {
                            Text(
                                "APAAR ID or institute roll number",
                                style = MaterialTheme.typography.bodySmall
                            )
                        },
                        leadingIcon = {
                            Icon(Icons.Filled.Search, contentDescription = null, modifier = Modifier.size(17.dp))
                        },
                        singleLine = true,
                        shape = RoundedCornerShape(12.dp),
                        textStyle = MaterialTheme.typography.bodyMedium.copy(fontFamily = FontFamily.Monospace),
                        colors = TextFieldDefaults.colors(
                            focusedContainerColor = MaterialTheme.colorScheme.surface,
                            unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                            focusedIndicatorColor = MaterialTheme.colorScheme.primary,
                            unfocusedIndicatorColor = MaterialTheme.colorScheme.outlineVariant
                        )
                    )
                    Spacer(Modifier.height(11.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                        Button(
                            onClick = { viewModel.verify(query) },
                            enabled = query.isNotBlank() && !state.isWorking,
                            shape = RoundedCornerShape(11.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = colors.navyDeep,
                                contentColor = Color.White
                            ),
                            modifier = Modifier.weight(1f)
                        ) {
                            Icon(Icons.Filled.Verified, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(Modifier.width(6.dp))
                            Text("Verify", style = MaterialTheme.typography.labelLarge)
                        }
                        OutlinedButton(
                            onClick = {
                                samples.firstOrNull()?.let {
                                    query = it
                                    viewModel.verify(it)
                                }
                            },
                            enabled = samples.isNotEmpty(),
                            shape = RoundedCornerShape(11.dp),
                            modifier = Modifier.weight(1f)
                        ) {
                            Icon(Icons.Filled.QrCodeScanner, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(Modifier.width(6.dp))
                            Text("Scan QR", style = MaterialTheme.typography.labelLarge)
                        }
                    }
                    if (samples.isNotEmpty()) {
                        Spacer(Modifier.height(9.dp))
                        Text(
                            text = "Demo identifiers: " + samples.joinToString("  ·  "),
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.outline
                        )
                    }
                }
            }
        }

        val current = dossier
        if (current != null) {
            item { DossierCard(current) }
        } else {
            item {
                EmptyState(
                    title = "No verification performed yet",
                    message = "Scan a QR badge or enter an identifier to produce a verification dossier.",
                    icon = Icons.Filled.QrCodeScanner
                )
            }
        }

        val verifications = state.auditTrail.filter { it.action == "CREDENTIAL_VERIFICATION" }
        if (verifications.isNotEmpty()) {
            item {
                SectionHeader(
                    title = "Verification log",
                    subtitle = "${verifications.size} attempt(s) recorded in the immutable audit trail"
                )
            }
            items(verifications.take(12), key = { it.logId }) { entry ->
                ApaarCard(modifier = Modifier.fillMaxWidth()) {
                    Row(modifier = Modifier.padding(12.dp), verticalAlignment = Alignment.Top) {
                        Box(
                            modifier = Modifier
                                .size(28.dp)
                                .clip(CircleShape)
                                .background(
                                    when (entry.category) {
                                        "VERIFIED" -> colors.success.copy(alpha = 0.13f)
                                        "FLAGGED" -> colors.critical.copy(alpha = 0.13f)
                                        else -> MaterialTheme.colorScheme.outline.copy(alpha = 0.13f)
                                    }
                                ),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                imageVector = when (entry.category) {
                                    "VERIFIED" -> Icons.Filled.CheckCircle
                                    "FLAGGED" -> Icons.Filled.Warning
                                    else -> Icons.Filled.Error
                                },
                                contentDescription = null,
                                tint = when (entry.category) {
                                    "VERIFIED" -> colors.success
                                    "FLAGGED" -> colors.critical
                                    else -> MaterialTheme.colorScheme.onSurfaceVariant
                                },
                                modifier = Modifier.size(14.dp)
                            )
                        }
                        Spacer(Modifier.width(10.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = entry.details,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                            Spacer(Modifier.height(3.dp))
                            Text(
                                text = "${entry.subject} · ${SealGenerator.formatTimestamp(entry.timestamp)}",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.outline,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                        }
                    }
                }
            }
        }
    }
}

/**
 * The verification dossier produced for a single identifier.
 */
@Composable
private fun DossierCard(dossier: VerificationDossier) {
    val colors = ApaarTheme.colors

    if (!dossier.found) {
        ApaarCard(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(15.dp)) {
                InfoBanner(
                    title = "No matching enrolment",
                    message = dossier.message.ifBlank { "The identifier is not present in the registry." },
                    tone = Tone.CRITICAL
                )
                Spacer(Modifier.height(10.dp))
                DetailRow(label = "Query", value = dossier.query, mono = true)
                DetailRow(label = "Checked at", value = SealGenerator.formatTimestamp(dossier.timestamp))
            }
        }
        return
    }

    val student = dossier.student ?: return
    val payload = ApaarQrPayload.build(
        apaarId = student.apaarId,
        institutionId = student.institutionId,
        programId = student.programId,
        seal = dossier.seal,
        timestamp = dossier.timestamp
    )
    val matrix = remember(payload) { QrEncoder.encode(payload) }

    ApaarCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(15.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                StudentAvatar(initials = student.initials, seed = student.photoSeed, size = 46.dp)
                Spacer(Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = student.studentName,
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Text(
                        text = ApaarIdValidator.format(student.apaarId),
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontFamily = FontFamily.Monospace
                    )
                }
                StatusPill(
                    text = if (dossier.anomalies.isEmpty()) "Verified" else "Flagged",
                    container = if (dossier.anomalies.isEmpty()) colors.successContainer else colors.criticalContainer,
                    content = if (dossier.anomalies.isEmpty()) colors.onSuccessContainer else colors.onCriticalContainer,
                    icon = if (dossier.anomalies.isEmpty()) Icons.Filled.CheckCircle else Icons.Filled.Warning
                )
            }

            Spacer(Modifier.height(14.dp))
            InfoBanner(
                title = if (dossier.anomalies.isEmpty()) "Credential confirmed" else "Regulatory flags open",
                message = dossier.message,
                tone = if (dossier.anomalies.isEmpty()) Tone.SUCCESS else Tone.CRITICAL
            )

            Spacer(Modifier.height(14.dp))
            DetailRow(label = "Institution", value = dossier.institution?.name ?: student.institutionId)
            DetailRow(label = "Institution PID", value = student.institutionId, mono = true)
            DetailRow(label = "Programme", value = dossier.program?.programName ?: student.programId)
            DetailRow(label = "Programme code", value = student.programId, mono = true)
            DetailRow(label = "Academic year", value = student.academicYear, mono = true)
            DetailRow(label = "Enrolled on", value = student.enrollmentDate, mono = true)
            DetailRow(label = "Roll number", value = student.studentInstituteRollNo, mono = true)
            DetailRow(label = "Quota", value = student.admissionQuota.label)
            DetailRow(label = "Nationality", value = student.nationality)

            Spacer(Modifier.height(14.dp))
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(14.dp))
                    .background(MaterialTheme.colorScheme.surfaceContainerLow)
                    .border(1.dp, colors.divider, RoundedCornerShape(14.dp))
                    .padding(14.dp)
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    QrCodeView(matrix = matrix, size = 168.dp)
                    Spacer(Modifier.height(10.dp))
                    Text(
                        text = "SCAN TO VERIFY",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        letterSpacing = 1.1.sp
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(
                        text = "Tamper-evident seal",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(Modifier.height(3.dp))
                    Text(
                        text = dossier.seal,
                        style = MaterialTheme.typography.labelSmall,
                        color = colors.navyDeep,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            if (dossier.duplicateInstitutions.size > 1) {
                Spacer(Modifier.height(12.dp))
                InfoBanner(
                    title = "Cross-institution enrolment detected",
                    message = "This APAAR ID is concurrently active at " +
                        dossier.duplicateInstitutions.joinToString(", ") { it.name } + ".",
                    tone = Tone.CRITICAL
                )
            }

            if (dossier.anomalies.isNotEmpty()) {
                Spacer(Modifier.height(14.dp))
                SectionHeader(
                    title = "Open regulatory flags",
                    subtitle = "${dossier.anomalies.size} finding(s) on this record"
                )
                Spacer(Modifier.height(9.dp))
                dossier.anomalies.forEach { anomaly ->
                    Column(modifier = Modifier.padding(bottom = 9.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            SeverityBadge(anomaly.severity)
                            Spacer(Modifier.width(7.dp))
                            Text(
                                text = anomaly.anomalyType.label,
                                style = MaterialTheme.typography.titleSmall,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                        }
                        Spacer(Modifier.height(3.dp))
                        Text(
                            text = anomaly.details,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    }
}
