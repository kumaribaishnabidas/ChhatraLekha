package com.acadentrix.core.security

import java.security.SecureRandom
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

/**
 * Local credential hardening for the portal's sign-in.
 *
 * The PIN is never stored. Only a PBKDF2-HMAC-SHA256 digest of it, together
 * with a per-account random salt, is persisted. PBKDF2 is implemented on top
 * of [Mac] rather than `SecretKeyFactory` because the JCE `PBKDF2WithHmacSHA256`
 * algorithm is only guaranteed from API 26 while the app supports API 24.
 */
object Credentials {

    /** Number of PBKDF2 iterations. High enough to be slow, low enough for a phone. */
    const val ITERATIONS: Int = 120_000

    /** Length of the derived key in bytes. */
    const val KEY_LENGTH: Int = 32

    /** Length of the random salt in bytes. */
    const val SALT_LENGTH: Int = 16

    private const val ALGORITHM = "HmacSHA256"

    /**
     * Generates a fresh random salt, hex encoded.
     */
    fun newSalt(random: SecureRandom = SecureRandom()): String {
        val bytes = ByteArray(SALT_LENGTH)
        random.nextBytes(bytes)
        return hex(bytes)
    }

    /**
     * Derives the stored hash of [pin] for the given [salt].
     */
    fun hash(pin: String, salt: String): String {
        val derived = pbkdf2(pin.toCharArray(), salt.toByteArray(Charsets.UTF_8), ITERATIONS, KEY_LENGTH)
        return hex(derived)
    }

    /**
     * Verifies a presented PIN against a stored hash.
     *
     * The comparison is constant time so that the verification cannot be used
     * as an oracle to guess the PIN byte by byte.
     */
    fun verify(pin: String, salt: String, expectedHash: String): Boolean {
        if (expectedHash.isBlank()) return false
        if (pin.isBlank()) return false
        if (salt.isBlank()) return false
        val actual = hash(pin, salt)
        return constantTimeEquals(actual, expectedHash.trim().lowercase())
    }

    /**
     * A very small PIN policy check. Returns the list of policy violations.
     */
    fun policyViolations(pin: String): List<String> {
        val violations = mutableListOf<String>()
        if (pin.length < 6) violations += "The PIN must be at least 6 characters long."
        if (pin.none { it.isDigit() }) violations += "The PIN must contain at least one digit."
        if (pin.none { it.isLetter() }) violations += "The PIN must contain at least one letter."
        if (pin.all { it.isDigit() }) violations += "The PIN must not be digits only."
        return violations
    }

    private fun pbkdf2(password: CharArray, salt: ByteArray, iterations: Int, keyLength: Int): ByteArray {
        val mac = Mac.getInstance(ALGORITHM)
        val keyMaterial = if (password.isEmpty()) ByteArray(0) else password.concatToString().toByteArray(Charsets.UTF_8)
        val key = SecretKeySpec(keyMaterial, ALGORITHM)
        val blockCount = (keyLength + mac.macLength - 1) / mac.macLength
        val output = ByteArray(blockCount * mac.macLength)
        val block = ByteArray(salt.size + 4)
        salt.copyInto(block)

        for (blockIndex in 1..blockCount) {
            block[salt.size] = (blockIndex ushr 24).toByte()
            block[salt.size + 1] = (blockIndex ushr 16).toByte()
            block[salt.size + 2] = (blockIndex ushr 8).toByte()
            block[salt.size + 3] = blockIndex.toByte()

            mac.init(key)
            var u = mac.doFinal(block)

            val accumulator = u.copyOf()
            for (iteration in 2..iterations) {
                u = mac.doFinal(u)
                for (i in accumulator.indices) {
                    accumulator[i] = (accumulator[i].toInt() xor u[i].toInt()).toByte()
                }
            }
            accumulator.copyInto(output, blockIndex - 1)
        }
        return output.copyOf(keyLength)
    }

    private fun constantTimeEquals(a: String, b: String): Boolean {
        if (a.length != b.length) return false
        var difference = 0
        for (i in a.indices) {
            difference = difference or (a[i].code xor b[i].code)
        }
        return difference == 0
    }

    private fun hex(bytes: ByteArray): String = buildString {
        for (byte in bytes) append("%02x".format(byte))
    }
}
