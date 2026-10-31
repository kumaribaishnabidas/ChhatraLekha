package com.acadentrix.core.qr

/**
 * Builds and parses the deep-link payload carried by the APAAR QR badge.
 *
 * The payload is a plain HTTPS verification link so that any standards-compliant
 * QR scanner (or a future deep-link handler) can resolve the credential.
 */
object ApaarQrPayload {

    const val BASE_URL = "https://chhatralekha.vercel.app/verify"

    data class Parsed(
        val apaarId: String,
        val institutionId: String? = null,
        val programId: String? = null,
        val seal: String? = null,
        val timestamp: Long? = null,
        val token: String? = null
    ) {
        val isTokenPayload: Boolean get() = !token.isNullOrBlank()
    }

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

    fun buildToken(token: String, baseUrl: String = BASE_URL): String =
        "${baseUrl.trimEnd('/')}/t/$token"

    /**
     * Extracts the APAAR identifier or opaque token from a scanned payload. Accepts:
     * 1. Token URLs: {origin}/verify/t/{token} or {origin}/verify/token/{token}
     * 2. Canonical query verification URLs: {origin}/verify?apaar=...&seal=...
     * 3. Bare 12-digit identifier.
     */
    fun parse(raw: String?): Parsed? {
        val value = raw?.trim().orEmpty()
        if (value.isEmpty()) return null
        if (value.matches(Regex("^\\d{12}$"))) {
            return Parsed(apaarId = value)
        }

        // Check for token pattern: /verify/t/{token} or /verify/token/{token} or ?token={token}
        val tokenFromPath = Regex("/verify/(?:t|token)/([A-Za-z0-9_.-]+)")
            .find(value)?.groupValues?.get(1)
        val tokenFromParam = parameter(value, "token")
        val token = tokenFromPath ?: tokenFromParam
        if (!token.isNullOrBlank()) {
            return Parsed(apaarId = "", token = token)
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

