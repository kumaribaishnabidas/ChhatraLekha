package com.edusync.apaar.ui.screens.institution

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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Error
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.edusync.apaar.core.model.AdmissionQuota
import com.edusync.apaar.core.model.IntakeSnapshot
import com.edusync.apaar.ui.components.AnimatedGauge
import com.edusync.apaar.ui.components.ApaarCard
import com.edusync.apaar.ui.components.DropdownSelector
import com.edusync.apaar.ui.components.EmptyState
import com.edusync.apaar.ui.components.InfoBanner
import com.edusync.apaar.ui.components.LabelledMeter
import com.edusync.apaar.ui.components.QuotaChip
import com.edusync.apaar.ui.components.SectionHeader
import com.edusync.apaar.ui.components.StatusPill
import com.edusync.apaar.ui.components.Tone
import com.edusync.apaar.ui.theme.ApaarTheme
import com.edusync.apaar.ui.viewmodel.ApaarViewModel

/**
 * Live department-wise intake tracker for an institution.
 */
@Composable
fun IntakeTrackerScreen(viewModel: ApaarViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val colors = ApaarTheme.colors

    val snapshots = state.institutionSnapshots
    var selectedProgramId by remember { mutableStateOf<String?>(null) }
    val selected = snapshots.firstOrNull { it.program.programId == selectedProgramId }
        ?: snapshots.firstOrNull()

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
                    text = "INTAKE TRACKER",
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.saffron,
                    letterSpacing = 1.2.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Department-wise Seat Consumption",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(Modifier.height(8.dp))
                DropdownSelector(
                    label = "Programme",
                    options = snapshots.map { it.program.programId },
                    selected = selected?.program?.programId,
                    onSelect = { selectedProgramId = it },
                    itemLabel = { code ->
                        snapshots.firstOrNull { it.program.programId == code }
                            ?.program?.programName ?: code
                    },
                    supporting = selected?.let { "${it.program.approvedIntake} sanctioned regular seats" }
                )
            }
        }

        if (selected == null) {
            item {
                EmptyState(
                    title = "No programme selected",
                    message = "This institution has no approved programme to track.",
                    icon = Icons.Filled.Warning
                )
            }
            return@LazyColumn
        }

        item {
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = selected.program.programName,
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Text(
                        text = "${selected.program.programId} · ${selected.program.programLevel} · " +
                            "AY 2024-25",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(Modifier.height(16.dp))

                    val fraction = if (selected.program.approvedIntake == 0) 0f
                    else selected.regularEnrolled.toFloat() / selected.program.approvedIntake
                    val animated by animateFloatAsState(
                        targetValue = fraction,
                        animationSpec = tween(900),
                        label = "intakeFraction"
                    )

                    AnimatedGauge(
                        fraction = animated,
                        diameter = 176.dp,
                        centerContent = {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text(
                                    text = "${(animated * 100).toInt()}%",
                                    style = MaterialTheme.typography.displaySmall,
                                    color = MaterialTheme.colorScheme.onSurface,
                                    fontWeight = FontWeight.Bold
                                )
                                Text(
                                    text = "${selected.regularEnrolled} / ${selected.program.approvedIntake}",
                                    style = MaterialTheme.typography.labelMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                                Spacer(Modifier.height(4.dp))
                                Text(
                                    text = if (selected.regularOverflow > 0) {
                                        "+${selected.regularOverflow} OVER"
                                    } else {
                                        "${selected.program.approvedIntake - selected.regularEnrolled} FREE"
                                    },
                                    style = MaterialTheme.typography.labelSmall,
                                    color = if (selected.regularOverflow > 0) colors.critical else colors.success,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }
                    )

                    Spacer(Modifier.height(16.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        StatusPill(
                            text = "Regular ${selected.regularEnrolled}",
                            container = MaterialTheme.colorScheme.surfaceContainerHigh,
                            content = MaterialTheme.colorScheme.onSurface
                        )
                        StatusPill(
                            text = "Supernumerary ${selected.supernumeraryEnrolled}",
                            container = MaterialTheme.colorScheme.surfaceContainerHigh,
                            content = MaterialTheme.colorScheme.onSurface
                        )
                        StatusPill(
                            text = "Total ${selected.totalEnrolled}",
                            container = MaterialTheme.colorScheme.surfaceContainerHigh,
                            content = MaterialTheme.colorScheme.onSurface
                        )
                    }
                }
            }
        }

        if (selected.hasBreach) {
            item {
                InfoBanner(
                    title = "Sanctioned capacity breached",
                    message = buildString {
                        if (selected.regularOverflow > 0) {
                            append("Regular intake exceeds the sanctioned limit by ${selected.regularOverflow} seat(s). ")
                        }
                        if (selected.nriOverflow > 0) {
                            append("NRI supernumerary exceeds its 5% ceiling by ${selected.nriOverflow}. ")
                        }
                        if (selected.ociFnOverflow > 0) {
                            append("OCI / Foreign National band exceeds its 15% ceiling by ${selected.ociFnOverflow}. ")
                        }
                        if (selected.tfwOverflow > 0) {
                            append("TFW band exceeds its 5% ceiling by ${selected.tfwOverflow}. ")
                        }
                        if (selected.pmsssOverflow > 0) {
                            append("PMSSS allocation exceeds the course cap by ${selected.pmsssOverflow}.")
                        }
                    }.trim(),
                    tone = Tone.CRITICAL
                )
            }
        }

        item {
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(15.dp)) {
                    SectionHeader(
                        title = "Supernumerary ceilings",
                        subtitle = "AICTE Approval Process Handbook limits"
                    )
                    Spacer(Modifier.height(12.dp))
                    LabelledMeter(
                        label = "NRI supernumerary · max 5%",
                        value = selected.nriEnrolled,
                        total = selected.program.maxSupernumeraryNri,
                        caption = if (selected.nriOverflow > 0) {
                            "${selected.nriOverflow} seat(s) over the ceiling"
                        } else {
                            null
                        }
                    )
                    Spacer(Modifier.height(11.dp))
                    LabelledMeter(
                        label = "OCI / Foreign National · max 15%",
                        value = selected.ociFnEnrolled,
                        total = selected.program.maxSupernumeraryFnOci,
                        caption = if (selected.ociFnOverflow > 0) {
                            "${selected.ociFnOverflow} seat(s) over the ceiling"
                        } else {
                            null
                        }
                    )
                    Spacer(Modifier.height(11.dp))
                    LabelledMeter(
                        label = "Tuition Fee Waiver · max 5%",
                        value = selected.tfwEnrolled,
                        total = selected.program.maxSupernumeraryTfw,
                        caption = if (selected.tfwOverflow > 0) {
                            "${selected.tfwOverflow} seat(s) over the ceiling"
                        } else {
                            null
                        }
                    )
                    Spacer(Modifier.height(11.dp))
                    LabelledMeter(
                        label = "PMSSS · capped per course",
                        value = selected.pmsssEnrolled,
                        total = selected.program.maxPmsss,
                        caption = if (selected.pmsssOverflow > 0) {
                            "${selected.pmsssOverflow} seat(s) over the ceiling"
                        } else {
                            null
                        }
                    )
                }
            }
        }

        item {
            SectionHeader(
                title = "Programme roster",
                subtitle = "${selected.totalEnrolled} active enrolments in this programme"
            )
        }

        val roster = state.students
            .filter {
                it.isActive &&
                    it.institutionId == selected.program.institutionId &&
                    it.programId == selected.program.programId
            }
            .sortedWith(compareByDescending<com.edusync.apaar.core.model.Student> { it.admissionQuota.isRegular }
                .thenBy { it.enrollmentDate })

        if (roster.isEmpty()) {
            item {
                EmptyState(
                    title = "No enrolments yet",
                    message = "Onboard students through the batch CSV or manual admission flow.",
                    icon = Icons.Filled.Warning
                )
            }
        }

        items(roster.take(40), key = { it.recordId }) { student ->
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Row(modifier = Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = student.studentName,
                            style = MaterialTheme.typography.titleSmall,
                            color = MaterialTheme.colorScheme.onSurface,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                        Text(
                            text = "${student.studentInstituteRollNo} · ${student.enrollmentDate}",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                    Spacer(Modifier.width(8.dp))
                    QuotaChip(student.admissionQuota)
                }
            }
        }

        if (roster.size > 40) {
            item {
                Text(
                    text = "+ ${roster.size - 40} further enrolments — use the Register workspace for the full list.",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.outline
                )
            }
        }
    }
}
