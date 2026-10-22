package com.acadentrix.core.security

import org.junit.Assert.assertEquals
import org.junit.Test

class PrivacyMaskTest {
    @Test fun `masks full APAAAR number`() = assertEquals("9842 **** ****", PrivacyMask.apaar("984210357890"))
    @Test fun `does not expose a short partial number`() = assertEquals("***", PrivacyMask.apaar("123"))
}
