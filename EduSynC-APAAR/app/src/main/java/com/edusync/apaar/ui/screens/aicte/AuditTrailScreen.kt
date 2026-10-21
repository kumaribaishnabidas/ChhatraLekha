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
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.QrCodeScanner
import androidx.compose.material.icons.filled.School
import androidx.compose.material.icons.filled.UploadFile
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
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.edusync.apaar.core.model.AuditEntry
import com.edusync.apaar.core.security.SealGenerator
import com.edusync.apaar.ui.components.ApaarCard
import com.edusync.apaar.ui.components.EmptyState
import com.edusync.apaar.ui.components.FilterChipRow
import com.edusync.apaar.ui.components.StatusPill
import com.edusync.apaar.ui.theme.ApaarTheme
import com.edusync.apaar.ui.viewmodel.ApaarViewModel

/**
 * Categories used to slice the national audit trail.
 */
private enum class AuditCategory(val label: String) {
    ALL("All"),
    ADMISSIONS("Admissions"),
    VERIFICATION("Verification"),
    SYSTEM("System")
}

/**
 * The immutable regulatory audit trail of the national registry.
 */
@Composable
fun AuditTrailScreen(viewModel: ApaarViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val colors = ApaarTheme.colors
    var category by remember { mutableStateOf(AuditCategory.ALL) }

    val visible = state.auditTrail.filter { entry ->
        when (category) {
            AuditCategory.ALL -> true
            AuditCategory.ADMISSIONS -> entry.category == "ADMISSIONS"
            AuditCategory.VERIFICATION -> entry.category == "VERIFIED" ||
                entry.category == "FLAGGED" ||
                entry.category == "NOT_FOUND"
            AuditCategory.SYSTEM -> entry.category == "SYSTEM"
        }
    }

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
                    text = "REGULATORY AUDIT TRAIL",
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.saffron,
                    letterSpacing = 1.2.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Immutable Action Log",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(Modifier.height(3.dp))
                Text(
                    text = "Append-only record of every admission, verification and system action " +
                        "performed against the national APAAR registry.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        item {
            FilterChipRow(
                items = AuditCategory.entries.toList(),
                selected = category,
                onSelect = { category = it },
                labelOf = { it.label },
                countOf = { filter ->
                    state.auditTrail.count { entry ->
                        when (filter) {
                            AuditCategory.ALL -> true
                            AuditCategory.ADMISSIONS -> entry.category == "ADMISSIONS"
                            AuditCategory.VERIFICATION -> entry.category == "VERIFIED" ||
                                entry.category == "FLAGGED" || entry.category == "NOT_FOUND"
                            AuditCategory.SYSTEM -> entry.category == "SYSTEM"
                        }
                    }
                }
            )
        }

        if (visible.isEmpty()) {
            item {
                EmptyState(
                    title = "No entries in this category",
                    message = "Actions matching the selected category will be listed here.",
                    icon = Icons.Filled.History
                )
            }
        }

        items(visible, key = { it.logId }) { entry ->
            AuditRow(entry)
        }
    }
}

/**
 * One audit entry rendered as a timeline node.
 */
@Composable
private fun AuditRow(entry: AuditEntry) {
    val colors = ApaarTheme.colors
    val (icon, accent) = when (entry.action) {
        "BATCH_COMMIT" -> Pair(Icons.Filled.UploadFile, colors.saffron)
        "MANUAL_ADMISSION" -> Pair(Icons.Filled.School, colors.info)
        "CREDENTIAL_VERIFICATION" -> Pair(Icons.Filled.QrCodeScanner, colors.success)
        "INITIAL_SEED" -> Pair(Icons.Filled.AccountBalance, colors.navyDeep)
        else -> Pair(Icons.Filled.History, MaterialTheme.colorScheme.onSurfaceVariant)
    }

    ApaarCard(modifier = Modifier.fillMaxWidth()) {
        Row(modifier = Modifier.padding(13.dp), verticalAlignment = Alignment.Top) {
            Box(
                modifier = Modifier
                    .size(34.dp)
                    .clip(CircleShape)
                    .background(accent.copy(alpha = 0.13f))
                    .border(1.dp, accent.copy(alpha = 0.28f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    icon,
                    contentDescription = null,
                    tint = accent,
                    modifier = Modifier.size(16.dp)
                )
            }
            Spacer(Modifier.width(11.dp))
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = entry.action.replace('_', ' '),
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.onSurface,
                        modifier = Modifier.weight(1f)
                    )
                    StatusPill(
                        text = entry.category.replace('_', ' '),
                        container = MaterialTheme.colorScheme.surfaceContainerHigh,
                        content = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Spacer(Modifier.height(4.dp))
                Text(
                    text = entry.details,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(Modifier.height(6.dp))
                Text(
                    text = "Subject: ${entry.subject}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = "${entry.actor} · ${SealGenerator.formatTimestamp(entry.timestamp)}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.outline
                )
            }
        }
    }
}
