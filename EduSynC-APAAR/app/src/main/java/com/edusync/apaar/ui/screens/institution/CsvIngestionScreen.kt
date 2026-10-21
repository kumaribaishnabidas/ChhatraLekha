package com.edusync.apaar.ui.screens.institution

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
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.ContentCopy
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.UploadFile
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.edusync.apaar.core.csv.CsvIngestionReport
import com.edusync.apaar.core.csv.CsvStudentRow
import com.edusync.apaar.core.csv.RowIssue
import com.edusync.apaar.core.csv.RowIssueSeverity
import com.edusync.apaar.core.validation.ApaarIdValidator
import com.edusync.apaar.ui.components.ApaarCard
import com.edusync.apaar.ui.components.EmptyState
import com.edusync.apaar.ui.components.InfoBanner
import com.edusync.apaar.ui.components.SectionHeader
import com.edusync.apaar.ui.components.StatusPill
import com.edusync.apaar.ui.components.SummaryChip
import com.edusync.apaar.ui.components.Tone
import com.edusync.apaar.ui.theme.ApaarTheme
import com.edusync.apaar.ui.viewmodel.ApaarViewModel

/**
 * Batch CSV onboarding with a live parser and validator.
 */
@Composable
fun CsvIngestionScreen(viewModel: ApaarViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val csvInput by viewModel.csvInput.collectAsState()
    val report by viewModel.csvReport.collectAsState()
    val colors = ApaarTheme.colors

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
                    text = "BATCH ADMISSION ONBOARDING",
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.saffron,
                    letterSpacing = 1.2.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "CSV Intake Gateway",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(Modifier.height(3.dp))
                Text(
                    text = "Paste the AICTE batch file. Every row is validated live against the national " +
                        "registry, the sanctioned intake and the supernumerary ceilings before it can be committed.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        item {
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(14.dp)) {
                    SectionHeader(
                        title = "Batch payload",
                        subtitle = "Schema: APAAR_ID, Full_Name, DOB, Gender, Roll_No, Program_Code, " +
                            "Category, Nationality, Doc_Number"
                    )
                    Spacer(Modifier.height(10.dp))
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = 130.dp, max = 240.dp)
                            .clip(RoundedCornerShape(12.dp))
                            .background(MaterialTheme.colorScheme.surfaceContainerLow)
                            .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(12.dp))
                            .padding(10.dp)
                    ) {
                        androidx.compose.foundation.text.BasicTextField(
                            value = csvInput,
                            onValueChange = { viewModel.updateCsvInput(it) },
                            modifier = Modifier.fillMaxWidth(),
                            textStyle = MaterialTheme.typography.bodySmall.copy(
                                fontFamily = FontFamily.Monospace,
                                color = MaterialTheme.colorScheme.onSurface
                            ),
                            cursorBrush = androidx.compose.ui.graphics.SolidColor(colors.saffron),
                            decorationBox = { inner ->
                                if (csvInput.isBlank()) {
                                    Text(
                                        text = "Paste CSV rows here…",
                                        style = MaterialTheme.typography.bodySmall.copy(
                                            fontFamily = FontFamily.Monospace
                                        ),
                                        color = MaterialTheme.colorScheme.outline
                                    )
                                }
                                inner()
                            }
                        )
                    }
                    Spacer(Modifier.height(11.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                        Button(
                            onClick = { viewModel.validateCsv() },
                            enabled = csvInput.isNotBlank() && !state.isWorking,
                            shape = RoundedCornerShape(11.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = colors.navyDeep,
                                contentColor = androidx.compose.ui.graphics.Color.White
                            ),
                            modifier = Modifier.weight(1f)
                        ) {
                            Icon(Icons.Filled.UploadFile, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(Modifier.width(6.dp))
                            Text("Validate batch", style = MaterialTheme.typography.labelLarge)
                        }
                        OutlinedButton(
                            onClick = { viewModel.loadSampleCsv() },
                            shape = RoundedCornerShape(11.dp),
                            modifier = Modifier.weight(1f)
                        ) {
                            Icon(Icons.Filled.ContentCopy, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(Modifier.width(6.dp))
                            Text("Load sample", style = MaterialTheme.typography.labelLarge)
                        }
                    }
                }
            }
        }

        val current = report
        if (current != null) {
            item { ValidationSummary(current) }

            if (current.headerErrors.isNotEmpty()) {
                item {
                    InfoBanner(
                        title = "Header rejected",
                        message = current.headerErrors.joinToString(" "),
                        tone = Tone.CRITICAL
                    )
                }
            }

            if (current.programImpacts.isNotEmpty()) {
                item {
                    ApaarCard(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            SectionHeader(
                                title = "Seat impact preview",
                                subtitle = "Projected utilisation if this batch is committed"
                            )
                            Spacer(Modifier.height(11.dp))
                            current.programImpacts.forEach { impact ->
                                Column {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Text(
                                            text = impact.programCode,
                                            style = MaterialTheme.typography.titleSmall,
                                            color = MaterialTheme.colorScheme.onSurface,
                                            modifier = Modifier.weight(1f)
                                        )
                                        StatusPill(
                                            text = "${impact.projectedRegular}/${impact.approvedIntake} regular",
                                            container = if (impact.regularOverflow > 0) {
                                                colors.criticalContainer
                                            } else {
                                                colors.successContainer
                                            },
                                            content = if (impact.regularOverflow > 0) {
                                                colors.onCriticalContainer
                                            } else {
                                                colors.onSuccessContainer
                                            }
                                        )
                                    }
                                    Text(
                                        text = impact.programName,
                                        style = MaterialTheme.typography.labelSmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis
                                    )
                                    impact.capMessages.forEach { message ->
                                        Spacer(Modifier.height(5.dp))
                                        Row(verticalAlignment = Alignment.Top) {
                                            Icon(
                                                Icons.Filled.Warning,
                                                contentDescription = null,
                                                tint = colors.critical,
                                                modifier = Modifier.size(13.dp)
                                            )
                                            Spacer(Modifier.width(5.dp))
                                            Text(
                                                text = message,
                                                style = MaterialTheme.typography.labelSmall,
                                                color = colors.critical
                                            )
                                        }
                                    }
                                    Spacer(Modifier.height(12.dp))
                                }
                            }
                        }
                    }
                }
            }

            if (current.rows.isNotEmpty()) {
                item {
                    SectionHeader(
                        title = "Row-by-row validation",
                        subtitle = "${current.rows.size} data row(s) parsed"
                    )
                }
            }

            items(current.rows, key = { it.lineNumber }) { row ->
                RowCard(row)
            }

            item {
                Button(
                    onClick = {
                        viewModel.commitCsv { message -> viewModel.postMessage(message) }
                    },
                    enabled = current.committableRows.isNotEmpty() && !state.isWorking,
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = colors.success,
                        contentColor = androidx.compose.ui.graphics.Color.White
                    ),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Icon(Icons.Filled.CheckCircle, contentDescription = null, modifier = Modifier.size(17.dp))
                    Spacer(Modifier.width(8.dp))
                    Text(
                        text = "Commit ${current.committableRows.size} valid row(s) to the registry",
                        style = MaterialTheme.typography.labelLarge
                    )
                }
            }
        } else {
            item {
                EmptyState(
                    title = "No validation yet",
                    message = "Paste a batch and tap “Validate batch” to see the live row-by-row report.",
                    icon = Icons.Filled.Info
                )
            }
        }
    }
}

/**
 * The "38 Valid, 3 Critical Violations" summary strip.
 */
@Composable
private fun ValidationSummary(report: CsvIngestionReport) {
    val colors = ApaarTheme.colors
    Column(verticalArrangement = Arrangement.spacedBy(9.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            SummaryChip(
                label = "Valid",
                value = report.validRows.toString(),
                tone = Tone.SUCCESS,
                icon = Icons.Filled.CheckCircle,
                modifier = Modifier.weight(1f)
            )
            SummaryChip(
                label = "Critical",
                value = report.criticalRows.toString(),
                tone = Tone.CRITICAL,
                icon = Icons.Filled.Error,
                modifier = Modifier.weight(1f)
            )
            SummaryChip(
                label = "Warnings",
                value = report.warningRows.toString(),
                tone = Tone.WARNING,
                icon = Icons.Filled.Warning,
                modifier = Modifier.weight(1f)
            )
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            SummaryChip(
                label = "Rows",
                value = report.totalRows.toString(),
                tone = Tone.INFO,
                modifier = Modifier.weight(1f)
            )
            SummaryChip(
                label = "Duplicates",
                value = report.duplicateRows.toString(),
                tone = Tone.CRITICAL,
                modifier = Modifier.weight(1f)
            )
            SummaryChip(
                label = "Committable",
                value = report.committableRows.size.toString(),
                tone = Tone.SUCCESS,
                modifier = Modifier.weight(1f)
            )
        }
        if (report.unknownPrograms.isNotEmpty()) {
            InfoBanner(
                title = "Unrecognised programme code(s)",
                message = report.unknownPrograms.joinToString(", ") +
                    " — not sanctioned for the selected institution.",
                tone = Tone.CRITICAL
            )
        }
    }
}

/**
 * One parsed row with its issues.
 */
@Composable
private fun RowCard(row: CsvStudentRow) {
    val colors = ApaarTheme.colors
    val tone = when {
        row.criticalIssues.isNotEmpty() -> Tone.CRITICAL
        row.warningIssues.isNotEmpty() -> Tone.WARNING
        else -> Tone.SUCCESS
    }
    val accent = when (tone) {
        Tone.CRITICAL -> colors.critical
        Tone.WARNING -> colors.warning
        Tone.SUCCESS -> colors.success
        else -> colors.info
    }

    ApaarCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(13.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(24.dp)
                        .clip(CircleShape)
                        .background(accent.copy(alpha = 0.14f)),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = row.lineNumber.toString(),
                        style = MaterialTheme.typography.labelSmall,
                        color = accent,
                        fontWeight = FontWeight.Bold
                    )
                }
                Spacer(Modifier.width(9.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = row.fullName.ifBlank { "— unnamed row —" },
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.onSurface,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Text(
                        text = "${ApaarIdValidator.format(row.apaarId)} · ${row.programCode.ifBlank { "—" }}",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                StatusPill(
                    text = when (tone) {
                        Tone.CRITICAL -> "Blocked"
                        Tone.WARNING -> "Advisory"
                        else -> "Valid"
                    },
                    container = when (tone) {
                        Tone.CRITICAL -> colors.criticalContainer
                        Tone.WARNING -> colors.warningContainer
                        else -> colors.successContainer
                    },
                    content = when (tone) {
                        Tone.CRITICAL -> colors.onCriticalContainer
                        Tone.WARNING -> colors.onWarningContainer
                        else -> colors.onSuccessContainer
                    }
                )
            }

            if (row.issues.isNotEmpty()) {
                Spacer(Modifier.height(9.dp))
                row.issues.forEach { issue -> IssueLine(issue) }
            }
        }
    }
}

@Composable
private fun IssueLine(issue: RowIssue) {
    val colors = ApaarTheme.colors
    val accent = if (issue.severity == RowIssueSeverity.CRITICAL) colors.critical else colors.warning
    Row(modifier = Modifier.padding(vertical = 2.dp), verticalAlignment = Alignment.Top) {
        Box(
            modifier = Modifier
                .padding(top = 4.dp)
                .size(5.dp)
                .clip(CircleShape)
                .background(accent)
        )
        Spacer(Modifier.width(8.dp))
        Column {
            Text(
                text = issue.code,
                style = MaterialTheme.typography.labelSmall,
                color = accent,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = issue.message,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
