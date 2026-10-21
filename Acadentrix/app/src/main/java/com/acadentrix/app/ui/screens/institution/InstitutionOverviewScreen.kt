package com.acadentrix.app.ui.screens.institution

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
import androidx.compose.material.icons.filled.Assignment
import androidx.compose.material.icons.filled.Badge
import androidx.compose.material.icons.filled.Business
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.UploadFile
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.acadentrix.app.core.model.AnomalySeverity
import com.acadentrix.app.ui.components.ApaarCard
import com.acadentrix.app.ui.components.DetailRow
import com.acadentrix.app.ui.components.DropdownSelector
import com.acadentrix.app.ui.components.EmptyState
import com.acadentrix.app.ui.components.InfoBanner
import com.acadentrix.app.ui.components.KpiCard
import com.acadentrix.app.ui.components.LabelledMeter
import com.acadentrix.app.ui.components.SectionHeader
import com.acadentrix.app.ui.components.StatusPill
import com.acadentrix.app.ui.components.Tone
import com.acadentrix.app.ui.theme.ApaarTheme
import com.acadentrix.app.ui.viewmodel.ApaarViewModel

/**
 * Landing workspace of an AICTE-approved institution.
 */
@Composable
fun InstitutionOverviewScreen(viewModel: ApaarViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val colors = ApaarTheme.colors

    val institution = state.selectedInstitution
    val snapshots = state.institutionSnapshots
    val students = state.institutionStudents
    val flags = state.institutionAnomalies

    val regularEnrolled = snapshots.sumOf { it.regularEnrolled }
    val regularSanctioned = snapshots.sumOf { it.program.approvedIntake }
    val totalSanctioned = snapshots.sumOf { it.program.totalSanctioned }
    val supernumerary = students.count { it.admissionQuota.isSupernumerary }

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
                    text = "INSTITUTION WORKSPACE",
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.saffron,
                    letterSpacing = 1.2.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Admission Control Desk",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(Modifier.height(8.dp))
                DropdownSelector(
                    label = "Operating institution",
                    options = state.institutions,
                    selected = institution,
                    onSelect = { viewModel.selectInstitution(it.institutionId) },
                    itemLabel = { "${it.name} · ${it.institutionId}" },
                    supporting = institution?.let { "${it.location} · AICTE PID ${it.institutionId}" }
                )
            }
        }

        if (institution == null) {
            item {
                EmptyState(
                    title = "No institution selected",
                    message = "Pick an institution to view its intake dashboard.",
                    icon = Icons.Filled.Business
                )
            }
            return@LazyColumn
        }

        item {
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(15.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(46.dp)
                                .clip(RoundedCornerShape(13.dp))
                                .background(colors.navyDeep),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                Icons.Filled.Badge,
                                contentDescription = null,
                                tint = colors.saffron,
                                modifier = Modifier.size(24.dp)
                            )
                        }
                        Spacer(Modifier.width(12.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = institution.name,
                                style = MaterialTheme.typography.titleMedium,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                            Text(
                                text = "${institution.institutionType.label} · Approved ${institution.approvalYear}",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        StatusPill(
                            text = "NAAC ${institution.naacGrade}",
                            container = colors.successContainer,
                            content = colors.onSuccessContainer
                        )
                    }
                    Spacer(Modifier.height(12.dp))
                    DetailRow(label = "AICTE PID", value = institution.institutionId, mono = true)
                    DetailRow(label = "Location", value = institution.location)
                    DetailRow(label = "Affiliating university", value = institution.affiliationUniversity)
                }
            }
        }

        item {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    KpiCard(
                        label = "Enrolled",
                        value = students.size.toString(),
                        caption = "$supernumerary supernumerary",
                        accent = colors.success,
                        modifier = Modifier.weight(1f)
                    )
                    KpiCard(
                        label = "Sanctioned",
                        value = totalSanctioned.toString(),
                        caption = "$regularSanctioned regular seats",
                        accent = colors.navyDeep,
                        modifier = Modifier.weight(1f)
                    )
                }
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    KpiCard(
                        label = "Regular use",
                        value = "${if (regularSanctioned == 0) 0 else (regularEnrolled * 100 / regularSanctioned)}%",
                        caption = "$regularEnrolled of $regularSanctioned seats",
                        accent = colors.saffron,
                        modifier = Modifier.weight(1f)
                    )
                    KpiCard(
                        label = "Open flags",
                        value = flags.size.toString(),
                        caption = "${flags.count { it.severity == AnomalySeverity.CRITICAL }} critical",
                        accent = if (flags.isEmpty()) colors.success else colors.critical,
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        }

        if (flags.isNotEmpty()) {
            item {
                InfoBanner(
                    title = "${flags.size} regulatory flag(s) open",
                    message = flags.take(3).joinToString(" · ") { it.anomalyType.shortLabel } +
                        if (flags.size > 3) " · +${flags.size - 3} more" else "",
                    tone = Tone.CRITICAL
                )
            }
        }

        item {
            SectionHeader(
                title = "Quick actions",
                subtitle = "Onboard and audit this institution's admissions"
            )
        }

        item {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                ActionCard(
                    icon = Icons.Filled.UploadFile,
                    title = "Batch CSV",
                    caption = "Bulk intake",
                    accent = colors.saffron,
                    modifier = Modifier.weight(1f)
                )
                ActionCard(
                    icon = Icons.Filled.Assignment,
                    title = "Manual entry",
                    caption = "Single admission",
                    accent = colors.info,
                    modifier = Modifier.weight(1f)
                )
            }
        }

        item {
            SectionHeader(
                title = "Programme intake",
                subtitle = "${snapshots.size} approved programmes"
            )
        }

        if (snapshots.isEmpty()) {
            item {
                EmptyState(
                    title = "No approved programmes",
                    message = "This institution has no sanctioned programme codes in the registry.",
                    icon = Icons.Filled.Assignment
                )
            }
        }

        items(snapshots, key = { it.program.programId }) { snapshot ->
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(13.dp)) {
                    Text(
                        text = snapshot.program.programName,
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.onSurface,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                    Text(
                        text = "${snapshot.program.programId} · ${snapshot.program.programLevel}",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(Modifier.height(10.dp))
                    LabelledMeter(
                        label = "Regular intake",
                        value = snapshot.regularEnrolled,
                        total = snapshot.program.approvedIntake
                    )
                    Spacer(Modifier.height(8.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        StatusPill(
                            text = "Super ${snapshot.supernumeraryEnrolled}",
                            container = MaterialTheme.colorScheme.surfaceContainerHigh,
                            content = MaterialTheme.colorScheme.onSurface
                        )
                        StatusPill(
                            text = "Total ${snapshot.totalEnrolled}/${snapshot.program.totalSanctioned}",
                            container = if (snapshot.hasBreach) {
                                colors.criticalContainer
                            } else {
                                colors.successContainer
                            },
                            content = if (snapshot.hasBreach) {
                                colors.onCriticalContainer
                            } else {
                                colors.onSuccessContainer
                            }
                        )
                        if (snapshot.hasBreach) {
                            Icon(
                                Icons.Filled.Warning,
                                contentDescription = "Ceiling breach",
                                tint = colors.critical,
                                modifier = Modifier.size(15.dp)
                            )
                        }
                    }
                }
            }
        }
    }
}

/**
 * A tappable action tile.
 */
@Composable
private fun ActionCard(
    icon: ImageVector,
    title: String,
    caption: String,
    accent: Color,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .background(MaterialTheme.colorScheme.surface)
            .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(16.dp))
            .padding(13.dp)
    ) {
        Box(
            modifier = Modifier
                .size(34.dp)
                .clip(RoundedCornerShape(10.dp))
                .background(accent.copy(alpha = 0.13f)),
            contentAlignment = Alignment.Center
        ) {
            Icon(icon, contentDescription = null, tint = accent, modifier = Modifier.size(18.dp))
        }
        Spacer(Modifier.height(9.dp))
        Text(
            text = title,
            style = MaterialTheme.typography.titleSmall,
            color = MaterialTheme.colorScheme.onSurface
        )
        Text(
            text = caption,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}
