package com.edusync.apaar.core.security

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Behaviour of the tamper-evident credential seal.
 */
class SealGeneratorTest {

    private val apaarId = "984210357890"
    private val institutionId = "INST-0421"
    private val programId = "BTECH_CSE"
    private val academicYear = "2024-25"
    private val enrollmentDate = "2024-08-01"

    private fun sealOf(
        apaar: String = apaarId,
        institution: String = institutionId,
        programme: String = programId,
        year: String = academicYear,
        enrolled: String = enrollmentDate
    ) = SealGenerator.seal(apaar, institution, programme, year, enrolled)

    @Test
    fun sealIsThirtyTwoUppercaseHexCharacters() {
        val seal = sealOf()
        assertEquals(32, seal.length)
        assertTrue(seal, seal.all { it.isDigit() || it in 'A'..'F' })
    }

    @Test
    fun sealIsDeterministic() {
        assertEquals(sealOf(), sealOf())
    }

    @Test
    fun surroundingWhitespaceDoesNotChangeTheSeal() {
        assertEquals(sealOf(), sealOf(apaar = "  $apaarId  ", institution = " $institutionId "))
    }

    @Test
    fun sha256MatchesThePublishedReferenceVector() {
        assertEquals(
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            SealGenerator.sha256("abc")
        )
    }

    @Test
    fun verifyAcceptsAMatchingSeal() {
        val seal = sealOf()
        assertTrue(SealGenerator.verify(seal, apaarId, institutionId, programId, academicYear, enrollmentDate))
    }

    @Test
    fun verifyIsCaseInsensitive() {
        val seal = sealOf()
        assertTrue(
            SealGenerator.verify(
                seal.lowercase(),
                apaarId,
                institutionId,
                programId,
                academicYear,
                enrollmentDate
            )
        )
    }

    @Test
    fun verifyRejectsATamperedSeal() {
        val seal = sealOf()
        assertFalse(
            SealGenerator.verify(
                seal.dropLast(1) + if (seal.last() == '0') "1" else "0",
                apaarId,
                institutionId,
                programId,
                academicYear,
                enrollmentDate
            )
        )
    }

    @Test
    fun everyFieldParticipatesInTheSeal() {
        val reference = sealOf()
        assertNotEquals(reference, sealOf(apaar = "984210357891"))
        assertNotEquals(reference, sealOf(institution = "INST-0422"))
        assertNotEquals(reference, sealOf(programme = "BTECH_ECE"))
        assertNotEquals(reference, sealOf(year = "2025-26"))
        assertNotEquals(reference, sealOf(enrolled = "2024-08-02"))
    }

    @Test
    fun distinctCredentialTuplesProduceDistinctSeals() {
        assertNotEquals(
            sealOf(apaar = "98421035789", institution = "0INST-0421"),
            sealOf(apaar = "984210357890", institution = "INST-0421")
        )
    }

    @Test
    fun formatIsoRendersUtc() {
        assertEquals("2024-09-10T20:26:40Z", SealGenerator.formatIso(1_726_000_000_000L))
        assertEquals("1970-01-01T00:00:00Z", SealGenerator.formatIso(0L))
    }

    @Test
    fun formatTimestampRendersIndiaStandardTime() {
        assertEquals("11 Sep 2024, 01:56:40 IST", SealGenerator.formatTimestamp(1_726_000_000_000L))
    }
}
