package com.chhatralekha.core.security

/**
 * Presentation-only privacy helpers. APAAR IDs are never spoken, logged or
 * rendered in full; callers must use this result outside trusted input fields.
 */
object PrivacyMask {
    fun apaar(value: String?): String {
        val digits = value.orEmpty().filter(Char::isDigit)
        return when {
            digits.isEmpty() -> "—"
            digits.length < 4 -> "*".repeat(digits.length)
            else -> "${digits.take(4)} **** ****"
        }
    }
}
