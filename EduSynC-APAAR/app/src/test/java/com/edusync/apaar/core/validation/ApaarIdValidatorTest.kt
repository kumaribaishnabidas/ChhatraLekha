package com.edusync.apaar.core.validation

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Behavioural contract of the APAAR identifier validator.
 */
class ApaarIdValidatorTest {

    @Test
    fun acceptsAWellFormedTwelveDigitIdentifier() {
        val validation = ApaarIdValidator.validate("984210357890")
        assertTrue(validation.errors.toString(), validation.isStructurallyValid)
        assertTrue(validation.isAcceptable)
        assertEquals("984210357890", validation.normalised)
    }

    @Test
    fun stripsFormattingCharactersBeforeValidating() {
        val validation = ApaarIdValidator.validate("9842-1035-7890")
        assertTrue(validation.isStructurallyValid)
        assertEquals("984210357890", validation.normalised)
    }

    @Test
    fun rejectsIdentifiersThatAreNotTwelveDigitsLong() {
        val validation = ApaarIdValidator.validate("98421035789")
        assertFalse(validation.isStructurallyValid)
        assertTrue(validation.errors.any { it.contains("12 digits") })
    }

    @Test
    fun rejectsNonNumericIdentifiers() {
        val validation = ApaarIdValidator.validate("9842X0357890")
        assertFalse(validation.isStructurallyValid)
        assertTrue(validation.errors.any { it.contains("digits only") })
    }

    @Test
    fun rejectsTrivialPlaceholderSequences() {
        listOf("000000000000", "111111111111", "123456789012", "987654321098", "121212121212")
            .forEach { candidate ->
                val validation = ApaarIdValidator.validate(candidate)
                assertFalse("expected '$candidate' to be rejected", validation.isStructurallyValid)
            }
    }

    @Test
    fun rejectsAscendingAndDescendingRuns() {
        assertFalse(ApaarIdValidator.validate("123456789012").isStructurallyValid)
        assertFalse(ApaarIdValidator.validate("987654321098").isStructurallyValid)
    }

    @Test
    fun rejectsIdentifiersPaddedWithLeadingZeros() {
        assertFalse(ApaarIdValidator.validate("000098421035").isStructurallyValid)
    }

    @Test
    fun treatsTheLuhnChecksumAsANonBlockingAdvisory() {
        // A structurally valid identifier whose Luhn check digit does not match
        // must still be accepted, with the failure surfaced as an advisory.
        var candidate = "984210357890"
        var attempts = 0
        while (ApaarIdValidator.luhnValid(candidate) && attempts < 12) {
            candidate = candidate.dropLast(1) + ((candidate.last().digitToInt() + 1) % 10).toString()
            attempts++
        }
        val validation = ApaarIdValidator.validate(candidate)
        assertTrue(validation.errors.toString(), validation.isStructurallyValid)
        assertFalse(validation.isChecksumValid)
        assertTrue(validation.advisories.any { it.contains("Luhn") })
    }

    @Test
    fun reportsNoAdvisoryForACorrectChecksum() {
        val candidate = ApaarIdValidator.generate(42)
        val validation = ApaarIdValidator.validate(candidate)
        assertTrue(validation.isStructurallyValid)
        assertTrue(validation.isChecksumValid)
        assertTrue(validation.advisories.isEmpty())
    }

    @Test
    fun generatesIdentifiersThatPassEveryCheck() {
        for (seed in 1L..60L) {
            val generated = ApaarIdValidator.generate(seed)
            assertEquals(12, generated.length)
            val validation = ApaarIdValidator.validate(generated)
            assertTrue("seed $seed -> $generated", validation.isStructurallyValid)
            assertTrue("seed $seed -> $generated", validation.isChecksumValid)
        }
    }

    @Test
    fun generationIsDeterministic() {
        assertEquals(ApaarIdValidator.generate(7), ApaarIdValidator.generate(7))
    }

    @Test
    fun computesTheCorrectLuhnCheckDigit() {
        // "7992739871" is the canonical Luhn example; the check digit is 3.
        assertEquals(3, ApaarIdValidator.luhnCheckDigit("7992739871"))
        assertTrue(ApaarIdValidator.luhnValid("79927398713"))
    }

    @Test
    fun formatsIdentifiersForDisplay() {
        assertEquals("9842 1035 7890", ApaarIdValidator.format("984210357890"))
        assertEquals("9842-1035-7890", ApaarIdValidator.formatWithSeparator("984210357890"))
        assertEquals("", ApaarIdValidator.format(null))
    }

    @Test
    fun masksIdentifiersForAuditTrails() {
        assertEquals("9842 •••• ••••", ApaarIdValidator.mask("984210357890"))
    }

    @Test
    fun reportsABlankIdentifierAsMandatory() {
        val validation = ApaarIdValidator.validate("   ")
        assertFalse(validation.isStructurallyValid)
        assertTrue(validation.errors.any { it.contains("mandatory") })
    }
}
