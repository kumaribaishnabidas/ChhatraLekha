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
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.PersonAdd
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.edusync.apaar.core.model.AdmissionQuota
import com.edusync.apaar.core.model.Gender
import com.edusync.apaar.core.validation.ApaarIdValidator
import com.edusync.apaar.ui.components.ApaarCard
import com.edusync.apaar.ui.components.DropdownSelector
import com.edusync.apaar.ui.components.InfoBanner
import com.edusync.apaar.ui.components.SectionHeader
import com.edusync.apaar.ui.components.Tone
import com.edusync.apaar.ui.theme.ApaarTheme
import com.edusync.apaar.ui.viewmodel.ApaarViewModel

/**
 * Manual single-student onboarding with live field validation.
 */
@Composable
fun ManualAdmissionScreen(viewModel: ApaarViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val errors by viewModel.manualErrors.collectAsState()
    val colors = ApaarTheme.colors

    var apaarId by remember { mutableStateOf("") }
    var fullName by remember { mutableStateOf("") }
    var dob by remember { mutableStateOf("") }
    var gender by remember { mutableStateOf(Gender.MALE) }
    var rollNo by remember { mutableStateOf("") }
    var programId by remember { mutableStateOf<String?>(null) }
    var quota by remember { mutableStateOf(AdmissionQuota.MERIT) }
    var nationality by remember { mutableStateOf("Indian") }
    var passport by remember { mutableStateOf("") }
    var country by remember { mutableStateOf("") }

    val validation = remember(apaarId) { ApaarIdValidator.validate(apaarId) }
    val programs = state.institutionPrograms

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
                    text = "MANUAL ADMISSION",
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.saffron,
                    letterSpacing = 1.2.sp,
                    fontWeight = androidx.compose.ui.text.font.FontWeight.Bold
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Single Enrolment Onboarding",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(Modifier.height(3.dp))
                Text(
                    text = "Onboard one student outside the batch flow. The record is validated against the " +
                        "APAAR structural rules and the live registry before it is written.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        item {
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(14.dp)) {
                    SectionHeader(
                        title = "Student identity",
                        subtitle = "Fields marked mandatory are enforced at submission"
                    )
                    Spacer(Modifier.height(12.dp))

                    ApaarField(
                        label = "APAAR ID *",
                        value = apaarId,
                        onValueChange = { apaarId = it.filter { c -> c.isDigit() || c == '-' } },
                        placeholder = "12-digit registry identifier",
                        error = errors["apaar"],
                        mono = true
                    )
                    if (apaarId.length >= 12 && validation.isStructurallyValid) {
                        Spacer(Modifier.height(6.dp))
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                Icons.Filled.CheckCircle,
                                contentDescription = null,
                                tint = colors.success,
                                modifier = Modifier.size(14.dp)
                            )
                            Spacer(Modifier.width(6.dp))
                            Text(
                                text = "Structurally valid · ${ApaarIdValidator.format(validation.normalised)}" +
                                    if (validation.isChecksumValid) " · Luhn OK" else " · Luhn advisory raised",
                                style = MaterialTheme.typography.labelSmall,
                                color = if (validation.isChecksumValid) colors.success else colors.warning
                            )
                        }
                    }

                    Spacer(Modifier.height(12.dp))
                    ApaarField(
                        label = "Full name *",
                        value = fullName,
                        onValueChange = { fullName = it },
                        placeholder = "As printed on the academic record",
                        error = errors["name"]
                    )

                    Spacer(Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        ApaarField(
                            label = "Date of birth *",
                            value = dob,
                            onValueChange = { dob = it },
                            placeholder = "yyyy-MM-dd",
                            error = errors["dob"],
                            mono = true,
                            modifier = Modifier.weight(1f)
                        )
                        Column(modifier = Modifier.weight(1f)) {
                            DropdownSelector(
                                label = "Gender",
                                options = Gender.entries.toList(),
                                selected = gender,
                                onSelect = { gender = it },
                                itemLabel = { it.label }
                            )
                        }
                    }

                    Spacer(Modifier.height(12.dp))
                    ApaarField(
                        label = "Institute roll number",
                        value = rollNo,
                        onValueChange = { rollNo = it },
                        placeholder = "Auto-generated if left blank"
                    )
                }
            }
        }

        item {
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(14.dp)) {
                    SectionHeader(
                        title = "Programme & quota",
                        subtitle = "Determines the sanctioned seat band consumed"
                    )
                    Spacer(Modifier.height(12.dp))
                    DropdownSelector(
                        label = "Sanctioned programme *",
                        options = programs.map { it.programId },
                        selected = programId,
                        onSelect = { programId = it },
                        itemLabel = { code ->
                            programs.firstOrNull { it.programId == code }?.programName ?: code
                        },
                        supporting = programId?.let { code ->
                            programs.firstOrNull { it.programId == code }?.let {
                                "${it.approvedIntake} regular seats · NRI ${it.maxSupernumeraryNri} · " +
                                    "OCI/FN ${it.maxSupernumeraryFnOci} · TFW ${it.maxSupernumeraryTfw}"
                            }
                        },
                        enabled = programs.isNotEmpty()
                    )
                    if (errors["program"] != null) {
                        Spacer(Modifier.height(5.dp))
                        Text(
                            text = errors["program"]!!,
                            style = MaterialTheme.typography.labelSmall,
                            color = colors.critical
                        )
                    }

                    Spacer(Modifier.height(12.dp))
                    DropdownSelector(
                        label = "Admission quota *",
                        options = AdmissionQuota.entries.toList(),
                        selected = quota,
                        onSelect = { quota = it },
                        itemLabel = { "${it.label} (${it.code})" },
                        supporting = if (quota.isSupernumerary) {
                            "Supernumerary band — consumes a capped supernumerary seat, not the regular intake."
                        } else {
                            "Regular band — consumes the AICTE sanctioned intake."
                        }
                    )
                }
            }
        }

        item {
            ApaarCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(14.dp)) {
                    SectionHeader(
                        title = "Nationality & documents",
                        subtitle = "Mandatory for foreign-national and supernumerary admissions"
                    )
                    Spacer(Modifier.height(12.dp))
                    ApaarField(
                        label = "Nationality",
                        value = nationality,
                        onValueChange = { nationality = it },
                        placeholder = "Indian"
                    )
                    Spacer(Modifier.height(12.dp))
                    ApaarField(
                        label = if (quota.requiresForeignDocs) "Passport / document number *" else "Passport / document number",
                        value = passport,
                        onValueChange = { passport = it },
                        placeholder = "e.g. P1234567",
                        error = errors["passport"]
                    )
                    Spacer(Modifier.height(12.dp))
                    ApaarField(
                        label = "Country of origin",
                        value = country,
                        onValueChange = { country = it },
                        placeholder = "Required for Foreign National quota"
                    )

                    if (quota.requiresForeignDocs) {
                        Spacer(Modifier.height(12.dp))
                        InfoBanner(
                            title = "Foreign-national documentation",
                            message = "${quota.label} admissions must carry a passport number and a country of " +
                                "origin. Missing documents are raised as data-consistency anomalies by the engine.",
                            tone = Tone.WARNING
                        )
                    }
                }
            }
        }

        item {
            Button(
                onClick = {
                    viewModel.submitManualStudent(
                        apaarId = apaarId,
                        fullName = fullName,
                        dob = dob,
                        gender = gender.code,
                        rollNo = rollNo,
                        programId = programId.orEmpty(),
                        quota = quota,
                        nationality = nationality,
                        passportNumber = passport,
                        countryOfOrigin = country
                    ) { message -> viewModel.postMessage(message) }
                },
                enabled = !state.isWorking,
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = colors.navyDeep,
                    contentColor = androidx.compose.ui.graphics.Color.White
                ),
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(Icons.Filled.PersonAdd, contentDescription = null, modifier = Modifier.size(17.dp))
                Spacer(Modifier.width(8.dp))
                Text("Onboard student to the registry", style = MaterialTheme.typography.labelLarge)
            }
        }

        item {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(MaterialTheme.colorScheme.surfaceContainerLow)
                    .padding(12.dp)
            ) {
                Text(
                    text = "Onboarding writes an immutable audit entry naming the registrar and the " +
                        "institution, then re-runs the full detection engine against the registry.",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

/**
 * A labelled text field with an inline error message.
 */
@Composable
private fun ApaarField(
    label: String,
    value: String,
    onValueChange: (String) -> Unit,
    modifier: Modifier = Modifier,
    placeholder: String = "",
    error: String? = null,
    mono: Boolean = false
) {
    val colors = ApaarTheme.colors
    Column(modifier = modifier.fillMaxWidth()) {
        Text(
            text = label.uppercase(),
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            letterSpacing = 0.7.sp
        )
        Spacer(Modifier.height(4.dp))
        OutlinedTextField(
            value = value,
            onValueChange = onValueChange,
            modifier = Modifier.fillMaxWidth(),
            placeholder = {
                Text(placeholder, style = MaterialTheme.typography.bodySmall)
            },
            singleLine = true,
            isError = error != null,
            shape = RoundedCornerShape(12.dp),
            textStyle = MaterialTheme.typography.bodyMedium.copy(
                fontFamily = if (mono) FontFamily.Monospace else FontFamily.SansSerif
            ),
            colors = TextFieldDefaults.colors(
                focusedContainerColor = MaterialTheme.colorScheme.surface,
                unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                focusedIndicatorColor = MaterialTheme.colorScheme.primary,
                unfocusedIndicatorColor = MaterialTheme.colorScheme.outlineVariant,
                errorIndicatorColor = colors.critical
            )
        )
        if (error != null) {
            Spacer(Modifier.height(4.dp))
            Text(
                text = error,
                style = MaterialTheme.typography.labelSmall,
                color = colors.critical
            )
        }
    }
}
