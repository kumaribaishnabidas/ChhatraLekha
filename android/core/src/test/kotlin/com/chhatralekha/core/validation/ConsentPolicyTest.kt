package com.chhatralekha.core.validation

import com.chhatralekha.core.model.ConsentChannel
import com.chhatralekha.core.model.ConsentPurpose
import com.chhatralekha.core.model.ConsentRecord
import com.chhatralekha.core.model.ConsentStatus
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Behaviour of the consent ledger policy.
 */
class ConsentPolicyTest {

    private fun consent(
        purpose: ConsentPurpose,
        status: ConsentStatus = ConsentStatus.GRANTED,
        recordedAt: Long = 1_726_000_000_000L,
        channel: ConsentChannel = ConsentChannel.MOBILE_APP
    ) = ConsentRecord(
        consentId = "CNS-${purpose.name}-$recordedAt",
        studentApaarId = "984210357890",
        purpose = purpose,
        status = status,
        channel = channel,
        policyVersion = "2024-01",
        recordedAt = recordedAt,
        revokedAt = if (status == ConsentStatus.REVOKED) recordedAt + 1_000 else null
    )

    @Test
    fun anExplicitPurposeIsBlockedWithoutConsent() {
        val decision = ConsentPolicy.evaluate(ConsentPurpose.CREDENTIAL_VERIFICATION, emptyList())
        assertFalse(decision.allowed)
        assertEquals(ConsentStatus.PENDING, decision.status)
        assertTrue(decision.reason.contains("No consent"))
    }

    @Test
    fun aGrantedExplicitPurposeIsAllowed() {
        val decision = ConsentPolicy.evaluate(
            ConsentPurpose.CREDENTIAL_VERIFICATION,
            listOf(consent(ConsentPurpose.CREDENTIAL_VERIFICATION))
        )
        assertTrue(decision.allowed)
        assertEquals(ConsentStatus.GRANTED, decision.status)
    }

    @Test
    fun aRevocationBlocksThePurpose() {
        val decision = ConsentPolicy.evaluate(
            ConsentPurpose.DATA_SHARING_WITH_EMPLOYER,
            listOf(
                consent(ConsentPurpose.DATA_SHARING_WITH_EMPLOYER, recordedAt = 1L),
                consent(
                    ConsentPurpose.DATA_SHARING_WITH_EMPLOYER,
                    status = ConsentStatus.REVOKED,
                    recordedAt = 2L
                )
            )
        )
        assertFalse(decision.allowed)
        assertEquals(ConsentStatus.REVOKED, decision.status)
        assertTrue(decision.reason.contains("withdrew"))
    }

    @Test
    fun aLaterGrantReinstatesARevokedPurpose() {
        val decision = ConsentPolicy.evaluate(
            ConsentPurpose.DATA_SHARING_WITH_EMPLOYER,
            listOf(
                consent(ConsentPurpose.DATA_SHARING_WITH_EMPLOYER, status = ConsentStatus.REVOKED, recordedAt = 1L),
                consent(ConsentPurpose.DATA_SHARING_WITH_EMPLOYER, recordedAt = 2L)
            )
        )
        assertTrue(decision.allowed)
    }

    @Test
    fun aNonExplicitPurposeIsAllowedByDefault() {
        val decision = ConsentPolicy.evaluate(ConsentPurpose.ANALYTICS_AND_REPORTING, emptyList())
        assertTrue(decision.allowed)
        assertEquals(ConsentStatus.PENDING, decision.status)
    }

    @Test
    fun aRevokedNonExplicitPurposeStillBlocks() {
        val decision = ConsentPolicy.evaluate(
            ConsentPurpose.ANALYTICS_AND_REPORTING,
            listOf(consent(ConsentPurpose.ANALYTICS_AND_REPORTING, status = ConsentStatus.REVOKED))
        )
        assertFalse(decision.allowed)
    }

    @Test
    fun aPendingExplicitPurposeBlocks() {
        val decision = ConsentPolicy.evaluate(
            ConsentPurpose.RESEARCH,
            listOf(consent(ConsentPurpose.RESEARCH, status = ConsentStatus.PENDING))
        )
        assertFalse(decision.allowed)
    }

    @Test
    fun fullConsentRequiresEveryExplicitPurpose() {
        val explicit = ConsentPurpose.entries.filter { it.requiresExplicitConsent }
        assertTrue(explicit.isNotEmpty())

        val partial = explicit.dropLast(1).map { consent(it) }
        assertFalse(ConsentPolicy.isFullyConsented(partial))

        val complete = explicit.map { consent(it) }
        assertTrue(ConsentPolicy.isFullyConsented(complete))
    }

    @Test
    fun blockingPurposesListsWhatStopsTheOperation() {
        val consents = listOf(consent(ConsentPurpose.CREDENTIAL_VERIFICATION))
        val blocking = ConsentPolicy.blockingPurposes(consents)
        assertFalse(blocking.contains(ConsentPurpose.CREDENTIAL_VERIFICATION))
        assertTrue(blocking.contains(ConsentPurpose.DATA_SHARING_WITH_EMPLOYER))
    }

    @Test
    fun evaluateAllCoversEveryPurpose() {
        val decisions = ConsentPolicy.evaluateAll(emptyList())
        assertEquals(ConsentPurpose.entries.size, decisions.size)
    }
}
