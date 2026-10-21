package com.acadentrix.app.ui.screens.aicte

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
import androidx.compose.material.icons.filled.AccountBalance
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Search
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
import com.acadentrix.app.core.model.Anomaly
import com.acadentrix.app.core.model.AnomalySeverity
import com.acadentrix.app.ui.components.ApaarCard
import com.acadentrix.app.ui.components.DetailRow
import com.acadentrix.app.ui.components.EmptyState
import com.acadentrix.app.ui.components.FilterChipRow
import com.acadentrix.app.ui.components.InfoBanner
import com.acadentrix.app.ui.components.SearchField
import com.acadentrix.app.ui.components.SectionHeader
import com.acadentrix.app.ui.components.SeverityBadge
import com.acadentrix.app.ui.components.StatusPill
import com.acadentrix.app.ui.components.SummaryChip
import com.acadentrix.app.ui.components.Tone
import com.acadentrix.app.ui.theme.ApaarTheme
import com.acadentrix.app.ui.viewmodel.AnomalyFilter
import com.acadentrix.app.ui.viewmodel.ApaarViewModel

/**
 * The national anomaly inbox for the AICTE Directorate.
 */
@Composable
fun AnomalyInspectorScreen(viewModel: ApaarViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val colors = ApaarTheme.colors
    var search by remember { mutableStateOf("") }

    val visible = state.filteredAnomalies.filter { anomaly ->
        val query = search.trim()
        if (query.isEmpty()) {
            true
        } else {
            anomaly.studentApaarId.contains(query, ignoreCase = true) ||
                anomaly.institutionId.contains(query, ignoreCase = true) ||
                anomaly.anomalyType.label.contains(query, ignoreCase = true) ||
                anomaly.details.contains(query, ignoreCase = true)
        }
    }

    val criticalCount = state.anomalies.count {
        it.severity == AnomalySeverity.CRITICAL || it.severity == AnomalySeverity.HIGH
    }
    val warningCount = state.anomalies.count { it.severity == AnomalySeverity.WARNING }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(14.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Column {
                Text(
                    text = "NATIONAL ANOMALY INBOX",
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.saffron,
                    letterSpacing = 1.2.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Regulatory Flag Inspector",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(Modifier.height(3.dp))
                Text(
                    text = "Every finding is regenerated live by the four-layer detection engine.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                SummaryChip(
                    label = "Total",
                    value = state.anomalies.size.toString(),
                    tone = Tone.INFO,
                    modifier = Modifier.weight(1f)
                )
                SummaryChip(
                    label = "Critical",
                    value = criticalCount.toString(),
                    tone = Tone.CRITICAL,
                    modifier = Modifier.weight(1f)
                )
                SummaryChip(
                    label = "Warnings",
                    value = warningCount.toString(),
                    tone = Tone.WARNING,
                    modifier = Modifier.weight(1f)
                )
            }
        }

        item {
            SearchField(
                value = search,
                onValueChange = { search = it },
                placeholder = "Search by APAAR ID, institution or rule…"
            )
        }

        item {
            FilterChipRow(
                items = AnomalyFilter.entries.toList(),
                selected = state.anomalyFilter,
                onSelect = { viewModel.setAnomalyFilter(it) },
                labelOf = { it.label },
                countOf = { filter ->
                    when (filter) {
                        AnomalyFilter.ALL -> state.anomalies.size
                        AnomalyFilter.CRITICAL -> state.anomalies.count {
                            it.severity == AnomalySeverity.CRITICAL || it.severity == AnomalySeverity.HIGH
                        }
                        AnomalyFilter.DUPLICATE -> state.anomalies.count {
                            it.anomalyType == com.acadentrix.app.core.model.AnomalyType.DUPLICATE_CROSS_COLLEGE
                        }
                        AnomalyFilter.INTAKE -> state.anomalies.count {
                            it.anomalyType == com.acadentrix.app.core.model.AnomalyType.EXCESS_APPROVED_INTAKE
                        }
                        AnomalyFilter.SUPERNUMERARY -> state.anomalies.count {
                            it.anomalyType == com.acadentrix.app.core.model.AnomalyType.SUPERNUMERARY_BREACH
                        }
                        AnomalyFilter.DATA -> state.anomalies.count {
                            it.anomalyType == com.acadentrix.app.core.model.AnomalyType.INVALID_APAAR_FORMAT ||
                                it.anomalyType == com.acadentrix.app.core.model.AnomalyType.INCONSISTENT_CATEGORY ||
                                it.anomalyType == com.acadentrix.app.core.model.AnomalyType.UNSANCTIONED_PROGRAM
                        }
                    }
                }
            )
        }

        if (visible.isEmpty()) {
            item {
                EmptyState(
                    title = "No flags match this view",
                    message = "Adjust the filter or the search query to widen the inspection scope.",
                    icon = Icons.Filled.Info
                )
            }
        }

        items(visible, key = { it.anomalyId }) { anomaly ->
            AnomalyRow(
                anomaly = anomaly,
                institutionName = state.institutions
                    .firstOrNull { it.institutionId == anomaly.institutionId }
                    ?.name
                    ?: anomaly.institutionId
            )
        }
    }
}

/**
 * One anomaly record with an expandable forensic detail panel.
 */
@Composable
private fun AnomalyRow(anomaly: Anomaly, institutionName: String) {
    val colors = ApaarTheme.colors
    var expanded by remember { mutableStateOf(false) }
    val accent = when (anomaly.severity) {
        AnomalySeverity.CRITICAL -> colors.critical
        AnomalySeverity.HIGH -> colors.warning
        AnomalySeverity.WARNING -> colors.saffron
        AnomalySeverity.INFO -> colors.info
    }

    ApaarCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(13.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(32.dp)
                        .clip(CircleShape)
                        .background(accent.copy(alpha = 0.13f)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = when (anomaly.severity) {
                            AnomalySeverity.CRITICAL -> Icons.Filled.Error
                            AnomalySeverity.HIGH, AnomalySeverity.WARNING -> Icons.Filled.Warning
                            AnomalySeverity.INFO -> Icons.Filled.Info
                        },
                        contentDescription = null,
                        tint = accent,
                        modifier = Modifier.size(16.dp)
                    )
                }
                Spacer(Modifier.width(10.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = anomaly.anomalyType.label,
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.onSurface,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Text(
                        text = anomaly.anomalyType.description,
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                }
                Spacer(Modifier.width(6.dp))
                SeverityBadge(anomaly.severity)
            }

            Spacer(Modifier.height(10.dp))

            Row(verticalAlignment = Alignment.CenterVertically) {
                StatusPill(
                    text = com.acadentrix.app.core.validation.ApaarIdValidator.format(anomaly.studentApaarId),
                    container = MaterialTheme.colorScheme.surfaceContainerHigh,
                    content = MaterialTheme.colorScheme.onSurface
                )
                Spacer(Modifier.width(7.dp))
                Text(
                    text = institutionName,
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.weight(1f)
                )
                Box(
                    modifier = Modifier
                        .clip(CircleShape)
                        .clickable { expanded = !expanded }
                        .padding(3.dp)
                ) {
                    Icon(
                        imageVector = if (expanded) Icons.Filled.ExpandLess else Icons.Filled.ExpandMore,
                        contentDescription = if (expanded) "Collapse" else "Expand",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(18.dp)
                    )
                }
            }

            if (expanded) {
                Spacer(Modifier.height(10.dp))
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(1.dp)
                        .background(colors.divider)
                )
                Spacer(Modifier.height(8.dp))
                DetailRow(label = "APAAR ID", value = anomaly.studentApaarId, mono = true)
                DetailRow(label = "Institution", value = institutionName)
                DetailRow(label = "Institution PID", value = anomaly.institutionId, mono = true)
                DetailRow(label = "Programme", value = anomaly.programId ?: "—", mono = true)
                DetailRow(label = "Rule", value = anomaly.anomalyType.label)
                DetailRow(label = "Severity", value = anomaly.severity.label)
                Spacer(Modifier.height(6.dp))
                InfoBanner(
                    title = "Finding",
                    message = anomaly.details,
                    tone = when (anomaly.severity) {
                        AnomalySeverity.CRITICAL -> Tone.CRITICAL
                        AnomalySeverity.HIGH -> Tone.WARNING
                        AnomalySeverity.WARNING -> Tone.WARNING
                        AnomalySeverity.INFO -> Tone.INFO
                    }
                )
            }
        }
    }
}
