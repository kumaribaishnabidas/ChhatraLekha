package com.acadentrix.core.qr

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Round-trip proof that [QrEncoder] emits standards-compliant QR symbols.
 *
 * The decoder lives in the main source set and re-derives the
 * function-pattern map, the data-module placement order, the Reed-Solomon
 * block layout and the payload framing from ISO/IEC 18004 rather than reusing
 * [QrEncoder] internals. Decoding a symbol therefore proves that the encoder
 * produces a *valid* symbol and not merely a self-consistent one.
 */
class QrRoundTripTest {

    @Test
    fun encodesAndDecodesShortPayload() {
        val matrix = QrEncoder.encode("APAAR")
        assertEquals("APAAR", QrDecoder.decode(matrix))
    }

    @Test
    fun encodesAndDecodesTheRealCredentialPayload() {
        val payload = ApaarQrPayload.build(
            apaarId = "984210357890",
            institutionId = "INST-0421",
            programId = "BTECH_CSE",
            seal = "A1B2C3D4E5F60718293A4B5C6D7E8F90",
            timestamp = 1_726_000_000_000L
        )
        val matrix = QrEncoder.encode(payload)
        assertEquals(payload, QrDecoder.decode(matrix))
    }

    @Test
    fun encodesAndDecodesAcrossEveryErrorCorrectionLevel() {
        val text = "AICTE|984210357890|INST-0421|BTECH_CSE|2024-25|2024-08-01"
        QrEncoder.EcLevel.entries.forEach { level ->
            val matrix = QrEncoder.encode(text, level)
            assertEquals(level, matrix.ecLevel)
            assertEquals(text, QrDecoder.decode(matrix))
        }
    }

    @Test
    fun encodesAndDecodesAcrossManyPayloadLengths() {
        // Sweep the payload length so that several symbol versions and block
        // layouts (1 block, 2 blocks, mixed short/long blocks) are exercised.
        for (length in 1..400 step 7) {
            val text = buildString {
                repeat(length) { append("APAAR".toCharArray()[it % 5]) }
            }
            val matrix = QrEncoder.encode(text)
            assertEquals("payload length $length", text, QrDecoder.decode(matrix))
        }
    }

    @Test
    fun appliesTheSelectedMaskExactlyOnce() {
        // A double-applied mask would XOR the data modules back to their
        // unmasked state. The reference decoder would then read the format
        // bits with a mask that no longer matches the payload and the
        // Reed-Solomon syndromes would not vanish.
        val matrix = QrEncoder.encode("MASK-CHECK-984210357890")
        val decodedMask = QrDecoder.readMask(matrix.modules)
        assertEquals(matrix.mask, decodedMask)
        assertEquals("MASK-CHECK-984210357890", QrDecoder.decode(matrix))
    }

    @Test
    fun formatBitsCarryTheEcLevelAndMask() {
        for (level in QrEncoder.EcLevel.entries) {
            val matrix = QrEncoder.encode("LEVEL-$level", level)
            assertEquals(level, QrDecoder.readEcLevel(matrix.modules))
        }
    }

    @Test
    fun growsTheSymbolVersionWithThePayload() {
        val small = QrEncoder.encode("A")
        val large = QrEncoder.encode("A".repeat(600))
        assertTrue(small.version < large.version)
        assertEquals(4 * small.version + 17, small.size)
        assertEquals(4 * large.version + 17, large.size)
    }

    @Test
    fun rejectsPayloadsThatExceedTheMaximumVersion() {
        val failure = runCatching { QrEncoder.encode("A".repeat(5000)) }.exceptionOrNull()
        assertTrue(failure is QrEncoder.QrEncodingException)
    }

    // --------------------------------------------------------- image decoding

    @Test
    fun decodesASymbolThatWasRenderedIntoAPicture() {
        val payload = "https://apaar.aicte-india.gov.in/verify?apaar=984210357890&seal=ABC123"
        val matrix = QrEncoder.encode(payload)
        val (image, width, height) = render(matrix)
        assertEquals(payload, QrDecoder.decodeImage(image, width, height))
    }

    @Test
    fun decodesASymbolThatWasPhotographedAtADifferentScale() {
        val payload = "https://apaar.aicte-india.gov.in/verify?apaar=984210357890&seal=ABC123"
        val matrix = QrEncoder.encode(payload)
        val (image, width, height) = render(matrix, scale = 6)
        assertEquals(payload, QrDecoder.decodeImage(image, width, height))
    }

    @Test
    fun decodesASymbolThroughTheLuminanceThreshold() {
        val payload = "AICTE|984210357890|INST-0421"
        val matrix = QrEncoder.encode(payload)
        val (image, width, height) = render(matrix, scale = 5)
        val luminance = IntArray(width * height) { if (image[it]) 0 else 255 }
        val binary = QrDecoder.binarise(luminance, width, height)
        assertEquals(payload, QrDecoder.decodeImage(binary, width, height))
    }

    @Test
    fun reportsNoSymbolWhenThePictureIsBlank() {
        val image = BooleanArray(200 * 200)
        assertNull(QrDecoder.decodeImage(image, 200, 200))
    }

    @Test
    fun rejectsAGridThatIsNotAValidSymbolSize() {
        val failure = runCatching { QrDecoder.decodeGrid(Array(20) { BooleanArray(20) }) }.exceptionOrNull()
        assertTrue(failure is QrDecoder.QrDecodingException)
    }

    @Test
    fun refusesToDecodeASymbolWhoseModulesWereAltered() {
        // Flipping a single module breaks the Reed-Solomon syndromes, which is
        // exactly what the error-correction level is there to detect.
        val matrix = QrEncoder.encode("TAMPER-PAYLOAD-984210357890")
        val modules = Array(matrix.size) { y -> BooleanArray(matrix.size) { x -> matrix.isDark(x, y) } }
        // The bottom-right module always carries payload bits (the only dark
        // module that is not part of a function pattern sits at (8, 4v+9)).
        modules[matrix.size - 1][matrix.size - 1] = !modules[matrix.size - 1][matrix.size - 1]
        val corrupted = runCatching { QrDecoder.decodeGrid(modules) }
        assertNotNull(corrupted.exceptionOrNull())
    }

    // --------------------------------------------------------------- helpers

    /**
     * Renders a symbol into a black-and-white picture with a quiet zone, the
     * way it would appear on a printed badge or a screen.
     */
    private fun render(
        matrix: QrEncoder.QrMatrix,
        scale: Int = 4,
        quietZone: Int = 4
    ): Triple<BooleanArray, Int, Int> {
        val size = (matrix.size + quietZone * 2) * scale
        val image = BooleanArray(size * size)
        for (y in 0 until matrix.size) {
            for (x in 0 until matrix.size) {
                if (!matrix.isDark(x, y)) continue
                for (dy in 0 until scale) {
                    for (dx in 0 until scale) {
                        val px = (x + quietZone) * scale + dx
                        val py = (y + quietZone) * scale + dy
                        image[py * size + px] = true
                    }
                }
            }
        }
        return Triple(image, size, size)
    }
}
