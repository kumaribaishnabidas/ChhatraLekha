package com.acadentrix.app.ui.screens.role

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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AccountBalance
import androidx.compose.material.icons.filled.Badge
import androidx.compose.material.icons.filled.QrCodeScanner
import androidx.compose.material.icons.filled.School
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.acadentrix.core.model.UserRole
import com.acadentrix.app.ui.components.ChhatraLekhaPlate
import com.acadentrix.app.ui.components.ChhatraLekhaLockup
import com.acadentrix.app.ui.components.RoleCard
import com.acadentrix.app.ui.theme.ApaarTheme
import com.acadentrix.app.ui.theme.NavyDeep
import com.acadentrix.app.ui.theme.NavyPrimary
import com.acadentrix.app.ui.theme.Saffron
import com.acadentrix.app.ui.viewmodel.ApaarViewModel

/**
 * Entry point of the portal — lets every stakeholder pick their workspace.
 */
@Composable
fun RoleSelectScreen(viewModel: ApaarViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val colors = ApaarTheme.colors

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .verticalScroll(rememberScrollState())
    ) {
        // ------------------------------------------------------- hero banner
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    Brush.verticalGradient(
                        listOf(NavyDeep, NavyPrimary, NavyDeep)
                    )
                )
                .padding(horizontal = 20.dp, vertical = 26.dp)
        ) {
            Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ChhatraLekhaPlate(markSize = 26.dp, platePadding = 8.dp, radius = 13.dp)
                    Spacer(Modifier.width(12.dp))
                    Column {
                        Text(
                            text = "MINISTRY OF EDUCATION · AICTE",
                            style = MaterialTheme.typography.labelSmall,
                            color = Color.White.copy(alpha = 0.75f),
                            letterSpacing = 1.1.sp
                        )
                        Text(
                            text = "EDUSYNC",
                            style = MaterialTheme.typography.headlineMedium,
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 2.sp
                        )
                        Text(
                            text = "APAAR ID platform",
                            style = MaterialTheme.typography.labelSmall,
                            color = Color.White.copy(alpha = 0.70f),
                            letterSpacing = 1.4.sp
                        )
                    }
                }
                Spacer(Modifier.height(18.dp))
                Text(
                    text = "Automated Permanent Academic Account Registry",
                    style = MaterialTheme.typography.titleSmall,
                    color = Saffron,
                    fontWeight = FontWeight.SemiBold
                )
                Spacer(Modifier.height(6.dp))
                Text(
                    text = "One Nation, One Student ID — a single national academic identifier for every " +
                        "AICTE-approved institution, with real-time intake validation, supernumerary " +
                        "quota enforcement and tamper-evident credential verification.",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.White.copy(alpha = 0.82f)
                )
                Spacer(Modifier.height(18.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    HeroStat("${state.kpis.institutionCount}", "Institutions")
                    HeroStat("${state.kpis.totalEnrolled}", "Enrolled")
                    HeroStat("${state.kpis.flaggedAnomalies}", "Flags")
                }
            }
        }

        // -------------------------------------------------- workspace picker
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = "SELECT YOUR WORKSPACE",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                letterSpacing = 1.2.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(Modifier.height(12.dp))

            RoleCard(
                title = UserRole.AICTE_DIRECTORATE.label,
                tagline = UserRole.AICTE_DIRECTORATE.tagline,
                icon = Icons.Filled.AccountBalance,
                accent = NavyPrimary,
                modifier = Modifier.fillMaxWidth()
            ) { viewModel.selectRole(UserRole.AICTE_DIRECTORATE) }

            Spacer(Modifier.height(10.dp))

            RoleCard(
                title = UserRole.INSTITUTION.label,
                tagline = UserRole.INSTITUTION.tagline,
                icon = Icons.Filled.School,
                accent = Saffron,
                modifier = Modifier.fillMaxWidth()
            ) { viewModel.selectRole(UserRole.INSTITUTION) }

            Spacer(Modifier.height(10.dp))

            RoleCard(
                title = UserRole.VERIFIER.label,
                tagline = UserRole.VERIFIER.tagline,
                icon = Icons.Filled.QrCodeScanner,
                accent = colors.success,
                modifier = Modifier.fillMaxWidth()
            ) { viewModel.selectRole(UserRole.VERIFIER) }

            Spacer(Modifier.height(10.dp))

            RoleCard(
                title = UserRole.STUDENT.label,
                tagline = UserRole.STUDENT.tagline,
                icon = Icons.Filled.Badge,
                accent = colors.info,
                modifier = Modifier.fillMaxWidth()
            ) { viewModel.selectRole(UserRole.STUDENT) }

            Spacer(Modifier.height(22.dp))

            // ------------------------------------------------ regulatory notice
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(16.dp))
                    .background(colors.infoContainer.copy(alpha = 0.55f))
                    .border(1.dp, colors.info.copy(alpha = 0.22f), RoundedCornerShape(16.dp))
                    .padding(14.dp)
            ) {
                Column {
                    Text(
                        text = "REGULATORY BASIS",
                        style = MaterialTheme.typography.labelSmall,
                        color = colors.info,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.9.sp
                    )
                    Spacer(Modifier.height(5.dp))
                    Text(
                        text = "NEP 2020 · AICTE Approval Process Handbook (APH) · AICTE Approval Process " +
                            "Handbook supernumerary ceilings: NRI 5%, OCI / Foreign National 15%, " +
                            "TFW 5%, PMSSS capped per course.",
                        style = MaterialTheme.typography.bodySmall,
                        color = colors.onInfoContainer
                    )
                }
            }

            Spacer(Modifier.height(18.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                ChhatraLekhaLockup(
                    markSize = 22.dp,
                    wordColor = MaterialTheme.colorScheme.onSurface,
                    subColor = MaterialTheme.colorScheme.onSurfaceVariant,
                    subText = "ChhatraLekha v1.0.0",
                    onWhite = true
                )
            }
            Spacer(Modifier.height(10.dp))
        }
    }
}

@Composable
private fun HeroStat(value: String, label: String) {
    Column(
        modifier = Modifier
            .clip(RoundedCornerShape(12.dp))
            .background(Color.White.copy(alpha = 0.10f))
            .padding(horizontal = 14.dp, vertical = 8.dp)
    ) {
        Text(
            text = value,
            style = MaterialTheme.typography.titleLarge,
            color = Color.White,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = Color.White.copy(alpha = 0.7f)
        )
    }
}
