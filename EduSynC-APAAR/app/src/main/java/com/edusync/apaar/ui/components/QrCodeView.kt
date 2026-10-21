package com.edusync.apaar.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.edusync.apaar.core.qr.QrEncoder
import com.edusync.apaar.ui.theme.ApaarTheme
import kotlin.math.ceil
import kotlin.math.roundToInt

/**
 * Renders a QR matrix produced by [QrEncoder] as crisp, scannable modules.
 */
@Composable
fun QrCodeView(
    matrix: QrEncoder.QrMatrix,
    modifier: Modifier = Modifier,
    size: Dp = 220.dp,
    darkColor: Color = MaterialTheme.colorScheme.onSurface,
    backgroundColor: Color = Color.White,
    quietZoneRatio: Float = 0.08f
) {
    Box(
        modifier = modifier
            .size(size)
            .background(backgroundColor, RoundedCornerShape(10.dp))
            .padding(6.dp)
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val totalCells = matrix.size + 2 * ceil(matrix.size * quietZoneRatio).toInt()
            val cell = this.size.width / totalCells
            val origin = cell * ceil(matrix.size * quietZoneRatio).toInt()
            val inset = cell * 0.04f

            val path = Path()
            for (y in 0 until matrix.size) {
                for (x in 0 until matrix.size) {
                    if (!matrix.isDark(x, y)) continue
                    val left = origin + x * cell + inset
                    val top = origin + y * cell + inset
                    path.addRect(
                        androidx.compose.ui.geometry.Rect(
                            offset = Offset(left, top),
                            size = Size(cell - inset * 2, cell - inset * 2)
                        )
                    )
                }
            }
            drawPath(path, darkColor)
        }
    }
}

/**
 * QR badge rendered inside an AICTE-styled frame.
 */
@Composable
fun QrBadge(
    matrix: QrEncoder.QrMatrix,
    modifier: Modifier = Modifier,
    size: Dp = 220.dp,
    caption: String? = null
) {
    val colors = ApaarTheme.colors
    Box(
        modifier = modifier
            .background(colors.card, RoundedCornerShape(16.dp))
            .border(1.dp, colors.divider, RoundedCornerShape(16.dp))
            .padding(12.dp),
        contentAlignment = androidx.compose.ui.Alignment.Center
    ) {
        QrCodeView(matrix = matrix, size = size)
        if (caption != null) {
            androidx.compose.foundation.layout.Column(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = androidx.compose.foundation.layout.Arrangement.Bottom
            ) {}
        }
    }
}

/**
 * Converts a QR matrix into a fixed-size boolean grid (useful for previews).
 */
fun QrEncoder.QrMatrix.toGrid(): Array<BooleanArray> =
    Array(size) { y -> BooleanArray(size) { x -> isDark(x, y) } }

/**
 * Counts the number of dark modules — a quick sanity metric for the renderer.
 */
fun QrEncoder.QrMatrix.darkModuleCount(): Int =
    (0 until size).sumOf { y -> (0 until size).count { x -> isDark(x, y) } }

/**
 * Rounds a float to the nearest integer percentage.
 */
fun Float.asPercent(): Int = (this * 100f).roundToInt()
