package com.acadentrix.core.security

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.Signature
import java.security.spec.ECGenParameterSpec

/**
 * Behaviour of the credential seal: signing, verification, key handling and
 * the verdicts a verifier may report.
 */
class SignedSealTest {

    private val payload = CredentialPayload(
        apaarId = "987654321012",
        institutionId = "1-245023901",
        programId = "BTECH_CSE",
        academicYear = "2024-25",
        enrollmentDate = "2024-08-01",
        studentName = "Asha Verma",
        dateOfBirth = "2004-02-11",
        gender = "FEMALE",
        admissionQuota = "MERIT",
        nationality = "Indian",
        rollNo = "CSE-24-117",
        issuedAt = 1_726_000_000_000L
    )

    private val secret = "a-very-long-shared-secret-value-0123456789".toByteArray()

    private fun ecKeyPair(): KeyPair {
        val generator = KeyPairGenerator.getInstance("EC")
        generator.initialize(ECGenParameterSpec("secp256r1"))
        return generator.generateKeyPair()
    }

    // -------------------------------------------------------------- canonical form

    @Test
    fun theCanonicalFormCoversEveryIdentityField() {
        val canonical = payload.canonical()
        listOf(
            "987654321012",
            "1-245023901",
            "BTECH_CSE",
            "2024-25",
            "2024-08-01",
            "ASHA VERMA",
            "2004-02-11",
            "FEMALE",
            "MERIT",
            "Indian",
            "CSE-24-117",
            "1726000000000"
        ).forEach { field ->
            assertTrue("canonical form is missing '$field'", canonical.contains(field))
        }
    }

    @Test
    fun theCanonicalFormIsStableAcrossWhitespaceDifferences() {
        val padded = payload.copy(
            studentName = "  Asha Verma  ",
            institutionId = " 1-245023901 ",
            academicYear = " 2024-25 "
        )
        assertEquals(payload.canonical(), padded.canonical())
    }

    @Test
    fun changingAnySignedFieldChangesTheCanonicalForm() {
        val base = payload.canonical()
        assertNotEquals(base, payload.copy(studentName = "Asha Verma II").canonical())
        assertNotEquals(base, payload.copy(dateOfBirth = "2004-02-12").canonical())
        assertNotEquals(base, payload.copy(admissionQuota = "NRI").canonical())
        assertNotEquals(base, payload.copy(nationality = "Nepal").canonical())
        assertNotEquals(base, payload.copy(rollNo = "CSE-24-118").canonical())
        assertNotEquals(base, payload.copy(issuedAt = 1L).canonical())
        assertNotEquals(base, payload.copy(version = 3).canonical())
    }

    // ------------------------------------------------------------------- HMAC

    @Test
    fun anHmacSealVerifiesAgainstTheRecordItWasIssuedFor() {
        val seal = SignedSeal.signHmac(payload, "aicte-2026", secret)
        val verdict = SignedSeal.verify(seal, payload, SealKeyRing(sharedSecrets = mapOf("aicte-2026" to secret)))
        assertEquals(SealVerdict.VALID, verdict.verdict)
        assertTrue(verdict.isValid)
        assertEquals("aicte-2026", verdict.keyId)
        assertEquals(SealAlgorithm.HMAC, verdict.algorithm)
    }

    @Test
    fun anHmacSealFailsWhenTheRecordIsEdited() {
        val seal = SignedSeal.signHmac(payload, "aicte-2026", secret)
        val tampered = payload.copy(studentName = "Asha Verma II")
        val verdict = SignedSeal.verify(seal, tampered, SealKeyRing(sharedSecrets = mapOf("aicte-2026" to secret)))
        assertEquals(SealVerdict.TAMPERED, verdict.verdict)
        assertTrue(verdict.isTampered)
    }

    @Test
    fun anHmacSealFailsUnderADifferentSecret() {
        val seal = SignedSeal.signHmac(payload, "aicte-2026", secret)
        val other = SealKeyRing(sharedSecrets = mapOf("aicte-2026" to "a-different-secret-value-9876543210".toByteArray()))
        val verdict = SignedSeal.verify(seal, payload, other)
        assertEquals(SealVerdict.TAMPERED, verdict.verdict)
    }

    @Test
    fun anHmacSealUnderAnUnknownKeyIsReportedAsSuch() {
        val seal = SignedSeal.signHmac(payload, "aicte-2026", secret)
        val verdict = SignedSeal.verify(seal, payload, SealKeyRing.EMPTY)
        assertEquals(SealVerdict.UNKNOWN_KEY, verdict.verdict)
        assertTrue(verdict.detail.contains("aicte-2026"))
    }

    @Test
    fun anEmptyHmacSecretIsRejected() {
        val failed = runCatching { SignedSeal.signHmac(payload, "k", ByteArray(0)) }
        assertTrue(failed.isFailure)
    }

    // ------------------------------------------------------------------ ECDSA

    @Test
    fun anEcdsaSealVerifiesWithThePublishedPublicKey() {
        val keys = ecKeyPair()
        val seal = SignedSeal.signEcdsa(payload, "aicte-p256", keys.private)
        val verdict = SignedSeal.verify(
            seal,
            payload,
            SealKeyRing(publicKeys = mapOf("aicte-p256" to keys.public))
        )
        assertEquals(SealVerdict.VALID, verdict.verdict)
        assertEquals(SealAlgorithm.ECDSA, verdict.algorithm)
    }

    @Test
    fun anEcdsaSealFailsWhenTheRecordIsEdited() {
        val keys = ecKeyPair()
        val seal = SignedSeal.signEcdsa(payload, "aicte-p256", keys.private)
        val tampered = payload.copy(rollNo = "CSE-24-999")
        val verdict = SignedSeal.verify(
            seal,
            tampered,
            SealKeyRing(publicKeys = mapOf("aicte-p256" to keys.public))
        )
        assertEquals(SealVerdict.TAMPERED, verdict.verdict)
    }

    @Test
    fun anEcdsaSealUnderAnUnknownKeyIsReportedAsSuch() {
        val keys = ecKeyPair()
        val seal = SignedSeal.signEcdsa(payload, "aicte-p256", keys.private)
        val verdict = SignedSeal.verify(seal, payload, SealKeyRing.EMPTY)
        assertEquals(SealVerdict.UNKNOWN_KEY, verdict.verdict)
    }

    @Test
    fun anEcdsaSealIsRejectedWhenTheSignatureIsTruncated() {
        val keys = ecKeyPair()
        val seal = SignedSeal.signEcdsa(payload, "aicte-p256", keys.private)
        val parsed = SignedSeal.parse(seal)!!
        val truncated = "${SealAlgorithm.ECDSA.id}.${parsed.keyId}.${parsed.signature.dropLast(4)}"
        val verdict = SignedSeal.verify(
            truncated,
            payload,
            SealKeyRing(publicKeys = mapOf("aicte-p256" to keys.public))
        )
        assertEquals(SealVerdict.TAMPERED, verdict.verdict)
    }

    @Test
    fun theEcdsaSignatureHasAFixedWidthEncoding() {
        // ECDSA is randomised, so two signatures over the same payload differ.
        // What must be stable is the *encoding*: fixed-width IEEE P1363, so a
        // verifier can parse the seal without a length prefix.
        val keys = ecKeyPair()
        val first = SignedSeal.signEcdsa(payload, "aicte-p256", keys.private)
        val second = SignedSeal.signEcdsa(payload, "aicte-p256", keys.private)
        assertNotEquals(first, second)

        val ring = SealKeyRing(publicKeys = mapOf("aicte-p256" to keys.public))
        assertEquals(SealVerdict.VALID, SignedSeal.verify(first, payload, ring).verdict)
        assertEquals(SealVerdict.VALID, SignedSeal.verify(second, payload, ring).verdict)

        listOf(first, second).forEach { seal ->
            val parsed = SignedSeal.parse(seal)!!
            assertEquals(64, Base64Url.decode(parsed.signature).size)
        }
    }

    @Test
    fun theEcdsaSignatureIsAcceptedByThePlainJcaVerifier() {
        // Guards the DER <-> P1363 conversion: the published bytes must still be
        // a valid ECDSA signature for the canonical message.
        val keys = ecKeyPair()
        val seal = SignedSeal.signEcdsa(payload, "aicte-p256", keys.private)
        val parsed = SignedSeal.parse(seal)!!
        val raw = Base64Url.decode(parsed.signature)
        val verifier = Signature.getInstance("SHA256withECDSA")
        verifier.initVerify(keys.public)
        verifier.update(payload.canonical().toByteArray(Charsets.UTF_8))
        val der = derSequence(
            derInteger(raw.copyOfRange(0, 32)),
            derInteger(raw.copyOfRange(32, 64))
        )
        assertTrue(verifier.verify(der))
    }

    private fun derInteger(value: ByteArray): ByteArray {
        var start = 0
        while (start < value.size - 1 && value[start] == 0.toByte()) start++
        val trimmed = value.copyOfRange(start, value.size)
        val needsSignByte = (trimmed[0].toInt() and 0x80) != 0
        if (!needsSignByte) return trimmed
        return ByteArray(trimmed.size + 1).also { out ->
            out[0] = 0
            System.arraycopy(trimmed, 0, out, 1, trimmed.size)
        }
    }

    private fun derSequence(vararg parts: ByteArray): ByteArray {
        val bodyLength = parts.sumOf { 2 + it.size }
        return ByteArray(2 + bodyLength).also { out ->
            var i = 0
            out[i++] = 0x30.toByte()
            out[i++] = bodyLength.toByte()
            parts.forEach { part ->
                out[i++] = 0x02.toByte()
                out[i++] = part.size.toByte()
                System.arraycopy(part, 0, out, i, part.size)
                i += part.size
            }
        }
    }

    // ----------------------------------------------------------------- legacy

    @Test
    fun aLegacySealIsNeverReportedAsValid() {
        val seal = SignedSeal.legacySeal(payload)
        val verdict = SignedSeal.verify(seal, payload, SealKeyRing.EMPTY)
        assertEquals(SealVerdict.LEGACY_UNVERIFIED, verdict.verdict)
        assertFalse(verdict.isValid)
    }

    @Test
    fun aLegacySealThatDoesNotMatchIsReportedAsTampered() {
        val seal = SignedSeal.legacySeal(payload)
        // The legacy digest only covered five fields, so one of those has to
        // change for the mismatch to be visible at all.
        val verdict = SignedSeal.verify(seal, payload.copy(enrollmentDate = "2024-09-01"), SealKeyRing.EMPTY)
        assertEquals(SealVerdict.TAMPERED, verdict.verdict)
    }

    @Test
    fun aLegacySealDoesNotCoverTheFieldsItNeverSigned() {
        // Documents the known weakness of the first generation: the student name
        // is not part of the digest, which is exactly why the legacy seal can
        // never be reported as authentic.
        val seal = SignedSeal.legacySeal(payload)
        val verdict = SignedSeal.verify(seal, payload.copy(studentName = "Someone Else"), SealKeyRing.EMPTY)
        assertEquals(SealVerdict.LEGACY_UNVERIFIED, verdict.verdict)
    }

    // ----------------------------------------------------------------- parsing

    @Test
    fun aSealIsSplitIntoAlgorithmKeyAndSignature() {
        val seal = SignedSeal.signHmac(payload, "k1", secret)
        val parsed = SignedSeal.parse(seal)!!
        assertEquals(SealAlgorithm.HMAC, parsed.algorithm)
        assertEquals("k1", parsed.keyId)
        assertTrue(parsed.signature.isNotBlank())
    }

    @Test
    fun malformedSealsAreRejected() {
        assertNull(SignedSeal.parse(""))
        assertNull(SignedSeal.parse("only-two-parts"))
        assertNull(SignedSeal.parse("SHA256.k1"))
        assertNull(SignedSeal.parse("NOT-AN-ALGORITHM.k1.signature"))
        assertNull(SignedSeal.parse("SHA256..signature"))
        assertNull(SignedSeal.parse("SHA256.k1."))
    }

    @Test
    fun anEmptySealIsReportedAsMalformed() {
        val verdict = SignedSeal.verify("", payload, SealKeyRing.EMPTY)
        assertEquals(SealVerdict.MALFORMED, verdict.verdict)
    }

    @Test
    fun aSealWithAnUnreadableSignatureIsReportedAsMalformed() {
        val verdict = SignedSeal.verify(
            "HMAC-SHA256.k1.not!valid!base64",
            payload,
            SealKeyRing(sharedSecrets = mapOf("k1" to secret))
        )
        assertEquals(SealVerdict.MALFORMED, verdict.verdict)
    }

    // -------------------------------------------------------------- key ring

    @Test
    fun theKeyRingKnowsWhichKeysItHolds() {
        val keys = ecKeyPair()
        val ring = SealKeyRing(publicKeys = mapOf("pub" to keys.public))
            .withSharedSecret("sec", secret)
        assertTrue(ring.hasKey("pub"))
        assertTrue(ring.hasKey("sec"))
        assertFalse(ring.hasKey("nope"))
        assertEquals(setOf("pub", "sec"), ring.keyIds)
        assertEquals(keys.public, ring.publicKey("pub"))
        assertEquals(secret.size, ring.sharedSecret("sec")?.size)
    }

    @Test
    fun theKeyRingDoesNotHandOutItsOwnSecretMaterial() {
        val ring = SealKeyRing(sharedSecrets = mapOf("sec" to secret))
        val copy = ring.sharedSecret("sec")!!
        copy[0] = 'X'.code.toByte()
        assertFalse(ring.sharedSecret("sec")!![0] == 'X'.code.toByte())
    }

    @Test
    fun aPublicKeyCanBeLoadedFromPem() {
        val keys = ecKeyPair()
        val pem = pemEncode(keys.public.encoded)
        val loaded = SignedSeal.publicKeyFromPem(pem)
        assertEquals(keys.public, loaded)
    }

    @Test
    fun aPublicKeyRingVerifiesASealIssuedElsewhere() {
        val keys = ecKeyPair()
        val seal = SignedSeal.signEcdsa(payload, "aicte-p256", keys.private)
        val ring = SealKeyRing(publicKeys = mapOf("aicte-p256" to SignedSeal.publicKeyFromPem(pemEncode(keys.public.encoded))!!))
        assertEquals(SealVerdict.VALID, SignedSeal.verify(seal, payload, ring).verdict)
    }

    // ---------------------------------------------------------------- base64url

    @Test
    fun base64UrlRoundTripsArbitraryBytes() {
        val cases = listOf(
            ByteArray(0),
            byteArrayOf(0),
            byteArrayOf(1),
            byteArrayOf(1, 2),
            byteArrayOf(1, 2, 3),
            ByteArray(64) { it.toByte() },
            ByteArray(255) { (it * 7).toByte() }
        )
        cases.forEach { bytes ->
            val encoded = Base64Url.encode(bytes)
            assertTrue("encoded form must not contain padding", !encoded.contains('='))
            assertTrue("encoded form must be URL safe", encoded.none { it == '+' || it == '/' })
            assertTrue(bytes.contentEquals(Base64Url.decode(encoded)))
        }
    }

    @Test
    fun base64UrlAcceptsTheStandardAlphabetToo() {
        // PEM bodies use the standard alphabet; the decoder must cope with both.
        val bytes = byteArrayOf(-5, 60, -1, 32, 7)
        val standard = java.util.Base64.getEncoder().encodeToString(bytes)
        assertTrue(bytes.contentEquals(Base64Url.decode(standard)))
    }

    @Test
    fun base64UrlRejectsCharactersOutsideTheAlphabet() {
        assertTrue(runCatching { Base64Url.decode("!!!!") }.isFailure)
    }

    // ------------------------------------------------------------------ helpers

    private fun pemEncode(bytes: ByteArray): String {
        val body = java.util.Base64.getMimeEncoder(64, "\n".toByteArray()).encodeToString(bytes)
        return "-----BEGIN PUBLIC KEY-----\n$body\n-----END PUBLIC KEY-----"
    }
}
