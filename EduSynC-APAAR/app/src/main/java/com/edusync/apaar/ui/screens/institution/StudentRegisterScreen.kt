package com.edusync.apaar.ui.screens.institution

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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.edusync.apaar.core.model.AdmissionQuota
import com.edusync.apaar.core.model.Student
import com.edusync.apaar.core.validation.ApaarIdValidator
import com.edusync.apaar.ui.components.ApaarCard
import com.edusync.apaar.ui.components.DetailRow
import com.edusync.apaar.ui.components.EmptyState
import com.edusync.apaar.ui.components.QuotaChip
import com.edusync.apaar.ui.components.SearchField
import com.edusync.apaar.ui.components.StatusPill
import com.edusync.apaar.ui.components.StudentAvatar
import com.edusync.apaar.ui.components.VerificationBadge
import com.edusync.apaar.ui.theme.ApaarTheme
import com.edusync.apaar.ui.viewmodel.ApaarViewModel

/**
 * The searchable student register of an AICTE-approved institution.
 */
@Composable
fun StudentRegisterScreen(viewModel: ApaarViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val colors = ApaarTheme.colors
    var quotaFilter by remember { mutableStateOf<AdmissionQuota?>(null) }

    val students = state.institutionStudents.filter { student ->
        val query = state.registerSearch.trim()
        val matchesQuery = query.isEmpty() ||
            student.studentName.contains(query, ignoreCase = true) ||
            student.apaarId.contains(query, ignoreCase = true) ||
            student.studentInstituteRollNo.contains(query, ignoreCase = true) ||
            student.programId.contains(query, ignoreCase = true)
        val matchesQuota = quotaFilter == null || student.admissionQuota == quotaFilter
        matchesQuery && matchesQuota
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
                    text = "STUDENT REGISTER",
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.saffron,
                    letterSpacing = 1.2.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Enrolment Ledger",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(Modifier.height(3.dp))
                Text(
                    text = "${state.institutionStudents.size} active enrolments · " +
                        "${state.institutionAnomalies.size} open flag(s) on this institution",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        item {
            SearchField(
                value = state.registerSearch,
                onValueChange = { viewModel.setRegisterSearch(it) },
                placeholder = "Search name, APAAR ID, roll number or programme…"
            )
        }

        item {
            androidx.compose.foundation.lazy.LazyRow(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(7.dp)
            ) {
                item {
                    com.edusync.apaar.ui.components.ApaarFilterChip(
                        label = "All",
                        selected = quotaFilter == null,
                        onClick = { quotaFilter = null },
                        count = state.institutionStudents.size
                    )
                }
                items(AdmissionQuota.entries.toList()) { quota ->
                    com.edusync.apaar.ui.components.ApaarFilterChip(
                        label = quota.shortLabel,
                        selected = quotaFilter == quota,
                        onClick = { quotaFilter = quota },
                        count = state.institutionStudents.count { it.admissionQuota == quota }
                    )
                }
            }
        }

        if (students.isEmpty()) {
            item {
                EmptyState(
                    title = "No matching students",
                    message = "Adjust the search query or the quota filter.",
                    icon = Icons.Filled.Info
                )
            }
        }

        items(students.take(120), key = { it.recordId }) { student ->
            RegisterRow(
                student = student,
                programmeName = state.programs
                    .firstOrNull { it.institutionId == student.institutionId && it.programId == student.programId }
                    ?.programName
                    ?: student.programId,
                flagCount = state.anomalies.count { it.studentApaarId == student.apaarId }
            )
        }

        if (students.size > 120) {
            item {
                Text(
                    text = "+ ${students.size - 120} more enrolments — refine the search to narrow the ledger.",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.outline
                )
            }
        }
    }
}

/**
 * One register row with an expandable detail panel.
 */
@Composable
private fun RegisterRow(student: Student, programmeName: String, flagCount: Int) {
    val colors = ApaarTheme.colors
    var expanded by remember { mutableStateOf(false) }

    ApaarCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { expanded = !expanded },
                verticalAlignment = Alignment.CenterVertically
            ) {
                StudentAvatar(
                    initials = student.initials,
                    seed = student.photoSeed,
                    size = 40.dp
                )
                Spacer(Modifier.width(11.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = student.studentName,
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.onSurface,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Text(
                        text = "${ApaarIdValidator.format(student.apaarId)} · ${student.studentInstituteRollNo}",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Text(
                        text = programmeName,
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.outline,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }
                Spacer(Modifier.width(7.dp))
                Column(horizontalAlignment = Alignment.End) {
                    QuotaChip(student.admissionQuota)
                    Spacer(Modifier.height(4.dp))
                    Icon(
                        imageVector = if (expanded) Icons.Filled.ExpandLess else Icons.Filled.ExpandMore,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(17.dp)
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
                DetailRow(label = "APAAR ID", value = student.apaarId, mono = true)
                DetailRow(label = "Roll number", value = student.studentInstituteRollNo, mono = true)
                DetailRow(label = "Programme", value = programmeName)
                DetailRow(label = "Programme code", value = student.programId, mono = true)
                DetailRow(label = "Quota", value = "${student.admissionQuota.label} (${student.admissionQuota.code})")
                DetailRow(label = "Date of birth", value = student.dateOfBirth, mono = true)
                DetailRow(label = "Gender", value = student.gender.label)
                DetailRow(label = "Nationality", value = student.nationality)
                student.passportNumber?.let { DetailRow(label = "Passport", value = it, mono = true) }
                student.countryOfOrigin?.let { DetailRow(label = "Country of origin", value = it) }
                DetailRow(label = "Enrolled on", value = student.enrollmentDate, mono = true)
                DetailRow(label = "Academic year", value = student.academicYear, mono = true)
                student.abcAccountId?.let { DetailRow(label = "ABC account", value = it, mono = true) }
                Spacer(Modifier.height(8.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    VerificationBadge(student.verificationStatus)
                    if (flagCount > 0) {
                        Spacer(Modifier.width(7.dp))
                        StatusPill(
                            text = "$flagCount flag(s)",
                            container = colors.criticalContainer,
                            content = colors.onCriticalContainer
                        )
                    }
                }
            }
        }
    }
}
