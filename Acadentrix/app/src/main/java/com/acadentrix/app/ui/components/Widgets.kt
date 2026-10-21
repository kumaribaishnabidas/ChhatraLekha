package com.acadentrix.app.ui.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.FastOutSlowInEasing
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
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.acadentrix.app.ui.theme.ApaarTheme
import kotlin.math.min

/**
 * The regulatory tone of a banner / chip.
 */
enum class Tone {
    INFO,
    SUCCESS,
    WARNING,
    CRITICAL
}

/**
 * Resolves the container / content colour pair for a [Tone].
 */
@Composable
fun toneColors(tone: Tone): Pair<Color, Color> {
    val colors = ApaarTheme.colors
    return when (tone) {
        Tone.INFO -> colors.infoContainer to colors.onInfoContainer
        Tone.SUCCESS -> colors.successContainer to colors.onSuccessContainer
        Tone.WARNING -> colors.warningContainer to colors.onWarningContainer
        Tone.CRITICAL -> colors.criticalContainer to colors.onCriticalContainer
    }
}

@Composable
private fun toneAccent(tone: Tone): Color {
    val colors = ApaarTheme.colors
    return when (tone) {
        Tone.INFO -> colors.info
        Tone.SUCCESS -> colors.success
        Tone.WARNING -> colors.warning
        Tone.CRITICAL -> colors.critical
    }
}

@Composable
private fun toneIcon(tone: Tone): ImageVector = when (tone) {
    Tone.INFO -> Icons.Filled.Info
    Tone.SUCCESS -> Icons.Filled.CheckCircle
    Tone.WARNING -> Icons.Filled.Warning
    Tone.CRITICAL -> Icons.Filled.Error
}

/**
 * A regulatory notice strip.
 */
@Composable
fun InfoBanner(
    title: String,
    message: String,
    modifier: Modifier = Modifier,
    tone: Tone = Tone.INFO
) {
    val (container, content) = toneColors(tone)
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(container)
            .border(1.dp, toneAccent(tone).copy(alpha = 0.25f), RoundedCornerShape(14.dp))
            .padding(12.dp),
        verticalAlignment = Alignment.Top
    ) {
        Icon(
            toneIcon(tone),
            contentDescription = null,
            tint = toneAccent(tone),
            modifier = Modifier.size(17.dp)
        )
        Spacer(Modifier.width(9.dp))
        Column {
            Text(
                text = title,
                style = MaterialTheme.typography.labelLarge,
                color = content,
                fontWeight = FontWeight.Bold
            )
            Spacer(Modifier.height(2.dp))
            Text(
                text = message,
                style = MaterialTheme.typography.bodySmall,
                color = content.copy(alpha = 0.92f)
            )
        }
    }
}

/**
 * A selectable filter chip with an optional counter badge.
 */
@Composable
fun ApaarFilterChip(
    label: String,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    count: Int? = null,
    tone: Tone? = null
) {
    val accent = tone?.let { toneAccent(it) } ?: MaterialTheme.colorScheme.primary
    val container by animateColorAsState(
        targetValue = if (selected) accent else MaterialTheme.colorScheme.surface,
        animationSpec = tween(220),
        label = "chipContainer"
    )
    val content by animateColorAsState(
        targetValue = if (selected) Color.White else MaterialTheme.colorScheme.onSurfaceVariant,
        animationSpec = tween(220),
        label = "chipContent"
    )
    Row(
        modifier = modifier
            .clip(CircleShape)
            .background(container)
            .border(
                width = 1.dp,
                color = if (selected) accent else MaterialTheme.colorScheme.outlineVariant,
                shape = CircleShape
            )
            .clickable { onClick() }
            .padding(horizontal = 12.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(5.dp)
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            color = content,
            fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium,
            maxLines = 1
        )
        if (count != null) {
            Text(
                text = count.toString(),
                style = MaterialTheme.typography.labelSmall,
                color = if (selected) Color.White.copy(alpha = 0.85f) else accent,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

/**
 * A horizontally scrolling row of filter chips.
 */
@Composable
fun <T> FilterChipRow(
    items: List<T>,
    selected: T,
    onSelect: (T) -> Unit,
    labelOf: (T) -> String,
    modifier: Modifier = Modifier,
    countOf: ((T) -> Int?)? = null
) {
    LazyRow(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(7.dp)
    ) {
        items(items) { item ->
            ApaarFilterChip(
                label = labelOf(item),
                selected = item == selected,
                onClick = { onSelect(item) },
                count = countOf?.invoke(item)
            )
        }
    }
}

/**
 * Summary chip used by the CSV validator — e.g. "38 Valid" / "3 Critical Violations".
 */
@Composable
fun SummaryChip(
    label: String,
    value: String,
    tone: Tone,
    modifier: Modifier = Modifier,
    icon: ImageVector? = null
) {
    val (container, content) = toneColors(tone)
    val accent = toneAccent(tone)
    Row(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .background(container)
            .border(1.dp, accent.copy(alpha = 0.28f), RoundedCornerShape(12.dp))
            .padding(horizontal = 11.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(7.dp)
    ) {
        if (icon != null) {
            Icon(icon, contentDescription = null, tint = accent, modifier = Modifier.size(15.dp))
        }
        Text(
            text = value,
            style = MaterialTheme.typography.titleMedium,
            color = content,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = content.copy(alpha = 0.88f),
            maxLines = 1
        )
    }
}

/**
 * An animated radial gauge used for intake utilisation.
 */
@Composable
fun AnimatedGauge(
    fraction: Float,
    modifier: Modifier = Modifier,
    diameter: Dp = 148.dp,
    strokeWidth: Dp = 13.dp,
    trackColor: Color = MaterialTheme.colorScheme.surfaceContainerHighest,
    progressColor: Color? = null,
    centerContent: @Composable () -> Unit = {}
) {
    val colors = ApaarTheme.colors
    val animated by animateFloatAsState(
        targetValue = fraction.coerceIn(0f, 1.35f),
        animationSpec = tween(900, easing = FastOutSlowInEasing),
        label = "gauge"
    )
    val clamped = min(animated, 1f)
    val overflow = animated > 1f
    val barColor by animateColorAsState(
        targetValue = progressColor
            ?: when {
                overflow -> colors.critical
                clamped >= 1f -> colors.warning
                clamped >= 0.9f -> colors.saffron
                else -> colors.success
            },
        animationSpec = tween(600),
        label = "gaugeColor"
    )

    Box(
        modifier = modifier.size(diameter),
        contentAlignment = Alignment.Center
    ) {
        androidx.compose.foundation.Canvas(modifier = Modifier.size(diameter)) {
            val stroke = strokeWidth.toPx()
            val inset = stroke / 2f
            val arcSize = Size(size.width - stroke, size.height - stroke)
            val topLeft = Offset(inset, inset)
            drawArc(
                color = trackColor,
                startAngle = 135f,
                sweepAngle = 270f,
                useCenter = false,
                topLeft = topLeft,
                size = arcSize,
                style = Stroke(width = stroke, cap = StrokeCap.Round)
            )
            drawArc(
                color = barColor,
                startAngle = 135f,
                sweepAngle = 270f * clamped,
                useCenter = false,
                topLeft = topLeft,
                size = arcSize,
                style = Stroke(width = stroke, cap = StrokeCap.Round)
            )
        }
        centerContent()
    }
}

/**
 * A compact horizontal meter with a label on the left and the value on the right.
 */
@Composable
fun LabelledMeter(
    label: String,
    value: Int,
    total: Int,
    modifier: Modifier = Modifier,
    caption: String? = null,
    color: Color? = null
) {
    val colors = ApaarTheme.colors
    val overflow = value > total
    val barColor = color ?: when {
        overflow -> colors.critical
        total > 0 && value >= total -> colors.warning
        else -> colors.success
    }
    Column(modifier = modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = label,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.weight(1f),
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
            Text(
                text = "$value / $total",
                style = MaterialTheme.typography.labelMedium,
                color = if (overflow) colors.critical else MaterialTheme.colorScheme.onSurface,
                fontWeight = FontWeight.Bold
            )
        }
        Spacer(Modifier.height(4.dp))
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(7.dp)
                .clip(CircleShape)
                .background(MaterialTheme.colorScheme.surfaceContainerHighest)
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth(if (total <= 0) 0f else (value.toFloat() / total).coerceIn(0f, 1f))
                    .height(7.dp)
                    .clip(CircleShape)
                    .background(barColor)
            )
        }
        if (caption != null) {
            Spacer(Modifier.height(3.dp))
            Text(
                text = caption,
                style = MaterialTheme.typography.labelSmall,
                color = if (overflow) colors.critical else MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

/**
 * Circular monogram used in place of a photograph.
 */
@Composable
fun StudentAvatar(
    initials: String,
    seed: Int,
    modifier: Modifier = Modifier,
    size: Dp = 42.dp
) {
    val palette = listOf(
        Color(0xFF163A5F), Color(0xFF0D2B45), Color(0xFF1B5E20),
        Color(0xFFE65100), Color(0xFF1565C0), Color(0xFF6A1B9A)
    )
    val background = palette[((seed % palette.size) + palette.size) % palette.size]
    Box(
        modifier = modifier
            .size(size)
            .clip(CircleShape)
            .background(background),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = initials,
            style = MaterialTheme.typography.labelLarge,
            color = Color.White,
            fontWeight = FontWeight.Bold
        )
    }
}

/**
 * A compact search field.
 */
@Composable
fun SearchField(
    value: String,
    onValueChange: (String) -> Unit,
    modifier: Modifier = Modifier,
    placeholder: String = "Search"
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        modifier = modifier.fillMaxWidth(),
        placeholder = {
            Text(placeholder, style = MaterialTheme.typography.bodySmall)
        },
        leadingIcon = {
            Icon(Icons.Filled.Search, contentDescription = null, modifier = Modifier.size(17.dp))
        },
        singleLine = true,
        shape = RoundedCornerShape(12.dp),
        textStyle = MaterialTheme.typography.bodyMedium,
        colors = TextFieldDefaults.colors(
            focusedContainerColor = MaterialTheme.colorScheme.surface,
            unfocusedContainerColor = MaterialTheme.colorScheme.surface,
            focusedIndicatorColor = MaterialTheme.colorScheme.primary,
            unfocusedIndicatorColor = MaterialTheme.colorScheme.outlineVariant
        )
    )
}

/**
 * A labelled dropdown selector.
 */
@Composable
fun <T> DropdownSelector(
    label: String,
    options: List<T>,
    selected: T?,
    onSelect: (T) -> Unit,
    itemLabel: (T) -> String,
    modifier: Modifier = Modifier,
    supporting: String? = null,
    enabled: Boolean = true
) {
    var expanded by remember { mutableStateOf(false) }
    Column(modifier = modifier.fillMaxWidth()) {
        Text(
            text = label.uppercase(),
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            letterSpacing = 0.7.sp
        )
        Spacer(Modifier.height(4.dp))
        Box {
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .clickable(enabled = enabled) { expanded = true }
                    .then(
                        if (enabled) Modifier else Modifier.alphaCompat(0.5f)
                    ),
                color = MaterialTheme.colorScheme.surface,
                shape = RoundedCornerShape(12.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 13.dp, vertical = 12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = selected?.let(itemLabel) ?: "Select…",
                        style = MaterialTheme.typography.bodyMedium,
                        color = if (selected == null) {
                            MaterialTheme.colorScheme.onSurfaceVariant
                        } else {
                            MaterialTheme.colorScheme.onSurface
                        },
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f)
                    )
                    Text(
                        text = "▾",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            DropdownMenu(
                expanded = expanded,
                onDismissRequest = { expanded = false },
                containerColor = MaterialTheme.colorScheme.surface
            ) {
                options.forEach { option ->
                    DropdownMenuItem(
                        text = {
                            Text(
                                text = itemLabel(option),
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = if (option == selected) FontWeight.Bold else FontWeight.Normal
                            )
                        },
                        onClick = {
                            expanded = false
                            onSelect(option)
                        }
                    )
                }
            }
        }
        if (supporting != null) {
            Spacer(Modifier.height(3.dp))
            Text(
                text = supporting,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

/**
 * Modifier helper that mirrors [androidx.compose.ui.draw.alpha] without pulling
 * the import into every screen.
 */
private fun Modifier.alphaCompat(alpha: Float): Modifier =
    this.then(Modifier.alpha(alpha))

/**
 * A labelled key/value tile used on the dashboards.
 */
@Composable
fun MetricTile(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
    caption: String? = null,
    accent: Color = MaterialTheme.colorScheme.primary
) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(14.dp))
            .background(MaterialTheme.colorScheme.surface)
            .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(14.dp))
            .padding(horizontal = 12.dp, vertical = 10.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(6.dp)
                    .clip(CircleShape)
                    .background(accent)
            )
            Spacer(Modifier.width(6.dp))
            Text(
                text = label.uppercase(),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
        }
        Spacer(Modifier.height(5.dp))
        Text(
            text = value,
            style = MaterialTheme.typography.titleLarge,
            color = MaterialTheme.colorScheme.onSurface,
            fontWeight = FontWeight.Bold
        )
        if (caption != null) {
            Text(
                text = caption,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis
            )
        }
    }
}
