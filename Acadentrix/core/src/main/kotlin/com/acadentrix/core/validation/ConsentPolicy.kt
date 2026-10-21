package com.acadentrix.core.validation

import com.acadentrix.core.model.ConsentPurpose
import com.acadentrix.core.model.ConsentRecord
import com.acadentrix.core.model.ConsentStatus

/**
 * The outcome of checking one purpose against the consent ledger.
 */
data class ConsentDecision(
    val purpose: ConsentPurpose,
    val status: ConsentStatus,
    val allowed: Boolean,
    val reason: String,
    val record: ConsentRecord? = null
)

/**
 * Evaluates the consent ledger against the purposes for which a student record
 * is about to be used.
 *
 * The rules follow the Digital Personal Data Protection Act 2023:
 *
 *  * a purpose that requires explicit consent is only allowed when a
 *    `GRANTED` record exists for it;
 *  * a revocation always wins over an earlier grant, whatever the order in
 *    which the records were written;
 *  * a purpose that does not require explicit consent is allowed by default,
 *    but a recorded revocation still blocks it;
 *  * the most recent record for a purpose is the one that counts.
 */
object ConsentPolicy {

    /**
     * Decides whether [purpose] may be exercised for a student.
     *
     * @param consents every consent record belonging to that student.
     */
    fun evaluate(purpose: ConsentPurpose, consents: List<ConsentRecord>): ConsentDecision {
        val relevant = consents.filter { it.purpose == purpose }
        if (relevant.isEmpty()) {
            return if (purpose.requiresExplicitConsent) {
                ConsentDecision(
                    purpose = purpose,
                    status = ConsentStatus.PENDING,
                    allowed = false,
                    reason = "No consent has been recorded for '${purpose.label}'."
                )
            } else {
                ConsentDecision(
                    purpose = purpose,
                    status = ConsentStatus.PENDING,
                    allowed = true,
                    reason = "'${purpose.label}' does not require explicit consent."
                )
            }
        }

        val latest = relevant.maxByOrNull { it.recordedAt }!!
        return when (latest.status) {
            ConsentStatus.GRANTED -> ConsentDecision(
                purpose = purpose,
                status = ConsentStatus.GRANTED,
                allowed = true,
                reason = "Consent granted on ${latest.channel.label}.",
                record = latest
            )

            ConsentStatus.REVOKED -> ConsentDecision(
                purpose = purpose,
                status = ConsentStatus.REVOKED,
                allowed = false,
                reason = "The student withdrew consent for '${purpose.label}'.",
                record = latest
            )

            ConsentStatus.PENDING -> ConsentDecision(
                purpose = purpose,
                status = ConsentStatus.PENDING,
                allowed = !purpose.requiresExplicitConsent,
                reason = "Consent for '${purpose.label}' is still pending.",
                record = latest
            )
        }
    }

    /**
     * Evaluates every purpose at once.
     */
    fun evaluateAll(consents: List<ConsentRecord>): List<ConsentDecision> =
        ConsentPurpose.entries.map { evaluate(it, consents) }

    /**
     * Whether every purpose that requires explicit consent has been granted.
     */
    fun isFullyConsented(consents: List<ConsentRecord>): Boolean =
        ConsentPurpose.entries
            .filter { it.requiresExplicitConsent }
            .all { evaluate(it, consents).allowed }

    /**
     * The purposes that block the requested operation.
     */
    fun blockingPurposes(consents: List<ConsentRecord>): List<ConsentPurpose> =
        evaluateAll(consents).filterNot { it.allowed }.map { it.purpose }
}
