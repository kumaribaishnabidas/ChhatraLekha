package com.edusync.apaar.ui.screens.aicte

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
import androidx.compose.material.icons.filled.AccountBalance
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Insights
import androidx.compose.material.icons.filled.School
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.edusync.apaar.core.model.AnomalySeverity
import com.edusync.apaar.core.model.AnomalyType
import com.edusync.apaar.core.security.SealGenerator
import com.edusync.apaar.ui.components.ApaarCard
import com.edusync.apaar.ui.components.EmptyState
import com.edusync.apaar.ui.components.KpiCard
import com.edusync.apaar.ui.components.LabelledMeter
import com.edusync.apaar.ui.components.SectionHeader
import com.edusync.apaar.ui.components.StatusPill
import com.edusync.apaar.ui.theme.ApaarTheme
import com.edusync.apaar.ui.viewmodel.ApaarViewModel

/**
 * National command centre for the AICTE Central Directorate.
 */
@Composable
fun AicteDashboardScreen(viewModel: ApaarViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val colors = ApaarTheme.colors

    if (state.isLoading) {
        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text("Loading national registry…", style = MaterialTheme.typography.bodyMedium)
        }
        return
    }

    val kpis = state.kpis
    val severityCounts = state.anomalies.groupingBy { it.severity }.eachCount()

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(14.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            Column {
                Text(
                    text = "NATIONAL REGISTRY COMMAND CENTRE",
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.saffron,
                    letterSpacing = 1.2.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "AICTE Directorate Overview",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(Modifier.height(3.dp))
                Text(
                    text = "Live pan-India intake, quota compliance and anomaly surveillance across " +
                        "${kpis.institutionCount} approved institutions.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        item {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    KpiCard(
                        label = "Institutions",
                        value = kpis.institutionCount.toString(),
                        caption = "${kpis.programmeCount} sanctioned programmes",
                        accent = colors.navyDeep,
                        icon = Icons.Filled.AccountBalance,
                        modifier = Modifier.weight(1f)
                    )
                    KpiCard(
                        label = "Enrolled",
                        value = kpis.totalEnrolled.toString(),
                        caption = "${"%.1f".format(kpis.utilisationPercent)}% of sanctioned intake",
                        accent = colors.success,
                        icon = Icons.Filled.School,
                        modifier = Modifier.weight(1f)
                    )
                }
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    KpiCard(
                        label = "Open flags",
                        value = kpis.flaggedAnomalies.toString(),
                        caption = "Across every detection layer",
                        accent = colors.warning,
                        icon = Icons.Filled.Warning,
                        modifier = Modifier.weight(1f)
                    )
                    KpiCard(
                        label = "Critical",
                        value = kpis.criticalAnomalies.toString(),
                        caption = "Require directorate intervention",
                        accent = colors.critical,
                        icon = Icons.Filled.Error,
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        }

        item {
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(15.dp)) {
                    SectionHeader(
                        title = "Seat-bucket utilisation",
                        subtitle = "Sanctioned AICTE capacity vs. realised enrolment"
                    )
                    Spacer(Modifier.height(12.dp))
                    state.quotaDistribution.forEach { bucket ->
                        LabelledMeter(
                            label = bucket.label,
                            value = bucket.enrolled,
                            total = bucket.sanctioned,
                            caption = "${"%.0f".format(bucket.utilisation * 100)}% of sanctioned band"
                        )
                        Spacer(Modifier.height(11.dp))
                    }
                }
            }
        }

        item {
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(15.dp)) {
                    SectionHeader(
                        title = "Detection-layer breakdown",
                        subtitle = "Multi-layer regulatory anomaly engine"
                    )
                    Spacer(Modifier.height(12.dp))
                    val total = state.anomalies.size.coerceAtLeast(1)
                    listOf(
                        AnomalyType.DUPLICATE_CROSS_COLLEGE to "Cross-institution multi-enrolment",
                        AnomalyType.EXCESS_APPROVED_INTAKE to "Excess approved intake",
                        AnomalyType.SUPERNUMERARY_BREACH to "Supernumerary ceiling breach",
                        AnomalyType.INVALID_APAAR_FORMAT to "APAAR syntactic violation",
                        AnomalyType.UNSANCTIONED_PROGRAM to "Unsanctioned programme",
                        AnomalyType.INCONSISTENT_CATEGORY to "Inconsistent category data"
                    ).forEach { (type, label) ->
                        val count = state.anomalies.count { it.anomalyType == type }
                        LabelledMeter(
                            label = label,
                            value = count,
                            total = total,
                            caption = null,
                            color = if (count > 0) colors.warning else colors.success
                        )
                        Spacer(Modifier.height(10.dp))
                    }
                }
            }
        }

        item {
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(15.dp)) {
                    SectionHeader(
                        title = "Severity mix",
                        subtitle = "Open regulatory flags by enforcement weight"
                    )
                    Spacer(Modifier.height(11.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        AnomalySeverity.entries.forEach { severity ->
                            val count = severityCounts[severity] ?: 0
                            val accent = when (severity) {
                                AnomalySeverity.CRITICAL -> colors.critical
                                AnomalySeverity.HIGH -> colors.warning
                                AnomalySeverity.WARNING -> colors.saffron
                                AnomalySeverity.INFO -> colors.info
                            }
                            Column(
                                modifier = Modifier
                                    .weight(1f)
                                    .clip(RoundedCornerShape(12.dp))
                                    .background(accent.copy(alpha = 0.10f))
                                    .border(1.dp, accent.copy(alpha = 0.25f), RoundedCornerShape(12.dp))
                                    .padding(vertical = 9.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Text(
                                    text = count.toString(),
                                    style = MaterialTheme.typography.titleLarge,
                                    color = accent,
                                    fontWeight = FontWeight.Bold
                                )
                                Text(
                                    text = severity.label,
                                    style = MaterialTheme.typography.labelSmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }
                }
            }
        }

        item {
            SectionHeader(
                title = "Institutions under surveillance",
                subtitle = "Ranked by number of open regulatory flags"
            )
        }

        items(state.institutionsByRisk.take(6), key = { it.first.institutionId }) { (institution, flags) ->
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Row(
                    modifier = Modifier.padding(13.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .size(38.dp)
                            .clip(RoundedCornerShape(11.dp))
                            .background(colors.navyDeep.copy(alpha = 0.10f)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            Icons.Filled.Insights,
                            contentDescription = null,
                            tint = colors.navyDeep,
                            modifier = Modifier.size(19.dp)
                        )
                    }
                    Spacer(Modifier.width(11.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = institution.name,
                            style = MaterialTheme.typography.titleSmall,
                            color = MaterialTheme.colorScheme.onSurface,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                        Text(
                            text = "${institution.displayId} · ${institution.location}",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                    Spacer(Modifier.width(8.dp))
                    StatusPill(
                        text = if (flags == 0) "Clear" else "$flags flags",
                        container = if (flags == 0) colors.successContainer else colors.criticalContainer,
                        content = if (flags == 0) colors.onSuccessContainer else colors.onCriticalContainer
                    )
                }
            }
        }

        item {
            SectionHeader(
                title = "Recent regulatory activity",
                subtitle = "Immutable national audit trail"
            )
        }

        if (state.auditTrail.isEmpty()) {
            item {
                EmptyState(
                    title = "No audit entries yet",
                    message = "Regulatory actions taken in the portal are recorded here."
                )
            }
        } else {
            items(state.auditTrail.take(6), key = { it.logId }) { entry ->
                ApaarCard(modifier = Modifier.fillMaxWidth()) {
                    Row(modifier = Modifier.padding(13.dp), verticalAlignment = Alignment.Top) {
                        Box(
                            modifier = Modifier
                                .size(30.dp)
                                .clip(CircleShape)
                                .background(colors.info.copy(alpha = 0.12f)),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                Icons.Filled.History,
                                contentDescription = null,
                                tint = colors.info,
                                modifier = Modifier.size(15.dp)
                            )
                        }
                        Spacer(Modifier.width(10.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = entry.action.replace('_', ' '),
                                style = MaterialTheme.typography.titleSmall,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                            Text(
                                text = entry.details,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Spacer(Modifier.height(4.dp))
                            Text(
                                text = "${entry.actor} · ${SealGenerator.formatIso(entry.timestamp)}",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.outline
                            )
                        }
                    }
                }
            }
        }

        item {
            Spacer(Modifier.height(8.dp))
            Text(
                text = "Source: AICTE national APAAR registry (offline mirror) · All figures recomputed " +
                    "live by the multi-layer detection engine.",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.outline
            )
        }
    }
}
