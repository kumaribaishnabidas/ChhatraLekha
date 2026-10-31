package com.chhatralekha.app.ui.screens.aicte

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
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.GridView
import androidx.compose.material.icons.filled.School
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
import com.chhatralekha.core.model.AdmissionQuota
import com.chhatralekha.core.model.AnomalySeverity
import com.chhatralekha.core.model.IntakeSnapshot
import com.chhatralekha.app.ui.components.ApaarCard
import com.chhatralekha.app.ui.components.EmptyState
import com.chhatralekha.app.ui.components.InfoBanner
import com.chhatralekha.app.ui.components.LabelledMeter
import com.chhatralekha.app.ui.components.SectionHeader
import com.chhatralekha.app.ui.components.StatusPill
import com.chhatralekha.app.ui.components.Tone
import com.chhatralekha.app.ui.theme.ApaarTheme
import com.chhatralekha.app.ui.viewmodel.ApaarViewModel

/**
 * Institution × programme compliance matrix for the Directorate.
 */
@Composable
fun ComplianceMatrixScreen(viewModel: ApaarViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val colors = ApaarTheme.colors
    var expandedId by remember { mutableStateOf<String?>(null) }

    val byInstitution = state.snapshots.groupBy { it.program.institutionId }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(14.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        item {
            Column {
                Text(
                    text = "COMPLIANCE MATRIX",
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.saffron,
                    letterSpacing = 1.2.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Programme-wise Seat Compliance",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(Modifier.height(3.dp))
                Text(
                    text = "Sanctioned intake, supernumerary ceilings and live utilisation for every " +
                        "approved programme of every institution.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        item {
            InfoBanner(
                title = "Regulatory basis",
                message = "NRI ≤ 5% · OCI / Foreign National ≤ 15% · TFW ≤ 5% · PMSSS capped per course. " +
                    "A programme is compliant when regular enrolment is within the sanctioned intake and " +
                    "no supernumerary band exceeds its ceiling.",
                tone = Tone.INFO
            )
        }

        item {
            SectionHeader(
                title = "Institutions",
                subtitle = "${byInstitution.size} institutions · ${state.snapshots.size} programmes"
            )
        }

        if (byInstitution.isEmpty()) {
            item {
                EmptyState(
                    title = "No programme data",
                    message = "The registry has not been seeded yet.",
                    icon = Icons.Filled.GridView
                )
            }
        }

        items(byInstitution.entries.toList(), key = { it.key }) { (institutionId, snapshots) ->
            val institution = state.institutions.firstOrNull { it.institutionId == institutionId }
            val flags = state.anomalies.count { it.institutionId == institutionId }
            val critical = state.anomalies.count {
                it.institutionId == institutionId &&
                    (it.severity == AnomalySeverity.CRITICAL || it.severity == AnomalySeverity.HIGH)
            }
            val expanded = expandedId == institutionId
            val regularEnrolled = snapshots.sumOf { it.regularEnrolled }
            val regularSanctioned = snapshots.sumOf { it.program.approvedIntake }

            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(13.dp)) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { expandedId = if (expanded) null else institutionId },
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(36.dp)
                                .clip(RoundedCornerShape(11.dp))
                                .background(colors.navyDeep.copy(alpha = 0.10f)),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                Icons.Filled.School,
                                contentDescription = null,
                                tint = colors.navyDeep,
                                modifier = Modifier.size(18.dp)
                            )
                        }
                        Spacer(Modifier.width(10.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = institution?.name ?: institutionId,
                                style = MaterialTheme.typography.titleSmall,
                                color = MaterialTheme.colorScheme.onSurface,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                            Text(
                                text = "$institutionId · ${snapshots.size} programmes · ${institution?.state ?: ""}",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                        }
                        Spacer(Modifier.width(6.dp))
                        StatusPill(
                            text = if (flags == 0) "Clear" else "$flags flags",
                            container = if (flags == 0) colors.successContainer else colors.criticalContainer,
                            content = if (flags == 0) colors.onSuccessContainer else colors.onCriticalContainer
                        )
                        Spacer(Modifier.width(4.dp))
                        Icon(
                            imageVector = if (expanded) Icons.Filled.ExpandLess else Icons.Filled.ExpandMore,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.size(18.dp)
                        )
                    }

                    Spacer(Modifier.height(11.dp))
                    LabelledMeter(
                        label = "Regular intake (all programmes)",
                        value = regularEnrolled,
                        total = regularSanctioned,
                        caption = if (critical > 0) "$critical critical flag(s) require action" else null
                    )

                    if (expanded) {
                        Spacer(Modifier.height(12.dp))
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(1.dp)
                                .background(colors.divider)
                        )
                        snapshots.forEach { snapshot ->
                            ProgrammeMatrixRow(snapshot)
                            Spacer(Modifier.height(11.dp))
                        }
                    }
                }
            }
        }
    }
}

/**
 * One programme row of the compliance matrix.
 */
@Composable
private fun ProgrammeMatrixRow(snapshot: IntakeSnapshot) {
    val colors = ApaarTheme.colors
    val program = snapshot.program
    val nriOver = snapshot.nriEnrolled > program.maxSupernumeraryNri
    val ociOver = snapshot.ociFnEnrolled > program.maxSupernumeraryFnOci
    val tfwOver = snapshot.tfwEnrolled > program.maxSupernumeraryTfw
    val pmsssOver = snapshot.pmsssEnrolled > program.maxPmsss
    val anyOver = nriOver || ociOver || tfwOver || pmsssOver
    val regularOver = snapshot.regularEnrolled > program.approvedIntake

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(MaterialTheme.colorScheme.surfaceContainerLow)
            .border(
                1.dp,
                if (anyOver || regularOver) colors.critical.copy(alpha = 0.3f) else colors.divider,
                RoundedCornerShape(12.dp)
            )
            .padding(11.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = program.programName,
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.onSurface,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.weight(1f)
            )
            Spacer(Modifier.width(7.dp))
            StatusPill(
                text = program.programLevel,
                container = MaterialTheme.colorScheme.secondaryContainer,
                content = MaterialTheme.colorScheme.onSecondaryContainer
            )
        }
        Spacer(Modifier.height(2.dp))
        Text(
            text = program.programId,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(Modifier.height(9.dp))

        LabelledMeter(
            label = "Regular intake",
            value = snapshot.regularEnrolled,
            total = program.approvedIntake
        )
        Spacer(Modifier.height(8.dp))
        LabelledMeter(
            label = "NRI supernumerary (5%)",
            value = snapshot.nriEnrolled,
            total = program.maxSupernumeraryNri,
            caption = if (nriOver) "Ceiling breached" else null
        )
        Spacer(Modifier.height(8.dp))
        LabelledMeter(
            label = "OCI / Foreign National (15%)",
            value = snapshot.ociFnEnrolled,
            total = program.maxSupernumeraryFnOci,
            caption = if (ociOver) "Ceiling breached" else null
        )
        Spacer(Modifier.height(8.dp))
        LabelledMeter(
            label = "TFW supernumerary (5%)",
            value = snapshot.tfwEnrolled,
            total = program.maxSupernumeraryTfw,
            caption = if (tfwOver) "Ceiling breached" else null
        )
        Spacer(Modifier.height(8.dp))
        LabelledMeter(
            label = "PMSSS (capped)",
            value = snapshot.pmsssEnrolled,
            total = program.maxPmsss,
            caption = if (pmsssOver) "Ceiling breached" else null
        )

        Spacer(Modifier.height(9.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            StatusPill(
                text = "Total ${snapshot.totalEnrolled}",
                container = MaterialTheme.colorScheme.surfaceContainerHigh,
                content = MaterialTheme.colorScheme.onSurface
            )
            StatusPill(
                text = "Sanctioned ${program.totalSanctioned}",
                container = MaterialTheme.colorScheme.surfaceContainerHigh,
                content = MaterialTheme.colorScheme.onSurface
            )
        }
    }
}
