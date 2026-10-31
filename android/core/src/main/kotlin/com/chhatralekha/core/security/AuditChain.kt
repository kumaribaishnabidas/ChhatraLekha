package com.chhatralekha.core.security

import com.chhatralekha.core.model.AuditEntry

/**
 * Makes the regulatory audit trail **tamper-evident** by chaining every entry
 * to its predecessor.
 *
 * Each entry stores the hash of the previous entry and its own hash:
 *
 * ```
 * hash(n) = SHA-256( hash(n-1) || timestamp || actor || action || subject || details || category )
 * ```
 *
 * Deleting, reordering or editing any row invalidates every hash after it, so
 * an auditor can prove that the trail has not been rewritten. The chain is
 * self-contained — no server, no key — which means it can be re-verified
 * offline by the AICTE inspector or by the student who holds a copy.
 */
object AuditChain {

    /** The `prevHash` of the very first entry in a chain. */
    const val GENESIS_HASH: String =
        "0000000000000000000000000000000000000000000000000000000000000000"

    /**
     * Computes the chain hash of a single entry.
     *
     * The fields are joined with a `|` separator, which cannot occur inside a
     * field value, so two different field tuples can never collide.
     */
    fun hash(
        prevHash: String,
        timestamp: Long,
        actor: String,
        action: String,
        subject: String,
        details: String,
        category: String
    ): String = SealGenerator.sha256(
        listOf(
            prevHash.ifBlank { GENESIS_HASH },
            timestamp.toString(),
            actor,
            action,
            subject,
            details,
            category
        ).joinToString("|")
    )

    /**
     * Computes the chain hash of an entry that has no hash yet.
     */
    fun hashOf(entry: AuditEntry): String = hash(
        prevHash = entry.prevHash,
        timestamp = entry.timestamp,
        actor = entry.actor,
        action = entry.action,
        subject = entry.subject,
        details = entry.details,
        category = entry.category
    )

    /**
     * Returns the entries with their chain hashes filled in.
     *
     * The entries are chained in the order given; callers should pass them
     * oldest-first.
     */
    fun chain(entries: List<AuditEntry>): List<AuditEntry> {
        var prev = GENESIS_HASH
        return entries.map { entry ->
            val digest = hash(
                prevHash = prev,
                timestamp = entry.timestamp,
                actor = entry.actor,
                action = entry.action,
                subject = entry.subject,
                details = entry.details,
                category = entry.category
            )
            val chained = entry.copy(prevHash = prev, hash = digest)
            prev = digest
            chained
        }
    }

    /**
     * Verifies a chain of entries.
     *
     * The entries must be supplied oldest-first. A chain is valid when every
     * entry's [AuditEntry.prevHash] equals the previous entry's
     * [AuditEntry.hash] and every stored hash matches the recomputed one.
     */
    fun verify(entries: List<AuditEntry>): Boolean {
        var prev = GENESIS_HASH
        entries.forEach { entry ->
            if (entry.prevHash != prev) return false
            val expected = hash(
                prevHash = entry.prevHash,
                timestamp = entry.timestamp,
                actor = entry.actor,
                action = entry.action,
                subject = entry.subject,
                details = entry.details,
                category = entry.category
            )
            if (entry.hash != expected) return false
            prev = entry.hash
        }
        return true
    }

    /**
     * Describes the first broken link of a chain, or `null` when the chain is
     * intact. Used by the audit-trail screen to explain *why* a trail is bad.
     */
    fun firstBreak(entries: List<AuditEntry>): String? {
        var prev = GENESIS_HASH
        entries.forEachIndexed { index, entry ->
            if (entry.prevHash != prev) {
                return "Entry ${index + 1} does not link to the previous entry."
            }
            val expected = hash(
                prevHash = entry.prevHash,
                timestamp = entry.timestamp,
                actor = entry.actor,
                action = entry.action,
                subject = entry.subject,
                details = entry.details,
                category = entry.category
            )
            if (entry.hash != expected) {
                return "Entry ${index + 1} has been altered after it was written."
            }
            prev = entry.hash
        }
        return null
    }
}
