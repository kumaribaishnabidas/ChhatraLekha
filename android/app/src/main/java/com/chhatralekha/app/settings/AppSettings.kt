package com.chhatralekha.app.settings

import android.content.Context
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = "chhatralekha_settings")

/** The exact three in-app appearance choices; persisted with DataStore. */
enum class ThemePreference { SYSTEM, LIGHT, DARK }

class AppSettings(private val context: Context) {
    private val themeKey = stringPreferencesKey("theme")
    val theme: Flow<ThemePreference> = context.dataStore.data.map { preferences ->
        runCatching { ThemePreference.valueOf(preferences[themeKey] ?: ThemePreference.SYSTEM.name) }
            .getOrDefault(ThemePreference.SYSTEM)
    }

    suspend fun setTheme(value: ThemePreference) {
        context.dataStore.edit { it[themeKey] = value.name }
    }
}
