package com.acadentrix.app.ui.components

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.acadentrix.app.R
import com.acadentrix.app.ui.theme.BrandPlate
import com.acadentrix.app.ui.theme.BrandPlateBorder

/**
 * The ChhatraLekha brand mark.
 *
 * The artwork ships as the team's own raster asset (`res/drawable-nodpi/chhatralekha_mark.png`)
 * so the branding on screen is pixel-identical to the supplied logo.
 */
@Composable
fun ChhatraLekhaMark(
    modifier: Modifier = Modifier,
    size: Dp = 40.dp
) {
    Image(
        painter = painterResource(R.drawable.chhatralekha_mark),
        contentDescription = "ChhatraLekha",
        contentScale = ContentScale.Fit,
        modifier = modifier.size(size)
    )
}

/**
 * The ChhatraLekha mark presented on its white plate, for use on the dark navy
 * header surfaces where the artwork needs a light ground to sit on.
 */
@Composable
fun ChhatraLekhaPlate(
    modifier: Modifier = Modifier,
    markSize: Dp = 38.dp,
    platePadding: Dp = 7.dp,
    radius: Dp = 11.dp,
    plateColor: Color = BrandPlate,
    borderColor: Color = BrandPlateBorder
) {
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(radius))
            .background(plateColor)
            .border(1.dp, borderColor, RoundedCornerShape(radius))
            .padding(platePadding),
        contentAlignment = Alignment.Center
    ) {
        ChhatraLekhaMark(size = markSize)
    }
}

/**
 * Horizontal brand lockup: ChhatraLekha mark + the ChhatraLekha wordmark.
 */
@Composable
fun ChhatraLekhaLockup(
    modifier: Modifier = Modifier,
    markSize: Dp = 34.dp,
    wordColor: Color = Color.White,
    subColor: Color = Color.White.copy(alpha = 0.72f),
    subText: String = "by ChhatraLekha",
    onWhite: Boolean = false
) {
    Row(modifier = modifier, verticalAlignment = Alignment.CenterVertically) {
        if (onWhite) {
            ChhatraLekhaMark(size = markSize)
        } else {
            ChhatraLekhaPlate(markSize = markSize, platePadding = 5.dp, radius = 9.dp)
        }
        Spacer(Modifier.width(10.dp))
        Column {
            Text(
                text = "ChhatraLekha",
                style = MaterialTheme.typography.titleSmall,
                color = wordColor,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.2.sp
            )
            if (subText.isNotBlank()) {
                Text(
                    text = subText,
                    style = MaterialTheme.typography.labelSmall,
                    color = subColor,
                    letterSpacing = 0.6.sp
                )
            }
        }
    }
}
