package com.acadentrix.core.validation

/**
 * Outcome of validating a candidate APAAR ID.
 */
data class ApaarValidation(
    val raw: String,
    val normalised: String,
    val isStructurallyValid: Boolean,
    val isChecksumValid: Boolean,
    val masked: String,
    val errors: List<String>,
    val advisories: List<String>
) {
    val isAcceptable: Boolean get() = isStructurallyValid
    val hasErrors: Boolean get() = errors.isNotEmpty()
}

/**
 * Validator for the 12-digit Automated Permanent Academic Account Registry identifier.
 *
 * Hard (blocking) rules implement the AICTE syntactic check:
 *  - exactly 12 numeric characters,
 *  - not a trivial / placeholder sequence (repeated digits, ascending or descending runs),
 *  - not a padded-zero or all-zero value.
 *
 * The Luhn check-digit is evaluated as a **non-blocking advisory** because the
 * published APAAR allocation algorithm is administered by the Ministry and the
 * checksum is not part of the public verification contract. A failing checksum is
 * surfaced as a warning so registrars can double-check transcription without
 * rejecting genuine identifiers.
 */
object ApaarIdValidator {

    const val LENGTH = 12

    private val trivialRuns = setOf(
        "012345678901", "123456789012", "987654321098", "098765432109", "111111111111",
        "000000000000", "222222222222", "333333333333", "444444444444", "555555555555",
        "666666666666", "777777777777", "888888888888", "999999999999", "121212121212",
        "123123123123", "123412341234", "101010101010", "202020202020", "999999999990"
    )

    fun validate(raw: String?): ApaarValidation {
        val original = raw.orEmpty()
        val compact = original.filter { it.isDigit() }
        val errors = mutableListOf<String>()
        val advisories = mutableListOf<String>()

        if (original.isBlank()) {
            errors += "APAAR ID is mandatory."
            return ApaarValidation(original, "", false, false, mask(""), errors, advisories)
        }

        if (original.any { !it.isDigit() && !it.isWhitespace() && it != '-' }) {
            errors += "APAAR ID must contain digits only (found '${original.first { !it.isDigit() && !it.isWhitespace() && it != '-' }}')."
        }

        if (compact.length != LENGTH) {
            errors += "APAAR ID must be exactly $LENGTH digits (found ${compact.length})."
        }

        val structurallyValid = errors.isEmpty()

        if (structurallyValid) {
            if (compact in trivialRuns) {
                errors += "APAAR ID '$compact' is a trivial placeholder sequence and is not a valid registry identifier."
            } else if (compact.all { it == compact[0] }) {
                errors += "APAAR ID must not be a single repeated digit."
            } else if (isStrictRun(compact)) {
                errors += "APAAR ID must not be an ascending or descending digit run."
            } else if (compact.startsWith("0000")) {
                errors += "APAAR ID must not start with four or more zeros."
            }
        }

        val checksumValid = if (compact.length == LENGTH) luhnValid(compact) else false
        if (structurallyValid && !checksumValid) {
            advisories += "Luhn check-digit advisory: checksum does not match. Re-verify transcription (non-blocking)."
        }

        return ApaarValidation(
            raw = original,
            normalised = compact,
            isStructurallyValid = errors.isEmpty(),
            isChecksumValid = checksumValid,
            masked = mask(compact),
            errors = errors,
            advisories = advisories
        )
    }

    /** Formats a 12-digit identifier as `1234 5678 9012`. */
    fun format(value: String?): String {
        val compact = value.orEmpty().filter { it.isDigit() }
        if (compact.isEmpty()) return ""
        return compact.chunked(4).joinToString(" ")
    }

    /** Formats as `1234-5678-9012` for printed certificate layouts. */
    fun formatWithSeparator(value: String?): String {
        val compact = value.orEmpty().filter { it.isDigit() }
        if (compact.isEmpty()) return ""
        return compact.chunked(4).joinToString("-")
    }

    /** Partially masks an identifier for display in audit trails: `9842 10•• ••••`. */
    fun mask(value: String?): String {
        val compact = value.orEmpty().filter { it.isDigit() }
        if (compact.length < 4) return compact
        val groups = compact.chunked(4)
        return groups.mapIndexed { index, group ->
            if (index == 0) group else "•".repeat(group.length)
        }.joinToString(" ")
    }

    /**
     * Standard Luhn modulo-10 check over a run of digits.
     *
     * The check is generic so that it can be exercised against the canonical
     * reference vectors; [validate] applies it only to 12-digit identifiers.
     */
    fun luhnValid(digits: String): Boolean {
        if (digits.isEmpty() || digits.any { !it.isDigit() }) return false
        var sum = 0
        var double = false
        for (i in digits.length - 1 downTo 0) {
            var value = digits[i] - '0'
            if (double) {
                value *= 2
                if (value > 9) value -= 9
            }
            sum += value
            double = !double
        }
        return sum % 10 == 0
    }

    /** Computes the Luhn check digit for a candidate prefix. */
    fun luhnCheckDigit(prefix: String): Int {
        var sum = 0
        var double = true // the check digit position itself is doubled
        for (i in prefix.length - 1 downTo 0) {
            var value = prefix[i] - '0'
            if (double) {
                value *= 2
                if (value > 9) value -= 9
            }
            sum += value
            double = !double
        }
        return (10 - (sum % 10)) % 10
    }

    /** Generates a demo APAAR identifier that passes the structural and Luhn checks. */
    fun generate(seed: Long): String {
        var state = seed * 6_364_136_223_846_793_005L + 1_442_695_040_888_963_407L
        val builder = StringBuilder(LENGTH)
        repeat(LENGTH - 1) {
            state = state * 6_364_136_223_846_793_005L + 1_442_695_040_888_963_407L
            val digit = ((state ushr 33) % 10L).toInt()
            if (it == 0 && digit == 0) builder.append(1) else builder.append(digit)
        }
        builder.append(luhnCheckDigit(builder.toString()))
        return builder.toString()
    }

    private fun isStrictRun(digits: String): Boolean {
        val ascending = digits.zipWithNext().all { (a, b) -> b - a == 1 }
        val descending = digits.zipWithNext().all { (a, b) -> a - b == 1 }
        return ascending || descending
    }
}
