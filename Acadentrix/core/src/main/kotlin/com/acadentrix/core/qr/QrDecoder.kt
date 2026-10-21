package com.acadentrix.core.qr

/**
 * A dependency-free QR Code (ISO/IEC 18004) decoder.
 *
 * The decoder re-derives the function-pattern map, the data-module placement
 * order, the Reed-Solomon block layout and the payload framing from the
 * standard rather than reusing [QrEncoder] internals, so decoding an encoded
 * symbol proves that the encoder produces a *valid* symbol and not merely a
 * self-consistent one.
 *
 * Three levels of input are supported:
 *
 *  * [decode] — a symbol that is already a module grid.
 *  * [decodeImage] — a photographed or screenshotted symbol; the three finder
 *    patterns are located, the symbol version is derived from them and the
 *    module grid is sampled back out of the picture.
 *  * [binarise] — the luminance-to-bitmap step that goes with [decodeImage].
 */
object QrDecoder {

    /** Raised when a symbol cannot be read. */
    class QrDecodingException(message: String) : IllegalArgumentException(message)

    // --------------------------------------------------------------- GF(256)

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

    // --------------------------------------------------------------- tables

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

    // ---------------------------------------------------------- function map

    private fun buildFunctionMap(version: Int, size: Int): Array<BooleanArray> {
        val map = Array(size) { BooleanArray(size) }
        fun mark(x: Int, y: Int) {
            if (x in 0 until size && y in 0 until size) map[y][x] = true
        }

        // Finder patterns together with their separators. A QR symbol carries
        // only three of them — the bottom-right corner holds data.
        val finderCentres = listOf(3 to 3, size - 4 to 3, 3 to size - 4)
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

    /** The data mask the symbol was encoded with (0-7). */
    fun readMask(modules: Array<BooleanArray>): Int = readFormat(modules).second

    /** The error-correction level the symbol was encoded with. */
    fun readEcLevel(modules: Array<BooleanArray>): QrEncoder.EcLevel {
        val (ecBits, _) = readFormat(modules)
        return ecLevelFor(ecBits)
    }

    private fun ecLevelFor(ecBits: Int): QrEncoder.EcLevel = when (ecBits) {
        0b01 -> QrEncoder.EcLevel.LOW
        0b00 -> QrEncoder.EcLevel.MEDIUM
        0b11 -> QrEncoder.EcLevel.QUARTILE
        else -> QrEncoder.EcLevel.HIGH
    }

    private fun readFormat(modules: Array<BooleanArray>): Pair<Int, Int> {
        val size = modules.size
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

    // --------------------------------------------------------------- masking

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

    // ---------------------------------------------------------------- decode

    /** Decodes a symbol that was produced by [QrEncoder]. */
    fun decode(matrix: QrEncoder.QrMatrix): String = decodeGrid(matrix.modules)

    /**
     * Decodes a symbol from its module grid.
     *
     * @param modules the symbol, `modules[y][x]` is true for a dark module.
     */
    fun decodeGrid(modules: Array<BooleanArray>): String {
        val size = modules.size
        if (size < 21 || size % 4 != 1) {
            throw QrDecodingException("A QR symbol must be 4v+17 modules wide; got $size.")
        }
        val version = (size - 17) / 4
        val function = buildFunctionMap(version, size)
        val (ecBits, mask) = readFormat(modules)
        val index = ecLevelFor(ecBits).ordinal

        // --- unmask -------------------------------------------------------
        val plain = Array(size) { y -> BooleanArray(size) { x -> modules[y][x] } }
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
                if (syndrome != 0) {
                    throw QrDecodingException(
                        "Reed-Solomon syndrome $i of block $block is 0x${syndrome.toString(16)} (expected 0)."
                    )
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
        if (mode != 0b0100) {
            throw QrDecodingException("Unexpected QR mode 0b${mode.toString(2)} — only byte mode is supported.")
        }
        val characterCountBits = if (version <= 9) 8 else 16
        val characterCount = take(characterCountBits)
        val out = ByteArray(characterCount)
        for (i in 0 until characterCount) out[i] = take(8).toByte()
        return String(out, Charsets.UTF_8)
    }

    // --------------------------------------------------------------- imaging

    /**
     * Converts a luminance image into a black-and-white bitmap.
     *
     * A global threshold is not good enough for a photograph with a shadow, so
     * the mean of the image is used as the cut-off. The caller can pass a
     * bitmap that has already been thresholded.
     */
    fun binarise(luminance: IntArray, width: Int, height: Int): BooleanArray {
        require(luminance.size == width * height) { "Luminance buffer does not match the image size." }
        var sum = 0L
        for (value in luminance) sum += value
        val threshold = (sum / luminance.size).toInt()
        val out = BooleanArray(luminance.size)
        for (i in luminance.indices) out[i] = luminance[i] < threshold
        return out
    }

    /**
     * Locates a QR symbol inside a black-and-white image and decodes it.
     *
     * The three finder patterns are located by their 1:1:3:1:1 module ratio,
     * the symbol version is derived from the distance between them and the
     * module grid is then sampled back out of the picture.
     *
     * @return the decoded payload, or null when no readable symbol was found.
     */
    fun decodeImage(image: BooleanArray, width: Int, height: Int): String? {
        val finders = locateFinders(image, width, height)
        if (finders.size < 3) return null

        for (candidate in candidateCorners(finders)) {
            val (corner, first, second) = candidate
            // The two neighbours may be in either order depending on how the
            // symbol was rotated, so both orientations are attempted.
            for ((u, v) in listOf(first to second, second to first)) {
                val decoded = decodeWithFinders(image, width, height, corner, u, v)
                if (decoded != null) return decoded
            }
        }
        return null
    }

    /**
     * Samples the symbol that the three finder patterns describe and decodes
     * it.
     */
    private fun decodeWithFinders(
        image: BooleanArray,
        width: Int,
        height: Int,
        topLeft: Finder,
        topRight: Finder,
        bottomLeft: Finder
    ): String? {
        // The finder centres sit 3.5 modules in from the symbol edge, so the
        // distance between two of them spans (size - 7) modules.
        val spanX = distance(topLeft, topRight)
        val spanY = distance(topLeft, bottomLeft)
        if (spanX <= 0 || spanY <= 0) return null

        val finderModule = (topLeft.moduleSize + topRight.moduleSize + bottomLeft.moduleSize) / 3.0
        if (finderModule <= 0) return null

        val sizeModules = Math.round((spanX + spanY) / 2.0 / finderModule).toInt() + 7
        if (sizeModules < 21 || sizeModules % 4 != 1) return null
        val version = (sizeModules - 17) / 4
        if (version !in 1..40) return null

        // Re-derive the module size from the symbol extent; the finder estimate
        // is only used to pick the right version.
        val module = (spanX + spanY) / 2.0 / (sizeModules - 7)
        if (module <= 0.5) return null

        val ux = (topRight.x - topLeft.x) / spanX
        val uy = (topRight.y - topLeft.y) / spanX
        val vx = (bottomLeft.x - topLeft.x) / spanY
        val vy = (bottomLeft.y - topLeft.y) / spanY

        val grid = Array(sizeModules) { y -> BooleanArray(sizeModules) { x ->
            // Module (x, y) has its centre 3 modules in from the finder centre.
            val dx = (x - 3) * module
            val dy = (y - 3) * module
            val px = topLeft.x + ux * dx + vx * dy
            val py = topLeft.y + uy * dx + vy * dy
            sample(image, width, height, px, py)
        } }

        return runCatching { decodeGrid(grid) }.getOrNull()
    }

    /** Samples a single module centre with a 3x3 majority vote. */
    private fun sample(image: BooleanArray, width: Int, height: Int, px: Double, py: Double): Boolean {
        var dark = 0
        var total = 0
        for (dy in -1..1) {
            for (dx in -1..1) {
                val x = Math.round(px).toInt() + dx
                val y = Math.round(py).toInt() + dy
                if (x !in 0 until width || y !in 0 until height) continue
                total++
                if (image[y * width + x]) dark++
            }
        }
        if (total == 0) return false
        return dark * 2 > total
    }

    private data class Finder(
        val x: Double,
        val y: Double,
        val moduleSize: Double
    )

    private fun distance(a: Finder, b: Finder): Double =
        Math.sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y))

    /**
     * Finds the finder patterns in the image.
     *
     * A finder pattern is a 7x7 square with a 1:1:3:1:1 run-length ratio, so
     * every row and every column that crosses it shows that signature.
     */
    private fun locateFinders(image: BooleanArray, width: Int, height: Int): List<Finder> {
        val horizontal = mutableListOf<Finder>()
        for (y in 0 until height) {
            val row = BooleanArray(width) { image[y * width + it] }
            horizontal += scanForFinders(row).map { Finder(it.centre, y.toDouble(), it.moduleSize) }
        }
        val vertical = mutableListOf<Finder>()
        for (x in 0 until width) {
            val column = BooleanArray(height) { image[it * width + x] }
            vertical += scanForFinders(column).map { Finder(x.toDouble(), it.centre, it.moduleSize) }
        }

        // A real finder pattern shows up in both scans; keep the pairs.
        val matched = mutableListOf<Finder>()
        for (h in horizontal) {
            val best = vertical
                .filter { Math.abs(it.x - h.x) <= h.moduleSize && Math.abs(it.y - h.y) <= h.moduleSize }
                .minByOrNull { Math.abs(it.x - h.x) + Math.abs(it.y - h.y) }
                ?: continue
            if (matched.none { Math.abs(it.x - h.x) < h.moduleSize && Math.abs(it.y - h.y) < h.moduleSize }) {
                matched += Finder((h.x + best.x) / 2, (h.y + best.y) / 2, (h.moduleSize + best.moduleSize) / 2)
            }
        }
        return matched
    }

    /**
     * A finder pattern sighting: the centre position along the scanned line and
     * the module size derived from the run lengths.
     */
    private data class Sighting(val centre: Double, val moduleSize: Double)

    /**
     * Scans a single row or column for the 1:1:3:1:1 run-length signature.
     */
    private fun scanForFinders(line: BooleanArray): List<Sighting> {
        val runs = mutableListOf<Int>() // start index of each run
        var index = 0
        while (index < line.size) {
            val value = line[index]
            var end = index
            while (end < line.size && line[end] == value) end++
            runs += index
            index = end
        }
        if (runs.size < 5) return emptyList()

        val found = mutableListOf<Sighting>()
        var i = 0
        while (i + 4 < runs.size) {
            if (line[runs[i]]) { // the pattern starts on a dark run
                val counts = IntArray(5)
                for (k in 0..4) {
                    counts[k] = runLength(line, runs[i + k])
                }
                if (isFinderRatio(counts)) {
                    val moduleSize = counts.sum() / 7.0
                    val centre = runs[i + 2] + counts[2] / 2.0
                    found += Sighting(centre, moduleSize)
                    i += 5
                    continue
                }
            }
            i++
        }
        return found
    }

    private fun runLength(line: BooleanArray, start: Int): Int {
        val value = line[start]
        var end = start
        while (end < line.size && line[end] == value) end++
        return end - start
    }

    /** The 1:1:3:1:1 ratio test used to recognise a finder pattern. */
    private fun isFinderRatio(counts: IntArray): Boolean {
        val total = counts.sum()
        if (total < 7) return false
        val module = total / 7.0
        val tolerance = module / 2.0
        return Math.abs(module - counts[0]) < tolerance &&
            Math.abs(module - counts[1]) < tolerance &&
            Math.abs(3 * module - counts[2]) < 3 * tolerance &&
            Math.abs(module - counts[3]) < tolerance &&
            Math.abs(module - counts[4]) < tolerance
    }

    /**
     * Picks the finder patterns that form the corners of the symbol.
     *
     * The three patterns meet at right angles, so the corner is the one whose
     * two neighbours are at a right angle to each other, and the two legs have
     * to be of comparable length because a QR symbol is square.
     */
    private fun candidateCorners(finders: List<Finder>): List<Triple<Finder, Finder, Finder>> {
        val out = mutableListOf<Triple<Finder, Finder, Finder>>()
        for (a in finders) {
            for (b in finders) {
                if (a === b) continue
                for (c in finders) {
                    if (a === c || b === c) continue
                    val ab = distance(a, b)
                    val ac = distance(a, c)
                    if (ab < 10 || ac < 10) continue
                    val bc = distance(b, c)
                    // The legs must meet at a right angle:
                    // |a-b|^2 + |a-c|^2 = |b-c|^2.
                    val cosine = (ab * ab + ac * ac - bc * bc) / (2 * ab * ac)
                    if (Math.abs(cosine) > 0.35) continue
                    // A QR symbol is square, so the legs must be of similar length.
                    val longer = maxOf(ab, ac)
                    if (kotlin.math.abs(ab - ac) / longer > 0.3) continue
                    out += Triple(a, b, c)
                }
            }
        }
        // The biggest, most legible symbol wins.
        return out.sortedByDescending { minOf(distance(it.second, it.third), distance(it.first, it.second)) }
    }
}
