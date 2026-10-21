package com.edusync.apaar.core.qr

import com.edusync.apaar.core.security.SealGenerator
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * End-to-end behaviour of the APAAR credential badge: the verification link,
 * its parsing and its survival through a QR symbol.
 */
class ApaarQrPayloadTest {

    private val apaarId = "984210357890"
    private val institutionId = "INST-0421"
    private val programId = "BTECH_CSE"
    private val academicYear = "2024-25"
    private val enrollmentDate = "2024-08-01"
    private val timestamp = 1_726_000_000_000L

    private val seal = SealGenerator.seal(
        apaarId = apaarId,
        institutionId = institutionId,
        programId = programId,
        academicYear = academicYear,
        enrollmentDate = enrollmentDate
    )

    private fun payload() = ApaarQrPayload.build(
        apaarId = apaarId,
        institutionId = institutionId,
        programId = programId,
        seal = seal,
        timestamp = timestamp
    )

    @Test
    fun buildProducesTheCanonicalVerificationLink() {
        assertEquals(
            "https://apaar.aicte-india.gov.in/verify?apaar=984210357890&inst=INST-0421" +
                "&prog=BTECH_CSE&seal=$seal&t=$timestamp",
            payload()
        )
    }

    @Test
    fun parseRoundTripsEveryField() {
        val parsed = ApaarQrPayload.parse(payload())
        assertNotNull(parsed)
        assertEquals(apaarId, parsed?.apaarId)
        assertEquals(institutionId, parsed?.institutionId)
        assertEquals(programId, parsed?.programId)
        assertEquals(seal, parsed?.seal)
        assertEquals(timestamp, parsed?.timestamp)
    }

    @Test
    fun parseAcceptsABareIdentifier() {
        val parsed = ApaarQrPayload.parse("984210357890")
        assertNotNull(parsed)
        assertEquals(apaarId, parsed?.apaarId)
        assertNull(parsed?.institutionId)
        assertNull(parsed?.seal)
    }

    @Test
    fun parseRejectsEmptyAndUnrelatedInput() {
        assertNull(ApaarQrPayload.parse(null))
        assertNull(ApaarQrPayload.parse(""))
        assertNull(ApaarQrPayload.parse("   "))
        assertNull(ApaarQrPayload.parse("not a verification link"))
    }

    @Test
    fun theCredentialLinkSurvivesAQrRoundTrip() {
        val matrix = QrEncoder.encode(payload())
        val decoded = ReferenceQrDecoder.decode(matrix)
        assertEquals(payload(), decoded)
    }

    @Test
    fun theSealSurvivesAQrRoundTripAndStillVerifies() {
        val matrix = QrEncoder.encode(payload())
        val decoded = ReferenceQrDecoder.decode(matrix)
        val parsed = ApaarQrPayload.parse(decoded)
        assertNotNull(parsed)
        assertEquals(apaarId, parsed?.apaarId)
        assertTrue(
            SealGenerator.verify(
                presented = parsed?.seal.orEmpty(),
                apaarId = parsed?.apaarId.orEmpty(),
                institutionId = parsed?.institutionId.orEmpty(),
                programId = parsed?.programId.orEmpty(),
                academicYear = academicYear,
                enrollmentDate = enrollmentDate
            )
        )
    }

    @Test
    fun aTamperedSealIsRejectedByTheVerifier() {
        val tampered = "0" + seal.drop(1)
        assertFalse(
            SealGenerator.verify(tampered, apaarId, institutionId, programId, academicYear, enrollmentDate)
        )
    }
}
