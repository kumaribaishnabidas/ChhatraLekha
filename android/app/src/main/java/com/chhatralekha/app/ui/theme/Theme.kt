package com.chhatralekha.app.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat
import com.chhatralekha.app.settings.ThemePreference

/**
 * Semantic colours that sit outside the Material 3 palette but are required by
 * the regulatory status language (verified / warning / critical / informational).
 */
@Immutable
data class ApaarExtendedColors(
    val success: Color,
    val successContainer: Color,
    val onSuccessContainer: Color,
    val warning: Color,
    val warningContainer: Color,
    val onWarningContainer: Color,
    val critical: Color,
    val criticalContainer: Color,
    val onCriticalContainer: Color,
    val info: Color,
    val infoContainer: Color,
    val onInfoContainer: Color,
    val navyDeep: Color,
    val saffron: Color,
    val brandTeal: Color,
    val card: Color,
    val divider: Color,
    val isDark: Boolean
)

private val LightExtendedColors = ApaarExtendedColors(
    success = Emerald,
    successContainer = EmeraldContainerLight,
    onSuccessContainer = EmeraldOnContainerLight,
    warning = AmberLight,
    warningContainer = AmberContainerLight,
    onWarningContainer = AmberOnContainerLight,
    critical = Crimson,
    criticalContainer = CrimsonContainerLight,
    onCriticalContainer = CrimsonOnContainerLight,
    info = InfoBlue,
    infoContainer = InfoContainerLight,
    onInfoContainer = InfoOnContainerLight,
    navyDeep = NavyDeep,
    saffron = Saffron,
    brandTeal = BrandTeal,
    card = Color.White,
    divider = DividerLight,
    isDark = false
)

private val DarkExtendedColors = ApaarExtendedColors(
    success = EmeraldLight,
    successContainer = EmeraldContainerDark,
    onSuccessContainer = EmeraldOnContainerDark,
    warning = Color(0xFFFFB74D),
    warningContainer = AmberContainerDark,
    onWarningContainer = AmberOnContainerDark,
    critical = Color(0xFFFF8A80),
    criticalContainer = CrimsonContainerDark,
    onCriticalContainer = CrimsonOnContainerDark,
    info = Color(0xFF90CAF9),
    infoContainer = InfoContainerDark,
    onInfoContainer = InfoOnContainerDark,
    navyDeep = Color(0xFF08131F),
    saffron = Color(0xFFFFB68A),
    brandTeal = BrandTealLight,
    card = CardDark,
    divider = DividerDark,
    isDark = true
)

val LocalApaarColors = staticCompositionLocalOf { LightExtendedColors }

private val LightScheme = lightColorScheme(
    primary = NavyPrimary,
    onPrimary = Color.White,
    primaryContainer = NavyContainerLight,
    onPrimaryContainer = NavyOnContainerLight,
    secondary = Saffron,
    onSecondary = Color.White,
    secondaryContainer = SaffronContainerLight,
    onSecondaryContainer = SaffronOnContainerLight,
    tertiary = Emerald,
    onTertiary = Color.White,
    tertiaryContainer = EmeraldContainerLight,
    onTertiaryContainer = EmeraldOnContainerLight,
    error = Crimson,
    onError = Color.White,
    errorContainer = CrimsonContainerLight,
    onErrorContainer = CrimsonOnContainerLight,
    background = SurfaceLight,
    onBackground = Color(0xFF121A24),
    surface = Color.White,
    onSurface = Color(0xFF121A24),
    surfaceVariant = Color(0xFFE9EDF1),
    onSurfaceVariant = Color(0xFF41484D),
    surfaceContainerLowest = Color.White,
    surfaceContainerLow = Color(0xFFFCFDFE),
    surfaceContainer = Color(0xFFF1F4F7),
    surfaceContainerHigh = Color(0xFFEBEEF2),
    surfaceContainerHighest = Color(0xFFE5E9EE),
    outline = Color(0xFF72787E),
    outlineVariant = Color(0xFFC2C7CE),
    inverseSurface = Color(0xFF121A24),
    inverseOnSurface = Color(0xFFF1F4F7),
    inversePrimary = NavyContainerLight
)

private val DarkScheme = darkColorScheme(
    primary = Color(0xFFA6C9E4),
    onPrimary = Color(0xFF0A2540),
    primaryContainer = NavyContainerDark,
    onPrimaryContainer = NavyOnContainerDark,
    secondary = Color(0xFFFFB68A),
    onSecondary = Color(0xFF5A2500),
    secondaryContainer = SaffronContainerDark,
    onSecondaryContainer = SaffronOnContainerDark,
    tertiary = Color(0xFF7FD98F),
    onTertiary = Color(0xFF00390D),
    tertiaryContainer = EmeraldContainerDark,
    onTertiaryContainer = EmeraldOnContainerDark,
    error = Color(0xFFFFB4AB),
    onError = Color(0xFF690005),
    errorContainer = CrimsonContainerDark,
    onErrorContainer = CrimsonOnContainerDark,
    background = BackgroundDark,
    onBackground = Color(0xFFE2E6EA),
    surface = SurfaceDark,
    onSurface = Color(0xFFE2E6EA),
    surfaceVariant = Color(0xFF2A333D),
    onSurfaceVariant = Color(0xFFC2C7CE),
    surfaceContainerLowest = Color(0xFF0B121A),
    surfaceContainerLow = Color(0xFF121A24),
    surfaceContainer = Color(0xFF172029),
    surfaceContainerHigh = Color(0xFF1E2831),
    surfaceContainerHighest = Color(0xFF263039),
    outline = Color(0xFF8C9198),
    outlineVariant = Color(0xFF41484D),
    inverseSurface = Color(0xFFE2E6EA),
    inverseOnSurface = Color(0xFF121A24),
    inversePrimary = NavyPrimary
)

@Composable
fun ApaarTheme(
    preference: ThemePreference = ThemePreference.SYSTEM,
    content: @Composable () -> Unit
) {
    val darkTheme = when (preference) {
        ThemePreference.SYSTEM -> isSystemInDarkTheme()
        ThemePreference.LIGHT -> false
        ThemePreference.DARK -> true
    }
    val colorScheme = if (darkTheme) DarkScheme else LightScheme
    val extended = if (darkTheme) DarkExtendedColors else LightExtendedColors

    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = Color.Transparent.value.toInt()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }

    CompositionLocalProvider(LocalApaarColors provides extended) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography = ApaarTypography,
            content = content
        )
    }
}

/** Convenience accessor for the regulatory semantic palette. */
object ApaarTheme {
    val colors: ApaarExtendedColors
        @Composable get() = LocalApaarColors.current
}
