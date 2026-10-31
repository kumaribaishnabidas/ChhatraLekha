package com.chhatralekha.core.qr

/**
 * A dependency-free QR Code (ISO/IEC 18004) encoder used to render the
 * APAAR Digital Academic Identity Card badge.
 *
 * Supports byte mode, versions 1-40 and all four error-correction levels.
 */
object QrEncoder {

    enum class EcLevel(val formatBits: Int, val label: String) {
        LOW(0b01, "L"),
        MEDIUM(0b00, "M"),
        QUARTILE(0b11, "Q"),
        HIGH(0b10, "H")
    }

    /**
     * Result of an encode operation.
     */
    class QrMatrix internal constructor(
        val size: Int,
        val version: Int,
        val ecLevel: EcLevel,
        mask: Int
    ) {
        /** The data mask ultimately applied to the symbol (0-7). */
        var mask: Int = mask
            internal set
        internal val modules: Array<BooleanArray> = Array(size) { BooleanArray(size) }
        internal val functionModules: Array<BooleanArray> = Array(size) { BooleanArray(size) }

        fun isDark(x: Int, y: Int): Boolean =
            x in 0 until size && y in 0 until size && modules[y][x]

        /** Renders the matrix as a plain string of '0'/'1' rows (used by tests). */
        fun toAscii(): String = (0 until size).joinToString("\n") { y ->
            (0 until size).joinToString("") { x -> if (modules[y][x]) "1" else "0" }
        }
    }

    class QrEncodingException(message: String) : IllegalArgumentException(message)

    // ------------------------------------------------------------- tables

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

    // ------------------------------------------------------------- GF(256)

    private val GF_EXP = IntArray(512)
    private val GF_LOG = IntArray(256)

    init {
        var x = 1
        for (i in 0 until 255) {
            GF_EXP[i] = x
            GF_LOG[x] = i
            x = x shl 1
            if (x and 0x100 != 0) x = x xor 0x11D
        }
        for (i in 255 until 512) GF_EXP[i] = GF_EXP[i - 255]
    }

    private fun gfMultiply(a: Int, b: Int): Int {
        if (a == 0 || b == 0) return 0
        return GF_EXP[GF_LOG[a] + GF_LOG[b]]
    }

    // ------------------------------------------------------------- helpers

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

    private fun capacityBits(version: Int, ecLevel: EcLevel): Int {
        val blocks = NUM_ERROR_CORRECTION_BLOCKS[ecLevel.ordinal][version]
        val eccLen = ECC_CODEWORDS_PER_BLOCK[ecLevel.ordinal][version]
        val rawCodewords = rawDataModules(version) / 8
        val dataCodewords = rawCodewords - eccLen * blocks
        val ccBits = if (version <= 9) 8 else 16
        return dataCodewords * 8 - 4 - ccBits
    }

    // ------------------------------------------------------------- encode

    fun encode(text: String, ecLevel: EcLevel = EcLevel.MEDIUM, minVersion: Int = 1): QrMatrix {
        val bytes = text.toByteArray(Charsets.UTF_8)
        var version = minVersion.coerceAtLeast(1)
        while (version <= 40 && capacityBits(version, ecLevel) < bytes.size * 8) version++
        if (version > 40) throw QrEncodingException("Payload is too large for a QR code (${bytes.size} bytes).")

        val dataCapacityBits = capacityBits(version, ecLevel)
        val ccBits = if (version <= 9) 8 else 16

        // --- build the raw bit stream -------------------------------------
        val bits = ArrayList<Boolean>(dataCapacityBits + 64)
        fun append(value: Int, length: Int) {
            for (i in length - 1 downTo 0) bits.add((value ushr i) and 1 == 1)
        }
        append(0b0100, 4)                    // byte mode
        append(bytes.size, ccBits)           // character count indicator
        for (byte in bytes) append(byte.toInt() and 0xFF, 8)

        val capacity = dataCapacityBits + 4 + ccBits
        // terminator
        val terminator = minOf(4, capacity - bits.size)
        repeat(terminator) { bits.add(false) }
        // pad to byte boundary
        while (bits.size % 8 != 0) bits.add(false)
        // pad bytes
        var padByte = 0xEC
        while (bits.size < capacity) {
            append(padByte, 8)
            padByte = padByte xor 0xFD // 0xEC <-> 0x11
        }

        val dataCodewords = IntArray(bits.size / 8)
        for (i in dataCodewords.indices) {
            var value = 0
            for (j in 0 until 8) if (bits[i * 8 + j]) value = value or (1 shl (7 - j))
            dataCodewords[i] = value
        }

        val interleaved = addEccAndInterleave(dataCodewords, version, ecLevel)
        val matrix = QrMatrix(4 * version + 17, version, ecLevel, 0)
        drawFunctionPatterns(matrix, version, ecLevel)
        drawCodewords(matrix, interleaved)
        val mask = selectMask(matrix, version)
        matrix.mask = mask
        applyMask(matrix, mask)
        drawFormatBits(matrix, ecLevel, mask)
        return matrix
    }

    private fun addEccAndInterleave(data: IntArray, version: Int, ecLevel: EcLevel): BooleanArray {
        val numBlocks = NUM_ERROR_CORRECTION_BLOCKS[ecLevel.ordinal][version]
        val blockEccLen = ECC_CODEWORDS_PER_BLOCK[ecLevel.ordinal][version]
        val rawCodewords = rawDataModules(version) / 8
        val numShortBlocks = numBlocks - rawCodewords % numBlocks
        val shortBlockLen = rawCodewords / numBlocks

        val generator = reedSolomonDivisor(blockEccLen)
        // Each block holds (data codewords + error-correction codewords) *bytes*;
        // the buffer below stores one Boolean per *bit*.
        val blocks = Array(numBlocks) { BooleanArray((shortBlockLen + 1) * 8) }
        var k = 0
        for (block in 0 until numBlocks) {
            val dataLen = shortBlockLen - blockEccLen + (if (block < numShortBlocks) 0 else 1)
            val chunk = IntArray(dataLen)
            for (i in 0 until dataLen) {
                chunk[i] = data[k]
                k++
            }
            val ecc = reedSolomonRemainder(chunk, generator)
            val blockData = BooleanArray((shortBlockLen + 1) * 8)
            var bitIndex = 0
            for (i in 0 until dataLen) {
                for (b in 7 downTo 0) blockData[bitIndex++] = (chunk[i] ushr b) and 1 == 1
            }
            for (value in ecc) {
                for (b in 7 downTo 0) blockData[bitIndex++] = (value ushr b) and 1 == 1
            }
            blocks[block] = blockData
        }

        val result = BooleanArray(rawCodewords * 8)
        var index = 0
        val maxDataCodewords = shortBlockLen - blockEccLen + 1
        // Data codewords are interleaved first, column-wise across every block.
        for (i in 0 until maxDataCodewords) {
            for (block in 0 until numBlocks) {
                val dataLen = shortBlockLen - blockEccLen + (if (block < numShortBlocks) 0 else 1)
                if (i >= dataLen) continue
                for (b in 0 until 8) result[index++] = blocks[block][i * 8 + b]
            }
        }
        // Error-correction codewords follow, column-wise across every block.
        for (i in 0 until blockEccLen) {
            for (block in 0 until numBlocks) {
                val dataLen = shortBlockLen - blockEccLen + (if (block < numShortBlocks) 0 else 1)
                val start = dataLen * 8
                for (b in 0 until 8) result[index++] = blocks[block][start + i * 8 + b]
            }
        }
        return result
    }

    // ------------------------------------------------------- Reed-Solomon

    /**
     * Builds the Reed-Solomon divisor polynomial, coefficients low-degree first,
     * with the leading coefficient (x^degree) equal to 1.
     */
    private fun reedSolomonDivisor(degree: Int): IntArray {
        var poly = intArrayOf(1)
        var root = 1
        repeat(degree) {
            val next = IntArray(poly.size + 1)
            for (j in poly.indices) {
                next[j] = next[j] xor gfMultiply(poly[j], root)
                next[j + 1] = next[j + 1] xor poly[j]
            }
            poly = next
            root = gfMultiply(root, 0x02)
        }
        return poly
    }

    private fun reedSolomonRemainder(data: IntArray, generator: IntArray): IntArray {
        val eccLen = generator.size - 1
        val result = IntArray(eccLen)
        for (value in data) {
            val factor = value xor result[0]
            for (i in 0 until eccLen - 1) result[i] = result[i + 1]
            result[eccLen - 1] = 0
            for (i in 0 until eccLen) {
                // generator is low-degree-first; the leading 1 coefficient is implicit
                result[i] = result[i] xor gfMultiply(generator[eccLen - 1 - i], factor)
            }
        }
        return result
    }

    // --------------------------------------------------------- drawing

    private fun drawFunctionPatterns(matrix: QrMatrix, version: Int, ecLevel: EcLevel) {
        val size = matrix.size

        // Timing patterns
        for (i in 0 until size) {
            matrix.setFunction(6, i, i % 2 == 0)
            matrix.setFunction(i, 6, i % 2 == 0)
        }

        // Finder patterns (centred at 3,3 / size-4,3 / 3,size-4)
        drawFinder(matrix, 3, 3)
        drawFinder(matrix, size - 4, 3)
        drawFinder(matrix, 3, size - 4)

        // Alignment patterns
        val positions = alignmentPositions(version)
        val n = positions.size
        for (i in 0 until n) {
            for (j in 0 until n) {
                val overlapsFinder = (i == 0 && j == 0) ||
                    (i == 0 && j == n - 1) ||
                    (i == n - 1 && j == 0)
                if (!overlapsFinder) drawAlignment(matrix, positions[i], positions[j])
            }
        }

        // Reserve the format / version information areas before data placement.
        drawFormatBits(matrix, ecLevel, 0)
        drawVersionBits(matrix, version)
    }

    private fun drawFinder(matrix: QrMatrix, cx: Int, cy: Int) {
        for (dy in -4..4) {
            for (dx in -4..4) {
                val dist = maxOf(kotlin.math.abs(dx), kotlin.math.abs(dy))
                val x = cx + dx
                val y = cy + dy
                if (x in 0 until matrix.size && y in 0 until matrix.size) {
                    matrix.setFunction(x, y, dist != 2 && dist != 4)
                }
            }
        }
    }

    private fun drawAlignment(matrix: QrMatrix, cx: Int, cy: Int) {
        for (dy in -2..2) {
            for (dx in -2..2) {
                val dist = maxOf(kotlin.math.abs(dx), kotlin.math.abs(dy))
                matrix.setFunction(cx + dx, cy + dy, dist != 1)
            }
        }
    }

    private fun drawCodewords(matrix: QrMatrix, data: BooleanArray) {
        var i = 0
        val size = matrix.size
        var right = size - 1
        while (right >= 1) {
            if (right == 6) right = 5
            for (vert in 0 until size) {
                for (j in 0 until 2) {
                    val x = right - j
                    val upward = ((right + 1) and 2) == 0
                    val y = if (upward) size - 1 - vert else vert
                    if (!matrix.functionModules[y][x] && i < data.size) {
                        matrix.modules[y][x] = data[i]
                        i++
                    }
                }
            }
            right -= 2
        }
    }

    private fun applyMask(matrix: QrMatrix, mask: Int) {
        for (y in 0 until matrix.size) {
            for (x in 0 until matrix.size) {
                if (matrix.functionModules[y][x]) continue
                val invert = when (mask) {
                    0 -> (x + y) % 2 == 0
                    1 -> y % 2 == 0
                    2 -> x % 3 == 0
                    3 -> (x + y) % 3 == 0
                    4 -> (x / 2 + y / 3) % 2 == 0
                    5 -> x * y % 2 + x * y % 3 == 0
                    6 -> (x * y % 2 + x * y % 3) % 2 == 0
                    else -> ((x + y) % 2 + x * y % 3) % 2 == 0
                }
                if (invert) matrix.modules[y][x] = !matrix.modules[y][x]
            }
        }
    }

    private fun drawFormatBits(matrix: QrMatrix, ecLevel: EcLevel, mask: Int) {
        val size = matrix.size
        val data = ecLevel.formatBits shl 3 or mask
        var rem = data
        for (i in 0 until 10) {
            rem = (rem shl 1) xor ((rem ushr 9) * 0x537)
        }
        val bits = ((data shl 10) or rem) xor 0x5412

        for (i in 0..5) matrix.setFunction(8, i, bitAt(bits, i))
        matrix.setFunction(8, 7, bitAt(bits, 6))
        matrix.setFunction(8, 8, bitAt(bits, 7))
        matrix.setFunction(7, 8, bitAt(bits, 8))
        for (i in 9..14) matrix.setFunction(14 - i, 8, bitAt(bits, i))

        for (i in 0..7) matrix.setFunction(size - 1 - i, 8, bitAt(bits, i))
        for (i in 8..14) matrix.setFunction(8, size - 15 + i, bitAt(bits, i))

        matrix.setFunction(8, size - 8, true) // permanently dark module
    }

    private fun drawVersionBits(matrix: QrMatrix, version: Int) {
        if (version < 7) return
        var rem = version
        for (i in 0 until 12) {
            rem = (rem shl 1) xor ((rem ushr 11) * 0x1F25)
        }
        val bits = (version shl 12) or rem
        for (i in 0 until 18) {
            val dark = bitAt(bits, i)
            val a = matrix.size - 11 + i % 3
            val b = i / 3
            matrix.setFunction(a, b, dark)
            matrix.setFunction(b, a, dark)
        }
    }

    private fun bitAt(value: Int, index: Int): Boolean = (value ushr index) and 1 == 1

    // ------------------------------------------------------- mask scoring

    /**
     * Scores all eight masks and returns the best one.
     *
     * The matrix is left **unmasked** on return — [encode] applies the winning
     * mask exactly once. Applying it here as well would XOR the modules twice
     * and silently cancel the mask out.
     */
    private fun selectMask(matrix: QrMatrix, version: Int): Int {
        var bestMask = 0
        var bestPenalty = Int.MAX_VALUE
        for (mask in 0 until 8) {
            applyMask(matrix, mask)
            drawFormatBits(matrix, matrix.ecLevel, mask)
            drawVersionBits(matrix, version)
            val penalty = penaltyScore(matrix)
            if (penalty < bestPenalty) {
                bestPenalty = penalty
                bestMask = mask
            }
            applyMask(matrix, mask) // XOR is its own inverse -> revert
        }
        return bestMask
    }

    private fun penaltyScore(matrix: QrMatrix): Int {
        val size = matrix.size
        var penalty = 0

        // Rule 1 — runs of five or more identical modules
        for (y in 0 until size) {
            var run = 1
            for (x in 1 until size) {
                if (matrix.modules[y][x] == matrix.modules[y][x - 1]) {
                    run++
                } else {
                    if (run >= 5) penalty += 3 + (run - 5)
                    run = 1
                }
            }
            if (run >= 5) penalty += 3 + (run - 5)
        }
        for (x in 0 until size) {
            var run = 1
            for (y in 1 until size) {
                if (matrix.modules[y][x] == matrix.modules[y - 1][x]) {
                    run++
                } else {
                    if (run >= 5) penalty += 3 + (run - 5)
                    run = 1
                }
            }
            if (run >= 5) penalty += 3 + (run - 5)
        }

        // Rule 2 — 2x2 blocks of identical modules
        for (y in 0 until size - 1) {
            for (x in 0 until size - 1) {
                val c = matrix.modules[y][x]
                if (c == matrix.modules[y][x + 1] && c == matrix.modules[y + 1][x] && c == matrix.modules[y + 1][x + 1]) {
                    penalty += 3
                }
            }
        }

        // Rule 3 — finder-like 1:1:3:1:1 patterns
        val patternA = intArrayOf(1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0)
        val patternB = intArrayOf(0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1)
        for (y in 0 until size) {
            for (x in 0..size - 11) {
                var matchA = true
                var matchB = true
                for (i in 0 until 11) {
                    val dark = matrix.modules[y][x + i]
                    if (dark != (patternA[i] == 1)) matchA = false
                    if (dark != (patternB[i] == 1)) matchB = false
                }
                if (matchA) penalty += 40
                if (matchB) penalty += 40
            }
        }
        for (x in 0 until size) {
            for (y in 0..size - 11) {
                var matchA = true
                var matchB = true
                for (i in 0 until 11) {
                    val dark = matrix.modules[y + i][x]
                    if (dark != (patternA[i] == 1)) matchA = false
                    if (dark != (patternB[i] == 1)) matchB = false
                }
                if (matchA) penalty += 40
                if (matchB) penalty += 40
            }
        }

        // Rule 4 — balance between dark and light modules
        var dark = 0
        for (y in 0 until size) for (x in 0 until size) if (matrix.modules[y][x]) dark++
        val total = size * size
        val k = (kotlin.math.abs(dark * 20 - total * 10) + total - 1) / total - 1
        penalty += k * 10
        return penalty
    }
}

/**
 * Internal helper that marks a module as a function (reserved) module.
 */
private fun QrEncoder.QrMatrix.setFunction(x: Int, y: Int, dark: Boolean) {
    modules[y][x] = dark
    functionModules[y][x] = true
}
