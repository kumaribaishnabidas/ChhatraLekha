package com.edusync.apaar.core.qr

/**
 * Builds and parses the deep-link payload carried by the APAAR QR badge.
 *
 * The payload is a plain HTTPS verification link so that any standards-compliant
 * QR scanner (or a future deep-link handler) can resolve the credential.
 */
object ApaarQrPayload {

    const val BASE_URL = "https://apaar.aicte-india.gov.in/verify"

    data class Parsed(
        val apaarId: String,
        val institutionId: String?,
        val programId: String?,
        val seal: String?,
        val timestamp: Long?
    )

    fun build(
        apaarId: String,
        institutionId: String,
        programId: String,
        seal: String,
        timestamp: Long
    ): String = buildString {
        append(BASE_URL)
        append("?apaar=").append(apaarId)
        append("&inst=").append(institutionId)
        append("&prog=").append(programId)
        append("&seal=").append(seal)
        append("&t=").append(timestamp)
    }

    /**
     * Extracts the APAAR identifier from a scanned payload. Accepts the canonical
     * verification URL as well as a bare 12-digit identifier.
     */
    fun parse(raw: String?): Parsed? {
        val value = raw?.trim().orEmpty()
        if (value.isEmpty()) return null
        if (value.matches(Regex("^\\d{12}$"))) {
            return Parsed(value, null, null, null, null)
        }
        val apaar = parameter(value, "apaar") ?: return null
        return Parsed(
            apaarId = apaar,
            institutionId = parameter(value, "inst"),
            programId = parameter(value, "prog"),
            seal = parameter(value, "seal"),
            timestamp = parameter(value, "t")?.toLongOrNull()
        )
    }

    private fun parameter(url: String, key: String): String? {
        val query = url.substringAfter('?', "").ifEmpty { return null }
        return query.split('&').firstOrNull { it.substringBefore('=').equals(key, ignoreCase = true) }
            ?.substringAfter('=', "")
            ?.takeIf { it.isNotBlank() }
    }
}
