package com.acadentrix.core.qr

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Round-trip proof that [QrEncoder] emits standards-compliant QR symbols.
 *
 * The decoder below is deliberately independent of the encoder: it re-derives
 * the function-pattern map, the data-module placement order, the Reed-Solomon
 * block layout and the payload framing from ISO/IEC 18004 rather than reusing
 * [QrEncoder] internals. Decoding a symbol therefore proves that the encoder
 * produces a *valid* symbol and not merely a self-consistent one.
 */
class QrRoundTripTest {

    @Test
    fun encodesAndDecodesShortPayload() {
        val matrix = QrEncoder.encode("APAAR")
        assertEquals("APAAR", ReferenceQrDecoder.decode(matrix))
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
        assertEquals(payload, ReferenceQrDecoder.decode(matrix))
    }

    @Test
    fun encodesAndDecodesAcrossEveryErrorCorrectionLevel() {
        val text = "AICTE|984210357890|INST-0421|BTECH_CSE|2024-25|2024-08-01"
        QrEncoder.EcLevel.entries.forEach { level ->
            val matrix = QrEncoder.encode(text, level)
            assertEquals(level, matrix.ecLevel)
            assertEquals(text, ReferenceQrDecoder.decode(matrix))
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
            assertEquals("payload length $length", text, ReferenceQrDecoder.decode(matrix))
        }
    }

    @Test
    fun appliesTheSelectedMaskExactlyOnce() {
        // A double-applied mask would XOR the data modules back to their
        // unmasked state. The reference decoder would then read the format
        // bits with a mask that no longer matches the payload and the
        // Reed-Solomon syndromes would not vanish.
        val matrix = QrEncoder.encode("MASK-CHECK-984210357890")
        val decodedMask = ReferenceQrDecoder.readMask(matrix)
        assertEquals(matrix.mask, decodedMask)
        assertEquals("MASK-CHECK-984210357890", ReferenceQrDecoder.decode(matrix))
    }

    @Test
    fun formatBitsCarryTheEcLevelAndMask() {
        for (level in QrEncoder.EcLevel.entries) {
            val matrix = QrEncoder.encode("LEVEL-$level", level)
            assertEquals(level, ReferenceQrDecoder.readEcLevel(matrix))
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
}

/**
 * An independent QR Code Model 2 decoder used only by the tests.
 */
internal object ReferenceQrDecoder {

    // ------------------------------------------------------------- GF(256)

    private val EXP = IntArray(512)
    private val LOG = IntArray(256)

    init {
        var x = 1
        for (i in 0 until 255) {
            EXP[i] = x
            LOG[x] = i
            x = x shl 1
            if (x and 0x100 != 0) x = x xor 0x11D
        }
        for (i in 255 until 512) EXP[i] = EXP[i - 255]
    }

    private fun mul(a: Int, b: Int): Int = if (a == 0 || b == 0) 0 else EXP[LOG[a] + LOG[b]]

    private fun alphaPower(exponent: Int): Int {
        var result = 1
        var base = 2
        var e = exponent
        while (e > 0) {
            if (e and 1 == 1) result = mul(result, base)
            base = mul(base, base)
            e = e shr 1
        }
        return result
    }

    // -------------------------------------------------------------- tables

    private val ECC_CODEWORDS_PER_BLOCK = arrayOf(
        intArrayOf(-1, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28, 28, 28, 30, 30, 26, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30),
        intArrayOf(-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28),
        intArrayOf(-1, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24, 28, 26, 24, 20, 30, 24, 28, 28, 26, 30, 28, 30, 30, 30, 30, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30),
        intArrayOf(-1, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28, 30, 24, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30)
    )

    private val NUM_ERROR_CORRECTION_BLOCKS = arrayOf(
        intArrayOf(-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4, 4, 4, 4, 4, 6, 6, 6, 6, 7, 8, 8, 9, 9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 19, 20, 21, 22, 24, 25),
        intArrayOf(-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49),
        intArrayOf(-1, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8, 8, 10, 12, 16, 12, 17, 16, 18, 21, 20, 23, 23, 25, 27, 29, 34, 34, 35, 38, 40, 43, 45, 48, 51, 53, 56, 59, 62, 65, 68),
        intArrayOf(-1, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25, 25, 34, 30, 32, 35, 37, 40, 42, 45, 48, 51, 54, 57, 60, 63, 66, 70, 74, 77, 81)
    )

    private fun ecIndex(level: QrEncoder.EcLevel): Int = level.ordinal

    private fun rawDataModules(version: Int): Int {
        var result = (16 * version + 128) * version + 64
        if (version >= 2) {
            val numAlign = version / 7 + 2
            result -= (25 * numAlign - 10) * numAlign - 55
            if (version >= 7) result -= 36
        }
        return result
    }

    private fun alignmentPositions(version: Int): IntArray {
        if (version == 1) return IntArray(0)
        val numAlign = version / 7 + 2
        val step = if (version == 32) 26 else (version * 4 + numAlign * 2 + 1) / (numAlign * 2 - 2) * 2
        val result = IntArray(numAlign)
        result[0] = 6
        for (i in result.size - 1 downTo 1) {
            result[i] = version * 4 + 10 - step * (result.size - 1 - i)
        }
        return result
    }

    // -------------------------------------------------------- function map

    private fun buildFunctionMap(version: Int, size: Int): Array<BooleanArray> {
        val map = Array(size) { BooleanArray(size) }
        fun mark(x: Int, y: Int) {
            if (x in 0 until size && y in 0 until size) map[y][x] = true
        }

        // Finder patterns together with their separators. A QR symbol carries
        // only three of them — the bottom-right corner holds data.
        val finderCentres = listOf(
            3 to 3,
            size - 4 to 3,
            3 to size - 4
        )
        for ((cx, cy) in finderCentres) {
            for (dy in -4..4) for (dx in -4..4) mark(cx + dx, cy + dy)
        }
        // Timing patterns.
        for (i in 0 until size) {
            mark(6, i)
            mark(i, 6)
        }
        // Alignment patterns (except the three that overlap the finders).
        val positions = alignmentPositions(version)
        for (i in positions.indices) {
            for (j in positions.indices) {
                val overlaps = (i == 0 && j == 0) ||
                    (i == 0 && j == positions.size - 1) ||
                    (i == positions.size - 1 && j == 0)
                if (overlaps) continue
                for (dy in -2..2) for (dx in -2..2) mark(positions[i] + dx, positions[j] + dy)
            }
        }
        // Format information (both copies) and the permanently dark module.
        for (i in 0..8) {
            mark(8, i)
            mark(i, 8)
        }
        for (i in 0..7) mark(size - 1 - i, 8)
        for (i in 8..14) mark(8, size - 15 + i)
        mark(8, size - 8)
        // Version information.
        if (version >= 7) {
            for (i in 0..17) {
                mark(size - 11 + i % 3, i / 3)
                mark(i / 3, size - 11 + i % 3)
            }
        }
        return map
    }

    // ---------------------------------------------------------- format info

    fun readMask(matrix: QrEncoder.QrMatrix): Int = readFormat(matrix).second

    fun readEcLevel(matrix: QrEncoder.QrMatrix): QrEncoder.EcLevel {
        val (ecBits, _) = readFormat(matrix)
        return when (ecBits) {
            0b01 -> QrEncoder.EcLevel.LOW
            0b00 -> QrEncoder.EcLevel.MEDIUM
            0b11 -> QrEncoder.EcLevel.QUARTILE
            else -> QrEncoder.EcLevel.HIGH
        }
    }

    private fun readFormat(matrix: QrEncoder.QrMatrix): Pair<Int, Int> {
        val modules = matrix.modules
        val size = matrix.size
        val bits = BooleanArray(15)
        for (i in 0..5) bits[i] = modules[i][8]
        bits[6] = modules[7][8]
        bits[7] = modules[8][8]
        bits[8] = modules[8][7]
        for (i in 9..14) bits[i] = modules[8][14 - i]

        var raw = 0
        for (i in 0..14) if (bits[i]) raw = raw or (1 shl i)
        val unmasked = raw xor 0x5412
        val data = unmasked ushr 10
        return ((data ushr 3) and 0x3) to (data and 0x7)
    }

    // ------------------------------------------------------------- masking

    private fun maskCondition(mask: Int, x: Int, y: Int): Boolean = when (mask) {
        0 -> (x + y) % 2 == 0
        1 -> y % 2 == 0
        2 -> x % 3 == 0
        3 -> (x + y) % 3 == 0
        4 -> (x / 2 + y / 3) % 2 == 0
        5 -> x * y % 2 + x * y % 3 == 0
        6 -> (x * y % 2 + x * y % 3) % 2 == 0
        else -> ((x + y) % 2 + x * y % 3) % 2 == 0
    }

    // --------------------------------------------------------------- decode

    fun decode(matrix: QrEncoder.QrMatrix): String {
        val size = matrix.size
        val version = (size - 17) / 4
        val function = buildFunctionMap(version, size)
        val (ecBits, mask) = readFormat(matrix)
        val index = ecIndex(
            when (ecBits) {
                0b01 -> QrEncoder.EcLevel.LOW
                0b00 -> QrEncoder.EcLevel.MEDIUM
                0b11 -> QrEncoder.EcLevel.QUARTILE
                else -> QrEncoder.EcLevel.HIGH
            }
        )

        // --- unmask -------------------------------------------------------
        val plain = Array(size) { y -> BooleanArray(size) { x -> matrix.modules[y][x] } }
        for (y in 0 until size) {
            for (x in 0 until size) {
                if (function[y][x]) continue
                if (maskCondition(mask, x, y)) plain[y][x] = !plain[y][x]
            }
        }

        // --- read the interleaved codeword stream -------------------------
        val rawCodewords = rawDataModules(version) / 8
        val stream = ArrayList<Boolean>(rawCodewords * 8)
        var right = size - 1
        while (right >= 1) {
            if (right == 6) right = 5
            for (vert in 0 until size) {
                for (j in 0 until 2) {
                    val x = right - j
                    val upward = ((right + 1) and 2) == 0
                    val y = if (upward) size - 1 - vert else vert
                    if (!function[y][x]) stream.add(plain[y][x])
                }
            }
            right -= 2
        }

        // --- de-interleave into Reed-Solomon blocks ------------------------
        val numBlocks = NUM_ERROR_CORRECTION_BLOCKS[index][version]
        val blockEccLen = ECC_CODEWORDS_PER_BLOCK[index][version]
        val numShortBlocks = numBlocks - rawCodewords % numBlocks
        val shortBlockLen = rawCodewords / numBlocks
        val blocks = Array(numBlocks) { IntArray(shortBlockLen + 1) }

        var cursor = 0
        fun readByte(): Int {
            var value = 0
            repeat(8) {
                value = (value shl 1) or (if (cursor < stream.size && stream[cursor]) 1 else 0)
                cursor++
            }
            return value
        }

        val maxDataCodewords = shortBlockLen - blockEccLen + 1
        for (i in 0 until maxDataCodewords) {
            for (block in 0 until numBlocks) {
                val dataLen = shortBlockLen - blockEccLen + (if (block < numShortBlocks) 0 else 1)
                if (i >= dataLen) continue
                blocks[block][i] = readByte()
            }
        }
        for (i in 0 until blockEccLen) {
            for (block in 0 until numBlocks) {
                val dataLen = shortBlockLen - blockEccLen + (if (block < numShortBlocks) 0 else 1)
                blocks[block][dataLen + i] = readByte()
            }
        }

        // --- verify the Reed-Solomon syndromes ------------------------------
        // The codeword polynomial is d0*x^(n-1) + ... + dn-1*x^k + e0*x^(k-1) + ...
        // so Horner's method must walk the codeword from the FIRST data codeword
        // (highest degree) towards the last error-correction codeword.
        for (block in 0 until numBlocks) {
            val dataLen = shortBlockLen - blockEccLen + (if (block < numShortBlocks) 0 else 1)
            val codeword = blocks[block].copyOf(dataLen + blockEccLen)
            for (i in 0 until blockEccLen) {
                val root = alphaPower(i)
                var syndrome = 0
                for (j in codeword.indices) {
                    syndrome = mul(syndrome, root) xor codeword[j]
                }
                check(syndrome == 0) {
                    "Reed-Solomon syndrome $i of block $block is 0x${syndrome.toString(16)} (expected 0)."
                }
            }
        }

        // --- recover the data codewords ------------------------------------
        val dataBytes = ArrayList<Int>(rawCodewords)
        for (block in 0 until numBlocks) {
            val dataLen = shortBlockLen - blockEccLen + (if (block < numShortBlocks) 0 else 1)
            for (i in 0 until dataLen) dataBytes.add(blocks[block][i])
        }

        // --- parse the bit stream ------------------------------------------
        val dataBits = ArrayList<Boolean>(dataBytes.size * 8)
        for (byte in dataBytes) {
            for (k in 7 downTo 0) dataBits.add((byte ushr k) and 1 == 1)
        }
        var p = 0
        fun take(count: Int): Int {
            var value = 0
            repeat(count) {
                value = (value shl 1) or (if (p < dataBits.size && dataBits[p]) 1 else 0)
                p++
            }
            return value
        }

        val mode = take(4)
        check(mode == 0b0100) { "Unexpected QR mode 0b${mode.toString(2)} — only byte mode is supported." }
        val characterCountBits = if (version <= 9) 8 else 16
        val characterCount = take(characterCountBits)
        val out = ByteArray(characterCount)
        for (i in 0 until characterCount) out[i] = take(8).toByte()
        return String(out, Charsets.UTF_8)
    }
}
