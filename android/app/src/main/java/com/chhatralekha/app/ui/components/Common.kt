package com.chhatralekha.app.ui.components

import androidx.compose.animation.animateColorAsState
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
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowForward
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
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
import com.chhatralekha.core.model.AnomalySeverity
import com.chhatralekha.core.model.AdmissionQuota
import com.chhatralekha.core.model.VerificationStatus
import com.chhatralekha.core.validation.ApaarIdValidator
import com.chhatralekha.app.ui.theme.ApaarIdSmallTextStyle
import com.chhatralekha.app.ui.theme.ApaarIdTextStyle
import com.chhatralekha.app.ui.theme.ApaarKpiNumberStyle
import com.chhatralekha.app.ui.theme.ApaarTheme

/**
 * Small pill used for quota buckets and category tags.
 */
@Composable
fun StatusPill(
    text: String,
    container: Color,
    content: Color,
    modifier: Modifier = Modifier,
    icon: ImageVector? = null
) {
    Row(
        modifier = modifier
            .clip(CircleShape)
            .background(container)
            .padding(horizontal = 9.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        if (icon != null) {
            Icon(icon, contentDescription = null, tint = content, modifier = Modifier.size(12.dp))
        }
        Text(
            text = text,
            style = MaterialTheme.typography.labelSmall,
            color = content,
            fontWeight = FontWeight.SemiBold,
            maxLines = 1
        )
    }
}

/**
 * Coloured chip for the quota buckets used across the register and dashboards.
 */
@Composable
fun QuotaChip(quota: AdmissionQuota, modifier: Modifier = Modifier) {
    val colors = ApaarTheme.colors
    val (container, content) = when (quota) {
        AdmissionQuota.MERIT -> colors.infoContainer to colors.onInfoContainer
        AdmissionQuota.MANAGEMENT -> MaterialTheme.colorScheme.secondaryContainer to MaterialTheme.colorScheme.onSecondaryContainer
        AdmissionQuota.NRI -> colors.warningContainer to colors.onWarningContainer
        AdmissionQuota.OCI -> colors.warningContainer to colors.onWarningContainer
        AdmissionQuota.FN -> colors.warningContainer to colors.onWarningContainer
        AdmissionQuota.TFW -> colors.saffron.copy(alpha = 0.16f) to colors.saffron
        AdmissionQuota.PMSSS -> colors.successContainer to colors.onSuccessContainer
    }
    StatusPill(quota.shortLabel, container, content, modifier)
}

/**
 * Verification status badge.
 */
@Composable
fun VerificationBadge(status: VerificationStatus, modifier: Modifier = Modifier) {
    val colors = ApaarTheme.colors
    val (container, content, icon) = when (status) {
        VerificationStatus.VERIFIED -> Triple(colors.successContainer, colors.onSuccessContainer, Icons.Filled.CheckCircle)
        VerificationStatus.FLAGGED_ANOMALY -> Triple(colors.criticalContainer, colors.onCriticalContainer, Icons.Filled.Error)
        VerificationStatus.PENDING_REVIEW -> Triple(colors.infoContainer, colors.onInfoContainer, Icons.Filled.Info)
    }
    StatusPill(status.label, container, content, modifier, icon)
}

/**
 * Severity badge used by the anomaly inspector.
 */
@Composable
fun SeverityBadge(severity: AnomalySeverity, modifier: Modifier = Modifier) {
    val colors = ApaarTheme.colors
    val (container, content, icon) = when (severity) {
        AnomalySeverity.CRITICAL -> Triple(colors.criticalContainer, colors.onCriticalContainer, Icons.Filled.Error)
        AnomalySeverity.HIGH -> Triple(colors.warningContainer, colors.onWarningContainer, Icons.Filled.Warning)
        AnomalySeverity.WARNING -> Triple(colors.warningContainer, colors.onWarningContainer, Icons.Filled.Warning)
        AnomalySeverity.INFO -> Triple(colors.infoContainer, colors.onInfoContainer, Icons.Filled.Info)
    }
    StatusPill(severity.label.uppercase(), container, content, modifier, icon)
}

/**
 * Headline KPI tile.
 */
@Composable
fun KpiCard(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
    caption: String? = null,
    accent: Color = MaterialTheme.colorScheme.primary,
    icon: ImageVector? = null,
    onClick: (() -> Unit)? = null
) {
    val colors = ApaarTheme.colors
    Surface(
        modifier = modifier
            .clip(RoundedCornerShape(18.dp))
            .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier),
        color = colors.card,
        shape = RoundedCornerShape(18.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, colors.divider),
        shadowElevation = 1.dp
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .clip(CircleShape)
                        .background(accent)
                )
                Spacer(Modifier.width(7.dp))
                Text(
                    text = label.uppercase(),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.weight(1f)
                )
                if (icon != null) {
                    Icon(icon, contentDescription = null, tint = accent, modifier = Modifier.size(15.dp))
                }
            }
            Spacer(Modifier.height(8.dp))
            Text(
                text = value,
                style = ApaarKpiNumberStyle,
                color = MaterialTheme.colorScheme.onSurface
            )
            if (caption != null) {
                Spacer(Modifier.height(3.dp))
                Text(
                    text = caption,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }
    }
}

/**
 * Section title with optional trailing action.
 */
@Composable
fun SectionHeader(
    title: String,
    modifier: Modifier = Modifier,
    subtitle: String? = null,
    trailing: (@Composable () -> Unit)? = null
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface
            )
            if (subtitle != null) {
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
        trailing?.invoke()
    }
}

/**
 * Horizontal quota meter that changes colour as capacity fills.
 */
@Composable
fun QuotaBar(
    value: Int,
    total: Int,
    modifier: Modifier = Modifier,
    trackColor: Color = MaterialTheme.colorScheme.surfaceContainerHighest,
    showOverflow: Boolean = true
) {
    val colors = ApaarTheme.colors
    val fraction = if (total <= 0) 0f else (value.toFloat() / total).coerceIn(0f, 1f)
    val animated by animateFloatAsState(
        targetValue = fraction,
        animationSpec = tween(700),
        label = "quota"
    )
    val barColor by animateColorAsState(
        targetValue = when {
            value > total -> colors.critical
            fraction >= 1f -> colors.warning
            fraction >= 0.9f -> colors.saffron
            else -> colors.success
        },
        animationSpec = tween(700),
        label = "quotaColor"
    )
    Column(modifier = modifier) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(9.dp)
                .clip(CircleShape)
                .background(trackColor)
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth(animated)
                    .height(9.dp)
                    .clip(CircleShape)
                    .background(barColor)
            )
        }
        if (showOverflow && value > total) {
            Spacer(Modifier.height(3.dp))
            Text(
                text = "+${value - total} over sanctioned capacity",
                style = MaterialTheme.typography.labelSmall,
                color = colors.critical
            )
        }
    }
}

/**
 * Label / value pair used across the detail dossiers.
 */
@Composable
fun DetailRow(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
    mono: Boolean = false,
    valueColor: Color = MaterialTheme.colorScheme.onSurface
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(vertical = 5.dp),
        verticalAlignment = Alignment.Top
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.width(124.dp)
        )
        Text(
            text = value,
            style = if (mono) ApaarIdSmallTextStyle else MaterialTheme.typography.bodyMedium,
            color = valueColor,
            fontWeight = if (mono) FontWeight.Medium else FontWeight.Medium,
            modifier = Modifier.weight(1f)
        )
    }
}

/**
 * Monospaced 12-digit APAAR identifier.
 */
@Composable
fun ApaarIdText(
    value: String,
    modifier: Modifier = Modifier,
    color: Color = MaterialTheme.colorScheme.onSurface,
    large: Boolean = false
) {
    Text(
        text = ApaarIdValidator.format(value),
        style = if (large) ApaarIdTextStyle else ApaarIdSmallTextStyle,
        color = color
    )
}

/**
 * Empty / neutral state.
 */
@Composable
fun EmptyState(
    title: String,
    message: String,
    modifier: Modifier = Modifier,
    icon: ImageVector = Icons.Filled.Info
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(28.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Icon(icon, contentDescription = null, tint = MaterialTheme.colorScheme.outline, modifier = Modifier.size(34.dp))
        Text(
            text = title,
            style = MaterialTheme.typography.titleSmall,
            color = MaterialTheme.colorScheme.onSurface
        )
        Text(
            text = message,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

/**
 * A tappable call-to-action card used on the role selection screen.
 */
@Composable
fun RoleCard(
    title: String,
    tagline: String,
    icon: ImageVector,
    accent: Color,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    Surface(
        modifier = modifier
            .clip(RoundedCornerShape(20.dp))
            .clickable { onClick() },
        color = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(20.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
        shadowElevation = 2.dp
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(46.dp)
                    .clip(RoundedCornerShape(14.dp))
                    .background(accent.copy(alpha = 0.14f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(icon, contentDescription = null, tint = accent, modifier = Modifier.size(24.dp))
            }
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(Modifier.height(3.dp))
                Text(
                    text = tagline,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            Icon(
                Icons.Filled.ArrowForward,
                contentDescription = null,
                tint = accent,
                modifier = Modifier.size(18.dp)
            )
        }
    }
}

/**
 * A bordered container used for grouped content blocks.
 */
@Composable
fun ApaarCard(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit
) {
    Surface(
        modifier = modifier,
        color = ApaarTheme.colors.card,
        shape = RoundedCornerShape(18.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, ApaarTheme.colors.divider),
        shadowElevation = 1.dp
    ) {
        content()
    }
}

/**
 * Dotted "under construction"-style divider used between register rows.
 */
@Composable
fun HairLine(modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(1.dp)
            .background(ApaarTheme.colors.divider)
    )
}
