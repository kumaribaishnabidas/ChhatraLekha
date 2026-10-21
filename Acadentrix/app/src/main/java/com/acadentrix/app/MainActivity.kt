package com.acadentrix.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.lifecycle.viewmodel.compose.viewModel
import com.acadentrix.app.ui.ApaarApp
import com.acadentrix.app.ui.theme.ApaarTheme
import com.acadentrix.app.ui.viewmodel.ApaarViewModel

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
