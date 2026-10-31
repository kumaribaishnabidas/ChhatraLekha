package com.chhatralekha.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.compose.runtime.getValue
import com.chhatralekha.app.ui.ApaarApp
import com.chhatralekha.app.ui.theme.ApaarTheme
import com.chhatralekha.app.ui.viewmodel.ApaarViewModel

/**
 * The single-activity host for the multi-role APAAR portal.
 */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val repository = (application as ApaarApplication).repository
        val settings = (application as ApaarApplication).settings

        setContent {
            val theme by settings.theme.collectAsStateWithLifecycle(initialValue = com.chhatralekha.app.settings.ThemePreference.SYSTEM)
            ApaarTheme(preference = theme) {
                val viewModel: ApaarViewModel = viewModel(
                    factory = ApaarViewModel.factory(repository)
                )
                ApaarApp(viewModel = viewModel, settings = settings, themePreference = theme)
            }
        }
    }
}
