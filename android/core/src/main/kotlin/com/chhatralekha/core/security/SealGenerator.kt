package com.chhatralekha.core.security

import java.security.MessageDigest
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

/**
 * Produces the tamper-evident cryptographic seal printed on every APAAR
 * verification certificate and encoded into the QR badge.
 *
 * The seal is a truncated SHA-256 digest over the canonical credential string,
 * which means any alteration of the student record changes the seal and can be
 * detected by an independent verifier.
 */
object SealGenerator {

    private const val SEAL_LENGTH = 32

    /**
     * Canonical digest of a student credential.
     */
    fun seal(
        apaarId: String,
        institutionId: String,
        programId: String,
        academicYear: String,
        enrollmentDate: String
    ): String {
        val canonical = listOf(
            "APAAR",
            apaarId.trim(),
            institutionId.trim(),
            programId.trim(),
            academicYear.trim(),
            enrollmentDate.trim()
        ).joinToString("|")
        return sha256(canonical).take(SEAL_LENGTH).uppercase()
    }

    /**
     * Full SHA-256 hex digest of an arbitrary string.
     */
    fun sha256(value: String): String {
        val digest = MessageDigest.getInstance("SHA-256").digest(value.toByteArray(Charsets.UTF_8))
        return buildString { for (byte in digest) append("%02x".format(byte)) }
    }

    /**
     * Verifies that a presented seal matches the recomputed digest.
     */
    fun verify(
        presented: String,
        apaarId: String,
        institutionId: String,
        programId: String,
        academicYear: String,
        enrollmentDate: String
    ): Boolean {
        val expected = seal(apaarId, institutionId, programId, academicYear, enrollmentDate)
        return presented.trim().equals(expected, ignoreCase = true)
    }

    /**
     * Human readable RFC-3339 style timestamp used on certificates.
     */
    fun formatTimestamp(millis: Long): String {
        val format = SimpleDateFormat("dd MMM yyyy, HH:mm:ss 'IST'", Locale.ENGLISH)
        format.timeZone = TimeZone.getTimeZone("Asia/Kolkata")
        return format.format(Date(millis))
    }

    /**
     * ISO timestamp used for audit logs and machine-readable payloads.
     */
    fun formatIso(millis: Long): String {
        val format = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.ENGLISH)
        format.timeZone = TimeZone.getTimeZone("UTC")
        return format.format(Date(millis))
    }
}
