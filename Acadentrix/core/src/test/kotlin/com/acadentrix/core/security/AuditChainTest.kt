package com.acadentrix.core.security

import com.acadentrix.core.model.AuditEntry
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Behaviour of the tamper-evident audit chain.
 */
class AuditChainTest {

    private fun entry(
        id: Long,
        timestamp: Long = 1_726_000_000_000L + id,
        actor: String = "AICTE Central Registry",
        action: String = "BATCH_COMMIT",
        subject: String = "INST-0421",
        details: String = "Committed $id rows.",
        category: String = "ADMISSIONS"
    ) = AuditEntry(
        logId = id,
        timestamp = timestamp,
        actor = actor,
        action = action,
        subject = subject,
        details = details,
        category = category
    )

    @Test
    fun theFirstEntryLinksToTheGenesisHash() {
        val chained = AuditChain.chain(listOf(entry(1)))
        assertEquals(AuditChain.GENESIS_HASH, chained.single().prevHash)
        assertEquals(64, chained.single().hash.length)
    }

    @Test
    fun everyEntryLinksToItsPredecessor() {
        val chained = AuditChain.chain((1L..5L).map { entry(it) })
        assertEquals(AuditChain.GENESIS_HASH, chained[0].prevHash)
        chained.zipWithNext().forEach { (previous, next) ->
            assertEquals(previous.hash, next.prevHash)
        }
    }

    @Test
    fun theHashDependsOnEveryField() {
        val base = entry(1)
        val reference = AuditChain.hashOf(base.copy(prevHash = AuditChain.GENESIS_HASH))
        assertNotEquals(reference, AuditChain.hashOf(base.copy(prevHash = AuditChain.GENESIS_HASH, actor = "Someone else")))
        assertNotEquals(reference, AuditChain.hashOf(base.copy(prevHash = AuditChain.GENESIS_HASH, action = "DELETE")))
        assertNotEquals(reference, AuditChain.hashOf(base.copy(prevHash = AuditChain.GENESIS_HASH, subject = "INST-9999")))
        assertNotEquals(reference, AuditChain.hashOf(base.copy(prevHash = AuditChain.GENESIS_HASH, details = "42 rows")))
        assertNotEquals(reference, AuditChain.hashOf(base.copy(prevHash = AuditChain.GENESIS_HASH, category = "SYSTEM")))
        assertNotEquals(reference, AuditChain.hashOf(base.copy(prevHash = AuditChain.GENESIS_HASH, timestamp = 1L)))
    }

    @Test
    fun aFreshlyChainedTrailVerifies() {
        val chained = AuditChain.chain((1L..10L).map { entry(it) })
        assertTrue(AuditChain.verify(chained))
        assertNull(AuditChain.firstBreak(chained))
    }

    @Test
    fun anAlteredEntryBreaksTheChain() {
        val chained = AuditChain.chain((1L..5L).map { entry(it) })
        val tampered = chained.toMutableList()
        tampered[2] = tampered[2].copy(details = "Committed 9999 rows.")
        assertFalse(AuditChain.verify(tampered))
        assertTrue(AuditChain.firstBreak(tampered)!!.contains("altered"))
    }

    @Test
    fun aRemovedEntryBreaksTheChain() {
        val chained = AuditChain.chain((1L..5L).map { entry(it) })
        val withHole = chained.toMutableList().apply { removeAt(2) }
        assertFalse(AuditChain.verify(withHole))
        assertTrue(AuditChain.firstBreak(withHole)!!.contains("link"))
    }

    @Test
    fun aReorderedChainBreaksTheChain() {
        val chained = AuditChain.chain((1L..5L).map { entry(it) })
        val shuffled = chained.toMutableList().apply { add(1, removeAt(3)) }
        assertFalse(AuditChain.verify(shuffled))
    }

    @Test
    fun anEmptyChainVerifies() {
        assertTrue(AuditChain.verify(emptyList()))
        assertNull(AuditChain.firstBreak(emptyList()))
    }

    @Test
    fun theHashIsStableAcrossRuns() {
        val first = AuditChain.hashOf(entry(1).copy(prevHash = AuditChain.GENESIS_HASH))
        val second = AuditChain.hashOf(entry(1).copy(prevHash = AuditChain.GENESIS_HASH))
        assertEquals(first, second)
        assertEquals(64, first.length)
        assertTrue(first.all { it.isDigit() || it in 'a'..'f' })
    }
}
