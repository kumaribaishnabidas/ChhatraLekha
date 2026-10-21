package com.acadentrix.app.ui

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
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AccountBalance
import androidx.compose.material.icons.filled.Assignment
import androidx.compose.material.icons.filled.Badge
import androidx.compose.material.icons.filled.Dashboard
import androidx.compose.material.icons.filled.GridView
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.QrCodeScanner
import androidx.compose.material.icons.filled.School
import androidx.compose.material.icons.filled.SwapHoriz
import androidx.compose.material.icons.filled.UploadFile
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.filled.Workspaces
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.acadentrix.app.core.model.UserRole
import com.acadentrix.app.ui.components.EduSynCPlate
import com.acadentrix.app.ui.screens.aicte.AnomalyInspectorScreen
import com.acadentrix.app.ui.screens.aicte.AuditTrailScreen
import com.acadentrix.app.ui.screens.aicte.AicteDashboardScreen
import com.acadentrix.app.ui.screens.aicte.ComplianceMatrixScreen
import com.acadentrix.app.ui.screens.institution.CsvIngestionScreen
import com.acadentrix.app.ui.screens.institution.IntakeTrackerScreen
import com.acadentrix.app.ui.screens.institution.InstitutionOverviewScreen
import com.acadentrix.app.ui.screens.institution.ManualAdmissionScreen
import com.acadentrix.app.ui.screens.institution.StudentRegisterScreen
import com.acadentrix.app.ui.screens.role.RoleSelectScreen
import com.acadentrix.app.ui.screens.student.DegreeCertificateScreen
import com.acadentrix.app.ui.screens.student.ApaarCardScreen
import com.acadentrix.app.ui.screens.verifier.VerifierScreen
import com.acadentrix.app.ui.theme.ApaarTheme
import com.acadentrix.app.ui.theme.NavyDeep
import com.acadentrix.app.ui.theme.NavyPrimary
import com.acadentrix.app.ui.theme.Saffron
import com.acadentrix.app.ui.viewmodel.ApaarViewModel

object Routes {
    const val HOME = "home"
    const val AICTE_DASHBOARD = "aicte/dashboard"
    const val AICTE_ANOMALIES = "aicte/anomalies"
    const val AICTE_MATRIX = "aicte/matrix"
    const val AICTE_AUDIT = "aicte/audit"
    const val INST_OVERVIEW = "institution/overview"
    const val INST_INTAKE = "institution/intake"
    const val INST_CSV = "institution/csv"
    const val INST_MANUAL = "institution/manual"
    const val INST_REGISTER = "institution/register"
    const val VERIFIER = "verifier/verify"
    const val STUDENT_CARD = "student/card"
    const val STUDENT_CERTIFICATE = "student/certificate"
}

private data class NavItem(val route: String, val label: String, val icon: ImageVector)

private fun navItemsFor(role: UserRole): List<NavItem> = when (role) {
    UserRole.AICTE_DIRECTORATE -> listOf(
        NavItem(Routes.AICTE_DASHBOARD, "Dashboard", Icons.Filled.Dashboard),
        NavItem(Routes.AICTE_ANOMALIES, "Anomalies", Icons.Filled.Warning),
        NavItem(Routes.AICTE_MATRIX, "Matrix", Icons.Filled.GridView),
        NavItem(Routes.AICTE_AUDIT, "Audit", Icons.Filled.History)
    )
    UserRole.INSTITUTION -> listOf(
        NavItem(Routes.INST_OVERVIEW, "Overview", Icons.Filled.Assignment),
        NavItem(Routes.INST_INTAKE, "Intake", Icons.Filled.Workspaces),
        NavItem(Routes.INST_CSV, "Batch CSV", Icons.Filled.UploadFile),
        NavItem(Routes.INST_REGISTER, "Register", Icons.Filled.School)
    )
    UserRole.VERIFIER -> listOf(
        NavItem(Routes.VERIFIER, "Verify", Icons.Filled.QrCodeScanner)
    )
    UserRole.STUDENT -> listOf(
        NavItem(Routes.STUDENT_CARD, "My Card", Icons.Filled.Badge),
        NavItem(Routes.STUDENT_CERTIFICATE, "Certificate", Icons.Filled.AccountBalance)
    )
}

/**
 * Root of the multi-role portal.
 */
@Composable
fun ApaarApp(
    viewModel: ApaarViewModel,
    navController: NavHostController = rememberNavController()
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val role = state.role
    val items = navItemsFor(role)
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = backStackEntry?.destination?.route

    Scaffold(
        topBar = {
            ApaarHeader(
                role = role,
                onRoleChange = { next ->
                    viewModel.selectRole(next)
                    navController.navigate(
                        when (next) {
                            UserRole.AICTE_DIRECTORATE -> Routes.AICTE_DASHBOARD
                            UserRole.INSTITUTION -> Routes.INST_OVERVIEW
                            UserRole.VERIFIER -> Routes.VERIFIER
                            UserRole.STUDENT -> Routes.STUDENT_CARD
                        }
                    ) {
                        popUpTo(Routes.HOME) { inclusive = false }
                        launchSingleTop = true
                    }
                },
                onHome = {
                    navController.navigate(Routes.HOME) {
                        popUpTo(Routes.HOME) { inclusive = true }
                    }
                }
            )
        },
        bottomBar = {
            if (items.size > 1 || role != UserRole.VERIFIER) {
                NavigationBar(
                    containerColor = MaterialTheme.colorScheme.surface,
                    tonalElevation = 3.dp
                ) {
                    items.forEach { item ->
                        val selected = currentRoute == item.route
                        NavigationBarItem(
                            selected = selected,
                            onClick = {
                                if (!selected) {
                                    navController.navigate(item.route) {
                                        popUpTo(navController.graph.startDestinationId) { saveState = true }
                                        launchSingleTop = true
                                        restoreState = true
                                    }
                                }
                            },
                            icon = { Icon(item.icon, contentDescription = item.label) },
                            label = { Text(item.label, style = MaterialTheme.typography.labelSmall) },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = MaterialTheme.colorScheme.onPrimaryContainer,
                                selectedTextColor = MaterialTheme.colorScheme.primary,
                                indicatorColor = MaterialTheme.colorScheme.primaryContainer,
                                unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        )
                    }
                }
            }
        },
        contentWindowInsets = androidx.compose.foundation.layout.WindowInsets(0, 0, 0, 0)
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            ApaarNavHost(navController = navController, viewModel = viewModel)
        }
    }
}

/**
 * The AICTE-styled gradient header with the role switcher.
 */
@Composable
private fun ApaarHeader(
    role: UserRole,
    onRoleChange: (UserRole) -> Unit,
    onHome: () -> Unit
) {
    var expanded by remember { mutableStateOf(false) }
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(Brush.verticalGradient(listOf(NavyDeep, NavyPrimary)))
            .statusBarsPadding()
    ) {
        Column(modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                EduSynCPlate(markSize = 22.dp, platePadding = 7.dp, radius = 11.dp)
                Spacer(Modifier.width(11.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "ACADENTRIX",
                        style = MaterialTheme.typography.titleMedium,
                        color = Color.White,
                        letterSpacing = 1.4.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "by EduSynC · AICTE National Academic Identifier",
                        style = MaterialTheme.typography.labelSmall,
                        color = Color.White.copy(alpha = 0.72f),
                        letterSpacing = 0.4.sp
                    )
                }
                Box {
                    Row(
                        modifier = Modifier
                            .clip(CircleShape)
                            .background(Color.White.copy(alpha = 0.14f))
                            .border(1.dp, Color.White.copy(alpha = 0.22f), CircleShape)
                            .clickable { expanded = true }
                            .padding(start = 11.dp, end = 7.dp, top = 6.dp, bottom = 6.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            Icons.Filled.SwapHoriz,
                            contentDescription = "Switch role",
                            tint = Color.White,
                            modifier = Modifier.size(14.dp)
                        )
                        Spacer(Modifier.width(4.dp))
                        Text(
                            text = role.shortLabel,
                            style = MaterialTheme.typography.labelMedium,
                            color = Color.White,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                    DropdownMenu(
                        expanded = expanded,
                        onDismissRequest = { expanded = false },
                        containerColor = MaterialTheme.colorScheme.surface
                    ) {
                        UserRole.entries.forEach { candidate ->
                            DropdownMenuItem(
                                text = {
                                    Column {
                                        Text(
                                            candidate.shortLabel,
                                            style = MaterialTheme.typography.bodyMedium,
                                            fontWeight = if (candidate == role) FontWeight.Bold else FontWeight.Normal
                                        )
                                        Text(
                                            candidate.tagline,
                                            style = MaterialTheme.typography.labelSmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    }
                                },
                                leadingIcon = {
                                    Icon(
                                        when (candidate) {
                                            UserRole.AICTE_DIRECTORATE -> Icons.Filled.AccountBalance
                                            UserRole.INSTITUTION -> Icons.Filled.School
                                            UserRole.VERIFIER -> Icons.Filled.QrCodeScanner
                                            UserRole.STUDENT -> Icons.Filled.Person
                                        },
                                        contentDescription = null,
                                        tint = if (candidate == role) Saffron else MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                },
                                onClick = {
                                    expanded = false
                                    onRoleChange(candidate)
                                }
                            )
                        }
                        DropdownMenuItem(
                            text = { Text("Role selection screen", style = MaterialTheme.typography.bodyMedium) },
                            leadingIcon = {
                                Icon(Icons.Filled.Dashboard, contentDescription = null)
                            },
                            onClick = {
                                expanded = false
                                onHome()
                            }
                        )
                    }
                }
            }
        }
    }
}

/**
 * Nav graph wiring every role-specific screen.
 */
@Composable
private fun ApaarNavHost(
    navController: NavHostController,
    viewModel: ApaarViewModel
) {
    NavHost(navController = navController, startDestination = Routes.HOME) {
        composable(Routes.HOME) {
            RoleSelectScreen(viewModel = viewModel)
        }
        composable(Routes.AICTE_DASHBOARD) { AicteDashboardScreen(viewModel = viewModel) }
        composable(Routes.AICTE_ANOMALIES) { AnomalyInspectorScreen(viewModel = viewModel) }
        composable(Routes.AICTE_MATRIX) { ComplianceMatrixScreen(viewModel = viewModel) }
        composable(Routes.AICTE_AUDIT) { AuditTrailScreen(viewModel = viewModel) }
        composable(Routes.INST_OVERVIEW) { InstitutionOverviewScreen(viewModel = viewModel) }
        composable(Routes.INST_INTAKE) { IntakeTrackerScreen(viewModel = viewModel) }
        composable(Routes.INST_CSV) { CsvIngestionScreen(viewModel = viewModel) }
        composable(Routes.INST_MANUAL) { ManualAdmissionScreen(viewModel = viewModel) }
        composable(Routes.INST_REGISTER) { StudentRegisterScreen(viewModel = viewModel) }
        composable(Routes.VERIFIER) { VerifierScreen(viewModel = viewModel) }
        composable(Routes.STUDENT_CARD) { ApaarCardScreen(viewModel = viewModel) }
        composable(Routes.STUDENT_CERTIFICATE) { DegreeCertificateScreen(viewModel = viewModel) }
    }
}
