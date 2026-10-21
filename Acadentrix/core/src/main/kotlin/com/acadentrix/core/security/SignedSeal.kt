package com.acadentrix.core.security

import java.security.KeyFactory
import java.security.MessageDigest
import java.security.PrivateKey
import java.security.PublicKey
import java.security.Signature
import java.security.spec.X509EncodedKeySpec
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

/**
 * The facts a credential seal is computed over.
 *
 * Every field that identifies the student takes part in the digest, so a
 * record cannot be renamed, re-quotaed or re-dated without invalidating its
 * seal. [issuedAt] and [version] are part of the signed material as well, which
 * is what makes a reissued credential distinguishable from the original.
 */
data class CredentialPayload(
    val apaarId: String,
    val institutionId: String,
    val programId: String,
    val academicYear: String,
    val enrollmentDate: String,
    val studentName: String = "",
    val dateOfBirth: String = "",
    val gender: String = "",
    val admissionQuota: String = "",
    val nationality: String = "",
    val rollNo: String = "",
    val issuedAt: Long = 0L,
    val version: Int = CURRENT_VERSION
) {
    /** Canonical, unambiguous serialisation of the signed material. */
    fun canonical(): String = listOf(
        "APAAR",
        version.toString(),
        apaarId.trim(),
        institutionId.trim(),
        programId.trim(),
        academicYear.trim(),
        enrollmentDate.trim(),
        studentName.trim().uppercase(),
        dateOfBirth.trim(),
        gender.trim().uppercase(),
        admissionQuota.trim().uppercase(),
        nationality.trim(),
        rollNo.trim(),
        issuedAt.toString()
    ).joinToString("|")

    /**
     * The canonical form of the *first* seal generation.
     *
     * It covers only five fields and carries no version marker, which is
     * exactly why a legacy seal can never be authenticated. It is kept so that
     * records issued before the signed-seal scheme can still be checked for
     * accidental alteration.
     */
    fun legacyCanonical(): String = listOf(
        "APAAR",
        apaarId.trim(),
        institutionId.trim(),
        programId.trim(),
        academicYear.trim(),
        enrollmentDate.trim()
    ).joinToString("|")

    companion object {
        const val CURRENT_VERSION = 2
    }
}

/** The algorithm family a seal was produced with. */
enum class SealAlgorithm(val id: String, val label: String) {
    /** Plain truncated SHA-256. Unkeyed: readable by anyone, forgeable by anyone. */
    LEGACY("SHA256", "SHA-256 (legacy, unkeyed)"),

    /** HMAC-SHA256 with a server-held shared secret. */
    HMAC("HMAC-SHA256", "HMAC-SHA256 (shared secret)"),

    /** ECDSA over NIST P-256 with SHA-256. Verifiable offline with the public key. */
    ECDSA("ECDSA-SHA256", "ECDSA P-256 / SHA-256 (public-key)");

    companion object {
        fun from(id: String?): SealAlgorithm? = entries.firstOrNull { it.id == id }
    }
}

/** The outcome of checking a presented seal. */
enum class SealVerdict {
    /** The presented seal matches the recomputed seal under a known key. */
    VALID,

    /** The seal was well formed but does not match the recomputed value. */
    TAMPERED,

    /** The seal was produced under a key this verifier does not hold. */
    UNKNOWN_KEY,

    /** The seal could not be parsed at all. */
    MALFORMED,

    /** A legacy unkeyed seal that could be recomputed but not authenticated. */
    LEGACY_UNVERIFIED
}

/**
 * The result of a seal check, with enough context to explain itself on a
 * verifier screen.
 */
data class SealVerification(
    val verdict: SealVerdict,
    val presented: String,
    val expected: String? = null,
    val keyId: String? = null,
    val algorithm: SealAlgorithm? = null,
    val detail: String = ""
) {
    val isValid: Boolean get() = verdict == SealVerdict.VALID

    val isTampered: Boolean get() = verdict == SealVerdict.TAMPERED
}

/** A seal split into its algorithm, key identifier and signature material. */
data class ParsedSeal(
    val algorithm: SealAlgorithm,
    val keyId: String,
    val signature: String
)
/**
 * The keys a verifier trusts.
 *
 * A verifier never holds a signing key — only public keys for asymmetric
 * seals and, where the deployment is closed-loop, shared secrets for HMAC
 * seals. This is what lets an institution, an employer or a regulator check a
 * credential offline without being able to mint one.
 */
class SealKeyRing(
    publicKeys: Map<String, PublicKey> = emptyMap(),
    sharedSecrets: Map<String, ByteArray> = emptyMap()
) {
    private val publicKeyMap: Map<String, PublicKey> = publicKeys.toMap()
    private val secretMap: Map<String, ByteArray> = sharedSecrets.mapValues { it.value.copyOf() }

    val keyIds: Set<String> get() = publicKeyMap.keys + secretMap.keys

    fun hasKey(keyId: String): Boolean = publicKeyMap.containsKey(keyId) || secretMap.containsKey(keyId)

    fun publicKey(keyId: String): PublicKey? = publicKeyMap[keyId]

    fun sharedSecret(keyId: String): ByteArray? = secretMap[keyId]?.copyOf()

    fun withPublicKey(keyId: String, key: PublicKey): SealKeyRing =
        SealKeyRing(publicKeyMap + (keyId to key), secretMap)

    fun withSharedSecret(keyId: String, secret: ByteArray): SealKeyRing =
        SealKeyRing(publicKeyMap, secretMap + (keyId to secret.copyOf()))

    companion object {
        val EMPTY = SealKeyRing()
    }
}

/**
 * Signs and verifies academic credentials.
 *
 * Three seal generations coexist so that a verifier can read anything ever
 * issued while only ever trusting the current one:
 *
 * * [SealAlgorithm.LEGACY] — the original truncated SHA-256 digest. It is
 *   tamper-*evident* (any change to the record changes the digest) but it is
 *   not a MAC: anybody who knows the canonical format can forge one. It can
 *   therefore never be reported as [SealVerdict.VALID].
 * * [SealAlgorithm.HMAC] — HMAC-SHA256 under a secret only the issuer holds.
 *   Authenticated, but verification requires the secret, so it is a
 *   server-side check.
 * * [SealAlgorithm.ECDSA] — ECDSA over P-256. The issuer holds the private
 *   key and the world holds only the public key, so credentials can be
 *   verified offline by anyone the issuer publishes the key to.
 *
 * Wire format: `<ALGORITHM>.<KEY_ID>.<SIGNATURE>`, e.g.
 * `ECDSA-SHA256.aicte-2026.<base64url>`.
 */
object SignedSeal {

    const val LEGACY_PREFIX = "SHA256"

    /** The key identifier reported for a first-generation, unkeyed seal. */
    const val LEGACY_KEY_ID = "legacy"

    /** A first-generation seal is a bare 32-character hex digest. */
    private val LEGACY_PATTERN = Regex("^[0-9A-Fa-f]{32}$")

    /** Canonical signed material for [payload]. */
    fun canonical(payload: CredentialPayload): String = payload.canonical()

    /** Produces a legacy (unkeyed) seal. Kept for backwards compatibility only. */
    fun legacySeal(payload: CredentialPayload): String =
        hex(MessageDigest.getInstance("SHA-256").digest(payload.legacyCanonical().toByteArray(Charsets.UTF_8)))
            .take(32)
            .uppercase()

    /** Signs [payload] with an HMAC-SHA256 shared secret. */
    fun signHmac(payload: CredentialPayload, keyId: String, secret: ByteArray): String {
        require(secret.isNotEmpty()) { "HMAC secret must not be empty" }
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(secret, "HmacSHA256"))
        val raw = mac.doFinal(payload.canonical().toByteArray(Charsets.UTF_8))
        return "${SealAlgorithm.HMAC.id}.$keyId.${Base64Url.encode(raw)}"
    }

    /**
     * Signs [payload] with an ECDSA P-256 private key.
     *
     * The signature is emitted in the DER-free IEEE P1363 form so that the
     * encoding is fixed-width and stable across providers.
     */
    fun signEcdsa(payload: CredentialPayload, keyId: String, privateKey: PrivateKey): String {
        val signer = Signature.getInstance("SHA256withECDSA")
        signer.initSign(privateKey)
        signer.update(payload.canonical().toByteArray(Charsets.UTF_8))
        val der = signer.sign()
        val raw = derToP1363(der)
        return "${SealAlgorithm.ECDSA.id}.$keyId.${Base64Url.encode(raw)}"
    }

    /** Splits a seal into algorithm, key id and signature material. */
    fun parse(presented: String): ParsedSeal? {
        val trimmed = presented.trim()
        val parts = trimmed.split('.')
        if (parts.size == 3) {
            val algorithm = SealAlgorithm.from(parts[0]) ?: return null
            if (parts[1].isBlank() || parts[2].isBlank()) return null
            return ParsedSeal(algorithm, parts[1], parts[2])
        }
        // The first generation of seals was a bare 32-character hex digest with
        // no algorithm prefix. It has to stay readable so that credentials
        // issued before the signed-seal scheme can still be checked.
        if (parts.size == 1 && LEGACY_PATTERN.matches(trimmed)) {
            return ParsedSeal(SealAlgorithm.LEGACY, LEGACY_KEY_ID, trimmed)
        }
        return null
    }

    /**
     * Verifies a presented seal against [payload] using whatever keys [keyRing]
     * holds.
     *
     * A legacy seal is recomputed so the caller can report *whether it matches*,
     * but it is never reported as [SealVerdict.VALID] because it carries no
     * proof of who issued it.
     */
    fun verify(presented: String, payload: CredentialPayload, keyRing: SealKeyRing): SealVerification {
        val trimmed = presented.trim()
        if (trimmed.isBlank()) {
            return SealVerification(SealVerdict.MALFORMED, presented, detail = "No seal was presented.")
        }

        val parsed = parse(trimmed)
            ?: return SealVerification(SealVerdict.MALFORMED, presented, detail = "The seal is not in a recognised format.")

        return when (parsed.algorithm) {
            SealAlgorithm.LEGACY -> {
                val expected = legacySeal(payload)
                val matches = trimmed.substringAfterLast('.').trim().equals(expected, ignoreCase = true)
                SealVerification(
                    verdict = if (matches) SealVerdict.LEGACY_UNVERIFIED else SealVerdict.TAMPERED,
                    presented = trimmed,
                    expected = expected,
                    keyId = parsed.keyId,
                    algorithm = parsed.algorithm,
                    detail = if (matches) {
                        "Digest matches the record, but this seal is unkeyed and cannot prove who issued it."
                    } else {
                        "The digest does not match the record. The credential has been altered."
                    }
                )
            }

            SealAlgorithm.HMAC -> {
                val secret = keyRing.sharedSecret(parsed.keyId)
                    ?: return SealVerification(
                        SealVerdict.UNKNOWN_KEY, trimmed, keyId = parsed.keyId,
                        algorithm = parsed.algorithm,
                        detail = "This seal was issued under key '${parsed.keyId}', which this verifier does not hold."
                    )
                val raw = runCatching { Base64Url.decode(parsed.signature) }.getOrNull()
                    ?: return SealVerification(
                        SealVerdict.MALFORMED, trimmed, keyId = parsed.keyId,
                        algorithm = parsed.algorithm, detail = "The signature could not be decoded."
                    )
                val expectedRaw = hmac(secret, payload.canonical())
                val ok = constantTimeEquals(raw, expectedRaw)
                SealVerification(
                    verdict = if (ok) SealVerdict.VALID else SealVerdict.TAMPERED,
                    presented = trimmed,
                    expected = "${SealAlgorithm.HMAC.id}.${parsed.keyId}.${Base64Url.encode(expectedRaw)}",
                    keyId = parsed.keyId,
                    algorithm = parsed.algorithm,
                    detail = if (ok) "Authentic seal issued under key '${parsed.keyId}'."
                    else "The signature does not match the record. The credential has been altered."
                )
            }

            SealAlgorithm.ECDSA -> {
                val publicKey = keyRing.publicKey(parsed.keyId)
                    ?: return SealVerification(
                        SealVerdict.UNKNOWN_KEY, trimmed, keyId = parsed.keyId,
                        algorithm = parsed.algorithm,
                        detail = "This seal was issued under key '${parsed.keyId}', which this verifier does not trust."
                    )
                val raw = runCatching { Base64Url.decode(parsed.signature) }.getOrNull()
                    ?: return SealVerification(
                        SealVerdict.MALFORMED, trimmed, keyId = parsed.keyId,
                        algorithm = parsed.algorithm, detail = "The signature could not be decoded."
                    )
                val ok = verifyEcdsa(publicKey, payload.canonical(), raw)
                SealVerification(
                    verdict = if (ok) SealVerdict.VALID else SealVerdict.TAMPERED,
                    presented = trimmed,
                    keyId = parsed.keyId,
                    algorithm = parsed.algorithm,
                    detail = if (ok) "Authentic signature issued under key '${parsed.keyId}'."
                    else "The signature does not match the record. The credential has been altered."
                )
            }
        }
    }

    /** Convenience for the shared-secret flavour of [verify]. */
    fun verifyHmac(
        presented: String,
        payload: CredentialPayload,
        keyId: String,
        secret: ByteArray
    ): SealVerification = verify(presented, payload, SealKeyRing(sharedSecrets = mapOf(keyId to secret)))

    /** Convenience for the public-key flavour of [verify]. */
    fun verifyEcdsa(
        presented: String,
        payload: CredentialPayload,
        keyId: String,
        publicKey: PublicKey
    ): SealVerification = verify(presented, payload, SealKeyRing(publicKeys = mapOf(keyId to publicKey)))

    /** Loads a PEM-encoded X.509 public key. */
    fun publicKeyFromPem(pem: String): PublicKey? = runCatching {
        val body = pem
            .replace("-----BEGIN PUBLIC KEY-----", "")
            .replace("-----END PUBLIC KEY-----", "")
            .replace("\\s".toRegex(), "")
        val bytes = Base64Url.decode(body)
        KeyFactory.getInstance("EC").generatePublic(X509EncodedKeySpec(bytes))
    }.getOrNull()

    // ------------------------------------------------------------------ internals

    private fun hmac(secret: ByteArray, canonical: String): ByteArray {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(secret, "HmacSHA256"))
        return mac.doFinal(canonical.toByteArray(Charsets.UTF_8))
    }

    private fun verifyEcdsa(publicKey: PublicKey, canonical: String, rawSignature: ByteArray): Boolean {
        val verifier = Signature.getInstance("SHA256withECDSA")
        verifier.initVerify(publicKey)
        verifier.update(canonical.toByteArray(Charsets.UTF_8))
        return runCatching { verifier.verify(p1363ToDer(rawSignature)) }.getOrDefault(false)
    }

    private fun constantTimeEquals(a: ByteArray, b: ByteArray): Boolean {
        if (a.size != b.size) return false
        var diff = 0
        for (i in a.indices) diff = diff or (a[i].toInt() xor b[i].toInt())
        return diff == 0
    }

    private fun hex(bytes: ByteArray): String = buildString {
        for (byte in bytes) append("%02x".format(byte))
    }

    /**
     * Converts a DER-encoded ECDSA signature into the fixed-width IEEE P1363
     * form (`r || s`, 32 bytes each for P-256).
     */
    private fun derToP1363(der: ByteArray): ByteArray {
        var offset = 0
        if (der[offset++] != 0x30.toByte()) return der
        offset += 1 // length byte, single-byte lengths only for P-256
        if (der[offset++] != 0x02.toByte()) return der
        val rLength = der[offset++].toInt()
        val r = der.copyOfRange(offset, offset + rLength)
        offset += rLength
        if (der[offset++] != 0x02.toByte()) return der
        val sLength = der[offset++].toInt()
        val s = der.copyOfRange(offset, offset + sLength)
        val out = ByteArray(64)
        copyRightAligned(r, out, 0, 32)
        copyRightAligned(s, out, 32, 32)
        return out
    }

    /** Converts an IEEE P1363 signature back into the DER form the JCA expects. */
    private fun p1363ToDer(raw: ByteArray): ByteArray {
        if (raw.size != 64) return raw
        val r = derInteger(raw.copyOfRange(0, 32))
        val s = derInteger(raw.copyOfRange(32, 64))
        val bodyLength = 2 + r.size + 2 + s.size
        return ByteArray(2 + bodyLength).also { out ->
            var i = 0
            out[i++] = 0x30.toByte()
            out[i++] = bodyLength.toByte()
            out[i++] = 0x02.toByte()
            out[i++] = r.size.toByte()
            System.arraycopy(r, 0, out, i, r.size)
            i += r.size
            out[i++] = 0x02.toByte()
            out[i++] = s.size.toByte()
            System.arraycopy(s, 0, out, i, s.size)
        }
    }

    /**
     * Encodes a big-endian integer as a DER INTEGER.
     *
     * DER integers are signed, so a value whose top bit is set has to be
     * prefixed with a zero byte — otherwise a conforming parser would read it
     * as a negative number and reject the signature.
     */
    private fun derInteger(value: ByteArray): ByteArray {
        val trimmed = stripLeadingZeros(value)
        val needsSignByte = (trimmed[0].toInt() and 0x80) != 0
        if (!needsSignByte) return trimmed
        return ByteArray(trimmed.size + 1).also { out ->
            out[0] = 0
            System.arraycopy(trimmed, 0, out, 1, trimmed.size)
        }
    }

    private fun stripLeadingZeros(value: ByteArray): ByteArray {
        var start = 0
        while (start < value.size - 1 && value[start] == 0.toByte()) start++
        return value.copyOfRange(start, value.size)
    }

    /**
     * Copies [source] into `target[targetOffset until targetOffset + regionSize]`,
     * right-aligned so that a shorter value keeps its low-order bytes.
     */
    private fun copyRightAligned(source: ByteArray, target: ByteArray, targetOffset: Int, regionSize: Int) {
        val trimmed = stripLeadingZeros(source)
        val pad = regionSize - trimmed.size
        System.arraycopy(trimmed, 0, target, targetOffset + pad, trimmed.size)
    }
}

/**
 * Minimal, dependency-free base64url codec.
 *
 * `java.util.Base64` is API 26+ on Android and this module targets API 24, so
 * the encoding is implemented here. The decoder accepts both the URL-safe and
 * the standard alphabets so PEM material can be read with it too.
 */
object Base64Url {

    private const val ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

    fun encode(bytes: ByteArray): String {
        if (bytes.isEmpty()) return ""
        val out = StringBuilder((bytes.size + 2) / 3 * 4)
        var i = 0
        while (i + 2 < bytes.size) {
            val n = ((bytes[i].toInt() and 0xFF) shl 16) or
                ((bytes[i + 1].toInt() and 0xFF) shl 8) or
                (bytes[i + 2].toInt() and 0xFF)
            out.append(ALPHABET[(n shr 18) and 0x3F])
            out.append(ALPHABET[(n shr 12) and 0x3F])
            out.append(ALPHABET[(n shr 6) and 0x3F])
            out.append(ALPHABET[n and 0x3F])
            i += 3
        }
        when (bytes.size - i) {
            1 -> {
                val n = (bytes[i].toInt() and 0xFF) shl 16
                out.append(ALPHABET[(n shr 18) and 0x3F])
                out.append(ALPHABET[(n shr 12) and 0x3F])
            }
            2 -> {
                val n = ((bytes[i].toInt() and 0xFF) shl 16) or ((bytes[i + 1].toInt() and 0xFF) shl 8)
                out.append(ALPHABET[(n shr 18) and 0x3F])
                out.append(ALPHABET[(n shr 12) and 0x3F])
                out.append(ALPHABET[(n shr 6) and 0x3F])
            }
        }
        return out.toString()
    }

    fun decode(value: String): ByteArray {
        val cleaned = value.filterNot { it.isWhitespace() }.replace('+', '-').replace('/', '_')
        if (cleaned.isEmpty()) return ByteArray(0)
        val out = java.io.ByteArrayOutputStream(cleaned.length * 3 / 4 + 3)
        var buffer = 0
        var bits = 0
        for (ch in cleaned) {
            if (ch == '=') break
            val index = ALPHABET.indexOf(ch)
            if (index < 0) throw IllegalArgumentException("Not a base64 character: '$ch'")
            buffer = (buffer shl 6) or index
            bits += 6
            if (bits >= 8) {
                bits -= 8
                out.write((buffer shr bits) and 0xFF)
            }
        }
        return out.toByteArray()
    }
}
