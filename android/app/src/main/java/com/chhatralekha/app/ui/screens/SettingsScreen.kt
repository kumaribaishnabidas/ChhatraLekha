package com.chhatralekha.app.ui.screens

import androidx.appcompat.app.AppCompatDelegate
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.core.os.LocaleListCompat
import com.chhatralekha.app.R
import com.chhatralekha.app.settings.AppSettings
import com.chhatralekha.app.settings.ThemePreference
import kotlinx.coroutines.launch

/** Appearance and language preferences. It uses DataStore for theme and
 * AppCompat locales so per-app languages work below Android 13 as well. */
@Composable
fun SettingsScreen(settings: AppSettings, themePreference: ThemePreference) {
    val scope = rememberCoroutineScope()
    val themes = listOf(
        ThemePreference.SYSTEM to stringResource(R.string.theme_system),
        ThemePreference.LIGHT to stringResource(R.string.theme_light),
        ThemePreference.DARK to stringResource(R.string.theme_dark)
    )
    val languages = listOf("en" to "English", "hi" to "हिन्दी", "bn" to "বাংলা", "ta" to "தமிழ்", "te" to "తెలుగు", "mr" to "मराठी", "ur" to "اردو")
    Column(
        modifier = Modifier.fillMaxSize().padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text(stringResource(R.string.settings), style = MaterialTheme.typography.headlineSmall)
        Text(stringResource(R.string.theme), style = MaterialTheme.typography.titleMedium)
        themes.forEach { (value, label) ->
            TextButton(onClick = { scope.launch { settings.setTheme(value) } }, modifier = Modifier.fillMaxWidth()) {
                RadioButton(selected = themePreference == value, onClick = null)
                Text(label, modifier = Modifier.padding(start = 8.dp))
            }
        }
        Text(stringResource(R.string.language), style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 12.dp))
        languages.forEach { (tag, label) ->
            TextButton(onClick = { AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(tag)) }) {
                Text(label)
            }
        }
        Text(stringResource(R.string.voice_privacy), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(top = 12.dp))
        Text(stringResource(R.string.not_official_verification), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}
