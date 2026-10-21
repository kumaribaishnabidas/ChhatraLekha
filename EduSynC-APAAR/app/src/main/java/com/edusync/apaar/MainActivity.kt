package com.edusync.apaar

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.lifecycle.viewmodel.compose.viewModel
import com.edusync.apaar.ui.ApaarApp
import com.edusync.apaar.ui.theme.ApaarTheme
import com.edusync.apaar.ui.viewmodel.ApaarViewModel

/**
 * The single-activity host for the multi-role APAAR portal.
 */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val repository = (application as ApaarApplication).repository

        setContent {
            ApaarTheme {
                val viewModel: ApaarViewModel = viewModel(
                    factory = ApaarViewModel.factory(repository)
                )
                ApaarApp(viewModel = viewModel)
            }
        }
    }
}
