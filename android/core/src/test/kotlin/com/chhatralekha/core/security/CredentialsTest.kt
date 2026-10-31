package com.chhatralekha.core.security

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Behaviour of the local credential hardening.
 */
class CredentialsTest {

    @Test
    fun aGeneratedSaltIsLongAndUnique() {
        val first = Credentials.newSalt()
        val second = Credentials.newSalt()
        assertEquals(Credentials.SALT_LENGTH * 2, first.length)
        assertNotEquals(first, second)
    }

    @Test
    fun theCorrectPinVerifies() {
        val salt = Credentials.newSalt()
        val hash = Credentials.hash("ChhatraLekha2024", salt)
        assertTrue(Credentials.verify("ChhatraLekha2024", salt, hash))
    }

    @Test
    fun theWrongPinIsRejected() {
        val salt = Credentials.newSalt()
        val hash = Credentials.hash("ChhatraLekha2024", salt)
        assertFalse(Credentials.verify("ChhatraLekha2025", salt, hash))
        assertFalse(Credentials.verify("", salt, hash))
        assertFalse(Credentials.verify("chhatralekha2024", salt, hash))
    }

    @Test
    fun theSamePinUnderADifferentSaltProducesADifferentHash() {
        val first = Credentials.hash("ChhatraLekha2024", Credentials.newSalt())
        val second = Credentials.hash("ChhatraLekha2024", Credentials.newSalt())
        assertNotEquals(first, second)
    }

    @Test
    fun theHashIsDeterministicForTheSameSalt() {
        val salt = Credentials.newSalt()
        assertEquals(Credentials.hash("ChhatraLekha2024", salt), Credentials.hash("ChhatraLekha2024", salt))
    }

    @Test
    fun anEmptyStoredHashNeverVerifies() {
        assertFalse(Credentials.verify("ChhatraLekha2024", Credentials.newSalt(), ""))
        assertFalse(Credentials.verify("ChhatraLekha2024", Credentials.newSalt(), "   "))
    }

    @Test
    fun thePinIsNeverStoredInPlainText() {
        val salt = Credentials.newSalt()
        val hash = Credentials.hash("ChhatraLekha2024", salt)
        assertFalse(hash.contains("ChhatraLekha2024"))
    }

    @Test
    fun thePolicyRejectsShortPins() {
        assertTrue(Credentials.policyViolations("12").any { it.contains("6 characters") })
    }

    @Test
    fun thePolicyRequiresBothLettersAndDigits() {
        assertTrue(Credentials.policyViolations("abcdefgh").any { it.contains("digit") })
        assertTrue(Credentials.policyViolations("12345678").any { it.contains("letter") })
        assertTrue(Credentials.policyViolations("12345678").any { it.contains("digits only") })
    }

    @Test
    fun aCompliantPinHasNoViolations() {
        assertTrue(Credentials.policyViolations("ChhatraLekha2024").isEmpty())
    }
}
